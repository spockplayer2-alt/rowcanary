# Release verification — 2026-11-02

This report describes the reviewed source in this release preparation. The
original source had 21 tests. The current suite has 65 tests, including parser,
real CLI subprocess and README transcript regressions.

## Executed test matrix

`python -m unittest discover -s tests -v` passed with 65 tests and no skips in
each environment below: 650 successful test executions in total.

| Environment | Python versions | Result |
| --- | --- | --- |
| Native Windows | 3.10.20, 3.11.15, 3.12.11, 3.13.15, 3.14.0 | 65/65 in each |
| Linux, official Python slim Docker images, Debian 13 | 3.10.22, 3.11.18, 3.12.16, 3.13.18, 3.14.10 | 65/65 in each |

The Linux tests ran with a read-only source mount and container networking
disabled. Native macOS and GitHub-hosted runners were not executed.

Coverage includes UTF-8/BOM and invalid bytes; CSV quoting, commas, semicolon,
pipe and tab delimiters; Unicode and output under ASCII/cp1252; exact CR/LF/CRLF
cell differences; empty versus absent values; JSON numeric types/precision,
large exponents and 5,000-digit integer tokens; corrupt/empty/nested documents;
duplicate keys/headers; record order/missing/duplicate/unexpected rows; blank
CSV records; file/row/field limits; exclusive creation and both existing and
dangling symlinks. Symlink tests actually ran in the listed environments.

The new regressions were first run against the original implementation and
reproduced failures before fixes. Formula-like controls were only parsed and
compared as data; no spreadsheet or formula engine was executed.

## Packaging and installation

- `python -m build` built an sdist and then built a wheel from that sdist, using
  an isolated setuptools build environment.
- `python -m twine check dist/*` passed for both distributions.
- `python tools/check_package.py dist` verified modules, entry point, license,
  source assets/tests/docs and absence of private/development files in the wheel.
  The wheel has 10 members and no runtime dependencies. The sdist includes the
  editable vector sources, fixtures, tests and development tools.
- Three separate clean Python 3.14 virtual environments installed from
  `pyproject.toml` (`pip install .`), the wheel and the sdist, respectively.
  From temporary directories outside the checkout, each installation passed
  module demo/make/check, installed console version/check, altered-data exit 1,
  refusal to overwrite exit 2 and missing-input JSON error exit 2.
- The README demo transcript is compared with actual output by an automated
  test. Local Markdown/HTML asset links were checked for existing targets.

## Static, security and visual checks

- Ruff static checks passed, targeting Python 3.10 syntax.
- The code and tests were reviewed for exact-data handling, unsafe execution,
  overwrites, temporary files, resource bounds and error handling.
- A release-file scan for private keys, GitHub tokens, AWS access keys and
  credential assignments found no matching secrets. This is a pattern scan,
  not a guarantee against every possible secret. PNGs had no EXIF, author,
  comment or description metadata fields.
- All five SVG masters parsed and rendered with CairoSVG. They contain actual
  paths/shapes, with no raster embedding, scripts, external references or live
  fonts. The original raster remains as a provenance reference.
- All six PNG exports matched fresh SVG renders byte-for-byte in RGBA pixels.
  Sizes are 32/64/128/256 square icons, a 512-square logo and a 1280 × 640 social
  image. The mark and social composition were visually inspected, including
  the 32px icon and dark/light background treatments.
- Workflow YAML was parsed: a 15-combination OS/Python matrix plus package and
  asset jobs. Action revisions are pinned to verified upstream commit SHAs.

## Pending or outside verified scope

- Native macOS, Ubuntu runners and all GitHub Actions runs. Configured jobs do
  not count as executed checks. The verified Linux environment is Debian Docker.
- Live round trips through Excel, Google Sheets, CRMs or other applications.
- A process-memory ceiling: JSON objects/reports consume memory beyond the
  32 MiB byte cap; JSON row count is checked after parsing.
- Complete protection against concurrent hostile replacement of filesystem
  parent directories/reparse points; see [limitations](limitations.md).
- GitHub-hosted checks and public release URLs will be recorded after the
  hosted checks complete. A release is published only after every required
  job succeeds.
- PyPI upload, external security certification, name/trademark clearance and
  verification of future Python versions are not included.

See [the release process](publication.md) for repository metadata and release
verification requirements.
