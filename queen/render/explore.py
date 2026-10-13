"""Draws the map (GDD 14.4): the hive's locations joined by veins, Rook's token, the agenda and act, and actions."""

import math

import pyxel

from ..config import H, W
from ..content import CONTENT
from ..rules import explore
from ..ui import layout
from ..ui.layout import wrap
from . import art
from .art import C, center, text
from .hud import top_bar


def draw(scene, game, t):
    run = game.run
    pyxel.cls(C("void"))
    art.background("hive", 0, 46, W, 380, 240, 60)
    art.dim(0, 46, W, 380, 0.55)
    s = CONTENT.scenario
    moves = {a["to"] for a in explore.actions(run) if a["kind"] == "move"}
    # Veins between known locations.
    drawn = set()
    for lid, rec in s.locations.items():
        for other in rec.links:
            key = tuple(sorted((lid, other)))
            if key in drawn:
                continue
            drawn.add(key)
            if not (run.available(lid) and run.available(other)):
                continue
            a, b = rec.pos, s.locations[other].pos
            vein(a[0], a[1] + layout.MAP_Y, b[0], b[1] + layout.MAP_Y, t, run.location in key)
    for lid, rec in s.locations.items():
        node(run, lid, rec, t, lid in moves)
    # The panels under the map.
    agenda_card(run)
    act_card(run)
    pyxel.rect(0, layout.ACTION_Y, W, H - layout.ACTION_Y, C("ink"))
    pyxel.line(0, layout.ACTION_Y, W, layout.ACTION_Y, C("panel_hi"))
    here = s.locations[run.location]
    text(12, layout.ACTION_Y + 6, here.name, "bone", "l")
    text(12, layout.ACTION_Y + 20, "Actions", "ash", "m", None)
    art.pips(
        16 + art.text_w("Actions"),
        layout.ACTION_Y + 24,
        run.actions,
        CONTENT.rules.actions_per_round,
        col="rook",
        size=6,
    )
    if run.loc().clues:
        art.right(W - 12, layout.ACTION_Y + 8, f"{run.loc().clues} clue(s) here", "clue", "m", None)
    art.menu(scene.menu)
    top_bar(game)


def vein(x0, y0, x1, y1, t, lit):
    n = int(math.hypot(x1 - x0, y1 - y0) / 4)
    for i in range(n + 1):
        f = i / max(1, n)
        x = x0 + (x1 - x0) * f + math.sin(f * 9 + t / 30) * 2
        y = y0 + (y1 - y0) * f
        col = "entropy" if lit and (i + t // 6) % 6 == 0 else ("line" if lit else "panel_hi")
        pyxel.circ(x, y, 1, C(col))


def node(run, lid, rec, t, reachable):
    x, y, w, h = layout.node_rect(rec.pos)
    loc = run.loc(lid)
    if not run.available(lid):
        art.panel(x, y, w, h, fill="void", border="panel_hi")
        art.icon("lock", x + w // 2 - 8, y + 6)
        center(x + w // 2, y + 26, "???", "line", "m", None)
        return
    here = lid == run.location
    border = "rook" if here else ("crit" if reachable and (t // 20) % 2 == 0 else ("bone" if reachable else "line"))
    art.panel(x - 1, y - 1, w + 2, h + 2, fill="void", border=border)
    if loc.revealed:
        ax, ay = rec.art_xy
        bg = rec.art if rec.art in art.BG else "hive"
        pyxel.blt(x + 2, y + 2, art.BG[bg], ax, ay, w - 4, h - 4)
        node_name(x, y, w, h, rec.name, "bone", band=True)
        if loc.clues:
            for i in range(loc.clues):
                pyxel.circ(x + 6 + i * 6, y + 6, 2, C("clue"))
        if loc.enemies:
            art.icon("skull", x + w - 18, y + 2)
            if len(loc.enemies) > 1:
                text(x + w - 26, y + 3, str(len(loc.enemies)), "blood", "l")
        text(x + 6 + loc.clues * 6, y + 2, f"S{rec.shroud}", "ash", "m")  # Shroud, after the clue dots.
    else:
        pyxel.rect(x + 2, y + 2, w - 4, h - 4, C("panel"))
        art.icon("question", x + w // 2 - 8, y + 3)
        node_name(x, y, w, h, rec.name, "ash")
    if here:
        bob = int(math.sin(t / 12) * 2)
        pyxel.circ(x + w // 2, y - 6 + bob, 6, C("rook"))
        pyxel.circb(x + w // 2, y - 6 + bob, 6, C("void"))
        center(x + w // 2, y - 12 + bob, "R", "void", "l", None)


def node_name(x, y, w, h, name, col, band=False):
    """A location's name in one or two lines at the bottom of its node."""
    lines = wrap(name, w - 6, "m")[:2]
    top = y + h - 3 - 11 * len(lines)
    if band:
        pyxel.rect(x + 2, top - 1, w - 4, y + h - 1 - top, C("void"))
    for i, ln in enumerate(lines):
        center(x + w // 2, top + i * 11 - 1, ln, col, "m", None)


def agenda_card(run):
    x, y, w, h = layout.AGENDA_BOX
    ag = explore.current_agenda(run)
    art.panel(x, y, w, h, fill="ink", border="entropy")
    if not ag:
        center(x + w // 2, y + 30, "SHE IS AWAKE", "entropy", "m")
        return
    text(x + 6, y + 3, f"AGENDA {ag.id}", "entropy", "m", None)
    text(x + 6, y + 16, ag.name, "bone", "l", None)
    art.bar(x + 6, y + 32, w - 12, 8, run.entropy, ag.entropy, fill="entropy", back="panel")
    text(x + 6, y + 43, f"Entropy {run.entropy}/{ag.entropy}", "ash", "m", None)
    text(x + 6, y + 57, "Tap to read", "line", "m", None)


def act_card(run):
    x, y, w, h = layout.ACT_BOX
    a = explore.current_act(run)
    art.panel(x, y, w, h, fill="ink", border="clue")
    if not a:
        return
    text(x + 6, y + 3, f"ACT {a.id}", "clue", "m", None)
    text(x + 6, y + 16, a.name, "bone", "l", None)
    if a.clues:
        art.bar(x + 6, y + 32, w - 12, 8, run.clues, a.clues, fill="clue", back="panel")
        text(x + 6, y + 43, f"Clues {run.clues}/{a.clues}", "ash", "m", None)
    else:
        text(x + 6, y + 36, "Kill the Queen.", "blood", "m", None)
    text(x + 6, y + 57, "Tap to read", "line", "m", None)
