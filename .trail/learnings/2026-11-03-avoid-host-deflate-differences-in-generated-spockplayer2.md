---
title: Avoid host DEFLATE differences in generated XLSX bytes
author: Spockplayer2
date: 2026-11-03
branch: main
id: l-068bbaa8
scope: repo
status: active
src: agent
touches:
  - CHANGELOG.md
  - PROGRESS.md
  - docs/compatibility.md
  - docs/performance.md
  - examples/compatibility/clean.xlsx
  - examples/compatibility/manifest.json
  - rowcanary/formats.py
  - tests/test_formats.py
  - tests/test_compatibility.py
---

## Decided
Write generated XLSX members without DEFLATE compression, keeping fixed metadata and literal XML. Continue accepting bounded compressed workbooks as input.
## Tried and ruled out
The hosted corpus rebuild failed on14 test jobs after ZIP platform metadata was fixed. Python3.10 and3.14 produced identical XML but different compressed sizes and hashes due to host zlib. Fixed timestamps and create_system were insufficient.
## Watch out
Generated XLSX files are larger and still subject to the32MiB output limit. Do not normalize native application CSV outputs or weaken the golden-fixture check to hide platform differences.
In the code: rowcanary/formats.py encode_probes; tests/test_formats.py compressor-independence regression; tests/test_compatibility.py.
