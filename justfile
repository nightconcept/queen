# Queen on NightEngine (Pyxel only). The public recipes are the engine's standard surface
# (nightengine/docs/games/commands.md), and `just check` fails if it grows. Helpers start with `_`.

set positional-arguments

# Run tools through mise when it is installed (the Android build needs its Java 17).
mise := `command -v mise >/dev/null && echo "mise x --" || true`

# Fetch the engine and install the tools.
setup:
    git submodule update --init --recursive
    mise install
    uv sync

# Run the tests, then the justfile check. `just check web` also runs the browser build checks.
check *runtimes:
    #!/usr/bin/env bash
    set -eo pipefail
    uv run python -m unittest discover -s tests -t .
    for runtime in "$@"; do
      case "$runtime" in
        pyxel) ;;
        web)
          uv run python -m nightengine.web build --offline --out dist/web-offline
          npm ci
          npx playwright test ;;
        *) echo "unknown runtime: $runtime (pyxel, web)" >&2; exit 2 ;;
      esac
    done
    uv run python -m nightengine.recipes

# Check lint and format.
lint *runtimes:
    uvx ruff check .
    uvx ruff format --check .

# Fix the format.
fmt:
    uvx ruff format .
    uvx ruff check --fix .

# Play: --target desktop|web|android --seed N --replay FILE. --browser serves the web build (add --host 0.0.0.0).
run *args:
    @just _play run "$@"

# Start in a state with dev tools on: scene=title|map|battle enemies=A+B location=ID clues=N xp=N act=N agenda=N cards=A+B
dev *args:
    @just _play dev "$@"

# Build release files into dist/release: desktop (this system), android, web.
build *args:
    #!/usr/bin/env bash
    set -eo pipefail
    targets=("$@")
    [ ${#targets[@]} -gt 0 ] || targets=(web android desktop)
    [ -n "$ANDROID_HOME" ] || [ ! -d "$HOME/Library/Android/sdk" ] || export ANDROID_HOME="$HOME/Library/Android/sdk"
    version=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
    out=dist/release
    mkdir -p "$out"
    for t in "${targets[@]}"; do
      case "$t" in
        web)
          uv run python -m nightengine.web build --out dist/web
          uv run python -m nightengine.web build --offline --out dist/web-offline
          (cd dist && uv run python -m zipfile -c "release/queen-$version-web.zip" web) ;;
        android)
          {{ mise }} uv run python -m nightengine.android build --out dist/android
          cp "dist/android/queen-$version.apk" "$out/queen-$version-android.apk" ;;
        desktop)
          rm -f dist/desktop/queen-*.zip
          uv run --with pyinstaller python -m nightengine.desktop build --out dist/desktop
          cp dist/desktop/queen-"$version"-*.zip "$out/" ;;
        *) echo "unknown target: $t (web, android, desktop)" >&2; exit 2 ;;
      esac
    done
    ls -l "$out"

# Watch a recording: just replay FILE.
replay file *args:
    @just _play run --replay "$@"

# Render a recording to PNG files with no window: just frames FILE [--out DIR] [--every N].
frames file *args:
    #!/usr/bin/env bash
    set -eo pipefail
    file=$1; shift
    out=frames every=300
    while [ $# -gt 0 ]; do
      case "$1" in
        --out) out=$2; shift 2 ;;
        --every) every=$2; shift 2 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
      esac
    done
    uv run python -m queen.frames "$file" "$out" --every "$every" --scale 1

# Let the autopilot play a seed by touch and record it to replays/: just autoplay [--seed N].
autoplay *args:
    #!/usr/bin/env bash
    set -eo pipefail
    seed=7
    while [ $# -gt 0 ]; do
      case "$1" in
        --seed) seed=$2; shift 2 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
      esac
    done
    uv run python -m queen.autopilot --seed "$seed" --out "replays/auto-$seed.json"

# --- Helpers. Run them by name: `just _shots`.

# Start the game. `mode` is run or dev; the rest are run's options.
_play mode *args:
    #!/usr/bin/env bash
    set -eo pipefail
    mode=$1; shift
    browser= rest=()
    while [ $# -gt 0 ]; do
      case "$1" in
        --browser) browser=1; shift ;;
        *) rest+=("$1"); shift ;;
      esac
    done
    dev=()
    [ "$mode" = dev ] && dev=(--dev)
    if [ -n "$browser" ]; then exec uv run python -m nightengine.web serve "${rest[@]}"; fi
    exec uv run game.py "${dev[@]}" "${rest[@]}"

# Headless phone-size pictures from scripted input (tools/shots.py has the script language).
_shots out="out/shots" *scripts:
    uv run python tools/shots.py "{{ out }}" {{ scripts }}

# Import the CC0 art packs into assets/art (see assets/art/README.md for where to get them).
_import-art packs:
    uv run --with pillow python -I tools/import_art.py "{{ packs }}"

# A balance sample: the autopilot plays N seeds and prints the outcomes.
_sim n="20":
    uv run python tools/sim.py {{ n }}
