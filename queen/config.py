"""Screen size, safe areas, and paths. No tuning numbers: those are in data/."""

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
DATA = PACKAGE / "data"
ASSETS = ROOT / "assets"
REPLAYS = ROOT / "replays"

# Portrait 320x714: an exact 4x on the Pixel 10 Pro (1280x2856). GDD 14.1.
W, H = 320, 714
SAFE_TOP = 12  # The status bar and the camera.
SAFE_BOTTOM = 16  # The gesture bar.
TOUCH_MIN = 24  # The smallest touch target, in logical px.

HUNTER = "ROOK"
SCENARIO = "sovereign"
