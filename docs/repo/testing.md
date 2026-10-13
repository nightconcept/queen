# Testing

- `just check`: every unittest in `tests/` (under a second), then the justfile surface check.
  - `test_layers`: no pyxel outside render/app/audio/frames.
  - `test_content`: every name in data resolves; sound notes are valid.
  - `test_battle`: dice maths, statuses, Guard, ammo, Ward, eggs, the Queen's phases, determinism.
  - `test_explore`: actions, Mythos, flips, the bag, save and load, hunters moving.
  - `test_touch`: drag a card onto an enemy, drop it back, tap End Turn (NightEngine pointers).
  - `test_run`: the autopilot plays whole runs by touch to a resolution, and the recording replays the same.
- `just check web`: builds the offline web build and runs Playwright in Chromium: the engine's checks, then
  `tests/browser/queen.spec.mjs` (title, story, map, and a card dragged with real touch events).
- `just autoplay --seed N`: records a whole run to `replays/auto-N.json`. `just replay FILE` watches it, and
  `just frames FILE` renders it to PNGs.
- `just _shots OUT "SCRIPT"`: headless 540x1170 PNGs from a tiny script (`tools/shots.py`), for example
  `just _shots out/shots "dev:scene=battle;enemies=HUSK+DRONE,wait:400,shot:battle"`.
- `just _sim 20`: the autopilot plays 20 seeds and prints the outcomes, a rough balance signal. The bot is
  simple (it does not plan blocks or choose cards), so expect a low win rate.

Always check visual changes at the phone size (540x1170) by looking at the PNGs.
