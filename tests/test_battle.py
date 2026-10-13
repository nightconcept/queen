"""The battle rules, headless: dice, weapons, statuses, Guard, ammo, hooks, enemies, and determinism."""

import unittest

import queen.mech  # noqa: F401
from queen.content import Params
from queen.rules.battle import Battle, hit_distribution
from queen.rules.run import new_run


def battle(enemies=("DRONE",), seed=3, cards=None):
    run = new_run(seed)
    if cards is not None:
        run.deck = [c for c in run.deck if c.uid == run.weapon]
        for cid in cards:
            run.add_card(cid)
    return Battle(run, list(enemies))


class Dice(unittest.TestCase):
    def test_distribution_sums_to_one(self):
        for dice, hit, crit, focus in ((4, 5, False, 0), (6, 4, True, 2), (3, 6, True, 5)):
            self.assertAlmostEqual(sum(hit_distribution(dice, hit, crit, 2, focus).values()), 1.0)

    def test_expected_hits(self):
        d = hit_distribution(6, 5, False, 2, 0)
        self.assertAlmostEqual(sum(h * p for h, p in d.items()), 2.0)

    def test_focus_raises_hits(self):
        plain = sum(h * p for h, p in hit_distribution(4, 5, False, 2, 0).items())
        focused = sum(h * p for h, p in hit_distribution(4, 5, False, 2, 2).items())
        self.assertGreater(focused, plain)


class Fire(unittest.TestCase):
    def test_exposed_lowers_the_hit_target(self):
        b = battle()
        foe = b.foes[0]
        _, _, hit = b.fire_pool(foe)
        b.apply(foe, "EXPOSED", 1)
        self.assertEqual(b.fire_pool(foe)[2], hit - 1)

    def test_shaken_removes_dice(self):
        b = battle()
        dice = b.fire_pool(b.foes[0])[1]
        b.apply(b.hero, "SHAKEN", 2)
        self.assertEqual(b.fire_pool(b.foes[0])[1], dice - 2)

    def test_double_special(self):
        b = battle()
        roll = b.fire(b.foes[0], Params())
        self.assertEqual(roll.damage, roll.hits * 2 * 2)  # RTX: 2 per hit, doubled.

    def test_ammo_spends_and_comes_back(self):
        b = battle(cards=["BRACE"] * 8)
        top = b.weapon.card.weapon.durability
        for _ in range(top):
            b.fire(b.foes[0], Params())
            if not b.foes[0].alive:
                b.foes[0].hp = b.foes[0].max_hp = 999
        self.assertIsNone(b.weapon)
        b.finish()
        b2 = Battle(b.run, ["DRONE"])
        self.assertEqual(b2.weapon.durability, top)

    def test_shields_absorb_first(self):
        b = battle()
        b.hero.shields = 5
        b.deal(b.hero, 8)
        self.assertEqual((b.hero.shields, b.hero.hp), (0, b.hero.max_hp - 3))

    def test_ward_prevents(self):
        b = battle()
        b.apply(b.hero, "WARD", 6)
        b.deal(b.hero, 4)
        self.assertEqual(b.hero.hp, b.hero.max_hp)
        self.assertEqual(b.hero.has("WARD"), 2)


class Rules(unittest.TestCase):
    def test_guard_forces_the_target(self):
        b = battle(("DRONE", "HUSK"))
        drone, husk = b.foes
        self.assertFalse(b.targetable(drone))
        self.assertTrue(b.targetable(husk))

    def test_cannot_play_without_energy(self):
        b = battle()
        b.energy = 0
        self.assertFalse(any(b.play(i, 0) for i in range(len(b.hand)) if b.hand[i].card.cost > 0))

    def test_end_turn_discards_and_draws(self):
        b = battle(cards=["FIRE", "BRACE"] * 6)
        n = len(b.draw) + len(b.hand) + len(b.discard)
        b.end_turn()
        self.assertEqual(len(b.hand), 5)
        self.assertEqual(len(b.draw) + len(b.hand) + len(b.discard) + len(b.exhaust), n)

    def test_egg_hatches(self):
        b = battle(("BROOD_EGG",))
        for _ in range(3):
            b.end_turn()
        self.assertEqual([f.rec.id for f in b.living()], ["DRONE"])

    def test_queen_awakens(self):
        b = battle(("QUEEN",))
        q = b.foes[0]
        q.hp = q.max_hp // 2 - 1
        b.foes[0].intent_id = next(q.gen)
        seen = set()
        for _ in range(4):
            seen.add(q.intent_id)
            b.end_turn()
            if b.over:
                break
            b.hero.hp = b.hero.max_hp
        self.assertTrue(q.flags.get("awakened"))

    def test_won_and_lost(self):
        b = battle()
        b.lose_hp(b.foes[0], 99)
        b.check_end()
        self.assertEqual(b.over, "won")
        b = battle()
        b.lose_hp(b.hero, 999)
        b.check_end()
        self.assertEqual(b.over, "lost")

    def test_same_seed_same_battle(self):
        def run(seed):
            b = battle(("DRONE", "SPITTER"), seed)
            for _ in range(60):
                if b.over:
                    break
                if not any(b.play(i, next(j for j, f in enumerate(b.foes) if f.alive)) for i in range(len(b.hand))):
                    b.end_turn()
            return [(e.kind, sorted(e.data.items(), key=str)) for e in b.events]

        self.assertEqual(run(11), run(11))
        self.assertNotEqual(run(11), run(12))

    def test_autoloader_fires_twice(self):
        b = battle(cards=["RXX_AUTOLOADER", "FIRE"] * 3)
        b.equipment = [b.run.new_card("RXX_AUTOLOADER")]
        b.foes[0].hp = b.foes[0].max_hp = 999
        rolls = len([e for e in b.events if e.kind == "roll"])
        b.push([Params(op="fire")], b.hand[0], b.foes[0])
        b.run_queue()
        self.assertEqual(len([e for e in b.events if e.kind == "roll"]) - rolls, 2)


if __name__ == "__main__":
    unittest.main()
