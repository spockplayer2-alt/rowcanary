<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img src="assets/logo.svg" width="156" height="132" alt="RowCanary: a canary shaped like a data table">
  </picture>
  <h1>RowCanary</h1>
  <p><strong>Detect silent data changes during import/export workflows.</strong></p>
  <p>Local Python CLI and browser UI · CSV, TSV, JSON, JSONL and XLSX · MIT</p>
</div>

An import can succeed while changing the data. A spreadsheet might turn
`00012345` into `12345`, an importer might interpret `5E12` as a number, or an
export might trim spaces that matter.

RowCanary creates 24 known control values. Pass them through the same workflow
as your data, export the result, and check which values survived. It reports
exact differences without trimming, numeric conversion or Unicode normalization.

## Demonstration

Run this from the source directory or after installation:

```console
$ python -m rowcanary demo
DEMO: three sample values were intentionally modified.
FAIL  21/24 test values preserved
  [changed] zeroes: Leading zeroes may have been removed
    expected: '00012345'
    actual:   '12345'
  [changed] scientific: Identifier may have been read as scientific notation
    expected: '5E12'
    actual:   '5000000000000'
  [changed] formula: Formula-like text was evaluated or rewritten
    expected: '=1+1'
    actual:   '2'
  Scope: only the provided control samples, not an entire real dataset.
Use 'rowcanary make probe.csv' to test a real import/export process.
```

The demo deliberately alters three values in a temporary directory. It exits
successfully when the demonstration runs; this is not an observed result from
Excel, Google Sheets, a CRM or another third-party application.

## Installation

Requires **Python 3.10 or newer**. Clone the repository and install locally:

```bash
git clone https://github.com/spockplayer2-alt/rowcanary.git
cd rowcanary
python -m pip install .
rowcanary --version
```

The version output is `rowcanary 0.6.0`. Use a virtual environment if your Python
installation requires one. If the console script is not on your `PATH`, use
`python -m rowcanary` with the Python interpreter that installed the package.
You can also run the module directly from the extracted source directory.

Alternatively, extract a downloaded source archive and run `python -m pip
install .` in the directory containing `pyproject.toml`. RowCanary has not been
published to PyPI. Do not assume that `pip install rowcanary` installs this project.

## Quick start

For the local browser interface, run `rowcanary serve --open`. It binds only to
`127.0.0.1`, uses no external resources and provides generation, upload/check,
light/dark themes and JSON/HTML downloads. Stop it with Ctrl+C. See the
[local UI guide](docs/web-ui.md) for privacy, limits and port options.

```bash
python -m rowcanary make probe.csv
python -m rowcanary check probe.csv
```

The second command checks the unmodified control file:

```text
PASS  24/24 test values preserved
  No changes detected in the test values.
  Scope: only the provided control samples, not an entire real dataset.
```

`make` refuses to overwrite an existing path. Choose a new filename for each
probe. The default filename, when omitted, is `rowcanary-probe.csv`.

**Spreadsheet safety:** the probes deliberately include strings beginning with
`=`, `+` and `-`, including `=1+1`. Spreadsheet software may evaluate them.
CSV quoting does not prevent formula evaluation. Use isolated test data and
inspect import settings before opening a probe. RowCanary itself never evaluates
formulas or executes input values. It does not sanitize arbitrary CSV files.

## Real-world usage

1. Generate a probe with `rowcanary make probe.csv`.
2. Import it into an isolated test area of the application being assessed.
3. Export those same records through the workflow you want to test.
4. Run `rowcanary check exported.csv`.

Keep `_rowcanary_id` and `_rowcanary_value` in the export. Records can be
reordered and additional named columns are allowed. The file should contain
only the probe records: other records are reported as unexpected.

If the application renames the columns:

```bash
rowcanary check exported.csv --id-column probe_id --value-column probe_value
```

For a semicolon-delimited workflow, explicitly choose the same delimiter for
generation and checking:

```bash
rowcanary make probe-semicolon.csv --delimiter ";"
rowcanary check exported.csv --delimiter ";"
```

There is no delimiter detection. A delimiter must be one UTF-8 character; tab
and pipe are also supported. Newline, carriage return, NUL and double quote
cannot be delimiters.

For JSON exports, use an array of objects with the same column names. Probe
values and IDs must remain **strings**; a JSON number, boolean or null is a
change, even if it looks similar when printed.
See [the complete JSON example](examples/clean.json).

```bash
rowcanary check exported.json --json
rowcanary check export.txt --format json --json
```

`--format` chooses the input parser; `--json` chooses the output report.
Without `--format`, a supported extension selects the parser; recognizable
content is used for files with unknown extensions.
`--delimiter` applies only to CSV.

| Exit code | Meaning |
| --- | --- |
| `0` | All controls match, or `make` / `demo` completed |
| `1` | The export was read, but integrity differences were found |
| `2` | Invalid input, command usage or an I/O error |

Normal JSON reports contain `schema_version`, `ok`, `passed`, `total`, `input`,
`issues` and non-failing `observations`.
For input or I/O errors, `check --json` writes `{"error": "..."}` to stdout and
exits 2. Argument-parsing errors use the usual stderr usage message. Human
reports escape terminal control characters and characters the output encoding
cannot represent. JSON escapes preserve the original Unicode values.

## Supported formats

| Operation | Format |
| --- | --- |
| Generate / check | CSV, TSV, JSON array of objects, JSONL, XLSX |
| Input encoding | UTF-8, UTF-16/32 with BOM; explicit `--encoding` for legacy text |
| Report | Human-readable text, versioned JSON or standalone HTML |

See [reports and batch checks](docs/reporting.md) for diagnostic fields, the
packaged JSON Schema, `--strict-order`, exclusive `--report` exports and batch
exit-code precedence.

The [compatibility matrix](docs/compatibility.md) separates deterministic parser
fixtures from actual Excel observations and unverified application workflows.

CSV quoting, embedded delimiters, escaped double quotes and embedded line
breaks are parsed. Line breaks **inside values** are compared exactly, including
the difference between LF, CR and CRLF. Record terminators may vary.

Use `--format` when the extension/content is ambiguous. XLSX uses one worksheet
and stores generated strings as literal text; returned formulas are refused
without evaluation. CSV/TSV can still be interpreted as formulas by external
spreadsheet applications. See [formats and custom probes](docs/formats.md) and
[the format and resource limits](docs/limitations.md).

## What it detects

The controls cover leading zeros, large integers, scientific notation, decimal
formatting, signed values, an international phone number, date/time-like text,
boolean/null-like strings, empty strings, spaces, tabs, newlines, punctuation,
Unicode, emoji and formula-like text.

It also reports missing, duplicated and unexpected records, non-text IDs and
missing required fields. A valid export with no records reports 24 missing
controls. Blank CSV records are reported rather than discarded. Duplicate CSV
headers, extra CSV fields, duplicate JSON object keys and nonstandard JSON
constants such as `NaN` are rejected as invalid input.

The preserved-value count measures matching known controls; extra or duplicate
rows can therefore produce a failing report showing `24/24`. Always use the
exit code or JSON `ok` field to decide whether the check passed.

## Limitations

A pass applies to **these controls in this specific workflow**. It does not
prove that an entire real dataset is intact, that formulas never ran, or that
an application is secure. A formula-like string being changed does not establish
why it changed. Intentional normalization is reported as a difference.

The application must support export or read-back and preserve the two probe
columns. A rejected import is inconclusive; its schema may legitimately reject
some controls. RowCanary has no application integrations and does not inspect
an importer's internal storage. See [limitations](docs/limitations.md) and
[security guidance](SECURITY.md).

## How it works

`make` writes the deterministic controls defined in `rowcanary/core.py`.
`check` reads the bounded UTF-8 export, matches records by their stable IDs and
compares each value as an exact string. Input order is irrelevant. JSON numeric
tokens retain their original spelling for diagnostics and remain numbers for
comparison; they are never silently converted into strings. The CLI wraps
these checks with text/JSON reports and exit codes.

All processing stays local. There are no network calls, accounts, telemetry or
third-party runtime packages.

## Development

From the source directory:

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python -m ruff check .
python -m build
python -m twine check dist/*
python tools/check_package.py dist
```

The tests use the standard library. GitHub Actions is configured for Ubuntu,
Windows and macOS on Python 3.10–3.14, plus package and static checks. The
[verification report](docs/verification.md) distinguishes executed checks from
pending hosted CI and third-party application tests.

The existing flat `rowcanary/` package is retained. `tests/` contains regression
tests, `examples/` contains clean and deliberately altered fixtures, and
`assets/` contains genuine vector masters and their PNG exports. See
[asset provenance and regeneration](assets/README.md).

## Contributing

Reproducible data-change cases and focused improvements are welcome. Read
[CONTRIBUTING.md](CONTRIBUTING.md). Use synthetic data in reports and never
include customer records or credentials. Report security issues through the
process in [SECURITY.md](SECURITY.md).

## License

RowCanary is distributed under the [MIT license](LICENSE). The social preview
uses outlined Noto Sans glyphs; its [font license](assets/FONT-LICENSE.txt) is
included.

Reusable JSON options, Python API and batch/Actions examples: [integration guide](docs/integrations.md).
