"""Mechanics as code: every named handler that data refers to. Importing this package registers them all."""

from . import behaviours, conditions, hooks, intents, ops, story, weapons  # noqa: F401
from .registry import BEHAVIOURS, CONDITIONS, HOOKS, INTENT_OPS, OPS, STORY, WEAPON_SPECIALS  # noqa: F401
