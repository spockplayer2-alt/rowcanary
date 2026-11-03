"""Single-user loopback UI. Never exposes the filesystem or a public bind."""

from __future__ import annotations

import base64
import binascii
import json
import secrets
import socket
import tempfile
import webbrowser
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.resources import files
from pathlib import Path

from .core import (
    MAX_BYTES,
    ID_COLUMN,
    VALUE_COLUMN,
    ProbeFileError,
    _json_object,
    check_file,
    write_probes,
)
from .formats import FORMATS
from .probes import select_probes
from .reporting import html_report

MAX_REQUEST_BYTES = ((MAX_BYTES + 2) // 3) * 4 + 1024 * 1024
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/app.css": ("app.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/icon.svg": ("icon.svg", "image/svg+xml"),
}
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"


def _operate(payload, operation):
    allowed = {
        "format",
        "encoding",
        "delimiter",
        "probe_set",
        "custom_values",
        "custom_values_json",
        "strict_order",
        "id_column",
        "value_column",
        "data",
        "filename",
    }
    if not isinstance(payload, dict) or set(payload) - allowed:
        raise ProbeFileError("Unknown request options")
    for key in (
        "format",
        "encoding",
        "delimiter",
        "probe_set",
        "id_column",
        "value_column",
        "filename",
    ):
        if key in payload and (not isinstance(payload[key], str) or len(payload[key]) > 255):
            raise ProbeFileError(f"{key} must be bounded text")
    if "strict_order" in payload and not isinstance(payload["strict_order"], bool):
        raise ProbeFileError("strict_order must be a boolean")
    fmt = payload.get("format", "csv" if operation == "make" else "auto")
    if fmt not in ("auto", *FORMATS) or (operation == "make" and fmt == "auto"):
        raise ProbeFileError("Choose a supported format")
    suffix = fmt
    if fmt == "auto":
        suffix = payload.get("filename", "").rsplit(".", 1)[-1].lower()
        if suffix not in FORMATS:
            suffix = "bin"
    with tempfile.TemporaryDirectory(prefix="rowcanary-web-") as directory:
        root = Path(directory)
        custom_path = None
        if "custom_values" in payload:
            if not isinstance(payload["custom_values"], list):
                raise ProbeFileError("Custom controls must be a JSON array")
            custom_path = root / "custom.json"
            custom_path.write_text(json.dumps(payload["custom_values"]), encoding="utf-8")
        if "custom_values_json" in payload:
            if "custom_values" in payload or not isinstance(payload["custom_values_json"], str):
                raise ProbeFileError("Provide custom controls as one JSON array or raw JSON string")
            custom_path = root / "custom.json"
            custom_path.write_bytes(payload["custom_values_json"].encode("utf-8"))
        probes = select_probes(payload.get("probe_set", "default"), custom_path)
        path = root / ("uploaded." + suffix)
        options = dict(
            file_format=fmt,
            encoding=payload.get("encoding", "utf-8-sig" if operation == "check" else "utf-8"),
            delimiter=payload.get("delimiter", ","),
            probes=probes,
        )
        if operation == "make":
            write_probes(path, **options)
            return {
                "filename": "rowcanary-probe." + fmt,
                "data": base64.b64encode(path.read_bytes()).decode("ascii"),
                "count": len(probes),
            }
        encoded = payload.get("data")
        if not isinstance(encoded, str):
            raise ProbeFileError("Upload data must be base64 text")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ProbeFileError("Upload data is not valid base64") from exc
        if len(content) > MAX_BYTES:
            raise ProbeFileError("Upload exceeds the 32 MiB limit")
        path.write_bytes(content)
        report = check_file(
            path,
            **options,
            id_column=payload.get("id_column", ID_COLUMN),
            value_column=payload.get("value_column", VALUE_COLUMN),
            strict_order=payload.get("strict_order", False),
        )
        report = replace(report, input_path=path.name)
        return {"report": report.as_dict(), "html": html_report([report])}


class _Handler(BaseHTTPRequestHandler):
    # One request per connection; do not allow a rejected body to become a request.
    protocol_version = "HTTP/1.0"

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format, *args):
        # Paths and control values stay out of request logs.
        pass

    def _reply(self, status, content, content_type="application/json; charset=utf-8"):
        if not isinstance(content, bytes):
            content = json.dumps(content, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        for key, value in {
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
            "Cache-Control": "no-store",
            "Content-Security-Policy": CSP,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "DENY",
        }.items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def _host_allowed(self):
        return self.headers.get_all("Host", []) == [f"127.0.0.1:{self.server.server_port}"]

    def do_GET(self):
        if not self._host_allowed():
            self._reply(403, {"error": "Untrusted Host"})
        elif self.path not in STATIC:
            self._reply(404, {"error": "Not found"})
        else:
            name, mime = STATIC[self.path]
            content = files("rowcanary").joinpath("static", name).read_bytes()
            if name == "index.html":
                content = content.replace(b"{{TOKEN}}", self.server.token.encode("ascii"))
            self._reply(200, content, mime)

    def do_POST(self):
        origin = f"http://127.0.0.1:{self.server.server_port}"
        if (
            not self._host_allowed()
            or self.headers.get_all("Origin", []) != [origin]
            or self.headers.get_all("X-RowCanary-Token", []) != [self.server.token]
        ):
            self._reply(403, {"error": "Untrusted origin or missing session token"})
            return
        if self.path not in ("/api/make", "/api/check"):
            self._reply(404, {"error": "Not found"})
            return
        if (
            self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            != "application/json"
        ):
            self._reply(415, {"error": "Use application/json"})
            return
        lengths = self.headers.get_all("Content-Length", [])
        if (
            len(lengths) != 1
            or not lengths[0].isascii()
            or not lengths[0].isdigit()
            or self.headers.get("Transfer-Encoding")
        ):
            self._reply(400, {"error": "One valid Content-Length is required"})
            return
        length = int(lengths[0]) if len(lengths[0]) <= 10 else MAX_REQUEST_BYTES + 1
        if length > MAX_REQUEST_BYTES:
            self._reply(413, {"error": "Request exceeds the upload limit"})
            return
        try:
            data = self.rfile.read(length)
            if len(data) != length:
                raise ProbeFileError("Incomplete upload")
            payload = json.loads(data.decode("utf-8"), object_pairs_hook=_json_object)
            self._reply(200, _operate(payload, self.path.rsplit("/", 1)[-1]))
        except (ProbeFileError, ValueError, UnicodeError, RecursionError) as exc:
            self._reply(400, {"error": str(exc)})
        except (OSError, socket.timeout):
            self._reply(400, {"error": "Local operation failed or upload timed out"})


def make_server(*, port=8765):
    """Create a server bound only to IPv4 loopback; port 0 requests a free port."""
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ProbeFileError("Port must be an integer from 0 through 65535")
    server = HTTPServer(("127.0.0.1", port), _Handler)
    server.token = secrets.token_urlsafe(32)
    return server


def serve(*, port=8765, open_browser=False):
    with make_server(port=port) as server:
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"RowCanary local UI: {url}\nPress Ctrl+C to stop.", flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0
