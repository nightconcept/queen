"""Exploration, headless: actions, Mythos, flips, tests, saving."""

import json
import unittest

import queen.mech  # noqa: F401
from queen.content import CONTENT
from queen.rules import explore, flow, skilltest
from queen.rules.run import RunState, new_run


def idle(run):
    """Close every interactive step with its first choice, until the run is idle."""
    for _ in range(100):
        step = explore.advance(run)
        if step is None:
            return
        kind = step["kind"]
        if kind in ("story", "engage"):
            explore.choose(run, step, explore.story_choices(run, step)[0]["index"])
        elif kind == "test":
            explore.test_done(run, step, skilltest.resolve(run, step["skill"], step["difficulty"], []))
        else:
            explore.step_done(run, step)


class Explore(unittest.TestCase):
    def test_new_run(self):
        run = new_run(1)
        h = CONTENT.hunter
        self.assertEqual(len(run.deck), sum(n for _, n in h.deck) + 1)
        self.assertEqual(run.location, CONTENT.scenario.start)
        self.assertEqual(len(run.encounter), sum(n for _, n in CONTENT.scenario.encounter))

    def test_three_actions_then_mythos(self):
        run = new_run(1)
        idle(run)
        start = run.total_entropy
        for _ in range(3):
            run.locs[run.location].clues = 1
            explore.act(run, {"kind": "investigate"})
            idle(run)
        self.assertEqual(run.round, 2)
        self.assertGreaterEqual(run.total_entropy, start)  # The Beacon may hold the first one back.

    def test_agenda_flips(self):
        run = new_run(1)
        idle(run)
        run.entropy = CONTENT.scenario.agendas[0].entropy
        flow.push(run, {"kind": "agenda"})
        idle(run)
        self.assertEqual(run.agenda, 1)
        self.assertEqual(run.hive_hp, 2)

    def test_act_advances_and_unlocks(self):
        run = new_run(1)
        idle(run)
        run.clues = CONTENT.scenario.acts[0].clues
        self.assertIn("advance", [a["kind"] for a in explore.actions(run)])
        explore.act(run, {"kind": "advance"})
        idle(run)
        self.assertEqual(run.act, 1)
        self.assertTrue(run.available("THRONE_APPROACH"))

    def test_chance_counts_the_bag(self):
        run = new_run(1)
        run.bag = ["0", "-1", "FAIL", "+1"]
        run.skills["intellect"] = 3
        self.assertAlmostEqual(skilltest.chance(run, "intellect", 3, []), 0.5)

    def test_save_round_trip(self):
        run = new_run(5)
        idle(run)
        text = json.dumps(run.to_json())
        back = RunState.from_json(json.loads(text))
        self.assertEqual(back.to_json(), run.to_json())
        self.assertEqual(back.rng["dice"].next(), run.rng["dice"].next())

    def test_hunters_move_toward_rook(self):
        run = new_run(1)
        run.locs["ECHO_ARCHIVE"].enemies = ["STALKER"]
        run.location = "BREACH_POINT"
        explore.move_hunters(run)
        self.assertEqual(run.locs["SPORE_GALLERY"].enemies, ["STALKER"])


if __name__ == "__main__":
    unittest.main()
