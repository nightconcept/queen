"""Battle rewards (GDD 10.8, 13.1) and XP spending at rests (GDD 13.2)."""

from ..content import CONTENT
from .rng import shuffle, weighted
from .run import RunState


def reward_pool(run: RunState) -> list[str]:
    el = CONTENT.hunter.element
    return [cid for cid, c in CONTENT.cards.items() if c.pool and c.element in (el, None)]


def card_choices(run: RunState, n: int | None = None) -> list[str]:
    """`n` different cards by tier weight. A pick with no Prime raises the Prime weight (the pity counter)."""
    rng = run.rng["rewards"]
    rules = CONTENT.rules
    n = n or rules.reward_choices
    pool = reward_pool(run)
    by_tier: dict[str, list[str]] = {}
    for cid in pool:
        by_tier.setdefault(CONTENT.cards[cid].tier, []).append(cid)
    weights = dict(rules.tier_weights)
    weights["X"] = weights.get("X", 0) + run.prime_pity
    out: list[str] = []
    for _ in range(n * 4):
        if len(out) >= n:
            break
        tier = weighted(rng, {t: w for t, w in weights.items() if by_tier.get(t)})
        options = [c for c in by_tier[tier] if c not in out]
        if options:
            out.append(options[rng.randint(0, len(options) - 1)])
    if any(CONTENT.cards[c].tier == "X" for c in out):
        run.prime_pity = 0
    else:
        run.prime_pity += rules.prime_pity
    return out


def relic_choices(run: RunState, pool: str = "elite", n: int = 2) -> list[str]:
    options = [rid for rid, r in CONTENT.relics.items() if r.pool == pool and rid not in run.relics]
    shuffle(run.rng["rewards"], options)
    return options[:n]


def battle_reward(run: RunState, elite: bool) -> dict:
    lo, hi = CONTENT.rules.scrip["elite" if elite else "normal"]
    return {
        "kind": "reward",
        "cards": card_choices(run),
        "relics": relic_choices(run) if elite else [],
        "scrip": run.rng["rewards"].randint(lo, hi),
        "xp": 1 if elite else 0,
    }


# --- XP at rests


def upgrades(run: RunState) -> list[dict]:
    """Every way to spend XP now: {kind, uid, cost, label}."""
    costs = CONTENT.rules.xp_costs
    out = []
    for inst in run.deck:
        card = CONTENT.cards[inst.id]
        if card.tier in ("W", "T"):
            continue
        if not inst.plus and card.plus:
            out.append({"kind": "plus", "uid": inst.uid, "cost": costs.plus, "label": f"Upgrade {card.name}"})
        if inst.plus and card.upgrades_to:
            nxt = CONTENT.cards[card.upgrades_to]
            cost = costs.prime if nxt.tier == "X" else costs.tier_up
            out.append({"kind": "tier", "uid": inst.uid, "cost": cost, "label": f"{card.name}+ to {nxt.name}"})
    for inst in run.deck:
        card = CONTENT.cards[inst.id]
        if card.tier not in ("W",) and inst.uid != run.weapon:
            out.append({"kind": "remove", "uid": inst.uid, "cost": costs.remove, "label": f"Remove {card.name}"})
    return out


def spend(run: RunState, option: dict) -> bool:
    if option["cost"] > run.xp:
        return False
    inst = run.find(option["uid"])
    if inst is None:
        return False
    kind = option["kind"]
    if kind == "plus":
        inst.plus = True
    elif kind == "tier":
        nxt = CONTENT.cards[CONTENT.cards[inst.id].upgrades_to]
        inst.id, inst.plus = nxt.id, False
        if nxt.weapon:
            inst.durability = nxt.weapon.durability
    elif kind == "remove":
        run.remove(inst.uid)
    run.xp -= option["cost"]
    run.bump("upgrades")
    return True
