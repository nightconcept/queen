"""The top bar on the map and in battle. It shows only what the screen below does not: the map shows health and
nerve (its agenda and act cards show entropy and clues); a battle shows entropy and clues (Rook's panel shows health
and nerve). XP and the round show on both. Nothing is drawn under the camera cutout but the bar's colour."""

import pyxel

from ..config import SAFE_TOP, W
from ..rules import explore
from ..ui.layout import TOP_BAR
from . import art
from .art import C, text


def top_bar(game, view=None):
    run = game.run
    if run is None:
        return
    h = TOP_BAR[3]
    pyxel.rect(0, 0, W, h, C("void"))
    pyxel.line(0, h - 1, W, h - 1, C("panel_hi"))
    y = SAFE_TOP + 4
    if view is None:
        _health(run, y)
    else:
        _clocks(run, view, y)
    art.right(W - 14, y, f"XP {run.xp}", "crit", "m")
    art.right(W - 14, y + 20, f"Round {run.round}", "ash", "s", None)


def _health(run, y):
    art.icon("heart", 14, y + 2)
    text(36, y, f"{run.hp}/{run.max_hp}", "blood", "m")
    art.bar(36, y + 24, 110, 8, run.hp, run.max_hp)
    art.icon("eye", 170, y + 2)
    text(192, y, "Nerve", "horror", "m")
    art.pips(192, y + 24, run.nerve, run.max_nerve, col="horror", size=8, gap=3)


def _clocks(run, view, y):
    ag = explore.current_agenda(run)
    art.icon("hourglass", 14, y + 2)
    if ag:
        e = run.entropy + view["entropy"]
        text(36, y, f"Entropy {e}/{ag.entropy}", "entropy", "m")
        art.bar(36, y + 24, 130, 8, e, ag.entropy, fill="entropy", back="panel")
    else:
        text(36, y, "SHE IS AWAKE", "entropy", "m")
    a = explore.current_act(run)
    clues = run.clues + view["clues"]
    art.icon("key", 196, y + 2)
    if a and a.clues:
        text(218, y, f"Clues {clues}/{a.clues}", "clue", "m")
        art.bar(218, y + 24, 110, 8, clues, a.clues, fill="clue", back="panel")
    else:
        text(218, y, f"Clues {clues}", "clue", "m")
