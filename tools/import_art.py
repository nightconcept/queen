"""Import the CC0 art packs into assets/art/, quantised to one palette.

    uv run --with pillow python -I tools/import_art.py PACKS_DIR

PACKS_DIR holds the unzipped packs (see assets/art/README.md for the sources):

    PACKS_DIR/monsters/x/PackMonsters/...          OneBitPudding, Pixel Sci-Fi Monster Animations
    PACKS_DIR/city2/x/cyberpunk city 2 files/...   ansimuz, Warped City 2
    PACKS_DIR/lab/x/Scifi lab Files/...            ansimuz, Warped Sci-Fi Lab
    PACKS_DIR/kenney/x/Tilesheet/...               Kenney, 1-Bit Pack

It writes one PNG strip per sprite (frames left to right), the backgrounds, the icons, `queen/data/art.json` (frame
sizes and animations), and `queen/data/palette.json` (64 colours: index 0 is the transparent key, then the named UI
colours, then the art colours). Every pixel of every PNG is an exact palette colour, so Pyxel's load maps it exactly.
"""

import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "assets" / "art"
DATA = ROOT / "queen" / "data"

KEY = (255, 0, 255)  # Index 0: never drawn. Transparent pixels become this colour.

# The named UI colours (indices 1..). The art colours follow them.
UI = {
    "void": 0x0B0A12,
    "ink": 0x16131F,
    "panel": 0x241F33,
    "panel_hi": 0x3A3150,
    "line": 0x5C4F7A,
    "bone": 0xE8DCC8,
    "ash": 0x9A8FA8,
    "blood": 0xD8324A,
    "blood_dark": 0x7A1830,
    "shield": 0x4FA8E8,
    "shield_dark": 0x1F4A78,
    "energy": 0xF2C14E,
    "crit": 0xFFE45C,
    "horror": 0xA45CE8,
    "spore": 0x8CE05C,
    "rook": 0xF08A3C,
    "clue": 0x5CE0D0,
    "entropy": 0xE85CA0,
    "white": 0xFFFFFF,
}
ART_COLOURS = 64 - 1 - len(UI)


def monsters(packs):
    return packs / "monsters" / "x" / "PackMonsters"


def city(packs):
    return packs / "city2" / "x" / "cyberpunk city 2 files"


def frames_from_sheet(path, fw, fh, indices):
    sheet = Image.open(path).convert("RGBA")
    cols = sheet.width // fw
    return [
        sheet.crop(((i % cols) * fw, (i // cols) * fh, (i % cols) * fw + fw, (i // cols) * fh + fh)) for i in indices
    ]


def frames_from_files(paths):
    return [Image.open(p).convert("RGBA") for p in paths]


def r(a, b):
    return list(range(a, b + 1))


def sprites(packs):
    """{name: (frames by animation, in order)}. Frame numbers in the pack's info file count from 1."""
    m = monsters(packs)
    c = city(packs)
    out = {}

    def sheet(name, file, fw, fh, anims):
        out[name] = {a: frames_from_sheet(m / file, fw, fh, [i - 1 for i in idx]) for a, idx in anims.items()}

    sheet(
        "drone",
        "Monster1Pack.png",
        64,
        32,
        {"idle": r(19, 22), "attack": r(1, 5), "hit": r(23, 24), "death": r(25, 32)},
    )
    sheet(
        "brood_egg",
        "Monster2Pack.png",
        64,
        32,
        {"idle": r(1, 4), "hatch": r(5, 17), "hit": r(18, 19), "death": r(20, 24)},
    )
    sheet("stalker", "Monster3Pack.png", 96, 64, {"idle": r(1, 4), "attack": r(37, 43), "death": r(44, 52)})
    sheet("spitter", "Monster4Pack.png", 64, 64, {"idle": r(1, 4), "attack": r(9, 16), "hit": [17], "death": r(18, 25)})
    sheet("warden", "Monster5Pack.png", 128, 64, {"idle": r(5, 8), "death": r(9, 14)})
    sheet("slug", "Monster7Pack.png", 80, 32, {"idle": r(5, 8), "attack": r(18, 25), "hit": [9], "death": r(10, 17)})
    sheet(
        "queen",
        "Monster8Pack.png",
        80,
        64,
        {"idle": r(1, 4), "hit": [11], "attack": r(12, 19), "death": r(20, 30), "stun": r(76, 79)},
    )
    s = c / "Sprites"
    out["husk"] = {"idle": frames_from_files(sorted((s / "cop" / "idle").glob("cop*.png")))}
    out["rook"] = {
        "idle": frames_from_files([s / "Player" / "Idle" / f"Idle{i}.png" for i in range(1, 5)]),
        "shoot": frames_from_files([s / "Player" / "Shoot" / f"Shoot{i}.png" for i in range(1, 4)]),
        "hit": frames_from_files([s / "Player" / "Hurt" / "Hurt2.png"]),
    }
    out["boom"] = {"play": frames_from_files([s / "explosion-a" / f"explosion-a{i}.png" for i in range(1, 9)])}
    return out


# Kenney 1-bit colored-transparent_packed.png, 16x16 tiles: (column, row).
ICONS = {
    "heart": (39, 10),
    "shield": (37, 4),
    "sword": (35, 8),
    "skull": (38, 11),
    "crown": (43, 2),
    "eye": (37, 0),
    "hourglass": (39, 12),
    "key": (33, 11),
    "question": (37, 13),
    "warning": (35, 21),
    "gun": (38, 9),
    "flask": (39, 11),
    "lock": (39, 21),
    "up": (28, 21),
    "down": (30, 21),
}


def icons(packs):
    sheet = Image.open(packs / "kenney" / "x" / "Tilesheet" / "colored-transparent_packed.png").convert("RGBA")
    return {n: sheet.crop((c * 16, rw * 16, c * 16 + 16, rw * 16 + 16)) for n, (c, rw) in ICONS.items()}


def backgrounds(packs):
    m = monsters(packs)
    hive = Image.new("RGBA", (800, 448))
    for i in range(7):
        hive.alpha_composite(Image.open(m / f"MonstersBGLayer{i}.png").convert("RGBA"))
    layers = packs / "lab" / "x" / "Scifi lab Files" / "layers"
    lab = Image.new("RGBA", (320, 240))
    for n in ("back", "middle", "front"):
        lab.alpha_composite(Image.open(layers / f"{n}.png").convert("RGBA"))
    return {"hive": hive.convert("RGBA"), "lab": lab}


def pixels(im):
    im = im.convert("RGBA")
    return im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()


def opaque_pixels(images):
    for im in images:
        for p in pixels(im):
            if p[3] >= 128:
                yield p[:3]


def build_palette(images):
    """The UI colours, then ART_COLOURS from a median cut of every opaque art pixel."""
    pixels = list(opaque_pixels(images))
    strip = Image.new("RGB", (len(pixels), 1))
    strip.putdata(pixels)
    q = strip.quantize(colors=ART_COLOURS, method=Image.Quantize.MEDIANCUT)
    flat = q.getpalette()[: ART_COLOURS * 3]
    art = [tuple(flat[i : i + 3]) for i in range(0, len(flat), 3)]
    ui = [((v >> 16) & 255, (v >> 8) & 255, v & 255) for v in UI.values()]
    return [KEY, *ui, *art]


def nearest(colour, palette, cache):
    if colour not in cache:
        cache[colour] = min(
            range(1, len(palette)),
            key=lambda i: sum((a - b) ** 2 for a, b in zip(colour, palette[i], strict=True)),
        )
    return cache[colour]


def quantise(im, palette, cache):
    out = Image.new("RGB", im.size)
    out.putdata([KEY if p[3] < 128 else palette[nearest(p[:3], palette, cache)] for p in pixels(im)])
    return out


def strip(frames):
    w = max(f.width for f in frames)
    h = max(f.height for f in frames)
    out = Image.new("RGBA", (w * len(frames), h))
    for i, f in enumerate(frames):
        out.paste(f, (i * w, 0))
    return out, w, h


def main(packs):
    packs = Path(packs)
    sprite_frames = sprites(packs)
    icon_images = icons(packs)
    bgs = backgrounds(packs)
    everything = [f for anims in sprite_frames.values() for fs in anims.values() for f in fs]
    everything += list(icon_images.values()) + list(bgs.values())
    palette = build_palette(everything)
    cache = {}
    (ART / "sprites").mkdir(parents=True, exist_ok=True)
    (ART / "bg").mkdir(parents=True, exist_ok=True)
    manifest = {"_doc": "Written by tools/import_art.py. Sprite strips: frames left to right.", "sprites": {}}
    for name, anims in sprite_frames.items():
        order, spans = [], {}
        for anim, fs in anims.items():
            spans[anim] = [len(order), len(fs)]
            order += fs
        im, w, h = strip(order)
        quantise(im, palette, cache).save(ART / "sprites" / f"{name}.png")
        manifest["sprites"][name] = {"file": f"sprites/{name}.png", "w": w, "h": h, "anims": spans}
    icon_strip, _, _ = strip(list(icon_images.values()))
    quantise(icon_strip, palette, cache).save(ART / "icons.png")
    manifest["icons"] = {"file": "icons.png", "size": 16, "names": list(icon_images)}
    manifest["backgrounds"] = {}
    for name, im in bgs.items():
        quantise(im, palette, cache).save(ART / "bg" / f"{name}.png")
        manifest["backgrounds"][name] = {"file": f"bg/{name}.png", "w": im.width, "h": im.height}
    (DATA / "art.json").write_text(json.dumps(manifest, indent=1) + "\n")
    names = ["key", *UI, *[f"art{i}" for i in range(ART_COLOURS)]]
    colours = {n: f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}" for n, c in zip(names, palette, strict=True)}
    doc = "Index 0 is the transparent key. The UI colours are hand-picked; art0.. come from tools/import_art.py."
    (DATA / "palette.json").write_text(json.dumps({"_doc": doc, "colours": colours}, indent=1) + "\n")
    print(f"{len(sprite_frames)} sprites, {len(icon_images)} icons, {len(bgs)} backgrounds, {len(palette)} colours")


if __name__ == "__main__":
    main(sys.argv[1])
