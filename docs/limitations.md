# Scope and limits

RowCanary checks observable exported controls. It cannot prove that unrelated
records survived, diagnose an application's internals, or verify an import-only
system without export/read-back access. Run controls through the same process
and settings as the data you want to protect, using isolated test records.

## Input contract

- CSV: UTF-8, optional leading BOM, a unique header row, comma delimiter unless
  explicitly selected with `--delimiter`. Named extra columns and reordered
  records are allowed. Extra fields beyond the header are malformed. Short
  records retain absent values as missing data. Blank records are audited.
- JSON: UTF-8, optional leading BOM, one array of objects. Duplicate object keys,
  `NaN` and infinity constants are invalid. Bounded numeric tokens
  remain non-text values; comparison never rounds or converts them into strings.
- Both generated column names must survive, or be selected with `--id-column`
  and `--value-column`. These options must name different columns.
- A valid empty array or header-only CSV reports missing controls. Empty files
  and malformed documents are input errors. Per-record missing columns are
  reported; an export lacking the required column names entirely is invalid.
- Text is compared exactly. Only the initial UTF-8 BOM is removed; spaces,
  Unicode normalization forms and in-cell CR/LF/CRLF are preserved. CSV record
  separators and JSON escape spelling are representation details, not values.
- See [formats](formats.md) for TSV, JSONL, XLSX and explicit legacy encodings.
  XML and direct database connections are unsupported. CSV follows Python's
  `csv` parsing rules with strict quoted-field handling; it is not a general
  validator for every CSV dialect or external system's schema.

## Resource limits

- At most 32 MiB of file bytes; the read itself is bounded, not just a preceding
  size check.
- At most 100,000 exported records, including blank CSV records.
- Text fields and JSON numeric tokens are limited to 128 Ki characters; the host interpreter's CSV parser
  can impose a lower limit if another library changes its global setting.
- CSV, TSV and JSONL are streamed with exact in-cell CR/LF/CRLF preservation.
  JSONL requires exactly one object on each nonblank line. Reads remain bounded
  even if the file grows after its initial size check; handles close on errors.
- JSON arrays are parsed in memory before their record count is checked. Parsed Python
  objects and reports take additional memory; 32 MiB is not a process-memory cap.
  Excessive JSON nesting is rejected when it exceeds the interpreter's parser
  limits. Use the utility on small control exports, not large production dumps.
- XLSX ZIPs allow at most 1,000 members and 64 MiB declared expansion; encrypted
  and duplicate members are rejected. Workbooks are read without formula
  evaluation, external-link retention or extraction to arbitrary filesystem paths.
- Reports allow at most 10,000 issues and 2 Mi characters of diagnostic text
  (including metadata). Exceeding either limit is an operational error, never
  a partial passing report. Reduce the control set and rerun.
- The local UI serializes operations, limits its listen backlog to four, and
  checks upload/request sizes and HTTP framing before reading bodies. It renders
  the first 200 diagnostic items; downloads retain every item within the limits.
  See [performance measurements](performance.md) and the [UI guide](web-ui.md).

## Interpretation and safety

- The demo intentionally changes its own fixtures. It does not test Excel,
  Google Sheets, a CRM or any other external application.
- Spreadsheet software may evaluate values beginning with `=`, `+` or `-`.
  CSV quoting offers no protection. RowCanary does not evaluate or sanitize
  formulas, and cannot tell whether they executed elsewhere.
- A passing count alone is insufficient: duplicates or extra rows can yield a
  failing report with 24/24 values preserved. Use `ok` or the exit status.
- Probe generation uses exclusive creation and refuses existing files and
  symlinks. It is not a transaction against concurrent replacement of parent
  directories or Windows reparse points by another local process.
- Diagnosis strings describe plausible changes, not proven causes. Intentional
  normalization is still a difference; an application's refusal to import the
  controls may reflect valid schema constraints.

See [the verification report](verification.md) for the environments actually
tested. Configuring CI does not establish cross-platform success.
