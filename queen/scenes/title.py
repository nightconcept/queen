"""The title: New Run, Continue, and the Hunter's dossier (the campaign log)."""

from ..config import H
from ..ui import layout
from .base import Button, Menu, QScene


class Title(QScene):
    def __init__(self):
        super().__init__()
        self.menu = Menu()
        self.dossier = False

    def buttons(self, game) -> list[Button]:
        items = []
        if game.saved_run:
            items.append(("Continue", "continue", "primary"))
        items.append(("New Run", "new", "normal" if game.saved_run else "primary"))
        items.append(("Dossier", "dossier", "ghost"))
        rects = layout.button_column(len(items), H - 230, h=44, gap=10, x=40, w=240)
        return [Button(r, label, value, style=style) for r, (label, value, style) in zip(rects, items, strict=True)]

    def tick(self, game, inp, gestures):
        if self.dossier:
            if self.back(inp) or any(g.kind == "tap" for g in gestures) or inp.hit(1 << 4):
                self.dossier = False
            return
        self.menu.set(self.buttons(game))
        choice = self.menu.update(inp, gestures)
        if choice == "new":
            game.new_run()
        elif choice == "continue":
            game.continue_run()
        elif choice == "dossier":
            self.dossier = True
