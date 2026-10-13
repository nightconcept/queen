"""Screen size, safe areas, and paths. No tuning numbers: those are in data/."""

from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parent
DATA = PACKAGE / "data"
ASSETS = ROOT / "assets"
REPLAYS = ROOT / "replays"

# Portrait 540x1170: an exact 2x on the smallest flagship screens (1080x2340, Galaxy S25 class), and 2x on the
# 1080-wide default mode of the Pixel 10 and 10 Pro, with a thin band left over. GDD 14.1.
W, H = 540, 1170
SAFE_TOP = 52  # The status bar and the camera cutout: art may go under it, text and touch may not.
SAFE_BOTTOM = 24  # The gesture bar.
TOUCH_MIN = 48  # The smallest touch target, in logical px (about 6 mm at 2x).

HUNTER = "ROOK"
SCENARIO = "sovereign"
