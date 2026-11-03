"""Exercise the real loopback HTTP boundary without a browser dependency."""

import base64
import http.client
import json
import threading
import unittest


class WebTests(unittest.TestCase):
    def setUp(self):
        from rowcanary.web import make_server

        self.server = make_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.port = self.server.server_port
        self.origin = f"http://127.0.0.1:{self.port}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, payload=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
        self.addCleanup(connection.close)
        body = json.dumps(payload).encode() if payload is not None else None
        normal = {
            "Content-Type": "application/json",
            "Origin": self.origin,
            "X-RowCanary-Token": self.server.token,
        }
        normal.update(headers or {})
        connection.request(method, path, body, normal)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def post(self, path, payload, headers=None):
        status, response_headers, body = self.request("POST", path, payload, headers)
        return status, response_headers, json.loads(body)

    def test_loopback_only_and_safe_static_routes(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"RowCanary", body)
        self.assertIn(self.server.token.encode(), body)
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Cache-Control"], "no-store")
        for path in ("/../pyproject.toml", "/PROGRESS.md", "/%2e%2e/", "/nothing"):
            self.assertEqual(self.request("GET", path)[0], 404)
        for path in ("/app.css", "/app.js", "/icon.svg"):
            self.assertEqual(self.request("GET", path)[0], 200)

    def test_host_origin_token_and_content_type_are_enforced(self):
        for headers, code in (
            ({"Host": "attacker.test"}, 403),
            ({"Origin": "https://attacker.test"}, 403),
            ({"Origin": "null"}, 403),
            ({"X-RowCanary-Token": ""}, 403),
            ({"Content-Type": "text/plain"}, 415),
        ):
            with self.subTest(headers=headers):
                self.assertEqual(self.post("/api/make", {}, headers)[0], code)
        self.assertEqual(self.request("GET", "/", headers={"Host": "attacker.test"})[0], 403)

    def test_generate_and_check_all_formats_with_reports(self):
        for fmt in ("csv", "tsv", "json", "jsonl", "xlsx"):
            with self.subTest(fmt=fmt):
                status, _, generated = self.post(
                    "/api/make", {"format": fmt, "probe_set": "extended"}
                )
                self.assertEqual(status, 200, generated)
                self.assertEqual(generated["filename"], "rowcanary-probe." + fmt)
                data = base64.b64decode(generated["data"], validate=True)
                self.assertTrue(data)
                status, _, checked = self.post(
                    "/api/check",
                    {"format": fmt, "probe_set": "extended", "data": generated["data"]},
                )
                self.assertEqual(status, 200, checked)
                self.assertTrue(checked["report"]["ok"])
                self.assertIn("<!doctype html>", checked["html"])

    def test_malformed_uploads_and_differences_are_distinct(self):
        status, _, checked = self.post(
            "/api/check", {"format": "json", "data": base64.b64encode(b"[]").decode()}
        )
        self.assertEqual(status, 200)
        self.assertFalse(checked["report"]["ok"])
        for payload in (
            {"data": "!bad"},
            {"data": 12},
            {"format": "json", "data": ""},
            {"format": "unknown"},
            {"output": "../escape.csv"},
            {"custom_values": {"bad": True}},
            {"strict_order": "false"},
        ):
            with self.subTest(payload=payload):
                status, _, result = self.post("/api/check", payload)
                self.assertEqual(status, 400, result)
                self.assertIn("error", result)
        self.assertEqual(self.post("/api/nothing", {})[0], 404)

    def test_upload_bound_is_checked_before_reading_body(self):
        from rowcanary.web import MAX_REQUEST_BYTES

        self.assertEqual(
            self.post("/api/make", {}, {"Content-Length": str(MAX_REQUEST_BYTES + 1)})[0], 413
        )

    def test_custom_controls_use_exact_types_and_never_name_local_paths(self):
        custom = [{"id": "x", "value": "a\r\nb"}, {"id": "n", "value": None}]
        options = {"format": "json", "probe_set": "none", "custom_values": custom}
        status, _, generated = self.post("/api/make", options)
        self.assertEqual(status, 200)
        status, _, checked = self.post("/api/check", {**options, "data": generated["data"]})
        self.assertEqual(status, 200)
        self.assertTrue(checked["report"]["ok"])
        self.assertEqual(checked["report"]["input"], "uploaded.json")

    def test_raw_custom_json_preserves_large_integers_without_javascript_coercion(self):
        options = {
            "format": "json",
            "probe_set": "none",
            "custom_values_json": '[{"id":"large","value":9007199254740993}]',
        }
        status, _, generated = self.post("/api/make", options)
        self.assertEqual(status, 200, generated)
        rows = json.loads(base64.b64decode(generated["data"]))
        self.assertEqual(rows[0]["_rowcanary_value"], 9007199254740993)
        status, _, checked = self.post("/api/check", {**options, "data": generated["data"]})
        self.assertEqual(status, 200)
        self.assertTrue(checked["report"]["ok"])

    def test_default_check_encoding_accepts_utf8_bom_exports(self):
        _, _, generated = self.post("/api/make", {"format": "csv"})
        data = b"\xef\xbb\xbf" + base64.b64decode(generated["data"])
        status, _, checked = self.post(
            "/api/check", {"format": "csv", "data": base64.b64encode(data).decode()}
        )
        self.assertEqual(status, 200, checked)
        self.assertTrue(checked["report"]["ok"])

    def test_duplicate_lengths_and_transfer_encoding_are_rejected(self):
        for transfer in (False, True):
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
            self.addCleanup(connection.close)
            connection.putrequest("POST", "/api/make")
            connection.putheader("Origin", self.origin)
            connection.putheader("X-RowCanary-Token", self.server.token)
            connection.putheader("Content-Type", "application/json")
            connection.putheader("Content-Length", "2")
            if transfer:
                connection.putheader("Transfer-Encoding", "chunked")
            else:
                connection.putheader("Content-Length", "2")
            connection.endheaders(b"{}")
            self.assertEqual(connection.getresponse().status, 400)

    def test_concurrent_clients_keep_custom_controls_separate(self):
        from concurrent.futures import ThreadPoolExecutor

        def make(value):
            options = {
                "format": "json",
                "probe_set": "none",
                "custom_values_json": json.dumps([{"id": "x", "value": value}]),
            }
            status, _, result = self.post("/api/make", options)
            return status, json.loads(base64.b64decode(result["data"]))[0]["_rowcanary_value"]

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(make, ("first", "second")))
        self.assertEqual(results, [(200, "first"), (200, "second")])
