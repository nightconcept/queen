# Releases

A `v*` tag builds the Android APK on GitHub Actions and publishes a normal GitHub release, marked Latest (not a
pre-release) (`.github/workflows/release.yml`). The tag must match `version` in `pyproject.toml`. Only the Android APK
ships for now (`queen-<version>-android.apk`), as the developer asked. After it publishes, the workflow
deletes every older release, so the page holds only the newest build. The tags stay in the history.

The `release` skill (`.claude/skills/release/SKILL.md`) does these steps for an agent:

1. Bump the patch `version` in `pyproject.toml`, then `uv lock`.
2. `just check` and `just lint`.
3. Commit, then `git tag -m "Queen v<version>" v<version>` (this repo's git config wants a message on every
   tag) and `git push origin main v<version>`.
4. Watch the run (`gh run watch`) and check that `gh release list` shows only the new release, as Latest.

Locally, `just build android` writes `dist/release/queen-<version>-android.apk`. It needs JDK 17 (mise) and
the Android SDK (`ANDROID_HOME`, or `~/Library/Android/sdk` on macOS). The APK is debug-signed with
`android/debug.keystore`, which is committed so each build can update the last one on a phone.
