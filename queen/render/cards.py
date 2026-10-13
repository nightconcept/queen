"""Card faces: drawn once per card into an image (64x90), then blitted with scale and rotation."""

import pyxel

from ..content import CONTENT, Card
from ..ui.cardtext import TIER_NAMES, keyword_help, short_lines, type_line
from ..ui.layout import CARD_H, CARD_W, wrap
from .art import FONT, ICONS, KEY, C, panel, text, text_w

ELEMENT = {"R": "crit", "G": "horror", "K": "blood", "E": "spore", "Z": "shield", None: "ash"}
TYPE_FRAME = {"action": "line", "weapon": "rook", "equipment": "shield", "aura": "horror", "trauma": "blood_dark",
              "spore": "spore"}  # fmt: skip
TIER_GEM = {"B": "ash", "S": "bone", "P": "shield", "X": "crit", "W": "horror", "T": "blood"}
SKILL_COL = {"willpower": "horror", "intellect": "clue", "combat": "blood", "agility": "spore", "wild": "crit"}

_cache: dict[tuple, pyxel.Image] = {}


def face(card: Card) -> pyxel.Image:
    key = (card.id, card.name)
    img = _cache.get(key)
    if img is None:
        img = _cache[key] = _draw_face(card)
    return img


def _rrect(img, x, y, w, h, col):
    img.rect(x + 1, y, w - 2, h, col)
    img.rect(x, y + 1, w, h - 2, col)


def _draw_face(card: Card) -> pyxel.Image:
    img = pyxel.Image(CARD_W, CARD_H)
    img.cls(KEY)
    frame = C(TYPE_FRAME.get(card.type, "line"))
    _rrect(img, 0, 0, CARD_W, CARD_H, C("void"))
    _rrect(img, 1, 1, CARD_W - 2, CARD_H - 2, frame)
    _rrect(img, 3, 3, CARD_W - 6, CARD_H - 6, C("ink"))
    # Name: one or two lines of the small font.
    lines = wrap(card.name, CARD_W - 8, "s")[:2]
    for i, ln in enumerate(lines):
        img.text(CARD_W // 2 - len(ln) * 5 // 2 + 2, 5 + i * 8, ln, C("bone"), FONT["s"])
    # Art box: the element's colour behind the card's icon.
    ay = 22
    img.rect(5, ay, CARD_W - 10, 24, C(ELEMENT.get(card.element, "ash")))
    img.dither(0.5)
    img.rect(5, ay, CARD_W - 10, 24, C("void"))
    img.dither(1.0)
    icons, u = ICONS.get(card.art, ICONS["sword"])
    img.blt(CARD_W // 2 - 8, ay + 4, icons, u, 0, 16, 16, KEY)
    # Type line.
    tl = type_line(card).upper()[:12]
    img.text(CARD_W // 2 - len(tl) * 5 // 2, ay + 26, tl, C("ash"), FONT["s"])
    # Short rules lines.
    y = ay + 36
    for ln in short_lines(card):
        ln = ln[:11]
        img.text(CARD_W // 2 - len(ln) * 5 // 2, y, ln, C("bone"), FONT["s"])
        y += 8
    # Skill icons (bottom left) and the tier gem (bottom right).
    for i, sk in enumerate(card.icons[:3]):
        img.rect(6 + i * 6, CARD_H - 9, 4, 4, C(SKILL_COL.get(sk, "ash")))
    img.rect(CARD_W - 10, CARD_H - 9, 4, 4, C(TIER_GEM.get(card.tier, "ash")))
    if card.name.endswith("+"):
        img.text(CARD_W - 18, CARD_H - 11, "+", C("spore"), FONT["s"])
    return img


def draw_card(card: Card, cx, cy, scale=1.0, rot=0.0, cost: int | None = None, dim=False, glow: str | None = None):
    """A card centred at (cx, cy). `cost` overrides the printed cost (a cost changed by a modifier)."""
    img = face(card)
    x, y = cx - CARD_W / 2, cy - CARD_H / 2
    if glow:
        pyxel.dither(0.6)
        pyxel.rect(
            cx - CARD_W * scale / 2 - 2, cy - CARD_H * scale / 2 - 2, CARD_W * scale + 4, CARD_H * scale + 4, C(glow)
        )
        pyxel.dither(1.0)
    pyxel.blt(x, y, img, 0, 0, CARD_W, CARD_H, KEY, rotate=rot, scale=scale)
    if dim:
        pyxel.dither(0.5)
        pyxel.rect(cx - CARD_W * scale / 2, cy - CARD_H * scale / 2, CARD_W * scale, CARD_H * scale, C("void"))
        pyxel.dither(1.0)
    if card.tier not in ("T",) or card.type == "spore":
        c = card.cost if cost is None else cost
        ox, oy = cx - (CARD_W / 2 - 1) * scale, cy - (CARD_H / 2 - 1) * scale  # On the corner, as in StS.
        col = "energy" if cost is None or cost == card.cost else ("spore" if cost < card.cost else "blood")
        pyxel.circ(ox, oy, 7 * min(scale, 1.4), C("void"))
        pyxel.circ(ox, oy, 6 * min(scale, 1.4), C(col))
        pyxel.text(ox - 2, oy - 5, str(c), C("void"), FONT["m"])


def inspect_panel(card: Card, inst=None, x=None, y=None):
    """The large view of a card (GDD 4: tap and hold): the face at 2x, then the full text and keywords."""
    from ..ui.layout import INSPECT

    ix, iy, iw, ih = INSPECT
    if x is not None:
        ix, iy = x, y
    pyxel.dither(0.85)
    pyxel.rect(0, 0, pyxel.width, pyxel.height, C("void"))
    pyxel.dither(1.0)
    panel(ix, iy, iw, ih + 80, fill="ink", border="line")
    draw_card(card, ix + iw // 2, iy + 98, scale=2.0)
    ty = iy + 196
    text(ix + 8, ty, f"{TIER_NAMES.get(card.tier, card.tier)} | {card.set}", "ash", "s", None)
    if inst is not None and card.weapon and inst.durability is not None:
        t = f"Ammo {inst.durability}/{card.weapon.durability}"
        text(ix + iw - 8 - text_w(t, "s"), ty, t, "rook", "s", None)
    ty += 12
    for ln in wrap(card.text, iw - 16, "m"):
        text(ix + 8, ty, ln, "bone", "m", None)
        ty += 12
    ty += 4
    for kw in keyword_help(card):
        for ln in wrap(kw, iw - 16, "s"):
            if ty > iy + ih + 70:
                return
            text(ix + 8, ty, ln, "ash", "s", None)
            ty += 9


def mini_card(card: Card, x, y, w, h, selected=False, dim=False):
    """A card scaled into the rect (x, y, w, h)."""
    s = min(w / CARD_W, h / CARD_H)
    draw_card(card, x + w / 2, y + h / 2, scale=s, dim=dim, glow="crit" if selected else None)


def card_for(cid: str, plus: bool = False) -> Card:
    return CONTENT.card(cid, plus)
