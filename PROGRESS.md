# Development progress

Target: **v1.0.0**. Current published version: **v1.0.0**.
Completed 2026-11-03: v0.7.0, v0.8.0, v0.9.0 and v1.0.0 published sequentially.
Final release: https://github.com/spockplayer2-alt/rowcanary/releases/tag/v1.0.0

## Published in this sprint

| Version | Commit | Hosted Checks run | Result |
| --- | --- | --- | --- |
| v0.7.0 | 5fda0a1 | 41680640926 | 17/17 passed; 4 public artifact hashes verified |
| v0.8.0 | e2e6a0a | 41682165242 | 17/17 passed; 4 public artifact hashes verified |
| v0.9.0 | 3704c9e | 41683474568 | 17/17 passed; 4 public artifact hashes verified |
| v1.0.0 | d536ec2 | 41684567466 | 17/17 passed; 4 public artifact hashes verified |

Earlier v0.1.0–v0.6.0 releases and history remain intact. The historical detailed
checkpoint is preserved in Git through v0.9.0. PyPI publication is now authorized.

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

## Final verification

- Complete local suite: **125 tests passed**, 16.780 seconds; no tests disabled,
  skipped or removed. No repeated complete local suite during this sprint.
- Ruff lint/format, Twine, package inspection, secret-pattern scan and clean
  wheel/sdist CLI/API/configuration-schema/HTTP installations passed on final source.
- Final commit/main CI **41684567466** and tag CI **41685181551** each passed
  **all 17 jobs** (Python 3.10–3.14, Ubuntu/Windows/macOS, package and assets).
- v1.0.0 is the public latest release, non-draft/non-prerelease. Wheel, sdist,
  source ZIP and SHA256SUMS.txt were anonymously downloaded and verified against
  local SHA-256 hashes. Each preceding sprint release passed the same public gates.
- Release commit/tag: **d536ec2 / v1.0.0**. Implementation and learning committed
  and pushed. Only this final local PROGRESS.md checkpoint differs from the tag.
- Browser and owned local server processes were stopped; no automatic work remains.
- PyPI v1.0.0 published through Trusted Publishing on 2026-11-03, source
  `d0842f5`, workflow run 41702034555: build and publish succeeded.
  https://pypi.org/project/rowcanary/1.0.0/
- Public wheel and sdist hashes match the hosted workflow artifacts. Fresh,
  uncached PyPI installation outside the checkout returned `rowcanary 1.0.0`;
  `pip check`, demo and extended XLSX round trip (35/35) passed.

## Remaining limits

- Native Excel 16.0 build 20527 text and automatic CSV profiles preserve 33/35
  and 20/35 controls respectively. These remain detected differences, not
  normalized away. Other Excel workflows, Sheets, LibreOffice and CRM unverified.
- Stored XLSX ZIP members deliberately use more space for byte reproducibility.
- Accessibility checks are targeted; no screen-reader/WCAG certification claimed.
- A PASS covers only supplied controls. Formula-like controls require isolated
  test data. Local UI is single-user loopback only. See docs/limitations.md.

## Exact next action

The v1.0.0 roadmap is complete. Resume only for a requested maintenance task.
Preserve existing release tags and compatibility fixtures. PyPI publication is
complete for v1.0.0 via `publish.yml` and the `pypi` environment. The hosted
workflow, public registry files and a clean PyPI installation were verified.
External application compatibility claims still require direct evidence.

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
