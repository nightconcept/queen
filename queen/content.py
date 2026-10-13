"""Loads `data/` into frozen records, once. `CONTENT` is the loaded data.

Shared tables live in `data/`. A scenario's own tables live in `data/scenarios/<id>/`; its `enemies.json` merges
with the shared one (an id in both is an error). docs/repo/content.md lists the fields of every record.
"""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any

from nightengine import ContentError, read_json, records

from .config import DATA, HUNTER, SCENARIO


def freeze(v: Any) -> Any:
    if isinstance(v, list):
        return tuple(freeze(x) for x in v)
    if isinstance(v, dict):
        return Params(v)
    return v


class Params(Mapping):
    """Numbers and settings for a handler, read as attributes (`p.n`) or with `p.get("n", 0)`. Frozen.
    Lists become tuples and objects become Params."""

    __slots__ = ("_d",)

    def __init__(self, data: Mapping | None = None, **more):
        object.__setattr__(self, "_d", {k: freeze(v) for k, v in {**(data or {}), **more}.items()})

    def __getattr__(self, name: str):
        try:
            return self._d[name]
        except KeyError:
            raise AttributeError(f"no param {name!r}; params: {', '.join(self._d) or 'none'}") from None

    def __setattr__(self, name, value):
        raise AttributeError("params are frozen")

    def __getitem__(self, key):
        return self._d[key]

    def __iter__(self) -> Iterator:
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __repr__(self) -> str:
        return f"Params({self._d!r})"

    def __eq__(self, other):
        return isinstance(other, Mapping) and dict(self.items()) == dict(other.items())

    def __hash__(self):
        return hash(tuple(sorted(self._d)))

    def over(self, other: Mapping | None) -> "Params":
        return Params({**self._d, **(other or {})})


def effects(v) -> tuple[Params, ...]:
    return tuple(Params(e) for e in v or ())


@dataclass(frozen=True)
class Weapon:
    dice: int = 0  # Bonus dice on Fire.
    hit: int = 5  # A die at or above this hits.
    damage: int = 1  # Damage per hit.
    crit: bool = False  # 6s count as 2 hits.
    durability: int = 0  # Fires before it breaks. 0: never breaks (Bare Hands).
    special: str | None = None  # A handler in WEAPON_SPECIALS.
    params: Params = field(default_factory=Params)
    name: str = ""

    @staticmethod
    def of(v) -> "Weapon | None":
        if v is None:
            return None
        v = dict(v)
        v["params"] = Params(v.get("params"))
        return Weapon(**v)


CARD_FIELDS = ("text", "cost", "effects", "weapon", "hooks", "params", "keywords", "cost_mods", "uses")


@dataclass(frozen=True)
class Card:
    id: str
    name: str
    set: str
    element: str | None
    tier: str  # B basic, S Standard, P Prototype, X Prime, W weakness, T trauma.
    type: str  # action, weapon, equipment, aura, trauma, spore.
    cost: int
    target: str  # enemy or none.
    text: str
    icons: tuple[str, ...] = ()
    art: str = "sword"  # An icon name (data/art.json).
    effects: tuple[Params, ...] = ()
    keywords: tuple[str, ...] = ()
    weapon: Weapon | None = None
    hooks: Params = field(default_factory=Params)
    params: Params = field(default_factory=Params)
    cost_mods: tuple[Params, ...] = ()
    uses: int = 0  # Equipment: uses before it is destroyed.
    plus: Params | None = None  # The upgrade: any of CARD_FIELDS.
    upgrades_to: str | None = None  # The next tier's card id (GDD 13.2).
    pool: bool = False  # Can appear as a reward.
    signature: bool = False
    weakness: bool = False
    subtype: str = ""

    def upgraded(self) -> "Card":
        """This card with its `plus` fields on top."""
        if not self.plus:
            return self
        changes = {}
        for k, v in self.plus.items():
            if k == "weapon":
                changes[k] = Weapon.of(v)
            elif k in ("effects", "cost_mods"):
                changes[k] = tuple(Params(e) for e in v)
            elif k == "keywords":
                changes[k] = tuple(v)
            else:
                changes[k] = v
        return Card(**{**self.__dict__, **changes, "name": self.name + "+", "plus": None})

    def has(self, keyword: str) -> bool:
        return keyword in self.keywords


@dataclass(frozen=True)
class Intent:
    kind: str  # attack, horror, defend, buff, debuff, summon, hatch, unknown (GDD 12.1).
    effects: tuple[Params, ...]


@dataclass(frozen=True)
class Enemy:
    id: str
    name: str
    hp: tuple[int, int]
    art: str
    behaviour: str  # A generator in BEHAVIOURS.
    intents: dict[str, Intent]
    params: Params = field(default_factory=Params)
    statuses: Params = field(default_factory=Params)  # Statuses at the start of a battle.
    scale: float = 1.0
    elite: bool = False
    boss: bool = False
    hunter: bool = False  # Moves toward Rook on the map.
    evade: int = 2
    vp: int = 0  # Victory points: XP at the resolution.
    clues: int = 0  # Clues it drops.


@dataclass(frozen=True)
class Status:
    id: str
    name: str
    colour: str
    decay: str  # turn, battle, or none.
    good: bool
    text: str
    hooks: Params = field(default_factory=Params)


@dataclass(frozen=True)
class Relic:
    id: str
    name: str
    icon: str
    pool: str  # start, elite, or story.
    text: str
    hooks: Params = field(default_factory=Params)
    params: Params = field(default_factory=Params)


@dataclass(frozen=True)
class Hunter:
    id: str
    name: str
    title: str
    element: str
    art: str
    health: int
    nerve: int
    skills: Params
    deck: tuple[tuple[str, int], ...]
    weapon: str
    relics: tuple[str, ...] = ()
    hooks: Params = field(default_factory=Params)
    elder_sign: Params = field(default_factory=Params)
    blurb: str = ""


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    art: str
    pos: tuple[int, int]
    shroud: int
    clues: int
    links: tuple[str, ...]
    text: str
    art_xy: tuple[int, int] = (0, 0)
    revealed: bool = False
    locked: bool = False
    locked_text: str = ""
    on_reveal: tuple[Params, ...] = ()
    on_enter: tuple[Params, ...] = ()
    actions: tuple[Params, ...] = ()


@dataclass(frozen=True)
class Story:
    id: str
    kind: str  # story, treachery, enemy, boon, agenda, act.
    title: str
    text: tuple[str, ...]
    choices: tuple[Params, ...]
    art: str | None = None
    art_xy: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class Scenario:
    id: str
    name: str
    subtitle: str
    intro: tuple[str, ...]
    start: str
    symbols: Params
    acts: tuple[Params, ...]
    agendas: tuple[Params, ...]
    resolutions: Params
    locations: dict[str, Location]
    stories: dict[str, Story]
    encounter: tuple[tuple[str, int], ...]


def _enemies(data: dict) -> dict[str, Enemy]:
    def intents(v):
        return {k: Intent(i["kind"], effects(i.get("effects"))) for k, i in v.items()}

    return records(
        data,
        Enemy,
        convert={"hp": tuple, "intents": intents, "params": Params, "statuses": Params},
    )


def _cards(data: dict) -> dict[str, Card]:
    return records(
        data,
        Card,
        convert={
            "icons": tuple,
            "effects": effects,
            "keywords": tuple,
            "weapon": Weapon.of,
            "hooks": Params,
            "params": Params,
            "cost_mods": effects,
            "plus": Params,
        },
    )


def _scenario(sid: str) -> Scenario:
    root = DATA / "scenarios" / sid
    s = read_json(root / "scenario.json")
    locations = records(
        read_json(root / "locations.json"),
        Location,
        convert={
            "pos": tuple,
            "links": tuple,
            "art_xy": tuple,
            "on_reveal": effects,
            "on_enter": effects,
            "actions": effects,
        },
    )
    stories = records(
        read_json(root / "story.json"),
        Story,
        convert={"text": tuple, "choices": effects, "art_xy": tuple},
    )
    encounter = tuple((sid_, n) for sid_, n in read_json(root / "encounter.json")["deck"])
    try:
        return Scenario(
            id=sid,
            name=s["name"],
            subtitle=s["subtitle"],
            intro=tuple(s["intro"]),
            start=s["start"],
            symbols=Params(s["symbols"]),
            acts=effects(s["acts"]),
            agendas=effects(s["agendas"]),
            resolutions=Params(s["resolutions"]),
            locations=locations,
            stories=stories,
            encounter=encounter,
        )
    except KeyError as e:
        raise ContentError(f"scenario {sid!r}: missing {e}") from e


def _merge(*tables: dict, label: str) -> dict:
    out = {}
    for t in tables:
        for k, v in t.items():
            if k in out:
                raise ContentError(f"{label} {k!r} is defined twice")
            out[k] = v
    return out


class Content:
    """Every table, loaded on first use."""

    def __init__(self, root: Path = DATA, scenario: str = SCENARIO):
        self.root = root
        self.scenario_id = scenario

    @cached_property
    def rules(self) -> Params:
        return Params(read_json(self.root / "rules.json"))

    @cached_property
    def palette(self) -> dict[str, int]:
        colours = read_json(self.root / "palette.json")["colours"]
        return {name: int(hexcode[1:], 16) for name, hexcode in colours.items()}

    @cached_property
    def colour(self) -> dict[str, int]:
        """Palette index by name."""
        return {name: i for i, name in enumerate(self.palette)}

    @cached_property
    def art(self) -> dict:
        return read_json(self.root / "art.json")

    @cached_property
    def cards(self) -> dict[str, Card]:
        tables = [read_json(p) for p in sorted((self.root / "cards").glob("*.json"))]
        return _cards(_merge(*tables, label="card"))

    @cached_property
    def enemies(self) -> dict[str, Enemy]:
        shared = read_json(self.root / "enemies.json")
        own = self.root / "scenarios" / self.scenario_id / "enemies.json"
        return _enemies(_merge(shared, read_json(own) if own.exists() else {}, label="enemy"))

    @cached_property
    def statuses(self) -> dict[str, Status]:
        return records(read_json(self.root / "statuses.json"), Status, convert={"hooks": Params})

    @cached_property
    def relics(self) -> dict[str, Relic]:
        return records(read_json(self.root / "relics.json"), Relic, convert={"hooks": Params, "params": Params})

    @cached_property
    def hunters(self) -> dict[str, Hunter]:
        return records(
            read_json(self.root / "hunters.json"),
            Hunter,
            convert={
                "skills": Params,
                "deck": lambda v: tuple((c, n) for c, n in v),
                "relics": tuple,
                "hooks": Params,
                "elder_sign": Params,
            },
        )

    @cached_property
    def bag(self) -> Params:
        return Params(read_json(self.root / "hive_bag.json"))

    @cached_property
    def scenario(self) -> Scenario:
        return _scenario(self.scenario_id)

    @property
    def hunter(self) -> Hunter:
        return self.hunters[HUNTER]

    def card(self, cid: str, plus: bool = False) -> Card:
        c = self.cards[cid]
        return c.upgraded() if plus else c


CONTENT = Content()
