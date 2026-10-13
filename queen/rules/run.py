"""The state of one run: the Hunter, the deck, the map, the two clocks, and the campaign log (GDD 8.1).

Plain data only, so a run saves to JSON and loads back the same. The rules that change it are in explore.py.
"""

from dataclasses import asdict, dataclass, field

from ..content import CONTENT, Card
from .rng import Streams, shuffle


@dataclass
class CardInst:
    """One card in the deck. Weapons keep their durability and equipment its uses between battles."""

    uid: int
    id: str
    plus: bool = False
    durability: int | None = None
    uses: int | None = None
    temp: bool = False  # A battle-only card (a Spore). It never joins the run's deck.

    @property
    def card(self) -> Card:
        return CONTENT.card(self.id, self.plus)


@dataclass
class LocState:
    revealed: bool = False
    clues: int = 0
    enemies: list[str] = field(default_factory=list)
    exhausted: bool = False  # Evaded until the next Mythos phase.
    done: list[str] = field(default_factory=list)  # Location actions used (`once`).
    rested: int = -1  # The agenda index when it was last rested at.


@dataclass
class RunState:
    seed: int
    hunter: str
    hp: int
    max_hp: int
    nerve: int
    max_nerve: int
    skills: dict[str, int]
    deck: list[CardInst]
    weapon: int | None  # The uid of the equipped weapon.
    equipment: list[int] = field(default_factory=list)
    relics: list[str] = field(default_factory=list)
    xp: int = 0
    scrip: int = 0
    clues: int = 0
    location: str = ""
    locs: dict[str, LocState] = field(default_factory=dict)
    unlocked: list[str] = field(default_factory=list)
    act: int = 0
    agenda: int = 0
    entropy: int = 0  # Entropy on the current agenda.
    total_entropy: int = 0
    encounter: list[str] = field(default_factory=list)
    encounter_discard: list[str] = field(default_factory=list)
    bag: list[str] = field(default_factory=list)
    actions: int = 3  # Actions left this round.
    round: int = 1
    mythos_draws: int = 1
    hive_hp: int = 0  # Extra max HP for every enemy (Agenda 1's flip).
    queen_awake: bool = False
    next_battle: dict[str, int] = field(default_factory=dict)  # spores, energy, shields for the next battle only.
    fatigued: list[int] = field(default_factory=list)  # Committed cards: they start the next battle discarded.
    opening_draw: int = 0  # Extra cards in the next battle's opening hand (Elder Sign).
    beacon_used: int = -1  # The agenda index when Lantern's Beacon was used.
    vp: int = 0
    log: dict[str, int] = field(default_factory=dict)
    trauma: dict[str, int] = field(default_factory=dict)
    outcome: str | None = None  # A resolution id when the run is over.
    next_uid: int = 1
    rng_state: dict[str, list[int]] = field(default_factory=dict)
    prime_pity: int = 0
    stats: dict[str, int] = field(default_factory=dict)
    steps: list[dict] = field(default_factory=list)  # What happens next (flow.py).

    def __post_init__(self):
        self.rng = Streams(self.seed, self.rng_state or None)

    # --- Deck

    def new_card(self, cid: str, plus: bool = False, temp: bool = False) -> CardInst:
        card = CONTENT.card(cid, plus)
        inst = CardInst(self.next_uid, cid, plus, temp=temp)
        if card.weapon:
            inst.durability = card.weapon.durability
        if card.type == "equipment":
            inst.uses = card.uses
        self.next_uid += 1
        return inst

    def add_card(self, cid: str, plus: bool = False) -> CardInst:
        inst = self.new_card(cid, plus)
        self.deck.append(inst)
        return inst

    def find(self, uid: int | None) -> CardInst | None:
        return next((c for c in self.deck if c.uid == uid), None)

    def remove(self, uid: int):
        self.deck = [c for c in self.deck if c.uid != uid]
        if self.weapon == uid:
            self.weapon = None
        self.equipment = [u for u in self.equipment if u != uid]

    @property
    def weapon_inst(self) -> CardInst | None:
        return self.find(self.weapon)

    # --- Scenario

    @property
    def scenario(self):
        return CONTENT.scenario

    def loc(self, lid: str | None = None) -> LocState:
        return self.locs[lid or self.location]

    def available(self, lid: str) -> bool:
        rec = self.scenario.locations[lid]
        return not rec.locked or lid in self.unlocked

    def bump(self, stat: str, n: int = 1):
        self.stats[stat] = self.stats.get(stat, 0) + n

    # --- Saving

    def to_json(self) -> dict:
        self.rng_state = self.rng.state()
        d = asdict(self)
        return d

    @staticmethod
    def from_json(d: dict) -> "RunState":
        d = dict(d)
        d["deck"] = [CardInst(**c) for c in d["deck"]]
        d["locs"] = {k: LocState(**v) for k, v in d["locs"].items()}
        return RunState(**d)


def new_run(seed: int, difficulty: str | None = None, log: dict[str, int] | None = None) -> RunState:
    """A fresh run of the scenario, with the Hunter's starting deck, relics and weapon."""
    h = CONTENT.hunter
    s = CONTENT.scenario
    run = RunState(
        seed=seed,
        hunter=h.id,
        hp=h.health,
        max_hp=h.health,
        nerve=h.nerve,
        max_nerve=h.nerve,
        skills=dict(h.skills),
        deck=[],
        weapon=None,
        relics=list(h.relics),
        log=dict(log or {}),
    )
    for cid, n in h.deck:
        for _ in range(n):
            run.add_card(cid)
    run.weapon = run.add_card(h.weapon).uid
    run.trauma = {"physical": run.log.get("trauma_physical", 0), "mental": run.log.get("trauma_mental", 0)}
    run.max_hp -= 5 * run.trauma["physical"]
    run.max_nerve -= run.trauma["mental"]
    run.hp, run.nerve = run.max_hp, run.max_nerve
    for lid, rec in s.locations.items():
        run.locs[lid] = LocState(revealed=rec.revealed, clues=rec.clues)
    run.location = s.start
    run.locs[s.start].revealed = True
    run.encounter = [sid for sid, n in s.encounter for _ in range(n)]
    shuffle(run.rng["encounter"], run.encounter)
    bag = CONTENT.bag[difficulty or CONTENT.rules.difficulty]
    run.bag = [token for token, n in bag.items() for _ in range(n)]
    run.actions = CONTENT.rules.actions_per_round
    run.entropy = run.log.get("next_entropy", 0)
    run.total_entropy = run.entropy
    return run
