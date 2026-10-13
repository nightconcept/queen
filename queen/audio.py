"""Builds the engine's AudioManager from sound/tables.py. Imports pyxel (through the engine host)."""

from nightengine.host.audio import AudioManager

from .sound.tables import MUSIC, ONCE, SFX

AUDIO = AudioManager(SFX, MUSIC, once=ONCE, sfx_channel=3, priority=True)
