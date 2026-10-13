"""Battle ops: the effects of cards (`effects` in data/cards). Each is fn(ctx, src, target, p).

`ctx` is the Battle, `src` the card being played (a CardInst), `target` the chosen enemy or None, `p` the op's
params. Add an op here and a row in docs/repo/content.md.
"""

from .registry import op


def _targets(ctx, target, to: str):
    if to == "self":
        return [ctx.hero]
    if to == "all_enemies":
        return ctx.living()
    return [target] if target is not None else []


@op("fire")
def fire(ctx, src, target, p):
    """Fire with the equipped weapon. params: dice (bonus), zero_as (hits when 0), at ("random")."""
    if p.get("at") == "random":
        target = None
    ctx.fire(target, p)


@op("last_round")
def last_round(ctx, src, target, p):
    """Fire with 2 extra dice per point of durability, then the weapon breaks."""
    dur = ctx.weapon.durability if ctx.weapon else 0
    ctx.fire(target, p.over({"extra": 2 * (dur or 0)}))
    if ctx.weapon:
        ctx.weapon.durability = 1
        ctx.spend_durability()


@op("execute")
def execute(ctx, src, target, p):
    """If the target has `below` of its health or less, it dies."""
    if target is not None and target.alive and target.hp <= target.max_hp * p.below:
        ctx.emit("execute", who=target.uid)
        ctx.lose_hp(target, target.hp)


@op("shield")
def shield(ctx, src, target, p):
    ctx.gain_shields(ctx.hero, p.n)


@op("draw")
def draw(ctx, src, target, p):
    ctx.draw_cards(p.n)


@op("apply")
def apply(ctx, src, target, p):
    """params: status, n, to (target, self, all_enemies)."""
    for f in _targets(ctx, target, p.get("to", "target")):
        ctx.apply(f, p.status, p.n)


@op("energy")
def energy(ctx, src, target, p):
    ctx.energy += p.n
    ctx.emit("energy", n=p.n)


@op("lose_hp")
def lose_hp(ctx, src, target, p):
    ctx.lose_hp(ctx.hero, p.n)


@op("repair")
def repair(ctx, src, target, p):
    ctx.repair(p.n)


@op("clue")
def clue(ctx, src, target, p):
    ctx.gain_clues(p.n)
