# Content formats

The fields of every record in `queen/data/`. [structure.md](structure.md) says where files go. A table is a
JSON object keyed by an UPPER_CASE id; a `_doc` key is a comment. Records load into frozen dataclasses
(`queen/content.py`); an unknown or missing field fails with the record's name.

## Cards (`data/cards/*.json`)

| Field | Meaning |
| --- | --- |
| `name`, `set` | Display name; `INVA` (Highcard Set 001) or `QUEEN`. |
| `face` | Optional shorter name for the card face, when `name` does not fit it (`tests/test_content.py` checks). |
| `element` | `R`, `G`, `K`, `E`, `Z` or null (neutral). Reward pools use the Hunter's element and neutral. |
| `tier` | `B` basic, `S` Standard, `P` Prototype, `X` Prime, `W` weakness, `T` trauma. |
| `type` | `action`, `weapon`, `equipment`, `aura`, `trauma`, `spore`. |
| `cost` | Energy. `cost_mods`: `[{"if": condition, "delta": -1}]`. |
| `target` | `enemy` (drag onto an enemy) or `none` (drag above the play line). |
| `text` | The full rules text (inspect view). Hand faces are generated from the ops (`ui/cardtext.py`). |
| `effects` | Ops, in order: `{"op": name, ...params, "if": condition}`. |
| `keywords` | `exhaust`, `retain`, `ethereal`, `innate`, `unplayable`. |
| `weapon` | `dice`, `hit`, `damage` (per hit), `crit`, `durability` (ammo per battle), `special`, `params`. |
| `hooks`, `params` | Hook event to handler, and the handler's numbers (auras, equipment, traumas). `<event>_in_hand` listens while in hand. |
| `uses` | Equipment uses. |
| `plus` | The upgrade: any of `text`, `cost`, `effects`, `weapon`, `hooks`, `params`, `keywords`, `cost_mods`, `uses`. |
| `upgrades_to` | The next tier's card id (XP tier path). |
| `pool`, `signature`, `weakness`, `icons`, `art`, `subtype` | Reward pool; flags; skill icons (`willpower`, `intellect`, `combat`, `agility`, `wild`); icon name; Highcard subtype. |

### Card ops (`mech/ops.py`)

| Op | Params |
| --- | --- |
| `fire` | `dice` (bonus), `zero_as` (hits when 0), `at: "random"` |
| `last_round` | — (2 extra dice per ammo, then spent) |
| `execute` | `below` (a health fraction) |
| `shield` / `draw` / `energy` / `lose_hp` / `repair` / `clue` | `n` |
| `apply` | `status`, `n`, `to` (`target`, `self`, `all_enemies`) |

## Statuses (`data/statuses.json`)

`name`, `colour` (palette name), `decay` (`turn`: -1 at the end of its owner's turn; `battle`; `none`), `good`,
`text` (`{n}` is the stacks), `hooks`.

## Relics (`data/relics.json`)

`name`, `icon`, `pool` (`start`, `elite`, `story`), `text`, `hooks`, `params`.

## Hooks (`mech/hooks.py`)

Events: `battle_start`, `battle_end`, `turn_start`, `turn_end`, `draw_count`, `fire_dice`, `hit_target`,
`crit_hits`, `damage_per_hit`, `damage_per_hit_taken`, `attack_mult`, `shield_gain`, `damage_taken`, `crit`,
`after_fire`, `clue_gain`, `drawn` (battle); `mythos_entropy`, `test_bonus` (exploration).

## Enemies (`data/enemies.json`, `data/scenarios/<id>/enemies.json`)

| Field | Meaning |
| --- | --- |
| `name`, `hp` (`[min, max]`), `art` (a sprite), `scale` (on top of the 2x battle scale) | |
| `behaviour`, `params` | A generator in `mech/behaviours.py` and its numbers (`order`, `weights`, `max_repeat`, ...). |
| `intents` | `{ID: {"kind": attack/horror/defend/buff/debuff/summon/hatch/unknown, "effects": [intent ops]}}` |
| `statuses` | Statuses at the start of a battle. |
| `elite`, `boss`, `hunter` | Elite rewards; the boss battle; moves toward Rook each Mythos. |
| `evade`, `vp`, `clues` | Evade difficulty; XP at the resolution; clues dropped on death. |

Intent ops (`mech/intents.py`): `attack` (`damage`, `times`), `horror` (`n`), `shield`, `shield_all` (`n`),
`apply` (`status`, `n`, `to`), `rally` (`status`, `n`), `add_cards` (`card`, `n`), `summon` (`enemy`),
`gestate`, `devour` (`heal`), `awaken`.

## Hunters (`data/hunters.json`)

`name`, `title`, `element`, `art`, `health`, `nerve`, `skills`, `deck` (`[[card, count], ...]`), `weapon`,
`relics`, `hooks`, `elder_sign` (`bonus`, `effects`), `blurb`.

## Rules (`data/rules.json`)

`energy`, `draw`, `hand_limit`, `shield_decay`, `entropy_every_rounds`, `actions_per_round`, `rest_heal`
(fraction), `rest_nerve`, `bare_hands`, `reward_choices`, `tier_weights`, `prime_pity`, `scrip`, `xp_costs`,
`test_hand`, `difficulty`.

## Hive Bag (`data/hive_bag.json`)

`tokens` defines each token (`value`, `symbol`, `auto_fail`, `elder`). `EASY`, `STANDARD`, `HARD`, `EXPERT`
give the counts.

## Scenario (`data/scenarios/<id>/`)

- `scenario.json`: `name`, `subtitle`, `intro` (lines), `start`, `symbols` (Brood, Choir, Crown: `value`,
  `if_enemies`, `fail` ops), `acts` and `agendas` (`id`, `name`, `clues` or `entropy`, `front`, `back`,
  `effects`), `resolutions` (`name`, `outcome`, `xp`, `next_entropy`, `text`, `log`, `trauma`).
- `locations.json`: `name`, `art` and `art_xy` (a background crop), `pos`, `shroud`, `clues`, `links`,
  `revealed`, `locked`, `locked_text`, `text`, `on_reveal`, `on_enter` (story ops), `actions`
  (`id`, `label`, `rest`, `once`, `test`, `success`, `fail`, `story`, `effects`).
- `story.json`: `kind` (`story`, `treachery`, `enemy`, `boon`, `agenda`), `title`, `text` (paragraphs), `art`,
  `art_xy`, `choices` (`label`, `if`, `effects`, or `test` + `success` + `fail`).
- `encounter.json`: `deck`: `[[story id, count], ...]`.

### Story ops (`mech/story.py`)

`story` (`id`), `say` (`text`), `spawn` (`enemies`, `location`: id, `far`, or here), `boss` (`enemies`),
`test` (`skill`, `difficulty`, `title`, `success`, `fail`), `horror`, `damage`, `heal`, `clue`, `entropy`,
`xp`, `scrip` (`n`), `log` (`key`, `value`), `add_card` (`card`), `relic` (`id`), `unlock` (`location`),
`bag_add` / `bag_remove` (`token`), `hive_buff` (`hp`), `mythos_draws` (`n`), `next_battle` (`spores`,
`energy`, `shields`), `opening_draw` (`n`), `awaken_queen`, `goto` (`location`), `resolve` (`id`),
`take_clue`, `evade`, `fight`.

### Conditions (`mech/conditions.py`)

`{"cond": name, ...}`: `first_card`, `target_has` (`status`), `unlocked` (`location`), `log` / `not_log`
(`key`, `value`), `entropy_at_least` (`n`).

## Art (`data/art.json`, `data/palette.json`)

Written by `tools/import_art.py`: sprite strips (`w`, `h`, `anims`: `{name: [first, count]}`), the icon
names, the backgrounds, and the 64 named colours (index 0 is the transparent key).
