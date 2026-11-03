"""Public configuration contract and real CLI integration."""

import dataclasses
import json
import subprocess
import sys
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path

import jsonschema

from rowcanary import Config, Issue, Probe, ProbeFileError, load_config
from rowcanary import check_file, html_report, select_probes, write_probes


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "settings.json"

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "rowcanary", *map(str, args)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )

    def test_public_api_and_exact_relative_custom_controls(self):
        custom = [
            {"id": "crlf", "value": "a\r\nb\rc"},
            {"id": "large", "value": 9007199254740993},
            {"id": "null", "value": None},
        ]
        (self.root / "values.json").write_bytes(json.dumps(custom).encode())
        self.config.write_text(json.dumps({"probe_set": "none", "custom_values": "values.json"}))
        config = load_config(self.config)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            config.strict_order = True
        path = self.root / "controls.json"
        write_probes(path, **config.make_options())
        report = check_file(path, **config.check_options())
        self.assertTrue(report.ok)
        self.assertEqual(report.total, 3)
        self.assertIn("PASS", html_report([report]))
        self.assertIsInstance(select_probes()[0], Probe)
        self.assertTrue(dataclasses.is_dataclass(Issue))

    def test_reject_invalid_config_and_direct_options(self):
        documents = [
            "[]",
            '{"unknown":1}',
            '{"delimiter":",","delimiter":";"}',
            '{"strict_order":1}',
            '{"encoding":false}',
            '{"encoding":"absent-codec"}',
            '{"file_format":"exe"}',
            '{"delimiter":"\\n"}',
            '{"id_column":""}',
            '{"id_column":"x","value_column":"x"}',
            '{"probe_set":"absent"}',
            '{"custom_values":""}',
            '{"custom_values":12}',
            '{"schema_version":"2.0"}',
            '{"delimiter":NaN}',
            "[" * 1100,
            " " * 65537,
        ]
        for document in documents:
            with self.subTest(document=document[:70]):
                self.config.write_bytes(document.encode())
                with self.assertRaises(ProbeFileError):
                    load_config(self.config)
        for options in ({"strict_order": "false"}, {"delimiter": "xx"}, {"encoding": "xyz"}):
            with self.subTest(options=options), self.assertRaises(ProbeFileError):
                Config(**options)

    def test_real_cli_precedence_and_batch(self):
        self.config.write_text(
            json.dumps(
                {
                    "delimiter": ";",
                    "probe_set": "extended",
                    "strict_order": True,
                    "encoding": "utf-8-sig",
                }
            )
        )
        sample = self.root / "controls.csv"
        result = self.cli(
            "make", sample, "--config", self.config, "--delimiter", ",", "--probe-set", "default"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b",", sample.read_bytes().splitlines()[0])
        self.assertEqual(len(sample.read_bytes().decode("utf-8-sig").splitlines()) > 24, True)
        # Write reordered rows through the API to retain embedded line breaks.
        write_probes(self.root / "reordered.json", probes=tuple(reversed(select_probes())))
        strict = self.cli(
            "check",
            self.root / "reordered.json",
            "--config",
            self.config,
            "--probe-set",
            "default",
            "--json",
        )
        self.assertEqual(strict.returncode, 1, strict.stdout + strict.stderr)
        relaxed = self.cli(
            "batch",
            sample,
            self.root / "reordered.json",
            "--config",
            self.config,
            "--delimiter",
            ",",
            "--probe-set",
            "default",
            "--no-strict-order",
            "--json",
        )
        self.assertEqual(relaxed.returncode, 0, relaxed.stdout + relaxed.stderr)
        self.assertEqual(json.loads(relaxed.stdout)["results"][0]["total"], 24)
        invalid = self.cli("check", sample, "--config", self.root / "missing.json", "--json")
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("error", json.loads(invalid.stdout))

    def test_schema_and_shipped_example_agree(self):
        schema = json.loads(files("rowcanary").joinpath("config.schema.json").read_bytes())
        example = Path(__file__).resolve().parents[1] / "examples/config.json"
        document = json.loads(example.read_bytes())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(document, schema)
        self.assertIsInstance(load_config(example), Config)
        for document in ({"unknown": 1}, {"strict_order": 1}, {"delimiter": "xx"}):
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(document, schema)


if __name__ == "__main__":
    unittest.main()
