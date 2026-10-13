"""A card list over any screen: the deck, the draw pile, the discard pile. Tap a card to see it large."""

from nightengine import A

from ..config import SAFE_BOTTOM, SAFE_TOP, H, W
from ..ui import layout
from ..ui.gesture import inside
from ..ui.layout import CARD_H, CARD_W
from .base import Button, Menu, QScene

COLS = 4
CELL_W, CELL_H = CARD_W, CARD_H  # Cards at 1x: scaled 1-bit text does not read.
GRID_Y = SAFE_TOP + 84
GAP = 12
VIEW_BOTTOM = H - SAFE_BOTTOM - 96  # Above the Close button.


def cell_rect(i: int, scroll: int) -> tuple:
    row, col = divmod(i, COLS)
    x0 = (W - COLS * CELL_W - (COLS - 1) * GAP) // 2
    return (x0 + col * (CELL_W + GAP), GRID_Y + row * (CELL_H + GAP) - scroll, CELL_W, CELL_H)


class DeckScene(QScene):
    overlay = True

    def __init__(self, game, uids: list[int], title: str, cards=None):
        super().__init__()
        self.title = title
        self.uids = uids
        self.cards = cards  # {uid: CardInst} for battle-only cards; else the run's deck.
        self.scroll = 0
        self.inspect: int | None = None
        self.menu = Menu()

    def inst(self, game, uid):
        if self.cards and uid in self.cards:
            return self.cards[uid]
        return game.run.find(uid)

    def max_scroll(self) -> int:
        rows = (len(self.uids) + COLS - 1) // COLS
        return max(0, GRID_Y + rows * (CELL_H + GAP) - VIEW_BOTTOM)

    def tick(self, game, inp, gestures):
        if self.inspect is not None:
            if any(g.kind == "tap" for g in gestures) or inp.hit(A) or self.back(inp):
                self.inspect = None
            return
        for g in gestures:
            if g.kind == "drag":
                self.scroll = max(0, min(self.max_scroll(), self.scroll - g.dy))
            if g.kind == "tap" and g.y < VIEW_BOTTOM:
                for i, uid in enumerate(self.uids):
                    if inside(g.x, g.y, cell_rect(i, self.scroll)):
                        self.inspect = uid
        if inp.nav(1 << 1):
            self.scroll = min(self.max_scroll(), self.scroll + CELL_H // 2)
        if inp.nav(1 << 0):
            self.scroll = max(0, self.scroll - CELL_H // 2)
        self.menu.set([Button(layout.bottom_buttons(1)[0], "Close", "close")])
        if self.menu.update(inp, gestures) == "close" or self.back(inp):
            game.pop(self)
