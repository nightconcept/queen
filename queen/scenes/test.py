"""A skill test (GDD 14.6): the odds, commit cards, then draw from the Hive Bag."""

from nightengine import A

from ..config import W
from ..content import CONTENT
from ..rules import explore, skilltest
from ..ui import layout
from ..ui.gesture import inside
from ..ui.layout import CARD_H, CARD_W
from .base import Button, Menu, QScene

COMMIT_Y = 640

DRAW_FRAMES = 54


def commit_rects(n: int) -> list[tuple]:
    """Cards at 1x (sharp text), overlapping when there are many. A later card lies on top of an earlier one."""
    step = min(CARD_W + 6, (W - 40 - CARD_W) / max(1, n - 1))
    x0 = (W - (CARD_W + step * (n - 1))) / 2
    return [(int(x0 + i * step), COMMIT_Y, CARD_W, CARD_H) for i in range(n)]


def commit_at(n: int, x: int, y: int) -> int | None:
    """The index of the topmost commit card under (x, y)."""
    for i, r in reversed(list(enumerate(commit_rects(n)))):
        if inside(x, y, r):
            return i
    return None


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
                    i = commit_at(len(self.hand), g.x, g.y)
                    if i is not None and self.useful(game, self.hand[i]):
                        self.toggle(self.hand[i])
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
