"""`just dev` pairs (GDD 17): start in a state. Keys:

scene=title|map|battle      where to start (default map)
enemies=DRONE,SPITTER      the battle's enemies (scene=battle)
location=ECHO_ARCHIVE      move the Hunter there (scene=map)
clues=N  xp=N  entropy=N   set the run's numbers
act=N  agenda=N            start at that act or agenda (0-based)
cards=FIRE,DOUBLE_TAP      add cards to the deck
"""

from ..content import CONTENT


def start_dev(game, pairs: dict[str, str]):
    scene = pairs.get("scene", "map")
    if scene == "title":
        return
    from ..rules.run import new_run

    run = game.run = new_run(game.seed, log=game.campaign)
    for key in ("clues", "xp"):
        if key in pairs:
            setattr(run, key, int(pairs[key]))
    if "entropy" in pairs:
        run.entropy = int(pairs["entropy"])
    if "act" in pairs:
        run.act = int(pairs["act"])
        for a in CONTENT.scenario.acts[: run.act]:
            for e in a.effects:
                if e.op == "unlock":
                    run.unlocked.append(e.location)
    if "agenda" in pairs:
        run.agenda = int(pairs["agenda"])
    for cid in filter(None, pairs.get("cards", "").replace("+", ",").split(",")):
        run.add_card(cid)
    if "location" in pairs:
        run.location = pairs["location"]
        run.loc().revealed = True
    game.enter_run()
    if scene == "battle":
        enemies = pairs.get("enemies", "DRONE,SPITTER").replace("+", ",").split(",")
        boss = any(CONTENT.enemies[e].boss for e in enemies)
        run.loc().enemies = list(enemies)
        run.steps.insert(0, {"kind": "battle", "enemies": enemies, "location": run.location, "boss": boss})
