# Formats and probe sets

`make` and `check` accept `--format csv|tsv|json|jsonl|xlsx` (default: auto).
Known extensions take precedence. Unknown extensions can be recognized from
JSON/JSONL, XLSX ZIP signatures or default control-column text. Ambiguous input
requires an explicit format. CSV separators remain explicit; TSV always uses tab.

```sh
rowcanary make probe.xlsx --probe-set extended
rowcanary check returned.xlsx --probe-set extended
rowcanary make probe.jsonl --probe-set numbers,dates
rowcanary check returned.jsonl --probe-set numbers,dates
```

The original 24 controls remain the default. `extended` adds timestamps, locale
decimals, normalization, CRLF, duplicate values and long IDs. A comma-separated
category list selects from extended controls: control, identifiers, numbers,
dates, keywords, whitespace, punctuation, unicode, formula. Use the same set and
custom-value file when generating and checking.

`--custom-values values.json` appends local controls. `--probe-set none` selects
only custom controls. IDs must be unique non-empty text. Values must be finite
JSON scalars (text, number, boolean, null); objects and arrays are not probes.

```json
[{"id":"account","value":"000009"}, {"id":"flag","value":false}]
```

JSON/JSONL retain scalar types and exact numeric tokens when reading; strings
never pass as numbers or booleans. CSV/TSV project custom scalars into text
(`None` becomes an empty cell, booleans become `True`/`False`), so their original
types cannot be verified there. XLSX preserves booleans, ordinary numeric values,
empty text and blank/null cells. Integers with more than 15 decimal digits must
be supplied as strings for XLSX to avoid silent precision loss on generation.
XLSX allows 32,767 characters per string; unsupported XML controls are rejected.
XLSX is read with openpyxl and defusedxml; no macros or formulas are executed.

UTF-8 is the default output; UTF-8/16/32 BOM input is detected. For legacy text,
use `--encoding cp1252` (only if all values are representable). Decoding is strict:
invalid bytes are errors, never silently replaced. In-cell CR/LF are preserved.
JSONL requires one object per non-blank line. Duplicate JSON keys are errors.
Empty JSONL is a valid export with all controls missing.

File, row and field limits apply to every adapter. XLSX expanded archives are
limited to 64 MiB and 1,000 entries, with one sheet and at most 1,024 columns.
It is a control-file audit, not an arbitrary workbook comparison tool.
