# Development progress

Target: v1.0.0. Current published version: **v0.8.0**.

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

## Completed milestone: 0.5.0

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
- Commit `17d9c97`; all 17 jobs passed in hosted run **41673055353**.
  Published v0.5.0 and verified all four public attachment hashes.

## Completed milestone: 0.6.0

- 13 synthetic fixtures across all formats/BOM/dialect/type/change profiles;
  deterministic rebuilds, independent expected codes/IDs and SHA-256 manifests.
- Actual Microsoft Excel 16.0 build 20527, 32-bit: dedicated automation instance,
  35 synthetic extended controls, macros disabled, no existing workbook touched.
  OpenText of a byte-identical .txt copy with explicit UTF-8/comma, then CSVUTF8
  export with actual regional semicolon separator. Text profile: 33/35, 4 issues;
  automatic inference: 20/35, 18 issues. Both FAIL, retained without normalization.
- Native raw CSVs/manifest are in `examples/compatibility/excel/`; reproducible
  script and exact limitations are in `docs/compatibility.md`. No Excel process
  remained after the run. Google Sheets, LibreOffice and CRM remain unverified.
- Initial direct .csv OpenText did not produce required headers. The script now
  checks headers and stages .txt to select explicit text import; failed attempt
  stays only under `.local/verification/excel-0.6.0/`.
- Independent review confirmed actual outcomes using csv independently of the
  comparator. Found OS-dependent ZIP create_system metadata; regression first
  failed, then passed with fixed platform metadata and checked-in rebuild checks.
- All **120 tests passed**, plus Ruff, Twine, package/secret inspection and clean
  wheel/sdist CLI/HTTP/static installs. Independent review findings are fixed.
- Hosted run **41675668895** then blocked publication: 14 test jobs failed only
  the corpus rebuild check. Local Python 3.10 reproduction showed identical XML
  but different DEFLATE sizes/bytes versus 3.14. Use stored ZIP members instead;
  a compressor-independence regression first failed and now passes. Synthetic
  corpus comparisons now match on installed Python 3.10–3.13; final suite has
  121 tests. The failed candidate was not tagged or published; final gates and
  hosted CI were repeated successfully on the corrected source.
- Final retry local gates passed: **121 tests** (13.564 seconds), Ruff/Twine,
  package/secret checks and clean wheel/sdist CLI/HTTP/static installs.
- Latest Trail false positives match prose about ZIP metadata to the warning
  against timestamps alone. The fix retains explicit platform metadata AND uses
  stored members, with compressor-independence and cross-version corpus proof;
  the retry commit records this rationale. No ruled-out behavior was restored.
- Ruling: choose larger, uncompressed generated XLSX files for cross-runtime
  byte reproducibility; retain the 32 MiB output bound and compressed input support.
- Trail check flags the documented explicit UTF-8 Excel import as conflicting
  with the browser-default encoding learning. This is a false positive: native
  fixture input has known UTF-8 bytes; browser checking remains BOM-aware. The
  release commit records this distinction as required by Trail.
- Final commit **`675cfdd`**; all **17 jobs passed** in hosted run
  **41676886153**. Published [v0.6.0](https://github.com/spockplayer2-alt/rowcanary/releases/tag/v0.6.0)
  and verified wheel, sdist, source ZIP and checksums publicly against local
  hashes. Evidence: `.local/verification/publish-0.6.0.log`.

## End-of-session checkpoint — 2026-11-03

- Published independently today: **v0.3.0, v0.4.0, v0.5.0, v0.6.0**. Each has
  its own green 17-job matrix and four publicly verified release attachments.
- Final local suite: **121 passed** (13.564 seconds), plus lint/format, Twine,
  archive/secret checks and clean wheel/sdist CLI/HTTP/static installations.
- No unresolved test or release blocker. The first v0.6.0 CI failure is fixed;
  no failed or pending check was used as a publication gate.
- All implementation and learnings through v0.6.0 are committed and pushed.
  This final post-publication `PROGRESS.md` checkpoint remains a local tracked
  modification, as in the previous session; preserve it. No other source work
  is unfinished or untracked. `.local/` and browser evidence are ignored helpers.
- Test browser and local HTTP server were stopped; no Excel process remained.
  No local development process or automatic continuation runs in the background.
- Remaining roadmap: v0.7.0 public API/configuration/integration examples;
  v0.8.0 guides/UI/accessibility/screenshots; v0.9.0 freeze/security/package
  review; v1.0.0 final review/CI/public artifacts/install verification.
- Limitations: native Excel profiles both failed controls as documented; other
  Excel workflows, Google Sheets, LibreOffice and CRM remain unverified.
  Generated XLSX is now larger because it uses stored ZIP members. No PyPI
  publication occurred or is authorized.

## Exact next action

1. Start **v0.7.0**. Read this checkpoint and `docs/development-plan.md`; reuse
   existing checkout, releases, corpus, tests and helpers. Do not rebuild old
   features or repeat the completed baseline audit/Excel investigation.
2. `.local/plan-0.7.0.md` is a conceptual draft only: immutable configuration,
   bounded JSON/schema validation, relative custom-value paths, explicit CLI
   overrides and make/check API option helpers. No v0.7.0 source or tests exist
   yet. Inspect the current CLI/API with Trail, write behavioral tests first,
   and implement this milestone before touching v0.8.0.
3. Preserve exact line breaks, stable IDs/issue codes and the native Excel CSVs.
   Keep generated XLSX platform metadata and stored members deterministic.
4. Never publish to PyPI or rewrite existing release tags/history.

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
  v0.6.0 is committed/published; only this final progress checkpoint is local.
- Existing logo identity retained. Five SVGs render; six PNGs match masters.
- Native Excel OpenText profiles are verified only as recorded in v0.6.0 above.
  Google Sheets, LibreOffice, CRM and other Excel workflows remain unverified.
- Read the committed Trail learning about the Windows XLSX newline issue before
  changing the writer. Do not replace bounded binary decoding with `read_text`.

See [development plan](docs/development-plan.md) for the remaining milestones.
No milestone after v0.6.0 has been implemented or released. Resume at v0.7.0.

## Final sprint: v0.7.0 implementation

- Public API, immutable configuration, bounded duplicate-safe JSON and explicit
  CLI precedence implemented; exact relative CRLF/null/large-integer controls tested.
- Configuration regressions first failed on absent public imports, then passed.
- Focused local checks and existing 17-job hosted matrix gate this milestone.
- Ruling: use focused local tests per milestone and one final complete suite,
  as requested; reuse all distribution/install/security gates on each release.
- Existing Excel round-trip defects remain observable differences, not normalized.
- Local verification: 19 focused tests (configuration/CLI/documentation), lint/format,
  Twine, archive/secret checks and clean wheel/sdist CLI/API/HTTP installs.

## Published v0.7.0 / v0.8.0 candidate

- v0.7.0 commit `5fda0a1`, hosted run **41680640926**, all 17 jobs passed.
  Published https://github.com/spockplayer2-alt/rowcanary/releases/tag/v0.7.0;
  all four public artifact hashes verified. No PyPI publication.
- v0.8.0 adds first-run/Excel/troubleshooting guidance and actual screenshots.
- Actual Edge reproduced stale PASS after mode changes; fixed and retested.
  Generated upload passed 24/24; altered file returned 21/24, three issues;
  downloaded JSON/HTML verified. Keyboard, labels, busy/error announcements,
  reduced motion and mobile overflow passed. Screenshots inspected.
- Local/browser evidence: `.local/ui-stale.cjs`, `.local/ui-final.cjs`,
  `output/playwright/v0.8-*`; published captures in `docs/screenshots/`.

## Published v0.8.0 / v0.9.0 freeze

- v0.8.0 commit `e2e6a0a`, hosted run **41682165242**, all 17 jobs passed;
  published release and all four public artifact hashes verified.
- Frozen features; focused independent review of v0.7.0/v0.8.0 code found no
  confirmed important defects. Schema delimiter/path/NUL validation checked.
- Runtime versions match the existing same-day audit: openpyxl 3.1.5,
  defusedxml 0.7.1, et-xmlfile 2.0.0, no known vulnerabilities in that audit.
  No new runtime dependency or redundant full audit was introduced.
- Security guidance now covers five formats, local HTTP and bounded configuration.
  Hosted packaging also exercises the installed public API/configuration schema.
- Known Excel and other-application limitations remain as recorded; no claim
  of universal spreadsheet compatibility or complete WCAG conformance.
