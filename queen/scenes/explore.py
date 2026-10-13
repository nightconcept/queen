"""The map (GDD 14.4): locations, the agenda and act cards, and the action bar. It also opens the screen for each
interactive step that the rules queue (story, test, battle, reward, rest, resolution)."""

from nightengine import B, C

from ..content import CONTENT
from ..rules import explore
from ..ui import layout
from ..ui.gesture import inside
from .base import Button, Menu, QScene


class Explore(QScene):
    def __init__(self):
        super().__init__()
        self.menu = Menu()
        self.saved_round = None
        self.message = ""

    def music(self, game):
        return "explore"

    def open_step(self, game, step: dict) -> bool:
        from .battle import BattleScene
        from .resolution import Resolution
        from .rest import Rest
        from .reward import Reward
        from .story import StoryScene
        from .test import TestScene

        kind = step["kind"]
        scene = {
            "story": StoryScene,
            "say": StoryScene,
            "engage": StoryScene,
            "test": TestScene,
            "battle": BattleScene,
            "reward": Reward,
            "rest": Rest,
            "resolve": Resolution,
        }[kind](game, step)
        game.push(scene)
        return True

    def buttons(self, game) -> list[Button]:
        run = game.run
        acts = [a for a in explore.actions(run) if a["kind"] != "move"]
        items = [
            Button((0, 0, 0, 0), a["label"], a, style="primary" if a["kind"] == "advance" else "normal") for a in acts
        ]
        items.append(Button((0, 0, 0, 0), "Deck", {"kind": "deck"}, style="ghost"))
        rects = layout.button_grid(len(items), layout.ACTION_Y + 34)
        for b, r in zip(items, rects, strict=True):
            b.rect = r
        return items

    def tick(self, game, inp, gestures):
        run = game.run
        step = explore.advance(run)
        if step is not None:
            self.open_step(game, step)
            return
        if run.outcome:
            return
        if self.saved_round != (run.round, run.actions, len(run.deck), run.xp):
            self.saved_round = (run.round, run.actions, len(run.deck), run.xp)
            game.save_run()
        moves = {a["to"]: a for a in explore.actions(run) if a["kind"] == "move"}
        for g in gestures:
            if g.kind == "tap":
                for lid, a in moves.items():
                    if inside(g.x, g.y, layout.node_rect(CONTENT.scenario.locations[lid].pos)):
                        explore.act(run, a)
                        return
                if inside(g.x, g.y, layout.AGENDA_BOX):
                    self.show_card(game, "agenda")
                    return
                if inside(g.x, g.y, layout.ACT_BOX):
                    self.show_card(game, "act")
                    return
            if g.kind == "hold":
                for lid, rec in CONTENT.scenario.locations.items():
                    if inside(g.x, g.y, layout.node_rect(rec.pos)) and run.loc(lid).revealed:
                        from .story import StoryScene

                        game.push(
                            StoryScene(game, {"kind": "say", "title": rec.name, "text": [rec.text], "frame": "story"})
                        )
                        return
        self.menu.set(self.buttons(game) + self.move_buttons(moves))
        choice = self.menu.update(inp, gestures)
        if inp.hit(C):
            choice = {"kind": "deck"}
        if choice is not None:
            if choice["kind"] == "deck":
                from .deck import DeckScene

                game.push(DeckScene(game, [c.uid for c in run.deck], "Your deck"))
            else:
                explore.act(run, choice)
        if inp.hit(B):
            self.menu.cursor = -1

    def move_buttons(self, moves: dict) -> list[Button]:
        """Invisible buttons on the map nodes, so the keyboard cursor can reach the moves too."""
        out = []
        for lid, a in moves.items():
            out.append(Button(layout.node_rect(CONTENT.scenario.locations[lid].pos), a["label"], a, style="node"))
        return out

    def show_card(self, game, which: str):
        from .story import StoryScene

        run = game.run
        if which == "agenda":
            g = explore.current_agenda(run)
            if g is None:
                return
            text = [g.front, f"Entropy: {run.entropy} / {g.entropy}. Each Mythos phase adds 1."]
            step = {"kind": "say", "title": f"Agenda {g.id}a: {g.name}", "text": text, "frame": "agenda"}
        else:
            a = explore.current_act(run)
            if a is None:
                return
            need = f"Spend {a.clues} clues to advance. You have {run.clues}." if a.clues else a.front
            step = {"kind": "say", "title": f"Act {a.id}a: {a.name}", "text": [a.front, need], "frame": "act"}
        game.push(StoryScene(game, step))
