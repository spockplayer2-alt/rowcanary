# Changelog

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
