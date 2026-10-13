"""Draws the other screens: title, story, skill test, reward, rest, resolution, and the card list."""

import math

import pyxel

from ..config import SAFE_TOP, H, W
from ..content import CONTENT
from ..rules import skilltest
from ..scenes.deck import cell_rect
from ..scenes.reward import card_rects, relic_rects
from ..scenes.test import commit_rects
from ..ui import layout
from ..ui.layout import wrap
from . import art
from .art import C, center, text
from .cards import inspect_panel, mini_card

FRAME = {"story": "bone", "treachery": "horror", "enemy": "blood", "boon": "clue", "agenda": "entropy", "act": "clue",
         "mythos": "entropy"}  # fmt: skip


# --- Title


def title(scene, game, t):
    pyxel.cls(C("void"))
    art.background("hive", 0, 80, W, 448, 240, 0)
    art.dim(0, 80, W, 448, 0.35)
    for i in range(10):
        pyxel.dither(1 - i / 10)
        pyxel.rect(0, 80 + i * 6, W, 6, C("void"))
        pyxel.rect(0, 528 - i * 6, W, 6, C("void"))
    pyxel.dither(1.0)
    pyxel.rect(0, 528, W, H - 528, C("void"))
    bob = math.sin(t / 40) * 3
    art.big(W // 2, 120 + bob, "QUEEN", "entropy", scale=3)
    center(W // 2, 196, "A HIGHCARD TALE", "bone", "m")
    frame = art.frame_of("queen", "idle", t, 12)
    art.sprite("queen", frame, W // 2, 420, scale=2.0)
    art.sprite("rook", art.frame_of("rook", "idle", t, 10), 64, 500)
    log = game.campaign
    if log.get("runs"):
        center(W // 2, 452, f"Runs {log.get('runs', 0)}  |  Queen slain {log.get('queen_slain', 0)}", "ash", "m", None)
    art.menu(scene.menu)
    center(W // 2, H - 30, "CC0 art: OneBitPudding, ansimuz, Kenney", "line", "m", None)
    if scene.dossier:
        dossier(game)


def dossier(game):
    art.dim(0, 0, W, H, 0.8)
    art.panel(16, 100, 288, 480, fill="ink", border="rook")
    center(W // 2, 112, "HUNTER'S DOSSIER", "rook", "l")
    h = CONTENT.hunter
    text(30, 140, f"{h.name}, {h.title}", "bone", "l")
    y = 160
    for ln in wrap(h.blurb, 260, "m"):
        text(30, y, ln, "ash", "m", None)
        y += 14
    y += 8
    log = game.campaign
    if not log:
        text(36, y, "No runs yet. The Sovereign waits.", "ash", "m")
    for k, v in sorted(log.items()):
        if y > 540:
            break
        text(30, y, k.replace("_", " "), "bone", "m", None)
        art.right(290, y, str(v), "crit", "m", None)
        y += 14
    center(W // 2, 560, "Tap to close", "line", "m", None)


# --- Story


def story(scene, game, t):
    art.dim(0, 0, W, H, 0.9)
    col = FRAME.get(scene.frame, "bone")
    x, y, w = 12, SAFE_TOP + 40, W - 24
    top = y
    h = H - y - 200
    art.panel(x, y, w, h + 150, fill="ink", border=col)
    if scene.art:
        ax, ay = scene.art_xy
        pyxel.blt(x + 4, y + 4, art.BG.get(scene.art, art.BG["hive"]), ax, ay, w - 8, 140)
        for i in range(8):  # Fade the picture into the card.
            pyxel.dither(i / 8)
            pyxel.rect(x + 4, y + 4 + 140 - 8 + i, w - 8, 1, C("ink"))
        pyxel.dither(1.0)
        y += 146
    elif getattr(scene, "foes", None):
        n = len(scene.foes)
        for i, eid in enumerate(scene.foes):
            rec = CONTENT.enemies[eid]
            fx = x + w * (i + 1) / (n + 1)
            art.sprite(rec.art, art.frame_of(rec.art, "idle", t + i * 5, 9), fx, y + 110, scale=min(rec.scale, 1.5))
        y += 116
    kind = {"treachery": "TREACHERY", "enemy": "ENEMY", "boon": "BOON", "agenda": "AGENDA", "act": "ACT",
            "mythos": "MYTHOS PHASE"}.get(scene.frame, "")  # fmt: skip
    if kind:
        text(x + 10, y + 6, kind, col, "m", None)
        y += 16
    for ln in wrap(scene.title, w - 20, "l"):
        text(x + 10, y + 4, ln, "bone", "l")
        y += 15
    y += 6
    left = scene.chars
    for para in scene.text:
        shown = para[: max(0, left)]
        left -= len(para)
        for ln in wrap(shown, w - 20, "m"):
            text(x + 10, y, ln, "bone" if not para.startswith(("LANTERN", "ROOK")) else "clue", "m", None)
            y += 14
        y += 6
        if left <= 0:
            break
    if scene.typed:
        art.menu(scene.menu)
    elif (t // 20) % 2:
        center(W // 2, top + h + 120, "tap to skip", "line", "m", None)


# --- Skill test


SKILL_COL = {"willpower": "horror", "intellect": "clue", "combat": "blood", "agility": "spore"}


def test(scene, game, t):
    run = game.run
    art.dim(0, 0, W, H, 0.8)
    art.panel(12, 70, W - 24, H - 100, fill="ink", border=SKILL_COL.get(scene.skill, "bone"))
    center(W // 2, 84, scene.step.get("title", "Test").upper(), "bone", "l")
    sk = scene.skill
    base = skilltest.base(run, sk, scene.committed)
    center(W // 2, 112, f"{sk.capitalize()} {base}  vs  {scene.step['difficulty']}", SKILL_COL.get(sk, "bone"), "l")
    if scene.phase == "commit":
        pct = int(scene.chance(game) * 100)
        center(W // 2, 140, f"Chance to pass: {pct}%", "crit" if pct >= 60 else "bone", "m")
        center(W // 2, 300, "Commit cards for their icons.", "ash", "m", None)
        center(W // 2, 314, "They rest until the next battle.", "ash", "m", None)
        for i, (uid, r) in enumerate(zip(scene.hand, commit_rects(len(scene.hand)), strict=True)):
            inst = run.find(uid)
            useful = scene.useful(game, uid)
            sel = uid in scene.committed
            rx, ry, rw, rh = r
            mini_card(inst.card, rx, ry - (12 if sel else 0), rw, rh, selected=sel, dim=not useful)
            if i == scene.cursor:
                pyxel.rectb(rx - 2, ry - 2, rw + 4, rh + 4, C("white"))
        bag(run, t, 200)
        art.menu(scene.menu)
        return
    bag(run, t, 200, shake=scene.phase == "draw")
    if scene.phase == "draw":
        return
    r = scene.result
    tok_y = 300
    pyxel.circ(W // 2, tok_y, 26, C("void"))
    pyxel.circ(W // 2, tok_y, 24, C("bone" if r["value"] is not None else "blood"))
    center(W // 2, tok_y - 6, scene.token_text()[:9], "void", "m", None)
    if r["total"] is not None:
        center(W // 2, 360, f"{r['base']} {r['value']:+d} = {r['total']}  vs  {r['difficulty']}", "bone", "l")
    art.big(W // 2, 400, "PASS" if r["success"] else "FAIL", "spore" if r["success"] else "blood", scale=2)
    art.menu(scene.menu)


def bag(run, t, y, shake=False):
    dx = int(math.sin(t * 1.3) * 4) if shake else 0
    cx = W // 2 + dx
    pyxel.elli(cx - 34, y - 6, 68, 74, C("panel_hi"))
    pyxel.elli(cx - 30, y - 2, 60, 66, C("panel"))
    pyxel.tri(cx - 14, y - 4, cx + 14, y - 4, cx, y - 20, C("panel_hi"))
    center(cx, y + 18, "HIVE BAG", "ash", "m", None)
    center(cx, y + 32, f"{len(run.bag)} tokens", "line", "m", None)


# --- Reward


def reward(scene, game, t):
    pyxel.cls(C("void"))
    art.background("hive", 0, 0, W, 180, 240, 160)
    art.dim(0, 0, W, 180, 0.5)
    art.big(W // 2, 40, "SPOILS", "crit", scale=2)
    st = scene.step
    parts = []
    if st.get("clues"):
        parts.append(f"+{st['clues']} clue")
    if st.get("scrip"):
        parts.append(f"+{st['scrip']} scrip")
    if st.get("xp"):
        parts.append(f"+{st['xp']} XP")
    center(W // 2, 100, "   ".join(parts), "bone", "m")
    center(W // 2, 176, "Choose a card (hold to read)", "ash", "m", None)
    for cid, r in zip(st["cards"], card_rects(len(st["cards"])), strict=True):
        x, y, w, h = r
        sel = scene.card == cid
        mini_card(CONTENT.card(cid), x, y - (8 if sel else 0), w, h, selected=sel)
    if st["relics"]:
        center(W // 2, 360, "Choose a relic", "ash", "m", None)
        for rid, r in zip(st["relics"], relic_rects(len(st["relics"])), strict=True):
            rel = CONTENT.relics[rid]
            x, y, w, h = r
            art.panel(x, y, w, h, fill="ink", border="crit" if scene.relic == rid else "line")
            art.icon(rel.icon, x + 4, y + 4)
            name = wrap(rel.name, w - 26, "l")
            text(x + 22, y + 5, art.clip(name[0], w - 26, "l"), "crit", "l", None)
            for i, ln in enumerate(wrap(rel.text, w - 10, "m")[:5]):
                text(x + 5, y + 22 + i * 13, ln, "bone", "m", None)
    art.menu(scene.menu)
    if scene.inspect:
        inspect_panel(CONTENT.card(scene.inspect))


# --- Rest


def rest(scene, game, t):
    run = game.run
    pyxel.cls(C("void"))
    art.background("lab", 0, 40, W, 200, 0, 20)
    art.dim(0, 40, W, 200, 0.45)
    art.big(W // 2, 60, "REST", "clue", scale=2)
    art.dim(0, 110, W, 22, 0.85)
    center(W // 2, 114, f"Health {run.hp}/{run.max_hp}  Nerve {run.nerve}/{run.max_nerve}  XP {run.xp}", "bone", "m")
    if scene.rested:
        center(W // 2, 166, scene.flash, "spore", "m")
    center(W // 2, 230, "Spend XP (Highcard tier path)", "ash", "m", None)
    art.menu(scene.menu)
    if scene.rested and scene.flash and scene.t % 120 < 90:
        pass


# --- Resolution


def resolution(scene, game, t):
    s = scene.summary
    pyxel.cls(C("void"))
    col = {"good": "crit", "neutral": "bone", "bad": "blood"}[s["outcome"]]
    if s["outcome"] == "good":
        art.sprite("queen", art.frame_of("queen", "death", t, 8, loop=False), W // 2, 260, scale=2.0)
    else:
        art.sprite("queen", art.frame_of("queen", "idle", t, 12), W // 2, 260, scale=2.0)
    a = min(1.0, t / 60)
    pyxel.dither(a)
    art.big(W // 2, 300, s["name"].upper(), col)
    center(W // 2, 330, {"good": "RESOLUTION 1", "neutral": "RESOLUTION 2", "bad": "BAD END"}.get(s["outcome"], ""),
           "ash", "m", None)  # fmt: skip
    y = 352
    for ln in wrap(s["text"], W - 40, "m"):
        text(20, y, ln, "bone", "m")
        y += 13
    y += 10
    text(20, y, f"XP earned: {s['xp']}", "crit", "m")
    y += 16
    for k, v in s["log"].items():
        if k.startswith(("outcome_", "runs")) or y > H - 90:
            continue
        text(20, y, f"Log: {k.replace('_', ' ')} = {v}", "ash", "m", None)
        y += 14
    pyxel.dither(1.0)
    if t >= 60:
        art.menu(scene.menu)


# --- Card list


def deck(scene, game, t):
    art.dim(0, 0, W, H, 0.92)
    center(W // 2, SAFE_TOP + 20, scene.title, "bone", "l")
    center(W // 2, SAFE_TOP + 38, f"{len(scene.uids)} cards. Tap one to read it.", "ash", "m", None)
    pyxel.clip(0, 66, W, 560)
    for i, uid in enumerate(scene.uids):
        inst = scene.inst(game, uid)
        if inst is None:
            continue
        x, y, w, h = cell_rect(i, scene.scroll)
        if y > 640 or y + h < 60:
            continue
        mini_card(inst.card, x, y, w, h)
    pyxel.clip()
    art.menu(scene.menu)
    if scene.inspect is not None:
        inst = scene.inst(game, scene.inspect)
        if inst:
            inspect_panel(inst.card, inst)


__all__ = ["layout"]
