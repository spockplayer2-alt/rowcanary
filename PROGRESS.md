# Development progress

Target: v1.0.0. Current published version: v0.1.0.

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

## Active milestone: 0.1.1

- JSON strings currently bypass the documented field-size bound.
- Empty/non-string API column names need explicit validation.
- Implemented both fixes with regressions first observed failing.
- 67 tests passed; Ruff lint/format, Twine, archive inspection, secret-pattern
  scan and clean wheel/sdist CLI installs passed. Existing assets inspected.
- Formatting is now checked in CI; the version CLI regression follows the
  package version instead of hardcoding an obsolete release.
- Next: push this verified source, wait for all 17 CI jobs, publish v0.1.1 and
  verify public artifact hashes before beginning 0.2.0.

See [development plan](docs/development-plan.md) for the remaining milestones.
No later milestone has been implemented or released yet.
