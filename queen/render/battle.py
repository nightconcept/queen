"""Draws the battle (GDD 14.2): the hive, enemies with intents, Rook, the dice tray, the hand, and effects."""

import math

import pyxel

from ..config import SAFE_TOP, H, W
from ..content import CONTENT
from ..rules import explore
from ..ui import layout
from ..ui.intenttext import effect_lines, intent_lines, status_line
from ..ui.layout import CARD_H, PLAY_LINE, clip, wrap
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
        center(x, by + 9, f"{f['hp']}/{f['max_hp']}", "bone", "m")
        if f["shields"]:
            pyxel.circ(x - bw // 2 - 5, by + 3, 8, C("void"))
            pyxel.circ(x - bw // 2 - 5, by + 3, 7, C("shield"))
            center(x - bw // 2 - 4, by - 3, str(f["shields"]), "void", "l", None)
        statuses(f["statuses"], x, by + 24, centre=True)
        intent(f.get("intent"), x, layout.FEET_Y - h - 18, t)
        if targeting and scene.battle.targetable(next(o for o in scene.battle.foes if o.uid == f["uid"])):
            if (t // 15) % 2 == 0 and f["uid"] != hover_uid:
                pyxel.rectb(x - 22, layout.FEET_Y - h - 2, 44, h + 4, C("line"))


def statuses(st: dict, x, y, centre=False):
    """Status chips: a short name and the stack, in the body font. Tap the owner to read them in full."""
    chips = [(CONTENT.statuses[sid].colour, f"{STATUS_ABBR.get(sid, sid[:2])}{n}") for sid, n in sorted(st.items())]
    widths = [art.text_w(label, "l") + 5 for _, label in chips]
    cx = x - (sum(widths) + 2 * (len(chips) - 1)) // 2 if centre else x
    for (col, label), w in zip(chips, widths, strict=True):
        pyxel.rect(cx, y, w, 13, C(col))
        text(cx + 3, y, label, "void", "l", None)
        cx += w + 2


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
    w = 22 + art.text_w(label, "l")
    art.panel(x - w // 2, y - 2 + bob, w, 18, fill="void", border=col)
    art.icon(icon_name, x - w // 2 + 2, y - 1 + bob)
    if label:
        text(x - w // 2 + 19, y + 1 + bob, label, col, "l", None)


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
    text(x0, 382, "ROOK", "rook", "l")
    art.bar(x0, 398, 56, 8, v["hp"], v["max_hp"])
    text(x0, 408, f"{v['hp']}/{v['max_hp']}", "bone", "m")
    if v["shields"]:  # The shield badge sits on the health bar's left end, as in StS.
        pyxel.circ(x0 - 2, 402, 9, C("void"))
        pyxel.circ(x0 - 2, 402, 8, C("shield"))
        center(x0 - 1, 396, str(v["shields"]), "void", "l", None)
    art.pips(x0, 424, v["nerve"], v["max_nerve"], col="horror", size=5)
    statuses(v["statuses"], x0, 434)
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
        name = card.name if art.text_w(card.name, "l") <= w - 26 else (card.face or card.name)
        text(x + 22, y + 5, clip(name, w - 26, "l"), "rook", "l", None)
        text(x + 6, y + 20, f"{scene.battle.combat + ws.dice}d6  hit {ws.hit}+  {ws.damage}/hit", "bone", "m", None)
        art.pips(x + 6, y + 38, wv["durability"] or 0, ws.durability, col="rook", size=6)
        art.right(x + w - 6, y + 35, "AMMO", "ash", "m", None)
    else:
        b = CONTENT.rules.bare_hands
        text(x + 6, y + 5, "Bare Hands", "ash", "l", None)
        text(x + 6, y + 20, f"{scene.battle.combat + b.dice}d6  hit {b.hit}+  {b.damage}/hit", "ash", "m", None)
    gx = 160
    for uid in scene.view["auras"]:
        art.panel(gx, layout.GEAR_ROW_Y, 74, 17, fill="ink", border="horror")
        text(gx + 4, layout.GEAR_ROW_Y + 2, clip(scene.card(uid).card.name, 66), "horror", "m", None)
        gx += 78
    for e in scene.view["equipment"]:
        art.panel(gx, layout.GEAR_ROW_Y, 74, 17, fill="ink", border="shield")
        n = f" {e['uses']}"
        name = clip(scene.card(e["uid"]).card.name, 66 - art.text_w(n))
        text(gx + 4, layout.GEAR_ROW_Y + 2, name + n, "shield", "m", None)
        gx += 78


DIE = 19  # The die's side in px. Pips are 3x3 on a 3-step grid.
THROW_FROM = (64, 400)  # Rook's hand: the dice fly from here into the tray.
_die_img: dict[tuple, pyxel.Image] = {}


def dice(scene, t):
    """The roll (GDD 10.3): each die is thrown from Rook, tumbles and bounces with its face flickering, then lands
    in turn. Hits light up as they land; the total shows when the last one is down. Drawing only: the faces are
    already rolled by the rules."""
    d = scene.dice
    if not d:
        return
    faces = d["faces"]
    n = len(faces)
    gap = 5
    x0 = W // 2 - (n * DIE + (n - 1) * gap) // 2
    age = d["t"]
    rerolled = {r[0] for r in d["rerolled"]}
    for i, face in enumerate(faces):
        fx, fy = x0 + i * (DIE + gap), layout.DICE_Y
        land = layout.die_lands(i)
        if age < land:
            p = age / land
            ease = 1 - (1 - p) ** 3
            x = THROW_FROM[0] + (fx - THROW_FROM[0]) * ease
            y = THROW_FROM[1] + (fy - THROW_FROM[1]) * ease
            y -= 34 * (1 - p) ** 1.5 * abs(math.sin(p * math.pi * 3))  # Three bounces, each lower.
            rot = (1 - p) ** 2 * (600 if i % 2 else -540)
            beat = 2 + int(p * 7)  # The face flickers fast, then slows as the die tires.
            shown = 1 + (age // beat * 5 + i * 3 + (age // beat) ** 2) % 6
            die(x, y, shown, "bone", rot=rot)
            continue
        since = age - land
        hit = face >= d["hit"]
        crit = hit and d["crit"] and face == 6
        col = "crit" if crit else ("bone" if hit else "panel_hi")
        drop = 2 if since < 3 else 0  # A small thud as it lands.
        die(fx, fy + drop, face, col)
        if since < 5:  # Dust.
            for k in (-1, 1):
                pyxel.pset(fx + DIE // 2 + k * (DIE // 2 + 2 + since), fy + DIE - 1 - since // 2, C("ash"))
        if hit and since < 10:
            r = 2 + since
            pyxel.rectb(fx - r, fy - r, DIE + 2 * r, DIE + 2 * r, C("crit" if crit else "white"))
        if i in rerolled:
            pyxel.rectb(fx - 1, fy - 1, DIE + 2, DIE + 2, C("crit"))
    done = layout.die_lands(n - 1)
    if age > done + 4:
        msg = f"{d['hits']} HIT" + ("S" if d["hits"] != 1 else "")
        pop = max(0, 6 - (age - done - 4))
        center(W // 2, layout.DICE_Y + DIE + 6 - pop, msg, "crit" if d["hits"] else "ash", "l")


PIPS = {1: [(1, 1)], 2: [(0, 0), (2, 2)], 3: [(0, 0), (1, 1), (2, 2)], 4: [(0, 0), (2, 0), (0, 2), (2, 2)],
        5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)], 6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]}  # fmt: skip


def die(x, y, face, col, rot=0.0):
    key = (face, col)
    img = _die_img.get(key)
    if img is None:
        img = _die_img[key] = pyxel.Image(DIE, DIE)
        img.cls(art.KEY)
        img.rect(1, 0, DIE - 2, DIE, C("void"))
        img.rect(0, 1, DIE, DIE - 2, C("void"))
        img.rect(1, 1, DIE - 2, DIE - 2, C(col))
        img.line(2, DIE - 2, DIE - 3, DIE - 2, C("ash") if col != "panel_hi" else C("line"))  # A shaded lower edge.
        for px, py in PIPS[face]:
            img.rect(3 + px * 5, 3 + py * 5, 3, 3, C("void"))
    if abs(rot) < 1:
        pyxel.blt(round(x), round(y), img, 0, 0, DIE, DIE, art.KEY)
    else:
        pyxel.blt(x, y, img, 0, 0, DIE, DIE, art.KEY, rotate=rot)


def controls(scene, t):
    v = scene.view
    for rect, label, n in ((layout.PILE_DRAW, "DRAW", v["draw"]), (layout.PILE_DISCARD, "DISC", v["discard"])):
        x, y, w, h = rect
        art.panel(x, y, w, h, fill="ink", border="line")
        center(x + w // 2, y + 3, label, "ash", "m", None)
        center(x + w // 2, y + 17, str(n), "bone", "l", None)
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
    w = max(art.text_w(label, "l"), art.text_w(kill, "l")) + 10
    x = max(4, min(W - w - 4, s.x - w / 2))
    y = s.y - CARD_H * s.scale / 2 - (36 if kill else 22)
    art.panel(x, y, w, 32 if kill else 18, fill="void", border="crit")
    text(x + 5, y + 3, label, "crit", "l", None)
    if kill:
        text(x + 5, y + 17, kill, "blood", "l", None)


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
    foe_panel(scene, foe)


def foe_panel(scene, foe):
    """Tap an enemy or its intent (GDD 14.3): what it will do next, in words, then its other moves and statuses."""
    rec = foe.rec
    art.dim(0, 0, W, H, 0.8)
    x, y, w = 16, 96, W - 32
    iw = w - 20
    view = next((f.get("intent") for f in scene.view_foes() if f["uid"] == foe.uid), None)
    lines: list[tuple[str, str, str]] = []  # (text, colour, font)
    if foe.intent is not None:
        title, body = intent_lines(foe.intent_id, foe.intent, view)
        kind = view["kind"] if view else foe.intent.kind
        lines.append(("NEXT TURN", "ash", "m"))
        lines.append((title, INTENT_ICON.get(kind, ("question", "ash"))[1], "l"))
        lines += [(ln, "bone", "m") for b in body for ln in wrap(b, iw, "m")]
        lines.append(("", "bone", "m"))
    hidden = view is not None and view.get("kind") == "unknown"
    others = [(iid, it) for iid, it in rec.intents.items() if iid != foe.intent_id]
    if others and not hidden:
        lines.append(("OTHER MOVES", "ash", "m"))
        for iid, it in others:
            body = " ".join(effect_lines(it))
            for k, ln in enumerate(wrap(f"{iid.replace('_', ' ').title()}: {body}", iw, "m")):
                lines.append((ln, INTENT_ICON.get(it.kind, ("question", "ash"))[1] if k == 0 else "bone", "m"))
        lines.append(("", "bone", "m"))
    if foe.statuses:
        lines.append(("STATUSES", "ash", "m"))
        for sid, n in foe.statuses.items():
            col = CONTENT.statuses[sid].colour
            lines += [(ln, col, "m") for ln in wrap(status_line(sid, n), iw, "m")]
    scale = min(2.0, layout.foe_scale(rec))
    feet = y + 10 + int(art.SPRITES[rec.art]["h"] * scale)
    h = min(H - y - 40, feet - y + 40 + len(lines) * 14 + 26)
    art.panel(x, y, w, h, fill="ink", border="blood")
    art.sprite(rec.art, art.frame_of(rec.art, "idle", pyxel.frame_count, 9), W // 2, feet, scale=scale)
    center(W // 2, feet + 4, rec.name, "bone", "l")
    center(W // 2, feet + 19, f"Health {foe.hp}/{foe.max_hp}   Evade {rec.evade}", "ash", "m", None)
    ty = feet + 40
    for ln, col, font in lines:
        if ty > y + h - 34:
            break
        text(x + 10, ty, ln, col, font, None)
        ty += 14
    center(W // 2, y + h - 18, "Tap to close", "line", "m", None)


__all__ = ["draw", "explore", "SAFE_TOP"]
