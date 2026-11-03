"""Build a deterministic synthetic corpus; never claims native-app evidence."""

import argparse
import csv
import hashlib
import io
import json
import unicodedata
from pathlib import Path

from rowcanary import write_probes
from rowcanary.probes import select_probes


def build(root):
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("Corpus destination must be empty")
    root.mkdir(parents=True, exist_ok=True)
    probes = select_probes("extended")
    fixtures = []

    def record(name, fmt, delimiter=",", issues=(), observations=()):
        fixtures.append(
            {
                "path": name,
                "format": fmt,
                "encoding": "utf-8-sig",
                "delimiter": delimiter,
                "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(),
                "ok": not issues,
                "issues": sorted([list(issue) for issue in issues]),
                "observations": list(observations),
            }
        )

    profiles = [
        ("clean." + fmt, fmt, "utf-8", ",") for fmt in ("csv", "tsv", "json", "jsonl", "xlsx")
    ]
    profiles += [
        ("utf8-bom.csv", "csv", "utf-8-sig", ","),
        ("utf16.csv", "csv", "utf-16", ","),
        ("utf16.tsv", "tsv", "utf-16", ","),
        ("semicolon.csv", "csv", "utf-8", ";"),
        ("utf32.json", "json", "utf-32", ","),
        ("utf16.jsonl", "jsonl", "utf-16", ","),
    ]
    for name, fmt, encoding, delimiter in profiles:
        write_probes(
            root / name, file_format=fmt, encoding=encoding, delimiter=delimiter, probes=probes
        )
        record(name, fmt, delimiter)

    rows = json.loads((root / "clean.json").read_bytes())
    for row in rows:
        ident = row["_rowcanary_id"]
        if ident == "zeroes":
            row["_rowcanary_value"] = "12345"
        elif ident == "crlf":
            row["_rowcanary_value"] = "alpha\nbeta"
        elif ident == "nfd":
            row["_rowcanary_value"] = unicodedata.normalize("NFC", row["_rowcanary_value"])
    rows = [row for row in rows if row["_rowcanary_id"] != "large-int"]
    rows = rows[::-1] + [
        next(row for row in rows if row["_rowcanary_id"] == "plain"),
        {"_rowcanary_id": "extra", "_rowcanary_value": "synthetic"},
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=["_rowcanary_id", "_rowcanary_value"])
    writer.writeheader()
    writer.writerows(rows)
    (root / "synthetic-changes.csv").write_bytes(stream.getvalue().encode("utf-8"))
    record(
        "synthetic-changes.csv",
        "csv",
        issues=(
            ("changed", "zeroes"),
            ("changed", "crlf"),
            ("changed", "nfd"),
            ("missing", "large-int"),
            ("duplicate", "plain"),
            ("unexpected", "extra"),
        ),
        observations=("reordered",),
    )

    rows = json.loads((root / "clean.json").read_bytes())
    values = {"zeroes": 12345, "large-int": 12345678901234567000, "bool": True, "empty": None}
    for row in rows:
        if row["_rowcanary_id"] in values:
            row["_rowcanary_value"] = values[row["_rowcanary_id"]]
    (root / "synthetic-types.json").write_bytes(
        (json.dumps(rows, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    record("synthetic-types.json", "json", issues=(("changed", ident) for ident in values))
    manifest = {
        "schema_version": "1.0",
        "provenance": "synthetic",
        "probe_set": "extended",
        "scope": "Deterministic parser fixtures; no native spreadsheet or CRM compatibility claim",
        "fixtures": fixtures,
    }
    (root / "manifest.json").write_bytes(
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    result = build(arguments.output)
    print(f"Built {len(result['fixtures'])} synthetic fixtures")
