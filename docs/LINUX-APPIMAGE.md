# Linux AppImage — does not start on older Linux

**Issue:** [#23](https://github.com/dwsdolce/guitar-tap-project/issues/23)

Status: **IN PROGRESS — the AppImage built and checked in GitHub Actions and tried by the owner on Mint 22.3; to ship with the next release, then the catalog retest.** Python edition only (Linux packaging); the Mac and
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

## Decisions (owner, 2026-10-22)

1. **Build in GitHub Actions** on `ubuntu-22.04`, and attach the AppImage to the GitHub release from there once a
   release is published. A workflow on `release: published` (and on demand for a named tag): check out the tag
   with its history (the build number is the commit count), a portable Python 3.14, `packaging/build_linux` with
   the current `appimagetool`, a start test on that system without `libfuse2`, then `gh release upload`. The
   other five release assets stay as they are made now.
2. **Ship with the next release** (1.0.3 or 1.1, not yet decided); the 1.0.2 asset is not replaced.
3. **List GuitarTap in the AppImage catalog:** once a fixed AppImage is on a release, ask for a retest on
   AppImage/appimage.github.io#5378.

## Done (2026-10-22/23; owner's go for the night's commits and runs)

**The workflow** — `guitar_tap` `.github/workflows/release-linux.yml` (`4d540fb`, `dc23dc8`, `861fdce`, `4702f60`,
`14aa6f6`, `a9bbb19`, `1119104`): on a published release, or by hand for a tag or branch, on `ubuntu-22.04` — setup-python 3.14 (built
for 22.04), `appimagetool` 1.9.1 (static runtime), `packaging/build_linux`; then checks: no bundled library needs
glibc newer than 2.35, the runtime links no `libfuse`, none of the libraries that must be the system's is bundled
(item 4), the icons and fonts are where the app reads them, and the app, started
off-screen with no sound server and `libportaudio2` removed, stays up with no error and loads the bundled PortAudio
(`GT_AUDIO_BACKEND_REPORT=1`); then keeps the AppImage as the run's artifact and attaches it to the release. Runs on
`main` (not attached): the run of build 672 passed — glibc 2.35, the bundled PortAudio loaded and started. The Tests
workflow passed on Linux, Windows and macOS for every commit.

**Found on the way:**
1. **#37's loader dropped `sounddevice` from every packaged build** (macOS, Windows, Linux): PyInstaller bundles
   what the code imports, and `audio_backend` loads `sounddevice` by name. The spec names it as a hidden import
   (`861fdce`). Not shipped — no release since #37.
2. **The AppImage relied on the user's `libportaudio2`**, which a clean Ubuntu does not have; without it the audio
   code could not load and the app was broken (the 1.0.2 AppImage too, behind its glibc failure). Now the spec
   bundles the build machine's `libportaudio.so.2` and `audio_backend` points `sounddevice` at it; JACK's client
   library comes with it, ALSA's is left to the system (it must match the system's ALSA configuration and plugins,
   as the AppImage exclusion list has it). A PortAudio that cannot be found or loaded now gives "Audio input
   unavailable" rather than a broken app — also from source (`4702f60`, `14aa6f6`; test `test_no_audio_system`,
   both failures).
3. **The icons and fonts were bundled where the app does not read them** (every packaged build): the window icon,
   the splash and, on Linux, the export's Liberation Sans were missing. They now go beside the app's package,
   `guitar_tap/icons` and `guitar_tap/fonts` (`a9bbb19`).
4. **The file dialogs had no network or remote places in the AppImage:** the build bundled the build machine's GTK
   stack and GLib, and the system's GVFS modules (built against its newer GLib) would not load into them. GTK,
   GLib/GIO, ATK, Pango, Cairo, Pixman, Epoxy, HarfBuzz, FriBidi, Thai, fontconfig and FreeType are now the
   system's, as ALSA is (`a9bbb19`). So are the C library's `libmvec` and the C++ and GCC runtimes
   (`libstdc++`, `libgcc_s`), which the system's graphics drivers need at the system's own versions (`1119104`).
5. **The AppImage relied on the user's `libxcb-cursor0`**, which Qt needs to open a window under X11 and not every
   desktop has: the build machine lacked it, so it was not bundled. On a clean Ubuntu 22.04 (minimal install) under
   X11, build 671 stopped with "xcb-cursor0 or libxcb-cursor0 is needed"; the other eight libraries Qt's X11 plugin
   needs were present there and on Mint, so they stay the system's. The workflow installs it on the build machine,
   and `build_linux` stops if it or PortAudio is not on the build machine, or not in the bundle (`1119104`). The README names `libxcb-cursor0` (not the `-dev` package)
   to run from source — the owner checked it on the Mint VM with only `libxcb-cursor0` installed.

**Docs:** `guitar_tap` README — the AppImage built by the workflow, the current `appimagetool`, `libportaudio2` to
build locally (`4702f60`); `process/RELEASE-CHECKLIST.md` — the workflow attaches the AppImage, five assets by hand,
check the run; the tooling line. The release notes' "requires no system package installation" is now true. No
`.deb` or `.rpm` is built — Linux ships as the AppImage only.

**Owner's try (2026-10-23), build 671 on the Mint 22.3 VM (Ubuntu 24.04; sound through PipeWire): passes** — the
bundled PortAudio loaded and started, sound works; no console errors; the window icon and splash show; the Play File
dialog shows Other Locations; the PDF's spectrum picture is drawn in Liberation Sans. Build 671 on a clean Ubuntu
22.04 (minimal install, nothing added): under Wayland it opens, sound (PulseAudio) and taps work, Other Locations
shows; under X11 it does not start (item 5). **Build 672 on the same clean Ubuntu 22.04: passes under Wayland and
X11** — the window opens, sound and taps work.

**Still to do:** the next release (1.0.3 or 1.1) carries it; then a retest on AppImage/appimage.github.io#5378, and
#23 closed.
