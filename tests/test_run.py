"""Whole runs by the autopilot, by touch: they reach a resolution, and a replay plays back the same."""

import unittest

from nightengine.replay import play
from queen import autopilot


class Run(unittest.TestCase):
    def test_runs_reach_a_resolution_and_replay(self):
        for seed in (4, 8):
            recording, game = autopilot.play(seed, limit=60_000)
            self.assertGreater(game.campaign.get("runs", 0), 0, f"seed {seed} did not finish")
            again = play(autopilot.make, recording)
            self.assertEqual(again.campaign, game.campaign)
            self.assertEqual(again.frame, game.frame)


if __name__ == "__main__":
    unittest.main()
