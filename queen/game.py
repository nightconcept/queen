"""QueenGame: the scene stack, the campaign log, the run, and saving. No pyxel."""

import json

from nightengine import DOWN, LEFT, RIGHT, UP, Game

from . import mech  # noqa: F401  (registers every handler)
from .rules import explore
from .rules.run import RunState, new_run

LOAD = "load "


class QueenGame(Game):
    repeat_buttons = (UP, DOWN, LEFT, RIGHT)

    def __init__(self, seed: int = 0, target=None):
        super().__init__(seed, target)
        self.campaign: dict[str, int] = {}
        self.saved_run: dict | None = None
        self.run: RunState | None = None
        self.dev_pairs: dict[str, str] = {}
        from .scenes.title import Title

        self.push(Title())

    # --- Host events: saved files on frame 0, `just dev` pairs

    def before_scene(self, inp):
        for event in inp.events:
            if event.startswith(LOAD):
                key, _, text = event[len(LOAD) :].partition(" ")
                try:
                    data = json.loads(text)
                except ValueError:
                    continue
                if key == "campaign" and isinstance(data, dict):
                    self.campaign = data
                elif key == "run" and isinstance(data, dict) and not data.get("outcome"):
                    self.saved_run = data
        pairs = inp.dev()
        if pairs:
            self.dev_pairs = pairs
            from .scenes.dev import start_dev

            start_dev(self, pairs)

    # --- Runs

    def new_run(self):
        self.run = new_run(self.rng.randint(0, 2**31 - 1), log=self.campaign)
        explore.start(self.run)
        self.save_run()
        self.enter_run()

    def continue_run(self):
        if self.saved_run:
            self.run = RunState.from_json(self.saved_run)
            self.enter_run()

    def enter_run(self):
        from .scenes.explore import Explore

        self.scenes.replace(Explore())

    def save_run(self):
        if self.run is not None and not self.run.outcome:
            data = self.run.to_json()
            self.saved_run = data
            self.write("run", json.dumps(data))

    def end_run(self, log: dict):
        self.campaign = log
        self.write("campaign", json.dumps(log))
        self.write("run", "null")
        self.saved_run = None

    def to_title(self):
        from .scenes.title import Title

        self.run = None
        self.scenes.replace(Title())
