"""Card faces: drawn once per card into an image (104x216), then blitted (scaled only while a card moves)."""

import pyxel

from ..content import CONTENT, Card
from ..ui.cardtext import EQUIP, FACE_RULES, FACE_W, TIER_NAMES, face_name, face_rules, keyword_help, type_line
from ..ui.layout import CARD_H, CARD_W, clip, font_h, line_h, wrap
from .art import FONT, ICONS, KEY, C, panel, text, text_w

ELEMENT = {"R": "crit", "G": "horror", "K": "blood", "E": "spore", "Z": "shield", None: "ash"}
TYPE_FRAME = {"action": "line", "weapon": "rook", "equipment": "shield", "aura": "horror", "trauma": "blood_dark",
              "spore": "spore"}  # fmt: skip
TIER_GEM = {"B": "ash", "S": "bone", "P": "shield", "X": "crit", "W": "horror", "T": "blood"}
SKILL_COL = {"willpower": "horror", "intellect": "clue", "combat": "blood", "agility": "spore", "wild": "crit"}

NAME_BAND = (6, 46)  # y and height of the name band.
ART_Y, ART_H = 54, 38
TYPE_Y = 96
RULES_Y, RULES_STEP = 117, 21

_cache: dict[tuple, pyxel.Image] = {}


def face(card: Card) -> pyxel.Image:
    key = (card.id, card.name)
    img = _cache.get(key)
    if img is None:
        img = _cache[key] = _draw_face(card)
    return img


def _rrect(img, x, y, w, h, col):
    img.rect(x + 2, y, w - 4, h, col)
    img.rect(x + 1, y + 1, w - 2, h - 2, col)
    img.rect(x, y + 2, w, h - 4, col)


def _draw_face(card: Card) -> pyxel.Image:
    img = pyxel.Image(CARD_W, CARD_H)
    img.cls(KEY)
    frame = C(TYPE_FRAME.get(card.type, "line"))
    _rrect(img, 0, 0, CARD_W, CARD_H, C("void"))
    _rrect(img, 1, 1, CARD_W - 2, CARD_H - 2, frame)
    _rrect(img, 4, 4, CARD_W - 8, CARD_H - 8, C("ink"))
    # Name: up to two lines, centred in the top band.
    font, lines = face_name(card)
    by, bh = NAME_BAND
    step = line_h(font)
    ny = by + (bh - step * len(lines) + 3) // 2
    for i, ln in enumerate(lines):
        _ctext(img, ny + i * step, ln, "bone", font)
    # Art box: the element's colour behind the card's icon at 2x.
    img.rect(7, ART_Y, CARD_W - 14, ART_H, C(ELEMENT.get(card.element, "ash")))
    img.dither(0.5)
    img.rect(7, ART_Y, CARD_W - 14, ART_H, C("void"))
    img.dither(1.0)
    icons, u = ICONS.get(card.art, ICONS["sword"])
    img.blt(CARD_W // 2 - 8, ART_Y + 11, icons, u, 0, 16, 16, KEY, scale=2)  # Scaled about its centre: 32x32.
    # Type line, then the short rules lines.
    _ctext(img, TYPE_Y, clip(type_line(card).upper(), FACE_W, "s"), "ash", "s")
    y = RULES_Y
    for ln in face_rules(card)[:FACE_RULES]:
        _ctext(img, y, clip(ln, FACE_W), "rook" if ln.startswith(EQUIP) else "bone", "m")
        y += RULES_STEP
    # Skill icons (bottom left) and the tier gem (bottom right).
    for i, sk in enumerate(card.icons[:3]):
        img.rect(9 + i * 10, CARD_H - 13, 7, 7, C(SKILL_COL.get(sk, "ash")))
    img.rect(CARD_W - 16, CARD_H - 13, 7, 7, C(TIER_GEM.get(card.tier, "ash")))
    if card.name.endswith("+"):
        img.text(CARD_W - 32, CARD_H - 22, "+", C("spore"), FONT["l"])
    return img


def _ctext(img, y, s, col, font):
    img.text(CARD_W // 2 - text_w(s, font) // 2, y, s, C(col), FONT[font])


def draw_card(card: Card, cx, cy, scale=1.0, rot=0.0, cost: int | None = None, dim=False, glow: str | None = None):
    """A card centred at (cx, cy). `cost` overrides the printed cost (a cost changed by a modifier).

    Pixel text only reads at whole scales with no rotation, so resting cards use scale 1 and rot 0.
    """
    img = face(card)
    x, y = cx - CARD_W / 2, cy - CARD_H / 2
    if glow:
        pyxel.dither(0.6)
        pyxel.rect(
            cx - CARD_W * scale / 2 - 2, cy - CARD_H * scale / 2 - 2, CARD_W * scale + 4, CARD_H * scale + 4, C(glow)
        )
        pyxel.dither(1.0)
    if abs(rot) < 0.5 and abs(scale - 1) < 0.03:
        scale = 1
        pyxel.blt(round(x), round(y), img, 0, 0, CARD_W, CARD_H, KEY)
    else:
        pyxel.blt(x, y, img, 0, 0, CARD_W, CARD_H, KEY, rotate=rot, scale=scale)
    if dim:
        pyxel.dither(0.5)
        pyxel.rect(cx - CARD_W * scale / 2, cy - CARD_H * scale / 2, CARD_W * scale, CARD_H * scale, C("void"))
        pyxel.dither(1.0)
    if card.tier not in ("T",) or card.type == "spore":
        c = str(card.cost if cost is None else cost)
        ox, oy = cx - (CARD_W / 2 - 4) * scale, cy - (CARD_H / 2 - 4) * scale  # On the corner, as in StS.
        col = "energy" if cost is None or cost == card.cost else ("spore" if cost < card.cost else "blood")
        r = 13 * min(scale, 1.4)
        pyxel.circ(ox, oy, r + 2, C("void"))
        pyxel.circ(ox, oy, r, C(col))
        pyxel.text(ox - text_w(c, "l") // 2 + 1, oy - font_h("l") // 2, c, C("void"), FONT["l"])


def inspect_panel(card: Card, inst=None, x=None, y=None):
    """The large view of a card (GDD 4: tap and hold): the face at 2x (1x if the text needs the room), the full name,
    the text and keywords."""
    from ..ui.layout import INSPECT

    ix, iy, iw, ih = INSPECT
    if x is not None:
        ix, iy = x, y
    pyxel.dither(0.85)
    pyxel.rect(0, 0, pyxel.width, pyxel.height, C("void"))
    pyxel.dither(1.0)
    tw = iw - 32
    lh = line_h("m")
    body = wrap(card.text, tw, "m")
    keys = [ln for kw in keyword_help(card) for ln in wrap(kw, tw, "m")]
    scale = 2 if ih >= 16 + CARD_H * 2 + 16 + 2 * lh + lh * (len(body) + len(keys)) + 40 else 1
    h = min(ih, 16 + CARD_H * scale + 16 + 2 * lh + 8 + lh * len(body) + 10 + lh * len(keys) + 16)
    panel(ix, iy, iw, h, fill="ink", border="line")
    draw_card(card, ix + iw // 2, iy + 16 + CARD_H * scale // 2, scale=scale)
    ty = iy + 16 + CARD_H * scale + 16
    text(ix + 16, ty, card.name, "bone", "l", None)
    ty += lh
    text(ix + 16, ty, f"{TIER_NAMES.get(card.tier, card.tier)} {type_line(card)} | {card.set}", "ash", "m", None)
    if inst is not None and card.weapon and inst.durability is not None:
        t = f"Ammo {inst.durability}/{card.weapon.durability}"
        text(ix + iw - 16 - text_w(t, "m"), ty, t, "rook", "m", None)
    ty += lh + 8
    for ln in body:
        text(ix + 16, ty, ln, "bone", "m", None)
        ty += lh
    ty += 10
    for ln in keys:
        if ty > iy + h - lh:
            return
        text(ix + 16, ty, ln, "ash", "m", None)
        ty += lh


def mini_card(card: Card, x, y, w, h, selected=False, dim=False):
    """A card scaled into the rect (x, y, w, h)."""
    s = min(w / CARD_W, h / CARD_H)
    draw_card(card, x + w / 2, y + h / 2, scale=s, dim=dim, glow="crit" if selected else None)


def card_for(cid: str, plus: bool = False) -> Card:
    return CONTENT.card(cid, plus)
