"""Enemy behaviours: generators that yield the id of the next intent (`behaviour` in data/enemies.json).

Each is fn(e, p): `e` is the Handle (battle.Handle: rng, hp_ratio, hero_shields, allies), `p` the enemy's params.
"""

from ..rules.rng import weighted as pick
from .registry import behaviour


@behaviour("cycle")
def cycle(e, p):
    """The intents in `order`, again and again."""
    while True:
        yield from p.order


@behaviour("weighted")
def weighted(e, p):
    """By `weights`, never the same one more than `max_repeat` times in a row."""
    last, run = None, 0
    while True:
        weights = dict(p.weights)
        if last is not None and run >= p.max_repeat and len(weights) > 1:
            weights.pop(last)
        nxt = pick(e.rng, weights)
        run = run + 1 if nxt == last else 1
        last = nxt
        yield nxt


@behaviour("hatch")
def hatch(e, p):
    while True:
        yield "GESTATE"


@behaviour("stalker")
def stalker(e, p):
    """Pounce when the Hunter's shields are under `threshold` (checked when it picks), else Lurk."""
    while True:
        yield "POUNCE" if e.hero_shields < p.threshold else "LURK"


@behaviour("queen")
def queen(e, p):
    """Dreaming until `phase2_at` of her health, then Awaken (a hidden intent), then the awakened cycle."""
    i = 0
    while not e.foe.flags.get("awakened"):
        if e.hp_ratio <= p.phase2_at:
            e.foe.flags["hide_intent"] = True
            yield "AWAKEN"
            break
        yield p.dreaming[i % len(p.dreaming)]
        i += 1
    i = 0
    while True:
        move = p.awakened[i % len(p.awakened)]
        i += 1
        if move == "DEVOUR" and not e.allies("DRONE"):
            move = p.awakened[i % len(p.awakened)]
            i += 1
        yield move
