# Python, configuration and automation

Supported public imports from `rowcanary` are `Probe`, `Issue`, `Report`,
`ProbeFileError`, `PROBES`, `ID_COLUMN`, `VALUE_COLUMN`, `write_probes`,
`check_file`, `select_probes`, `html_report`, `Config` and `load_config`.
Their existing arguments and issue codes remain compatible through 1.x.
Underscore helpers and other modules are implementation details. New optional
fields/codes may be added; consumers should tolerate them. Report JSON and
configuration schemas are packaged as `report.schema.json` and
`config.schema.json`, with schema version `1.0` independent of package version.

```python
from pathlib import Path
from rowcanary import load_config, write_probes, check_file

config = load_config(Path("examples/config.json"))
write_probes(Path("controls.json"), **config.make_options())
report = check_file(Path("controls.json"), **config.check_options())
assert report.ok
```

`write_probes` creates a new file exclusively and never overwrites it.
`check_file` returns a `Report`; differences set `ok=False`, while malformed
inputs raise `ProbeFileError` and filesystem failures raise `OSError`.
`report.as_dict()` gives the JSON-compatible versioned report.
`html_report([report])` returns an escaped standalone HTML string.
`select_probes("extended")` returns immutable controls; custom scalar values
use `select_probes("none", Path("values.json"))`. Keep integer values in Python
or raw JSON to avoid JavaScript number rounding.

`Config` is immutable and validates option types. Load at most 64 KiB of UTF-8
JSON (optional BOM); duplicate/unknown keys and invalid options fail. Keys match
the schema. `custom_values` is a local path resolved relative to the configuration
file; explicit `--custom-values` paths resolve from the working directory.
Configuration reads no code, changes no environment and names no output file.
Only load configurations and custom-value files you intend to read locally.
The schema checks structure; runtime additionally checks known encodings/probe
categories, distinct column names and valid Unicode. Custom files are validated
when building operation options, allowing explicit CLI overrides first.

```console
python -m rowcanary make controls.csv --config examples/config.json
python -m rowcanary check exported.csv --config examples/config.json --delimiter ";"
python -m rowcanary batch first.csv second.csv --config examples/config.json --json --report batch.json
python -m rowcanary check reordered.csv --config examples/config.json --no-strict-order
python -m examples.integration
```

Explicit CLI flags override config; missing options use existing defaults.
Null/omitted encoding defaults to UTF-8 generation and BOM-aware checking.
Generation always uses `_rowcanary_id`/`_rowcanary_value`; column options apply
only to checking renamed exports. Retain the same control set/custom values
through generation and checking. CSV/TSV represent scalar values as text;
JSON/JSONL/XLSX can retain native scalar types.

CLI exit codes: `0` preserved controls, `1` integrity differences, `2` invalid
input or operational error. Batch checks every file; an operational error takes
precedence over differences. Demo deliberately introduces differences and exits
`0` when the demonstration runs. See `examples/github-actions.yml` for pinned
automation using a public release wheel, and `examples/integration.py` for an
isolated Python integration. The synthetic Actions example proves the detector,
not an external application's import/export behavior.
