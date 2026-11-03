---
title: Reject dangling report links explicitly on Windows
author: Spockplayer2
date: 2026-11-03
branch: main
id: l-cedecd4e
scope: repo
status: active
src: agent
touches:
  - ".github/workflows/tests.yml"
  - CHANGELOG.md
  - PROGRESS.md
  - README.md
  - docs/development-plan.md
  - docs/verification.md
  - pyproject.toml
  - rowcanary/__init__.py
  - rowcanary/cli.py
  - rowcanary/core.py
---

## Decided
Keep an explicit symbolic-link check before exclusive report-file creation, matching control generation.
## Tried and ruled out
Relying on Path.open("x") alone was insufficient on native Windows: a dangling file symlink was followed and its absent target was created. A regression reproduced exit 0 before the guard, then exit 2 without target creation after it.
## Watch out
Test dangling links as well as existing regular files; exclusive creation semantics can differ by platform. Do not remove the guard as redundant.
In the code: rowcanary/reporting.py export_report; tests/test_reporting.py test_report_rejects_dangling_symlink_without_creating_its_target.
