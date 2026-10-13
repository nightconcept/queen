"""One finger (or the mouse): press, drag, hold, tap and release, from NightEngine pointers (GDD 14.3).

No pyxel here: scenes feed it `inp.pointers` each frame, so a replay sees the same gestures.
"""

from dataclasses import dataclass

from nightengine.pointer import PointerPhase, primary

HOLD_FRAMES = 18  # 0.3 s at 60 fps without moving: inspect.
DRAG_PX = 6  # Moving this far makes a press a drag.


@dataclass
class Gesture:
    kind: str  # press, drag, hold, tap, release
    x: int
    y: int
    sx: int  # Where the press started.
    sy: int
    dx: int = 0  # Movement since the last frame.
    dy: int = 0


class Touch:
    def __init__(self):
        self.pid: int | None = None
        self.frames = 0
        self.dragging = False
        self.holding = False
        self.x = self.y = self.sx = self.sy = 0

    @property
    def down(self) -> bool:
        return self.pid is not None

    def update(self, pointers) -> list[Gesture]:
        out: list[Gesture] = []
        p = next((q for q in pointers if q.id == self.pid), None) if self.pid is not None else None
        if p is None and self.pid is not None:  # The contact vanished: treat it as released where it was.
            out.append(Gesture("release", self.x, self.y, self.sx, self.sy))
            self.pid = None
        if self.pid is None:
            # A quick tap can press and release within one frame: then it is never active, but it still counts.
            p = primary(pointers) or next(iter(pointers), None)
            if p is None:
                return out
            self.pid, self.frames, self.dragging, self.holding = p.id, 0, False, False
            self.x, self.y, self.sx, self.sy = p.x, p.y, p.start_x, p.start_y
            out.append(Gesture("press", p.x, p.y, p.start_x, p.start_y))
            if not p.active:
                out.append(Gesture("tap", p.x, p.y, p.start_x, p.start_y))
                out.append(Gesture("release", p.x, p.y, p.start_x, p.start_y))
                self.pid = None
            return out
        dx, dy = p.x - self.x, p.y - self.y
        self.x, self.y = p.x, p.y
        self.frames += 1
        if not self.dragging and not self.holding and (abs(p.x - self.sx) > DRAG_PX or abs(p.y - self.sy) > DRAG_PX):
            self.dragging = True
        if self.dragging:
            out.append(Gesture("drag", p.x, p.y, self.sx, self.sy, dx, dy))
        elif not self.holding and self.frames >= HOLD_FRAMES:
            self.holding = True
            out.append(Gesture("hold", p.x, p.y, self.sx, self.sy))
        if not p.active:
            if not self.dragging and not self.holding and p.phase != PointerPhase.CANCELLED:
                out.append(Gesture("tap", p.x, p.y, self.sx, self.sy))
            out.append(Gesture("release", p.x, p.y, self.sx, self.sy))
            self.pid = None
        return out


def inside(x: int, y: int, rect) -> bool:
    rx, ry, rw, rh = rect
    return rx <= x < rx + rw and ry <= y < ry + rh
