"""Screen geometry at 540x1170 (GDD 14). Scenes use it for touch hit tests; render uses it to draw. No pyxel.

Every rect is (x, y, w, h) in logical pixels.
"""

import math
from dataclasses import dataclass

from ..config import ASSETS, SAFE_BOTTOM, SAFE_TOP, H, W

# --- Text (Atkinson Hyperlegible, proportional: widths and heights are read from the BDF files, so no pyxel is needed)

FONT_DIR = ASSETS / "fonts" / "atkinson"
FONTS = ("s", "m", "l", "xl")  # assets/fonts/atkinson/<name>.bdf: small, body, bold body, headings.
LEADING = 3  # Px between lines.
_WIDTHS: dict[str, dict[str, int]] = {}
_HEIGHTS: dict[str, int] = {}


def _load(font: str):
    w = _WIDTHS[font] = {}
    ch = None
    for line in (FONT_DIR / f"{font}.bdf").read_text().splitlines():
        if line.startswith("FONTBOUNDINGBOX "):
            _HEIGHTS[font] = int(line.split()[2])
        elif line.startswith("ENCODING "):
            ch = chr(int(line.split()[1]))
        elif line.startswith("DWIDTH ") and ch is not None:
            w[ch] = int(line.split()[1])


def advances(font: str) -> dict[str, int]:
    """Each glyph's advance width (DWIDTH), parsed once from the font's BDF."""
    if font not in _WIDTHS:
        _load(font)
    return _WIDTHS[font]


def text_w(s: str, font: str = "m") -> int:
    w = advances(font)
    return sum(w.get(c, w["?"]) for c in s)


def font_h(font: str = "m") -> int:
    """The height of the font's ink, from the top of a capital to the bottom of a descender."""
    if font not in _HEIGHTS:
        _load(font)
    return _HEIGHTS[font]


def line_h(font: str = "m") -> int:
    """The step from one line to the next."""
    return font_h(font) + LEADING


def clip(s: str, width: int, font: str = "m") -> str:
    """`s` cut to fit `width` pixels."""
    while s and text_w(s, font) > width:
        s = s[:-1]
    return s


def wrap(s: str, width: int, font: str = "m") -> list[str]:
    """Greedy word wrap to `width` pixels."""
    lines: list[str] = []
    for para in s.split("\n"):
        line = ""
        for word in para.split():
            while text_w(word, font) > width:
                if line:
                    lines.append(line)
                    line = ""
                part = clip(word, width, font) or word[0]
                lines.append(part)
                word = word[len(part) :]
            if not line:
                line = word
            elif text_w(line + " " + word, font) <= width:
                line += " " + word
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


# --- Battle (GDD 14.2)

TOP_BAR = (0, 0, W, SAFE_TOP + 44)
FEET_Y = 440  # Enemies stand on this line.
HP_BAR_Y = 450
DICE_Y = 540
HERO_FEET = (96, 836)
HERO_INFO = (204, 600)  # Name, health, nerve and statuses, right of Rook.
WEAPON_BOX = (204, 708, 326, 84)
GEAR_ROW_Y = 800
PLAY_LINE = 836
PILE_DRAW = (12, 848, 70, 56)
PILE_DISCARD = (90, 848, 70, 56)
ENERGY = (212, 876)
END_TURN = (318, 848, 210, 56)
CARD_W, CARD_H = 104, 216
HAND_Y = H - SAFE_BOTTOM - CARD_H // 2 - 16  # The centre line of a resting card: the fan clears the gesture bar.
LIFT = 64  # How far a lifted card rises.
INSPECT = (20, SAFE_TOP + 12, W - 40, H - SAFE_TOP - SAFE_BOTTOM - 24)
DIE = 32  # The side of a die in the tray.


def die_lands(i: int) -> int:
    """The frame of the roll at which die `i` lands: they land in turn (render/battle.py `dice`)."""
    return 30 + i * 5


def battle_scale(n: int) -> int:
    """Sprites draw at 3x in battle, or 2x when four or more enemies share the line."""
    return 3 if n <= 3 else 2


def foe_scale(rec, n: int = 1) -> float:
    return battle_scale(n) * rec.scale


def foe_x(i: int, n: int) -> int:
    """The centre x of enemy `i` of `n`: the middle of its share of the width, for any number of enemies."""
    if n == 2:
        return (W // 4, W * 3 // 4)[i]
    return round(W * (i + 0.5) / max(1, n))


def foe_rect(i: int, n: int, w: int, h: int) -> tuple[int, int, int, int]:
    """The touch rect of an enemy whose sprite is w x h (after scale)."""
    cx = foe_x(i, n)
    tw = max(80, min(w, W // max(1, n)))
    return (cx - tw // 2, FEET_Y - h - 10, tw, h + 50)


def intent_rect(i: int, n: int, h: int) -> tuple[int, int, int, int]:
    """The touch rect of the intent badge over enemy `i` of `n`, whose sprite is h tall (after scale)."""
    cx = foe_x(i, n)
    return (cx - 44, FEET_Y - h - 48, 88, 48)


@dataclass
class Slot:
    x: float
    y: float
    rot: float = 0.0
    scale: float = 1.0


def hand_slots(n: int, lifted: int | None = None) -> list[Slot]:
    """Where each of `n` hand cards rests: a fan along a shallow arc (GDD 14.2)."""
    if n == 0:
        return []
    span = W - 8 - CARD_W
    gap = min(CARD_W + 2, span / (n - 1)) if n > 1 else 0  # Five cards overlap by their frames; more overlap more.
    x0 = W / 2 - gap * (n - 1) / 2
    out = []
    for i in range(n):
        x = x0 + gap * i
        dx = x - W / 2
        slot = Slot(x, HAND_Y + int(dx * dx / 3600))  # No tilt: rotated 1-bit text does not read.
        if lifted is not None and i != lifted and gap < CARD_W - 8:  # Spread a crowded hand around the lifted card.
            push = 28
            slot.x += push if i > lifted else -push
        if i == lifted:
            slot.y -= LIFT  # Lifted at 1x so its text stays sharp.
        out.append(slot)
    return out


def card_at(slots: list[Slot], x: int, y: int, lifted: int | None = None) -> int | None:
    """The hand card under (x, y): the lifted one first, then the topmost (rightmost) of the rest."""
    order = list(range(len(slots) - 1, -1, -1))
    if lifted is not None and lifted < len(slots):
        order.remove(lifted)
        order.insert(0, lifted)
    for i in order:
        s = slots[i]
        hw, hh = CARD_W * s.scale / 2, CARD_H * s.scale / 2
        if s.x - hw <= x < s.x + hw and s.y - hh <= y < s.y + hh + 30:
            return i
    return None


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def arrow_points(x0: float, y0: float, x1: float, y1: float, n: int = 10) -> list[tuple[float, float]]:
    """A curved targeting arrow (StS): a quadratic curve that bows upward."""
    cx, cy = (x0 + x1) / 2, min(y0, y1) - 100
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
        pts.append((x, y))
    return pts


# --- Exploration (GDD 14.4)

MAP_Y = 136  # Location `pos` y is offset by this.
NODE_W, NODE_H = 140, 76
AGENDA_BOX = (12, 744, 252, 118)
ACT_BOX = (276, 744, 252, 118)
ACTION_Y = 876
BUTTON_H = 56


def node_rect(pos: tuple[int, int]) -> tuple[int, int, int, int]:
    x, y = pos
    return (x - NODE_W // 2, y + MAP_Y - NODE_H // 2, NODE_W, NODE_H)


def button_column(n: int, y0: int, h: int = BUTTON_H, gap: int = 10, x: int = 20, w: int = W - 40) -> list[tuple]:
    return [(x, y0 + i * (h + gap), w, h) for i in range(n)]


def button_grid(n: int, y0: int, cols: int = 2, h: int = BUTTON_H, gap: int = 10) -> list[tuple]:
    w = (W - 40 - gap * (cols - 1)) // cols
    return [(20 + (i % cols) * (w + gap), y0 + (i // cols) * (h + gap), w, h) for i in range(n)]


def bottom_buttons(n: int, h: int = 60, gap: int = 12) -> list[tuple]:
    """A column of `n` buttons that ends at the safe bottom."""
    y0 = H - SAFE_BOTTOM - n * h - (n - 1) * gap - 12
    return button_column(n, y0, h, gap)


def distance(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
