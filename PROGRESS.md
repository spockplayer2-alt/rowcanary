# Development progress

Target: v1.0.0. Current published version: **v0.4.0**.

**Resumed on 2026-11-03 with v0.3.0.** Work proceeds sequentially through the
existing roadmap; no PyPI publication is authorized.

## Baseline (2026-11-02)

- Clean checkout, existing main history and v0.1.0 release preserved.
- 65 unittest tests passed on native Windows before changes (10.408 seconds).
- Existing latest hosted Checks run 41521879070 is successful.
- Existing CSV/JSON engine, CLI, packaging, logo assets and documentation reviewed.
- GitHub authentication verified for the authorized repository. Local GitHub CLI
  reused. Public commits use the repository's public maintainer identity.
- Verified tooling: RTK 1.0.1, Trail graph/CLI, ripgrep, Serena Python symbol
  lookup, context-mode execution, native jq/ast-grep binaries. RTK hooks exist in
  configuration but RTK reports no active automatic hook; normal tool commands
  remain usable. No global settings or services installed or changed.
- Headroom MCP responds, but its configured proxy is unreachable; verification
  returned a no-op with zero savings. Do not depend on compression through it.
- Codex CLI/Desktop shared TOML, enabled MCP names, hook tool references and skill
  catalog inspected without printing credential configuration.

## Completed milestone: 0.1.1

- Fixed JSON strings bypassing the documented field-size bound.
- Added explicit validation of empty/non-string API column names.
- Implemented both fixes with regressions first observed failing.
- 67 tests passed; Ruff lint/format, Twine, archive inspection, secret-pattern
  scan and clean wheel/sdist CLI installs passed. Existing assets inspected.
- Formatting is now checked in CI; the version CLI regression follows the
  package version instead of hardcoding an obsolete release.
- Published after all 17 jobs passed in run 41551284480; all four public artifact
  hashes verified. Git pushes use the authenticated CLI helper for this command
  only, avoiding an unrelated saved Git credential.

## Completed milestone: 0.2.0

- Five formats, encoding/BOM handling, extended/category/custom probes and scalar
  type comparison implemented. Existing 24 default IDs and CLI behavior retained.
- New regressions first failed; 82 tests now pass on Windows (11.634 seconds).
- Openpyxl's pure-Python writer translated CRLF on Windows. Replaced generation
  with minimal deterministic literal OpenXML; external reads still use openpyxl
  with defusedxml. Exact extended probes pass in all five formats.
- Ruff, Twine, distribution inspection and clean wheel/sdist install gates passed.
- Commit: `d9d08b0cdd2964eb9d52307c730ff05d361a9441`, pushed to `main`.
- All 17 jobs passed in hosted run **41552578077**: Python 3.10–3.14 on
  Ubuntu, Windows and macOS, plus packaging and assets.
- Published [v0.2.0](https://github.com/spockplayer2-alt/rowcanary/releases/tag/v0.2.0).
  Wheel, sdist, source ZIP and checksums downloaded publicly and verified against
  their local SHA-256 hashes. v0.1.1 was published and verified independently.
- pip-audit found no known vulnerabilities in the three installed runtime
  dependencies. Evidence: `.local/verification/audit-0.2.0.json`.

## Completed milestone: 0.3.0

- Preserved the previous untracked tests, reproduced their 15 errors, then
  implemented diagnostics, tentative causes, severity/types/guidance, reorder
  observations and strict-order opt-in, standalone escaped HTML, batch checks,
  exclusive report export and packaged report schema 1.0.
- Added schema validation only to test/dev extras and CI; runtime dependencies
  unchanged. Added batch precedence/schema, JSON export, hostile HTML name,
  conservative diagnostic and strict-order coverage.
- Independent review found Windows exclusive file creation followed a dangling
  symlink. Regression reproduced exit 0 and target creation; explicit symlink
  rejection fixed it. Final suite: **96 tests passed** (11.378 seconds), including
  14 reporting tests. Independent review has no other actionable findings.
- Ruff, Twine, package inspection, secret-pattern scan and clean wheel/sdist
  installs passed on final source after the review changes.
- Runtime dependency audit found no known vulnerabilities; evidence:
  `.local/verification/audit-0.3.0.json`. Trail check reports no conflicts.
- Final self-review also reproduced a diagnostic depending on the host decimal
  rounding mode; explicitly use half-even. Added its regression (96 tests total).
- Commit `d64a4d4`, pushed to main. All 17 jobs passed in hosted run
  **41667334334**. Published v0.3.0 and verified all four public attachment
  hashes against local artifacts. Evidence: `.local/verification/publish-0.3.0.log`.
- Ruling: keep human demo output compatible; detailed diagnostic metadata is in
  JSON/HTML. Reorder observations appear in human output without failing.

## Completed milestone: 0.4.0

- Six new real HTTP boundary tests reproduced the absent UI, then passed:
  all five formats, custom CRLF/null controls, Host/Origin/token/content-type,
  static route isolation, malformed uploads and pre-read request size bounds.
- `serve --port/--open`, packaged HTML/CSS/JS and the existing icon implemented.
  Single serial loopback server; temporary request files, no external resources.
- Actual Edge browser generated/downloaded CSV and uploaded it for 24/24 PASS.
  Dark theme at 390px had no horizontal overflow. Screenshots and downloads:
  `output/playwright/` and `.playwright-cli/` (ignored local evidence).
- Independent review fixed two findings: preserve raw custom JSON instead of
  rounding integers in JavaScript; leave encoding blank for BOM-aware checks.
  Reproduced failures first. Actual browser download retained 9007199254740993
  exactly; actual UTF-8-BOM CSV upload passed 24/24 after the fix.
- All **104 tests passed** (15.558 seconds), Ruff/Twine/archive/secret checks and
  clean wheel/sdist CLI and HTTP/static-asset installs passed. No added runtime
  dependency; the v0.3.0 same-day audit covers the unchanged dependency versions.
- Ruling: use the standard-library server and base64 JSON for this single-user
  loopback tool, avoiding new runtime dependencies. No remote hosting support.
- Commit `ba8be20`; all 17 jobs passed in hosted run **41669984337**.
  Published v0.4.0 and verified all four public attachment hashes.

## Active milestone: 0.5.0 — local gates passed; hosted checks/publication pending

- Stream CSV/TSV/JSONL with bounded readers and exact newline decoding. Compare
  once; retain bounded buffered JSON arrays/XLSX. Close streams on every exit.
- Bound issue count/diagnostic text and numeric JSON tokens; reject duplicate
  ZIP members. Limit UI rendering to 200 items and server backlog to four.
- All **115 tests passed** (14.478 seconds). Review found a JSONL physical-line
  count bypass with multiple objects per line; both parsers now reject it.
  Review exercised 2,400 differential cases with no report/error mismatch,
  stale-stat limits and native Windows handle cleanup after errors.
- Benchmarks exposed a 33.7 MB allocation for an 8 KiB read; a failing regression
  now passes after chunked buffered reads. Final 10,000-control measurements in
  `.local/verification/benchmark-0.5.0.json` and `docs/performance.md` cover all
  five formats; all exact comparisons passed. These are Python allocations,
  not RSS. New streaming parser peaks are approximately 165–185 KB.
- Actual browser displayed 200 of 524 issues with an explicit full-download note.
  Downloaded JSON retained all 524 items. Ruff, Twine, package/secret inspection,
  clean wheel/sdist CLI and HTTP/static installs passed on final source.
- Ruling: reject oversized diagnostics as an operational error instead of
  presenting a partial pass. No schema or legacy issue-code change.

## Exact next action

1. Finish v0.5.0 release gates and full report-download verification; commit/push,
   wait for all 17 jobs, publish/verify artifacts.
2. Proceed with v0.6.0 compatibility fixtures/matrix and available live tests.
   Use tests first; preserve exact line breaks, stable IDs and issue codes.
3. Never publish to PyPI or rewrite existing release tags/history.

## Local helpers and evidence

- Python environment: `.venv/Scripts/python.exe` (uv-managed, no pip module).
- GitHub CLI: `.local/gh/gh.exe`; authenticated as the authorized repository owner.
  Ordinary Git selected a different cached account and returned 403. The helper
  below supplies the authenticated CLI credential helper per push command without
  changing global Git credentials. No secrets are stored in this progress file.
- `.local/release_cycle.py`: `prepare VERSION` runs local release gates/builds
  and clean wheel/sdist installs; `status` inspects HEAD CI; `publish VERSION`
  refuses non-green CI/dirty checkouts, tags/pushes/releases, and verifies downloads.
  Read it before reuse. It is local tooling, not committed product code.
- Local release artifacts/logs: `.local/v0.1.1/`, `.local/v0.2.0/` and
  `.local/verification/`. Development changes are committed through v0.2.0;
  v0.4.0 is committed/published; v0.5.0 resource work is currently uncommitted.
- Existing logo identity retained. Five SVGs render; six PNGs match masters.
- Real Excel, Google Sheets, LibreOffice and CRM round trips remain unverified;
  the format tests exercise parsers/generated files, not those applications.
- Read the committed Trail learning about the Windows XLSX newline issue before
  changing the writer. Do not replace bounded binary decoding with `read_text`.

See [development plan](docs/development-plan.md) for the remaining milestones.
No milestone after 0.4.0 has been released yet. v0.5.0 is implemented; do not
claim publication until hosted checks and public download verification pass.
