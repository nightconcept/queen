"""The end of the scenario (GDD 8.6): the resolution text, XP, and what the campaign log keeps."""

from nightengine import A

from ..rules import explore
from ..ui import layout
from .base import Button, Menu, QScene


class Resolution(QScene):
    def __init__(self, game, step: dict):
        super().__init__()
        self.summary = explore.resolve(game.run, step)
        game.end_run(self.summary["log"])
        self.menu = Menu()

    def music(self, game):
        return "end"

    def tick(self, game, inp, gestures):
        if self.t < 60:
            return
        self.menu.set([Button(layout.bottom_buttons(1)[0], "Back to the title", "go", style="primary")])
        if self.menu.update(inp, gestures) == "go" or inp.hit(A):
            game.to_title()
