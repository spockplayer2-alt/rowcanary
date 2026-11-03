# Development progress

Target: **v1.0.0**. Current published version: **v0.9.0**.
Final v1.0.0 candidate: metadata complete; final local gates/CI/publication pending.

## Published in this sprint

| Version | Commit | Hosted Checks run | Result |
| --- | --- | --- | --- |
| v0.7.0 | 5fda0a1 | 41680640926 | 17/17 passed; 4 public artifact hashes verified |
| v0.8.0 | e2e6a0a | 41682165242 | 17/17 passed; 4 public artifact hashes verified |
| v0.9.0 | 3704c9e | 41683474568 | 17/17 passed; 4 public artifact hashes verified |

Earlier v0.1.0–v0.6.0 releases and history remain intact. The historical detailed
checkpoint is preserved in Git through v0.9.0. No PyPI upload is authorized.

## Implemented and verified

- v0.7.0: additive stable public imports, immutable Config/load_config, bounded
  duplicate-safe UTF-8 JSON, packaged schema 1.0, relative custom-value paths,
  CLI overrides (including --no-strict-order), Python/batch/Actions examples.
  Exact CRLF, null and 9007199254740993 round-trip controls pass.
- v0.8.0: quickstart/troubleshooting/Excel guidance and actual screenshots.
  Edge reproduced stale PASS after mode changes; fixed and retested. Generation
  and upload passed 24/24; altered input produced 21/24, three issues, verified
  in downloaded JSON/HTML. Keyboard skip/focus, labels, busy/error state,
  reduced motion and mobile dark-theme overflow passed; screenshots inspected.
- v0.9.0: feature freeze, independent review with no confirmed important defects,
  updated security boundaries and installed public API/schema checks in CI.
- Focused local tests: 19 for v0.7.0, 11 for v0.8.0, 6 for v0.9.0. Every release
  passed lint/format, Twine, archive/secret checks and clean wheel/sdist CLI,
  public API/configuration schema and local HTTP/static-asset installations.
- Runtime versions match the existing same-day dependency audit: openpyxl 3.1.5,
  defusedxml 0.7.1, et-xmlfile 2.0.0; no known vulnerabilities in that audit.
  No new runtime dependency; no redundant baseline audit.

## Remaining limits

- Native Excel 16.0 build 20527 text and automatic CSV profiles preserve 33/35
  and 20/35 controls respectively. These remain detected differences, not
  normalized away. Other Excel workflows, Sheets, LibreOffice and CRM unverified.
- Stored XLSX ZIP members deliberately use more space for byte reproducibility.
- Accessibility checks are targeted; no screen-reader/WCAG certification claimed.
- A PASS covers only supplied controls. Formula-like controls require isolated
  test data. Local UI is single-user loopback only. See docs/limitations.md.

## Exact next action

Finish final local gates, commit/push, require all 17 CI jobs, publish v1.0.0,
verify all four public artifact hashes, then replace this pending checkpoint
with the actual final results. Do not rewrite earlier tags or publish to PyPI.

## Local helpers and evidence

- `.venv/Scripts/python.exe`; authenticated `.local/gh/gh.exe`.
- `.local/release_cycle.py`: prepare VERSION [focused test patterns], status,
  publish VERSION. Final prepare without patterns runs the complete suite.
  Pushes use its per-command authenticated helper; global credentials unchanged.
- `.local/wait-ci.py`: waits at 60-second intervals, writes a concise job summary
  and full ignored log. Publication independently refuses dirty/non-green states.
- `.local/vVERSION/dist/`: wheel/sdist/source ZIP/SHA256SUMS.txt.
- `.local/verification/`: audits/review/CI/Trail evidence; browser scripts in
  `.local/ui-*.cjs`, captures/downloads in `output/playwright/v0.8-*`.
- `docs/screenshots/`: shipped real synthetic desktop/mobile captures.
