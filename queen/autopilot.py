"""The autopilot: plays a whole run by touch (taps and drags), so its recording replays exactly. No pyxel.

    uv run python -m queen.autopilot --seed 7 --out replays/auto-7.json

It plays simply: Investigate where there are clues, advance the act, head for the Queen, and in battle block what
is coming, then shoot the weakest enemy. It is for tests and recordings, not a strong player.
"""

from pathlib import Path

from nightengine import Target, autopilot
from nightengine.pointer import Pointer, PointerKind, PointerPhase

from .config import REPLAYS, H, W
from .content import CONTENT
from .game import QueenGame
from .rules import explore
from .ui import layout


def press(x, y, sx=None, sy=None, phase=PointerPhase.PRESSED):
    sx = x if sx is None else sx
    sy = y if sy is None else sy
    return (Pointer(1, int(x), int(y), int(sx), int(sy), phase, PointerKind.TOUCH),)


def tap(x, y) -> list:
    return [(0, press(x, y)), (0, press(x, y, phase=PointerPhase.RELEASED)), (0, ())]


def drag(x0, y0, x1, y1, frames=10) -> list:
    out = [(0, press(x0, y0))]
    for i in range(1, frames + 1):
        f = i / frames
        out.append((0, press(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, x0, y0, PointerPhase.MOVED)))
    out.append((0, press(x1, y1, x0, y0, PointerPhase.RELEASED)))
    out.append((0, ()))
    return out


def centre(rect):
    x, y, w, h = rect
    return x + w // 2, y + h // 2


class Pilot:
    def __init__(self):
        self.plan: list = []
        self.wait = 0

    def __call__(self, game):
        if self.plan:
            return self.plan.pop(0)
        if self.wait > 0:
            self.wait -= 1
            return 0, ()
        self.plan = self.decide(game) or []
        if not self.plan:
            self.wait = 4
            return 0, ()
        return self.plan.pop(0)

    def menu_tap(self, scene, pick=None) -> list:
        buttons = [b for b in scene.menu.buttons if b.enabled and b.style != "node"]
        if not buttons:
            return []
        b = pick(buttons) if pick else buttons[0]
        return tap(*centre(b.rect)) if b else []

    def decide(self, game) -> list:
        scene = game.scene
        name = type(scene).__name__
        if name == "Title":
            return self.menu_tap(scene, lambda bs: next((b for b in bs if b.value == "new"), None))
        if name == "StoryScene":
            if not scene.typed:
                return tap(160, 200)
            return self.menu_tap(scene, lambda bs: bs[0])
        if name == "TestScene":
            return self.menu_tap(scene) if scene.phase != "draw" else []
        if name == "Reward":
            if scene.card is None and scene.step["cards"]:
                from .scenes.reward import card_rects

                return tap(*centre(card_rects(len(scene.step["cards"]))[0]))
            return self.menu_tap(scene)
        if name == "Rest":
            run = game.run
            if not scene.rested:
                want = "heal" if run.hp < run.max_hp * 0.8 or run.nerve >= run.max_nerve - 1 else "nerve"
                return self.menu_tap(scene, lambda bs: next((b for b in bs if b.value == want), None))
            return self.menu_tap(scene, lambda bs: next((b for b in bs if b.value == "done"), None))
        if name == "Resolution":
            return self.menu_tap(scene) if scene.t > 60 else []
        if name == "DeckScene":
            return self.menu_tap(scene)
        if name == "Explore":
            return self.explore(game, scene)
        if name == "BattleScene":
            return self.battle(game, scene)
        return []

    # --- The map

    def explore(self, game, scene) -> list:
        run = game.run
        acts = explore.actions(run)
        if not acts:
            return []
        by_kind = {}
        for a in acts:
            by_kind.setdefault(a["kind"], []).append(a)
        if "advance" in by_kind:
            return self.do(scene, by_kind["advance"][0])
        if "rest" in by_kind and (run.hp < run.max_hp * 0.6 or run.nerve <= 3):
            return self.do(scene, by_kind["rest"][0])
        if "investigate" in by_kind and explore.current_act(run).clues:
            return self.do(scene, by_kind["investigate"][0])
        goal = self.goal(run)
        if goal and "move" in by_kind:
            nxt = explore.path_step(run, run.location, goal)
            for a in by_kind["move"]:
                if a["to"] == nxt:
                    return tap(*centre(layout.node_rect(CONTENT.scenario.locations[a["to"]].pos)))
        if "move" in by_kind:
            a = by_kind["move"][run.round % len(by_kind["move"])]
            return tap(*centre(layout.node_rect(CONTENT.scenario.locations[a["to"]].pos)))
        return self.do(scene, acts[0])

    def goal(self, run) -> str | None:
        if run.hp < run.max_hp * 0.5:
            rests = [lid for lid, rec in CONTENT.scenario.locations.items() if run.available(lid)
                     and any(a.get("rest") for a in rec.actions) and run.loc(lid).rested != run.agenda]  # fmt: skip
            if rests:
                return min(rests, key=lambda lid: self.distance(run, run.location, lid))
        act = explore.current_act(run)
        if act is not None and act.clues is None:
            return "QUEENS_CHAMBER"
        best, dist = None, 99
        for lid, loc in run.locs.items():
            if lid == run.location or not run.available(lid):
                continue
            if loc.clues > 0 or not loc.revealed:
                d = self.distance(run, run.location, lid)
                if d < dist:
                    best, dist = lid, d
        return best

    @staticmethod
    def distance(run, a, b) -> int:
        n, cur = 0, a
        while cur != b and n < 20:
            cur = explore.path_step(run, cur, b)
            if cur is None:
                return 99
            n += 1
        return n

    def do(self, scene, action) -> list:
        for b in scene.menu.buttons:
            if b.value == action:
                return tap(*centre(b.rect))
        return []

    # --- Battle

    def battle(self, game, scene) -> list:
        if scene.busy:
            return []
        b = scene.battle
        if b.over:
            return self.menu_tap(scene)
        if not b.hand:
            return tap(*centre(layout.END_TURN))
        if not scene.slots:
            return []
        incoming = sum(
            (
                f.intent
                and sum(b.enemy_damage(f, e.damage) * e.get("times", 1) for e in f.intent.effects if e.op == "attack")
            )
            or 0
            for f in b.living()
        )
        need_block = incoming > b.hero.shields
        targets = sorted([j for j, f in enumerate(b.foes) if f.alive and b.targetable(f)], key=lambda j: b.foes[j].hp)
        best = None
        for i, inst in enumerate(b.hand):
            card = inst.card
            if card.has("unplayable"):
                continue
            t = targets[0] if card.target == "enemy" and targets else None
            if not b.playable(inst, b.foes[t] if t is not None else None):
                continue
            ops = {e.op for e in card.effects}
            score = 1
            if card.type == "weapon":
                score = 6 if b.weapon is None else (3 if card.effects else 0)  # Equip ops: a draw, a shot.
            elif "shield" in ops or any(e.op == "apply" and e.status == "WARD" for e in card.effects):
                score = 8 if need_block else 2
            elif "fire" in ops or "last_round" in ops:
                score = 5
            elif card.type in ("aura", "equipment"):
                score = 4
            if score and (best is None or score > best[0]):
                best = (score, i, t)
        if best is None:
            return tap(*centre(layout.END_TURN))
        _, i, t = best
        uid = b.hand[i].uid
        s = scene.slots.get(uid)
        if s is None:
            return []
        if t is None:
            return drag(s.x, s.y, s.x, 300)
        x, y = scene.fighter_xy(b.foes[t].uid)
        return drag(s.x, s.y, x, y + 4)


def make(seed: int, target=None) -> QueenGame:
    return QueenGame(seed, target or Target("android", W, H))


def play(seed: int, limit: int = 200_000):
    pilot = Pilot()
    return autopilot.run(make, pilot, seed, limit, done=lambda g: type(g.scene).__name__ == "Title" and g.frame > 100
                         and g.campaign.get("runs", 0) > 0, target=Target("android", W, H))  # fmt: skip


def summary(game) -> str:
    log = game.campaign
    return f"frame {game.frame}, runs {log.get('runs', 0)}, outcome keys {[k for k in log if k.startswith('outcome')]}"


if __name__ == "__main__":
    autopilot.cli(play, summary, Path(REPLAYS) / "auto.json", __doc__)
