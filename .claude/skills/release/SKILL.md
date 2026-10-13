---
name: release
description: Ship a new Queen build. Bumps the patch version, runs the checks, commits, tags v<version> and pushes, then watches the GitHub Actions release that builds the Android APK and leaves it as the only release on the page. Use when the user says "release", "new build", "ship it", "cut a build", "make an APK" or "publish".
---

# Release a Queen build

A `v*` tag builds the Android APK on GitHub Actions (`.github/workflows/release.yml`), publishes the
release, and deletes every older release, so the newest build is the only one on the page. The tags are
kept. [Releases](../../../docs/repo/release.md) has the details.

The user asked for a build, so push without asking again. Stop and report if a check fails.

## Steps

1. **Start clean.** On `main`, `git status` must show no changes the user has not asked to ship, and
   `git pull --ff-only` must succeed. If there are uncommitted changes, ask whether to commit them first.
2. **Pick the version.** Read `version` in `pyproject.toml` and bump the patch (`0.0.1` → `0.0.2`), unless
   the user named a version. The tag `v<version>` must not exist yet (`git tag -l`). The Android
   `versionCode` comes from the version, so each build updates the last one on a phone.
3. **Bump.** Set `version` in `pyproject.toml`, then run `uv lock` so `uv.lock` matches.
4. **Check.** `just check` and `just lint`. Both must pass.
5. **Commit, tag, push.**

   ```sh
   git commit -am "chore: release v<version>"
   git tag v<version>
   git push origin main v<version>
   ```

   End the commit message with the attribution lines the session asks for.
6. **Watch the build.** Find the run with
   `gh run list --workflow release.yml --limit 1 --json databaseId,status,headBranch`, then
   `gh run watch <id> --exit-status`. It takes about 5 to 10 minutes.
7. **Confirm.** `gh release list` must show only `v<version>`, and
   `gh release view v<version> --json assets --jq '.assets[].name'` must list
   `queen-<version>-android.apk` and `SHA256SUMS`. Give the user the release URL
   (`gh release view v<version> --json url --jq .url`).

## If the build fails

Read the log with `gh run view <id> --log-failed`. Fix the cause on `main`, then bump to the next patch
version and release again. Do not move or reuse a tag that was pushed. Delete a failed tag only if the
user asks.

## A local APK only

To build without publishing: `just build android`. It writes `dist/release/queen-<version>-android.apk`
and needs JDK 17 (mise) and the Android SDK.
