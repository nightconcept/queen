"""The run's step queue: what happens next, in order (GDD 8).

A step is a plain dict, so a run saves with its queue. Interactive steps open a screen: `story`, `test`, `battle`,
`engage`, `rest`, `reward`, `resolve`. Other steps run in the rules at once: `effects`, `mythos`, `agenda`.
Story ops and exploration actions push steps; the explore scene takes them off the front.
"""

from .run import RunState

INTERACTIVE = ("story", "test", "battle", "engage", "rest", "reward", "resolve", "say")


def pending(run: RunState) -> list[dict]:
    return run.steps


def push(run: RunState, step: dict, front: bool = False):
    steps = pending(run)
    if front:
        steps.insert(0, step)
    else:
        steps.append(step)


def push_effects(run: RunState, effects, front: bool = False):
    if effects:
        push(run, {"kind": "effects", "effects": [dict(e) for e in effects]}, front)


def say(run: RunState, text: str, title: str = "", kind: str = "story"):
    push(run, {"kind": "say", "title": title, "text": [text], "frame": kind})


def add_entropy(run: RunState, n: int):
    """Entropy on the current agenda. A full agenda flips (queued, so the current step finishes first)."""
    if n <= 0 or run.agenda >= len(run.scenario.agendas):
        return
    run.entropy += n
    run.total_entropy += n
    push(run, {"kind": "agenda"}, front=True)
