import contextlib
import io
import json
import tempfile
import unittest
import unicodedata
from pathlib import Path

from rowcanary import check_file, write_probes
from rowcanary.cli import main
from rowcanary.core import Probe


class ReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def report(self, expected, actual):
        path = self.root / "test.json"
        path.write_text(
            json.dumps([{"_rowcanary_id": "custom", "_rowcanary_value": actual}]), encoding="utf-8"
        )
        return check_file(path, probes=(Probe("custom", expected, "custom", "Control changed"),))

    def test_classifications_describe_observable_relationships(self):
        cases = [
            ("0001", "1", "leading-zero-removal"),
            ("1.2345", "1.23", "numeric-rounding"),
            ("abcdef", "abc", "truncated"),
            (" a  b ", "a b", "whitespace-change"),
            ("é", unicodedata.normalize("NFD", "é"), "unicode-normalization"),
            ("São", "São".encode().decode("latin1"), "encoding-corruption"),
            ("2025-08-09", "08/09/2025", "date-representation-change"),
            ("TRUE", True, "type-coercion"),
            ("NULL", None, "null-conversion"),
        ]
        for before, after, kind in cases:
            with self.subTest(kind=kind):
                issue = self.report(before, after).issues[0].as_dict()
                self.assertIn(kind, issue["classifications"])
                self.assertTrue(issue["observation"])
                self.assertTrue(issue["guidance"])
                self.assertIsInstance(issue["possible_causes"], list)
                self.assertEqual(issue["severity"], "error")

    def test_prefix_matching_alone_does_not_claim_rounding(self):
        issue = self.report("1.239", "1.23").issues[0].as_dict()
        self.assertNotIn("numeric-rounding", issue["classifications"])
        self.assertIn("precision-loss", issue["classifications"])

    def test_rounding_observation_is_independent_of_host_decimal_rounding(self):
        from decimal import ROUND_DOWN, localcontext

        with localcontext() as context:
            context.rounding = ROUND_DOWN
            issue = self.report("1.235", "1.23").issues[0].as_dict()
        self.assertNotIn("numeric-rounding", issue["classifications"])

    def test_reorder_observation_is_nonfailing_unless_requested(self):
        path = self.root / "reordered.json"
        write_probes(path)
        rows = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(rows[::-1]), encoding="utf-8")
        report = check_file(path)
        self.assertTrue(report.ok)
        self.assertEqual(report.observations[0].code, "reordered")
        self.assertFalse(check_file(path, strict_order=True).ok)

    def test_html_escapes_untrusted_values_and_includes_types(self):
        from rowcanary.reporting import html_report

        report = self.report("<script>alert(1)</script>", "<img src=x onerror=alert(1)>")
        document = html_report([report])
        self.assertNotIn("<script>", document)
        self.assertNotIn("<img src=x", document)
        self.assertIn("&lt;script&gt;", document)
        self.assertIn("Content-Security-Policy", document)
        self.assertIn("Expected", document)

    def test_batch_retains_errors_and_differences_with_stable_exit_codes(self):
        path = self.root / "clean.csv"
        write_probes(path)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = main(["batch", str(path), str(self.root / "absent.csv"), "--json"])
        self.assertEqual(result, 2)
        document = json.loads(output.getvalue())
        self.assertEqual(document["schema_version"], "1.0")
        self.assertEqual(len(document["results"]), 2)
        self.assertTrue(document["results"][0]["ok"])
        self.assertIn("error", document["results"][1])

    def test_reports_are_exclusive_and_deterministic(self):
        path = self.root / "clean.csv"
        write_probes(path)
        output = self.root / "report.html"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["check", str(path), "--report", str(output)]), 0)
            self.assertEqual(main(["check", str(path), "--report", str(output)]), 2)
        self.assertIn("<!doctype html>", output.read_text(encoding="utf-8"))

    def test_report_schema_validates_actual_reports(self):
        import importlib.resources
        import jsonschema

        schema = json.loads(
            importlib.resources.files("rowcanary").joinpath("report.schema.json").read_text()
        )
        report = self.report("001", "1").as_dict()
        jsonschema.validate(json.loads(json.dumps(report)), schema)

    def test_batch_exit_precedence_and_packaged_schema(self):
        import importlib.resources
        import jsonschema

        schema = json.loads(
            importlib.resources.files("rowcanary").joinpath("report.schema.json").read_text()
        )
        clean = self.root / "clean.json"
        changed = self.root / "changed.json"
        write_probes(clean)
        changed.write_text("[]", encoding="utf-8")
        for paths, status in (
            ([clean], 0),
            ([clean, changed], 1),
            ([self.root / "missing", changed], 2),
        ):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["batch", *map(str, paths), "--json"]), status)
            result = json.loads(output.getvalue())
            jsonschema.validate(result, schema)
            self.assertEqual(len(result["results"]), len(paths))
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate({"schema_version": "1.0", "ok": "yes"}, schema)

    def test_json_report_preserves_existing_files_and_matches_stdout(self):
        path = self.root / "clean.csv"
        write_probes(path)
        target = self.root / "report.json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["check", str(path), "--json", "--report", str(target)]), 0)
        original = target.read_bytes()
        self.assertEqual(json.loads(original), json.loads(stdout.getvalue()))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["check", str(path), "--json", "--report", str(target)]), 2)
        self.assertEqual(target.read_bytes(), original)

    def test_html_is_deterministic_and_does_not_interpret_input_names(self):
        from dataclasses import replace
        from rowcanary.reporting import html_report

        report = replace(self.report("a", "b"), input_path='<svg onload="alert(1)">')
        document = html_report([report])
        self.assertEqual(document, html_report([report]))
        self.assertNotIn("<svg", document)
        self.assertIn("&lt;svg", document)
        self.assertIn("default-src 'none'", document)

    def test_diagnostics_do_not_claim_unrelated_dates_or_rounding(self):
        for before, after in (
            ("2025-08-09", "08/10/2025"),
            ("word", "w"),
            ("1e999999999", "2e999999998"),
        ):
            issue = self.report(before, after).issues[0].as_dict()
            self.assertNotIn("date-representation-change", issue["classifications"])
            self.assertNotIn("numeric-rounding", issue["classifications"])

    def test_strict_order_cli_and_nonfailing_observation(self):
        path = self.root / "order.json"
        write_probes(path)
        path.write_text(json.dumps(json.loads(path.read_bytes())[::-1]), encoding="utf-8")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(main(["check", str(path), "--json", "--strict-order"]), 1)
        self.assertEqual(json.loads(stdout.getvalue())["issues"][0]["code"], "reordered")

    def test_report_rejects_dangling_symlink_without_creating_its_target(self):
        path = self.root / "clean.csv"
        write_probes(path)
        target = self.root / "absent.json"
        link = self.root / "report.json"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlink creation unavailable: {exc}")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["check", str(path), "--json", "--report", str(link)]), 2)
        self.assertFalse(target.exists())
