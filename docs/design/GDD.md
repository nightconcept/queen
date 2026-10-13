# Queen — Game Design Document

Queen is a single-player deckbuilding card game for phones. It is a prototype of the Highcard theme, built
with Python and Pyxel on NightEngine. It takes its battles from Slay the Spire (StS) and Marvel Snap, and its
story and scenario structure from Arkham Horror: The Card Game (AHLCG).

This GDD is a living document. It describes the game we want now. Git keeps the history. The numbers live in
`queen/data/`; this document gives the rules and the intent, and links to the data.

**Contents**

1. [Vision and pillars](#1-vision-and-pillars)
2. [Inspiration study: Slay the Spire](#2-inspiration-study-slay-the-spire)
3. [Inspiration study: Arkham Horror LCG](#3-inspiration-study-arkham-horror-lcg)
4. [Inspiration study: Marvel Snap (feel only)](#4-inspiration-study-marvel-snap-feel-only)
5. [Inspiration study: Highcard](#5-inspiration-study-highcard) — the theme, and tailoring it to solo play
6. [The synthesis: how Queen plays](#6-the-synthesis-how-queen-plays)
7. [Setting and story](#7-setting-and-story)
8. [The run: scenario, acts, agendas, locations](#8-the-run-scenario-acts-agendas-locations)
9. [Skill tests and the Hive Bag](#9-skill-tests-and-the-hive-bag)
10. [Battle](#10-battle)
11. [Cards](#11-cards)
12. [Enemies and intents](#12-enemies-and-intents)
13. [Progression: rewards, XP, upgrades, trauma](#13-progression-rewards-xp-upgrades-trauma)
14. [Screens, layout and touch controls](#14-screens-layout-and-touch-controls)
15. [Art, palette, font and audio](#15-art-palette-font-and-audio)
16. [Architecture: data-driven content, mechanics as code](#16-architecture-data-driven-content-mechanics-as-code)
17. [Testing and verification](#17-testing-and-verification)
18. [Scope: the vertical slice and beyond](#18-scope-the-vertical-slice-and-beyond)
19. [Open questions](#19-open-questions)

---

## 1. Vision and pillars

> A lone Hunter breaks into a living hive-ship to kill the alien Queen before she wakes. Every step inside
> costs time, and time feeds her.

**The pitch.** Slay the Spire's tight turn-by-turn card battles sit inside an Arkham Horror scenario. You
explore a small map of hive locations, gather clues to advance the Act, and watch the Agenda's doom climb
toward the Queen's awakening. The fights are punchy and readable, like Snap on a phone. The story reacts to
what you do, and the ending depends on how fast and how cleanly you got to her.

### Pillars

1. **Two clocks, one decision.** Every choice trades Discovery (progress) against Entropy (doom). This is
   Highcard's core tension and AHLCG's act/agenda race. Fighting costs time. Avoiding fights costs safety.
   Investigating costs both.
2. **Readable tactics, swingy dice.** As in StS, you can see what each enemy will do next turn. As in
   Highcard, damage comes from d6 rolls. The game always shows the odds before you commit, so a bad roll
   feels like a risk you chose, not a cheat.
3. **The story is a system.** Story text is not decoration between fights. Agendas change the rules,
   locations hide events, choices write to the campaign log, and the log changes the next run (AHLCG).
4. **One thumb, portrait, tactile.** You hold the phone in one hand. Cards lift, tilt and snap under your
   thumb. Every action is a drag or a tap, and every tap target is at least 24 logical px (96 device px).
5. **Data grows, code stays small.** New cards, enemies, locations and scenarios are JSON records. New
   mechanics are small named Python functions. A designer adds a card without touching the battle engine.

### Non-goals (prototype)

- No multiplayer, no PvP, no online features.
- No full Highcard rules port (no ally phase, no 2-action economy in battle, no movement on the battlefield).
- No meta-progression unlocks between runs beyond the campaign log (no StS-style unlock tree yet).
- No iOS build. Android (WebView APK), web, and desktop only, through NightEngine.

---

## 2. Inspiration study: Slay the Spire

This section explains how StS works and why. Queen copies the parts marked **Take**, changes the parts
marked **Adapt**, and leaves out the parts marked **Skip**.

### 2.1 Run structure

- **Three acts plus a finale.** Each act is a branching map of about 15 floors that ends in a boss. The map
  is a directed graph of rooms: Monster, Elite, Event (?), Merchant, Rest site and Treasure. The player sees
  the whole map at the start of the act and plans a route. **Why it works:** the route is a strategic
  decision. Elites give relics but risk death, rest sites let you heal or upgrade, and shops let you buy and
  remove cards. Every path is a risk/reward bet that you can see in advance.
- **Floor pressure.** HP carries between fights. Healing is scarce (rest sites, some relics, some events),
  so each fight's cost matters across the whole act.
- **Adapt:** Queen replaces the floor map with an AHLCG location graph (§8). We keep the "see the map,
  plan your route" feeling. Locations are face-down until you enter them, but their names and connections
  are visible. The pressure comes from doom (time), not floor count.

### 2.2 The combat loop

- **Energy.** 3 energy each turn, unspent energy is lost. Cards cost 0 to 3 (X costs exist). **Why:** a
  small fixed budget makes every turn a knapsack puzzle. **Take.** Queen uses 3 energy per turn.
- **Draw, hand, discard, exhaust.** You draw 5 cards each turn. At the end of the turn your hand goes to the
  discard pile (unless a card has **Retain**). When the draw pile is empty, the discard pile shuffles back.
  **Exhaust** removes a card for the rest of the fight. **Ethereal** cards exhaust if they are still in
  your hand at the end of the turn. **Innate** cards start in your opening hand. **Why:** deck cycling makes
  deck size and composition the long-term strategy. A thin deck sees its best cards more often. **Take
  all**, with Highcard names where they exist (see §11.4).
- **Block.** Block absorbs damage and resets at the start of your turn (unless something says otherwise).
  **Why:** with block, defence is a per-turn decision, so there is no slow turtling. **Take** as Highcard
  **Shields** (Highcard shields also reset each turn).
- **Intents.** Each enemy shows its next action above its head: attack (with the number), block, buff,
  debuff, or unknown. **Why:** this is the single most important StS design choice. It turns combat from
  guessing into planning. You know exactly how much block you need, or whether you can race. **Take**,
  and the intent shows expected damage and a range when the enemy rolls dice (§12).
- **Enemy move sets.** Enemies follow scripted patterns with weights and anti-repeat rules (for example,
  "never the same move three times in a row"). Elites and bosses have phases. **Take** as named behaviour
  scripts (§12, §16).
- **Statuses (buffs and debuffs).** Strength (+damage per hit), Dexterity (+block per card), Vulnerable
  (+50% damage taken), Weak (−25% damage dealt), Frail (−25% block gained), Poison, and many more. Most
  count down by 1 each turn. **Why:** they make multi-turn plans and give cards their synergies. **Adapt:**
  Queen's statuses fit dice (§10.6). For example, *Exposed* lowers the hit target against that enemy, and
  *Shaken* removes a die from attacks.
- **Powers.** Cards that stay in play for the whole fight and change the rules ("At the start of your turn,
  gain 1 Strength"). **Take** as Highcard **Auras** (persistent cards in play).
- **Status and curse cards.** Enemies put junk cards into your deck (Wound, Dazed, Slimed, Burn). Curses
  are permanent junk cards from events. **Why:** they create counter-play to deck thinning and make
  enemies feel different. **Take** as *Spore* (fight-only junk) and Highcard **Traumas** (permanent curses:
  *Shaken, Also Stirred*, *Remembrance of All Traumas*).

### 2.3 Rewards and deckbuilding

- **Card rewards.** After each normal fight, choose 1 of 3 cards or skip. Rarity is Common, Uncommon or Rare.
  The chance of a Rare grows each time you do not see one (pity timer). **Why:** skipping is a real choice.
  The best decks are small and focused, so the reward screen is about saying no. **Take**, including skip
  and a pity counter. Highcard tiers map to rarity: Standard is common, Prototype is uncommon, Prime is rare.
- **Gold and shops.** Gold buys cards, relics and potions, and pays for card removal. Removal price rises
  each time. **Adapt** as **Scrip** and a single *Supply Cache* location (post-slice; §18).
- **Upgrades.** Each card has one upgrade ("+"), usually +damage, −cost, or an extra keyword. Upgrades come
  from rest sites and some events. **Adapt:** Queen merges StS upgrades with AHLCG XP. You spend XP at a
  rest to upgrade a card along Highcard's tier path: Standard to Standard+, Standard+ to Prototype, and
  Prototype to Prime (§13).
- **Relics.** Passive items that change rules for the whole run. Bosses give a choice of 3 powerful relics,
  and some of those have a drawback. **Why:** relics create builds, and they change how you value cards.
  **Take** as Highcard **Relics** (§13.3). The slice has few of them.
- **Potions.** One-use items with limited slots. **Skip** for the slice. They fold into Arkham-style
  **Supplies** later (§19).

### 2.4 Difficulty and replay

- **Ascension.** 20 cumulative modifiers (more elites, stronger enemies, less healing). **Adapt:** AHLCG
  difficulty instead. Easy, Standard, Hard and Expert change the **Hive Bag** (§9.2) and the doom
  thresholds. Ascension-style modifiers can be added later as data.
- **Seeds.** A run is fully determined by its seed. **Take:** NightEngine is deterministic, with one
  `game.rng`, recorded input, and replays.

### 2.5 Why StS combat feels good (what we must keep)

1. Perfect information about the next enemy turn.
2. A small, fixed energy budget that forces trade-offs.
3. Fast resolution: a card resolves the moment you release it, with immediate numbers.
4. Damage previews: the number on an attack card updates for Strength, Weak and Vulnerable before you play
   it.
5. Undo-free but low-stakes turns: mistakes cost HP, not the run, early on.

Queen adds dice, which works against points 1 and 4. The fix is in §10.4: every Fire card shows its dice,
hit target and expected damage against the hovered enemy, and intents show ranges. The dice only add
variance on your side. Enemy damage is fixed unless the enemy says otherwise.

---

## 3. Inspiration study: Arkham Horror LCG

### 3.1 Scenario structure

- **Act deck and agenda deck.** Each scenario has an **Act deck** (the investigators' progress) and an
  **Agenda deck** (the enemy's plan). The act advances when the investigators spend the required clues (or
  meet a condition). The agenda advances when doom reaches its threshold. Each card has a front (setup and
  flavour) and a back (what happens when it flips: new enemies, new locations, rule changes, story).
  **Why:** two decks racing each other give every scenario a shape and a tension curve, and the flip text
  tells the story at the exact moment the state changes. **Take.** This is the backbone of a Queen run.
- **Doom.** One doom goes on the agenda at the start of each Mythos phase (each round). Some enemies and
  treacheries add more. Doom on enemies also counts toward the agenda. **Take** as **Entropy**, Highcard's
  name for the doom clock.
- **Resolutions.** Each scenario has several endings (R1, R2, R3, and "no resolution", which happens when
  everyone is defeated). Each resolution gives text, XP, and campaign log entries, and can add trauma or
  cards. **Why:** losing is still a story, and the campaign continues. **Take** as Good, Neutral and Bad
  outcomes (Highcard's names), plus a Defeat outcome.

### 3.2 Locations and clues

- **Locations** are cards on the table, connected by symbols. Most begin unrevealed. Entering one flips it.
  Each has a **shroud** value (how hard it is to investigate) and **clues** (how many you can find there,
  often "per investigator"). Some have forced effects or actions printed on them. **Why:** the map is a
  puzzle of where to spend actions. A high-shroud location is rich but slow. **Take:** Queen locations have
  shroud, clues, a reveal story, optional forced effects, and optional location actions (§8.3).
- **Investigate:** an Intellect test against the location's shroud. Success discovers 1 clue. **Take.**

### 3.3 The action economy

- **Three actions per turn.** Move, Investigate, Fight, Evade, Engage, Draw, Resource, Play, or
  Activate. **Why:** a tiny action budget is the time currency. Every action is a decision about time.
  **Take** for exploration mode: each round gives **3 actions**. After 3 actions, a **Mythos phase**
  happens (§8.5).
- **Attacks of opportunity.** If you take most actions while engaged with an enemy, that enemy attacks you.
  **Adapt:** in Queen, an enemy at your location starts a battle when you take a non-Fight/Evade action
  there (§8.4).

### 3.4 Skill tests and the chaos bag

- **Four skills:** Willpower, Intellect, Combat, Agility.
- **A test:** skill value + committed cards' icons + a token drawn from the **chaos bag**, compared with the
  difficulty. The bag holds numeric tokens (+1, 0, −1, −2, …), symbol tokens whose effect depends on the
  scenario (Skull, Cultist, Tablet, Elder Thing), the **Auto-fail** tentacle, and the **Elder Sign** (a
  good effect that depends on the investigator). **Why:** one bag lets the designer tune difficulty and
  theme per scenario. Symbol tokens make every scenario feel different with the same core rule. The
  campaign adds tokens to the bag as things go wrong, so a bad story makes the game harder. **Take** as the
  **Hive Bag** (§9).
- **Committing cards.** You can commit cards from your hand to add their skill icons. That costs you the
  cards. **Take:** Queen cards have skill icons, and you can commit them to an exploration test (§9.3).

### 3.5 Health, sanity, trauma, weaknesses

- **Damage and horror.** Each investigator has health and sanity. Some attacks deal horror. At 0 in either
  you are defeated and take **physical** or **mental trauma**, which lowers that stat for the rest of the
  campaign. **Take:** Queen has **Health** and **Nerve** (sanity). Horror attacks and treacheries reduce
  Nerve. Defeat writes trauma to the campaign log.
- **Signature cards and weaknesses.** Each investigator has unique signature cards and a personal
  weakness, plus one random basic weakness. A weakness is a bad card that you must resolve when you draw it.
  **Why:** the deck tells the character's story. **Take:** the Hunter Rook has a signature card and a
  signature weakness, *Tormented Dreamscape* (from Highcard Set 001).

### 3.6 Campaign, XP, deck upgrades

- **XP** comes from victory points on defeated enemies and explored locations, plus resolution bonuses. It
  is spent between scenarios on higher-level cards or upgrades. **Take:** Queen awards XP after the
  scenario and also at mid-run rest locations (§13.2).
- **Campaign log.** It records choices and outcomes ("The Lodge believes you", "You burned the house"),
  and later scenarios read it. **Take:** a key-value campaign log that story records can read and write
  (§8.6).

### 3.7 Why AHLCG works (what we must keep)

1. The agenda gives a hard clock, so exploring always has a cost.
2. Text at the flip moments turns state changes into story beats.
3. One chaos bag tunes difficulty and theme together.
4. Failure continues the story instead of ending it.
5. The map is small and hand-made, so every location is memorable.

---

## 4. Inspiration study: Marvel Snap (feel only)

Queen does not use Snap's rules (lanes, simultaneous reveal, snapping). It takes Snap's **feel**:

- **Big cards, one hand.** Cards in hand are large and readable. The hand is a gentle fan at the bottom of
  a portrait screen, inside thumb reach.
- **Physicality.** A card lifts when you touch it, follows your finger with a slight lag, tilts in the
  direction of motion, and grows when it is over a valid target. Releasing it on a target makes it slam:
  scale up, flash, then resolve. Releasing it in the wrong place springs it back to the hand.
- **Tap and hold to inspect.** Holding a card (or an enemy, a status icon, or a relic) for 0.3 s shows a
  large version with the full text, keywords and art. Releasing closes it.
- **Number punch.** Damage numbers are large, pop with overshoot, and use colour (white hit, yellow crit,
  grey blocked).
- **Short animations, never blocking for long.** No resolution waits more than 0.5 s. Input can be queued
  during animation.

---

## 5. Inspiration study: Highcard

Queen is a prototype of the Highcard theme. The source repo is `../highcard` (read `highcard/DESIGN.md`).

| Highcard concept | Queen use |
| --- | --- |
| Hunter (character card: element, health, power) | The player character: Rook, a Kinetic Hunter (§11.1) |
| Elements R, G, K, E, Z | The slice uses K (Kinetic: aggression, precision, crits, Rush, single-target burst). The data supports all five. |
| Weapons (one equipped; +dice, hit threshold, damage, durability) | Battle: the equipped Weapon sets how Fire cards roll (§10.3) |
| Equipment (slots) | Equipment cards: persistent, one or two slots (§11.4) |
| Actions | Skills/attacks played from hand (one-shot) |
| Aura | StS Powers: persistent effects (§11.4) |
| Relic | Run-wide passives (§13.3) |
| Ally | Post-slice. Snap-style board slots (§19) |
| Tiers: Standard / Prototype / Prime | Rarity and the upgrade path (§13.2) |
| Keywords: Rush, Guard, Pre-empt, Recon, Crit | Rush, Pre-empt, Recon and Crit are in the slice. Guard is used by enemies (§10.6). |
| Dice: d6, 5–6 hit, 6 crit | Fire cards (§10.4) |
| Discovery clock | Clues and the Act deck (§8) |
| Entropy clock | Doom and the Agenda deck (§8) |
| Encounter deck | The Mythos phase's encounter deck (§8.5) |
| Outcomes Good / Neutral / Bad, cascade into next scenario | Resolutions and the campaign log (§8.6) |
| XP upgrades Standard→Prototype→Prime | The XP upgrade path at rest locations (§13.2) |

Highcard Set 001 (INVA) has 20 cards: 12 weapons, 3 equipment, 3 auras, and 2 actions. None of them is
Kinetic, so the Kinetic demo deck combines the neutral Highcard cards that suit an aggressive Hunter with
new Kinetic cards written for Queen. Every card names its source (`set`: `INVA` or `QUEEN`) in the data.

Highcard is not fully designed yet. Queen is a place to explore its theme: Hunters, the Invasion, five
elements, weapons with dice and durability, and the two clocks. Queen keeps those as its identity. Where
Highcard is undecided, Queen makes a choice and writes it down (§5.2), so the decisions can flow back into
Highcard if they work.

### 5.1 Tailoring Highcard to solitary play

Highcard is a co-op tabletop game for 1–4 players. Many of its rules exist because of the table: shared
turns, physical bookkeeping, and group talk. A solo digital game needs different answers.

| Tabletop rule | Why it exists at the table | Solo digital answer in Queen |
| --- | --- | --- |
| 1–4 Hunters, each with a deck | Social play, role split (fighter, investigator) | One Hunter. Their deck must cover both roles, so skill icons and Survey cards matter more (§9.3). |
| Turn order: all players, then the enemy phase | Each player waits for the others | One Hunter. The enemy phase follows every turn, so the pace is StS-like. |
| Draw to 7, energy ramps 1, 2, 3… | Long games and few turns; hands are refilled by hand | Draw 5, flat 3 energy, discard the hand (StS). The computer does the shuffling and the counting. |
| 2 actions per turn (Move, Attack, Survey, Prepare, Activate) | Action economy on a shared board | Split in two. Exploration uses 3 AHLCG actions per round. In battle, cards are the actions, paid for with energy. |
| Allies act in an Allies phase | Board presence for a group | Post-slice (§19). A solo player has one board, so Allies would be Snap-style slots. |
| Encounter deck triggers on a d6 roll | No referee to choose | The Mythos phase draws every round; agenda flips raise the number drawn. The computer is the referee. |
| Scenario numbers scale with player count | Fairness at any table size | Tuned for one Hunter. Difficulty comes from the Hive Bag and the agenda thresholds instead. |
| Group discussion of the plan | The fun of co-op | Replaced by perfect information: visible intents, damage previews, odds on every test. |
| Dice rolled by hand, bonuses added up by hand | Tactile fun, but slow and error-prone | The dice are animated and the maths is automatic. Focus rerolls give back the player's agency. |
| Campaign log written on paper | Persistence between sessions | Saved automatically, and story cards read it. |
| Loot deck size by player count (10/14/20) | Group size | One pool for one Hunter. Loot becomes card rewards and relics. |

**Rule for future changes:** keep Highcard's **nouns** (Hunters, elements, weapons, auras, relics, entropy,
discovery, tiers, keywords) and its **tensions** (combat against discovery, durability as a clock, swingy
against consistent weapons). Change its **procedures** whenever the table is the only reason for them.

### 5.2 Decisions Queen makes for Highcard

These are open in Highcard. Queen chooses an answer for the prototype and records it here.

- **The five elements' solo roles.** Each element's Hunter must cover both clocks alone. Kinetic is weak at
  discovery, so a Kinetic deck gets clues mainly from killing clue-carrying enemies and from Recon cards.
- **What entropy does during combat.** It ticks every 3 battle rounds, so a slow fight costs time.
- **Weapon durability across scenes.** It persists between battles in a run (§10.3).
- **Fate** (Highcard's undefined micro-resource) is not used. Kinetic's **Focus** fills a similar role for
  this element.

---

## 6. The synthesis: how Queen plays

### 6.1 The core loop

```
          ┌─────────────────────── EXPLORE (AHLCG) ───────────────────────┐
          │  Round = 3 actions: Move · Investigate · Rest · Location action │
          │  After 3 actions → MYTHOS: +1 entropy, draw an encounter card  │
          └───────────────┬───────────────────────────────┬───────────────┘
                          │ enemy here / encounter spawns │ story card / reveal
                          ▼                               ▼
          ┌──────── BATTLE (StS) ────────┐      ┌──── STORY (AHLCG) ─────┐
          │ 3 energy · draw 5 · intents  │      │ text + choices         │
          │ Fire = dice through weapon   │      │ skill test (Hive Bag)  │
          │ every 3 rounds → +1 entropy  │      │ writes campaign log    │
          └──────────────┬───────────────┘      └───────────┬────────────┘
                         ▼                                  │
          ┌──── REWARD (StS) ────┐                          │
          │ pick 1 of 3 / skip   │◄─────────────────────────┘
          │ clues, scrip, XP     │
          └──────────┬───────────┘
                     ▼
     Act advances on clues ─── Agenda advances on entropy ─── Act 3: the Queen
```

### 6.2 The two clocks in numbers (slice tuning; the data is the source of truth)

- **Discovery (clues).** You need 4 clues for Act 1, 5 for Act 2, and Act 3 needs the Queen dead. Clues come
  from Investigate, from enemies that carry them, from story choices, and from Survey cards in battle.
- **Entropy (doom).** +1 each Mythos phase (every 3 actions), +1 every 3 battle rounds, and more from
  encounter cards and some enemies. Agenda thresholds are 6, 7 and 6. The final agenda flipping means the
  Queen wakes (the Bad resolution path, §8.6).
- **Expected run.** About 20 to 30 exploration actions, 4 to 6 battles including the Queen, and 25 to 40
  minutes in total. This fits a phone session, and it matches Highcard's 20–45 minute scenarios.

### 6.3 How the inspirations divide

| Layer | Owner | Why |
| --- | --- | --- |
| Moment-to-moment combat | StS | Readable, tactical, proven on touch (StS mobile) |
| Damage randomness | Highcard dice | Theme identity; Kinetic crits are the fun |
| Pacing and pressure | AHLCG doom + Highcard entropy | Time as a resource connects explore and battle |
| Map | AHLCG locations | Hand-made, story-bearing, small enough for a phone |
| Narrative | AHLCG act/agenda flips, encounter cards, resolutions, campaign log | Story as a system |
| Deck growth | StS rewards + AHLCG XP | The user chose "both": fast picks in the run, deliberate upgrades at rests |
| Out-of-battle randomness | AHLCG chaos bag | Difficulty and theme in one place |
| Feel | Marvel Snap | Tactile cards on a portrait phone |

---

## 7. Setting and story

### 7.1 Premise

The Invasion (Highcard Set 001) has a source: a living hive-ship called the **Sovereign** in low orbit. Its
brood rains down on the cities, and every night more of the sky goes dark. The Hunters' intelligence cell
has learned that the hive has one mind, the **Queen**. She is dormant, and she is growing. When she wakes
fully, the brood will no longer need the ship.

**Rook**, a Kinetic Hunter, rides a boarding pod into the Sovereign's hull alone. The mission is regicide.

### 7.2 Tone

Cosmic body-horror in space, told in short, clipped transmissions. The hive is organic: wet walls, choirs of
clicking, rooms that breathe. Rook is dry and tired, and they never waste words. Each story card has 1–3
short paragraphs (no more than 280 characters each) so it reads on a phone without scrolling.

### 7.3 Characters

- **Rook** — the Hunter. Kinetic, ex-security contractor, callsign from the chess piece that guards the
  king. Signature card: *Breach Charge*. Signature weakness: *Tormented Dreamscape* (the Highcard weapon
  curse: a weapon that hurts its wielder).
- **Handler "Lantern"** — a voice on the comms. She supplies exposition, and her signal decays as the
  agenda advances. On Agenda 3 her messages arrive garbled.
- **The Queen** — never speaks in words. She appears as text that intrudes into the UI (screen tint,
  scrambled letters in story cards) as entropy rises.

### 7.4 Scenario 1: "The Sovereign" (the slice)

**Act deck**

| Act | Name | Requirement | Flip (back) |
| --- | --- | --- | --- |
| 1a | Breach | 4 clues | "The walls remember the shape of a corridor. Lantern finds it in the noise." Reveals *Throne Approach*. Adds 1 Brood token to the bag. |
| 2a | The Path Inward | 5 clues | "The Approach opens like a throat. Something enormous breathes beyond it." Unlocks *Queen's Chamber*. |
| 3a | Regicide | Defeat the Queen | Resolution (§8.6). |

**Agenda deck**

| Agenda | Name | Threshold | Flip (back) |
| --- | --- | --- | --- |
| 1a | She Dreams | 6 entropy | "A pulse runs through the hull. Every egg in the Nursery turns toward you." All enemies gain +2 max HP for the rest of the run. Spawns a *Stalker* at the Nursery. |
| 2a | The Choir Wakes | 7 entropy | "Lantern's voice breaks into static. The singing is inside the comms now." Mythos phases draw two encounter cards. Lantern's story text is garbled. |
| 3a | Coronation | 6 entropy | "She opens her eyes." The Queen wakes: go to the Queen's Chamber with an Awakened Queen (phase 2 from the start), or flee for the Bad resolution. |

**Locations** (the slice map, §8.3)

```
                  [Queen's Chamber]          (locked until Act 2 flips)
                         │
                  [Throne Approach]          (hidden until Act 1 flips)
                  ╱               ╲
        [Echo Archive]        [Brood Nursery]
              │      ╲         ╱      │
              │     [Feeding Chamber] │
              │           │           │
        [Spore Gallery]───┴───[Husk Barracks]
                    ╲         ╱
                    [Breach Point]           (start)
```

| Location | Shroud | Clues | On reveal / special |
| --- | --- | --- | --- |
| Breach Point | 1 | 0 | Start. *Rest* action: heal, or spend XP on upgrades, once per Agenda. |
| Spore Gallery | 2 | 2 | Reveal: a story card, *The Gardens* (a choice that tests Willpower). |
| Husk Barracks | 2 | 1 | Reveal: the elite *Husk Captain* (a battle). It carries 1 clue. |
| Feeding Chamber | 2 | 2 | Forced: on entering, take 1 Horror unless you pass a Willpower (2) test. |
| Echo Archive | 4 | 3 | Action: *Listen* (Intellect 3): read Lantern's decoded log; gain 1 clue and a campaign log entry. |
| Brood Nursery | 2 | 2 | Reveal: 3 Brood Eggs (a battle where eggs hatch over time). Burning the eggs (story choice) changes R1 text. |
| Throne Approach | 3 | 2 | Rest action (the second rest point). An elite guards it: *Choir Warden*. |
| Queen's Chamber | — | — | The boss battle: *The Queen*. |

**Resolutions**

| Resolution | Condition | Outcome |
| --- | --- | --- |
| R1 — Good | Queen defeated with entropy ≤ 12 (during Agenda 1 or 2) | "The hive screams with one voice, then none." +3 XP. Log: `queen_slain`, `clean_kill`. |
| R2 — Neutral | Queen defeated during Agenda 3 | "She dies awake. You hear the brood scatter into the dark." +2 XP. Log: `queen_slain`, `brood_scattered`. Next scenario starts at +2 entropy. |
| R3 — Bad | Agenda 3 flips and you flee, or you lose to the Awakened Queen | "The Sovereign turns toward the planet." +1 XP. Log: `queen_awake`. Next scenario at +4 entropy. Rook takes 1 mental trauma. |
| Defeat | Health or Nerve reaches 0 outside the Queen fight | "Lantern keeps calling your name." +1 XP. Log: `rook_lost`. Trauma by cause. |

The encounter deck, enemies and story card texts are in `queen/data/scenarios/sovereign/` (§16.4).

---

## 8. The run: scenario, acts, agendas, locations

### 8.1 Run state

A run holds: the Hunter (health, max health, nerve, max nerve, skills), the deck (the card list with
upgrade levels), relics, scrip, unspent XP, clues held, the current location, the location states (revealed,
clues left, enemies present), the act index, the agenda index and entropy on it, the encounter deck and its
discard, the Hive Bag contents, the action count this round, and the campaign log.

### 8.2 Exploration actions (3 per round)

| Action | Cost | Effect |
| --- | --- | --- |
| **Move** | 1 action | Go to a connected, unlocked location. First entry reveals it (its reveal effect runs). |
| **Investigate** | 1 action | Intellect test against the location's shroud. On success, take 1 clue from the location. |
| **Rest** | 1 action | Only at a location with a Rest action, once per Agenda. Choose: heal 30% of max health, recover 2 Nerve, or spend XP (§13.2). |
| **Location action** | as printed | For example *Listen* at the Echo Archive. |
| **Advance** | 0 actions | When you hold enough clues, spend them to flip the Act. This is free, as in AHLCG. |
| **Deck** | 0 actions | View the deck, relics, log and bag. This is free. |

Clues are held by the Hunter and spent on the Act (AHLCG's "spend clues as a group" rule, for one player).

### 8.3 Locations

Each location record gives its name, art key, map position, connections, shroud, clue count, reveal handler
and params, forced handlers (on enter, on investigate), actions, and the conditions to unlock it. Locations
start face-down: you see the name and the connections, but not the shroud, clues or art. **Locked**
locations show a lock icon and their unlock text.

### 8.4 Enemies on the map

- An encounter card or a reveal can put an enemy group at a location.
- **Entering a location with enemies** starts a battle with that group at once (AHLCG: the enemy engages
  you).
- **Evade** (an action): an Agility test against the group's evade value. On success, you may take your
  next action as if they were not there. They stay, though, and **Hunter** enemies follow you on the next
  Mythos phase.
- When you win a battle the group is gone. Its clues drop to you, and you get the battle rewards.

### 8.5 The Mythos phase

After every 3 actions:

1. +1 entropy on the current agenda. If the threshold is met, the agenda flips (§7.4).
2. Draw the top encounter card and resolve it. Card types:
   - **Enemy**: spawn a group at your location (a battle starts) or at a named location.
   - **Treachery**: a bad effect, often with a skill test to reduce it (for example *Spore Bloom*: a
     Willpower 3 test, or add 2 *Spore* cards to your deck for the next battle).
   - **Story**: a short scene with a choice. These are the "?" events of StS.
3. *Hunter* enemies move one location toward you.
4. The round counter resets.

When the encounter deck runs out, shuffle its discard back in and add 1 entropy (AHLCG).

### 8.6 Resolutions and the campaign log

- The scenario ends at a resolution (§7.4). The resolution screen shows its text, XP earned (resolution
  XP plus victory points), trauma, and the campaign log entries it wrote.
- The **campaign log** is a flat `{key: value}` map (flags and counters). Story choices, location actions
  and resolutions write to it. Conditions in data can read it (`{"log": "eggs_burned"}`). It is saved
  between runs and shown on the title screen as the "Hunter's dossier".
- Starting entropy for the next scenario follows Highcard's cascade (Good 0, Neutral +2, Bad +4).

---

## 9. Skill tests and the Hive Bag

### 9.1 Skills

Rook's skills are Willpower 3, Intellect 2, Combat 4, and Agility 3. **Combat** also sets the base dice
pool in battle (§10.4). Skill tests are used **outside battle**: Investigate, Evade, treacheries, story
choices, and location actions.

### 9.2 The Hive Bag

A test is `skill + committed icons + token ≥ difficulty`. The token comes from the **Hive Bag**.

| Token | Standard bag | Effect |
| --- | --- | --- |
| +1 | 1 | +1 |
| 0 | 2 | 0 |
| −1 | 3 | −1 |
| −2 | 2 | −2 |
| −3 | 1 | −3 |
| −4 | 1 | −4 |
| **Brood** (skull) | 2 | −1, or −2 if an enemy is at your location (scenario-defined) |
| **Choir** (cultist) | 1 | −2. If you fail, take 1 Horror. |
| **Crown** (tablet) | 1 | −3. If you fail, +1 entropy. |
| **Auto-fail** (tentacle) | 1 | You fail. |
| **Elder Sign** (Hunter) | 1 | +2, and Rook's ability: draw 1 card into your next battle's opening hand. |

The bags for Easy, Standard, Hard and Expert are in `data/hive_bag.json`. Scenario symbol effects are in the
scenario's `scenario.json`. Act and agenda flips and campaign log entries can add or remove tokens.

**The test screen.** The draw is the drama, so it gets a full-screen moment. The bag shakes, a token slides
out and flips, and then the total counts up to pass or fail. The modified skill value and the odds of
success are shown before you draw (§14.6).

### 9.3 Committing cards

Before drawing, you can commit cards from a 5-card **test hand** drawn from your deck. Each committed card
adds its skill icons to the matching skill (Willpower, Intellect, Combat, Agility, or Wild; shown as coloured
pips on the card). Committed cards are **fatigued**: they start the next battle in the discard pile, so you
will not draw them until the first reshuffle. **Design intent:** your battle deck doubles as your
exploration toolkit, so building for combat has a cost. This is AHLCG's commit tension.

---

## 10. Battle

### 10.1 Setup

- The enemy group is placed (one to four enemies, left to right).
- Your deck is shuffled into the draw pile. *Innate* cards go to the top.
- Equipped Weapon and Equipment from the run carry into the battle (§10.3).
- Each enemy rolls its first intent.
- Turn 1 begins.

### 10.2 Turn structure

**Player turn**

1. Shields drop to 0 (unless *Retain Shields*).
2. Start-of-turn triggers (Auras, relics, statuses).
3. Gain 3 energy (the base from `data/rules.json`).
4. Draw 5 cards (hand limit 10; overflow is discarded).
5. Play cards in any order, until you choose **End Turn**.
6. End-of-turn triggers. Ethereal cards exhaust. The rest of the hand is discarded, except *Retain* cards.

**Enemy turn**

1. Each enemy, left to right, carries out its intent.
2. Enemy statuses tick down.
3. Each enemy rolls its next intent.
4. The battle round counter goes up. Every 3 rounds (`entropy_every_rounds`), +1 entropy (the agenda
   can flip mid-battle; its flip text shows as a banner and the effect applies at once).

**End.** You win when all enemies are dead (some enemies, such as Eggs, must be destroyed and do not count
as escaping). You lose when your health reaches 0. A Nerve of 0 makes you *Panicked*: you draw 1 fewer card
each turn until the battle ends. Nerve loss does not end a battle, because horror is the exploration threat.

### 10.3 Weapons and durability

- You have one **Weapon** slot. Playing a Weapon card equips it. The old weapon goes to the discard pile.
- A Weapon sets: **bonus dice**, **hit target** (default 5, meaning 5–6 hit), **damage per hit**, **crit**
  (6s count as 2 hits), **ammo** (Highcard's durability), and an optional **special** (a named handler: for
  example *December Remembrance*: "if at least 1 hit, deal 12 damage instead").
- **Ammo** is Highcard's durability, per battle. Each **Fire** uses 1. At 0 the weapon is **spent**: it is
  exhausted for the rest of this battle, and you fire Bare Hands until you equip another. Ammo refills at
  the start of every battle, and the last weapon you held stays equipped. Playtests showed that
  permanent breakage left a Hunter with Bare Hands after one fight, which no StS-length run survives.
  *Repair N* cards (Field Strip, Combat Reload) reload ammo mid-battle.
- With no weapon you fire **Bare Hands**: +0 dice, hit target 5, 2 damage per hit, no ammo.
- Rook starts with *RTX Special 00* equipped (Highcard: +1 attack, hits deal double damage; ammo 6).

### 10.4 Fire: the dice roll

A card with a **Fire** effect rolls `Combat (4) + weapon bonus + card bonus + status modifiers` dice.

- Each die that meets the hit target is a **hit**. A 6 on a Crit weapon is a **crit** (2 hits).
- Damage = hits × weapon damage per hit (+ Momentum), then Exposed/Weakened, then the target's shields.
- **Preview.** While you drag a Fire card over an enemy, the card shows the pool ("6d6 · 5+"), the expected
  damage ("≈ 4") and the chance to kill ("Kill 38%"). The enemy's HP bar shows a ghost of the expected
  damage. This keeps StS-style planning possible with dice.
- **Dice presentation.** The dice tumble on the battlefield for 0.4 s, then settle. Hits glow, crits flash
  yellow, misses dim, and then the damage number pops.
- **Focus** (a Kinetic status): each Focus rerolls one missed die, at once and in order, then is spent. The
  rerolled dice are outlined in the tray. Focus lasts until the battle ends. Kinetic's agency over luck is
  *when* to bank Focus (Steady Aim, Rook's crit chain). Rerolls are automatic, so a turn never stops for a
  prompt.

### 10.5 Shields, damage, health, nerve

- **Shields** absorb damage first and drop to 0 at the start of your turn.
- **Damage** reduces health. Health carries between battles.
- **Horror** reduces nerve. Some enemy intents are Horror attacks (purple), and they ignore shields unless a
  card says it blocks horror.

### 10.6 Statuses

Statuses are records in `data/statuses.json`. Their behaviour is a named hook in `rules/statuses.py`.

| Status | On | Effect | Ticks |
| --- | --- | --- | --- |
| **Momentum** | Hunter/Enemy | +1 damage per hit per stack (StS Strength) | No |
| **Exposed** | Enemy/Hunter | Attacks against it hit on 4+ instead of 5+ (Vulnerable for dice) | −1 per turn |
| **Shaken** | Hunter/Enemy | −1 die per stack on Fire (Weak for dice); enemies deal −25% | −1 per turn |
| **Brittle** | Hunter | −25% shields gained (StS Frail) | −1 per turn |
| **Focus** | Hunter | Reroll tokens (§10.4) | Reset per battle |
| **Bleed** | Enemy/Hunter | Lose N health at the end of turn, then −1 | −1 per turn |
| **Guard** | Enemy | Must be targeted first (Highcard Guard) | No |
| **Pre-empt** | Enemy | Acts before your first turn (Highcard Pre-empt) | Removed after |
| **Brood** | Enemy (Egg) | At N, hatches into the named enemy | Counts down |
| **Panicked** | Hunter | Draw 1 fewer card | Until battle end |

### 10.7 Card play rules

- **Targeted cards** (Fire at an enemy, or a debuff): drag onto an enemy. Release on a valid enemy to play.
- **Untargeted cards** (shields, draw, auras, weapons): drag above the **play line** (40% from the bottom)
  and release.
- **Keyboard/gamepad:** Left/Right selects a card, Up inspects it, A plays it (a targeted card asks for a
  target: Left/Right, then A), and B cancels. **End Turn** is C. Every pointer action has a button path
  (NightEngine rule).
- A card you cannot afford is dimmed, and it shakes if you try to play it.

### 10.8 Rewards after battle

- Normal battle: clues carried by the enemies, scrip 10–20, and a card reward (choose 1 of 3, or skip).
- Elite: the above, plus a Relic (a choice of 1 from 2), plus 1 XP.
- The Queen: the resolution.

---

## 11. Cards

### 11.1 The Hunter: Rook (Kinetic)

| Field | Value |
| --- | --- |
| Element | K (Kinetic) |
| Health / Nerve | 70 / 7 |
| Skills | Willpower 3, Intellect 3, Combat 4, Agility 3 |
| Starting relics | Lantern's Beacon, Field Medkit (heal 6 after a won battle) |
| Starting weapon | RTX Special 00 |
| Ability | **Kinetic Chain:** the first time each turn you score a crit, gain 1 Focus. |
| Elder Sign | +2. The next battle's opening hand draws 1 extra card. |
| Signature card | *Breach Charge* |
| Signature weakness | *Tormented Dreamscape* |

### 11.2 Starter deck (12 cards)

| Card | Count | Cost | Type | Text |
| --- | --- | --- | --- | --- |
| Fire | 4 | 1 | Action | Fire. |
| Brace | 4 | 1 | Action | Gain 5 Shields. |
| Breach Charge | 1 | 2 | Action (signature) | Fire with +2 dice. Exposed 2. |
| Survey | 1 | 1 | Action | Draw 1. Recon: if this is your first card this turn, gain 1 clue. Exhaust. |
| 101 Nights | 1 | 1 | Weapon (INVA) | +1 die, hits on 4+. 3 damage per hit. Ammo 6. |
| Tormented Dreamscape | 1 | 0 | Weapon (INVA, weakness) | When drawn, it equips itself. +3 dice, 2 damage per hit. On hit, your Shields become 0. Ammo 6. |

The basic Fire and Brace cards (StS Strike and Defend) are there to be removed or upgraded. This is
deliberate: card removal is the long-term goal of a StS deck.

### 11.3 The Kinetic reward pool (slice: 24 cards)

The tables below give the design intent. **The numbers in `queen/data/cards/` are the source of truth**;
when they differ, the data wins. Costs use StS scale (Highcard cost ÷ 2, rounded). Tiers: S = Standard (common), P = Prototype (uncommon),
X = Prime (rare). The full records are in `data/cards/*.json`.

| Card | Set | Tier | Cost | Type | Text |
| --- | --- | --- | --- | --- | --- |
| Double Tap | QUEEN | S | 1 | Action | Fire. Fire again with −1 die. |
| Quick Draw | QUEEN | S | 0 | Action | Fire with −2 dice. Rush: draw 1. |
| Steady Aim | QUEEN | S | 1 | Action | Gain 2 Focus. Draw 1. |
| Suppressing Fire | QUEEN | S | 1 | Action | Fire. Shaken 1. |
| Kinetic Barrier | QUEEN | S | 1 | Action | Gain 4 Shields. Gain 1 Momentum this turn. |
| Field Strip | QUEEN | S | 1 | Action | Repair your weapon by 2. Draw 1. |
| Combat Reload | QUEEN | S | 0 | Action | Repair your weapon by 1. Retain. |
| Ricochet | QUEEN | S | 1 | Action | Fire at a random enemy 2 times with −2 dice. |
| RTX Special 00 | INVA | S | 1 | Weapon | +1 die, 2 damage per hit, doubled. Ammo 6. |
| 101 Nights | INVA | S | 1 | Weapon | +1 die, hits on 4+, 3 damage per hit. Ammo 6. |
| Stand Behind Me | INVA | S | 1 | Action | Prevent the next 6 damage this turn (does not drop at turn start). |
| Hunter's Mark | QUEEN | P | 1 | Action | Exposed 2. Momentum +1 against this enemy. Exhaust. |
| Adrenal Spike | QUEEN | P | 0 | Action | Gain 2 energy. Take 3 damage. Exhaust. |
| Overclock | QUEEN | P | 1 | Aura | Your weapon's crits deal triple damage. |
| Crit Chain | QUEEN | P | 2 | Aura | Each crit draws a card. |
| Point Blank | QUEEN | P | 2 | Action | Fire with +3 dice. Costs 1 less if the target is Exposed. |
| Impossible Scenario | INVA | P | 1 | Action | Fire. If 0 hits, count 2 hits instead. |
| Gravitas Cannon | INVA | P | 2 | Weapon | +0 dice. On hit, deal 10 damage instead of the hit damage. Durability 3. |
| RXX Auto-loader Holster | INVA | P | 2 | Equipment | The first Fire each turn fires twice. Durability 5 (uses). |
| Forgetfulness | INVA | X | 2 | Weapon | +2 dice. If exactly one 6, deal 6 damage instead of 1. Crit. Durability 3. |
| December Remembrance | INVA | X | 2 | Weapon | +1 die. If at least 1 hit, deal 5 damage. Durability 3. |
| Last Round | QUEEN | X | 1 | Action | Fire with dice equal to twice your weapon's durability, then break it. |
| Execute | QUEEN | X | 2 | Action | Fire. If the enemy has less than 30% HP after, it dies. Exhaust. |
| Buster Exoskeleton | INVA | X | 2 | Equipment | Damage to you is reduced to 1. If it would kill you, destroy this instead. Durability 5. |

### 11.4 Card types and keywords

| Type | Behaviour |
| --- | --- |
| **Action** | Played from hand, resolves, goes to the discard pile (StS Skill/Attack). |
| **Weapon** | Equips into the weapon slot (§10.3). |
| **Equipment** | Goes into an equipment slot (2 slots). Persists between battles. Some have uses. |
| **Aura** | Stays in play until the battle ends (StS Power). |
| **Trauma** | Permanent curse. Unplayable unless it says otherwise. |
| **Spore** | Battle-only junk added by enemies. Ethereal. |

| Keyword | Meaning |
| --- | --- |
| **Fire** | Roll an attack with the equipped weapon (§10.4). |
| **Exhaust** | Remove from the battle after play. |
| **Retain** | Not discarded at end of turn. |
| **Ethereal** | Exhausts if in hand at end of turn. |
| **Innate** | Starts in the opening hand. |
| **Rush** (Highcard) | An extra effect if this is played as the first card of the turn. |
| **Recon** (Highcard) | Look at or gain information, or a clue, under the stated condition. |
| **Crit** (Highcard) | 6s count as 2 hits. |
| **Repair N** | Restore N durability to the weapon. |
| **Weakness** | Cannot be removed. Has a forced effect when drawn. |

### 11.5 Skill icons

Each card has 0–2 skill icons for committing to tests (§9.3). Kinetic cards lean toward Combat and Agility.
Survey and Field Strip carry Intellect. This gives the deck a reason to keep utility cards.

---

## 12. Enemies and intents

### 12.1 Intents

| Intent | Icon | Shows |
| --- | --- | --- |
| Attack | red blade | Damage (× hits). If the enemy rolls, a range "3–9". |
| Horror | purple eye | Nerve damage. |
| Defend | blue shield | Shields gained. |
| Buff | orange up-arrow | Status name on hold. |
| Debuff | green spiral | Status name on hold. |
| Summon/Spawn | pink egg | What it spawns. |
| Hatch | pink crack | Rounds until it hatches. |
| Unknown | grey ? | The Queen phase 2 only. |

### 12.2 Bestiary (slice)

| Enemy | Art | HP | Pattern (behaviour script) | Notes |
| --- | --- | --- | --- | --- |
| **Drone** | OneBitPudding monster 1 | 10–12 | `cycle`: Bite 5 → Bite 5 → Screech (Shaken 1) | Common filler. Carries 0 clues. |
| **Spitter** | OneBitPudding monster 4 | 18–20 | `weighted`: Acid 4 + Bleed 2 (60%), Harden 6 shields (40%); no repeat x3 | |
| **Husk** | Warped City cop (recoloured) | 24 | `cycle`: Rifle 3×2 → Brace 8 → Rifle 3×2 | Fallen Hunters. Guard. |
| **Husk Captain** (elite) | cop, larger | 40 | `cycle`: Rally (all Momentum +2) → Volley 4×3 → Dig In 12 | Carries 1 clue. Guards the Barracks alone. |
| **Brood Egg** | OneBitPudding monster 2 | 10 | `hatch`: Brood 3 → hatches into a Drone | Does not attack. |
| **Spore Slug** | OneBitPudding monster 7 | 9–11 | `cycle`: Spore (adds a Spore card) → Nibble 4 | |
| **Stalker** | OneBitPudding monster 3 | 30 | `stalker`: Pounce 12 if your shields < 5, else Lurk (Exposed on you) | Hunter keyword on the map. |
| **Choir Warden** (elite) | OneBitPudding monster 8 | 60 | `cycle`: Hymn (Horror 2, all enemies +4 shields) → Lash 10 → Lash 10 | Guards Throne Approach. |
| **The Queen** (boss) | OneBitPudding monster 3 at 2× + palette shift | 140 | `queen` phases (below) | |

**The Queen.** Phase 1 *Dreaming* (until 50% HP): Brood Pulse (summon 1 Egg) → Psychic Lash (Horror 2, 8
damage) → Carapace (15 shields). Phase 2 *Awakened*: intents show as "?" for the first round, then Crown of
Spines (14), Choir Scream (Horror 3, Shaken 2 to you), Devour (heals 10 if a Drone is alive, and kills it).
If Agenda 3 flipped, she starts in phase 2 with +40 HP.

---

## 13. Progression: rewards, XP, upgrades, trauma

### 13.1 Card rewards (StS)

After a battle, the game offers 3 cards from the Hunter's element pool plus neutral cards. The weights are
Standard 60%, Prototype 33% and Prime 7%. Each reward without a Prime adds +1% to the Prime chance (the pity
counter, reset when a Prime appears). **Skip** is always offered. Weights live in `data/rules.json`.

### 13.2 XP and upgrades (AHLCG and Highcard)

- XP sources: elites (+1), Echo Archive *Listen* (+1), the resolution (+1 to +3), and enemy victory points.
- Spend XP at a Rest action, or on the resolution screen for the next run:

| Upgrade | XP | Effect |
| --- | --- | --- |
| Standard → Standard+ | 1 | The card's `plus` record (StS upgrade: more damage, less cost, or a keyword) |
| Standard+ → Prototype | 2 | Becomes its named Prototype version, if one exists (`upgrades_to`) |
| Prototype → Prime | 3 | Becomes its named Prime version, if one exists |
| Remove a card | 2 | Remove a non-weakness card from the deck |

### 13.3 Relics (slice: 5)

| Relic | Source | Effect |
| --- | --- | --- |
| Lantern's Beacon | Start | Once per Agenda, a Mythos phase adds no entropy. |
| Spent Casing | Elite | Start each battle with 1 Focus. |
| Hive Lens | Elite | Enemies start battles Exposed 1. |
| Chitin Plate | Elite | Start each battle with 6 Shields. |
| Crown Shard | Story | +1 to all skill tests. At the start of each battle, take 1 Horror. |

### 13.4 Trauma

- Physical trauma: −1 max Health per point (×5) at the start of each future run.
- Mental trauma: −1 max Nerve per point.
- Some resolutions and story choices add a Trauma card (*Shaken, Also Stirred*: −1 die on Fire while in
  your hand; *Remembrance of All Traumas*: you cannot gain clues while it is in play).

---

## 14. Screens, layout and touch controls

### 14.1 Resolution and scaling

- **Logical screen 320 × 714, portrait.** The Pixel 10 Pro is 1280 × 2856, so this is an exact 4× integer
  scale with no letterbox. On other phones the WebView shell scales to fit (NightEngine `launcher.mjs`).
- **Safe area.** Keep text and touch targets 12 px from the top (status bar and camera) and 16 px from the
  bottom (gesture bar). Rules use `config.SAFE_TOP` and `config.SAFE_BOTTOM`.
- **Thumb zone.** Primary actions are in the bottom 45%. The top 15% is read-only info.
- **Minimum touch target:** 24 × 24 logical px (6 mm on the Pixel 10 Pro).

### 14.2 Battle layout (320 × 714)

```
 y=0   ┌──────────────────────────────────┐
       │ ♥ 54/60  ✦ 6/7   ⚡ ENTROPY 4/6  │  top bar (HP, Nerve, agenda clock, act clues)
 y=28  │ Act 1 · Clues 2/4      [≡ deck] │
 y=48  ├──────────────────────────────────┤
       │   [intent]   [intent]  [intent]  │  intents float above enemies
       │    ╭───╮      ╭───╮     ╭───╮    │
       │    │ E │      │ E │     │ E │    │  enemies (up to 4), art 48–96 px
       │    ╰───╯      ╰───╯     ╰───╯    │
       │   ▓▓▓▓░ 12    ▓▓▓░ 9   ▓▓▓▓ 14   │  HP bars + statuses
 y=300 │                                  │
       │        · · dice tray · ·         │  dice roll here (center)
 y=380 │                                  │
       │  ROOK [art]   🛡 5   Focus ●●    │  hunter row: shields, statuses, focus
       │  ╭weapon╮ RTX 00  dur ▮▮▮▯        │  weapon slot + equipment + auras
 y=470 ├────────── play line ─────────────┤
       │ (3)⚡           [END TURN]  (7)↻  │  energy orb, end turn, draw/discard piles
 y=520 │   ╭────╮╭────╮╭────╮╭────╮╭────╮ │
       │   │card││card││card││card││card│ │  hand: cards 66×120, shallow arc
       │   │    ││    ││    ││    ││    │ │
 y=700 └──────────────────────────────────┘
```

- Hand cards are 66 × 120 at rest, so five sit side by side with only their frames overlapping. The face
  shows the name (two bold lines or three regular ones; a card whose name does not fit has a shorter
  `face` name), the type, and up to four short lines generated from the card's ops and weapon stats
  (`ui/cardtext.py`: "FIRE +2d", "Expose 2", "+1d hit4+"), never hand-written. `tests/test_content.py`
  checks that every face fits. The inspect view shows the face at 2×, the full name, the rules text and a
  line for each keyword. A lifted card rises at 1×; a dragged one grows to 1.25× over a target.
- The hand sits on a shallow arc with no tilt: rotated pixel text does not read. With more than 5 cards the
  overlap grows, and the touched card rises and pushes its neighbours away (StS). Every other card list
  (reward, deck, skill test) also draws cards at 1×.
- **Dice roll.** Each die is thrown from Rook's hand, tumbles and bounces three times with its face
  flickering (fast, then slower), and the dice land one after another. A hit flashes as it lands; the total
  shows when the last die is down. The faces are rolled by the rules first: the animation only shows them.

### 14.3 Battle gestures

| Gesture | Result |
| --- | --- |
| Touch a card in hand | It lifts (rises 36 px at 1×). A crowded hand spreads. |
| Drag | The card follows the finger with smoothing (lerp 0.35). It tilts with the x velocity (max 8°). For a targeted card, an arrow (StS) draws from the card to the finger, and enemies under the finger highlight with the damage preview. |
| Release over a target / above the play line | The card plays: slam, flash, resolve. |
| Release elsewhere | It springs back to the hand. |
| Hold 0.3 s without moving (card, enemy, status, relic) | Inspect overlay. Release closes it. |
| Tap an enemy or its intent | The enemy panel: its next move in words ("Deals 6 damage 2 times."), its other moves and its statuses. A tap closes it. Button path: UP with no card lifted, LEFT/RIGHT for the next enemy. |
| Tap END TURN | Ends the turn. A long press is not needed; a confirm appears only if energy and playable cards remain (a setting). |
| Tap the draw or discard pile | A pile viewer (a scrollable grid). |
| Swipe up on the pile viewer | Scroll. |

### 14.4 Exploration screen

The map fills the top 60%. Location nodes are 56 × 40 tiles with the location's art, connected by
organic "vein" lines. Your token is Rook's portrait. Below the map are the agenda and act cards (tap to read
the full card), and below those the action bar: **Move** (tap a connected node), **Investigate**, **Rest**,
the location action, and **Advance Act** (when it is available). Three action pips show the actions left
before the Mythos phase.

### 14.5 Story screen

A card-shaped panel with art at the top, then text that types out (tap to finish it at once), then 1 to 3
choice buttons at the bottom. A choice with a skill test shows the skill and the difficulty, for example
"[Willpower 3] Burn the eggs".

### 14.6 Skill test screen

The skill value, the difficulty and the success chance are shown first. Then the **Commit** strip shows the
test hand; tap cards to commit them. **Draw** pulls a token from the bag: the bag shakes, the token flips,
and the result counts up.

### 14.7 Other screens

The title (Continue, New Run, Dossier, Settings), the reward screen (3 cards, Skip), the rest screen
(Heal, Recover, Upgrade, Repair, Remove), the deck viewer, the resolution screen, and the pause menu.

---

## 15. Art, palette, font and audio

### 15.1 Direction

Dark, wet, violet-and-magenta hive interiors with sickly green highlights (spores, eggs, acid). Rook and
human tech are the only warm colours: orange, cream and steel. This makes the player instantly readable
against the alien background.

### 15.2 Third-party art (all CC0)

| Pack | Author | Use | Source |
| --- | --- | --- | --- |
| Pixel Sci-Fi Monster Animations | OneBitPudding | Hive enemies, the Queen, backgrounds, spore FX | https://opengameart.org/content/pixel-sci-fi-monster-animations |
| Warped City 2 | ansimuz | Rook (the player sprite), Husks (the cop), Brood Egg (egg turret), explosions | https://opengameart.org/content/warped-city-2 |
| Warped Sci-Fi Lab | ansimuz | The breach point and human-tech backgrounds | https://opengameart.org/node/133446 |
| 1-Bit Pack | Kenney | UI icons (intents, statuses, skills) | https://kenney.nl/assets/1-bit-pack |

`assets/art/README.md` lists every file with its source and licence. `queen/assets.py` lists each asset
with its source (`file` or `code`) and status (`placeholder` or `final`), as in Nightrunner.

### 15.3 Palette

Pyxel 2 supports more than 16 colours. Queen uses a **64-colour palette** in `data/palette.json`, built by
`tools/palette.py` from the art packs plus UI colours, and named (`void`, `hive_dark`, `flesh`, `spore`,
`bone`, `rook_orange`, `crit_yellow`, `horror_violet`, and so on). Imported PNGs are quantised to it by
`tools/import_art.py` at import time, so Pyxel's own nearest-colour mapping never surprises us at runtime.

### 15.4 Font

**Pixel Operator** (CC0, Jayvee Enaguas), a proportional pixel font, converted to BDF at its design sizes
(`assets/fonts/pixel-operator/`, `tools/import_font.py`). At the 4× phone scale one logical pixel is about
0.2 mm, so text needs a cap height of 9 px or more to read at arm's length:

- `m` (Pixel Operator 16, 13 px line, 9 px caps): the body font. Card rules, numbers, labels, buttons.
- `l` (Pixel Operator Bold 16): names, headings, intent and status numbers.
- `xl` (Pixel Operator Bold 32): banners and big numbers.
- `s` (Pixel Operator 8): only the type line on a card face. Never for anything the player must read to decide.

Pixel text is drawn at whole scales with no rotation; a scaled or rotated card face is only shown while it
moves. `ui/layout.py` reads the glyph widths from the BDF files, so layout and tests need no pyxel.

### 15.5 Audio

Code-generated chiptune effects (Pyxel note strings): card lift, card slam, dice rattle, hit, crit, block,
shield gain, enemy death, the bag shake and the token flip, the agenda flip sting, and the act flip sting.
Music: a low drone for exploration and a pulse loop for battle. Both are code-written. The Warped City 2
music (CC0, OGG) cannot be played by Pyxel directly, so it stays out of the build.

---

## 16. Architecture: data-driven content, mechanics as code

### 16.1 Principles (from Nightrunner)

1. **Data holds the numbers and the composition. Code holds the behaviour.** A card is a JSON record. Its
   effect is a list of **ops** (`{"op": "fire", "dice": 2}`). Each op is a small registered Python
   function. A card that needs more than ops can name a **custom handler**.
2. **Every name in data is checked.** Content tests check every op, handler, status, enemy, location, art
   key and story id with `check_refs` and `Registry.missing`. A typo fails with one clear message.
3. **Handlers get a narrow handle.** An op gets `ctx` (the battle or run API: `deal`, `gain_shields`,
   `draw`, `apply`, `rng`, `log`) and its params. It never gets the scene, the renderer or `pyxel`.
4. **The rules are pure and deterministic.** `queen/rules/` imports no `pyxel` and uses `game.rng` only. A
   battle can run headless in a test from a seed and a list of commands.
5. **Rules emit events, the renderer animates them.** Every state change also appends an **Event**
   (`Damage`, `Roll`, `Draw`, `StatusApplied`, …) to a log. The battle scene plays these events through
   a presentation queue with timing. The rules never wait.
6. **Shared first, then per scenario.** Shared cards, enemies and statuses live in `data/`. Content that
   only one scenario uses lives in `data/scenarios/<id>/` and `queen/scenarios/<id>.py`.

### 16.2 Layers

```
 game.py ──► queen/app.py (pyxel, host)           render/ (pyxel)   audio.py (pyxel)
                 │                                     ▲
                 ▼                                     │ reads state + events
            queen/game.py: QueenGame(Game) ── scenes/ ─┘
                 │                               │ commands (play card, end turn, move…)
                 ▼                               ▼
            queen/rules/  (pure: battle, explore, tests, run, rewards)
                 │  calls by name
                 ▼
            queen/mech/  (registered ops, behaviours, story handlers, conditions, hooks)
                 │  reads
                 ▼
            queen/content.py ◄── queen/data/*.json + data/scenarios/<id>/*.json
```

### 16.3 Registries (one engine `Registry` per kind)

| Registry | Key in data | Signature | Example |
| --- | --- | --- | --- |
| `OPS` | card `effects[].op`, story `effects[].op` | `fn(ctx, src, target, p)` | `fire`, `shield`, `draw`, `apply`, `energy`, `repair`, `clue`, `entropy`, `heal`, `horror` |
| `CARD_HANDLERS` | card `handler` | `fn(ctx, card, target)` | `last_round`, `execute` |
| `WEAPON_SPECIALS` | weapon `special` | `fn(roll, p) -> damage` | `december`, `forgetfulness`, `gravitas` |
| `BEHAVIOURS` | enemy `behaviour` | generator yielding intents | `cycle`, `weighted`, `phases`, `hatch`, `stalker`, `queen` |
| `INTENT_OPS` | intent `effects[].op` | `fn(ctx, enemy, p)` | `attack`, `horror`, `shield`, `buff`, `summon`, `spore` |
| `HOOKS` | status / relic / aura `hooks` | `fn(ctx, owner, p, event)` | `momentum`, `exposed`, `crit_chain`, `chitin_plate` |
| `CONDITIONS` | `if` fields everywhere | `fn(state, p) -> bool` | `log`, `entropy_at_least`, `first_card`, `target_exposed` |
| `STORY` | story/encounter `handler` | `fn(run, p)` | `spawn`, `test_or`, `choose` |
| `LOCATION` | location `on_reveal`, `on_enter`, `actions` | `fn(run, loc, p)` | `spawn_group`, `horror_test`, `listen` |

A designer adds a card with existing ops by writing JSON only. A new op is a function with
`@op("name")` in `queen/mech/ops.py`, plus its row in `docs/repo/content.md`.

### 16.4 Data layout

```
queen/data/
  rules.json            energy, draw, hand limit, entropy_every_rounds, reward weights, pity, XP prices
  palette.json          64 named colours
  hunters.json          ROOK: stats, starting deck, weapon, relics, ability hook, signature ids
  cards/
    core.json           basic cards (Fire, Brace, Survey) and neutral cards
    kinetic.json        K cards written for Queen
    inva.json           Highcard Set 001 cards (with `set: "INVA"`)
    traumas.json        curses and spores
  statuses.json         statuses: name, icon, stacking, decay, hooks
  relics.json           relics: hooks and params
  enemies.json          shared enemies: hp, art, behaviour, intents, carries_clues, vp
  hive_bag.json         token sets per difficulty
  scenarios/
    sovereign/
      scenario.json     name, start, acts, agendas, symbol token effects, resolutions, starting relic
      locations.json    the location graph
      encounter.json    the encounter deck (counts, types, handlers, params)
      story.json        story cards: text, choices, tests, effects
      enemies.json      scenario-only enemies (the Queen)
```

### 16.5 A card record

```json
"DOUBLE_TAP": {
  "name": "Double Tap", "set": "QUEEN", "element": "K", "tier": "S", "type": "action",
  "cost": 1, "target": "enemy", "art": "card_double_tap", "icons": ["combat"],
  "text": "Fire. Fire again with -1 die.",
  "effects": [{"op": "fire"}, {"op": "fire", "dice": -1}],
  "plus": {"text": "Fire. Fire again.", "effects": [{"op": "fire"}, {"op": "fire"}]}
}
```

`text` is the displayed rules text and is written by hand. A content test checks that every card has text,
and a `just cards` tool prints the cards from their ops so the text can be compared with the effect.

### 16.6 An enemy record and its behaviour

```json
"SPITTER": {
  "name": "Spitter", "hp": [18, 20], "art": "spitter", "behaviour": "weighted",
  "intents": {
    "ACID":   {"kind": "attack", "effects": [{"op": "attack", "damage": 4}, {"op": "apply", "status": "BLEED", "n": 2}]},
    "HARDEN": {"kind": "defend", "effects": [{"op": "shield", "n": 6}]}
  },
  "params": {"weights": {"ACID": 60, "HARDEN": 40}, "max_repeat": 2}
}
```

```python
@behaviour("weighted")
def weighted(e, p):
    """Pick an intent by weight. Never the same one more than max_repeat times in a row."""
    last, run = None, 0
    while True:
        pick = e.rng_choice_weighted(p.weights, exclude=last if run >= p.max_repeat else None)
        run = run + 1 if pick == last else 1
        last = pick
        yield pick
```

### 16.7 The battle engine

- `Battle` (state): hunter, enemies, piles (draw, hand, discard, exhaust), in-play auras, energy, round,
  phase, the weapon, an action queue, and the event log.
- **Action queue (StS).** Playing a card pushes its ops onto a queue. The engine pops and resolves them one
  by one. Hooks can push more ops (for example, a crit triggers Crit Chain's draw). This keeps the order of
  resolution clear and testable, and it prevents re-entrancy bugs.
- **Commands** are the only way in: `PlayCard(hand_index, target)`, `EndTurn()`, `Reroll(die)`.
  The scene turns gestures into commands. The autopilot and the tests send commands directly.
- **Events** are the only way out to presentation: `CardPlayed`, `Rolled(dice, hits, crits)`,
  `Damaged(target, amount, blocked)`, `ShieldsGained`, `StatusChanged`, `Drew`, `Discarded`,
  `IntentShown`, `EnemyDied`, `EntropyTicked`, `AgendaFlipped`, `BattleWon`, `BattleLost`.

### 16.8 Scaling up

- **More cards:** JSON only, for most cards. A content test makes sure every op exists, every param is
  known to its op (each op declares its params), and every card has text and art (or a placeholder).
- **More elements and Hunters:** a new `hunters.json` record and a `cards/<element>.json` file. Reward pools
  filter by the Hunter's element and neutral cards.
- **More scenarios:** a new folder under `data/scenarios/` plus an optional `queen/scenarios/<id>.py` for
  scenario-only handlers. The campaign file lists scenarios in order.
- **Balance tooling:** `tools/sim.py` (post-slice) plays N battles with the autopilot for each card or
  enemy, and reports win rate, turns, and damage taken, like Nightrunner's `just sim`.
- **Highcard import:** `tools/import_highcard.py` reads `../highcard/highcard/cards/*/*.yaml` and writes
  a draft `cards/inva.json` (names, tiers, rules text). A person then writes the ops. This keeps Queen in
  step with the Highcard card text.

### 16.9 Determinism and replays

- One seeded RNG (`game.rng`), split into named streams so that a change in one system does not reshuffle
  another: `rng.stream("deck")`, `"bag"`, `"dice"`, `"ai"`, `"rewards"`, `"encounter"`.
- All input goes through `Game.step` (buttons and pointers), so NightEngine records and replays it.
- Animations count frames in the scene, never wall-clock time, so a replay produces the same frames.

---

## 17. Testing and verification

- `tests/test_layers.py`: no `pyxel` import outside `render/`, `app.py`, `audio.py`, `frames.py`.
- `tests/test_content.py`: every reference resolves; every op's params are known; every card has text.
- `tests/test_battle.py`: dice maths, weapon specials, statuses, queue order, and intents, headless.
- `tests/test_explore.py`: actions, Mythos, act and agenda flips, skill tests with a fixed bag draw.
- `tests/test_run.py`: a full seeded run by the autopilot reaches a resolution without errors.
- `tests/test_touch.py`: a NightEngine `Driver` drags a card to an enemy with pointers and checks that
  the card was played.
- `just frames`: renders a replay to PNGs at 320 × 714 for visual review. pyxel-mcp `run` captures for
  agent checks.
- Every visual change is checked at the phone size (320 × 714, `--target android`).

---

## 18. Scope: the vertical slice and beyond

### 18.1 The slice (this milestone)

- Title → New Run → the Sovereign scenario, with the full act/agenda race on the 8-location map.
- Exploration with Move, Investigate, Rest, Evade, the location actions, and Mythos with an encounter deck of
  12 cards.
- Battles with all of §10: weapons, dice, Focus, statuses, intents, auras, equipment, the drag-and-drop hand,
  inspect, and the pile viewers.
- 6 enemies, 2 elites and the Queen (two phases).
- The starter deck plus 24 reward cards, 5 relics, and the Hive Bag with commit.
- Rewards, XP upgrades at rests, resolutions, and a campaign log that persists.
- Touch first at 320 × 714. Keyboard and gamepad work too.
- Android APK, web and desktop builds through NightEngine.
- Code-written sound effects and two music loops.

### 18.2 After the slice

- Scenario 2 (the hive's second ship, with the cascade from scenario 1), then scenario 3.
- More Hunters (one per element), Allies in Snap-style slots, and a Supply Cache shop with Scrip.
- Supplies (AHLCG) as potions.
- Ascension-like difficulty modifiers in data.
- Balance simulation (`just sim`).

---

## 19. Open questions

1. **Allies.** Highcard has Allies that act on their own each turn. A Snap-like row of 3 ally slots above
   the hand would fit the portrait layout. Is that worth adding after the slice?
2. **Energy ramp.** Highcard's energy grows each turn (1, 2, 3, …). The slice uses a flat 3 (StS). Should
   a ramping variant be tested?
3. **Nerve at 0 in battle.** The slice gives *Panicked*. Should it be harsher (a defeat)?
4. **Ammo.** Ammo refills every battle (§10.3). A harder variant: ammo carries between battles, and rests
   reload it.
5. **Run length.** The target is 25–40 minutes. A phone session may want 15–20. Shorter agendas could fix
   that.
