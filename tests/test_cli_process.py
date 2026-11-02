"""Exercise the installed-style module boundary, streams, and exit codes."""

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class CliProcessTests(unittest.TestCase):
    def run_cli(self, *arguments, cwd=None, encoding="utf-8"):
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = encoding
        environment["PYTHONPATH"] = str(PROJECT_ROOT)
        return subprocess.run(
            [sys.executable, "-m", "rowcanary", *map(str, arguments)],
            cwd=cwd or PROJECT_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding=encoding,
            timeout=15,
            check=False,
        )

    def make_probe(self, directory):
        path = Path(directory) / "probe.csv"
        result = self.run_cli("make", path)
        self.assertEqual(result.returncode, 0, result.stderr)
        return path

    def save_rows(self, path, rows):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["_rowcanary_id", "_rowcanary_value"])
            writer.writeheader()
            writer.writerows(rows)

    def test_module_version_help_and_usage_exit_codes(self):
        version = self.run_cli("--version")
        self.assertEqual((version.returncode, version.stdout.strip(), version.stderr),
                         (0, "rowcanary 0.1.0", ""))
        for command in ((), ("unknown",)):
            with self.subTest(command=command):
                usage = self.run_cli(*command)
                self.assertEqual(usage.returncode, 2)
                self.assertEqual(usage.stdout, "")
                self.assertIn("usage:", usage.stderr)
                self.assertNotIn("Traceback", usage.stderr)
        for command in (("--help",), ("make", "--help"), ("check", "--help")):
            with self.subTest(command=command):
                help_result = self.run_cli(*command)
                self.assertEqual(help_result.returncode, 0)
                self.assertIn("usage:", help_result.stdout)
                self.assertEqual(help_result.stderr, "")

    def test_make_defaults_to_current_directory_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            made = self.run_cli("make", cwd=directory)
            self.assertEqual(made.returncode, 0, made.stderr)
            path = Path(directory) / "rowcanary-probe.csv"
            original = path.read_bytes()
            duplicate = self.run_cli("make", cwd=directory)
            self.assertEqual(duplicate.returncode, 2)
            self.assertEqual(duplicate.stdout, "")
            self.assertTrue(duplicate.stderr.startswith("rowcanary: "))
            self.assertEqual(path.read_bytes(), original)

    def test_make_explains_spreadsheet_evaluation_risk(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("make", Path(directory) / "probe.csv")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WARNING", result.stdout)
            self.assertIn("evaluate", result.stdout)
            for prefix in ("'='", "'+'", "'-'"):
                self.assertIn(prefix, result.stdout)
            self.assertNotIn("harmless", result.stdout.lower())

    def test_make_reports_missing_parent_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("make", Path(directory) / "missing" / "probe.csv")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertTrue(result.stderr.startswith("rowcanary: "))
            self.assertNotIn("Traceback", result.stderr)

    def test_check_pass_difference_and_demo_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_probe(directory)
            passed = self.run_cli("check", path, "--json")
            self.assertEqual(passed.returncode, 0, passed.stderr)
            self.assertTrue(json.loads(passed.stdout)["ok"])
            self.assertEqual(passed.stderr, "")
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            rows[0]["_rowcanary_value"] = "changed"
            self.save_rows(path, rows)
            changed = self.run_cli("check", path)
            self.assertEqual(changed.returncode, 1, changed.stderr)
            self.assertIn("FAIL", changed.stdout)
            self.assertEqual(changed.stderr, "")
        demo = self.run_cli("demo")
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertIn("FAIL  21/24", demo.stdout)
        self.assertEqual(demo.stderr, "")

    def test_check_json_input_errors_are_json_on_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixtures = {
                "missing.csv": None,
                "invalid.csv": b"\xff\xfe\xff",
                "invalid.json": b"{broken",
                "wrong-shape.json": b'{"probe_id":"zeroes","value":"0012345"}',
            }
            for name, content in fixtures.items():
                with self.subTest(name=name):
                    path = root / name
                    if content is not None:
                        path.write_bytes(content)
                    result = self.run_cli("check", path, "--json")
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stderr, "")
                    payload = json.loads(result.stdout)
                    self.assertEqual(set(payload), {"error"})
                    self.assertIsInstance(payload["error"], str)
                    self.assertTrue(payload["error"])

    def test_human_report_escapes_untrusted_terminal_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_probe(directory)
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            rows.append({"_rowcanary_id": "extra\x1b[31m\u202e\nforged", "_rowcanary_value": "text"})
            self.save_rows(path, rows)
            result = self.run_cli("check", path)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("\x1b", result.stdout)
            self.assertNotIn("\u202e", result.stdout)
            self.assertNotIn("\nforged", result.stdout)
            self.assertIn(r"extra\x1b[31m\u202e\nforged", result.stdout)
            machine = self.run_cli("check", path, "--json")
            self.assertEqual(machine.returncode, 1, machine.stderr)
            issue = json.loads(machine.stdout)["issues"][0]
            self.assertEqual(issue["ident"], "extra\x1b[31m\u202e\nforged")

    def test_reports_survive_restricted_stdout_encodings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.make_probe(directory)
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            rows[0]["_rowcanary_value"] = "\u5371\u967a\U0001f4a5"
            rows.append({"_rowcanary_id": "\u8ffd\u52a0\U0001f4a5", "_rowcanary_value": "text"})
            self.save_rows(path, rows)
            for encoding in ("cp1252", "ascii"):
                with self.subTest(encoding=encoding, output="human"):
                    result = self.run_cli("check", path, encoding=encoding)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertEqual(result.stderr, "")
                    self.assertIn(r"\u5371\u967a\U0001f4a5", result.stdout)
                with self.subTest(encoding=encoding, output="json"):
                    result = self.run_cli("check", path, "--json", encoding=encoding)
                    self.assertEqual(result.returncode, 1, result.stderr)
                    self.assertEqual(result.stderr, "")
                    report = json.loads(result.stdout)
                    self.assertIn("\u5371\u967a\U0001f4a5", [i.get("actual") for i in report["issues"]])
                    self.assertIn("\u8ffd\u52a0\U0001f4a5", [i["ident"] for i in report["issues"]])

    def test_delimiter_is_explicit_for_make_and_check(self):
        with tempfile.TemporaryDirectory() as directory:
            for delimiter in (";", "\t", "|"):
                with self.subTest(delimiter=delimiter):
                    path = Path(directory) / f"probe-{ord(delimiter)}.csv"
                    made = self.run_cli("make", path, "--delimiter", delimiter)
                    self.assertEqual(made.returncode, 0, made.stderr)
                    self.assertIn("--delimiter", made.stdout)
                    with path.open(encoding="utf-8", newline="") as stream:
                        rows = list(csv.DictReader(stream, delimiter=delimiter))
                    self.assertEqual(len(rows), 24)
                    checked = self.run_cli("check", path, "--delimiter", delimiter, "--json")
                    self.assertEqual(checked.returncode, 0, checked.stderr)
                    self.assertTrue(json.loads(checked.stdout)["ok"])
                    wrong_delimiter = self.run_cli("check", path, "--json")
                    self.assertEqual(wrong_delimiter.returncode, 2)
                    self.assertIn("error", json.loads(wrong_delimiter.stdout))

    def test_invalid_delimiters_are_operational_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            for delimiter in ("", "||", "\r", "\n", '"'):
                with self.subTest(delimiter=delimiter):
                    path = Path(directory) / "probe.csv"
                    made = self.run_cli("make", path, "--delimiter", delimiter)
                    self.assertEqual(made.returncode, 2)
                    self.assertEqual(made.stdout, "")
                    self.assertNotIn("Traceback", made.stderr)
                    self.assertFalse(path.exists())
                    checked = self.run_cli("check", path, "--delimiter", delimiter, "--json")
                    self.assertEqual(checked.returncode, 2)
                    self.assertEqual(checked.stderr, "")
                    self.assertIn("error", json.loads(checked.stdout))

    def test_unicode_paths_do_not_break_make_or_error_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "\u8ffd\u52a0.csv"
            made = self.run_cli("make", path, encoding="ascii")
            self.assertEqual(made.returncode, 0, made.stderr)
            self.assertTrue(path.exists())
            self.assertIn(r"\u8ffd\u52a0.csv", made.stdout)
            missing = Path(directory) / "\u8ffd\u52a0-missing.csv"
            for json_output in (False, True):
                with self.subTest(json_output=json_output):
                    arguments = ["check", missing] + (["--json"] if json_output else [])
                    result = self.run_cli(*arguments, encoding="ascii")
                    self.assertEqual(result.returncode, 2)
                    self.assertNotIn("Traceback", result.stderr)
                    if json_output:
                        self.assertEqual(result.stderr, "")
                        self.assertIn(str(missing), json.loads(result.stdout)["error"])
                    else:
                        self.assertEqual(result.stdout, "")
                        self.assertIn(r"\u8ffd\u52a0-missing.csv", result.stderr)


if __name__ == "__main__":
    unittest.main()
