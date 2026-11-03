---
title: Keep custom controls exact through the browser transport
author: Spockplayer2
date: 2026-11-03
branch: main
id: l-3b0287d9
scope: repo
status: active
src: agent
touches:
  - CHANGELOG.md
  - MANIFEST.in
  - PROGRESS.md
  - README.md
  - docs/development-plan.md
  - docs/verification.md
  - pyproject.toml
  - rowcanary/__init__.py
  - rowcanary/cli.py
  - tools/check_package.py
---

## Decided
Forward custom controls from the browser as raw JSON and parse them in Python. Use operation-specific default encodings.
## Tried and ruled out
JavaScript JSON.parse then JSON.stringify silently rounded 9007199254740993 to 9007199254740992. Shared explicit utf-8 also disabled the normal BOM-aware check default.
## Watch out
Verify browser download digits and actual BOM uploads, not just the exact Python API. Blank encoding means UTF-8 generation and BOM-aware checking.
In the code: rowcanary/static/app.js; rowcanary/web.py _operate; tests/test_web.py.
