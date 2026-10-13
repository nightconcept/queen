"""Weapon specials (`weapon.special` in data/cards). Each is fn(ctx, roll, p) and may change `roll.damage`."""

from .registry import special


@special("double")
def double(ctx, roll, p):
    """Hits deal double damage (RTX Special 00)."""
    roll.damage *= 2


@special("flat_on_hit")
def flat_on_hit(ctx, roll, p):
    """If at least 1 hit, deal `flat` damage instead (December Remembrance, Gravitas Cannon)."""
    if roll.hits > 0:
        roll.damage = p.flat


@special("exact_six")
def exact_six(ctx, roll, p):
    """If exactly one die shows 6, deal `flat` damage instead (Forgetfulness)."""
    if roll.faces.count(6) == 1:
        roll.damage = max(roll.damage, p.flat)


@special("dreamscape")
def dreamscape(ctx, roll, p):
    """On hit, the Hunter's shields become 0 (Tormented Dreamscape)."""
    if roll.hits > 0 and ctx.hero.shields:
        ctx.hero.shields = 0
        ctx.emit("shield_break", who=0)
