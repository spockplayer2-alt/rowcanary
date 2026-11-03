"""Reproducible synthetic measurements; run as python -m tools.benchmark."""

import argparse
import importlib
import json
import platform
import tempfile
import time
import tracemalloc
from pathlib import Path

from rowcanary import check_file, write_probes
from rowcanary.core import MAX_FIELD_CHARS, MAX_ROWS, Probe
from rowcanary.formats import FORMATS, load_rows
from rowcanary.streaming import open_rows


def measure(operation):
    tracemalloc.start()
    started = time.perf_counter()
    try:
        count = operation()
        elapsed = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return {"rows": count, "elapsed_seconds": round(elapsed, 6), "python_peak_bytes": peak}


def benchmark(rows, width, formats):
    value = "x" * max(0, width - 2) + "\r\n"
    probes = tuple(Probe(f"bench-{i}", value, "benchmark", "Control changed") for i in range(rows))
    results = []
    with tempfile.TemporaryDirectory(prefix="rowcanary-benchmark-") as directory:
        for fmt in formats:
            if fmt == "xlsx":
                importlib.import_module("openpyxl")
            path = Path(directory) / ("synthetic." + fmt)
            write_probes(path, probes=probes)

            def buffered():
                records, _, _ = load_rows(path, fmt, ",", "utf-8-sig")
                return len(records)

            def selected_parser():
                with open_rows(path, fmt, ",", "utf-8-sig") as (records, _, _):
                    return sum(1 for _ in records)

            def compare():
                report = check_file(path, probes=probes)
                if not report.ok:
                    raise RuntimeError("Synthetic controls failed exact comparison")
                return report.passed

            result = {
                "format": fmt,
                "input_bytes": path.stat().st_size,
                "buffered_parser": measure(buffered),
                "selected_parser": measure(selected_parser),
                "full_comparison": measure(compare),
            }
            if any(
                result[key]["rows"] != rows
                for key in ("buffered_parser", "selected_parser", "full_comparison")
            ):
                raise RuntimeError("Benchmark parser lost rows")
            results.append(result)
    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "rows": rows,
        "value_characters": len(value),
        "measurement": "Warm Python traced allocations during each operation; excludes fixture/probe construction; not process RSS. Times are illustrative, not performance guarantees.",
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--width", type=int, default=128)
    parser.add_argument("--formats", nargs="+", choices=FORMATS, default=list(FORMATS))
    args = parser.parse_args()
    if not 1 <= args.rows <= MAX_ROWS or not 2 <= args.width <= MAX_FIELD_CHARS:
        parser.error("Rows/width exceed the supported bounds")
    print(json.dumps(benchmark(args.rows, args.width, args.formats), indent=2))


if __name__ == "__main__":
    main()
