"""Art, fonts and colours, loaded once after pyxel.init (`bake`). Every drawing helper the screens share."""

import math

import pyxel

from ..config import ASSETS
from ..content import CONTENT
from ..ui.layout import (
    FONT_DIR,
    FONTS,
    clip,  # noqa: F401  (for the screens)
)
from ..ui.layout import text_w as _text_w

FONT: dict[str, pyxel.Font] = {}
SPRITES: dict[str, dict] = {}
BG: dict[str, pyxel.Image] = {}
ICONS: dict[str, tuple[pyxel.Image, int]] = {}
ICON_IMG: list[pyxel.Image] = []
KEY = 0


def C(name: str) -> int:
    """A palette index by colour name (data/palette.json)."""
    return CONTENT.colour[name]


def bake():
    art = CONTENT.art
    for name in FONTS:
        FONT[name] = pyxel.Font(str(FONT_DIR / f"{name}.bdf"))
    for name, rec in art["sprites"].items():
        SPRITES[name] = {**rec, "img": pyxel.Image.from_image(str(ASSETS / "art" / rec["file"]))}
    for name, rec in art["backgrounds"].items():
        BG[name] = pyxel.Image.from_image(str(ASSETS / "art" / rec["file"]))
    icons = pyxel.Image.from_image(str(ASSETS / "art" / art["icons"]["file"]))
    ICON_IMG.append(icons)
    for i, name in enumerate(art["icons"]["names"]):
        ICONS[name] = (icons, i * 16)


# --- Text


def text(x, y, s, col="bone", font="m", shadow: str | None = "void"):
    f = FONT[font]
    if shadow:
        pyxel.text(x + 1, y + 1, s, C(shadow), f)
    pyxel.text(x, y, s, C(col), f)


def text_w(s: str, font="m") -> int:
    return _text_w(s, font)


def center(cx, y, s, col="bone", font="m", shadow: str | None = "void"):
    text(cx - text_w(s, font) // 2, y, s, col, font, shadow)


def right(rx, y, s, col="bone", font="m", shadow: str | None = "void"):
    text(rx - text_w(s, font), y, s, col, font, shadow)


def big(cx, y, s, col="bone", scale=1, shadow="void"):
    """Large text: the 12x24 font, optionally drawn bigger by scaling a scratch image."""
    if scale == 1:
        center(cx, y, s, col, "xl", shadow)
        return
    w, h = text_w(s, "xl") + 2, 28
    img = pyxel.Image(w, h)
    img.cls(KEY)
    img.text(1, 1, s, C(shadow), FONT["xl"])
    img.text(0, 0, s, C(col), FONT["xl"])
    pyxel.blt(cx - w / 2, y + h * (scale - 1) / 2, img, 0, 0, w, h, KEY, scale=scale)


# --- Sprites and icons


def frame_of(name: str, anim: str, t: int, rate: int = 8, loop: bool = True) -> int:
    rec = SPRITES[name]
    start, count = rec["anims"].get(anim, rec["anims"].get("idle", [0, 1]))
    i = t // rate
    i = i % count if loop else min(i, count - 1)
    return start + i


def sprite(name: str, frame: int, cx, feet_y, scale=1.0, flip=False, white=False):
    rec = SPRITES[name]
    w, h = rec["w"], rec["h"]
    x = cx - w / 2
    y = feet_y - h - (h * (scale - 1)) / 2
    if white:
        for c in range(1, len(pyxel.colors)):
            pyxel.pal(c, C("white"))
    pyxel.blt(x, y, rec["img"], frame * w, 0, -w if flip else w, h, KEY, scale=scale)
    if white:
        pyxel.pal()


def icon(name: str, x, y, scale=1.0):
    img, u = ICONS[name]
    pyxel.blt(x, y, img, u, 0, 16, 16, KEY, scale=scale)


def background(name: str, x, y, w, h, sx=0, sy=0):
    pyxel.blt(x, y, BG[name], sx, sy, w, h)


def dim(x, y, w, h, alpha=0.5, col="void"):
    pyxel.dither(alpha)
    pyxel.rect(x, y, w, h, C(col))
    pyxel.dither(1.0)


# --- Panels and buttons


def panel(x, y, w, h, fill="panel", border="line", radius=3):
    x, y, w, h = int(x), int(y), int(w), int(h)
    r = radius
    pyxel.rect(x + r, y, w - 2 * r, h, C(fill))
    pyxel.rect(x, y + r, w, h - 2 * r, C(fill))
    for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r), (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
        pyxel.circ(cx, cy, r, C(fill))
    if border:
        pyxel.line(x + r, y, x + w - r - 1, y, C(border))
        pyxel.line(x + r, y + h - 1, x + w - r - 1, y + h - 1, C(border))
        pyxel.line(x, y + r, x, y + h - r - 1, C(border))
        pyxel.line(x + w - 1, y + r, x + w - 1, y + h - r - 1, C(border))
        for cx, cy, sx, sy in ((x + r, y + r, -1, -1), (x + w - r - 1, y + r, 1, -1), (x + r, y + h - r - 1, -1, 1),
                               (x + w - r - 1, y + h - r - 1, 1, 1)):  # fmt: skip
            for a in range(0, 91, 15):
                px = cx + sx * round(r * math.cos(math.radians(a)))
                py = cy + sy * round(r * math.sin(math.radians(a)))
                pyxel.pset(px, py, C(border))


STYLES = {
    "normal": ("panel_hi", "line", "bone"),
    "primary": ("rook", "energy", "void"),
    "danger": ("blood_dark", "blood", "bone"),
    "ghost": ("ink", "line", "ash"),
}


def button(b, focused=False, pressed=False):
    if b.style == "node":
        return
    x, y, w, h = b.rect
    fill, border, ink = STYLES.get(b.style, STYLES["normal"])
    if not b.enabled:
        fill, border, ink = "ink", "panel_hi", "line"
    oy = 2 if pressed else 0
    if not pressed:
        panel(x, y + 2, w, h, fill="void", border=None)
    panel(x, y + oy, w, h, fill=fill, border="white" if focused else border)
    shadow = None if b.style == "primary" else "void"
    note_ink = ink if b.style == "primary" else "ash"
    if b.note and h < 36:  # A short row: the label on the left, the note on the right.
        text(x + 10, y + oy + (h - 13) // 2, clip(b.label, w - 30 - text_w(b.note)), ink, "m", shadow)
        right(x + w - 10, y + oy + (h - 13) // 2, b.note, note_ink, "m", None)
    elif b.note:
        center(x + w // 2, y + oy + h // 2 - 13, b.label, ink, "m", shadow)
        center(x + w // 2, y + oy + h // 2 + 1, b.note, note_ink, "m", None)
    else:
        center(x + w // 2, y + oy + (h - 13) // 2, b.label, ink, "m", shadow)


def menu(m):
    for i, b in enumerate(m.buttons):
        button(b, focused=(i == m.cursor), pressed=(i == m.pressed))


def bar(x, y, w, h, value, top, fill="blood", back="blood_dark", ghost=0, ghost_col="white"):
    pyxel.rect(x, y, w, h, C("void"))
    pyxel.rect(x + 1, y + 1, w - 2, h - 2, C(back))
    if top > 0:
        fw = int((w - 2) * max(0, value) / top)
        pyxel.rect(x + 1, y + 1, fw, h - 2, C(fill))
        if ghost > 0:
            gw = int((w - 2) * min(value, ghost) / top)
            pyxel.dither(0.5 + 0.5 * math.sin(pyxel.frame_count / 4))
            pyxel.rect(x + 1 + fw - gw, y + 1, gw, h - 2, C(ghost_col))
            pyxel.dither(1.0)


def pips(x, y, n, top, col="energy", off="panel_hi", size=4, gap=2):
    for i in range(top):
        pyxel.rect(x + i * (size + gap), y, size, size, C(col if i < n else off))


def orb(cx, cy, r, col, value: str, font="l"):
    pyxel.circ(cx, cy, r + 1, C("void"))
    pyxel.circ(cx, cy, r, C(col))
    pyxel.circ(cx - r // 3, cy - r // 3, max(1, r // 3), C("white"))
    center(cx, cy - FONTS[font] // 2 + 1, value, "void", font, None)
