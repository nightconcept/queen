"""The battle screen (GDD 10, 14.2-14.3): the hand, dragging cards onto enemies, and playing back the events.

The rules (`rules/battle.py`) resolve a command at once and leave a list of events. This scene plays the events
one by one: each sets `view` (the snapshot to draw) and adds effects (`fx`). Input waits until they are shown.
"""

from nightengine import DOWN, LEFT, RIGHT, UP, A, B, C

from ..content import CONTENT
from ..rules import explore
from ..rules.battle import Battle, fire_preview
from ..ui import layout
from ..ui.gesture import inside
from ..ui.layout import PLAY_LINE, Slot, lerp
from .base import Button, Menu, QScene

# Frames each event holds the screen (60 fps). Events not listed take none.
DURATION = {
    "start": 24, "turn": 34, "draw": 5, "play": 10, "roll": 40, "damage": 16, "miss": 14, "shield": 8, "status": 8,
    "died": 26, "enemy_turn": 22, "act": 20, "equip": 12, "aura": 12, "entropy": 40, "won": 40, "lost": 40,
    "shuffle": 14, "discard_hand": 10, "heal": 12, "horror": 16, "summon": 20, "awaken": 50, "spent": 24,
    "execute": 20, "clue": 20, "add_cards": 14, "forced": 30, "trigger": 12, "energy": 8, "ward": 10,
    "shield_break": 14,
}  # fmt: skip
FAST = 3  # A tap during playback speeds it up this many times.


class BattleScene(QScene):
    def __init__(self, game, step: dict):
        super().__init__()
        self.step = step
        self.battle = Battle(game.run, list(step["enemies"]), boss=step.get("boss", False))
        self.ev = 0
        self.timer = 0
        self.view = self.battle.events[0].snap if self.battle.events else self.battle.snapshot()
        self.current = None  # The event on screen.
        self.fx: list[dict] = []
        self.dice: dict | None = None
        self.banner: tuple[str, str, int] | None = None  # (text, colour, frames left)
        self.slots: dict[int, Slot] = {}  # Where each hand card is drawn now, by uid.
        self.foe_x: dict[int, float] = {}
        self.anim: dict[int, tuple[str, int]] = {}  # uid -> (animation, start frame). 0 is the Hunter.
        self.lifted: int | None = None  # Hand index.
        self.drag: dict | None = None
        self.hover: int | None = None  # Enemy index under the dragged card.
        self.target_mode = False  # Keyboard targeting.
        self.target_cursor = 0
        self.inspect: tuple[str, int] | None = None
        self.speed = 1
        self.shake = 0
        self.menu = Menu()
        self.done = False

    def music(self, game):
        return "boss" if self.step.get("boss") else "battle"

    # --- Cards by uid

    def card(self, uid: int):
        b = self.battle
        for pile in (b.hand, b.draw, b.discard, b.exhaust, b.auras, b.equipment):
            for c in pile:
                if c.uid == uid:
                    return c
        if b.weapon and b.weapon.uid == uid:
            return b.weapon
        return b.run.find(uid)

    @property
    def busy(self) -> bool:
        return self.ev < len(self.battle.events) or self.timer > 0

    # --- Playback

    def next_event(self, game):
        e = self.battle.events[self.ev]
        self.ev += 1
        self.current = e
        self.view = e.snap
        self.timer = DURATION.get(e.kind, 0)
        k, d = e.kind, e.data
        if k == "turn":
            self.banner = ("YOUR TURN", "rook", 34)
            game.cue("turn")
        elif k == "enemy_turn":
            self.banner = ("ENEMY TURN", "blood", 22)
        elif k == "roll":
            self.dice = {"faces": d["faces"], "hit": d["hit"], "crit": d["crit"], "rerolled": d["rerolled"],
                         "t": 0, "hits": d["hits"], "damage": d["damage"]}  # fmt: skip
            self.anim[0] = ("shoot", self.t)
            self.timer = max(self.timer, layout.die_lands(len(d["faces"]) - 1) + 16)
            game.cue("dice")
        elif k == "damage":
            who = d["who"]
            col = "crit" if d["kind"] == "crit" else ("blood" if who == 0 else "white")
            x, y = self.fighter_xy(who)
            if d["lost"]:
                self.float(x, y - 10, str(d["lost"]), col, big=True)
            if d["blocked"]:
                self.float(x + 14, y + 6, f"-{d['blocked']}", "shield")
            self.anim[who] = ("hit", self.t)
            if who == 0:
                self.shake = 10 if d["lost"] else 4
                game.cue("hurt" if d["lost"] else "block")
            else:
                game.cue("crit" if d["kind"] == "crit" else "hit")
        elif k == "miss":
            x, y = self.fighter_xy(d["who"])
            self.float(x, y - 10, "MISS", "ash")
            game.cue("miss")
        elif k == "shield":
            x, y = self.fighter_xy(d["who"])
            self.float(x, y, f"+{d['n']}", "shield")
            game.cue("shield")
        elif k == "status":
            x, y = self.fighter_xy(d["who"])
            st = CONTENT.statuses[d["status"]]
            if d["status"] != "BROOD":
                self.float(x, y + 12, f"{st.name} {d['n']:+d}", st.colour)
        elif k == "died":
            self.anim[d["who"]] = ("death", self.t)
            game.cue("die")
        elif k == "act":
            self.anim[d["foe"]] = ("attack", self.t)
        elif k == "play":
            game.cue("play")
        elif k == "draw":
            game.cue("draw")
        elif k == "entropy":
            self.banner = ("+1 ENTROPY", "entropy", 40)
            game.cue("entropy")
        elif k == "horror":
            x, y = self.fighter_xy(0)
            self.float(x, y - 30, f"-{d['n']} NERVE", "horror", big=True)
            game.cue("horror")
        elif k == "heal":
            x, y = self.fighter_xy(d["who"])
            self.float(x, y - 10, f"+{d['n']}", "spore")
        elif k == "clue":
            self.float(160, 300, f"+{d['n']} CLUE", "clue", big=True)
            game.cue("clue")
        elif k == "spent":
            self.float(236, 380, "OUT OF AMMO", "blood")
        elif k == "forced":
            self.banner = ("TORMENTED DREAMSCAPE", "horror", 30)
        elif k == "awaken":
            self.banner = ("SHE WAKES", "entropy", 50)
            self.shake = 30
            game.cue("awaken")
        elif k == "summon":
            self.anim[d["who"]] = ("spawn", self.t)
        elif k == "execute":
            x, y = self.fighter_xy(d["who"])
            self.float(x, y - 20, "EXECUTED", "crit", big=True)
        elif k == "won":
            self.banner = ("VICTORY", "crit", 999)
            game.cue("win")
        elif k == "lost":
            self.banner = ("DEFEATED", "blood", 999)
            game.cue("lose")

    def float(self, x, y, text, col, big=False):
        self.fx.append({"kind": "num", "x": x, "y": y, "text": text, "col": col, "t": 0, "life": 50, "big": big})

    def fighter_xy(self, who: int) -> tuple[float, float]:
        if who == 0:
            return layout.HERO_FEET[0], layout.HERO_FEET[1] - 50
        foes = self.view_foes()
        for i, f in enumerate(foes):
            if f["uid"] == who:
                rec = CONTENT.enemies[f["id"]]
                h = CONTENT.art["sprites"][rec.art]["h"] * layout.foe_scale(rec)
                return self.foe_x.get(who, layout.foe_x(i, len(foes))), layout.FEET_Y - h / 2
        return 160, 200

    def view_foes(self) -> list[dict]:
        """The enemies to lay out: the living, and those still playing their death."""
        out = []
        for f in self.view["foes"]:
            if f["alive"]:
                out.append(f)
            else:
                a = self.anim.get(f["uid"])
                if a and a[0] == "death" and self.t - a[1] < 50:
                    out.append(f)
        return out

    # --- The frame

    def tick(self, game, inp, gestures):
        self.step_fx()
        if self.busy:
            if any(g.kind == "tap" for g in gestures) or inp.hit(A):
                self.speed = FAST
            for _ in range(self.speed):
                if self.timer > 0:
                    self.timer -= 1
                while self.timer <= 0 and self.ev < len(self.battle.events):
                    self.next_event(game)
            if not self.busy:
                self.speed = 1
            self.settle_hand()
            return
        self.settle_hand()
        if self.battle.over:
            self.finish_input(game, inp, gestures)
            return
        if self.inspect:
            if self.inspect[0] == "foe" and (inp.nav(LEFT) or inp.nav(RIGHT)):
                self.cycle_inspect(-1 if inp.nav(LEFT) else 1)
            elif any(g.kind in ("release", "tap") for g in gestures) or inp.hit(UP) or inp.hit(B) or inp.hit(A):
                self.inspect = None
            return
        self.pointer_input(game, gestures)
        self.key_input(game, inp)

    def step_fx(self):
        for f in self.fx:
            f["t"] += 1
        self.fx = [f for f in self.fx if f["t"] < f["life"]]
        if self.dice:
            self.dice["t"] += 1
            if self.dice["t"] > 100 and not self.busy:
                self.dice = None
        if self.banner:
            text, col, n = self.banner
            self.banner = (text, col, n - 1) if n > 1 else None
        if self.shake:
            self.shake -= 1

    def settle_hand(self):
        """Move every hand card toward its slot; the dragged one follows the finger."""
        hand = self.view["hand"]
        targets = layout.hand_slots(len(hand), self.lifted if not self.drag else None)
        live = set(hand)
        for uid, target in zip(hand, targets, strict=True):
            s = self.slots.get(uid)
            if s is None:  # Drawn: it flies in from the draw pile.
                s = self.slots[uid] = Slot(layout.PILE_DRAW[0] + 20, layout.PILE_DRAW[1] + 10, -20, 0.4)
            if self.drag and self.drag["uid"] == uid:
                tx, ty = self.drag["x"], self.drag["y"]
                s.x, s.y = lerp(s.x, tx, 0.45), lerp(s.y, ty, 0.45)
                s.rot = max(-10, min(10, self.drag["vx"] * 1.5))
                over = self.hover is not None or self.drag["y"] < PLAY_LINE
                s.scale = lerp(s.scale, 1.25 if over else 1.1, 0.3)
            else:
                s.x, s.y = lerp(s.x, target.x, 0.3), lerp(s.y, target.y, 0.3)
                s.rot, s.scale = lerp(s.rot, target.rot, 0.3), lerp(s.scale, target.scale, 0.3)
        for uid in list(self.slots):
            if uid not in live:
                del self.slots[uid]
        if self.drag:
            self.drag["vx"] *= 0.8

    def hand_index_at(self, x, y) -> int | None:
        hand = self.view["hand"]
        slots = [self.slots.get(u) or Slot(0, 0) for u in hand]
        return layout.card_at(slots, x, y, self.lifted)

    def foe_index_at(self, x, y, intents=False) -> int | None:
        """The enemy under (x, y). With `intents`, its intent badge counts too (tap to read it)."""
        foes = self.battle.foes
        living = self.view_foes()
        for i, f in enumerate(living):
            rec = CONTENT.enemies[f["id"]]
            art = CONTENT.art["sprites"][rec.art]
            h = int(art["h"] * layout.foe_scale(rec))
            r = layout.foe_rect(i, len(living), int(art["w"] * layout.foe_scale(rec)), h)
            hit = inside(x, y, r) or (intents and inside(x, y, layout.intent_rect(i, len(living), h)))
            if hit and f["alive"]:
                return next(j for j, foe in enumerate(foes) if foe.uid == f["uid"])
        return None

    def cycle_inspect(self, d: int):
        """Show the next living enemy in the inspect panel (the button path)."""
        living = [f for f in self.battle.foes if f.alive]
        if not living:
            self.inspect = None
            return
        uids = [f.uid for f in living]
        k = uids.index(self.inspect[1]) if self.inspect and self.inspect[1] in uids else -d
        self.inspect = ("foe", uids[(k + d) % len(uids)])

    def pointer_input(self, game, gestures):
        b = self.battle
        for g in gestures:
            if g.kind == "press":
                i = self.hand_index_at(g.x, g.y)
                if i is not None:
                    self.lifted = i
                    game.cue("lift")
            elif g.kind == "drag" and self.lifted is not None:
                uid = self.view["hand"][self.lifted]
                if self.drag is None:
                    self.drag = {"uid": uid, "x": g.x, "y": g.y - 30, "vx": 0.0}
                self.drag["x"], self.drag["y"] = g.x, g.y - 30
                self.drag["vx"] = self.drag["vx"] * 0.5 + g.dx
                inst = b.hand[self.lifted]
                self.hover = None
                if inst.card.target == "enemy" and g.y < PLAY_LINE:
                    j = self.foe_index_at(g.x, g.y)
                    if j is not None and b.targetable(b.foes[j]):
                        self.hover = j
            elif g.kind == "hold":
                i = self.hand_index_at(g.x, g.y)
                if i is not None:
                    self.inspect = ("card", self.view["hand"][i])
                    self.lifted = None
                    continue
                j = self.foe_index_at(g.x, g.y)
                if j is not None:
                    self.inspect = ("foe", b.foes[j].uid)
            elif g.kind == "release":
                if self.drag is not None and self.lifted is not None:
                    self.release(game, g.y)
                elif self.drag is None:
                    if self.hand_index_at(g.x, g.y) is None:
                        self.lifted = None
                self.drag = None
                self.hover = None
            elif g.kind == "tap":
                j = self.foe_index_at(g.x, g.y, intents=True)
                if j is not None:
                    self.inspect = ("foe", b.foes[j].uid)
                    self.lifted = None
                elif inside(g.x, g.y, layout.END_TURN):
                    self.end_turn(game)
                elif inside(g.x, g.y, layout.PILE_DRAW):
                    self.open_pile(game, "draw")
                elif inside(g.x, g.y, layout.PILE_DISCARD):
                    self.open_pile(game, "discard")

    def release(self, game, y):
        b = self.battle
        i = self.lifted
        inst = b.hand[i]
        played = False
        if inst.card.target == "enemy":
            if self.hover is not None:
                played = b.play(i, self.hover)
        elif y < PLAY_LINE:
            played = b.play(i, None)
        if played:
            self.fx.append(
                {"kind": "slam", "uid": inst.uid, "x": self.drag["x"], "y": self.drag["y"], "t": 0, "life": 16}
            )
            self.lifted = None
        elif y < PLAY_LINE:
            game.cue("deny")
            self.fx.append({"kind": "deny", "uid": inst.uid, "t": 0, "life": 16})

    def end_turn(self, game):
        self.lifted = None
        self.target_mode = False
        self.battle.end_turn()
        game.cue("end_turn")

    def open_pile(self, game, which: str):
        from .deck import DeckScene

        b = self.battle
        pile = b.draw if which == "draw" else b.discard
        insts = sorted(pile, key=lambda c: (c.card.cost, c.card.name)) if which == "draw" else list(pile)
        title = "Draw pile (random order)" if which == "draw" else "Discard pile"
        game.push(DeckScene(game, [c.uid for c in insts], title, cards={c.uid: c for c in insts}))

    def key_input(self, game, inp):
        b = self.battle
        n = len(b.hand)
        if inp.hit(C):
            self.end_turn(game)
            return
        if self.target_mode:
            targets = [j for j, f in enumerate(b.foes) if f.alive and b.targetable(f)]
            if not targets:
                self.target_mode = False
                return
            if self.target_cursor not in targets:
                self.target_cursor = targets[0]
            k = targets.index(self.target_cursor)
            if inp.nav(LEFT):
                self.target_cursor = targets[(k - 1) % len(targets)]
            if inp.nav(RIGHT):
                self.target_cursor = targets[(k + 1) % len(targets)]
            self.hover = self.target_cursor
            if inp.hit(A):
                if not b.play(self.lifted, self.target_cursor):
                    game.cue("deny")
                self.target_mode = False
                self.lifted = None
                self.hover = None
            if inp.hit(B):
                self.target_mode = False
                self.hover = None
            return
        if self.lifted is None and inp.hit(UP):  # Read the enemies' intents.
            self.cycle_inspect(1)
            return
        if n == 0:
            return
        if inp.nav(LEFT) or inp.nav(RIGHT):
            d = -1 if inp.nav(LEFT) else 1
            self.lifted = 0 if self.lifted is None else (self.lifted + d) % n
            game.cue("lift")
        if self.lifted is None or self.lifted >= n:
            return
        if inp.hit(UP):
            self.inspect = ("card", b.hand[self.lifted].uid)
        if inp.hit(DOWN) or inp.hit(B):
            self.lifted = None
            return
        if inp.hit(A):
            inst = b.hand[self.lifted]
            if inst.card.target == "enemy":
                self.target_mode = True
            elif b.play(self.lifted, None):
                self.lifted = None
            else:
                game.cue("deny")

    # --- Preview for the dragged or selected card

    def preview(self) -> dict | None:
        b = self.battle
        if self.lifted is None or self.lifted >= len(b.hand) or self.hover is None:
            return None
        return fire_preview(b, b.hand[self.lifted], b.foes[self.hover])

    # --- The end

    def finish_input(self, game, inp, gestures):
        label = "Continue" if self.battle.over == "won" else "Accept your fate"
        self.menu.set([Button(layout.bottom_buttons(1)[0], label, "go", style="primary")])
        if self.menu.update(inp, gestures) == "go" or inp.hit(A):
            explore.battle_done(game.run, self.step, self.battle)
            game.pop(self)
