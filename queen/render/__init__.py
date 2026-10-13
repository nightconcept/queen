"""RENDERER: one draw function per scene, the palette, and the bake. Imports pyxel."""

from nightengine.host.renderer import Renderer

from ..config import ASSETS
from ..content import CONTENT
from ..scenes.battle import BattleScene
from ..scenes.deck import DeckScene
from ..scenes.explore import Explore
from ..scenes.resolution import Resolution
from ..scenes.rest import Rest
from ..scenes.reward import Reward
from ..scenes.story import StoryScene
from ..scenes.test import TestScene
from ..scenes.title import Title
from . import art, battle, explore, screens

PALETTE = tuple(CONTENT.palette.values())

RENDERER = Renderer(
    {
        Title: screens.title,
        Explore: explore.draw,
        BattleScene: battle.draw,
        StoryScene: screens.story,
        TestScene: screens.test,
        Reward: screens.reward,
        Rest: screens.rest,
        Resolution: screens.resolution,
        DeckScene: screens.deck,
    },
    PALETTE,
    art.bake,
    ASSETS / "fonts" / "pixel-operator" / "m.bdf",
    (CONTENT.colour["bone"], CONTENT.colour["void"]),
)
