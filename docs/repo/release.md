# Releases

A `v*` tag builds the Android APK on GitHub Actions and publishes a GitHub release
(`.github/workflows/release.yml`). The tag must match `version` in `pyproject.toml`. Only the Android APK
ships for now (`queen-<version>-android.apk`), as the developer asked.

1. Bump `version` in `pyproject.toml`.
2. `just check` and `just lint`.
3. Commit, then `git tag v<version>` and `git push origin main v<version>`.

Locally, `just build android` writes `dist/release/queen-<version>-android.apk`. It needs JDK 17 (mise) and
the Android SDK (`ANDROID_HOME`, or `~/Library/Android/sdk` on macOS). The APK is debug-signed with
`android/debug.keystore`, which is committed so each build can update the last one on a phone.
