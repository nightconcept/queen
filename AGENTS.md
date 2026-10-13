# Queen

⚠ This file is hard-limited to ≤100 lines. Update spokes, not the hub.

## Intent

Queen is a single-player deckbuilder prototype of the Highcard theme (`../highcard`), for phones first.
Battles follow Slay the Spire with Highcard's dice and weapons and Marvel Snap's card feel. The run follows
Arkham Horror LCG: an act/agenda race across a small location map, a chaos bag, story cards, and a campaign
log. One Kinetic Hunter, Rook, hunts the alien Queen in the hive-ship Sovereign.
The game runs on NightEngine (Pyxel only). Portrait 320x714 is the only screen size: an exact 4x on the
target phone, the Pixel 10 Pro (1280x2856). Test every visual change at that size.

## Stack

- Python 3.11+ (venv 3.14), Pyxel 2.9.9 through the NightEngine submodule at `nightengine/` (main branch).
- `uv`, `just`, `ruff`, `unittest`. Node + Playwright for the browser checks. JDK 17 (mise) and the Android SDK
  for the APK.
- Art: CC0 packs (OneBitPudding, ansimuz, Kenney), imported by `tools/import_art.py`. Font: Spleen.

## Essential Commands

The public recipes are NightEngine's standard surface ([Game commands](nightengine/docs/games/commands.md)).

- **Setup**: `just setup`
- **Run**: `just run` (`--target android` plays the phone build with the mouse as a finger; `--browser`)
- **Agent entry point**: `just dev scene=battle enemies=HUSK+DRONE` (keys in `queen/scenes/dev.py`)
- **Test**: `just check` (under a second); `just check web` runs Playwright in Chromium
- **Lint / Format**: `just lint` / `just fmt`
- **Pictures**: `just _shots out/shots "dev:scene=map,wait:300,shot:map"` (headless, 320x714)
- **Recordings**: `just autoplay --seed 4`, `just replay FILE`, `just frames FILE`; balance: `just _sim 20`
- **APK**: `just build android` (only Android ships for now)

## Rules

- Data holds the numbers; code holds the behaviour. Add content as JSON in `queen/data/`; add a mechanic as a
  registered handler in `queen/mech/`. Read [Structure](docs/repo/structure.md) before you add anything, and
  document new fields and ops in [Content formats](docs/repo/content.md).
- Every name in data must resolve; `tests/test_content.py` checks it.
- Keep game rules free of pyxel: only `queen/render/`, `app.py`, `audio.py`, `frames.py` import it.
- Keep the simulation deterministic: random numbers only from `run.rng[stream]` (rules/rng.py). All input goes
  through `Game.step`, so replays play back exactly.
- Every touch action has a button path too (NightEngine rule).
- The GDD is the source of truth for design; the data is the source of truth for numbers. Change the GDD
  first when the design changes.
- Do not edit `nightengine/` here. Change it in its own repo on main, then move the submodule pointer.
- Run `just check` and `just lint` before you finish. After a visual change, take shots and look at them.
- One-line Conventional Commits.

## Spoke Index

- [GDD](docs/design/GDD.md): the design, with the StS / AHLCG / Snap / Highcard studies and the architecture.
- [Structure](docs/repo/structure.md): where code, data and assets go.
- [Content formats](docs/repo/content.md): every record field, op, hook and condition.
- [Testing](docs/repo/testing.md): unit, touch, autopilot, browser and screenshot checks.
- [Releases](docs/repo/release.md): the tag-driven Android release.
- [Plan 001](docs/exec-plans/active/001-vertical-slice.plan.md): the vertical slice.
- [Art sources](assets/art/README.md): every art file's pack, author and licence.
- [Engine README](nightengine/README.md) and its [Pyxel runtime](nightengine/docs/runtimes/python-pyxel.md).
