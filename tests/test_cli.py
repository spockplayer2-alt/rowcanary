import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from rowcanary.cli import main


class CliTests(unittest.TestCase):
    def test_demo(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["demo"]), 0)
        self.assertIn("FAIL  21/24", output.getvalue())

    def test_make_and_check(self):
        with tempfile.TemporaryDirectory() as t:
            probe = Path(t) / "probe.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["make", str(probe)]), 0)
                self.assertEqual(main(["check", str(probe), "--json"]), 0)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(main(["make", str(probe)]), 2)
            self.assertTrue(probe.exists())

    def test_unknown_file(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["check", "does-not-exist.csv"]), 2)


if __name__ == "__main__":
    unittest.main()
