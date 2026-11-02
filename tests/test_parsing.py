import csv
import io
import json
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from rowcanary.core import (
    ID_COLUMN, PROBES, VALUE_COLUMN, ProbeFileError, check_file, write_probes,
)


class ParsingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.probe = self.root / "probe.csv"
        write_probes(self.probe)

    def _rows(self):
        return [{ID_COLUMN: p.ident, VALUE_COLUMN: p.value} for p in PROBES]

    def _json(self, rows):
        output = self.root / "export.json"
        output.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        return output

    def _csv(self, rows):
        output = self.root / "export.csv"
        with output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=(ID_COLUMN, VALUE_COLUMN))
            writer.writeheader()
            writer.writerows(rows)
        return output

    def test_changed_embedded_cr_and_crlf_are_not_normalized(self):
        for changed in ("line one\rline two", "line one\r\nline two"):
            with self.subTest(changed=repr(changed)):
                rows = self._rows()
                next(row for row in rows if row[ID_COLUMN] == "newline")[VALUE_COLUMN] = changed
                report = check_file(self._csv(rows))
                self.assertFalse(report.ok)
                self.assertEqual([(i.code, i.ident, i.actual) for i in report.issues],
                                 [("changed", "newline", changed)])

    def test_blank_csv_records_are_detected(self):
        with self.probe.open("ab") as stream:
            stream.write(b"\r\n")
        report = check_file(self.probe)
        self.assertFalse(report.ok)
        self.assertEqual([issue.code for issue in report.issues], ["missing-column"])

    def test_read_limit_still_applies_when_stat_is_stale(self):
        byte_count = len(self.probe.read_bytes())
        stale = SimpleNamespace(st_mode=stat.S_IFREG, st_size=0)
        with patch("rowcanary.core.MAX_BYTES", byte_count - 1):
            with patch.object(Path, "stat", return_value=stale):
                with self.assertRaisesRegex(ProbeFileError, "safety limit"):
                    check_file(self.probe)

    def test_exact_byte_limit_is_accepted(self):
        with patch("rowcanary.core.MAX_BYTES", len(self.probe.read_bytes())):
            self.assertTrue(check_file(self.probe).ok)

    def test_explicit_csv_delimiters_preserve_every_probe(self):
        for index, delimiter in enumerate((";", "\t", "|")):
            with self.subTest(delimiter=repr(delimiter)):
                output = self.root / f"delimited-{index}.csv"
                write_probes(output, delimiter=delimiter)
                self.assertTrue(check_file(output, delimiter=delimiter).ok)
                self.assertIn(f"{ID_COLUMN}{delimiter}{VALUE_COLUMN}".encode(), output.read_bytes())

    def test_delimiter_is_not_detected_automatically(self):
        output = self.root / "semicolon.csv"
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, delimiter=";", fieldnames=(ID_COLUMN, VALUE_COLUMN))
        writer.writeheader()
        writer.writerows(self._rows())
        output.write_bytes(stream.getvalue().encode("utf-8"))
        with self.assertRaises(ProbeFileError):
            check_file(output)

    def test_invalid_delimiter_does_not_create_an_output(self):
        for index, delimiter in enumerate(("", "::", "\r", "\n", "\0", '"', "\ud800", None, 1)):
            with self.subTest(delimiter=repr(delimiter)):
                output = self.root / f"invalid-{index}.csv"
                with self.assertRaises(ProbeFileError):
                    write_probes(output, delimiter=delimiter)
                self.assertFalse(output.exists())

    def test_invalid_check_delimiter_is_a_file_error(self):
        with self.assertRaises(ProbeFileError):
            check_file(self.probe, delimiter="::")

    def test_json_ignores_csv_delimiter(self):
        self.assertTrue(check_file(self._json(self._rows()), delimiter=";").ok)

    def test_empty_json_array_reports_all_controls_missing(self):
        report = check_file(self._json([]))
        self.assertFalse(report.ok)
        self.assertEqual(report.passed, 0)
        self.assertEqual(len(report.issues), 24)
        self.assertEqual({issue.code for issue in report.issues}, {"missing"})

    def test_first_json_row_missing_a_field_is_audited(self):
        rows = self._rows()
        del rows[0][VALUE_COLUMN]
        report = check_file(self._json(rows))
        self.assertEqual(report.passed, 23)
        self.assertEqual({issue.code for issue in report.issues}, {"missing-column", "missing"})
        self.assertIn("plain", [issue.ident for issue in report.issues])

    def test_json_duplicate_keys_are_rejected(self):
        output = self._json(self._rows())
        text = output.read_text(encoding="utf-8")
        text = text.replace('"_rowcanary_value": "normal text"',
                            '"_rowcanary_value": "changed", "_rowcanary_value": "normal text"', 1)
        output.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ProbeFileError, "duplicate"):
            check_file(output)

    def test_nonstandard_json_numeric_constants_are_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                output = self._json(self._rows())
                text = output.read_text(encoding="utf-8").replace('"normal text"', token, 1)
                output.write_text(text, encoding="utf-8")
                with self.assertRaises(ProbeFileError):
                    check_file(output)

    def test_numeric_json_tokens_keep_precision_but_never_pass_as_text(self):
        for ident, token in (("large-int", "12345678901234567890"),
                             ("decimal", "19.9900"), ("scientific", "5E12"),
                             ("scientific", "1e9999"), ("large-int", "9" * 5000)):
            with self.subTest(ident=ident, token=token[:30]):
                output = self._json(self._rows())
                original = next(p.value for p in PROBES if p.ident == ident)
                text = output.read_text(encoding="utf-8").replace(json.dumps(original), token, 1)
                output.write_text(text, encoding="utf-8")
                try:
                    report = check_file(output)
                except Exception as exc:
                    self.fail(f"Valid numeric JSON token crashed: {type(exc).__name__}")
                self.assertEqual([(i.code, i.ident, i.actual) for i in report.issues],
                                 [("changed", ident, token)])

    def test_json_id_types_are_never_coerced_to_text(self):
        for ident in (12, 1.5, True, None, [], {}):
            with self.subTest(ident=repr(ident)):
                rows = self._rows()
                rows[0][ID_COLUMN] = ident
                report = check_file(self._json(rows))
                self.assertEqual(report.passed, 23)
                self.assertEqual({i.code for i in report.issues}, {"invalid-id", "missing"})

    def test_json_value_types_are_never_coerced_to_text(self):
        for value in (True, None, [], {}, 0):
            with self.subTest(value=repr(value)):
                rows = self._rows()
                rows[0][VALUE_COLUMN] = value
                report = check_file(self._json(rows))
                self.assertEqual([(i.code, i.ident) for i in report.issues], [("changed", "plain")])

    def test_json_bom_reordered_rows_and_extra_columns_preserve_controls(self):
        rows = self._rows()[::-1]
        for row in rows:
            row["unrelated"] = {"nested": [1, True, None]}
        output = self._json(rows)
        output.write_bytes(b"\xef\xbb\xbf" + output.read_bytes())
        self.assertTrue(check_file(output).ok)

    def test_json_duplicate_keys_in_extra_columns_are_rejected(self):
        output = self._json(self._rows())
        text = output.read_text(encoding="utf-8").replace(
            '"normal text"', '"normal text", "extra": {"a": 1, "a": 2}', 1)
        output.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ProbeFileError, "duplicate"):
            check_file(output)

    def test_empty_and_invalid_utf8_files_are_operational_errors(self):
        for suffix in ("csv", "json"):
            for data in (b"", b" \t\r\n", b"\xff", b"\xc3(", b"\xef\xbb\xbf"):
                with self.subTest(suffix=suffix, data=data):
                    output = self.root / f"invalid.{suffix}"
                    output.write_bytes(data)
                    with self.assertRaises(ProbeFileError):
                        check_file(output)

    def test_invalid_json_structures_are_operational_errors(self):
        for document in ({}, None, "text", 1, [None], [[]], ["text"]):
            with self.subTest(document=repr(document)):
                with self.assertRaises(ProbeFileError):
                    check_file(self._json(document))

    def test_deeply_nested_json_is_a_file_error(self):
        output = self.root / "nested.json"
        output.write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
        with self.assertRaises(ProbeFileError):
            check_file(output)

    def test_json_missing_all_required_columns_is_a_file_error(self):
        with self.assertRaisesRegex(ProbeFileError, "required columns"):
            check_file(self._json([{"id": "plain", "value": "normal text"}]))

    def test_csv_duplicate_headers_and_bad_quoted_trailers_are_file_errors(self):
        for text in (f"{ID_COLUMN},{ID_COLUMN}\r\nplain,normal text\r\n",
                     f'{ID_COLUMN},{VALUE_COLUMN}\r\nplain,"normal text"suffix\r\n'):
            with self.subTest(text=text):
                output = self.root / "malformed.csv"
                output.write_bytes(text.encode("utf-8"))
                with self.assertRaises(ProbeFileError):
                    check_file(output)

    def test_header_only_csv_reports_all_controls_missing(self):
        report = check_file(self._csv([]))
        self.assertEqual(report.passed, 0)
        self.assertEqual(len(report.issues), 24)
        self.assertEqual({issue.code for issue in report.issues}, {"missing"})

    def test_csv_absent_value_differs_from_explicit_empty_string(self):
        output = self._csv(self._rows())
        output.write_bytes(output.read_bytes().replace(b"empty,\r\n", b"empty\r\n", 1))
        report = check_file(output)
        self.assertEqual([(i.code, i.ident, i.actual) for i in report.issues],
                         [("changed", "empty", "None")])

    def test_csv_field_limit_survives_host_global_limit_increase(self):
        rows = self._rows()
        rows[0][VALUE_COLUMN] = "x" * (128 * 1024 + 1)
        output = self._csv(rows)
        previous = csv.field_size_limit(256 * 1024)
        try:
            with self.assertRaisesRegex(ProbeFileError, "field.*limit"):
                check_file(output)
        finally:
            csv.field_size_limit(previous)

    def test_csv_and_json_row_limits_allow_exact_boundary(self):
        for suffix in ("csv", "json"):
            with self.subTest(suffix=suffix):
                save = self._csv if suffix == "csv" else self._json
                with patch("rowcanary.core.MAX_ROWS", 2):
                    report = check_file(save(self._rows()[:2]))
                    self.assertEqual(report.passed, 2)
                    with self.assertRaisesRegex(ProbeFileError, "too many rows"):
                        check_file(save(self._rows()[:3]))

    def test_blank_csv_records_count_toward_row_limit(self):
        output = self._csv(self._rows()[:2])
        with output.open("ab") as stream:
            stream.write(b"\r\n")
        with patch("rowcanary.core.MAX_ROWS", 2):
            with self.assertRaisesRegex(ProbeFileError, "too many rows"):
                check_file(output)

    def test_identical_id_and_value_columns_are_rejected(self):
        with self.assertRaises(ProbeFileError):
            check_file(self.probe, id_column=ID_COLUMN, value_column=ID_COLUMN)

    def test_explicit_format_supports_renamed_file_extensions(self):
        output = self.root / "roundtrip.dat"
        output.write_bytes(self.probe.read_bytes())
        self.assertTrue(check_file(output, file_format="csv").ok)

    def test_make_never_follows_existing_file_symlink(self):
        target = self.root / "original.txt"
        target.write_bytes(b"keep this content")
        link = self.root / "link.csv"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {type(exc).__name__}")
        with self.assertRaises(FileExistsError):
            write_probes(link)
        self.assertEqual(target.read_bytes(), b"keep this content")

    def test_make_never_follows_dangling_file_symlink(self):
        target = self.root / "absent.txt"
        link = self.root / "link.csv"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Symlinks unavailable: {type(exc).__name__}")
        with self.assertRaises(FileExistsError):
            write_probes(link)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
