"""Short card lines for small card faces, made from the card's data (its ops and weapon), not hand-written.

A hand card is 104x216, too small for the full rules text. It shows these lines; the inspect view shows `text`.
"""

from ..content import CONTENT, Card
from .layout import CARD_W, text_w, wrap

FACE_W = CARD_W - 10  # The text width inside the frame.
FACE_RULES = 4  # Rules lines that fit under the art.

STATUS_SHORT = {"EXPOSED": "Expose", "SHAKEN": "Shake", "MOMENTUM": "Momentum", "FOCUS": "Focus", "MARKED": "Mark",
                "WARD": "Ward", "BLEED": "Bleed"}  # fmt: skip


EQUIP = "Eq: "  # A weapon's Equip op on a face (render/cards.py draws these lines in the weapon colour).


def short_lines(card: Card) -> list[str]:
    if card.weapon:  # The dice, the damage, the special, then the Equip ops. Ammo shows in the weapon box.
        w = card.weapon
        out = [f"+{w.dice}d hit{w.hit}+"]
        out.append(f"{w.damage}/hit" + (" crit" if w.crit else "") + (" x2" if w.special == "double" else ""))
        if w.special == "flat_on_hit":
            out.append(f"Hit: {w.params.flat}")
        elif w.special == "exact_six":
            out.append(f"One 6: {w.params.flat}")
        elif w.special == "dreamscape":
            out.append("Hit: -shield")
        return out + [EQUIP + ln for ln in op_lines(card)]
    out = op_lines(card)
    if card.type == "aura":
        out.append("Aura")
    if card.type == "equipment":
        out.append(f"{card.uses} uses")
    for k in ("exhaust", "retain", "ethereal"):
        if card.has(k):
            out.append(k.capitalize())
    if card.tier == "T":
        out = ["Trauma"] + out
    if any(e.get("zero_as") for e in card.effects):
        out.append("0 hits = 2")
    return out[:5]


def op_lines(card: Card) -> list[str]:
    """One short line per op in the card's `effects`."""
    out: list[str] = []
    for e in card.effects:
        rush = "Rush: " if e.get("if") is not None and e["if"].cond == "first_card" else ""
        if e.op == "fire":
            d = e.get("dice", 0)
            line = "FIRE" + (f" {d:+d}d" if d else "")
            if e.get("at") == "random":
                line = "RND " + line
            if out and out[-1] == line:
                out[-1] = line + " x2"
            elif out and out[-1] == line + " x2":
                out[-1] = line + " x3"
            else:
                out.append(line)
        elif e.op == "last_round":
            out.append("FIRE +2d/ammo")  # Wraps on the face: FIRE / +2d/ammo.
        elif e.op == "shield":
            out.append(f"Shield {e.n}")
        elif e.op == "draw":
            out.append(f"{rush}Draw {e.n}")
        elif e.op == "apply":
            out.append(f"{STATUS_SHORT.get(e.status, e.status.title())} {e.n}")
        elif e.op == "energy":
            out.append(f"+{e.n} energy")
        elif e.op == "lose_hp":
            out.append(f"Lose {e.n} HP")
        elif e.op == "repair":
            out.append(f"Reload {e.n}")
        elif e.op == "clue":
            out.append(f"Recon: +{e.n}" + ("" if rush else " clue"))
        elif e.op == "execute":
            out.append(f"Kill <{int(e.below * 100)}%")
    return out


TYPE_NAMES = {"action": "Action", "weapon": "Weapon", "equipment": "Gear", "aura": "Aura", "trauma": "Trauma",
              "spore": "Spore"}  # fmt: skip
TIER_NAMES = {"B": "Basic", "S": "Standard", "P": "Prototype", "X": "Prime", "W": "Weakness", "T": "Trauma"}


def type_line(card: Card) -> str:
    """The type, or a weapon's subtype (Revolver, AR...), short enough for a card face."""
    if card.subtype:
        return card.subtype
    return TYPE_NAMES.get(card.type, card.type)


def keyword_help(card: Card) -> list[str]:
    """One line for each keyword the card uses, for the inspect view."""
    out = []
    effects = {e.op for e in card.effects}
    statuses = {e.status for e in card.effects if e.op == "apply"}
    if "fire" in effects or "last_round" in effects:
        out.append("Fire: roll Combat + weapon dice. Each die at the weapon's target hits.")
    for s in statuses:
        st = CONTENT.statuses[s]
        out.append(f"{st.name}: {st.text.replace('{n}', 'N')}")
    if card.has("exhaust"):
        out.append("Exhaust: removed for the rest of the battle.")
    if card.has("retain"):
        out.append("Retain: stays in your hand at the end of the turn.")
    if card.has("ethereal"):
        out.append("Ethereal: exhausts if still in hand at the end of the turn.")
    if any(e.get("if") is not None and e["if"].cond == "first_card" for e in card.effects):
        out.append("Rush / Recon: only if it is the first card you play this turn.")
    if card.weapon:
        out.append("Ammo: each Fire uses 1. At 0 the weapon is spent until the next battle.")
        if card.effects:
            out.append("Eq (Equip): happens once, when you equip it.")
    return out


def fits(lines: list[str], font: str, width: int = FACE_W) -> bool:
    return all(text_w(ln, font) <= width for ln in lines)


def face_name(card: Card) -> tuple[str, list[str]]:
    """The font and lines for the name on a card face: up to two bold lines, or else two regular ones. `face` is a
    shorter name for cards whose name does not fit (an upgrade's + shows in the corner instead)."""
    name = card.face or card.name.removesuffix("+")
    for font in ("l", "m"):
        lines = wrap(name, FACE_W, font)
        if fits(name.split(), font) and len(lines) <= 2:
            return font, lines
    return "m", wrap(name, FACE_W, "m")[:2]


def face_rules(card: Card) -> list[str]:
    """The short lines wrapped to the face width: a long line breaks between words."""
    out = []
    for ln in short_lines(card):
        out += wrap(ln, FACE_W, "m") if text_w(ln, "m") > FACE_W else [ln]
    return out
