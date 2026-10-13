# Where everything goes

The GDD says **what** the game is. This file says **where** each part lives. Read it before you add content
or a module. The pattern follows Nightrunner: data holds the numbers and the composition, code holds the
behaviour (GDD 16).

## The rules

1. **Data holds the numbers. Code holds the behaviour.** A card, enemy, location or story card is a JSON
   record. What it does is a list of named ops; each op is a small registered Python function.
2. **Every name in data is checked.** `tests/test_content.py` resolves every op, hook, behaviour, special,
   condition, status, enemy, story, location, card and art name. A typo fails with one line that names it.
3. **Handlers get a narrow handle.** Battle ops get the Battle (`ctx`), behaviours get a `Handle`, story ops
   get the RunState. None of them gets a scene, the renderer or pyxel.
4. **Game rules never import pyxel.** Only `render/`, `app.py`, `audio.py` and `frames.py` do.
   `tests/test_layers.py` checks it.
5. **Rules emit events; scenes animate them.** A battle resolves a command at once and leaves events with
   snapshots. The scene plays them back with timings. Rules never wait.
6. **Shared first, then per scenario.** Content that only one scenario uses lives in
   `data/scenarios/<id>/` (and `queen/scenarios/<id>.py` for scenario-only handlers, when there are any).

## The tree

```
game.py                 Entry point: `uv run game.py` (just run / just dev).
queen/
  config.py             Screen size (540x1170), safe areas, paths. No tuning numbers.
  content.py            Loads data/ into frozen records (Card, Enemy, Location, Story, ...). CONTENT.
  game.py               QueenGame: the scene stack, the campaign log, the run, saving, host events.
  mech/                 Mechanics as code: every handler that data names.
    registry.py         OPS, INTENT_OPS, BEHAVIOURS, WEAPON_SPECIALS, HOOKS, CONDITIONS, STORY.
    ops.py              Card ops: fire, shield, draw, apply, energy, repair, clue, execute, last_round.
    intents.py          Enemy intent ops: attack, horror, shield, apply, summon, gestate, devour, awaken.
    behaviours.py       Enemy move pickers: cycle, weighted, hatch, stalker, queen.
    weapons.py          Weapon specials: double, flat_on_hit, exact_six, dreamscape.
    hooks.py            Status, relic, aura, equipment and Hunter hooks.
    conditions.py       `if` conditions: first_card, target_has, unlocked, log, entropy_at_least.
    story.py            Story ops: spawn, test, clue, entropy, horror, unlock, story, resolve, ...
  rules/                The game, pure and deterministic.
    run.py              RunState and CardInst: everything a run saves.
    battle.py           The battle engine: piles, energy, the queue, Fire, hooks, events, fire_preview.
    explore.py          Actions, Mythos, act and agenda flips, engagement, rewards and resolutions.
    flow.py             The run's step queue.
    skilltest.py        The Hive Bag and committing cards.
    rewards.py          Card and relic rewards, XP upgrades.
    rng.py              Named random streams (deck, dice, ai, bag, encounter, rewards, map).
  scenes/               One Scene per screen (no pyxel): title, explore, story, test, battle, reward,
                        rest, resolution, deck, dev (the `just dev` keys), base (Menu, Button, QScene).
  ui/                   Pure geometry and text shared by scenes and render: layout (and font widths),
                        gesture, cardtext (card faces), intenttext (enemy moves in words).
  render/               Everything that draws (pyxel): art, cards, hud, battle, explore, screens.
  sound/tables.py       SFX and MUSIC as note strings (no pyxel). audio.py builds the AudioManager.
  app.py                The host App: keys, pads, touch, saves, recording.
  autopilot.py          Plays whole runs by touch for tests and recordings.
  frames.py             Renders a recording to PNGs.
  data/                 The numbers. See content.md for every field.
assets/                 Fonts and imported art (assets/art/README.md lists sources and licences).
tools/                  import_art.py (art packs to assets), import_font.py (Atkinson Hyperlegible TTFs to BDF),
                        shots.py (headless screenshots from a script), sim.py (autopilot balance sample).
.claude/skills/release/ The repo's release skill: bump, tag, push, and keep one release on GitHub.
tests/                  unittest: layers, content, battle, explore, touch, run. tests/browser: Playwright.
android/                The APK icon and the committed debug keystore.
docs/design/GDD.md      The game design. docs/exec-plans/: plans for coding sessions.
```

## Where a change goes

| I want to... | Change |
| --- | --- |
| Add a card that uses existing ops | A record in `data/cards/<set>.json`. Nothing else. |
| Add a card that needs a new effect | An `@op` in `mech/ops.py`, a row in content.md, then the record. |
| Add a gun | A record in `data/cards/` (`arsenal.json` for Queen's own). Equip effects are its `effects` (ops). |
| Add a gun with a new rule | A `@special` in `mech/weapons.py` (changes its rolls), a new op (an Equip effect), or a hook (reacts while equipped), and the record. |
| Add a status | A record in `data/statuses.json` and its `@hook`s in `mech/hooks.py`. |
| Add a relic | A record in `data/relics.json`; a new `@hook` only if no existing one fits. |
| Add an enemy | A record in `data/enemies.json` (or the scenario's), a behaviour if `cycle`/`weighted` will not do, and a sprite in `tools/import_art.py`. |
| Change a location, story, act or agenda | `data/scenarios/<id>/*.json`. |
| Add a scenario | A folder in `data/scenarios/`, then point `config.SCENARIO` at it (a campaign list comes later). |
| Add a Hunter | A record in `data/hunters.json` and its element's cards. Reward pools filter by element. |
| Change a rule number (energy, draw, rest heal, reward weights, XP prices) | `data/rules.json`. |
| Change the bag | `data/hive_bag.json`; scenario symbols in `scenario.json`. |
| Change how a screen looks | `render/<screen>.py`; geometry in `ui/layout.py` (shared with touch hit tests). |
| Change a sound | `sound/tables.py`. `tests/test_content.py` checks the notes. |
