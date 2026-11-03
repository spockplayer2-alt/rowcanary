---
title: Fix ZIP platform metadata for cross-platform fixture hashes
author: Spockplayer2
date: 2026-11-03
branch: main
id: l-9334469f
scope: repo
status: active
src: agent
touches:
  - ".gitattributes"
  - CHANGELOG.md
  - MANIFEST.in
  - PROGRESS.md
  - README.md
  - docs/development-plan.md
  - docs/verification.md
  - pyproject.toml
  - rowcanary/__init__.py
  - rowcanary/formats.py
---

## Decided
Set XLSX ZIP create_system explicitly and compare regenerated compatibility fixtures with the checked-in bytes across CI operating systems.
## Tried and ruled out
Fixed ZIP timestamps alone did not give cross-platform bytes: ZipInfo defaults create_system to 0 on Windows and 3 on Linux. Simulating Linux changed clean.xlsx and its manifest hash. Two rebuilds on the same host missed it.
## Watch out
Preserve native Excel outputs unchanged; only synthetic fixtures are rebuildable without the native application. Platform metadata and newline conversion both matter for byte-level manifests.
In the code: rowcanary/formats.py encode_probes; tests/test_formats.py; tests/test_compatibility.py.
