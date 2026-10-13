"""One battle (GDD 10): StS turns, Highcard dice through the equipped weapon, intents, statuses, and hooks.

Commands go in (`play`, `end_turn`); events come out (`events`). Each event carries a snapshot of what the screen
should show after it, so the scene animates the events one by one while the rules have already finished.

Every effect runs through one queue (`push`, `run_queue`): a card's ops, an intent's ops, and the ops that hooks add.
The queue keeps the order of resolution clear and stops handlers from running inside each other.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from ..content import CONTENT, Enemy, Intent, Params, Weapon
from ..mech.registry import BEHAVIOURS, CONDITIONS, HOOKS, INTENT_OPS, OPS, WEAPON_SPECIALS
from .rng import choice, shuffle
from .run import CardInst, RunState

MAX_FOES = 4


@dataclass
class Fighter:
    name: str
    hp: int
    max_hp: int
    shields: int = 0
    statuses: dict[str, int] = field(default_factory=dict)

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def has(self, status: str) -> int:
        return self.statuses.get(status, 0)


@dataclass
class Hero(Fighter):
    nerve: int = 0
    max_nerve: int = 0


@dataclass
class Foe(Fighter):
    uid: int = 0
    rec: Enemy | None = None
    intent_id: str | None = None
    flags: dict[str, Any] = field(default_factory=dict)
    gen: Any = None

    @property
    def intent(self) -> Intent | None:
        return self.rec.intents[self.intent_id] if self.intent_id else None


@dataclass
class Event:
    kind: str
    data: dict
    snap: dict


@dataclass
class Roll:
    """One Fire's dice. Weapon specials read and change it."""

    faces: list[int]
    hit: int
    crit: bool
    hits: int
    crits: int
    per_hit: int
    damage: int
    rerolled: list[tuple[int, int, int]] = field(default_factory=list)  # (die index, old face, new face)
    preview: bool = False  # A what-if roll for the drag preview: specials change the damage only, nothing else.


class Handle:
    """What a behaviour generator sees of its enemy and the battle."""

    def __init__(self, battle: "Battle", foe: Foe):
        self.battle, self.foe = battle, foe
        self.rng = battle.rng_ai

    @property
    def hp_ratio(self) -> float:
        return self.foe.hp / self.foe.max_hp

    @property
    def hero_shields(self) -> int:
        return self.battle.hero.shields

    def allies(self, enemy_id: str | None = None) -> list[Foe]:
        return [f for f in self.battle.living() if f is not self.foe and (enemy_id is None or f.rec.id == enemy_id)]


class Battle:
    def __init__(self, run: RunState, enemy_ids: list[str], boss: bool = False):
        self.run = run
        self.rules = CONTENT.rules
        self.rng_deck, self.rng_dice, self.rng_ai = run.rng["deck"], run.rng["dice"], run.rng["ai"]
        self.boss = boss
        h = CONTENT.hunter
        self.hunter = h
        self.hero = Hero(h.name, run.hp, run.max_hp, nerve=run.nerve, max_nerve=run.max_nerve)
        self.combat = run.skills["combat"]
        self.foes: list[Foe] = []
        self.next_foe = 1
        self.events: list[Event] = []
        self.queue: deque = deque()
        self.turn = 0
        self.round = 0
        self.energy = 0
        self.cards_played = 0  # This turn.
        self.fires = 0  # This turn.
        self.target: Foe | None = None  # The target of the card being played (conditions read it).
        self.over: str | None = None  # "won" or "lost".
        self.clues = 0
        self.entropy = 0  # Entropy that the battle added (every N rounds).
        self.hand: list[CardInst] = []
        self.discard: list[CardInst] = []
        self.exhaust: list[CardInst] = []
        self.auras: list[CardInst] = []
        self.spent: list[int] = []  # Weapon uids out of ammo: exhausted for the rest of this battle.
        self.destroyed: list[int] = []  # Equipment uids used up.
        for inst in run.deck:  # Durability is ammo: it refills at the start of each battle (GDD 10.3).
            if inst.card.weapon:
                inst.durability = inst.card.weapon.durability
        self.weapon: CardInst | None = run.weapon_inst
        self.equipment: list[CardInst] = [c for c in (run.find(u) for u in run.equipment) if c]
        in_play = {c.uid for c in [self.weapon, *self.equipment] if c}
        self.draw = [c for c in run.deck if c.uid not in in_play]
        mods = dict(run.next_battle)
        run.next_battle = {}
        for _ in range(mods.get("spores", 0)):
            self.draw.append(run.new_card("SPORE", temp=True))
        shuffle(self.rng_deck, self.draw)
        fatigued = set(run.fatigued)
        run.fatigued = []
        self.discard = [c for c in self.draw if c.uid in fatigued]
        self.draw = [c for c in self.draw if c.uid not in fatigued]
        innate = [c for c in self.draw if c.card.has("innate")]
        self.draw = [c for c in self.draw if c not in innate] + innate  # The top of the pile is the end.
        self.first_energy = mods.get("energy", 0)
        self.extra_draw = run.opening_draw
        run.opening_draw = 0
        for eid in enemy_ids:
            self.add_foe(eid)
        if run.queen_awake:
            for f in self.foes:
                if f.rec.id == "QUEEN":
                    f.flags["awakened"] = True
                    f.max_hp += 40
                    f.hp += 40
        self.hero.shields = mods.get("shields", 0)
        self.emit("start")
        self.hook("battle_start", {})
        self.run_queue()
        for f in self.foes:
            self.roll_intent(f)
        self.start_turn()

    # --- Setup and helpers

    def add_foe(self, eid: str, slot: int | None = None) -> Foe | None:
        if len(self.living()) >= MAX_FOES:
            return None
        rec = CONTENT.enemies[eid]
        lo, hi = rec.hp
        hp = self.rng_ai.randint(lo, hi) + self.run.hive_hp
        foe = Foe(rec.name, hp, hp, uid=self.next_foe, rec=rec, statuses=dict(rec.statuses))
        self.next_foe += 1
        foe.gen = BEHAVIOURS[rec.behaviour](Handle(self, foe), rec.params)
        if slot is None:
            self.foes.append(foe)
        else:
            self.foes.insert(slot, foe)
        return foe

    def living(self) -> list[Foe]:
        return [f for f in self.foes if f.alive]

    def roll_intent(self, foe: Foe):
        if foe.alive:
            foe.intent_id = next(foe.gen)

    def weapon_stats(self) -> Weapon:
        if self.weapon:
            return self.weapon.card.weapon
        b = self.rules.bare_hands
        return Weapon(dice=b.dice, hit=b.hit, damage=b.damage, name=b.name)

    def card_cost(self, inst: CardInst, target: Foe | None = None) -> int:
        card = inst.card
        cost = card.cost
        saved, self.target = self.target, target
        for m in card.cost_mods:
            if self.check(m.get("if")):
                cost += m.delta
        self.target = saved
        return max(0, cost)

    def check(self, cond) -> bool:
        return cond is None or CONDITIONS[cond.cond](self, cond)

    def playable(self, inst: CardInst, target: Foe | None = None) -> bool:
        card = inst.card
        if self.over or card.has("unplayable") or inst not in self.hand:
            return False
        if card.target == "enemy" and (target is None or not target.alive or not self.targetable(target)):
            return False
        return self.card_cost(inst, target) <= self.energy

    def targetable(self, foe: Foe) -> bool:
        """Guard: while a living enemy has Guard, only Guard enemies can be targeted."""
        guards = [f for f in self.living() if f.has("GUARD")]
        return not guards or foe in guards

    # --- Events

    def snapshot(self) -> dict:
        w = self.weapon_stats()
        return {
            "hero": {
                "hp": self.hero.hp,
                "max_hp": self.hero.max_hp,
                "shields": self.hero.shields,
                "nerve": self.hero.nerve,
                "max_nerve": self.hero.max_nerve,
                "statuses": dict(self.hero.statuses),
            },
            "foes": [
                {
                    "uid": f.uid,
                    "id": f.rec.id,
                    "hp": max(0, f.hp),
                    "max_hp": f.max_hp,
                    "shields": f.shields,
                    "statuses": dict(f.statuses),
                    "alive": f.alive,
                    "intent": self.intent_view(f) if f.alive else None,
                }
                for f in self.foes
            ],
            "hand": [c.uid for c in self.hand],
            "draw": len(self.draw),
            "discard": len(self.discard),
            "exhaust": len(self.exhaust),
            "energy": self.energy,
            "weapon": None
            if not self.weapon
            else {"uid": self.weapon.uid, "id": self.weapon.id, "durability": self.weapon.durability},
            "weapon_name": w.name or (self.weapon.card.name if self.weapon else ""),
            "auras": [c.uid for c in self.auras],
            "equipment": [{"uid": c.uid, "id": c.id, "uses": c.uses} for c in self.equipment],
            "round": self.round,
            "turn": self.turn,
            "clues": self.clues,
            "entropy": self.entropy,
            "over": self.over,
        }

    def emit(self, event: str, /, **data):
        self.events.append(Event(event, data, self.snapshot()))

    def intent_view(self, foe: Foe) -> dict | None:
        """What the intent shows: its kind, and the damage after statuses, for attacks."""
        intent = foe.intent
        if intent is None:
            return None
        kind = intent.kind
        if foe.flags.get("hide_intent"):
            kind = "unknown"
        view = {"id": foe.intent_id, "kind": kind}
        for e in intent.effects:
            if e.op == "attack":
                view["damage"] = self.enemy_damage(foe, e.damage)
                view["times"] = e.get("times", 1)
            elif e.op == "horror":
                view["horror"] = e.n
            elif e.op in ("shield", "shield_all"):
                view["shield"] = e.n
            elif e.op == "apply":
                view["status"] = e.status
        return view

    # --- Hooks

    def hook_sources(self, event: str):
        """(handler name, owner, params) for every hook that listens to `event`."""
        for owner in [self.hero, *self.living()]:
            for sid, n in list(owner.statuses.items()):
                h = CONTENT.statuses[sid].hooks.get(event)
                if h and n:
                    yield h, owner, Params(n=n, status=sid)
        for rid in self.run.relics:
            r = CONTENT.relics[rid]
            if event in r.hooks:
                yield r.hooks[event], self.hero, r.params.over({"relic": rid})
        for inst in [*self.auras, *self.equipment, *([self.weapon] if self.weapon else [])]:
            c = inst.card
            if event in c.hooks:
                yield c.hooks[event], inst, c.params
        for inst in self.hand:
            c = inst.card
            if event + "_in_hand" in c.hooks:
                yield c.hooks[event + "_in_hand"], inst, c.params
        if event in self.hunter.hooks:
            yield self.hunter.hooks[event], self.hero, Params()

    def hook(self, event: str, ev: dict) -> dict:
        for name, owner, p in list(self.hook_sources(event)):
            HOOKS[name](self, owner, p, ev)
        return ev

    # --- The queue

    def push(self, ops, src, target, front: bool = True):
        """Queue ops (Params with `op`). `front` runs them next, before what is already queued."""
        items = [(op, src, target) for op in ops]
        if front:
            self.queue.extendleft(reversed(items))
        else:
            self.queue.extend(items)

    def run_queue(self):
        while self.queue and not self.over:
            p, src, target = self.queue.popleft()
            if not self.check(p.get("if")):
                continue
            if isinstance(src, Foe):
                if src.alive:
                    INTENT_OPS[p.op](self, src, p)
            else:
                saved, self.target = self.target, target
                OPS[p.op](self, src, target, p)
                self.target = saved
            self.check_end()
        if self.over:
            self.queue.clear()

    def check_end(self):
        if self.over:
            return
        if not self.hero.alive:
            self.over = "lost"
            self.emit("lost")
        elif not self.living():
            self.over = "won"
            self.emit("won")

    # --- Piles

    def draw_cards(self, n: int):
        for _ in range(n):
            if len(self.hand) >= self.rules.hand_limit:
                break
            if not self.draw:
                if not self.discard:
                    break
                self.draw, self.discard = self.discard, []
                shuffle(self.rng_deck, self.draw)
                self.emit("shuffle")
            inst = self.draw.pop()
            self.hand.append(inst)
            self.emit("draw", uid=inst.uid)
            hook = inst.card.hooks.get("drawn")
            if hook:
                HOOKS[hook](self, inst, inst.card.params, {"inst": inst})

    def to_discard(self, inst: CardInst):
        if inst.temp and inst.card.type == "spore":
            self.exhaust.append(inst)
        else:
            self.discard.append(inst)

    # --- Commands

    def play(self, hand_index: int, target_index: int | None = None) -> bool:
        """Play a card from the hand. False if it cannot be played."""
        if not 0 <= hand_index < len(self.hand):
            return False
        inst = self.hand[hand_index]
        target = self.foes[target_index] if target_index is not None and 0 <= target_index < len(self.foes) else None
        if inst.card.target != "enemy":
            target = None
        if not self.playable(inst, target):
            return False
        card = inst.card
        self.energy -= self.card_cost(inst, target)
        self.hand.remove(inst)
        self.cards_played += 1
        self.emit("play", uid=inst.uid, card=inst.id, target=target.uid if target else None)
        if card.type == "weapon":
            self.equip(inst, target)
        elif card.type == "equipment":
            self.equipment.append(inst)
            if len(self.equipment) > 2:
                self.to_discard(self.equipment.pop(0))
            self.emit("equip", uid=inst.uid)
        elif card.type == "aura":
            self.auras.append(inst)
            self.emit("aura", uid=inst.uid)
        else:
            self.push(card.effects, inst, target)
            self.run_queue()
            if card.has("exhaust"):
                self.exhaust.append(inst)
                self.emit("exhaust", uid=inst.uid)
            else:
                self.to_discard(inst)
        self.run_queue()
        self.check_end()
        return True

    def equip(self, inst: CardInst, target: Foe | None = None):
        """Put a weapon in the slot. Its card `effects` are its Equip ops (GDD 10.3): they run once, now, with the
        new weapon already in hand, so an Equip Fire shoots the new gun."""
        if inst in self.hand:
            self.hand.remove(inst)
        old = self.weapon
        if old is not None:
            self.to_discard(old)
        if inst.durability is None:
            inst.durability = inst.card.weapon.durability
        self.weapon = inst
        self.emit("equip", uid=inst.uid, weapon=True)
        if inst.card.effects:
            self.push(inst.card.effects, inst, target)

    def end_turn(self) -> bool:
        if self.over:
            return False
        self.end_hero_turn()
        if not self.over:
            self.enemy_turn()
        if not self.over:
            self.start_turn()
        return True

    # --- Turns

    def start_turn(self):
        self.turn += 1
        self.cards_played = 0
        self.fires = 0
        if self.rules.shield_decay:
            self.hero.shields = 0 if self.turn > 1 else self.hero.shields
        self.hero.statuses.pop("WARD", None)
        self.energy = self.rules.energy + (self.first_energy if self.turn == 1 else 0)
        self.emit("turn", turn=self.turn)
        self.hook("turn_start", {"who": self.hero})
        self.run_queue()
        n = self.hook("draw_count", {"n": self.rules.draw + (self.extra_draw if self.turn == 1 else 0)})["n"]
        self.draw_cards(max(0, n))
        self.run_queue()
        self.check_end()

    def end_hero_turn(self):
        self.hook("turn_end", {"who": self.hero})
        self.run_queue()
        for inst in list(self.hand):
            card = inst.card
            if card.has("retain"):
                continue
            self.hand.remove(inst)
            if card.has("ethereal"):
                self.exhaust.append(inst)
                self.emit("exhaust", uid=inst.uid)
            else:
                self.to_discard(inst)
        self.emit("discard_hand")
        self.decay(self.hero)

    def enemy_turn(self):
        self.emit("enemy_turn")
        for foe in list(self.foes):
            if not foe.alive or self.over:
                continue
            foe.shields = 0
            intent = foe.intent
            if intent is not None:
                self.emit("act", foe=foe.uid, intent=foe.intent_id, kind=intent.kind)
                self.push(intent.effects, foe, self.hero)
                self.run_queue()
        for foe in self.living():
            self.hook("turn_end", {"who": foe})
            self.run_queue()
            self.decay(foe)
        self.round += 1
        every = self.rules.entropy_every_rounds
        if every and self.round % every == 0 and not self.over:
            self.entropy += 1
            self.emit("entropy", n=1)
        for foe in self.living():
            foe.flags.pop("hide_intent", None)
            self.roll_intent(foe)
        self.check_end()

    def decay(self, f: Fighter):
        for sid in list(f.statuses):
            if CONTENT.statuses[sid].decay == "turn":
                f.statuses[sid] -= 1
                if f.statuses[sid] <= 0:
                    del f.statuses[sid]
        self.emit("decay")

    # --- Effects the handlers use

    def apply(self, f: Fighter, status: str, n: int):
        if not f.alive or n == 0:
            return
        f.statuses[status] = f.statuses.get(status, 0) + n
        if f.statuses[status] <= 0:
            del f.statuses[status]
        self.emit("status", who=self.who(f), status=status, n=n)

    def gain_shields(self, f: Fighter, n: int):
        n = self.hook("shield_gain", {"who": f, "n": n})["n"]
        f.shields += max(0, n)
        self.emit("shield", who=self.who(f), n=n)

    def who(self, f) -> int:
        """0 for the Hunter, else the enemy's uid. Events name fighters this way."""
        return 0 if f is self.hero else f.uid

    def deal(self, target: Fighter, amount: int, source=None, kind: str = "hit"):
        """Damage through shields, then health."""
        if not target.alive:
            return
        ev = self.hook("damage_taken", {"target": target, "amount": max(0, amount), "source": source, "limits": []})
        amount = max(0, ev["amount"])
        blocked = min(target.shields, amount)
        target.shields -= blocked
        lost = amount - blocked
        for limit in ev["limits"]:  # Hooks that change health loss after shields: fn(lost, hp) -> lost.
            lost = limit(lost, target.hp)
        target.hp -= lost
        self.emit("damage", who=self.who(target), amount=amount, blocked=blocked, lost=lost, kind=kind)
        if not target.alive:
            self.died(target)

    def lose_hp(self, f: Fighter, n: int):
        if not f.alive:
            return
        f.hp -= n
        self.emit("damage", who=self.who(f), amount=n, blocked=0, lost=n, kind="self")
        if not f.alive:
            self.died(f)

    def heal(self, f: Fighter, n: int):
        f.hp = min(f.max_hp, f.hp + n)
        self.emit("heal", who=self.who(f), n=n)

    def horror(self, n: int):
        self.hero.nerve = max(0, self.hero.nerve - n)
        self.emit("horror", n=n)
        if self.hero.nerve == 0 and not self.hero.has("PANICKED"):
            self.apply(self.hero, "PANICKED", 1)

    def gain_clues(self, n: int):
        n = self.hook("clue_gain", {"n": n})["n"]
        if n > 0:
            self.clues += n
            self.emit("clue", n=n)

    def died(self, f: Fighter):
        if isinstance(f, Foe):
            f.statuses.clear()
            f.intent_id = None
            self.emit("died", who=f.uid, id=f.rec.id)
            if f.rec.clues and not f.flags.get("silent"):
                self.gain_clues(f.rec.clues)
            if not f.flags.get("silent"):
                self.run.vp += f.rec.vp

    def repair(self, n: int):
        if self.weapon:
            top = self.weapon.card.weapon.durability
            self.weapon.durability = min(top, (self.weapon.durability or 0) + n)
            self.emit("repair", n=n)

    # --- Fire

    def fire_pool(self, target: Foe, bonus: int = 0, weapon: Weapon | None = None) -> tuple[Weapon, int, int]:
        """(weapon, dice, hit target) for a Fire at `target`, after hooks. `weapon` is a gun not yet equipped."""
        w = weapon or self.weapon_stats()
        dice = self.hook("fire_dice", {"attacker": self.hero, "target": target, "dice": self.combat + w.dice + bonus})
        hit = self.hook("hit_target", {"attacker": self.hero, "target": target, "hit": w.hit})
        return w, max(1, dice["dice"]), max(2, min(6, hit["hit"]))

    def per_hit(self, w: Weapon, target: Foe) -> int:
        ev = {"attacker": self.hero, "target": target, "per_hit": w.damage}
        self.hook("damage_per_hit", ev)
        self.hook("damage_per_hit_taken", ev)
        return max(0, ev["per_hit"])

    def crit_hits(self) -> int:
        return self.hook("crit_hits", {"hits": 2})["hits"]

    def fire(self, target: Foe, p: Params):
        if target is None or not target.alive:
            alive = self.living()
            if not alive:
                return
            target = choice(self.rng_dice, alive)
        w, dice, hit = self.fire_pool(target, p.get("dice", 0) + p.get("extra", 0))
        faces = [self.rng_dice.randint(1, 6) for _ in range(dice)]
        focus = self.hero.has("FOCUS")
        rerolled = []
        for i, face in enumerate(faces):
            if face < hit and focus > 0:
                new = self.rng_dice.randint(1, 6)
                rerolled.append((i, face, new))
                faces[i] = new
                focus -= 1
        if rerolled:
            self.hero.statuses["FOCUS"] = focus
            if focus <= 0:
                del self.hero.statuses["FOCUS"]
        per_crit = self.crit_hits()
        crits = sum(1 for f in faces if w.crit and f == 6)
        hits = sum(per_crit if (w.crit and f == 6) else 1 for f in faces if f >= hit)
        if hits == 0 and p.get("zero_as"):
            hits = p.zero_as
        per = self.per_hit(w, target)
        roll = Roll(faces, hit, w.crit, hits, crits, per, hits * per, rerolled)
        if w.special:
            WEAPON_SPECIALS[w.special](self, roll, w.params)
        self.emit("roll", target=target.uid, faces=faces, hit=hit, crit=w.crit, hits=roll.hits, crits=crits,
                  rerolled=rerolled, damage=roll.damage)  # fmt: skip
        if roll.damage > 0 or roll.hits > 0:
            self.deal(target, roll.damage, self.hero, kind="crit" if crits else "hit")
        else:
            self.emit("miss", who=target.uid)
        self.spend_durability()
        self.fires += 1
        if crits:
            self.hook("crit", {"attacker": self.hero, "target": target, "crits": crits})
        self.hook("after_fire", {"target": target, "params": p, "first": self.fires == 1})
        return roll

    def spend_durability(self):
        inst = self.weapon
        if inst is None or not inst.card.weapon.durability:
            return
        inst.durability = (inst.durability or 0) - 1
        if inst.durability <= 0:
            self.spent.append(inst.uid)
            self.exhaust.append(inst)
            self.weapon = None
            self.emit("spent", uid=inst.uid, id=inst.id)

    # --- Enemy attacks

    def enemy_damage(self, foe: Foe, base: int) -> int:
        ev = {"attacker": foe, "target": self.hero, "per_hit": base}
        self.hook("damage_per_hit", ev)
        mult = self.hook("attack_mult", {"attacker": foe, "target": self.hero, "mult": 1.0})["mult"]
        return max(0, int(ev["per_hit"] * mult))

    # --- The end

    def finish(self):
        """Write the battle's results back to the run."""
        self.hook("battle_end", {"result": self.over})
        run = self.run
        run.hp = max(0, self.hero.hp)
        run.nerve = self.hero.nerve
        run.clues += self.clues
        run.entropy += self.entropy
        run.total_entropy += self.entropy
        for inst in list(self.equipment):
            if inst.uses is not None and inst.uses <= 0:
                self.destroyed.append(inst.uid)
        for uid in self.destroyed:
            run.remove(uid)
        # The last weapon in hand stays equipped. A spent one comes back equipped, with fresh ammo next battle.
        last = self.weapon or next((run.find(u) for u in reversed(self.spent) if run.find(u)), None)
        run.weapon = last.uid if last and not last.temp else None
        run.equipment = [c.uid for c in self.equipment if c.uid not in self.destroyed]
        run.bump("battles")


# --- Preview maths (exact, no rolling): the odds a Fire card shows before you play it (GDD 10.4).


def hit_distribution(dice: int, hit: int, crit: bool, per_crit: int, focus: int) -> dict[int, float]:
    """{hits: probability} for `dice` d6 with `focus` rerolls of misses, applied greedily."""
    p_miss = (hit - 1) / 6
    p_crit = 1 / 6 if crit and hit <= 6 else 0.0
    p_hit = 1 - p_miss - p_crit
    outcomes = [(0, p_miss), (1, p_hit), (per_crit, p_crit)]
    dist: dict[tuple[int, int], float] = {(0, focus): 1.0}
    for _ in range(dice):
        nxt: dict[tuple[int, int], float] = {}
        for (h, f), pr in dist.items():
            for gain, pg in outcomes:
                if pg == 0:
                    continue
                if gain == 0 and f > 0:
                    for gain2, pg2 in outcomes:
                        if pg2:
                            k = (h + gain2, f - 1)
                            nxt[k] = nxt.get(k, 0) + pr * pg * pg2
                else:
                    k = (h + gain, f)
                    nxt[k] = nxt.get(k, 0) + pr * pg
        dist = nxt
    out: dict[int, float] = {}
    for (h, _), pr in dist.items():
        out[h] = out.get(h, 0) + pr
    return out


def fire_preview(battle: Battle, inst: CardInst, target: Foe) -> dict | None:
    """The dice, hit target, expected damage and kill chance of a card's Fire effects at `target`."""
    fires = [e for e in inst.card.effects if e.op in ("fire", "last_round")]
    if not fires or target is None:
        return None
    e = fires[0]
    bonus = e.get("dice", 0)
    if e.op == "last_round" and battle.weapon:
        bonus = 2 * (battle.weapon.durability or 0)
    w, dice, hit = battle.fire_pool(target, bonus, inst.card.weapon)  # A weapon's Equip Fire shoots itself.
    dist = hit_distribution(dice, hit, w.crit, battle.crit_hits(), battle.hero.has("FOCUS"))
    per = battle.per_hit(w, target)
    zero_as = e.get("zero_as")
    expected, kill = 0.0, 0.0
    need = target.hp + target.shields
    for hits, pr in dist.items():
        h = zero_as if hits == 0 and zero_as else hits
        dmg = h * per
        if w.special:  # The gun's own special, on a roll with no faces (a face rule like exact_six adds nothing).
            roll = Roll([], hit, w.crit, h, 0, per, dmg, preview=True)
            WEAPON_SPECIALS[w.special](battle, roll, w.params)
            dmg = roll.damage
        expected += pr * dmg
        if dmg >= need:
            kill += pr
    return {"dice": dice, "hit": hit, "expected": expected, "kill": kill if len(fires) == 1 else None,
            "times": len(fires), "crit": w.crit}  # fmt: skip
