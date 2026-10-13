"""Exploration (GDD 8): actions, the Mythos phase, act and agenda flips, engagement, and resolutions.

The scene asks `actions(run)` what the Hunter may do and calls `act(run, action)`. It then calls `advance(run)`,
which runs the automatic steps and returns the next interactive step (or None), and `complete(run, step, result)`
when that step's screen is done.
"""

from collections import deque

from ..content import CONTENT, Params
from ..mech.registry import CONDITIONS, HOOKS, STORY
from . import flow, rewards
from .battle import Battle
from .run import RunState

# --- What the Hunter can do


def actions(run: RunState) -> list[dict]:
    if run.outcome or run.steps:
        return []
    s = CONTENT.scenario
    rec = s.locations[run.location]
    loc = run.loc()
    out = []
    for lid in rec.links:
        if run.available(lid):
            out.append({"kind": "move", "to": lid, "label": f"Move to {s.locations[lid].name}"})
    if loc.clues > 0:
        out.append({"kind": "investigate", "label": f"Investigate (shroud {rec.shroud})"})
    for a in rec.actions:
        if a.get("rest"):
            if loc.rested != run.agenda:
                out.append({"kind": "rest", "label": "Rest"})
        elif a.id not in loc.done:
            out.append({"kind": "location", "id": a.id, "label": a.label})
    act = current_act(run)
    if act is not None and act.clues is not None and run.clues >= act.clues:
        out.append({"kind": "advance", "label": f"Advance: {act.name}", "free": True})
    return out


def current_act(run: RunState) -> Params | None:
    acts = CONTENT.scenario.acts
    return acts[run.act] if run.act < len(acts) else None


def current_agenda(run: RunState) -> Params | None:
    agendas = CONTENT.scenario.agendas
    return agendas[run.agenda] if run.agenda < len(agendas) else None


def spend_action(run: RunState):
    run.actions -= 1
    if run.actions <= 0:
        flow.push(run, {"kind": "mythos"})


def act(run: RunState, action: dict):
    """Do one exploration action. Most cost 1 action; Advance is free."""
    s = CONTENT.scenario
    kind = action["kind"]
    run.bump("actions")
    if kind == "move":
        run.location = action["to"]
        loc = run.loc()
        rec = s.locations[run.location]
        first = not loc.revealed
        loc.revealed = True
        if first:
            flow.push_effects(run, rec.on_reveal)
        flow.push_effects(run, rec.on_enter)
        if loc.enemies and not loc.exhausted:
            flow.push(run, {"kind": "engage", "location": run.location})
        spend_action(run)
    elif kind == "investigate":
        rec = s.locations[run.location]
        flow.push(
            run,
            {
                "kind": "test",
                "skill": "intellect",
                "difficulty": rec.shroud,
                "title": "Investigate",
                "success": [{"op": "take_clue"}],
                "fail": [],
            },
        )
        spend_action(run)
    elif kind == "location":
        rec = s.locations[run.location]
        a = next(x for x in rec.actions if x.get("id") == action["id"])
        if a.get("once"):
            run.loc().done.append(a.id)
        if a.get("test"):
            t = a.test
            flow.push(
                run,
                {
                    "kind": "test",
                    "skill": t.skill,
                    "difficulty": t.difficulty,
                    "title": t.get("title", a.label),
                    "success": [dict(e) for e in a.get("success", ())],
                    "fail": [dict(e) for e in a.get("fail", ())],
                },
            )
        if a.get("story"):
            flow.push(run, {"kind": "story", "id": a.story})
        flow.push_effects(run, a.get("effects", ()))
        spend_action(run)
    elif kind == "rest":
        run.loc().rested = run.agenda
        flow.push(run, {"kind": "rest"})
        spend_action(run)
    elif kind == "advance":
        advance_act(run)


def advance_act(run: RunState):
    a = current_act(run)
    if a is None or a.clues is None or run.clues < a.clues:
        return
    run.clues -= a.clues
    run.act += 1
    flow.push(run, {"kind": "say", "title": f"Act {a.id}b: {a.name}", "text": [a.back], "frame": "act"})
    flow.push_effects(run, a.effects)
    nxt = current_act(run)
    if nxt:
        flow.push(run, {"kind": "say", "title": f"Act {nxt.id}a: {nxt.name}", "text": [nxt.front], "frame": "act"})


# --- Automatic steps


def advance(run: RunState) -> dict | None:
    """Run automatic steps until an interactive one is first in the queue, and return it. None when idle."""
    steps = run.steps
    while True:
        if not run.outcome and (run.hp <= 0 or run.nerve <= 0):
            if not (steps and steps[0]["kind"] == "resolve"):
                steps.insert(0, {"kind": "resolve", "id": "DEFEAT"})
        if not steps:
            return None
        step = steps[0]
        kind = step["kind"]
        if kind == "effects":
            steps.pop(0)
            run_effects(run, step["effects"])
        elif kind == "mythos":
            steps.pop(0)
            mythos(run)
        elif kind == "agenda":
            steps.pop(0)
            check_agenda(run)
        elif kind == "engage":
            loc = run.loc(step["location"])
            if step["location"] != run.location or not loc.enemies or loc.exhausted:
                steps.pop(0)
                continue
            return step
        elif kind == "story" and not story_choices(run, step):
            steps.pop(0)
        else:
            return step


def run_effects(run: RunState, effects):
    """Run story ops now. Steps they queue go to the front, in order, ahead of what was already queued."""
    before = list(run.steps)
    run.steps.clear()
    for e in effects:
        p = e if isinstance(e, Params) else Params(e)
        if p.get("if") is not None and not CONDITIONS[p["if"].cond](run, p["if"]):
            continue
        STORY[p.op](run, p)
    run.steps.extend(before)


def check_agenda(run: RunState):
    ag = current_agenda(run)
    if ag is None or run.entropy < ag.entropy:
        return
    run.entropy = 0
    run.agenda += 1
    queued = [{"kind": "say", "title": f"Agenda {ag.id}b: {ag.name}", "text": [ag.back], "frame": "agenda"}]
    queued.append({"kind": "effects", "effects": [dict(e) for e in ag.effects]})
    nxt = current_agenda(run)
    if nxt:
        queued.append({"kind": "say", "title": f"Agenda {nxt.id}a: {nxt.name}", "text": [nxt.front], "frame": "agenda"})
    run.steps[0:0] = queued


def mythos(run: RunState):
    """GDD 8.5: entropy, encounter cards, hunters move, enemies ready, a new round."""
    ev = {"n": 1}
    for rid in run.relics:
        r = CONTENT.relics[rid]
        if "mythos_entropy" in r.hooks:
            HOOKS[r.hooks["mythos_entropy"]](run, None, r.params, ev)
    queued: list[dict] = [{"kind": "say", "title": "Mythos", "text": mythos_text(run, ev), "frame": "mythos"}]
    if ev["n"] > 0 and current_agenda(run):
        run.entropy += ev["n"]
        run.total_entropy += ev["n"]
        queued.append({"kind": "agenda"})
    for _ in range(run.mythos_draws):
        if not run.encounter:
            run.encounter, run.encounter_discard = run.encounter_discard, []
            from .rng import shuffle

            shuffle(run.rng["encounter"], run.encounter)
            if current_agenda(run):
                run.entropy += 1
                run.total_entropy += 1
                queued.append({"kind": "agenda"})
        if run.encounter:
            sid = run.encounter.pop()
            run.encounter_discard.append(sid)
            queued.append({"kind": "story", "id": sid})
    move_hunters(run)
    for loc in run.locs.values():
        loc.exhausted = False
    queued.append({"kind": "engage", "location": run.location})
    run.actions = CONTENT.rules.actions_per_round
    run.round += 1
    run.steps[0:0] = queued


def mythos_text(run: RunState, ev: dict) -> list[str]:
    lines = []
    if ev.get("note"):
        lines.append(ev["note"])
    elif ev["n"]:
        lines.append(f"The hive stirs. +{ev['n']} entropy.")
    if run.log.get("lantern_garbled"):
        lines.append("LANTERN: R--k... d-n't... she's lis--ning...")
    return lines or ["The hive stirs."]


def path_step(run: RunState, start: str, goal: str) -> str | None:
    """The next location on a shortest path from start to goal, over available locations."""
    locs = CONTENT.scenario.locations
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nxt in locs[cur].links:
            if nxt not in prev and run.available(nxt):
                prev[nxt] = cur
                q.append(nxt)
    if goal not in prev or goal == start:
        return None
    node = goal
    while prev[node] != start:
        node = prev[node]
    return node


def move_hunters(run: RunState):
    moves = []
    for lid, loc in run.locs.items():
        if lid == run.location:
            continue
        hunters = [e for e in loc.enemies if CONTENT.enemies[e].hunter]
        if hunters:
            nxt = path_step(run, lid, run.location)
            if nxt:
                moves.append((lid, nxt, hunters))
    for src, dst, hunters in moves:
        for e in hunters:
            run.loc(src).enemies.remove(e)
            run.loc(dst).enemies.append(e)


# --- Interactive steps


def story_choices(run: RunState, step: dict) -> list[dict]:
    """The choices a story-like step shows: {label, test?, enabled}."""
    kind = step["kind"]
    if kind == "story":
        rec = CONTENT.scenario.stories[step["id"]]
        out = []
        for i, c in enumerate(rec.choices):
            if c.get("if") is not None and not CONDITIONS[c["if"].cond](run, c["if"]):
                continue
            out.append({"index": i, "label": c.label, "test": dict(c.test) if c.get("test") else None})
        return out
    if kind == "engage":
        foes = run.loc(step["location"]).enemies
        evade = max(CONTENT.enemies[e].evade for e in foes)
        out = [{"index": 0, "label": "Fight", "test": None}]
        if not any(CONTENT.enemies[e].boss for e in foes):
            out.append({"index": 1, "label": "Evade", "test": {"skill": "agility", "difficulty": evade}})
        return out
    return [{"index": 0, "label": "Continue", "test": None}]


def choose(run: RunState, step: dict, index: int):
    """Take a story-like step's choice (by its `index`)."""
    run.steps.remove(step)
    kind = step["kind"]
    if kind == "story":
        c = CONTENT.scenario.stories[step["id"]].choices[index]
        if c.get("test"):
            t = c.test
            flow.push(
                run,
                {
                    "kind": "test",
                    "skill": t.skill,
                    "difficulty": t.difficulty,
                    "title": CONTENT.scenario.stories[step["id"]].title,
                    "success": [dict(e) for e in c.get("success", ())],
                    "fail": [dict(e) for e in c.get("fail", ())],
                },
                front=True,
            )
        else:
            flow.push_effects(run, c.get("effects", ()), front=True)
    elif kind == "engage":
        lid = step["location"]
        if index == 0:
            start_battle_step(run, lid, front=True)
        else:
            evade = max(CONTENT.enemies[e].evade for e in run.loc(lid).enemies)
            flow.push(
                run,
                {
                    "kind": "test",
                    "skill": "agility",
                    "difficulty": evade,
                    "title": "Evade",
                    "success": [{"op": "evade"}],
                    "fail": [{"op": "fight"}],
                },
                front=True,
            )


def start_battle_step(run: RunState, lid: str, front: bool = False):
    enemies = list(run.loc(lid).enemies)
    boss = any(CONTENT.enemies[e].boss for e in enemies)
    flow.push(run, {"kind": "battle", "enemies": enemies, "location": lid, "boss": boss}, front=front)


def test_done(run: RunState, step: dict, result: dict):
    run.steps.remove(step)
    effects = list(result["effects"]) + list(step["success"] if result["success"] else step["fail"])
    flow.push_effects(run, effects, front=True)


def battle_done(run: RunState, step: dict, battle: Battle):
    run.steps.remove(step)
    battle.finish()
    if battle.entropy:
        flow.push(run, {"kind": "agenda"}, front=True)  # finish() added the battle's entropy to the agenda.
    if battle.over == "lost":
        resolution = "R3" if step.get("boss") and run.queen_awake else "DEFEAT"
        flow.push(run, {"kind": "resolve", "id": resolution}, front=True)
        return
    run.loc(step["location"]).enemies = []
    if step.get("boss"):
        flow.push(run, {"kind": "resolve", "id": "R2" if run.queen_awake else "R1"}, front=True)
        return
    elite = any(CONTENT.enemies[e].elite for e in step["enemies"])
    reward = rewards.battle_reward(run, elite)
    reward["clues"] = battle.clues
    flow.push(run, reward, front=True)


def reward_done(run: RunState, step: dict, card: str | None, relic: str | None):
    run.steps.remove(step)
    if card:
        run.add_card(card)
    if relic and relic not in run.relics:
        run.relics.append(relic)
    run.scrip += step.get("scrip", 0)
    run.xp += step.get("xp", 0)


def rest(run: RunState, choice: str):
    """A rest's free part: heal or recover nerve (GDD 8.2)."""
    rules = CONTENT.rules
    if choice == "heal":
        run.hp = min(run.max_hp, run.hp + int(run.max_hp * rules.rest_heal))
    elif choice == "nerve":
        run.nerve = min(run.max_nerve, run.nerve + rules.rest_nerve)


def step_done(run: RunState, step: dict):
    """Close a step that needs no result (say, rest)."""
    if step in run.steps:
        run.steps.remove(step)


def resolve(run: RunState, step: dict) -> dict:
    """End the run. Returns the resolution record with the XP earned, and the campaign log entries to keep."""
    rid = step["id"]
    res = CONTENT.scenario.resolutions[rid]
    run.outcome = rid
    run.steps.clear()
    xp = res.xp + run.vp
    run.xp += xp
    for k, v in res.get("log", {}).items():
        run.log[k] = v
    log = {**run.log, "next_entropy": res.next_entropy}
    for kind, n in res.get("trauma", {}).items():
        key = f"trauma_{kind}"
        log[key] = log.get(key, 0) + n
    log["runs"] = log.get("runs", 0) + 1
    log[f"outcome_{res.outcome}"] = log.get(f"outcome_{res.outcome}", 0) + 1
    return {"id": rid, "name": res.name, "outcome": res.outcome, "text": res.text, "xp": xp, "log": log}


def start(run: RunState):
    """The scenario's opening: the intro, then the first act and agenda."""
    s = CONTENT.scenario
    flow.push(run, {"kind": "say", "title": s.name, "text": list(s.intro), "frame": "story"})
    a, g = current_act(run), current_agenda(run)
    flow.push(run, {"kind": "say", "title": f"Agenda {g.id}a: {g.name}", "text": [g.front], "frame": "agenda"})
    flow.push(run, {"kind": "say", "title": f"Act {a.id}a: {a.name}", "text": [a.front], "frame": "act"})
