"""Touch in battle: drag a card onto an enemy plays it; drag it back cancels; hold inspects."""

import unittest

from nightengine import dev_event
from queen import autopilot
from queen.ui import layout


def start(seed=3):
    game = autopilot.make(seed)
    game.step(0, (), (dev_event("scene=battle"), dev_event("enemies=DRONE")))
    for _ in range(400):
        game.step(0)
    return game


def run(game, frames):
    for code, ptrs in frames:
        game.step(code, ptrs)
    for _ in range(200):
        game.step(0)


class Touch(unittest.TestCase):
    def test_drag_fire_onto_enemy(self):
        game = start()
        scene = game.scene
        b = scene.battle
        i = next(i for i, c in enumerate(b.hand) if c.id == "FIRE" or c.card.target == "enemy")
        s = scene.slots[b.hand[i].uid]
        x, y = scene.fighter_xy(b.foes[0].uid)
        n = len(b.hand)
        run(game, autopilot.drag(s.x, s.y, x, y))
        self.assertEqual(len(b.hand), n - 1)
        self.assertTrue(any(e.kind == "roll" for e in b.events))

    def test_drop_back_in_hand_cancels(self):
        game = start()
        scene = game.scene
        b = scene.battle
        s = scene.slots[b.hand[0].uid]
        n = len(b.hand)
        run(game, autopilot.drag(s.x, s.y, s.x + 4, layout.PLAY_LINE + 60))
        self.assertEqual(len(b.hand), n)

    def test_end_turn_button(self):
        game = start()
        b = game.scene.battle
        run(game, autopilot.tap(*autopilot.centre(layout.END_TURN)))
        self.assertEqual(b.turn, 2)


class Layout(unittest.TestCase):
    def test_any_number_of_enemies_fits(self):
        """Four living enemies and one still dying is five on the line (the boss's adds crashed at 3+)."""
        for n in range(1, 8):
            xs = [layout.foe_x(i, n) for i in range(n)]
            self.assertEqual(xs, sorted(set(xs)))
            self.assertTrue(all(0 < x < layout.W for x in xs), xs)

    def test_hand_fits_the_screen(self):
        for n in range(1, 11):
            for s in layout.hand_slots(n):
                self.assertGreaterEqual(s.x - layout.CARD_W / 2, 0)
                self.assertLessEqual(s.x + layout.CARD_W / 2, layout.W)
                self.assertLessEqual(s.y + layout.CARD_H / 2, layout.H - layout.SAFE_BOTTOM)


if __name__ == "__main__":
    unittest.main()
