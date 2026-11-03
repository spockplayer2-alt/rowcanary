# Resource behavior and reproducible measurements

CSV, TSV and JSONL use single-pass row iterators over a bounded binary reader.
Decoding uses `newline=""`, preserving embedded CR, LF and CRLF across buffer
boundaries. JSON arrays and XLSX use the existing bounded buffered adapters.
The control definitions, known IDs and final report still require memory;
streaming does not make the entire comparison constant-memory.

Run this from the source checkout with its dependencies installed:

```bash
python -m tools.benchmark --rows 10000 --width 256
```

The tool generates isolated synthetic fixtures, measures the buffered parser,
the selected parser and the full exact comparison, then deletes its fixtures.
It reports `perf_counter` elapsed seconds and `tracemalloc` peak Python
allocations. Fixture construction and pre-existing probes are excluded. Imports
are warmed. These are illustrative measurements, not process RSS, maximum
memory guarantees, cold-start latency or application compatibility evidence.

Windows / Python 3.14.0, 10,000 controls with 256-character CRLF values:

These measurements were recorded for v0.5.0. Starting in v0.6.0, generated XLSX
uses uncompressed ZIP members for cross-runtime reproducibility; its file size
differs from the historical XLSX row below. Re-run the tool for current costs.

| Format | Input bytes | Buffered parser peak | Selected parser peak | Full comparison peak | Comparison seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| CSV | 2,708,922 | 21,660,058 | 184,842 | 1,594,154 | 0.188 |
| TSV | 2,708,922 | 21,660,058 | 184,730 | 1,571,435 | 0.150 |
| JSON | 3,288,893 | 12,058,119 | 12,068,250 | 12,068,407 | 0.130 |
| JSONL | 3,138,890 | 25,373,500 | 164,582 | 1,565,383 | 0.289 |
| XLSX | 138,610 | 7,477,364 | 7,446,774 | 7,445,851 | 1.664 |

The buffered baseline uses the existing adapter and materializes all records;
the selected parser streams line formats. JSON/XLSX peaks are similar because
their parsing architecture is unchanged. Every full comparison passed all
10,000 controls. Repeat locally for your interpreter and environment.

Regression tests separately consume 3,000 rows of 2,048-character values in
CSV/TSV/JSONL with a traced parser peak below 1 MiB. An 8 KiB buffered read also
stays below 1 MiB, avoiding the previous full-limit reservation. Tests verify
row/field/byte limits, buffer-boundary CRLF, early error closure, diagnostic
budgets, malformed archives and request framing. See [limits](limitations.md)
for the actual enforced boundaries.
