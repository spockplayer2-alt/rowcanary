import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rowcanary.core import ID_COLUMN, VALUE_COLUMN, ProbeFileError, check_file


class StabilizationTests(unittest.TestCase):
    def test_json_string_fields_enforce_the_same_bound_as_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "export.json"
            for value in ("x" * 33, {"nested": "x" * 33}, ["x" * 33]):
                path.write_text(
                    json.dumps([{ID_COLUMN: "plain", VALUE_COLUMN: value}]), encoding="utf-8"
                )
                with patch("rowcanary.core.MAX_FIELD_CHARS", 32):
                    with self.assertRaisesRegex(ProbeFileError, "field.*limit"):
                        check_file(path)

    def test_invalid_column_names_are_rejected_before_io(self):
        for name in ("", None, 123):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ProbeFileError, "column.*non-empty"):
                    check_file(Path("absent.csv"), id_column=name)


if __name__ == "__main__":
    unittest.main()
