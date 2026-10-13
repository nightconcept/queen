# Art

Every file here comes from a CC0 (public domain) pack, cut and quantised to the 64-colour palette by
`tools/import_art.py`. Run it again with `just _import-art PACKS_DIR` after you download and unzip the packs
(the script's docstring shows the folder names).

| Files | Pack | Author | Licence | Source |
| --- | --- | --- | --- | --- |
| `sprites/drone`, `brood_egg`, `stalker`, `spitter`, `warden`, `slug`, `queen`; `bg/hive` | Pixel Sci-Fi Monster Animations | OneBitPudding | CC0 | https://opengameart.org/content/pixel-sci-fi-monster-animations |
| `sprites/rook`, `husk`, `boom` | Warped City 2 | ansimuz (Luis Zuno) | CC0 | https://opengameart.org/content/warped-city-2 |
| `bg/lab` | Warped Sci-Fi Lab | ansimuz (Luis Zuno) | CC0 | https://opengameart.org/node/133446 |
| `icons.png` | 1-Bit Pack 1.2 | Kenney | CC0 | https://kenney.nl/assets/1-bit-pack |

Credit is not required by CC0, but the title screen names the artists.

The fonts are in `../fonts/atkinson/`: Atkinson Hyperlegible by the Braille Institute of America, SIL Open Font
License 1.1 (`OFL.txt`), from https://github.com/google/fonts/tree/main/ofl/atkinsonhyperlegible.
`tools/import_font.py` draws the TTFs at exact pixel sizes, with no anti-aliasing, into BDF files: `s` (Regular 17),
`m` (Regular 20), `l` (Bold 20) and `xl` (Bold 30). The BDFs are a converted form of the font, under the same
licence.
