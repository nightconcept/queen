"""Queen: a Highcard deckbuilder prototype on NightEngine (Pyxel).

python game.py                    play
python game.py --seed 7           play with a fixed random seed
python game.py --replay FILE      watch a recorded run
python game.py --target android   play as the phone build: touch only, with the mouse as a finger
python game.py --dev scene=battle start in a state (`just dev`): see queen/scenes/dev.py for the keys
"""

import argparse
import os

from nightengine import Recording
from nightengine.target import ENV, NAMES


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, help="random seed")
    parser.add_argument("--replay", help="recording to play back (see replays/)")
    parser.add_argument("--target", choices=NAMES, help="build target (see [tool.nightengine.targets])")
    parser.add_argument("--dev", action="store_true", help="a dev run: start in the state the pairs give")
    parser.add_argument("pairs", nargs="*", metavar="KEY=VALUE", help="dev state, such as scene=battle")
    args = parser.parse_intermixed_args()
    if args.pairs and not args.dev:
        parser.error("KEY=VALUE pairs need --dev")
    if args.target:
        os.environ[ENV] = args.target
    from queen.app import run_app

    run_app(args.seed, Recording.load(args.replay) if args.replay else None, tuple(args.pairs))


if __name__ == "__main__":
    main()
