"""Hooks: statuses, relics, auras, equipment and the Hunter react to events (`hooks` in data). fn(ctx, owner, p, ev).

`owner` is the fighter that has the status (or the Hunter for relics, or the CardInst for auras and equipment).
`p` holds the hook's params; for a status, `p.n` is its stacks. `ev` is the event's dict, which a hook may change.
The events: battle_start, turn_start, turn_end, draw_count, fire_dice, hit_target, crit_hits, damage_per_hit,
damage_per_hit_taken, attack_mult, shield_gain, damage_taken, crit, after_fire, clue_gain, drawn, battle_end (battle);
mythos_entropy, test_bonus (exploration). A card's `<event>_in_hand` hook listens while it is in the hand.
"""

from ..content import Params
from .registry import hook

# --- Statuses


@hook("momentum")
def momentum(ctx, owner, p, ev):
    if ev["attacker"] is owner:
        ev["per_hit"] += p.n


@hook("marked")
def marked(ctx, owner, p, ev):
    if ev["target"] is owner:
        ev["per_hit"] += p.n


@hook("exposed")
def exposed(ctx, owner, p, ev):
    if ev["target"] is owner:
        ev["hit"] -= 1


@hook("exposed_mult")
def exposed_mult(ctx, owner, p, ev):
    if ev["target"] is owner:
        ev["mult"] *= 1.5


@hook("shaken_dice")
def shaken_dice(ctx, owner, p, ev):
    if ev["attacker"] is owner:
        ev["dice"] -= p.n


@hook("shaken")
def shaken(ctx, owner, p, ev):
    if ev["attacker"] is owner:
        ev["mult"] *= 0.75


@hook("brittle")
def brittle(ctx, owner, p, ev):
    if ev["who"] is owner:
        ev["n"] = int(ev["n"] * 0.75)


@hook("bleed")
def bleed(ctx, owner, p, ev):
    if ev["who"] is owner:
        ctx.lose_hp(owner, p.n)


@hook("ward")
def ward(ctx, owner, p, ev):
    if ev["target"] is owner and ev["amount"] > 0:
        absorbed = min(p.n, ev["amount"])
        ev["amount"] -= absorbed
        left = p.n - absorbed
        if left > 0:
            owner.statuses["WARD"] = left
        else:
            owner.statuses.pop("WARD", None)
        ctx.emit("ward", n=absorbed)


@hook("draw_minus_one")
def draw_minus_one(ctx, owner, p, ev):
    ev["n"] -= 1


# --- Cards in hand, auras, equipment, weapons


@hook("dice_minus_one")
def dice_minus_one(ctx, owner, p, ev):
    if ev["attacker"] is ctx.hero:
        ev["dice"] -= 1


@hook("block_clues")
def block_clues(ctx, owner, p, ev):
    ev["n"] = 0


@hook("overclock")
def overclock(ctx, owner, p, ev):
    ev["hits"] = max(ev["hits"], p.hits)


@hook("crit_chain")
def crit_chain(ctx, owner, p, ev):
    ctx.push([Params(op="draw", n=p.n)], owner, None)


@hook("autoloader")
def autoloader(ctx, owner, p, ev):
    """The first Fire each turn fires again, at the same target, for one use."""
    if ev["first"] and not ev["params"].get("repeat") and (owner.uses or 0) > 0:
        owner.uses -= 1
        ctx.emit("trigger", uid=owner.uid)
        ctx.push([Params(op="fire", dice=ev["params"].get("dice", 0), repeat=True)], owner, ev["target"])


@hook("exoskeleton")
def exoskeleton(ctx, owner, p, ev):
    """Health loss to the Hunter becomes 1. Lethal loss is prevented, and the exoskeleton is destroyed."""
    if ev["target"] is not ctx.hero or (owner.uses or 0) <= 0:
        return

    def limit(lost, hp):
        if lost <= 0:
            return lost
        if lost >= hp:
            owner.uses = 0
            ctx.emit("trigger", uid=owner.uid, destroyed=True)
            return 0
        if lost > 1:
            owner.uses -= 1
            ctx.emit("trigger", uid=owner.uid)
            return 1
        return lost

    ev["limits"].append(limit)


@hook("forced_equip")
def forced_equip(ctx, owner, p, ev):
    """A weakness weapon equips itself when drawn."""
    ctx.equip(owner)
    ctx.emit("forced", uid=owner.uid)


# --- The Hunter


@hook("kinetic_chain")
def kinetic_chain(ctx, owner, p, ev):
    """Rook: the first crit each turn gives 1 Focus."""
    if getattr(ctx, "chain_turn", -1) != ctx.turn:
        ctx.chain_turn = ctx.turn
        ctx.apply(ctx.hero, "FOCUS", 1)


# --- Relics


@hook("start_status")
def start_status(ctx, owner, p, ev):
    ctx.apply(ctx.hero, p.status, p.n)


@hook("enemies_status")
def enemies_status(ctx, owner, p, ev):
    for f in ctx.living():
        ctx.apply(f, p.status, p.n)


@hook("start_shields")
def start_shields(ctx, owner, p, ev):
    ctx.gain_shields(ctx.hero, p.n)


@hook("start_horror")
def start_horror(ctx, owner, p, ev):
    ctx.horror(p.n)


@hook("heal_after_win")
def heal_after_win(ctx, owner, p, ev):
    if ev["result"] == "won":
        ctx.hero.hp = min(ctx.hero.max_hp, ctx.hero.hp + p.n)


@hook("lantern")
def lantern(run, owner, p, ev):
    """Lantern's Beacon: once per agenda, a Mythos phase adds no entropy."""
    if run.beacon_used != run.agenda and ev["n"] > 0:
        run.beacon_used = run.agenda
        ev["n"] = 0
        ev["note"] = "Lantern's Beacon holds the dark back."


@hook("flat_bonus")
def flat_bonus(run, owner, p, ev):
    ev["bonus"] += p.bonus
