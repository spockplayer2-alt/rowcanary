"""Rebuild vector branding and PNG exports with a locally supplied Noto Sans font.

Development only: install tools/requirements-assets.txt, then run
python tools/build_assets.py path/to/NotoSans.ttf
The exported artwork contains outlined glyphs, with no font dependencies.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ASSETS = Path(__file__).resolve().parents[1] / "assets"
NAVY = "#152334"
MINT = "#50d7c3"
GOLD = "#fcb54d"
WHITE = "#e9f0f6"

# Manually reconstructed from the supplied 512 x 432 raster. One smooth
# silhouette, a cut-out eye, one wing, one beak and four pairs of table cells.
BODY = (
    "M115 148H160C205 148 231 132 258 100"
    "C286 66 315 50 347 50C375 50 398 67 413 90"
    "L400 141V337C400 367 380 386 350 386H113"
    "C83 386 65 367 65 338V198C65 169 86 148 115 148Z"
    "M376 99A14 14 0 1 1 348 99A14 14 0 1 1 376 99Z"
)
WING = "M162 173C218 162 238 140 273 125C298 114 324 120 340 132C311 140 294 170 260 172Z"
BEAK = (
    "M413 90C428 98 442 108 452 115Q457 119 450 122C426 130 402 138 389 147C390 122 398 100 413 90Z"
)


def mark(*, dark: bool = False) -> str:
    body_color = "#203247" if dark else NAVY
    outline = ' stroke="#71859b" stroke-width="1.5"' if dark else ""
    parts = [
        f'<path fill="{body_color}" fill-rule="evenodd" d="{BODY}"{outline}/>',
        f'<path fill="{MINT}" d="{WING}"/>',
        f'<path fill="{GOLD}" d="{BEAK}"/>',
    ]
    for y, color in ((180, MINT), (227, MINT), (272, GOLD), (319, MINT)):
        # Clip just the right corners of the left cell, preserving the central
        # vertical table gutter from the original artwork.
        parts.append(
            f'<path fill="{color}" d="M99 {y}H141V{y + 36}H99Q88 {y + 36} 88 {y + 25}'
            f'V{y + 11}Q88 {y} 99 {y}Z"/>'
        )
        parts.append(
            f'<path fill="{color}" d="M156 {y}H366Q378 {y} 378 {y + 12}'
            f'V{y + 24}Q378 {y + 36} 366 {y + 36}H156Z"/>'
        )
    return "".join(parts)


def svg(
    content: str, title: str, *, width: int = 512, height: int = 432, viewbox: str = "0 0 512 432"
) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="{viewbox}" role="img" aria-labelledby="title">'
        f'<title id="title">{title}</title>{content}</svg>\n'
    )


class Outlines:
    def __init__(self, path: Path):
        source = TTFont(path)
        if "fvar" in source:
            source = instantiateVariableFont(source, {"wght": 600, "wdth": 100})
        self.font = source
        self.glyphs = source.getGlyphSet()
        self.cmap = source.getBestCmap()
        self.upem = source["head"].unitsPerEm

    def text(self, value: str, x: float, baseline: float, size: float, color: str = WHITE) -> str:
        scale = size / self.upem
        parts = [
            f'<g fill="{color}" transform="translate({x} {baseline}) scale({scale:g} {-scale:g})">'
        ]
        cursor = 0
        for character in value:
            name = self.cmap[ord(character)]
            pen = SVGPathPen(self.glyphs)
            self.glyphs[name].draw(pen)
            commands = pen.getCommands()
            if commands:
                parts.append(f'<path transform="translate({cursor} 0)" d="{commands}"/>')
            cursor += self.font["hmtx"][name][0]
        parts.append("</g>")
        return "".join(parts)


def build(font_path: Path) -> None:
    ASSETS.mkdir(exist_ok=True)
    for filename, dark in (("logo.svg", False), ("logo-light.svg", False), ("logo-dark.svg", True)):
        (ASSETS / filename).write_text(
            svg(mark(dark=dark), "RowCanary: a canary shaped like a data table"), encoding="utf-8"
        )
    (ASSETS / "icon.svg").write_text(
        svg(mark(), "RowCanary icon", width=256, height=256, viewbox="40 0 432 432"),
        encoding="utf-8",
    )
    for size in (32, 64, 128, 256):
        cairosvg.svg2png(
            url=str(ASSETS / "icon.svg"),
            write_to=str(ASSETS / f"icon-{size}.png"),
            output_width=size,
            output_height=size,
        )
    cairosvg.svg2png(
        url=str(ASSETS / "icon.svg"),
        write_to=str(ASSETS / "logo-512.png"),
        output_width=512,
        output_height=512,
    )
    outline = Outlines(font_path)
    social = (
        '<path fill="#0d1826" d="M0 0H1280V640H0Z"/>'
        f'<g transform="translate(65 44) scale(.15)">{mark(dark=True)}</g>'
        + outline.text("RowCanary", 151, 96, 40)
        + outline.text("v0.1.0", 1080, 88, 23, "#9eafc2")
        + outline.text("Detect silent", 80, 260, 64)
        + outline.text("data changes.", 80, 338, 64, MINT)
        + outline.text("Control samples for import/export workflows.", 83, 403, 26, "#b8c6d5")
        + f'<g transform="translate(855 170) scale(.72)">{mark(dark=True)}</g>'
        + '<path stroke="#2b3e54" d="M80 508H1200"/>'
        + outline.text("python -m rowcanary demo", 82, 565, 25, MINT)
        + outline.text("CSV + JSON  /  Python 3.10+  /  MIT", 756, 564, 21, "#9eafc2")
    )
    preview = ASSETS / "social-preview.svg"
    preview.write_text(
        svg(
            social,
            "RowCanary v0.1.0: detect silent data changes",
            width=1280,
            height=640,
            viewbox="0 0 1280 640",
        ),
        encoding="utf-8",
    )
    cairosvg.svg2png(url=str(preview), write_to=str(ASSETS / "social-preview.png"))
    print("Wrote 5 self-contained SVG masters and 6 PNG exports.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "font", type=Path, help="Noto Sans variable or static TTF; see assets/README.md"
    )
    build(parser.parse_args().font)
