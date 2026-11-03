# Development progress

Target: v1.0.0. Current published version: v0.1.1.

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

- JSON strings currently bypass the documented field-size bound.
- Empty/non-string API column names need explicit validation.
- Implemented both fixes with regressions first observed failing.
- 67 tests passed; Ruff lint/format, Twine, archive inspection, secret-pattern
  scan and clean wheel/sdist CLI installs passed. Existing assets inspected.
- Formatting is now checked in CI; the version CLI regression follows the
  package version instead of hardcoding an obsolete release.
- Published after all 17 jobs passed in run 41551284480; all four public artifact
  hashes verified. Git pushes use the authenticated CLI helper for this command
  only, avoiding an unrelated saved Git credential.

## Active milestone: 0.2.0

- Five formats, encoding/BOM handling, extended/category/custom probes and scalar
  type comparison implemented. Existing 24 default IDs and CLI behavior retained.
- New regressions first failed; 82 tests now pass on Windows (11.634 seconds).
- Openpyxl's pure-Python writer translated CRLF on Windows. Replaced generation
  with minimal deterministic literal OpenXML; external reads still use openpyxl
  with defusedxml. Exact extended probes pass in all five formats.
- Ruff, Twine, distribution inspection and clean wheel/sdist install gates passed.
- Next: push reviewed source, green hosted CI, publish 0.2.0,
  verify public artifacts, then start diagnostics/reporting.

See [development plan](docs/development-plan.md) for the remaining milestones.
No milestone after 0.2.0 has been implemented or released yet.
