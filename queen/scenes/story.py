"""A story card (GDD 14.5): art, typed-out text, and choices. Also flips, Mythos, engagement, and notes."""

from ..content import CONTENT
from ..rules import explore, skilltest
from ..ui import layout
from .base import Button, Menu, QScene

TYPE_SPEED = 2  # Characters per frame.
# The picture at the top of a card that has none of its own: (background, crop x, y).
FRAME_ART = {"agenda": ("hive", (420, 150)), "act": ("hive", (60, 190)), "mythos": ("hive", (560, 20)),
             "story": ("lab", (0, 60))}  # fmt: skip


class StoryScene(QScene):
    overlay = True

    def __init__(self, game, step: dict):
        super().__init__()
        self.step = step
        self.menu = Menu()
        kind = step["kind"]
        run = game.run
        if kind == "story":
            rec = CONTENT.scenario.stories[step["id"]]
            self.title, self.frame, self.text = rec.title, rec.kind, list(rec.text)
            self.art, self.art_xy = rec.art, rec.art_xy
        elif kind == "engage":
            foes = run.loc(step["location"]).enemies
            names = ", ".join(CONTENT.enemies[e].name for e in foes)
            self.title, self.frame = "Enemies!", "enemy"
            self.text = [f"{names} block your way."]
            self.art, self.art_xy = None, (0, 0)
            self.foes = list(foes)
        else:
            self.title, self.frame, self.text = step.get("title", ""), step.get("frame", "story"), list(step["text"])
            self.art, self.art_xy = FRAME_ART.get(self.frame, ("hive", (300, 40)))
        if self.frame == "story" and run and run.log.get("lantern_garbled"):
            self.text = [garble(p, run.seed) if p.startswith("LANTERN") else p for p in self.text]
        self.chars = 0
        self.total = sum(len(p) for p in self.text)

    @property
    def typed(self) -> bool:
        return self.chars >= self.total

    def choices(self, game) -> list[Button]:
        run = game.run
        opts = explore.story_choices(run, self.step) if run else [{"index": 0, "label": "Continue", "test": None}]
        rects = layout.bottom_buttons(len(opts))
        out = []
        for r, o in zip(rects, opts, strict=True):
            note = ""
            if o["test"]:
                t = o["test"]
                pct = int(100 * skilltest.chance(run, t["skill"], t["difficulty"], []))
                note = f"{t['skill'].capitalize()} {t['difficulty']} | {pct}%"
            out.append(Button(r, o["label"], o["index"], note=note))
        return out

    def tick(self, game, inp, gestures):
        if not self.typed:
            self.chars += TYPE_SPEED
            if any(g.kind == "tap" for g in gestures) or inp.hit(1 << 4):
                self.chars = self.total
            return
        self.menu.set(self.choices(game))
        choice = self.menu.update(inp, gestures)
        if choice is None:
            return
        run = game.run
        if run is not None and self.step in run.steps:
            if self.step["kind"] in ("story", "engage"):
                explore.choose(run, self.step, choice)
            else:
                explore.step_done(run, self.step)
        game.pop(self)


def garble(text: str, seed: int) -> str:
    """Lantern's signal breaking up (Agenda 2): every few letters become dashes, the same way each time."""
    out = []
    for i, ch in enumerate(text):
        if ch.isalpha() and (i * 7 + seed) % 5 == 0:
            out.append("-")
        else:
            out.append(ch)
    return "".join(out)
