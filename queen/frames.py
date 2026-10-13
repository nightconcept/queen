"""Render a recording to PNG files with no window: `just frames FILE`. Imports pyxel."""

from nightengine.host.frames import frames_main

from .autopilot import make
from .config import H, W
from .render import RENDERER


def summary(game) -> str:
    run = game.run
    where = f", at {run.location}, hp {run.hp}" if run else ""
    return f"frame {game.frame}, scene {type(game.scene).__name__}{where}"


if __name__ == "__main__":
    frames_main("Queen", W, H, RENDERER, make, summary, every=300)
