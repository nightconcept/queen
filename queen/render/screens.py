"""Draws the other screens: title, story, skill test, reward, rest, resolution, and the card list."""

import math

import pyxel

from ..config import SAFE_BOTTOM, SAFE_TOP, H, W
from ..content import CONTENT
from ..rules import skilltest
from ..scenes.deck import GRID_Y, VIEW_BOTTOM, cell_rect
from ..scenes.rest import LIST_Y
from ..scenes.reward import CARD_Y, RELIC_Y, card_rects, relic_rects
from ..scenes.test import COMMIT_Y, commit_rects
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
    top, bot = 120, 760
    art.background("hive", 0, top, W, bot - top, 240, 0)
    art.dim(0, top, W, bot - top, 0.35)
    for i in range(12):
        pyxel.dither(1 - i / 12)
        pyxel.rect(0, top + i * 8, W, 8, C("void"))
        pyxel.rect(0, bot - 8 - i * 8, W, 8, C("void"))
    pyxel.dither(1.0)
    pyxel.rect(0, bot, W, H - bot, C("void"))
    bob = math.sin(t / 40) * 4
    art.big(W // 2, SAFE_TOP + 70 + bob, "QUEEN", "entropy", scale=4)
    center(W // 2, SAFE_TOP + 196, "A HIGHCARD TALE", "bone", "l")
    frame = art.frame_of("queen", "idle", t, 12)
    art.sprite("queen", frame, W // 2 + 40, 716, scale=3.0)
    art.sprite("rook", art.frame_of("rook", "idle", t, 10), 110, 744, scale=3)
    log = game.campaign
    if log.get("runs"):
        center(W // 2, 772, f"Runs {log.get('runs', 0)}  |  Queen slain {log.get('queen_slain', 0)}", "ash", "m", None)
    art.menu(scene.menu)
    center(W // 2, H - SAFE_BOTTOM - 24, "CC0 art: OneBitPudding, ansimuz, Kenney", "line", "s", None)
    if scene.dossier:
        dossier(game)


def dossier(game):
    art.dim(0, 0, W, H, 0.8)
    x, y, w, h = 20, SAFE_TOP + 60, W - 40, H - SAFE_TOP - SAFE_BOTTOM - 120
    art.panel(x, y, w, h, fill="ink", border="rook")
    center(W // 2, y + 16, "HUNTER'S DOSSIER", "rook", "l")
    hunter = CONTENT.hunter
    lh = art.line_h("m")
    text(x + 20, y + 56, f"{hunter.name}, {hunter.title}", "bone", "l")
    ty = y + 56 + lh + 6
    for ln in wrap(hunter.blurb, w - 40, "m"):
        text(x + 20, ty, ln, "ash", "m", None)
        ty += lh
    ty += 12
    log = game.campaign
    if not log:
        text(x + 20, ty, "No runs yet. The Sovereign waits.", "ash", "m")
    for k, v in sorted(log.items()):
        if ty > y + h - 60:
            break
        text(x + 20, ty, k.replace("_", " "), "bone", "m", None)
        art.right(x + w - 20, ty, str(v), "crit", "m", None)
        ty += lh
    center(W // 2, y + h - 34, "Tap to close", "line", "m", None)


# --- Story


def story(scene, game, t):
    art.dim(0, 0, W, H, 0.9)
    col = FRAME.get(scene.frame, "bone")
    x, y, w = 16, SAFE_TOP + 16, W - 32
    top = y
    h = H - y - SAFE_BOTTOM - 16
    art.panel(x, y, w, h, fill="ink", border=col)
    lh = art.line_h("m")
    if scene.art:
        ax, ay = scene.art_xy
        art.background(scene.art if scene.art in art.BG else "hive", x + 4, y + 4, w - 8, 220, ax, ay)
        for i in range(12):  # Fade the picture into the card.
            pyxel.dither(i / 12)
            pyxel.rect(x + 4, y + 4 + 220 - 12 + i, w - 8, 1, C("ink"))
        pyxel.dither(1.0)
        y += 228
    elif getattr(scene, "foes", None):
        n = len(scene.foes)
        for i, eid in enumerate(scene.foes):
            rec = CONTENT.enemies[eid]
            fx = x + w * (i + 1) / (n + 1)
            scale = 2 if n > 2 else min(3, 2 * rec.scale)
            art.sprite(rec.art, art.frame_of(rec.art, "idle", t + i * 5, 9), fx, y + 200, scale=scale)
        y += 208
    kind = {"treachery": "TREACHERY", "enemy": "ENEMY", "boon": "BOON", "agenda": "AGENDA", "act": "ACT",
            "mythos": "MYTHOS PHASE"}.get(scene.frame, "")  # fmt: skip
    if kind:
        text(x + 16, y + 8, kind, col, "s", None)
        y += 24
    for ln in wrap(scene.title, w - 32, "xl"):
        text(x + 16, y + 6, ln, "bone", "xl")
        y += art.line_h("xl")
    y += 14
    left = scene.chars
    for para in scene.text:
        shown = para[: max(0, left)]
        left -= len(para)
        for ln in wrap(shown, w - 32, "m"):
            text(x + 16, y, ln, "bone" if not para.startswith(("LANTERN", "ROOK")) else "clue", "m", None)
            y += lh
        y += 10
        if left <= 0:
            break
    if scene.typed:
        art.menu(scene.menu)
    elif (t // 20) % 2:
        center(W // 2, top + h - 40, "tap to skip", "line", "m", None)


# --- Skill test


SKILL_COL = {"willpower": "horror", "intellect": "clue", "combat": "blood", "agility": "spore"}


def test(scene, game, t):
    run = game.run
    art.dim(0, 0, W, H, 0.8)
    art.panel(16, SAFE_TOP + 16, W - 32, H - SAFE_TOP - SAFE_BOTTOM - 32, fill="ink",
              border=SKILL_COL.get(scene.skill, "bone"))  # fmt: skip
    y0 = SAFE_TOP + 36
    center(W // 2, y0, scene.step.get("title", "Test").upper(), "bone", "xl")
    sk = scene.skill
    base = skilltest.base(run, sk, scene.committed)
    center(W // 2, y0 + 44, f"{sk.capitalize()} {base}  vs  {scene.step['difficulty']}", SKILL_COL.get(sk, "bone"), "l")
    if scene.phase == "commit":
        pct = int(scene.chance(game) * 100)
        center(W // 2, y0 + 76, f"Chance to pass: {pct}%", "crit" if pct >= 60 else "bone", "l")
        center(W // 2, COMMIT_Y - 70, "Commit cards for their icons.", "ash", "m", None)
        center(W // 2, COMMIT_Y - 46, "They rest until the next battle.", "ash", "m", None)
        for i, (uid, r) in enumerate(zip(scene.hand, commit_rects(len(scene.hand)), strict=True)):
            inst = run.find(uid)
            useful = scene.useful(game, uid)
            sel = uid in scene.committed
            rx, ry, rw, rh = r
            mini_card(inst.card, rx, ry - (20 if sel else 0), rw, rh, selected=sel, dim=not useful)
            if i == scene.cursor:
                pyxel.rectb(rx - 3, ry - 3, rw + 6, rh + 6, C("white"))
        bag(run, t, BAG_Y)
        art.menu(scene.menu)
        return
    bag(run, t, BAG_Y, shake=scene.phase == "draw")
    if scene.phase == "draw":
        return
    r = scene.result
    tok_y = 560
    pyxel.circ(W // 2, tok_y, 46, C("void"))
    pyxel.circ(W // 2, tok_y, 43, C("bone" if r["value"] is not None else "blood"))
    center(W // 2, tok_y - art.font_h("l") // 2, scene.token_text()[:9], "void", "l", None)
    if r["total"] is not None:
        center(W // 2, 640, f"{r['base']} {r['value']:+d} = {r['total']}  vs  {r['difficulty']}", "bone", "l")
    art.big(W // 2, 720, "PASS" if r["success"] else "FAIL", "spore" if r["success"] else "blood", scale=2)
    art.menu(scene.menu)


BAG_Y = 330


def bag(run, t, y, shake=False):
    dx = int(math.sin(t * 1.3) * 6) if shake else 0
    cx = W // 2 + dx
    pyxel.elli(cx - 60, y - 10, 120, 130, C("panel_hi"))
    pyxel.elli(cx - 54, y - 4, 108, 118, C("panel"))
    pyxel.tri(cx - 24, y - 6, cx + 24, y - 6, cx, y - 36, C("panel_hi"))
    center(cx, y + 36, "HIVE BAG", "ash", "m", None)
    center(cx, y + 60, f"{len(run.bag)} tokens", "line", "m", None)


# --- Reward


def reward(scene, game, t):
    pyxel.cls(C("void"))
    art.background("hive", 0, 0, W, 280, 240, 160)
    art.dim(0, 0, W, 280, 0.5)
    art.big(W // 2, SAFE_TOP + 40, "SPOILS", "crit", scale=2)
    st = scene.step
    parts = []
    if st.get("clues"):
        parts.append(f"+{st['clues']} clue")
    if st.get("scrip"):
        parts.append(f"+{st['scrip']} scrip")
    if st.get("xp"):
        parts.append(f"+{st['xp']} XP")
    center(W // 2, SAFE_TOP + 130, "   ".join(parts), "bone", "l")
    center(W // 2, CARD_Y - 44, "Choose a card (hold to read)", "ash", "m", None)
    for cid, r in zip(st["cards"], card_rects(len(st["cards"])), strict=True):
        x, y, w, h = r
        sel = scene.card == cid
        mini_card(CONTENT.card(cid), x, y - (14 if sel else 0), w, h, selected=sel)
    if st["relics"]:
        center(W // 2, RELIC_Y - 36, "Choose a relic", "ash", "m", None)
        lh = art.line_h("m")
        for rid, r in zip(st["relics"], relic_rects(len(st["relics"])), strict=True):
            rel = CONTENT.relics[rid]
            x, y, w, h = r
            art.panel(x, y, w, h, fill="ink", border="crit" if scene.relic == rid else "line")
            art.icon(rel.icon, x + 10, y + 10)
            name = wrap(rel.name, w - 44, "l")
            text(x + 34, y + 9, art.clip(name[0], w - 44, "l"), "crit", "l", None)
            for i, ln in enumerate(wrap(rel.text, w - 20, "m")[: (h - 44) // lh]):
                text(x + 10, y + 38 + i * lh, ln, "bone", "m", None)
    art.menu(scene.menu)
    if scene.inspect:
        inspect_panel(CONTENT.card(scene.inspect))


# --- Rest


def rest(scene, game, t):
    run = game.run
    pyxel.cls(C("void"))
    art.background("lab", 0, 0, W, 360, 0, 0)
    art.dim(0, 0, W, 360, 0.45)
    art.big(W // 2, SAFE_TOP + 30, "REST", "clue", scale=2)
    art.dim(0, SAFE_TOP + 110, W, 40, 0.85)
    center(W // 2, SAFE_TOP + 120, f"Health {run.hp}/{run.max_hp}   Nerve {run.nerve}/{run.max_nerve}   XP {run.xp}",
           "bone", "m")  # fmt: skip
    if scene.rested:
        center(W // 2, 270, scene.flash, "spore", "l")
    center(W // 2, LIST_Y - 32, "Spend XP (Highcard tier path)", "ash", "m", None)
    art.menu(scene.menu)


# --- Resolution


def resolution(scene, game, t):
    s = scene.summary
    pyxel.cls(C("void"))
    col = {"good": "crit", "neutral": "bone", "bad": "blood"}[s["outcome"]]
    if s["outcome"] == "good":
        art.sprite("queen", art.frame_of("queen", "death", t, 8, loop=False), W // 2, 400, scale=3.0)
    else:
        art.sprite("queen", art.frame_of("queen", "idle", t, 12), W // 2, 400, scale=3.0)
    a = min(1.0, t / 60)
    pyxel.dither(a)
    art.big(W // 2, 430, s["name"].upper(), col)
    center(W // 2, 470, {"good": "RESOLUTION 1", "neutral": "RESOLUTION 2", "bad": "BAD END"}.get(s["outcome"], ""),
           "ash", "m", None)  # fmt: skip
    lh = art.line_h("m")
    y = 506
    for ln in wrap(s["text"], W - 48, "m"):
        text(24, y, ln, "bone", "m")
        y += lh
    y += 14
    text(24, y, f"XP earned: {s['xp']}", "crit", "l")
    y += lh + 6
    for k, v in s["log"].items():
        if k.startswith(("outcome_", "runs")) or y > H - 130:
            continue
        text(24, y, f"Log: {k.replace('_', ' ')} = {v}", "ash", "m", None)
        y += lh
    pyxel.dither(1.0)
    if t >= 60:
        art.menu(scene.menu)


# --- Card list


def deck(scene, game, t):
    art.dim(0, 0, W, H, 0.92)
    center(W // 2, SAFE_TOP + 14, scene.title, "bone", "xl")
    center(W // 2, SAFE_TOP + 50, f"{len(scene.uids)} cards. Tap one to read it.", "ash", "m", None)
    pyxel.clip(0, GRID_Y - 8, W, VIEW_BOTTOM - GRID_Y + 8)
    for i, uid in enumerate(scene.uids):
        inst = scene.inst(game, uid)
        if inst is None:
            continue
        x, y, w, h = cell_rect(i, scene.scroll)
        if y > VIEW_BOTTOM or y + h < GRID_Y - 8:
            continue
        mini_card(inst.card, x, y, w, h)
    pyxel.clip()
    art.menu(scene.menu)
    if scene.inspect is not None:
        inst = scene.inst(game, scene.inspect)
        if inst:
            inspect_panel(inst.card, inst)


__all__ = ["layout"]
