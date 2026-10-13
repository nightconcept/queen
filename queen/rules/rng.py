"""Named random streams, so a change in one system never reshuffles another (GDD 16.9).

Each stream is an engine `Rng` seeded from the run seed and the stream name. Its state saves as four ints.
"""

from nightengine.rng import Rng

STREAMS = ("deck", "dice", "ai", "bag", "encounter", "rewards", "map")


class Streams:
    def __init__(self, seed: int, state: dict[str, list[int]] | None = None):
        self.seed = seed
        self._rngs: dict[str, Rng] = {}
        for name in STREAMS:
            rng = Rng(f"{seed}:{name}")
            if state and name in state:
                rng.s = list(state[name])
            self._rngs[name] = rng

    def __getitem__(self, name: str) -> Rng:
        return self._rngs[name]

    def state(self) -> dict[str, list[int]]:
        return {name: list(r.s) for name, r in self._rngs.items()}


def shuffle(rng: Rng, items: list) -> None:
    """Fisher-Yates in place."""
    for i in range(len(items) - 1, 0, -1):
        j = rng.randint(0, i)
        items[i], items[j] = items[j], items[i]


def choice(rng: Rng, items):
    return items[rng.randint(0, len(items) - 1)]


def weighted(rng: Rng, weights: dict[str, int]) -> str:
    total = sum(weights.values())
    r = rng.randint(1, total)
    for k, w in weights.items():
        r -= w
        if r <= 0:
            return k
    return next(iter(weights))
