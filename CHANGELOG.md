# Changelog

## [0.4.0] - 2026-11-03

- Add `rowcanary serve` with a browser interface bound only to `127.0.0.1`.
- Generate/download controls and upload/check exports in all five formats,
  including custom controls, exact types and strict-order comparison.
- Download versioned JSON and escaped standalone HTML reports.
- Include labeled keyboard-accessible controls, responsive light/dark themes,
  the existing canary identity and no external resources or runtime dependencies.
- Enforce exact Host/Origin and per-session token checks, fixed static routes,
  request/upload limits, temporary files and no-store/security headers.

## [0.3.0] - 2026-11-03

- Add evidence-based classifications, severity, scalar types, observations,
  tentative possible causes and practical guidance without changing issue codes.
- Observe reordered rows without failing by default; add opt-in `--strict-order`.
- Add deterministic, escaped standalone HTML and JSON exports with exclusive
  creation through `check --report` and `batch --report`.
- Check multiple files with `batch`, retaining every result; operational errors
  take exit-code precedence over integrity differences.
- Package report JSON Schema 1.0 and validate real single and batch reports.
- Keep schema validation a test dependency; runtime dependencies are unchanged.

## [0.2.0] - 2026-11-02

- Generate and audit CSV, TSV, JSON, JSONL and single-sheet XLSX files.
- Add explicit format/encoding options, conservative content detection and
  UTF-16/32 BOM decoding without normalizing in-cell line breaks.
- Add deterministic extended/category probe sets and validated custom scalar
  controls, preserving the original default probe IDs and CLI commands.
- Preserve JSON/XLSX scalar types; refuse lossy XLSX integer/text generation.
- Store XLSX strings as literal text and reject returned formulas without
  executing them. Bound ZIP expansion and validate malformed workbooks.
- Write deterministic OpenXML/ZIP metadata and preserve embedded CR/LF/CRLF
  across platforms without passing generated data through text-mode writers.

## [0.1.1] - 2026-11-02

- Enforce the documented string-field safety bound in JSON, including nested
  extra data, so JSON cannot bypass the bound applied to CSV fields.
- Reject invalid API column names before reading a file, with an actionable error.
- Add regression coverage for both validation failures. Preserve all existing
  CLI commands, default probes and exact CR/LF comparisons.

## [0.1.0] - 2026-11-02

- Generate 24 deterministic, realistic edge-case CSV controls.
- Compare round-tripped CSV or JSON by stable probe IDs, regardless of row order.
- Detect dropped, duplicate, added, and changed control records.
- Print human-readable or JSON reports with appropriate exit codes.
- Include an isolated demonstration, automated tests and CI configuration.
- Preserve in-cell CR/LF/CRLF exactly and report blank CSV records.
- Support explicit CSV delimiters without automatic data normalization.
- Reject duplicate JSON keys and nonstandard constants; retain numeric token
  precision for diagnostics without accepting numbers as strings.
- Bound reads to 32 MiB, exported records to 100,000 and CSV fields to 128 Ki
  characters; refuse existing output symlinks, including dangling links.
- Escape untrusted terminal text and support restricted output encodings.
- Return structured JSON errors for `check --json` input and I/O failures.
- Clarify spreadsheet formula risks and the limits of a passing result.
- Reconstruct the original bird/table logo as self-contained SVG paths, with
  PNG exports and a 1280 × 640 social preview.
- Include package inspection, asset verification and regression tests.
