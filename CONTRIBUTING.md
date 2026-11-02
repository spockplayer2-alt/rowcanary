# Contributing

Use an issue to describe a reproducible data-change case, including Python/OS
versions and the exact commands used. Include synthetic input and observed
output. Do not share customer records, credentials or unredacted private paths.
Read [SECURITY.md](SECURITY.md) before reporting a vulnerability.

For code changes:

1. Install development tools: `python -m pip install -e ".[dev]"`.
2. Add a focused regression test that fails before the fix.
3. Preserve exact strings and JSON types. Do not hide data changes through
   trimming, newline replacement, Unicode normalization or numeric coercion.
4. Prefer the Python standard library and small changes at the responsible
   layer. Keep Python 3.10 compatibility.
5. Run `python -m unittest discover -s tests -v` and `python -m ruff check .`.
6. For a release, also run `python -m build`, `python -m twine check dist/*` and
   `python tools/check_package.py dist` in a directory containing one current
   wheel and one current source distribution.

CLI exit statuses are part of the interface: 0 for matching controls or
successful generation/demo, 1 for integrity differences, 2 for invalid input or
I/O/usage errors. `check --json` operational errors produce an `error` object;
argument parsing errors remain stderr usage diagnostics.

Tests must never evaluate spreadsheet formulas. Use only synthetic fixtures
and temporary directories; verify that generation cannot overwrite an existing
path. See [asset instructions](assets/README.md) before changing artwork.
