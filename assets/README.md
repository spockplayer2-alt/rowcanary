# RowCanary artwork

The original supplied artwork is preserved as `rowcanary-logo.png` (512 × 432).
The vector masters reconstruct its bird/table silhouette, cut-out eye, wing,
beak, table gutter and four colored rows. The geometry uses a small set of
smooth paths rather than pixel tracing. The original subtle raster shading is
replaced by consistent flat fills.

| Asset | Use |
| --- | --- |
| `logo.svg`, `logo-light.svg` | Original navy/mint/gold mark on light backgrounds |
| `logo-dark.svg` | Same mark with a lighter navy and a restrained outline for dark backgrounds |
| `icon.svg` | Square framing of the same geometry; no distortion |
| `icon-{32,64,128,256}.png` | Transparent square exports of `icon.svg` |
| `logo-512.png` | Transparent 512 × 512 export of the square SVG geometry |
| `social-preview.svg`, `social-preview.png` | 1280 × 640 GitHub social image |

Main colors: navy `#152334`, mint `#50d7c3`, gold `#fcb54d`.
All SVGs use actual paths/shapes. None contains a raster image, external asset,
script or live font dependency. Social-preview typography is outlined Noto
Sans, under the included [SIL Open Font License](FONT-LICENSE.txt).

## Regenerate

The CLI does not need these tools. For asset development, install
`python -m pip install -r tools/requirements-assets.txt` from the repository
root. CairoSVG also needs the system Cairo library (on Windows, use a Cairo
installation supported by CairoSVG).

Obtain `NotoSans[wdth,wght].ttf` from the
[Google Fonts Noto Sans directory](https://github.com/google/fonts/tree/main/ofl/notosans).
The font used for this release has SHA-256
`bfb7bb691513f12e734dc346c03a03f784912432d7e3fa8e56efcf906fe86b3d`.
Then run:

```bash
python tools/build_assets.py path/to/NotoSans.ttf
python tools/check_assets.py
```

The generator instantiates weight 600 and width 100, outlines the glyphs and
exports every new PNG from vector geometry. The original raster is a reference
only and is never embedded in the SVGs or used as an export source.
