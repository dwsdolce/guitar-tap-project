# Linux AppImage — does not start on older Linux

**Issue:** [#23](https://github.com/dwsdolce/guitar-tap-project/issues/23)

Status: **ANALYSIS — no decision, nothing changed.** Python edition only (Linux packaging); the Mac and
Windows builds are unaffected.

## How this came up

Reported 2026-09-28 by the AppImage catalog's automated test, on [AppImage/appimage.github.io#5378](https://github.com/AppImage/appimage.github.io/pull/5378) — a pull request its discovery workflow (`discover-apps.yml`) opened to add GuitarTap to the catalog (AppImageHub) after finding the `guitar-tap-1.0.2.482-x86_64.AppImage` release asset. Nothing in our repos was touched; the test ran our shipped AppImage and it did not start.

## The report (verbatim)

> ❌ Test failure
>
> @dwsdolce: this pull request adds the AppImage from your GitHub repository to the AppImage catalog; the test reports the following. Could you have a look?
>
> Compatibility: not self-contained: uses the C library of the system; uses an old AppImage runtime that needs the C library (and libfuse2) of the system; references glibc 2.39
>
> The AppImage was built on a system that is too new. Please build it on the oldest still-supported Ubuntu LTS release so that it runs on all supported systems.
> The application quit or crashed right after starting. The error below usually shows why.
> First error in the log:
>
> ```
> [PYI-4:ERROR] Failed to load Python shared library '/run/firejail/appimage/usr/bin/guitar-tap/_internal/libpython3.14.so.1.0': /lib/x86_64-linux-gnu/libm.so.6: version `GLIBC_2.38' not found (required by /run/firejail/appimage/usr/bin/guitar-tap/_internal/libpython3.14.so.1.0)
> ```
>
> ERROR: The application exited within 11 seconds instead of showing a window
> Commit 23b6c6f. Full log

## Analysis

Two separate problems. Only the first stops the app from starting.

**1. Built on a system too new — the app crashes at start on older Linux.**
- The AppImage was built on a glibc 2.39 machine (Ubuntu 24.04 or similar). PyInstaller bundles the build machine's Python; its `libpython3.14.so` needs glibc 2.38, so Python cannot load on an older system and the app exits before a window appears.
- An AppImage never bundles glibc (the "uses the C library of the system" line is true of every PyInstaller AppImage), so the build machine's glibc sets the oldest Linux the app runs on.
- `process/RELEASE-CHECKLIST.md:79` already says to build "on old-glibc box"; this build did not.

**2. The old AppImage runtime — it needs `libfuse2` on the user's system.**
- `packaging/build_linux` uses the old AppImageKit `appimagetool` (its error message points to github.com/AppImage/AppImageKit), which embeds a runtime that needs the system's `libfuse2`. Ubuntu 22.04 and later do not install it by default, so on many systems the AppImage will not mount.
- The current tool, [github.com/AppImage/appimagetool](https://github.com/AppImage/appimagetool), embeds a static runtime that does not need `libfuse2`.
- The release notes (1.0.2, 1.0.3, current) say the AppImage "requires no system package installation" — not true with the old runtime.

**Scope.** Every Linux AppImage shipped so far (1.0.2 at least; check what else is attached to releases). The Python edition only; the Mac and Windows builds are unaffected.

## What would fix it (to evaluate)

- **Where to build:** the oldest still-supported LTS, Ubuntu 22.04 (glibc 2.35), either
  - (a) a 22.04 VM or Docker container on the Linux build box, or
  - (b) a GitHub Actions job on `ubuntu-22.04` that builds the AppImage (reproducible, independent of any local machine).
- **Python:** a Python 3.14 that does not raise the glibc floor — e.g. `uv python install 3.14` (its standalone builds target a far older glibc). PySide6/Qt's own wheels then set the floor (manylinux_2_28 for recent PySide6 — glibc 2.28), comfortably below 22.04.
- **Runtime:** switch `build_linux` (and the checklist's prerequisites line, which lists `appimagetool` + `libfuse2`) to the current `appimagetool`.
- **Docs:** correct the checklist and the release-notes wording.
- **Release:** decide whether to rebuild and replace the 1.0.2 asset or ship the fix with 1.0.3.
- **Verify:** run the new AppImage on a 22.04 system without `libfuse2`.
- **Afterwards (optional):** comment on AppImage/appimage.github.io#5378 asking for a retest, if the catalog listing is wanted.
