# Reports and batch checks

```bash
rowcanary check exported.csv --json
rowcanary check exported.xlsx --report report.html
rowcanary batch exported.csv exported.json --json --report batch.json
rowcanary check reordered.csv --strict-order
```

Reports use schema version `1.0`. The installed package includes
`rowcanary/report.schema.json` (JSON Schema draft 2020-12) for single reports
and batch envelopes. Read it with `importlib.resources.files('rowcanary')`.
Use your preferred schema validator; it is not a runtime dependency.

Each issue retains its existing `code`, `ident`, `reason`, `expected` and
`actual`. Additional fields describe severity, observable classifications,
expected/actual scalar types, tentative possible causes and guidance. Display
values remain strings; types distinguish a literal `null` from JSON null.
Classifications never affect exact matching. A shorter prefix alone does not
establish rounding. `numeric-rounding` means consistency with decimal half-even
rounding to the returned precision, not proof that an application rounded it.
Date classifications require a shared possible calendar date; ambiguous dates
remain ambiguous. No classification identifies which application caused damage.

Reordering is an informational observation and does not fail a normal check.
With `--strict-order`, it becomes an error, even when all values survive.
Structural and value differences have error severity. There is no inferred
confidence score or guarantee about records beyond the controls.

Batch mode processes inputs in command order and retains input errors alongside
successful checks and integrity differences. It shares `check` format, encoding,
column, probe-set and delimiter options. Exit codes are:

| Code | Single check | Batch check |
| --- | --- | --- |
| 0 | All controls preserved | Every input passed |
| 1 | Readable input with differences | At least one difference, no input error |
| 2 | Usage, input or output error | Any usage, input or output error |

`--report` accepts `.json` or `.html`. Files are created exclusively, refusing
existing paths and symlinks. Choose a new filename on each run. HTML contains
escaped text, an embedded stylesheet and a restrictive Content Security Policy,
without scripts, network resources or timestamps. JSON and HTML preserve the
same observations. Treat reports as potentially sensitive because they include
input paths and control values. No report or input is uploaded.

For compatibility, a single `check --json` operational failure still emits
`{"error": "..."}` with exit 2; this legacy error object is outside the successful
report schema. Batch input errors have both `input` and `error` inside `results`.
