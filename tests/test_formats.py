import json
import tempfile
import unittest
import zipfile
import time
from pathlib import Path

from rowcanary import check_file, write_probes
from rowcanary.core import PROBES, Probe, ProbeFileError


class FormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_all_five_formats_preserve_default_probes(self):
        for fmt in ("csv", "tsv", "json", "jsonl", "xlsx"):
            with self.subTest(fmt=fmt):
                path = self.root / ("probe." + fmt)
                write_probes(path, file_format=fmt)
                self.assertTrue(check_file(path).ok)

    def test_explicit_format_and_content_detection(self):
        path = self.root / "export.data"
        write_probes(path, file_format="jsonl")
        self.assertTrue(check_file(path).ok)
        self.assertTrue(check_file(path, file_format="jsonl").ok)

    def test_utf16_bom_and_explicit_legacy_encoding(self):
        for encoding in ("utf-16", "cp1252"):
            path = self.root / (encoding + ".csv")
            subset = tuple(p for p in PROBES if p.ident in ("plain", "accent"))
            write_probes(path, probes=subset, encoding=encoding)
            self.assertTrue(check_file(path, probes=subset, encoding=encoding).ok)
        self.assertTrue(check_file(self.root / "utf-16.csv", probes=subset).ok)

    def test_typed_custom_values_in_json_and_xlsx(self):
        probes = tuple(
            Probe(str(i), value, "custom", "Custom value changed")
            for i, value in enumerate([False, True, None, 123, 1.5, "=1+1", "0001"])
        )
        for fmt in ("json", "jsonl", "xlsx"):
            path = self.root / ("typed." + fmt)
            write_probes(path, probes=probes)
            self.assertTrue(check_file(path, probes=probes).ok)
        with zipfile.ZipFile(self.root / "typed.xlsx") as archive:
            sheet = archive.read("xl/worksheets/sheet1.xml")
            self.assertNotIn(b"<f>", sheet)
            self.assertIn(b"=1+1", sheet)

    def test_large_integers_in_xlsx_refuse_lossy_generation(self):
        with self.assertRaisesRegex(ProbeFileError, "integer.*text"):
            write_probes(self.root / "unsafe.xlsx", probes=(Probe("n", 10**20, "custom", ""),))
        self.assertFalse((self.root / "unsafe.xlsx").exists())

    def test_jsonl_rejects_invalid_lines_and_duplicate_keys(self):
        path = self.root / "bad.jsonl"
        for text in ("{}\n\n{}", '{"a":1,"a":2}', "[]", "{broken"):
            path.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ProbeFileError):
                check_file(path)

    def test_custom_probe_file_validates_ids_types_and_categories(self):
        from rowcanary.probes import select_probes

        path = self.root / "values.json"
        path.write_text(json.dumps([{"id": "custom-id", "value": "001"}]), encoding="utf-8")
        probes = select_probes("unicode", path)
        self.assertTrue(all(p.category == "unicode" for p in probes[:-1]))
        self.assertEqual(probes[-1].value, "001")
        path.write_text('[{"id":"plain","value":[]}]', encoding="utf-8")
        with self.assertRaises(ProbeFileError):
            select_probes("default", path)

    def test_extended_probe_set_is_deterministic_and_unique(self):
        from rowcanary.probes import select_probes

        probes = select_probes("extended")
        self.assertEqual(probes, select_probes("extended"))
        self.assertGreater(len(probes), len(PROBES))
        self.assertEqual(len({p.ident for p in probes}), len(probes))
        values = [p.value for p in probes]
        self.assertLess(len(set(values)), len(values))

    def test_xlsx_bytes_are_reproducible_across_clock_ticks(self):
        first = self.root / "first.xlsx"
        second = self.root / "second.xlsx"
        write_probes(first)
        time.sleep(1.1)
        write_probes(second)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_xlsx_zip_platform_metadata_is_reproducible_across_operating_systems(self):
        from unittest.mock import patch

        first, second = self.root / "windows.xlsx", self.root / "linux.xlsx"
        write_probes(first)
        with patch("zipfile.sys.platform", "linux"):
            write_probes(second)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_extended_probes_preserve_crlf_in_every_format(self):
        from rowcanary.probes import select_probes

        probes = select_probes("extended")
        for fmt in ("csv", "tsv", "json", "jsonl", "xlsx"):
            with self.subTest(fmt=fmt):
                path = self.root / ("extended." + fmt)
                write_probes(path, probes=probes)
                self.assertTrue(check_file(path, probes=probes).ok)

    def test_xlsx_formulas_are_never_evaluated_or_accepted_as_literals(self):
        from openpyxl import Workbook

        path = self.root / "formula.xlsx"
        book = Workbook()
        book.active.append(["_rowcanary_id", "_rowcanary_value"])
        book.active.append(["formula", "=1+1"])
        book.save(path)
        book.close()
        with self.assertRaisesRegex(ProbeFileError, "formulas"):
            check_file(path)

    def test_invalid_xlsx_and_xml_entities_are_input_errors(self):
        path = self.root / "malformed.xlsx"
        for data in (b"not a workbook", b"PK\x03\x04bad"):
            path.write_bytes(data)
            with self.assertRaises(ProbeFileError):
                check_file(path)
        write_probes(self.root / "valid.xlsx")
        with (
            zipfile.ZipFile(self.root / "valid.xlsx") as source,
            zipfile.ZipFile(path, "w") as target,
        ):
            for info in source.infolist():
                content = source.read(info.filename)
                if info.filename == "xl/workbook.xml":
                    content = b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///never-read">]><x>&e;</x>'
                target.writestr(info, content)
        with self.assertRaises(ProbeFileError):
            check_file(path)

    def test_xlsx_text_is_not_silently_truncated_on_generation(self):
        for value in ("x" * 32768, "abc\x01"):
            path = self.root / "unsafe.xlsx"
            with self.assertRaises(ProbeFileError):
                write_probes(path, probes=(Probe("custom", value, "custom", ""),))
            self.assertFalse(path.exists())

    def test_invalid_encoding_never_leaves_a_generated_file(self):
        path = self.root / "bad.csv"
        for encoding in ("not-a-codec", "ascii"):
            with self.assertRaises(ProbeFileError):
                write_probes(path, encoding=encoding)
            self.assertFalse(path.exists())

    def test_json_numbers_do_not_accept_boolean_or_string_coercion(self):
        probes = (Probe("custom", True, "custom", ""),)
        path = self.root / "bool.json"
        for value in (1, "True", None):
            path.write_text(
                json.dumps([{"_rowcanary_id": "custom", "_rowcanary_value": value}]),
                encoding="utf-8",
            )
            self.assertFalse(check_file(path, probes=probes).ok)
