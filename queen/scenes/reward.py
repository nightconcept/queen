"""After a battle (GDD 10.8): clues and scrip, pick 1 of 3 cards or skip, and an elite's relic."""

from nightengine import A

from ..config import W
from ..content import CONTENT
from ..rules import explore
from ..ui import layout
from ..ui.gesture import inside
from ..ui.layout import CARD_H, CARD_W
from .base import Button, Menu, QScene

CARD_Y = 330
RELIC_Y = 650


def card_rects(n: int) -> list[tuple]:
    """The card choices at 1x, so their text stays sharp."""
    gap = 28
    total = n * CARD_W + (n - 1) * gap
    x0 = (W - total) // 2
    return [(x0 + i * (CARD_W + gap), CARD_Y, CARD_W, CARD_H) for i in range(n)]


def relic_rects(n: int) -> list[tuple]:
    return [(20 + i * 256, RELIC_Y, 244, 150) for i in range(n)]


class Reward(QScene):
    overlay = False

    def __init__(self, game, step: dict):
        super().__init__()
        self.step = step
        self.card: str | None = None
        self.relic: str | None = step["relics"][0] if step["relics"] else None
        self.menu = Menu()
        self.inspect: str | None = None
        self.cursor = -1

    def tick(self, game, inp, gestures):
        if self.inspect:
            if any(g.kind in ("release", "tap") for g in gestures) or inp.hit(A) or self.back(inp):
                self.inspect = None
            return
        cards = self.step["cards"]
        for g in gestures:
            if g.kind == "tap":
                for cid, r in zip(cards, card_rects(len(cards)), strict=True):
                    if inside(g.x, g.y, r):
                        self.card = None if self.card == cid else cid
                for rid, r in zip(self.step["relics"], relic_rects(len(self.step["relics"])), strict=True):
                    if inside(g.x, g.y, r):
                        self.relic = rid
            if g.kind == "hold":
                for cid, r in zip(cards, card_rects(len(cards)), strict=True):
                    if inside(g.x, g.y, r):
                        self.inspect = cid
        if inp.nav(1 << 2) or inp.nav(1 << 3):
            d = -1 if inp.nav(1 << 2) else 1
            self.cursor = (self.cursor + d) % len(cards) if self.cursor >= 0 else 0
            self.card = cards[self.cursor]
        label = f"Take {CONTENT.cards[self.card].name}" if self.card else "Skip the card"
        self.menu.set([Button(layout.bottom_buttons(1)[0], label, "go", style="primary")])
        if self.menu.update(inp, gestures) == "go":
            explore.reward_done(game.run, self.step, self.card, self.relic)
            game.cue("pick")
            game.pop(self)
