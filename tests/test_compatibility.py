"""Portable compatibility corpus with literal expected results and provenance."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from rowcanary import check_file
from rowcanary.probes import select_probes


class CompatibilityTests(unittest.TestCase):
    def test_corpus_rebuilds_identical_bytes_and_has_no_native_app_claim(self):
        from tools.compatibility import build

        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "a", Path(directory) / "b"
            build(a)
            build(b)
            first = {p.name: p.read_bytes() for p in a.iterdir()}
            second = {p.name: p.read_bytes() for p in b.iterdir()}
            self.assertEqual(first, second)
            checked_in = Path(__file__).resolve().parents[1] / "examples" / "compatibility"
            self.assertEqual(
                first, {p.name: p.read_bytes() for p in checked_in.iterdir() if p.is_file()}
            )
            manifest = json.loads(first["manifest.json"])
            self.assertEqual(manifest["provenance"], "synthetic")
            self.assertGreaterEqual(len(manifest["fixtures"]), 12)

    def test_checked_in_corpus_matches_independently_recorded_outcomes(self):
        root = Path(__file__).resolve().parents[1] / "examples" / "compatibility"
        manifest = json.loads((root / "manifest.json").read_bytes())
        probes = select_probes("extended")
        for fixture in manifest["fixtures"]:
            with self.subTest(path=fixture["path"]):
                path = root / fixture["path"]
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), fixture["sha256"])
                report = check_file(
                    path,
                    probes=probes,
                    file_format=fixture["format"],
                    encoding=fixture["encoding"],
                    delimiter=fixture["delimiter"],
                )
                self.assertEqual(report.ok, fixture["ok"])
                self.assertEqual(
                    sorted([i.code, i.ident] for i in report.issues), fixture["issues"]
                )
                self.assertEqual([i.code for i in report.observations], fixture["observations"])

    def test_builder_refuses_nonempty_destinations(self):
        from tools.compatibility import build

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "keep.txt"
            existing.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                build(root)
            self.assertEqual(existing.read_bytes(), b"keep")

    def test_native_excel_evidence_matches_the_recorded_build_and_profile(self):
        root = Path(__file__).resolve().parents[1] / "examples" / "compatibility" / "excel"
        manifest = json.loads((root / "manifest.json").read_bytes())
        self.assertEqual(manifest["provenance"], "native-application-observation")
        self.assertEqual(manifest["application"], "Microsoft Excel")
        self.assertEqual(manifest["version"], "16.0")
        probes = select_probes("extended")
        for fixture in manifest["fixtures"]:
            path = root / fixture["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), fixture["sha256"])
            report = check_file(path, probes=probes, delimiter=fixture["delimiter"])
            self.assertEqual(report.passed, fixture["passed"])
            self.assertEqual(sorted([i.code, i.ident] for i in report.issues), fixture["issues"])
            self.assertFalse(report.ok)
