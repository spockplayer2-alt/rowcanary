import csv
import json
import tempfile
import unittest
from pathlib import Path

from rowcanary.core import (
    PROBES,
    ID_COLUMN,
    VALUE_COLUMN,
    ProbeFileError,
    check_file,
    write_probes,
)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.probe = self.root / "test.csv"
        write_probes(self.probe)

    def _csv_rows(self):
        with self.probe.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _save_csv(self, rows, *, fieldnames=(ID_COLUMN, VALUE_COLUMN)):
        output = self.root / "out.csv"
        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return output

    def test_clean_csv(self):
        report = check_file(self.probe)
        self.assertTrue(report.ok)
        self.assertEqual(report.passed, len(PROBES))

    def test_make_never_overwrites(self):
        with self.assertRaises(FileExistsError):
            write_probes(self.probe)

    def test_csv_reordered_and_extra_column(self):
        rows = self._csv_rows()[::-1]
        for row in rows:
            row["other"] = "ok"
        report = check_file(self._save_csv(rows, fieldnames=("other", ID_COLUMN, VALUE_COLUMN)))
        self.assertTrue(report.ok)

    def test_find_modified_and_missing_values(self):
        rows = self._csv_rows()
        rows = [r for r in rows if r[ID_COLUMN] != "emoji"]
        next(r for r in rows if r[ID_COLUMN] == "zeroes")[VALUE_COLUMN] = "12345"
        report = check_file(self._save_csv(rows))
        self.assertEqual(report.passed, len(PROBES) - 2)
        self.assertEqual({i.code for i in report.issues}, {"changed", "missing"})

    def test_find_duplicates_and_extra_rows(self):
        rows = self._csv_rows()
        rows.append(dict(rows[0]))
        rows.append({ID_COLUMN: "unknown", VALUE_COLUMN: "no"})
        report = check_file(self._save_csv(rows))
        self.assertEqual({i.code for i in report.issues}, {"duplicate", "unexpected"})

    def test_json_round_trip(self):
        output = self.root / "export.json"
        output.write_text(json.dumps(self._csv_rows(), ensure_ascii=False), encoding="utf-8")
        self.assertTrue(check_file(output).ok)

    def test_json_number_coercion(self):
        rows = self._csv_rows()
        next(r for r in rows if r[ID_COLUMN] == "large-int")[VALUE_COLUMN] = 123456789
        output = self.root / "export.json"
        output.write_text(json.dumps(rows), encoding="utf-8")
        self.assertEqual(check_file(output).issues[0].ident, "large-int")

    def test_column_renames(self):
        rows = [{"id": r[ID_COLUMN], "value": r[VALUE_COLUMN]} for r in self._csv_rows()]
        path = self._save_csv(rows, fieldnames=("id", "value"))
        self.assertTrue(check_file(path, id_column="id", value_column="value").ok)

    def test_bom(self):
        self.probe.write_bytes(b"\xef\xbb\xbf" + self.probe.read_bytes())
        self.assertTrue(check_file(self.probe).ok)

    def test_malformed_csv(self):
        path = self.root / "bad.csv"
        path.write_text(f'{ID_COLUMN},{VALUE_COLUMN}\nfoo,"unterminated\n', encoding="utf-8")
        with self.assertRaises(ProbeFileError):
            check_file(path)

    def test_extra_csv_field(self):
        path = self.root / "bad.csv"
        path.write_text(f"{ID_COLUMN},{VALUE_COLUMN}\nfoo,bar,baz\n", encoding="utf-8")
        with self.assertRaises(ProbeFileError):
            check_file(path)

    def test_bad_extension(self):
        with self.assertRaises(ProbeFileError):
            check_file(self.root / "bad.bin")

    def test_json_null_is_not_empty_string(self):
        rows = self._csv_rows()
        next(r for r in rows if r[ID_COLUMN] == "empty")[VALUE_COLUMN] = None
        output = self.root / "out.json"
        output.write_text(json.dumps(rows), encoding="utf-8")
        self.assertIn("empty", [i.ident for i in check_file(output).issues])

    def test_json_syntax_error(self):
        path = self.root / "out.json"
        path.write_text("[not json]", encoding="utf-8")
        with self.assertRaises(ProbeFileError):
            check_file(path)

    def test_file_size_limit(self):
        path = self.root / "out.csv"
        with path.open("wb") as stream:
            stream.truncate(32 * 1024 * 1024 + 1)
        with self.assertRaisesRegex(ProbeFileError, "safety limit"):
            check_file(path)

    def test_unsupported_json_root(self):
        path = self.root / "out.json"
        path.write_text("{}", encoding="utf-8")
        with self.assertRaises(ProbeFileError):
            check_file(path)

    def test_missing_columns(self):
        path = self.root / "out.csv"
        path.write_text("id,value\na,b\n", encoding="utf-8")
        with self.assertRaises(ProbeFileError):
            check_file(path)

    def test_report_json_serialization(self):
        self.assertEqual(check_file(self.probe).as_dict()["ok"], True)


if __name__ == "__main__":
    unittest.main()
