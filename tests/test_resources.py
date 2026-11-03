"""Real-file regressions for streaming, malformed inputs and resource budgets."""

import csv
import json
import tempfile
import tracemalloc
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

from rowcanary import ProbeFileError, check_file, write_probes
from rowcanary.core import Probe


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_line_format_parser_peak_does_not_scale_with_whole_file(self):
        from rowcanary.streaming import open_rows

        for fmt in ("csv", "tsv", "jsonl"):
            path = self.root / ("large." + fmt)
            with path.open("w", encoding="utf-8", newline="") as stream:
                if fmt == "jsonl":
                    record = (
                        json.dumps({"_rowcanary_id": "x", "_rowcanary_value": "a" * 2048}) + "\n"
                    )
                    stream.write(record * 3000)
                else:
                    delimiter = "\t" if fmt == "tsv" else ","
                    writer = csv.writer(stream, delimiter=delimiter)
                    writer.writerow(["_rowcanary_id", "_rowcanary_value"])
                    writer.writerows(("x", "a" * 2048) for _ in range(3000))
            tracemalloc.start()
            try:
                with open_rows(path, fmt, ",", "utf-8-sig") as (rows, _, selected):
                    count = sum(1 for _ in rows)
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            self.assertEqual((count, selected), (3000, fmt))
            self.assertLess(peak, 1024 * 1024, f"{fmt}: {peak} bytes")

    def test_buffered_reads_do_not_reserve_the_entire_file_limit_for_small_files(self):
        from rowcanary.core import _read_bytes

        path = self.root / "small.bin"
        path.write_bytes(b"x" * 8192)
        tracemalloc.start()
        try:
            data = _read_bytes(path)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertEqual(data, b"x" * 8192)
        self.assertLess(peak, 1024 * 1024)

    def test_streaming_preserves_line_breaks_across_buffer_boundaries(self):
        probe = Probe("boundary", "a" * 8190 + "\r\nb\rc\nd", "custom", "Exact text changed")
        for fmt, encoding in (("csv", "utf-8"), ("tsv", "utf-16"), ("jsonl", "utf-32")):
            path = self.root / ("boundary." + fmt)
            write_probes(path, probes=(probe,), encoding=encoding)
            self.assertTrue(check_file(path, probes=(probe,)).ok)
            path.unlink()  # The parser must release its file handle on Windows.

    def test_streaming_closes_on_parse_errors_and_enforces_row_bounds(self):
        for fmt in ("csv", "tsv", "jsonl"):
            path = self.root / ("rows." + fmt)
            write_probes(path)
            with patch("rowcanary.core.MAX_ROWS", 1):
                with self.assertRaisesRegex(ProbeFileError, "too many rows"):
                    check_file(path)
            path.unlink()

    def test_diagnostic_count_and_text_budgets_fail_without_partial_report(self):
        path = self.root / "extra.json"
        path.write_text(
            '[{"_rowcanary_id":"a","_rowcanary_value":"a"},{"_rowcanary_id":"b","_rowcanary_value":"b"}]',
            encoding="utf-8",
        )
        with patch("rowcanary.core.MAX_ISSUES", 1):
            with self.assertRaisesRegex(ProbeFileError, "diagnostic"):
                check_file(path)
        with patch("rowcanary.core.MAX_DIAGNOSTIC_CHARS", 1):
            with self.assertRaisesRegex(ProbeFileError, "diagnostic"):
                check_file(path)

    def test_json_numeric_tokens_have_a_field_bound(self):
        path = self.root / "number.json"
        path.write_text(
            '[{"_rowcanary_id":"plain","_rowcanary_value":' + "1" * 64 + "}]", encoding="utf-8"
        )
        with patch("rowcanary.core.MAX_FIELD_CHARS", 32):
            with self.assertRaisesRegex(ProbeFileError, "field.*safety limit"):
                check_file(path)

    def test_duplicate_xlsx_archive_members_are_rejected(self):
        path = self.root / "duplicate.xlsx"
        write_probes(path)
        with zipfile.ZipFile(path, "a") as archive:
            content = archive.read("[Content_Types].xml")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr("[Content_Types].xml", content)
        with self.assertRaisesRegex(ProbeFileError, "duplicate"):
            check_file(path)

    def test_jsonl_column_inference_does_not_consume_rows(self):
        path = self.root / "partial.jsonl"
        path.write_bytes(b'{"_rowcanary_id":"x"}\n{"_rowcanary_value":"a"}\n')
        report = check_file(path)
        self.assertEqual(
            [issue.code for issue in report.issues[:2]], ["missing-column", "missing-column"]
        )
        path.write_bytes(b'{"other":1}\n')
        with self.assertRaisesRegex(ProbeFileError, "Missing required columns"):
            check_file(path)

    def test_jsonl_multiple_objects_per_line_cannot_bypass_row_limits(self):
        from rowcanary.formats import load_rows
        from rowcanary.streaming import open_rows

        path = self.root / "multiple.jsonl"
        path.write_bytes(b"{},{}\n{},{}\n")
        with patch("rowcanary.core.MAX_ROWS", 2):
            with self.assertRaises(ProbeFileError):
                with open_rows(path, "jsonl", ",", "utf-8-sig") as (rows, _, _):
                    list(rows)
        path.write_bytes(b"{},{}\n")
        for adapter in ("streaming", "buffered"):
            with (
                self.subTest(adapter=adapter),
                self.assertRaisesRegex(ProbeFileError, "one object per line"),
            ):
                if adapter == "streaming":
                    with open_rows(path, "jsonl", ",", "utf-8-sig") as (rows, _, _):
                        list(rows)
                else:
                    load_rows(path, "jsonl", ",", "utf-8-sig")
