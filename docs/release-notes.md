# RowCanary v0.1.0

RowCanary detects silent data changes during import/export workflows. Generate
24 deterministic control values, send them through an application, export the
records and compare the result locally.

## Included

- `rowcanary make`, `rowcanary check` and the self-contained `rowcanary demo`.
- UTF-8 CSV generation and CSV/JSON checking, including a leading UTF-8 BOM,
  explicit CSV delimiters, renamed columns and reordered records.
- Exact string comparison for leading zeros, large numbers, scientific and
  date-like text, empty values, whitespace, Unicode and formula-like strings.
- Missing, duplicate, unexpected and changed-record reports; text or JSON
  output; exit codes suitable for scripts.
- Bounded input reads, strict JSON keys/constants, numeric diagnostics without
  precision loss, safe terminal display and exclusive probe creation.
- Genuine SVG reconstruction of the original canary/table artwork, transparent
  PNG exports and a GitHub social image.
- MIT license, no runtime dependencies, tests and CI configuration.

## Scope

The demo intentionally changes three values. A passing check applies only to
the supplied controls and tested workflow; it does not establish that a whole
dataset is intact or that formulas never executed in an external application.
Some probes begin with `=`, `+` or `-`; use isolated test data.

See [verification](verification.md) for executed environments and pending
checks, and [limitations](limitations.md) for input/resource constraints.

Distribution files: `rowcanary-0.1.0-py3-none-any.whl` and
`rowcanary-0.1.0.tar.gz`. Install a downloaded wheel with
`python -m pip install ./rowcanary-0.1.0-py3-none-any.whl`.

No PyPI publication is included in this release.
