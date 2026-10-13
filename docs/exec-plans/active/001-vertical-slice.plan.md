# Plan 001: the vertical slice

Build the slice in [GDD §18.1](../../design/GDD.md#181-the-slice-this-milestone): one full run of the
Sovereign scenario on a phone at 320 × 714.

Each phase ends with `just check` and `just lint` passing, and with frames captured at 320 × 714 and looked at.
Mark a phase done here when it is done.

## Phase 0: repo and engine — done when `just run` opens a 320 × 714 window

- [x] `git init`, the NightEngine submodule at `nightengine/` (main), and `.gitignore`.
- [x] `pyproject.toml`: the engine pin, `[tool.nightengine.web]` 320 × 714, targets, and Android portrait.
- [x] `mise.toml`, `justfile` (the engine's standard surface), `AGENTS.md`, `README.md`.
- [x] `docs/design/GDD.md`, `docs/repo/structure.md`, `docs/repo/content.md`.
- [x] The fonts (Spleen) and the art packs, imported and quantised, with `assets/art/README.md` for licences.

## Phase 1: content and rules core (headless) — done when a seeded battle plays out in a test

- [x] `content.py`: records for cards, enemies, statuses, relics, hunters, rules, bag, scenario files.
- [x] `mech/`: the registries (OPS, BEHAVIOURS, INTENT_OPS, HOOKS, CONDITIONS, STORY, LOCATION, WEAPON_SPECIALS).
- [x] `rules/battle.py`: piles, energy, the action queue, Fire with dice, shields, statuses, intents,
      auras, weapons and durability, events.
- [x] `tests/test_content.py`, `tests/test_battle.py`, `tests/test_layers.py`.

## Phase 2: the battle scene on a phone — done when you can drag a card onto an enemy and win a fight

- [x] `render/` battle layout (GDD §14.2): enemies, intents, HP bars, the hunter row, the hand fan.
- [x] Gestures (GDD §14.3): lift, drag with tilt, the target arrow, the play line, spring back, inspect.
- [x] Dice tray animation, damage numbers, the presentation queue that plays events.
- [x] Keyboard and gamepad path for every gesture.

## Phase 3: exploration and story — done when a run reaches a resolution

- [x] `rules/explore.py`: actions, Mythos, the encounter deck, act and agenda flips, Evade.
- [x] `rules/tests.py`: skill tests with the Hive Bag and commit.
- [x] Map, story, skill test, reward, rest, resolution screens.
- [x] The campaign log and saves.

## Phase 4: replays, autopilot, builds — done when the autopilot finishes a run and the APK builds

- [x] `autopilot.py` plays a full run from a seed. `frames.py` renders a replay.
- [x] `tests/test_run.py`: the autopilot reaches a resolution for several seeds.
- [x] `just build android` produces an APK (needs the Android SDK on this machine).

## Phase 5: juice and sound

- [x] Sound effects and four music loops in code (not yet listened to on a device).
- [ ] Screen shake, flashes and banners are in; the Queen's text intrusion (GDD 7.3) is only Lantern's garbling so far.

## Status (2026-10-13)

The slice plays end to end by touch, in the desktop window, in Chromium (Playwright), and as an APK build.
The autopilot wins about 1 run in 12 (it plays simply); human balance is not tuned yet.

Next: playtest on the Pixel 10 Pro; tune damage and encounter density from real runs; group the rest
screen's upgrade list by card; the Queen's UI intrusion; a second Hunter.

## Notes

- Keep the rules pure. If a scene needs a number, the rules or the data give it.
- Keep `docs/repo/content.md` up to date with every new record field and op.
