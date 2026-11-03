"""Human-friendly command-line interface for RowCanary."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from pathlib import Path
from typing import TextIO

from . import __version__
from .core import ProbeFileError, check_file, write_probes, ID_COLUMN, VALUE_COLUMN
from .formats import FORMATS
from .probes import select_probes
from .reporting import export_report


def _print_human(message: str, *, file: TextIO | None = None) -> None:
    """Keep untrusted text on one line and represent unsupported characters."""
    stream = file if file is not None else sys.stdout
    display = "".join(
        character if character.isprintable() else character.encode("unicode_escape").decode("ascii")
        for character in message
    )
    encoding = getattr(stream, "encoding", None) or "utf-8"
    print(display.encode(encoding, errors="backslashreplace").decode(encoding), file=stream)


def render_report(report, *, output_json: bool = False) -> None:
    if output_json:
        print(json.dumps(report.as_dict(), ensure_ascii=True, indent=2))
        return
    result = "PASS" if report.ok else "FAIL"
    _print_human(f"{result}  {report.passed}/{report.total} test values preserved")
    if report.issues:
        for issue in report.issues:
            _print_human(f"  [{issue.code}] {issue.ident}: {issue.reason}")
            if issue.expected is not None:
                _print_human(f"    expected: {issue.expected!r}")
            if issue.actual is not None:
                _print_human(f"    actual:   {issue.actual!r}")
    else:
        _print_human("  No changes detected in the test values.")
    for observation in report.observations:
        _print_human(f"  [{observation.severity}:{observation.code}] {observation.reason}")
    _print_human("  Scope: only the provided control samples, not an entire real dataset.")


def demo() -> int:
    with tempfile.TemporaryDirectory(prefix="rowcanary-") as directory:
        sample = Path(directory) / "probe.csv"
        altered = Path(directory) / "altered.csv"
        write_probes(sample)
        with sample.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        for row in rows:
            if row[ID_COLUMN] == "zeroes":
                row[VALUE_COLUMN] = "12345"
            elif row[ID_COLUMN] == "scientific":
                row[VALUE_COLUMN] = "5000000000000"
            elif row[ID_COLUMN] == "formula":
                row[VALUE_COLUMN] = "2"
        with altered.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=[ID_COLUMN, VALUE_COLUMN])
            writer.writeheader()
            writer.writerows(rows)
        print("DEMO: three sample values were intentionally modified.")
        render_report(check_file(altered))
        print("Use 'rowcanary make probe.csv' to test a real import/export process.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="rowcanary", description="Test whether an import/export process silently changes data."
    )
    parser.add_argument("--version", action="version", version=f"rowcanary {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    maker = sub.add_parser("make", help="Generate a deterministic file of edge-case test values")
    maker.add_argument("output", type=Path, nargs="?", default=Path("rowcanary-probe.csv"))
    maker.add_argument(
        "--delimiter", default=",", help="CSV field separator: one character (default: comma)"
    )
    checker = sub.add_parser("check", help="Audit an exported control file")
    checker.add_argument("input", type=Path)
    batch = sub.add_parser("batch", help="Audit several exports and retain every result")
    batch.add_argument("inputs", type=Path, nargs="+")
    for command in (maker, checker, batch):
        command.add_argument("--format", choices=("auto", *FORMATS), default="auto")
        command.add_argument(
            "--encoding",
            default="utf-8" if command is maker else "utf-8-sig",
            help="Text encoding (BOM encodings detected when checking)",
        )
        command.add_argument(
            "--probe-set",
            default="default",
            help="default, extended, none, or comma-separated categories",
        )
        command.add_argument(
            "--custom-values", type=Path, help="JSON array of custom {id, value} controls"
        )
    for command in (checker, batch):
        command.add_argument("--id-column", default=ID_COLUMN)
        command.add_argument("--value-column", default=VALUE_COLUMN)
        command.add_argument(
            "--delimiter", default=",", help="CSV field separator (default: comma)"
        )
        command.add_argument(
            "--json", action="store_true", help="Print a machine-readable JSON report"
        )
        command.add_argument(
            "--strict-order",
            action="store_true",
            help="Treat reordered rows as an integrity difference",
        )
        command.add_argument(
            "--report", type=Path, help="Create a new standalone .html or .json report"
        )
    sub.add_parser("demo", help="Run a self-contained example with intentionally broken values")
    args = parser.parse_args(argv)
    try:
        if args.command == "make":
            probes = select_probes(args.probe_set, args.custom_values)
            write_probes(
                args.output,
                delimiter=args.delimiter,
                file_format=args.format,
                encoding=args.encoding,
                probes=probes,
            )
            _print_human(f"Created {args.output} with {len(probes)} control rows.")
            _print_human("Import and export it, then run: rowcanary check <exported.csv>")
            if args.delimiter != ",":
                _print_human("Use the same --delimiter when checking the exported CSV.")
            _print_human(
                "WARNING: Values beginning with '=', '+', or '-' may be evaluated "
                "by spreadsheet software; use only in isolated test data."
            )
            return 0
        if args.command in ("check", "batch"):
            options = dict(
                file_format=args.format,
                id_column=args.id_column,
                value_column=args.value_column,
                delimiter=args.delimiter,
                encoding=args.encoding,
                probes=select_probes(args.probe_set, args.custom_values),
                strict_order=args.strict_order,
            )
            if args.command == "check":
                report = check_file(args.input, **options)
                if args.report:
                    export_report(args.report, [report])
                render_report(report, output_json=args.json)
                return 0 if report.ok else 1
            results = []
            status = 0
            for path in args.inputs:
                try:
                    report = check_file(path, **options)
                    results.append(report.as_dict())
                    status = max(status, 0 if report.ok else 1)
                    if not args.json:
                        _print_human(str(path))
                        render_report(report)
                except (ProbeFileError, OSError) as exc:
                    results.append({"input": str(path), "error": str(exc)})
                    status = 2
                    if not args.json:
                        _print_human(f"{path}: {exc}", file=sys.stderr)
            if args.report:
                export_report(args.report, results, batch=True)
            if args.json:
                print(
                    json.dumps(
                        {"schema_version": "1.0", "results": results}, ensure_ascii=True, indent=2
                    )
                )
            return status
        return demo()
    except (ProbeFileError, OSError) as exc:
        if args.command in ("check", "batch") and args.json:
            print(json.dumps({"error": str(exc)}, ensure_ascii=True, indent=2))
        else:
            _print_human(f"rowcanary: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
