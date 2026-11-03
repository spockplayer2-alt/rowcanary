# Release process

Public maintainer identity: **Spockplayer2** (`spockplayer2-alt`).
Repository: https://github.com/spockplayer2-alt/rowcanary

Description: Detect silent data changes during import/export workflows with local control samples.
Topics: `python`, `cli`, `csv`, `json`, `data-integrity`, `data-quality`, `import-export`, `testing`.

## Release requirements

1. Keep the scope small, preserve exact-data comparisons and review the README,
   examples, limitations and security guidance against actual CLI behavior.
2. Inspect tracked files and distribution contents for credentials, private data,
   personal identifiers and local machine paths. Use the public maintainer identity
   and GitHub noreply address for public commits. Keep internal notes private.
3. Run tests, Ruff, the package build, Twine validation, package inspection and
   vector/PNG checks. See [verification](verification.md).
4. Push the reviewed commit and wait for every required GitHub Actions job to
   succeed on the supported OS/Python matrix, packaging and assets. Investigate
   failures instead of bypassing them.
5. Build the final wheel and sdist from the reviewed source; verify clean installs.
   Create a source ZIP from the release commit and compute SHA-256 checksums.
6. Tag the reviewed commit and publish the GitHub release with professional English
   [release notes](release-notes.md), the verified packages, source ZIP and checksums.
7. Confirm the repository, release notes and every attachment are publicly accessible.

The social preview is [assets/social-preview.png](../assets/social-preview.png),
1280 x 640 pixels. The project uses the MIT license. XLSX uses openpyxl and
defusedxml; text formats and the CLI use Python's standard library.

**PyPI publication requires separate maintainer authorization.** Do not add an
automatic PyPI upload step to the release workflow without that authorization.
