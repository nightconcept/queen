"""The top bar on the map and in battle: health, nerve, the agenda's entropy clock, and the act's clues."""

import pyxel

from ..config import SAFE_TOP, W
from ..rules import explore
from . import art
from .art import C, text


def top_bar(game, view=None):
    run = game.run
    if run is None:
        return
    y = SAFE_TOP
    pyxel.rect(0, 0, W, y + 34, C("void"))
    pyxel.line(0, y + 34, W, y + 34, C("panel_hi"))
    hp, max_hp = (view["hero"]["hp"], view["hero"]["max_hp"]) if view else (run.hp, run.max_hp)
    nerve, max_nerve = (view["hero"]["nerve"], view["hero"]["max_nerve"]) if view else (run.nerve, run.max_nerve)
    art.icon("heart", 4, y + 2)
    text(22, y + 4, f"{hp}/{max_hp}", "blood", "m")
    art.icon("eye", 4, y + 18)
    art.pips(22, y + 22, nerve, max_nerve, col="horror", size=5, gap=2)
    ag = explore.current_agenda(run)
    battle_entropy = view["entropy"] if view else 0
    if ag:
        e = run.entropy + battle_entropy
        art.icon("hourglass", 120, y + 2)
        text(138, y + 4, f"{e}/{ag.entropy}", "entropy", "m")
        art.bar(120, y + 22, 64, 6, e, ag.entropy, fill="entropy", back="panel")
    else:
        text(120, y + 4, "AWAKE", "entropy", "m")
    a = explore.current_act(run)
    clues = run.clues + (view["clues"] if view else 0)
    art.icon("key", 200, y + 2)
    if a and a.clues:
        text(218, y + 4, f"{clues}/{a.clues}", "clue", "m")
        art.bar(200, y + 22, 52, 6, clues, a.clues, fill="clue", back="panel")
    else:
        text(218, y + 4, str(clues), "clue", "m")
    text(266, y + 4, f"XP {run.xp}", "crit", "m")
    text(266, y + 18, f"Round {run.round}", "ash", "m")
