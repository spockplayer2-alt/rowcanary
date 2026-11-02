"""Keep the README's actual CLI transcript from drifting."""

import contextlib
import io
import re
import unittest
from pathlib import Path

from rowcanary.cli import demo


class DocumentationTests(unittest.TestCase):
    def test_readme_demo_matches_actual_output(self):
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
        sample = re.search(r"```console\n\$ python -m rowcanary demo\n(.*?)```", readme, re.S)
        self.assertIsNotNone(sample)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(demo(), 0)
        self.assertEqual(sample.group(1), output.getvalue())


if __name__ == "__main__":
    unittest.main()
