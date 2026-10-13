"""Plain lines for what an enemy's move does, made from its intent ops (data/enemies.json). No pyxel.

The battle shows them when the player taps an intent or an enemy (GDD 14.3).
"""

from ..content import CONTENT, Intent

KIND_NAMES = {"attack": "Attack", "horror": "Horror", "defend": "Defend", "buff": "Buff", "debuff": "Debuff",
              "summon": "Summon", "hatch": "Hatch", "unknown": "Unknown"}  # fmt: skip


def effect_lines(intent: Intent, damage: int | None = None) -> list[str]:
    """One line per op. `damage` is the attack after statuses (the intent view), if known."""
    out = []
    for e in intent.effects:
        if e.op == "attack":
            n = e.damage if damage is None else damage
            times = e.get("times", 1)
            out.append(f"Deals {n} damage" + (f" {times} times." if times > 1 else "."))
        elif e.op == "horror":
            out.append(f"You lose {e.n} nerve.")
        elif e.op == "shield":
            out.append(f"Gains {e.n} shield.")
        elif e.op == "shield_all":
            out.append(f"Every enemy gains {e.n} shield.")
        elif e.op == "apply":
            st = CONTENT.statuses[e.status]
            who = "Gains" if e.get("to") == "self" else "Gives you"
            out.append(f"{who} {st.name} {e.n}.")
        elif e.op == "rally":
            out.append(f"Every enemy gains {CONTENT.statuses[e.status].name} {e.n}.")
        elif e.op == "add_cards":
            out.append(f"Adds {e.n} {CONTENT.cards[e.card].name} to your discard pile.")
        elif e.op == "summon":
            out.append(f"Calls a {CONTENT.enemies[e.enemy].name}.")
        elif e.op == "gestate":
            out.append("The egg grows. At Brood 0 it hatches.")
        elif e.op == "devour":
            out.append(f"Eats an allied Drone and heals {e.heal}.")
        elif e.op == "awaken":
            out.append("Awakens and gains 10 shield.")
        else:
            out.append(e.op.replace("_", " ").capitalize() + ".")
    return out


def intent_lines(intent_id: str, intent: Intent, view: dict | None) -> tuple[str, list[str]]:
    """The heading and the lines for the move an enemy shows now. A hidden intent tells nothing."""
    if view and view.get("kind") == "unknown":
        return "Unknown", ["Its next move is hidden."]
    title = f"{KIND_NAMES.get(intent.kind, intent.kind.title())}: {intent_id.replace('_', ' ').title()}"
    return title, effect_lines(intent, view.get("damage") if view else None)


def status_line(sid: str, n: int) -> str:
    st = CONTENT.statuses[sid]
    return f"{st.name} {n}: {st.text.replace('{n}', str(n))}"
