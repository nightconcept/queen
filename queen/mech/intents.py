"""Intent ops: what an enemy's move does (`intents.*.effects` in data/enemies.json). Each is fn(ctx, enemy, p)."""

from .registry import intent_op


@intent_op("attack")
def attack(ctx, foe, p):
    """params: damage, times."""
    for _ in range(p.get("times", 1)):
        if not ctx.hero.alive:
            return
        ctx.deal(ctx.hero, ctx.enemy_damage(foe, p.damage), foe, kind="enemy")


@intent_op("horror")
def horror(ctx, foe, p):
    ctx.horror(p.n)


@intent_op("shield")
def shield(ctx, foe, p):
    ctx.gain_shields(foe, p.n)


@intent_op("shield_all")
def shield_all(ctx, foe, p):
    for f in ctx.living():
        ctx.gain_shields(f, p.n)


@intent_op("apply")
def apply(ctx, foe, p):
    """A status on the Hunter (to: hero, the default) or on the enemy itself (to: self)."""
    ctx.apply(foe if p.get("to") == "self" else ctx.hero, p.status, p.n)


@intent_op("rally")
def rally(ctx, foe, p):
    """A status on every living enemy."""
    for f in ctx.living():
        ctx.apply(f, p.status, p.n)


@intent_op("add_cards")
def add_cards(ctx, foe, p):
    """Junk cards into the Hunter's discard pile, for this battle only."""
    for _ in range(p.n):
        ctx.discard.append(ctx.run.new_card(p.card, temp=True))
    ctx.emit("add_cards", card=p.card, n=p.n, who=foe.uid)


@intent_op("summon")
def summon(ctx, foe, p):
    new = ctx.add_foe(p.enemy)
    if new:
        ctx.roll_intent(new)
        ctx.emit("summon", who=new.uid, id=new.rec.id)


@intent_op("gestate")
def gestate(ctx, foe, p):
    """Brood counts down. At 0 the egg hatches into `into` (the behaviour's param) in its place."""
    foe.statuses["BROOD"] = foe.statuses.get("BROOD", 1) - 1
    ctx.emit("status", who=foe.uid, status="BROOD", n=-1)
    if foe.statuses["BROOD"] <= 0:
        slot = ctx.foes.index(foe)
        foe.flags["silent"] = True
        foe.hp = 0
        ctx.died(foe)
        new = ctx.add_foe(foe.rec.params.into, slot + 1)
        if new:
            ctx.roll_intent(new)
            ctx.emit("summon", who=new.uid, id=new.rec.id, hatched=foe.uid)


@intent_op("devour")
def devour(ctx, foe, p):
    """Kill an allied Drone and heal."""
    prey = next((f for f in ctx.living() if f is not foe and f.rec.id == "DRONE"), None)
    if prey:
        prey.flags["silent"] = True
        ctx.lose_hp(prey, prey.hp)
        ctx.heal(foe, p.heal)


@intent_op("awaken")
def awaken(ctx, foe, p):
    foe.flags["awakened"] = True
    ctx.gain_shields(foe, 10)
    ctx.emit("awaken", who=foe.uid)
