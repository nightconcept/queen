"""Screen geometry at 320x714 (GDD 14). Scenes use it for touch hit tests; render uses it to draw. No pyxel.

Every rect is (x, y, w, h) in logical pixels.
"""

import math
from dataclasses import dataclass

from ..config import ASSETS, SAFE_BOTTOM, SAFE_TOP, H, W

# --- Text (Pixel Operator, proportional: the widths are read from the BDF files, so no pyxel is needed)

FONT_DIR = ASSETS / "fonts" / "pixel-operator"
FONTS = {"s": 8, "m": 13, "l": 13, "xl": 26}  # Font name -> line height. assets/fonts/pixel-operator/<name>.bdf
_WIDTHS: dict[str, dict[str, int]] = {}


def advances(font: str) -> dict[str, int]:
    """Each glyph's advance width (DWIDTH), parsed once from the font's BDF."""
    w = _WIDTHS.get(font)
    if w is None:
        w = _WIDTHS[font] = {}
        ch = None
        for line in (FONT_DIR / f"{font}.bdf").read_text().splitlines():
            if line.startswith("ENCODING "):
                ch = chr(int(line.split()[1]))
            elif line.startswith("DWIDTH ") and ch is not None:
                w[ch] = int(line.split()[1])
    return w


def text_w(s: str, font: str = "m") -> int:
    w = advances(font)
    return sum(w.get(c, w["?"]) for c in s)


def font_h(font: str = "m") -> int:
    return FONTS[font]


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

TOP_BAR = (0, 0, W, SAFE_TOP + 34)
FEET_Y = 262  # Enemies stand on this line.
HP_BAR_Y = 268
DICE_Y = 330
HERO_FEET = (52, 470)
WEAPON_BOX = (160, 392, 152, 50)
GEAR_ROW_Y = 446
PLAY_LINE = 480
PILE_DRAW = (8, 490, 40, 30)
PILE_DISCARD = (52, 490, 40, 30)
ENERGY = (122, 505)
END_TURN = (210, 488, 102, 34)
CARD_W, CARD_H = 66, 120
HAND_Y = H - SAFE_BOTTOM - CARD_H // 2 - 6  # The centre line of a resting card.
INSPECT = (12, 40, W - 24, 640)


def die_lands(i: int) -> int:
    """The frame of the roll at which die `i` lands: they land in turn (render/battle.py `dice`)."""
    return 30 + i * 5


BATTLE_SCALE = 2  # Sprites draw at 2x in battle: the packs' creatures are small.


def foe_scale(rec) -> float:
    return BATTLE_SCALE * rec.scale


def foe_x(i: int, n: int) -> int:
    """The centre x of enemy `i` of `n`."""
    return {1: [160], 2: [100, 220], 3: [56, 160, 264], 4: [42, 122, 200, 280]}[max(1, min(4, n))][i]


def foe_rect(i: int, n: int, w: int, h: int) -> tuple[int, int, int, int]:
    """The touch rect of an enemy whose sprite is w x h (after scale)."""
    cx = foe_x(i, n)
    tw = max(48, min(w, W // max(1, n)))
    return (cx - tw // 2, FEET_Y - h - 10, tw, h + 30)


def intent_rect(i: int, n: int, h: int) -> tuple[int, int, int, int]:
    """The touch rect of the intent badge over enemy `i` of `n`, whose sprite is h tall (after scale)."""
    cx = foe_x(i, n)
    return (cx - 28, FEET_Y - h - 30, 56, 30)


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
    span = W - 6 - CARD_W
    gap = min(CARD_W + 2, span / (n - 1)) if n > 1 else 0  # Five cards overlap by their frames; more overlap more.
    x0 = W / 2 - gap * (n - 1) / 2
    out = []
    for i in range(n):
        x = x0 + gap * i
        dx = x - W / 2
        slot = Slot(x, HAND_Y + int(dx * dx / 1400))  # No tilt: rotated pixel text does not read.
        if lifted is not None and i != lifted and gap < CARD_W - 8:  # Spread a crowded hand around the lifted card.
            push = 18
            slot.x += push if i > lifted else -push
        if i == lifted:
            slot.y -= 36  # Lifted at 1x so its text stays sharp.
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
        if s.x - hw <= x < s.x + hw and s.y - hh <= y < s.y + hh + 20:
            return i
    return None


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def arrow_points(x0: float, y0: float, x1: float, y1: float, n: int = 10) -> list[tuple[float, float]]:
    """A curved targeting arrow (StS): a quadratic curve that bows upward."""
    cx, cy = (x0 + x1) / 2, min(y0, y1) - 60
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1
        pts.append((x, y))
    return pts


# --- Exploration (GDD 14.4)

MAP_Y = 64  # Location `pos` y is offset by this.
NODE_W, NODE_H = 84, 46
AGENDA_BOX = (8, 430, 148, 74)
ACT_BOX = (164, 430, 148, 74)
ACTION_Y = 516
BUTTON_H = 36


def node_rect(pos: tuple[int, int]) -> tuple[int, int, int, int]:
    x, y = pos
    return (x - NODE_W // 2, y + MAP_Y - NODE_H // 2, NODE_W, NODE_H)


def button_column(n: int, y0: int, h: int = BUTTON_H, gap: int = 6, x: int = 12, w: int = W - 24) -> list[tuple]:
    return [(x, y0 + i * (h + gap), w, h) for i in range(n)]


def button_grid(n: int, y0: int, cols: int = 2, h: int = BUTTON_H, gap: int = 6) -> list[tuple]:
    w = (W - 24 - gap * (cols - 1)) // cols
    return [(12 + (i % cols) * (w + gap), y0 + (i // cols) * (h + gap), w, h) for i in range(n)]


def bottom_buttons(n: int, h: int = 40, gap: int = 8) -> list[tuple]:
    """A column of `n` buttons that ends at the safe bottom."""
    y0 = H - SAFE_BOTTOM - n * h - (n - 1) * gap - 8
    return button_column(n, y0, h, gap)


def distance(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
