"""Sound effects and music as Pyxel note strings (GDD 15.5). No pyxel here: tests check the notes.

SFX is in priority order, highest first: when two cues sound in one frame, the earlier one wins.
"""

from nightengine.sound import ch

SFX = {
    "awaken": ("c1c1d#1c1c1g0", "n", "7", "f", 18),
    "win": ("c3e3g3c4e4g4c4", "s", "6", "n", 7),
    "lose": ("g2f2d#2c2b1c1", "t", "6", "f", 14),
    "entropy": ("c2c#2c2c#2", "p", "5", "v", 16),
    "crit": ("c4g3c4e4", "s", "7", "f", 4),
    "hurt": ("d1c1", "n", "7", "f", 7),
    "die": ("g2d2a1d1", "n", "6", "f", 7),
    "horror": ("c#2g1c#2g1", "t", "6", "v", 12),
    "hit": ("c2a1", "n", "6", "f", 5),
    "block": ("e3c3", "p", "5", "f", 5),
    "miss": ("a2f2", "t", "4", "f", 6),
    "dice": ("c3c3c3c3c3c3", "n", "3", "f", 3),
    "pass": ("c3e3g3c4", "s", "6", "n", 6),
    "fail": ("c3g2d#2c2", "t", "6", "f", 9),
    "bag": ("f2g2f2g2f2", "n", "3", "n", 8),
    "clue": ("e3b3e4", "p", "5", "f", 6),
    "heal": ("c3e3g3", "t", "5", "f", 8),
    "shield": ("g3c4", "p", "5", "f", 5),
    "play": ("c3g3", "s", "5", "f", 3),
    "turn": ("g3c4", "t", "5", "n", 8),
    "end_turn": ("c3g2", "t", "4", "f", 6),
    "pick": ("c4e4", "p", "5", "f", 6),
    "deny": ("c2c2", "s", "4", "f", 5),
    "draw": ("g4", "p", "2", "f", 2),
    "lift": ("c4", "p", "2", "f", 2),
}

_EXPLORE = [
    ch("t", "4", "n", 40, "c1 r r r g0 r r r d#1 r r r c1 r a#0 r"),
    ch("p", "2", "v", 40, "r r g2 r r r d#2 r r r g2 r r f2 r r"),
    ch("n", "1", "f", 40, "c1 r r r r r r r c1 r r r r r r r"),
]
_BATTLE = [
    ch("s", "4", "n", 14, "c2 c2 r c2 d#2 r c2 r c2 c2 r c2 g1 r a#1 r"),
    ch("t", "5", "n", 14, "c1 r c1 r c1 r c1 r d#1 r d#1 r a#0 r a#0 r"),
    ch("n", "5", "f", 14, "c1 r c3 r c1 c1 c3 r c1 r c3 r c1 c1 c3 c3"),
]
_BOSS = [
    ch("s", "5", "v", 12, "c2 r c#2 r c2 r g1 r c2 r c#2 r d#2 r c#2 r"),
    ch("t", "6", "n", 12, "c1 c1 c1 c1 c#1 c#1 c#1 c#1 c1 c1 c1 c1 g0 g0 g0 g0"),
    ch("n", "6", "f", 12, "c1 r c3 c1 c1 r c3 r c1 r c3 c1 c1 c3 c3 c3"),
]
_END = [
    ch("t", "5", "f", 30, "c3 r g2 r d#2 r c2 r g1 r r r r r r r"),
    ch("p", "3", "v", 30, "r r c3 r r r g2 r r r c2 r r r r r"),
]
MUSIC = {"explore": _EXPLORE, "battle": _BATTLE, "boss": _BOSS, "end": _END}
ONCE = ("end",)
