"""A balance sample: the autopilot plays N seeds by touch and prints the outcomes. `just _sim 20`."""

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from queen import autopilot  # noqa: E402


def main(n: int):
    outcomes = collections.Counter()
    for seed in range(1, n + 1):
        _, game = autopilot.play(seed, limit=300_000)
        log = game.campaign
        key = next((k for k in ("queen_slain", "queen_awake", "rook_lost") if k in log), "unfinished")
        outcomes[key] += 1
        print(f"seed {seed:3}: {key:10} frame {game.frame}")
    print(dict(outcomes))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
