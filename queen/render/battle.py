"""Draws the battle (GDD 14.2): the hive, enemies with intents, Rook, the dice tray, the hand, and effects."""

import math

import pyxel

from ..config import SAFE_TOP, H, W
from ..content import CONTENT
from ..rules import explore
from ..ui import layout
from ..ui.layout import CARD_H, PLAY_LINE
from . import art
from .art import C, center, text
from .cards import draw_card, inspect_panel
from .hud import top_bar

INTENT_ICON = {"attack": ("sword", "blood"), "horror": ("eye", "horror"), "defend": ("shield", "shield"),
               "buff": ("up", "rook"), "debuff": ("down", "spore"), "summon": ("skull", "entropy"),
               "hatch": ("hourglass", "spore"), "unknown": ("question", "ash")}  # fmt: skip
STATUS_ABBR = {"MOMENTUM": "MO", "EXPOSED": "EX", "SHAKEN": "SH", "BRITTLE": "BR", "FOCUS": "FO", "BLEED": "BL",
               "GUARD": "GD", "BROOD": "BD", "MARKED": "MK", "WARD": "WD", "PANICKED": "PN"}  # fmt: skip


def draw(scene, game, t):
    pyxel.cls(C("void"))
    sx = int(math.sin(t * 1.7) * scene.shake / 3) if scene.shake else 0
    pyxel.camera(sx, 0)
    backdrop(t)
    foes(scene, t)
    hero(scene, t)
    dice(scene, t)
    pyxel.camera()
    top_bar(game, scene.view)
    controls(scene, t)
    hand(scene, t)
    effects(scene, t)
    banner(scene, t)
    if scene.inspect:
        inspect(scene, game)
    if scene.battle.over and not scene.busy:
        art.dim(0, 0, W, H, 0.6)
        result = "VICTORY" if scene.battle.over == "won" else "DEFEATED"
        art.big(W // 2, 300, result, "crit" if scene.battle.over == "won" else "blood", scale=2)
        if scene.battle.clues and scene.battle.over == "won":
            center(W // 2, 360, f"+{scene.battle.clues} clue", "clue", "l")
        art.menu(scene.menu)


def backdrop(t):
    # The hive (OneBitPudding's background), cropped to the portrait battlefield.
    art.background("hive", 0, 0, W, 300, 240, 120)
    art.dim(0, 0, W, 300, 0.5)  # Push the busy hive back so the creatures' outlines read.
    pyxel.rect(0, 300, W, H - 300, C("ink"))
    for i in range(6):  # A fleshy floor that fades into the dark.
        pyxel.dither(0.9 - i * 0.14)
        pyxel.rect(0, 286 + i * 8, W, 8, C("panel"))
    pyxel.dither(1.0)
    pyxel.line(0, PLAY_LINE, W, PLAY_LINE, C("panel_hi"))


def foe_layout(scene):
    shown = scene.view_foes()
    n = len(shown)
    out = []
    for i, f in enumerate(shown):
        tx = layout.foe_x(i, n)
        x = scene.foe_x.get(f["uid"], tx)
        x = x + (tx - x) * 0.2
        scene.foe_x[f["uid"]] = x
        out.append((f, x))
    return out


def foes(scene, t):
    hover_uid = scene.battle.foes[scene.hover].uid if scene.hover is not None else None
    targeting = (
        scene.lifted is not None
        and scene.lifted < len(scene.battle.hand)
        and (scene.battle.hand[scene.lifted].card.target == "enemy")
        and (scene.drag or scene.target_mode)
    )
    for f, x in foe_layout(scene):
        rec = CONTENT.enemies[f["id"]]
        spr = art.SPRITES[rec.art]
        anim, start = scene.anim.get(f["uid"], ("idle", 0))
        age = t - start
        white = anim == "hit" and age < 6
        dx = int(math.sin(age * 2) * 3) if anim == "hit" and age < 12 else 0
        if anim == "death":
            frame = art.frame_of(rec.art, "death", age, 6, loop=False)
        elif anim == "attack" and age < 40 and "attack" in spr["anims"]:
            frame = art.frame_of(rec.art, "attack", age, 5, loop=False)
        elif anim == "spawn" and age < 40 and "hatch" in spr["anims"]:
            frame = art.frame_of(rec.art, "hatch", age, 3, loop=False)
        else:
            frame = art.frame_of(rec.art, "idle", t + f["uid"] * 7, 9)
        lunge = -int(math.sin(min(age, 16) / 16 * math.pi) * 10) if anim == "attack" and age < 16 else 0
        flip = rec.art in ("husk",)
        if f["uid"] == hover_uid:
            pyxel.dither(0.5)
            pyxel.elli(
                x - spr["w"] * layout.foe_scale(rec) / 2,
                layout.FEET_Y - 8,
                spr["w"] * layout.foe_scale(rec),
                14,
                C("crit"),
            )
            pyxel.dither(1.0)
        art.sprite(rec.art, frame, x + dx, layout.FEET_Y + lunge, scale=layout.foe_scale(rec), flip=flip, white=white)
        if not f["alive"]:
            continue
        h = spr["h"] * layout.foe_scale(rec)
        bw = max(44, min(72, int(spr["w"] * layout.foe_scale(rec) * 0.8)))
        by = layout.HP_BAR_Y
        ghost = 0
        if f["uid"] == hover_uid:
            p = scene.preview()
            if p:
                ghost = max(0, int(p["expected"]) - f["shields"])
        art.bar(x - bw // 2, by, bw, 7, f["hp"], f["max_hp"], ghost=ghost)
        center(x, by + 9, f"{f['hp']}/{f['max_hp']}", "bone", "s")
        if f["shields"]:
            pyxel.circ(x - bw // 2 - 4, by + 3, 6, C("shield"))
            center(x - bw // 2 - 4, by - 1, str(f["shields"]), "void", "s", None)
        statuses(f["statuses"], x - bw // 2, by + 19)
        intent(f.get("intent"), x, layout.FEET_Y - h - 18, t)
        if targeting and scene.battle.targetable(next(o for o in scene.battle.foes if o.uid == f["uid"])):
            if (t // 15) % 2 == 0 and f["uid"] != hover_uid:
                pyxel.rectb(x - 22, layout.FEET_Y - h - 2, 44, h + 4, C("line"))


def statuses(st: dict, x, y):
    for i, (sid, n) in enumerate(sorted(st.items())):
        s = CONTENT.statuses[sid]
        cx = x + i * 22
        pyxel.rect(cx, y, 20, 9, C(s.colour))
        text(cx + 1, y + 1, f"{STATUS_ABBR.get(sid, sid[:2])}{n}"[:4], "void", "s", None)


def intent(view, x, y, t):
    if not view:
        return
    icon_name, col = INTENT_ICON.get(view["kind"], ("question", "ash"))
    bob = int(math.sin(t / 10) * 2)
    label = ""
    if view["kind"] == "attack" and "damage" in view:
        label = f"{view['damage']}" + (f"x{view['times']}" if view.get("times", 1) > 1 else "")
    elif view["kind"] == "horror":
        label = f"{view.get('horror', '')}" + (f"+{view['damage']}" if view.get("damage") else "")
    elif view["kind"] == "defend":
        label = str(view.get("shield", ""))
    w = 22 + art.text_w(label, "m")
    art.panel(x - w // 2, y - 2 + bob, w, 18, fill="void", border=col)
    art.icon(icon_name, x - w // 2 + 2, y - 1 + bob)
    if label:
        text(x - w // 2 + 19, y + 1 + bob, label, col, "m", None)


def hero(scene, t):
    v = scene.view["hero"]
    hx, fy = layout.HERO_FEET
    anim, start = scene.anim.get(0, ("idle", 0))
    age = t - start
    if anim == "shoot" and age < 24:
        frame = art.frame_of("rook", "shoot", age, 8, loop=False)
    elif anim == "hit" and age < 14:
        frame = art.frame_of("rook", "hit", 0)
    else:
        frame = art.frame_of("rook", "idle", t, 10)
    art.sprite("rook", frame, hx, fy, scale=2, white=anim == "hit" and age < 4)
    # Health, shields, nerve and statuses beside Rook.
    x0 = 98
    text(x0, 384, "ROOK", "rook", "m")
    art.bar(x0, 400, 56, 8, v["hp"], v["max_hp"])
    text(x0, 410, f"{v['hp']}/{v['max_hp']}", "bone", "s")
    if v["shields"]:  # The shield badge sits on the health bar's left end, as in StS.
        pyxel.circ(x0 - 2, 404, 8, C("void"))
        pyxel.circ(x0 - 2, 404, 7, C("shield"))
        center(x0 - 1, 399, str(v["shields"]), "void", "s", None)
    art.pips(x0, 422, v["nerve"], v["max_nerve"], col="horror", size=4)
    statuses(v["statuses"], x0, 432)
    weapon_box(scene)


def weapon_box(scene):
    x, y, w, h = layout.WEAPON_BOX
    wv = scene.view["weapon"]
    art.panel(x, y, w, h, fill="ink", border="rook" if wv else "panel_hi")
    if wv:
        inst = scene.card(wv["uid"])
        card = inst.card
        ws = card.weapon
        art.icon("gun", x + 4, y + 4)
        text(x + 22, y + 5, card.name[:20], "rook", "s", None)
        text(x + 22, y + 15, f"{scene.battle.combat + ws.dice}d6  hit {ws.hit}+  {ws.damage}/hit", "bone", "s", None)
        art.pips(x + 22, y + 28, wv["durability"] or 0, ws.durability, col="rook", size=5)
        text(x + 22, y + 36, "AMMO", "ash", "s", None)
    else:
        b = CONTENT.rules.bare_hands
        text(x + 8, y + 8, "Bare Hands", "ash", "s", None)
        text(x + 8, y + 20, f"{scene.battle.combat + b.dice}d6  hit {b.hit}+  {b.damage}/hit", "ash", "s", None)
    gx = 160
    for uid in scene.view["auras"]:
        art.panel(gx, layout.GEAR_ROW_Y, 70, 14, fill="ink", border="horror")
        text(gx + 3, layout.GEAR_ROW_Y + 3, scene.card(uid).card.name[:13], "horror", "s", None)
        gx += 74
    for e in scene.view["equipment"]:
        art.panel(gx, layout.GEAR_ROW_Y, 70, 14, fill="ink", border="shield")
        text(gx + 3, layout.GEAR_ROW_Y + 3, f"{scene.card(e['uid']).card.name[:10]} {e['uses']}", "shield", "s", None)
        gx += 74


def dice(scene, t):
    d = scene.dice
    if not d:
        return
    faces = d["faces"]
    n = len(faces)
    size, gap = 16, 4
    total = n * size + (n - 1) * gap
    x0 = W // 2 - total // 2
    y = layout.DICE_Y
    age = d["t"]
    settle = 22
    for i, face in enumerate(faces):
        x = x0 + i * (size + gap)
        rolling = age < settle + i * 2
        if rolling:
            shown = 1 + (age * 7 + i * 3) % 6
            jy = -int(abs(math.sin((age + i * 5) / 3)) * 10)
        else:
            shown, jy = face, 0
        hit = not rolling and face >= d["hit"]
        crit = hit and d["crit"] and face == 6
        rer = any(r[0] == i for r in d["rerolled"])
        die(x, y + jy, size, shown, "crit" if crit else ("bone" if hit else "panel_hi"), rer and not rolling)
    if age > settle + n * 2:
        msg = f"{d['hits']} HIT" + ("S" if d["hits"] != 1 else "")
        center(W // 2, y + 22, msg, "crit" if d["hits"] else "ash", "m")


PIPS = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (2, 0), (0, 2), (2, 2)],
        5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)], 6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}  # fmt: skip


def die(x, y, size, face, col, rerolled=False):
    art.panel(x, y, size, size, fill=col, border="void", radius=2)
    for px, py in PIPS[face]:
        pyxel.rect(x + 3 + px * 4, y + 3 + py * 4, 2, 2, C("void"))
    if rerolled:
        pyxel.rectb(x - 1, y - 1, size + 2, size + 2, C("crit"))


def controls(scene, t):
    v = scene.view
    for rect, label, n in ((layout.PILE_DRAW, "DRAW", v["draw"]), (layout.PILE_DISCARD, "DISC", v["discard"])):
        x, y, w, h = rect
        art.panel(x, y, w, h, fill="ink", border="line")
        center(x + w // 2, y + 3, label, "ash", "s", None)
        center(x + w // 2, y + 13, str(n), "bone", "m", None)
    ex, ey = layout.ENERGY
    art.orb(ex, ey, 14, "energy" if v["energy"] else "panel_hi", str(v["energy"]))
    x, y, w, h = layout.END_TURN
    busy = scene.busy or scene.battle.over
    out_of_moves = not busy and not any(
        scene.battle.card_cost(c) <= v["energy"] and not c.card.has("unplayable") for c in scene.battle.hand
    )
    style = "ghost" if busy else ("primary" if out_of_moves and (t // 20) % 2 == 0 else "normal")
    from ..scenes.base import Button

    art.button(Button(layout.END_TURN, "END TURN", style=style))


def hand(scene, t):
    b = scene.battle
    uids = scene.view["hand"]
    drag_uid = scene.drag["uid"] if scene.drag else None
    idle = not scene.busy and not b.over
    order = list(range(len(uids)))
    if scene.lifted is not None and scene.lifted < len(uids):
        order.remove(scene.lifted)
        order.append(scene.lifted)
    for i in order:
        uid = uids[i]
        if uid == drag_uid:
            continue
        s = scene.slots.get(uid)
        if s is None:
            continue
        inst = scene.card(uid)
        target = b.foes[scene.hover] if scene.hover is not None else None
        cost = b.card_cost(inst, target) if idle and inst in b.hand else inst.card.cost
        playable = idle and inst in b.hand and cost <= v_energy(scene) and not inst.card.has("unplayable")
        glow = "energy" if playable and i == scene.lifted else None
        draw_card(inst.card, s.x, s.y, s.scale, s.rot, cost=cost, dim=idle and not playable, glow=glow)
    if scene.drag:
        uid = scene.drag["uid"]
        s = scene.slots.get(uid)
        inst = scene.card(uid)
        if s and inst:
            if inst.card.target == "enemy" and scene.drag["y"] < PLAY_LINE:
                arrow(scene, s, t)
            elif inst.card.target != "enemy" and scene.drag["y"] < PLAY_LINE:
                for i in range(3):
                    pyxel.line(0, PLAY_LINE - i, W, PLAY_LINE - i, C("energy" if (t // 6 + i) % 2 else "rook"))
                art.center(W // 2, PLAY_LINE - 16, "RELEASE TO PLAY", "energy", "m")
            target = b.foes[scene.hover] if scene.hover is not None else None
            draw_card(
                inst.card,
                s.x,
                s.y,
                s.scale,
                s.rot,
                cost=b.card_cost(inst, target),
                glow="crit"
                if (scene.hover is not None or (inst.card.target != "enemy" and scene.drag["y"] < PLAY_LINE))
                else None,
            )
            preview_tag(scene, s)
    if scene.target_mode and scene.lifted is not None and scene.hover is not None:
        uid = uids[scene.lifted] if scene.lifted < len(uids) else None
        s = scene.slots.get(uid) if uid else None
        if s:
            preview_tag(scene, s)


def v_energy(scene) -> int:
    return scene.view["energy"]


def arrow(scene, s, t):
    x1, y1 = scene.drag["x"], scene.drag["y"] - CARD_H // 2
    if scene.hover is not None:
        foe = scene.battle.foes[scene.hover]
        fx, fy = scene.fighter_xy(foe.uid)
        x1, y1 = fx, fy
    pts = layout.arrow_points(s.x, s.y - CARD_H * s.scale / 2, x1, y1, 12)
    col = C("crit" if scene.hover is not None else "bone")
    for i, (px, py) in enumerate(pts[:-1]):
        if (i + t // 4) % 2 == 0:
            pyxel.circ(px, py, 2, col)
    px, py = pts[-1]
    pyxel.circ(px, py, 4, col)
    pyxel.circb(px, py, 6, col)


def preview_tag(scene, s):
    p = scene.preview()
    if not p:
        return
    label = f"{p['dice']}d6 {p['hit']}+  ~{p['expected']:.0f}"
    if p["times"] > 1:
        label += f" x{p['times']}"
    kill = f"KILL {int(p['kill'] * 100)}%" if p.get("kill") else ""
    w = max(art.text_w(label, "s"), art.text_w(kill, "s")) + 8
    x = max(4, min(W - w - 4, s.x - w / 2))
    y = s.y - CARD_H * s.scale / 2 - (26 if kill else 16)
    art.panel(x, y, w, 24 if kill else 14, fill="void", border="crit")
    text(x + 4, y + 3, label, "crit", "s", None)
    if kill:
        text(x + 4, y + 13, kill, "blood", "s", None)


def effects(scene, t):
    for f in scene.fx:
        if f["kind"] == "num":
            age = f["t"]
            pop = 1.0 + max(0, 6 - age) * 0.12 if f["big"] else 1.0
            y = f["y"] - age * 0.6
            if age > f["life"] - 12:
                pyxel.dither((f["life"] - age) / 12)
            if f["big"]:
                art.big(f["x"], y - 12, f["text"], f["col"], scale=pop)
            else:
                center(f["x"], y, f["text"], f["col"], "m")
            pyxel.dither(1.0)
        elif f["kind"] == "slam":
            age = f["t"]
            inst = scene.card(f["uid"])
            if inst:
                pyxel.dither(max(0.0, 1 - age / 16))
                draw_card(inst.card, f["x"], f["y"] - age * 2, 1.25 + age * 0.04)
                pyxel.dither(1.0)


def banner(scene, t):
    if not scene.banner:
        return
    msg, col, n = scene.banner
    if msg in ("VICTORY", "DEFEATED"):
        return
    a = min(1.0, n / 10)
    pyxel.dither(a * 0.8)
    pyxel.rect(0, 200, W, 44, C("void"))
    pyxel.dither(a)
    pyxel.line(0, 200, W, 200, C(col))
    pyxel.line(0, 243, W, 243, C(col))
    art.big(W // 2, 210, msg, col)
    pyxel.dither(1.0)


def inspect(scene, game):
    kind, uid = scene.inspect
    if kind == "card":
        inst = scene.card(uid)
        if inst:
            inspect_panel(inst.card, inst)
        return
    foe = next((f for f in scene.battle.foes if f.uid == uid), None)
    if foe is None:
        return
    rec = foe.rec
    art.dim(0, 0, W, H, 0.75)
    x, y, w, h = 30, 140, 260, 360
    art.panel(x, y, w, h, fill="ink", border="blood")
    art.sprite(
        rec.art,
        art.frame_of(rec.art, "idle", pyxel.frame_count, 9),
        W // 2,
        y + 120,
        scale=min(2.0, layout.foe_scale(rec) * 1.5),
    )
    center(W // 2, y + 128, rec.name, "bone", "l")
    center(W // 2, y + 148, f"Health {foe.hp}/{foe.max_hp}  Evade {rec.evade}", "ash", "s", None)
    ty = y + 166
    for iid, it in rec.intents.items():
        if ty > y + h - 20:
            break
        parts = []
        for e in it.effects:
            if e.op == "attack":
                parts.append(f"{e.damage} dmg" + (f" x{e.times}" if e.get("times", 1) > 1 else ""))
            elif e.op in ("horror", "shield", "shield_all"):
                parts.append(f"{e.op.replace('_', ' ')} {e.n}")
            elif e.op == "apply":
                parts.append(f"{CONTENT.statuses[e.status].name} {e.n}")
            else:
                parts.append(e.op)
        text(x + 10, ty, iid.replace("_", " ").title(), INTENT_ICON[it.kind][1], "s", None)
        text(x + 100, ty, ", ".join(parts)[:30], "bone", "s", None)
        ty += 12
    ty += 6
    for sid, n in foe.statuses.items():
        st = CONTENT.statuses[sid]
        text(x + 10, ty, f"{st.name} {n}: {st.text.replace('{n}', str(n))}"[:48], st.colour, "s", None)
        ty += 10


__all__ = ["draw", "explore", "SAFE_TOP"]
