"""Story ops: effects of story choices, encounter cards, locations, acts and agendas. Each is fn(run, p).

They change the RunState, or queue steps (rules/flow.py) for the screens to show. Add an op here and a row in
docs/repo/content.md.
"""

from ..content import CONTENT
from ..rules import flow
from ..rules.rng import choice
from .registry import story_op


def _here(run, p) -> str:
    """The location an op names: `location` (an id, "far", or missing for the current one)."""
    lid = p.get("location")
    if lid == "far":
        far = [k for k in run.locs if k != run.location and run.available(k) and run.loc(k).revealed]
        return choice(run.rng["map"], far) if far else run.location
    return lid or run.location


@story_op("story")
def story(run, p):
    flow.push(run, {"kind": "story", "id": p.id}, front=p.get("front", False))


@story_op("say")
def say(run, p):
    flow.say(run, p.text, p.get("title", ""))


@story_op("spawn")
def spawn(run, p):
    """Enemies at a location. At the Hunter's location they engage at once."""
    lid = _here(run, p)
    loc = run.loc(lid)
    loc.enemies.extend(p.enemies)
    if lid == run.location:
        loc.exhausted = False
        flow.push(run, {"kind": "engage", "location": lid})


@story_op("boss")
def boss(run, p):
    flow.push(run, {"kind": "battle", "enemies": list(p.enemies), "location": run.location, "boss": True})


@story_op("test")
def test(run, p):
    flow.push(
        run,
        {
            "kind": "test",
            "skill": p.skill,
            "difficulty": p.difficulty,
            "title": p.get("title", "Test"),
            "success": [dict(e) for e in p.get("success", ())],
            "fail": [dict(e) for e in p.get("fail", ())],
        },
    )


@story_op("horror")
def horror(run, p):
    run.nerve = max(0, run.nerve - p.n)
    run.bump("horror", p.n)


@story_op("damage")
def damage(run, p):
    run.hp = max(0, run.hp - p.n)


@story_op("heal")
def heal(run, p):
    run.hp = min(run.max_hp, run.hp + p.n)


@story_op("clue")
def clue(run, p):
    run.clues += p.n
    run.bump("clues", p.n)


@story_op("entropy")
def entropy(run, p):
    flow.add_entropy(run, p.n)


@story_op("xp")
def xp(run, p):
    run.xp += p.n


@story_op("scrip")
def scrip(run, p):
    run.scrip += p.n


@story_op("log")
def log(run, p):
    run.log[p.key] = p.get("value", 1)


@story_op("add_card")
def add_card(run, p):
    run.add_card(p.card, p.get("plus", False))


@story_op("relic")
def relic(run, p):
    if p.id not in run.relics:
        run.relics.append(p.id)


@story_op("unlock")
def unlock(run, p):
    if p.location not in run.unlocked:
        run.unlocked.append(p.location)


@story_op("bag_add")
def bag_add(run, p):
    run.bag.append(p.token)


@story_op("bag_remove")
def bag_remove(run, p):
    if p.token in run.bag:
        run.bag.remove(p.token)


@story_op("hive_buff")
def hive_buff(run, p):
    run.hive_hp += p.hp


@story_op("mythos_draws")
def mythos_draws(run, p):
    run.mythos_draws = p.n


@story_op("next_battle")
def next_battle(run, p):
    """Changes for the next battle only: spores, energy (first turn), shields."""
    for k in ("spores", "energy", "shields"):
        if k in p:
            run.next_battle[k] = run.next_battle.get(k, 0) + p[k]


@story_op("opening_draw")
def opening_draw(run, p):
    run.opening_draw += p.n


@story_op("awaken_queen")
def awaken_queen(run, p):
    run.queen_awake = True


@story_op("goto")
def goto(run, p):
    """Move without spending an action, and run the location's enter effects."""
    run.location = p.location
    loc = run.loc()
    loc.revealed = True
    flow.push_effects(run, CONTENT.scenario.locations[p.location].on_enter)


@story_op("resolve")
def resolve(run, p):
    flow.push(run, {"kind": "resolve", "id": p.id}, front=True)


@story_op("take_clue")
def take_clue(run, p):
    """Investigate's success: 1 clue from the location."""
    loc = run.loc()
    if loc.clues > 0:
        loc.clues -= 1
        run.clues += 1
        run.bump("clues")


@story_op("evade")
def evade(run, p):
    run.loc().exhausted = True


@story_op("fight")
def fight(run, p):
    from ..rules.explore import start_battle_step

    start_battle_step(run, run.location, front=True)
