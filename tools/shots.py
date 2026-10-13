"""Headless pictures of the game at phone size, from scripted input. No window opens.

    uv run python tools/shots.py OUT_DIR [--seed N] [--scale S] [SCRIPT ...]

Each SCRIPT is a comma-separated list of commands, run in order on one game:

    dev:scene=battle;enemies=DRONE,SPITTER   start in a `just dev` state (pairs split by ;)
    wait:N            step N frames with no input
    tap:X:Y           a finger tap at a logical pixel
    drag:X0:Y0:X1:Y1  a finger drag (press, move over 12 frames, release)
    hold:X:Y          press and hold for 30 frames, then keep holding (shot it, then release with up)
    up                release a held finger
    key:NAME          press a button for one frame (UP DOWN LEFT RIGHT A B C)
    shot:NAME         save OUT_DIR/NAME.png

Example: uv run python tools/shots.py out/shots "dev:scene=battle,wait:240,shot:battle"
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pyxel  # noqa: E402

from nightengine import DOWN, LEFT, RIGHT, UP, A, B, C, Target, dev_event  # noqa: E402
from nightengine.pointer import Pointer, PointerKind, PointerPhase  # noqa: E402
from queen.config import H, W  # noqa: E402
from queen.game import QueenGame  # noqa: E402
from queen.render import RENDERER  # noqa: E402

BUTTONS = {"UP": UP, "DOWN": DOWN, "LEFT": LEFT, "RIGHT": RIGHT, "A": A, "B": B, "C": C}


def touch(x, y, sx, sy, phase):
    return (Pointer(1, int(x), int(y), int(sx), int(sy), phase, PointerKind.TOUCH),)


class Driver:
    def __init__(self, seed: int, out: Path, scale: int):
        self.game = QueenGame(seed, Target("android", W, H))
        self.out, self.scale = out, scale
        self.held: tuple | None = None

    def step(self, code=0, pointers=(), events=()):
        self.game.step(code, pointers, events)

    def run(self, script: str):
        for cmd in script.split(","):
            name, *args = cmd.split(":")
            getattr(self, "cmd_" + name)(*args)

    def cmd_dev(self, pairs: str):
        self.step(events=tuple(dev_event(p) for p in pairs.split(";")))

    def cmd_wait(self, n):
        for _ in range(int(n)):
            self.step()

    def cmd_tap(self, x, y):
        self.step(pointers=touch(x, y, x, y, PointerPhase.PRESSED))
        self.step(pointers=touch(x, y, x, y, PointerPhase.RELEASED))
        self.cmd_wait(2)

    def cmd_drag(self, x0, y0, x1, y1):
        x0, y0, x1, y1 = map(int, (x0, y0, x1, y1))
        self.step(pointers=touch(x0, y0, x0, y0, PointerPhase.PRESSED))
        for i in range(1, 13):
            f = i / 12
            self.step(pointers=touch(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, x0, y0, PointerPhase.MOVED))
        for _ in range(6):
            self.step(pointers=touch(x1, y1, x0, y0, PointerPhase.HELD))
        self.held = (x1, y1, x0, y0)

    def cmd_hold(self, x, y):
        self.step(pointers=touch(x, y, x, y, PointerPhase.PRESSED))
        for _ in range(30):
            self.step(pointers=touch(x, y, x, y, PointerPhase.HELD))
        self.held = (int(x), int(y), int(x), int(y))

    def cmd_up(self):
        if self.held:
            x, y, sx, sy = self.held
            self.step(pointers=touch(x, y, sx, sy, PointerPhase.RELEASED))
            self.held = None
            self.cmd_wait(2)

    def cmd_key(self, name):
        self.step(BUTTONS[name])
        self.step()

    def cmd_shot(self, name):
        RENDERER.draw(self.game)
        if self.held:  # Draw a fingertip so the picture shows where the touch is.
            x, y, _, _ = self.held
            pyxel.circb(x, y, 6, 7)
        pyxel.screen.save(str(self.out / name), self.scale)
        print(f"{self.out / name}.png  [{type(self.game.scene).__name__}]")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out")
    parser.add_argument("scripts", nargs="+")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--scale", type=int, default=1)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    pyxel.init(W, H, title="Queen shots", headless=True)
    RENDERER.setup()
    for script in args.scripts:
        Driver(args.seed, out, args.scale).run(script)


if __name__ == "__main__":
    main()
