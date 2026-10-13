"""Convert the Pixel Operator TTFs (CC0, Jayvee Enaguas) to the BDF files the game loads.

    uv run --with pillow python -I tools/import_font.py FONT_DIR

FONT_DIR holds the unzipped Pixel Operator release (https://www.dafont.com/pixel-operator.font). Each face is drawn
at its design size, so every pixel is a whole pixel, then the rows that no ASCII glyph uses are cut from the top
and the bottom. The game (and `queen/ui/layout.py`, which reads the advance widths without pyxel) loads the BDFs.
"""

import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fonts" / "pixel-operator"

# BDF name: (TTF, design size in px). The keys match FONTS in queen/ui/layout.py.
FACES = {
    "s": ("PixelOperator8.ttf", 8),
    "m": ("PixelOperator.ttf", 16),
    "l": ("PixelOperator-Bold.ttf", 16),
    "xl": ("PixelOperator-Bold.ttf", 32),
}
CHARS = [chr(c) for c in range(32, 127)]


def convert(ttf: Path, size: int, name: str) -> str:
    font = ImageFont.truetype(str(ttf), size)
    ascent, descent = font.getmetrics()
    tall = ascent + descent
    glyphs = {}
    for ch in CHARS:
        adv = round(font.getlength(ch))
        img = Image.new("1", (size * 2, tall), 0)
        d = ImageDraw.Draw(img)
        d.fontmode = "1"
        d.text((0, 0), ch, font=font, fill=1)
        glyphs[ch] = (adv, img)
    rows = [y for _, img in glyphs.values() for y in range(tall) if any(img.getpixel((x, y)) for x in range(size * 2))]
    top, bottom = min(rows), max(rows) + 1
    h = bottom - top
    base = ascent - top  # Rows above the baseline after the cut.
    widths = {ch: _ink_w(img, size, top, bottom) for ch, (_, img) in glyphs.items()}
    out = [
        "STARTFONT 2.1",
        f"FONT -queen-{name}",
        f"SIZE {size} 72 72",
        f"FONTBOUNDINGBOX {max(widths.values())} {h} 0 {base - h}",
        "STARTPROPERTIES 2",
        f"FONT_ASCENT {base}",
        f"FONT_DESCENT {h - base}",
        "ENDPROPERTIES",
        f"CHARS {len(glyphs)}",
    ]
    for ch, (adv, img) in glyphs.items():
        w = widths[ch]
        out += [
            f"STARTCHAR U+{ord(ch):04X}",
            f"ENCODING {ord(ch)}",
            f"SWIDTH {adv * 1000 // size} 0",
            f"DWIDTH {adv} 0",
            f"BBX {w} {h} 0 {base - h}",
            "BITMAP",
        ]
        nbytes = (w + 7) // 8
        for y in range(top, bottom):
            bits = 0
            for x in range(w):
                if img.getpixel((x, y)):
                    bits |= 1 << (nbytes * 8 - 1 - x)
            out.append(f"{bits:0{nbytes * 2}X}")
        out.append("ENDCHAR")
    out.append("ENDFONT")
    return "\n".join(out) + "\n"


def _ink_w(img, size: int, top: int, bottom: int) -> int:
    cols = [x for x in range(size * 2) for y in range(top, bottom) if img.getpixel((x, y))]
    return max(cols) + 1 if cols else 1


def main(src: Path):
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (ttf, size) in FACES.items():
        (OUT / f"{name}.bdf").write_text(convert(src / ttf, size, name))
    shutil.copy(src / "LICENSE.txt", OUT / "LICENSE")
    print(f"wrote {len(FACES)} fonts to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
