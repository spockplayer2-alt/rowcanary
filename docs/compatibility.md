# Compatibility evidence matrix

These are observed controls, not certifications or guarantees for other records,
application versions, locales or workflows. A failed native profile is evidence
that the controls changed, not a reason to adjust the expected values.

| Evidence | Profile | Result | Scope |
| --- | --- | --- | --- |
| Synthetic | CSV/TSV/JSON/JSONL/XLSX, extended controls | 35/35 each | RowCanary adapters only |
| Synthetic | UTF-8 BOM, UTF-16 CSV/TSV/JSONL, UTF-32 JSON, semicolon CSV | 35/35 each | Encoding/dialect fixtures |
| Synthetic | Intentional changes, reordering, missing/extra/duplicate IDs | Expected 6 issues + reorder observation | Simulated changes, no native-app claim |
| Synthetic | JSON type inference simulation | Expected 4 changes | Simulated scalar conversions |
| Native Excel | 16.0 build 20527, 32-bit, OpenText text columns | **33/35; FAIL** | This controlled automation profile |
| Native Excel | Same build, OpenText automatic inference | **20/35; FAIL** | This controlled automation profile |
| Google Sheets / LibreOffice / CRM | No live round trip run | **Unverified** | No compatibility claim |

## Reproduce the synthetic corpus

From a source checkout, choose a new empty directory:

```bash
python -m tools.compatibility new-corpus
python -m unittest discover -s tests -p test_compatibility.py -v
```

The checked-in corpus is under `examples/compatibility/`. Its manifest records
literal expected issue IDs/codes, parser settings and SHA-256 hashes. The builder
does not invoke the comparator to generate expectations. Tests rebuild twice,
check exact bytes/hashes and audit every fixture. Native outputs have a separate
manifest and are never presented as synthetic rebuilds.

## Native Excel observation — 2026-11-03

Input: the same 35 extended synthetic controls as `clean.csv`; the native manifest
records the exact input hash. A dedicated hidden Excel automation instance ran
with macros disabled and only its own synthetic workbook. No existing workbook
was opened or edited. The owned application/workbooks closed after the run; no
Excel process remained afterward.

```powershell
python -m rowcanary make excel-input.csv --probe-set extended
pwsh -NoProfile -File tools/excel-roundtrip.ps1 -InputCsv excel-input.csv -OutputDirectory new-excel-results
python -m rowcanary batch new-excel-results/text.csv new-excel-results/automatic.csv --probe-set extended --delimiter ";" --json
```

The script stages a byte-identical `.txt` copy and invokes `OpenText` with UTF-8,
explicit comma and double-quote qualification. The text profile assigns both
columns `xlTextFormat` and verifies that no formula was imported. Automatic
inference uses the general column format; the controlled `=1+1` probe may evaluate
to `2`. It contains no external or executable formula payload. `SaveAs` uses
`xlCSVUTF8`; this installation exported semicolons and a UTF-8 BOM. The script
records the actual regional separator and build and refuses existing outputs.

Text import changed the `newline` and `crlf` controls and produced two unexpected
rows (`line two"` and `beta"`): 33/35 values survived, 4 issues. Automatic
inference preserved 20/35 values and produced 18 issues, including changed numeric
representations, formula output, line breaks and the `false` ID becoming `FALSE`.
Raw outputs are retained in `examples/compatibility/excel/` with their hashes.

An initial direct `.csv` OpenText attempt did not yield the two expected headers;
it is retained only as local investigation evidence. The reusable script now
asserts both headers and uses the explicit text-import path. These observations
do not describe Excel's GUI, Power Query or every CSV-open path. Exact locale,
import mode and export settings matter. Do not normalize outputs to make a
profile pass.
