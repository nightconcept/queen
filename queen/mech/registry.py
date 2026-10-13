"""One engine Registry for each kind of named behaviour. Data names a handler by string; code registers it here.

GDD 16.3 lists the signatures. Import `queen.mech` (the package) to register every handler.
"""

from nightengine import Registry

OPS = Registry("battle op")  # fn(ctx, src, target, p): card effects and the hunter side of the battle.
INTENT_OPS = Registry("intent op")  # fn(ctx, enemy, p): what an enemy's intent does.
BEHAVIOURS = Registry("behaviour")  # generator fn(e, p) yielding intent ids.
WEAPON_SPECIALS = Registry("weapon special")  # fn(roll, p) -> damage, or None for the normal damage.
HOOKS = Registry("hook")  # fn(ctx, owner, p, ev): status, relic, aura, equipment and hunter hooks.
CONDITIONS = Registry("condition")  # fn(state, p) -> bool, for `if` fields.
STORY = Registry("story op")  # fn(run, p): story, encounter, location, act and agenda effects.

op = OPS.register
intent_op = INTENT_OPS.register
behaviour = BEHAVIOURS.register
special = WEAPON_SPECIALS.register
hook = HOOKS.register
condition = CONDITIONS.register
story_op = STORY.register
