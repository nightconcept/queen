"""Skill tests with the Hive Bag (GDD 9): skill + committed icons + a token >= difficulty."""

from ..content import CONTENT
from ..mech.registry import HOOKS
from .rng import choice, shuffle
from .run import RunState

SKILLS = ("willpower", "intellect", "combat", "agility")


def test_hand(run: RunState) -> list[int]:
    """The cards you may commit: `test_hand` cards of the deck, by uid. Weaknesses and traumas are left out."""
    rng = run.rng["bag"]
    pool = [c.uid for c in run.deck if c.card.tier not in ("W", "T") and c.uid != run.weapon and c.card.icons]
    shuffle(rng, pool)
    return pool[: CONTENT.rules.test_hand]


def icons_for(run: RunState, uid: int, skill: str) -> int:
    inst = run.find(uid)
    if inst is None:
        return 0
    return sum(1 for i in inst.card.icons if i in (skill, "wild"))


def bonus(run: RunState) -> int:
    ev = {"bonus": 0}
    for rid in run.relics:
        r = CONTENT.relics[rid]
        if "test_bonus" in r.hooks:
            HOOKS[r.hooks["test_bonus"]](run, None, r.params, ev)
    return ev["bonus"]


def base(run: RunState, skill: str, committed: list[int]) -> int:
    return run.skills[skill] + sum(icons_for(run, u, skill) for u in committed) + bonus(run)


def token_value(run: RunState, token: str) -> tuple[int | None, bool]:
    """(value, elder). None means an automatic failure."""
    t = CONTENT.bag.tokens[token]
    if t.get("auto_fail"):
        return None, False
    if t.get("elder"):
        return CONTENT.hunter.elder_sign.get("bonus", 2), True
    if t.get("symbol"):
        sym = CONTENT.scenario.symbols[token]
        if "if_enemies" in sym and run.loc().enemies:
            return sym.if_enemies, False
        return sym.value, False
    return t.value, False


def chance(run: RunState, skill: str, difficulty: int, committed: list[int]) -> float:
    """The chance to pass, from the bag as it is now."""
    total = base(run, skill, committed)
    wins = 0
    for token in run.bag:
        v, _ = token_value(run, token)
        if v is not None and total + v >= difficulty:
            wins += 1
    return wins / len(run.bag) if run.bag else 1.0


def resolve(run: RunState, skill: str, difficulty: int, committed: list[int]) -> dict:
    """Draw a token and decide. Committed cards are fatigued (they start the next battle discarded)."""
    token = choice(run.rng["bag"], run.bag)
    value, elder = token_value(run, token)
    total = base(run, skill, committed)
    success = value is not None and total + value >= difficulty
    run.fatigued.extend(u for u in committed if u not in run.fatigued)
    effects = []
    if elder:
        effects += [dict(e) for e in CONTENT.hunter.elder_sign.get("effects", ())]
    t = CONTENT.bag.tokens[token]
    if t.get("symbol") and not success:
        effects += [dict(e) for e in CONTENT.scenario.symbols[token].get("fail", ())]
    run.bump("tests")
    if success:
        run.bump("tests_passed")
    return {
        "token": token,
        "value": value,
        "base": total,
        "total": None if value is None else total + value,
        "difficulty": difficulty,
        "success": success,
        "effects": effects,
    }
