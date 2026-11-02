"""Validate self-contained vectors and reproduce every PNG from SVG masters."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
from PIL import Image

ASSETS = Path(__file__).resolve().parents[1] / "assets"


def check() -> None:
    vectors = sorted(ASSETS.glob("*.svg"))
    if {p.name for p in vectors} != {"logo.svg", "logo-dark.svg", "logo-light.svg",
                                    "icon.svg", "social-preview.svg"}:
        raise SystemExit("Expected the five release SVG masters")
    for path in vectors:
        root = ET.fromstring(path.read_bytes())
        paths = 0
        for element in root.iter():
            name = element.tag.rsplit("}", 1)[-1]
            if name in {"image", "script", "foreignObject", "text", "style"}:
                raise SystemExit(f"Unexpected SVG element in {path.name}: {name}")
            paths += name == "path"
            for key, value in element.attrib.items():
                if key.rsplit("}", 1)[-1] == "href" or "url(" in value or key.startswith("on"):
                    raise SystemExit(f"External/active SVG dependency in {path.name}")
        if not paths:
            raise SystemExit(f"No vector paths in {path.name}")
        cairosvg.svg2png(url=str(path))
    exports = [(f"icon-{size}.png", "icon.svg", size, size) for size in (32, 64, 128, 256)]
    exports += [("logo-512.png", "icon.svg", 512, 512),
                ("social-preview.png", "social-preview.svg", 1280, 640)]
    for png, master, width, height in exports:
        expected = Image.open(io.BytesIO(cairosvg.svg2png(
            url=str(ASSETS / master), output_width=width, output_height=height,
        ))).convert("RGBA")
        with Image.open(ASSETS / png) as actual:
            if actual.size != (width, height):
                raise SystemExit(f"Wrong PNG size: {png}")
            if expected.tobytes() != actual.convert("RGBA").tobytes():
                raise SystemExit(f"PNG differs from its SVG master: {png}")
    print("PASS: 5 self-contained SVGs rendered; 6 PNGs match SVG exports at required sizes.")


if __name__ == "__main__":
    check()
