# Road to 1.0

The existing exact-value comparison engine and its 24 default controls remain
compatible. Work proceeds in the requested release order; every tag requires a
green hosted matrix and verified wheel, sdist, source ZIP and checksums. No PyPI
publication is authorized. No customer data or credentials enter test fixtures.

- [x] 0.1.1: enforce JSON field bounds and column validation; regression tests.
- [x] 0.2.0: CSV/TSV/JSON/JSONL/XLSX adapters, explicit encoding/format,
  deterministic extended/custom probe sets and typed comparisons.
- [x] 0.3.0: evidence-based diagnostics, severity, JSON schema, safe HTML,
  report export, batch checks and documented exit status.
- [x] 0.4.0: loopback-only local web UI with upload, generation, comparison,
  downloads, accessible themes and no external resources.
- [x] 0.5.0: measure memory/time, stream line-based formats, bound archives,
  uploads and concurrent operations; large-file and malformed-input tests.
- [x] 0.6.0: reproducible compatibility fixtures, matrix, live tests where
  applications are available, clearly labeled evidence.
- [x] 0.7.0: stable public API, validated reusable JSON configuration,
  GitHub Actions and batch examples, integration tests.
- [x] 0.8.0: complete guides, CLI/UI polish, actual screenshots, distribution
  verification and accessibility checks.
- [x] 0.9.0: freeze features, regression/security/dependency/package review,
  full hosted matrix, known limitations and release automation proof.
- [ ] 1.0.0: final review, green CI, verified public artifacts and installation.

For each feature: write and run failing behavioral tests, implement the narrow
change, run the suite and static checks, inspect distributions, review the diff,
run `trail check`, commit/push, wait for CI, tag/publish, verify public artifacts.
Keep the ledger in `PROGRESS.md` current. Do not bypass failed or pending gates.

Review focus: exact CR/LF preservation; null versus absent versus empty; numeric
precision and native types; formula safety and hostile archives; filesystem,
browser-origin and resource boundaries. Classifications describe observations;
possible causes must remain explicitly tentative.
