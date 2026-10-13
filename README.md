# Queen

A single-player deckbuilder prototype set in the world of Highcard. Rook, a Kinetic Hunter, boards the
alien hive-ship *Sovereign* to kill its Queen before she wakes.

- **Battles** play like Slay the Spire: 3 energy, 5 cards, visible enemy intents. Damage comes from
  Highcard's d6 dice through your equipped weapon, and you can see the odds before you commit.
- **The run** plays like an Arkham Horror LCG scenario: explore a hive of eight locations, find clues to
  advance the Act, and race the Agenda's entropy clock. Story cards, a chaos bag, and three endings.
- **Phones first**: portrait 320x714 pixels (4x on a Pixel 10 Pro). Drag cards onto enemies, and hold to
  inspect anything.

It runs on [NightEngine](https://github.com/nightconcept/NightEngine) (Pyxel).

## Run

```sh
git clone --recurse-submodules https://github.com/nightconcept/queen.git
cd queen
just setup
just run                     # desktop window (mouse and keys)
just run --target android    # the phone layout, with the mouse as a finger
```

The Android APK is on the [releases page](https://github.com/nightconcept/queen/releases).

## Controls

| Touch | Keys / pad |
| --- | --- |
| Drag a card onto an enemy, or above the line for other cards | Left/Right pick a card, A play (then Left/Right and A for a target) |
| Hold a card or an enemy to inspect it | Up |
| Tap END TURN | C (E or Tab) |
| Tap map locations to move; tap the agenda or act to read it | Arrows and A on the action buttons |

## Develop

See [AGENTS.md](AGENTS.md) for the layout and the rules, and [the GDD](docs/design/GDD.md) for the design.
`just check`, `just lint`, `just dev scene=battle enemies=QUEEN`.

Art: CC0 packs by OneBitPudding, ansimuz and Kenney ([sources](assets/art/README.md)). Font: Pixel Operator by Jayvee Enaguas (CC0).
