"""Inspect wheel and source distribution members before release."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path, PurePosixPath


def check(directory: Path) -> None:
    wheels = list(directory.glob("*.whl"))
    sources = list(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise SystemExit("Expected exactly one wheel and one source distribution")
    with zipfile.ZipFile(wheels[0]) as archive:
        wheel = set(archive.namelist())
    with tarfile.open(sources[0]) as archive:
        source = {str(PurePosixPath(n).relative_to(n.split("/")[0])) for n in archive.getnames()}
    modules = {f"rowcanary/{path.name}" for path in Path("rowcanary").glob("*.py")}
    modules.add("rowcanary/report.schema.json")
    modules |= {
        f"rowcanary/static/{name}" for name in ("index.html", "app.css", "app.js", "icon.svg")
    }
    required = modules | {
        "README.md",
        "LICENSE",
        "pyproject.toml",
        "MANIFEST.in",
        ".gitattributes",
        ".github/workflows/tests.yml",
        "tests/test_core.py",
        "tests/test_cli.py",
        "tests/test_parsing.py",
        "tests/test_cli_process.py",
        "tests/test_documentation.py",
        "examples/clean.csv",
        "examples/clean.json",
        "examples/altered.csv",
        "docs/publication.md",
        "docs/verification.md",
        "docs/release-notes.md",
        "assets/logo.svg",
        "assets/logo-dark.svg",
        "assets/logo-light.svg",
        "assets/icon.svg",
        "assets/logo-512.png",
        "assets/social-preview.svg",
        "assets/social-preview.png",
        "assets/FONT-LICENSE.txt",
    }
    required |= {f"assets/icon-{size}.png" for size in (32, 64, 128, 256)}
    if not modules <= wheel or not required <= source:
        raise SystemExit(
            f"Missing package members: wheel={modules - wheel}; source={required - source}"
        )
    if not any(n.endswith(".dist-info/entry_points.txt") for n in wheel):
        raise SystemExit("Wheel lacks its console entry point")
    if not any(n.endswith(".dist-info/licenses/LICENSE") for n in wheel):
        raise SystemExit("Wheel lacks the MIT license")
    forbidden = {".git", ".venv", ".local", ".trail", "__pycache__", ".env", "AGENTS.md"}
    for name in wheel | source:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or forbidden.intersection(path.parts):
            raise SystemExit(f"Unexpected archive member: {name}")
        if name.endswith((".pyc", ".pyo", ".ttf", ".key", ".pem")):
            raise SystemExit(f"Unexpected generated/private file: {name}")
    if any(n.startswith(("assets/", "tests/", "docs/", "tools/")) for n in wheel):
        raise SystemExit("Wheel unexpectedly includes development files")
    print(
        f"PASS: {len(wheel)} wheel members; {len(source)} source members; no development/private files in wheel."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    check(parser.parse_args().directory)
