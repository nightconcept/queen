"""A skill test (GDD 14.6): the odds, commit cards, then draw from the Hive Bag."""

from nightengine import A

from ..content import CONTENT
from ..rules import explore, skilltest
from ..ui import layout
from ..ui.gesture import inside
from .base import Button, Menu, QScene

DRAW_FRAMES = 54
MINI_W, MINI_H = 56, 78


def commit_rects(n: int) -> list[tuple]:
    gap = 4
    total = n * MINI_W + (n - 1) * gap
    x0 = (320 - total) // 2
    return [(x0 + i * (MINI_W + gap), 360, MINI_W, MINI_H) for i in range(n)]


class TestScene(QScene):
    overlay = True

    def __init__(self, game, step: dict):
        super().__init__()
        self.step = step
        self.hand = skilltest.test_hand(game.run)
        self.committed: list[int] = []
        self.phase = "commit"
        self.result = None
        self.timer = 0
        self.menu = Menu()
        self.cursor = -1  # Keyboard cursor over the commit strip.

    @property
    def skill(self) -> str:
        return self.step["skill"]

    def useful(self, game, uid: int) -> bool:
        return skilltest.icons_for(game.run, uid, self.skill) > 0

    def tick(self, game, inp, gestures):
        run = game.run
        if self.phase == "commit":
            for g in gestures:
                if g.kind == "tap":
                    for uid, r in zip(self.hand, commit_rects(len(self.hand)), strict=True):
                        if inside(g.x, g.y, r) and self.useful(game, uid):
                            self.toggle(uid)
            if inp.nav(1 << 2) or inp.nav(1 << 3):
                n = len(self.hand)
                d = -1 if inp.nav(1 << 2) else 1
                self.cursor = (self.cursor + d) % max(1, n) if self.cursor >= 0 else 0
            if inp.hit(1 << 0) and 0 <= self.cursor < len(self.hand):  # UP commits the card under the cursor.
                uid = self.hand[self.cursor]
                if self.useful(game, uid):
                    self.toggle(uid)
            self.menu.set([Button(layout.bottom_buttons(1)[0], "Draw a token", "draw", style="primary")])
            if self.menu.update(inp, gestures) == "draw" or (inp.hit(A) and self.cursor < 0):
                self.result = skilltest.resolve(run, self.skill, self.step["difficulty"], self.committed)
                self.phase = "draw"
                self.timer = DRAW_FRAMES
                game.cue("bag")
        elif self.phase == "draw":
            self.timer -= 1
            if self.timer <= 0:
                self.phase = "result"
                game.cue("pass" if self.result["success"] else "fail")
        else:
            self.menu.set([Button(layout.bottom_buttons(1)[0], "Continue", "go", style="primary")])
            if self.menu.update(inp, gestures) == "go" or inp.hit(A):
                explore.test_done(run, self.step, self.result)
                game.pop(self)

    def toggle(self, uid: int):
        if uid in self.committed:
            self.committed.remove(uid)
        else:
            self.committed.append(uid)

    def chance(self, game) -> float:
        return skilltest.chance(game.run, self.skill, self.step["difficulty"], self.committed)

    def token_text(self) -> str:
        r = self.result
        t = CONTENT.bag.tokens[r["token"]]
        if t.get("auto_fail"):
            return "AUTO-FAIL"
        if t.get("elder"):
            return f"ELDER SIGN +{r['value']}"
        if t.get("symbol"):
            return f"{r['token']} {r['value']:+d}"
        return f"{r['value']:+d}"
