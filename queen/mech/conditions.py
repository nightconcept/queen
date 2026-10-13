"""Conditions for `if` fields: fn(state, p) -> bool. `state` is a Battle (card effects) or a RunState (story)."""

from .registry import condition


@condition("first_card")
def first_card(state, p):
    """Rush and Recon: the card being played is the first this turn."""
    return state.cards_played == 1


@condition("target_has")
def target_has(state, p):
    return state.target is not None and state.target.has(p.status) > 0


@condition("unlocked")
def unlocked(state, p):
    run = getattr(state, "run", state)
    return run.available(p.location)


@condition("log")
def log(state, p):
    run = getattr(state, "run", state)
    return run.log.get(p.key, 0) >= p.get("value", 1)


@condition("not_log")
def not_log(state, p):
    run = getattr(state, "run", state)
    return run.log.get(p.key, 0) < p.get("value", 1)


@condition("entropy_at_least")
def entropy_at_least(state, p):
    run = getattr(state, "run", state)
    return run.total_entropy >= p.n
