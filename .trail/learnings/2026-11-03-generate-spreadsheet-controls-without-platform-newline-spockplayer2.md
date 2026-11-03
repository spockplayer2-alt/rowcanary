---
title: Generate spreadsheet controls without platform newline conversion
author: Spockplayer2
date: 2026-11-03
branch: main
id: l-c3743b2d
scope: repo
status: active
src: agent
touches:
  - CHANGELOG.md
  - README.md
  - docs/limitations.md
  - docs/publication.md
  - pyproject.toml
  - rowcanary/__init__.py
  - rowcanary/cli.py
  - rowcanary/core.py
  - tools/check_package.py
---

## Decided
Generate the tiny one-sheet workbook as deterministic OpenXML, encoding CR as a character reference and using inline strings. Keep openpyxl/defusedxml for reading external workbooks.
## Tried and ruled out
The openpyxl 3.1.5 writer with the pure-Python et-xmlfile backend on Windows changed embedded CRLF into CRCRLF in worksheet XML. XML parsing then produced two LF characters. Normalizing ZIP timestamps fixed reproducibility but did not fix this data change. Do not normalize the original value to hide it.
## Watch out
Test the extended probes in every format, not just the original default set. Standalone CR, LF and CRLF inside values are distinct data. Spreadsheet literals must never become formula elements.
In the code: rowcanary/formats.py encode_probes; tests/test_formats.py test_extended_probes_preserve_crlf_in_every_format.
