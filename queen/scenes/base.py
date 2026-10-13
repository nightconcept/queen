"""What every Queen scene shares: a frame counter, the finger, and a button menu that works by touch and by keys.

Every pointer action also works with buttons (NightEngine rule): UP/DOWN/LEFT/RIGHT move the cursor, A confirms,
B goes back.
"""

from dataclasses import dataclass, field
from typing import Any

from nightengine import DOWN, LEFT, RIGHT, UP, A, B, Scene

from ..ui.gesture import Gesture, Touch, inside


@dataclass
class Button:
    rect: tuple[int, int, int, int]
    label: str
    value: Any = None
    enabled: bool = True
    note: str = ""  # A second line or a right-aligned hint.
    style: str = "normal"  # normal, primary, danger, ghost


@dataclass
class Menu:
    """A list of buttons. `cursor` is the keyboard selection; -1 hides it until a key is used."""

    buttons: list[Button] = field(default_factory=list)
    cursor: int = -1
    cols: int = 1
    pressed: int | None = None  # The button under a finger that is still down.

    def set(self, buttons: list[Button]):
        self.buttons = buttons
        if self.cursor >= len(buttons):
            self.cursor = len(buttons) - 1

    def at(self, x: int, y: int) -> int | None:
        for i, b in enumerate(self.buttons):
            if inside(x, y, b.rect):
                return i
        return None

    def update(self, inp, gestures: list[Gesture]) -> Any:
        """The value of the button chosen this frame, or None."""
        for g in gestures:
            if g.kind == "press":
                self.pressed = self.at(g.x, g.y)
            elif g.kind == "release":
                self.pressed = None
            if g.kind == "tap":
                i = self.at(g.x, g.y)
                if i is not None and self.buttons[i].enabled:
                    self.cursor = -1
                    return self.buttons[i].value
        n = len(self.buttons)
        if not n:
            return None
        step = {UP: -self.cols, DOWN: self.cols, LEFT: -1, RIGHT: 1}
        for b, d in step.items():
            if inp.nav(b) and (self.cols > 1 or b in (UP, DOWN)):
                self.cursor = 0 if self.cursor < 0 else (self.cursor + d) % n
        if inp.hit(A) and 0 <= self.cursor < n and self.buttons[self.cursor].enabled:
            return self.buttons[self.cursor].value
        return None


class QScene(Scene):
    """A scene with a frame counter `t` and a Touch. Subclasses implement `tick(game, inp, gestures)`."""

    overlay = False

    def __init__(self):
        self.t = 0
        self.touch = Touch()

    def update(self, game, inp):
        gestures = self.touch.update(inp.pointers)
        self.t += 1
        self.tick(game, inp, gestures)

    def tick(self, game, inp, gestures):
        pass

    def music(self, game):
        return None

    @staticmethod
    def back(inp) -> bool:
        return inp.hit(B)
