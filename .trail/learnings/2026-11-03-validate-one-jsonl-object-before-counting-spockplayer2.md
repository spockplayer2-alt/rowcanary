---
title: Validate one JSONL object before counting each line
author: Spockplayer2
date: 2026-11-03
branch: main
id: l-3669edee
scope: repo
status: active
src: agent
touches:
  - CHANGELOG.md
  - PROGRESS.md
  - README.md
  - docs/development-plan.md
  - docs/limitations.md
  - docs/verification.md
  - docs/web-ui.md
  - pyproject.toml
  - rowcanary/__init__.py
  - rowcanary/core.py
---

## Decided
Require exactly one object per nonblank JSONL line before counting streamed records. Apply the same rule to the buffered adapter.
## Tried and ruled out
Wrapping a line in brackets and yielding every parsed item accepted {},{} as two records. Counting physical lines then let four records through a two-row limit. The previous buffered adapter also accepted malformed multi-object lines below the limit.
## Watch out
The JSON parser validates each wrapper array, not JSONL framing. Retain a direct multi-object-line regression alongside ordinary row-boundary tests.
In the code: rowcanary/streaming.py _jsonl_records; rowcanary/formats.py load_rows; tests/test_resources.py.
