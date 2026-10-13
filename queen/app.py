"""The pyxel window: keys and pads, touch, sound, recording and replay, and saved files. Imports pyxel."""

import pyxel

from nightengine import DOWN, LEFT, RIGHT, UP, A, B, C, Recording
from nightengine.host import gamepad
from nightengine.host.app import App as EngineApp
from nightengine.host.app import AppConfig

from .audio import AUDIO
from .config import REPLAYS, H, W
from .game import QueenGame
from .render import RENDERER

KEYS = {
    UP: (pyxel.KEY_UP, pyxel.KEY_W),
    DOWN: (pyxel.KEY_DOWN, pyxel.KEY_S),
    LEFT: (pyxel.KEY_LEFT, pyxel.KEY_A),
    RIGHT: (pyxel.KEY_RIGHT, pyxel.KEY_D),
    A: (pyxel.KEY_RETURN, pyxel.KEY_SPACE, pyxel.KEY_Z),
    B: (pyxel.KEY_ESCAPE, pyxel.KEY_BACKSPACE, pyxel.KEY_X),
    C: (pyxel.KEY_E, pyxel.KEY_TAB),
}
KEYS = gamepad.merge(KEYS, gamepad.xbox(1))

CONFIG = AppConfig(
    title="Queen",
    width=W,
    height=H,
    keys=KEYS,
    replays=REPLAYS,
    fps=60,
    label_xy=(4, 700),
    mouse=True,
    vendor="NightCircle",
)


class App(EngineApp):
    def boot(self) -> list[str]:
        """Frame 0: the saved campaign log and run, as host events (the recording keeps them)."""
        out = []
        if self.store is not None:
            for key in ("campaign", "run"):
                text = self.store.read(key)
                if text and text.strip() not in ("null", ""):
                    out.append(f"load {key} {text}")
        return out


def inspect(game: QueenGame) -> dict:
    scene = game.scene
    out = {"scene": type(scene).__name__, "frame": game.frame}
    run = game.run
    if run:
        out.update(location=run.location, hp=run.hp, nerve=run.nerve, clues=run.clues, act=run.act,
                   agenda=run.agenda, entropy=run.entropy, deck=len(run.deck), outcome=run.outcome)  # fmt: skip
    if hasattr(scene, "battle"):
        b = scene.battle
        out["battle"] = {"turn": b.turn, "energy": b.energy, "hand": [c.id for c in b.hand], "over": b.over,
                         "foes": [(f.rec.id, f.hp, f.intent_id) for f in b.foes if f.alive]}  # fmt: skip
    return out


def run_app(seed: int | None = None, replay: Recording | None = None, dev: tuple[str, ...] = ()):
    App(CONFIG, QueenGame, RENDERER, AUDIO, seed, replay, inspect=inspect, dev=dev)
