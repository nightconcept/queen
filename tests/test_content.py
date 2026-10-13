"""Every name in data points at something that exists: ops, handlers, statuses, enemies, stories, art, sounds."""

import unittest

import queen.mech  # noqa: F401
from nightengine.sound import MAX_SOUNDS, note_errors, slots_used
from queen.content import CONTENT, Params
from queen.mech.registry import BEHAVIOURS, CONDITIONS, HOOKS, INTENT_OPS, OPS, STORY, WEAPON_SPECIALS
from queen.sound.tables import MUSIC, SFX
from queen.ui.cardtext import FACE_RULES, face_name, face_rules, fits
from queen.ui.intenttext import intent_lines


def walk_effects(effects):
    """Every op in a list of effects, including the ones nested in tests (success, fail)."""
    for e in effects or ():
        yield e
        for key in ("success", "fail", "effects"):
            if key in e:
                yield from walk_effects(e[key])


def conditions(effects):
    for e in walk_effects(effects):
        if e.get("if") is not None:
            yield e["if"]


class Content(unittest.TestCase):
    def setUp(self):
        self.problems: list[str] = []

    def tearDown(self):
        self.assertEqual(self.problems, [], "\n".join(self.problems))

    def need(self, ok, msg):
        if not ok:
            self.problems.append(msg)

    def test_cards(self):
        icons = set(CONTENT.art["icons"]["names"])
        for cid, card in CONTENT.cards.items():
            for c in (card, card.upgraded()):
                self.need(c.text, f"card {cid} has no text")
                for e in c.effects:
                    self.need(e.op in OPS, f"card {cid}: unknown op {e.op!r}")
                    if e.op == "apply":
                        self.need(e.status in CONTENT.statuses, f"card {cid}: unknown status {e.status!r}")
                for cond in conditions(c.effects):
                    self.need(cond.cond in CONDITIONS, f"card {cid}: unknown condition {cond.cond!r}")
                for m in c.cost_mods:
                    self.need(m["if"].cond in CONDITIONS, f"card {cid}: unknown cost condition")
                for h in c.hooks.values():
                    self.need(h in HOOKS, f"card {cid}: unknown hook {h!r}")
                if c.weapon and c.weapon.special:
                    self.need(c.weapon.special in WEAPON_SPECIALS, f"card {cid}: unknown special {c.weapon.special!r}")
                self.need(c.type != "weapon" or c.weapon, f"card {cid} is a weapon with no weapon stats")
            self.need(card.art in icons, f"card {cid}: unknown art icon {card.art!r}")
            if card.upgrades_to:
                self.need(card.upgrades_to in CONTENT.cards, f"card {cid}: upgrades to unknown {card.upgrades_to!r}")

    def test_card_faces_fit(self):
        """Every card face reads in the body fonts: no word cut in the name, no rules line lost (GDD 14.2)."""
        for cid, card in CONTENT.cards.items():
            for c in (card, card.upgraded()):
                font, lines = face_name(c)
                name = c.face or c.name.removesuffix("+")
                self.need(fits(name.split(), font) and len(lines) <= 3, f"card {cid}: name does not fit; add `face`")
                rules = face_rules(c)
                self.need(len(rules) <= FACE_RULES and fits(rules, "m"), f"card {cid}: face lines {rules} do not fit")

    def test_intents_have_text(self):
        for eid, e in CONTENT.enemies.items():
            for iid, intent in e.intents.items():
                title, lines = intent_lines(iid, intent, None)
                self.need(lines and all(lines), f"enemy {eid} intent {iid}: no description")

    def test_enemies(self):
        sprites = CONTENT.art["sprites"]
        for eid, e in CONTENT.enemies.items():
            self.need(e.behaviour in BEHAVIOURS, f"enemy {eid}: unknown behaviour {e.behaviour!r}")
            self.need(e.art in sprites, f"enemy {eid}: unknown art {e.art!r}")
            for sid in e.statuses:
                self.need(sid in CONTENT.statuses, f"enemy {eid}: unknown status {sid!r}")
            for iid, intent in e.intents.items():
                for op in intent.effects:
                    self.need(op.op in INTENT_OPS, f"enemy {eid} intent {iid}: unknown op {op.op!r}")
                    if op.op in ("summon",):
                        self.need(op.enemy in CONTENT.enemies, f"enemy {eid}: summons unknown {op.enemy!r}")
            names = list(e.params.get("order", ())) + list(e.params.get("weights", {}))
            names += list(e.params.get("dreaming", ())) + list(e.params.get("awakened", ()))
            for n in names:
                self.need(n in e.intents, f"enemy {eid}: behaviour names unknown intent {n!r}")
            if "into" in e.params:
                self.need(e.params.into in CONTENT.enemies, f"enemy {eid}: hatches into unknown {e.params.into!r}")

    def test_hooks(self):
        for sid, st in CONTENT.statuses.items():
            for h in st.hooks.values():
                self.need(h in HOOKS, f"status {sid}: unknown hook {h!r}")
        for rid, r in CONTENT.relics.items():
            for h in r.hooks.values():
                self.need(h in HOOKS, f"relic {rid}: unknown hook {h!r}")
        for h in CONTENT.hunter.hooks.values():
            self.need(h in HOOKS, f"hunter: unknown hook {h!r}")
        for cid, _ in CONTENT.hunter.deck:
            self.need(cid in CONTENT.cards, f"hunter deck: unknown card {cid!r}")

    def check_story_ops(self, where, effects):
        s = CONTENT.scenario
        for e in walk_effects(effects):
            if "op" not in e:
                continue
            self.need(e["op"] in STORY, f"{where}: unknown story op {e['op']!r}")
            for eid in e.get("enemies", ()):
                self.need(eid in CONTENT.enemies, f"{where}: unknown enemy {eid!r}")
            if e["op"] == "story":
                self.need(e["id"] in s.stories, f"{where}: unknown story {e['id']!r}")
            if e["op"] in ("unlock", "goto") or (e["op"] == "spawn" and e.get("location") not in (None, "far")):
                self.need(e["location"] in s.locations, f"{where}: unknown location {e['location']!r}")
            if e["op"] in ("add_card",):
                self.need(e["card"] in CONTENT.cards, f"{where}: unknown card {e['card']!r}")
            if e["op"] == "resolve":
                self.need(e["id"] in s.resolutions, f"{where}: unknown resolution {e['id']!r}")
        for cond in conditions(effects):
            self.need(cond.cond in CONDITIONS, f"{where}: unknown condition {cond.cond!r}")

    def test_scenario(self):
        s = CONTENT.scenario
        self.need(s.start in s.locations, "scenario start is not a location")
        for lid, loc in s.locations.items():
            for other in loc.links:
                self.need(other in s.locations, f"location {lid}: unknown link {other!r}")
                self.need(lid in s.locations[other].links, f"location {lid}: link to {other} is one-way")
            self.check_story_ops(f"location {lid} on_reveal", loc.on_reveal)
            self.check_story_ops(f"location {lid} on_enter", loc.on_enter)
            for a in loc.actions:
                self.check_story_ops(f"location {lid} action", [a])
                if a.get("story"):
                    self.need(a.story in s.stories, f"location {lid}: unknown story {a.story!r}")
        for sid, st in s.stories.items():
            self.need(st.choices, f"story {sid} has no choices")
            for c in st.choices:
                self.check_story_ops(f"story {sid}", [c])
        for sid, _ in s.encounter:
            self.need(sid in s.stories, f"encounter: unknown story {sid!r}")
        for deck in (s.acts, s.agendas):
            for card in deck:
                self.check_story_ops(f"act/agenda {card.name}", card.effects)
        for token in s.symbols:
            self.need(token in CONTENT.bag.tokens, f"symbol {token} is not a bag token")
            self.check_story_ops(f"symbol {token}", s.symbols[token].get("fail", ()))

    def test_bag(self):
        for diff in ("EASY", "STANDARD", "HARD", "EXPERT"):
            for token in CONTENT.bag[diff]:
                self.need(token in CONTENT.bag.tokens, f"bag {diff}: unknown token {token!r}")
        self.need(CONTENT.rules.difficulty in CONTENT.bag, "rules.difficulty names no bag")

    def test_sound(self):
        self.problems += note_errors(SFX, MUSIC)
        self.need(slots_used(SFX, MUSIC) <= MAX_SOUNDS, "too many sound slots")

    def test_params_are_frozen(self):
        p = Params({"a": [1, {"b": 2}]})
        self.assertEqual(p.a[1].b, 2)
        with self.assertRaises(AttributeError):
            p.a = 3


if __name__ == "__main__":
    unittest.main()
