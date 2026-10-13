"""A rest (GDD 8.2, 13.2): heal or recover nerve, then spend XP on upgrades."""

from ..rules import explore, rewards
from ..ui import layout
from .base import Button, Menu, QScene

LIST_Y = 250
ROW_H = 30


class Rest(QScene):
    def __init__(self, game, step: dict):
        super().__init__()
        self.step = step
        self.rested = False
        self.menu = Menu()
        self.scroll = 0
        self.flash = ""

    def options(self, game) -> list[dict]:
        return rewards.upgrades(game.run)

    def buttons(self, game) -> list[Button]:
        run = game.run
        out = []
        if not self.rested:
            heal = int(run.max_hp * 0.3)
            r1, r2 = layout.button_grid(2, 150, h=44)
            out.append(Button(r1, "Patch up", "heal", note=f"+{heal} health", style="primary"))
            out.append(Button(r2, "Steady", "nerve", note="+2 nerve", style="primary"))
        opts = self.options(game)
        visible = opts[self.scroll : self.scroll + 10]
        for i, o in enumerate(visible):
            rect = (12, LIST_Y + i * (ROW_H + 4), 296, ROW_H)
            out.append(Button(rect, o["label"], o, enabled=o["cost"] <= run.xp, note=f"{o['cost']} XP"))
        if len(opts) > 10:
            out.append(Button((12, LIST_Y + 10 * (ROW_H + 4), 144, 28), "Up", "up", style="ghost"))
            out.append(Button((164, LIST_Y + 10 * (ROW_H + 4), 144, 28), "Down", "down", style="ghost"))
        out.append(Button(layout.bottom_buttons(1)[0], "Move on", "done", style="normal"))
        return out

    def tick(self, game, inp, gestures):
        run = game.run
        self.menu.set(self.buttons(game))
        choice = self.menu.update(inp, gestures)
        if choice in ("heal", "nerve"):
            explore.rest(run, choice)
            self.rested = True
            self.flash = "You feel steadier." if choice == "nerve" else "You patch the worst of it."
            game.cue("heal")
        elif choice == "up":
            self.scroll = max(0, self.scroll - 10)
        elif choice == "down":
            self.scroll = min(max(0, len(self.options(game)) - 10), self.scroll + 10)
        elif choice == "done" or self.back(inp):
            explore.step_done(run, self.step)
            game.save_run()
            game.pop(self)
        elif isinstance(choice, dict):
            if rewards.spend(run, choice):
                self.flash = choice["label"] + "."
                game.cue("pick")
