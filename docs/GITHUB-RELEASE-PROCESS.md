# One GitHub release process for Python and the web

**Issue:** [#46](https://github.com/dwsdolce/guitar-tap-project/issues/46)

Status: **OPEN — both workflows built, tested (owner); the web's 1.0.2 released with its build; the `.deb`, `.rpm` and `SHA256SUMS` built and tested; users told how to install (manual §2.1); the release checklist rewritten; next: step 8, 1.1.0 — when the owner is ready (a rehearsal on `main` first, if wanted).**

## The problem

Lutherie Academy will host GuitarTapWeb on their own site, as they host their other tools: a copy on their server.
They need the built web app for each release, and there is no such file: the web edition's GitHub releases carry no
build, and stop at 1.0.1 — 1.0.2 shipped (tag `1.0.2`, build 213, deployed to dolcesfogato.com) with no release.

The two editions released on GitHub have no common process:

| | GitHub release now | Built how |
|---|---|---|
| Web | one release, 1.0.1, notes only | `npm run build` by hand, uploaded to dolcesfogato.com through cPanel |
| Python | a release per version, its files uploaded by hand | macOS `.dmg` (`packaging/build_mac`, signed and notarised on the owner's Mac); Windows `.exe` (`packaging/build_win` with Inno Setup, unsigned, on a Windows machine); the PDFs (release notes, Quick-Start Guide, from `build_mac`; the User Manual, from GuitarTap); the Linux AppImage by a workflow (`release-linux.yml`) that runs when a release is published — not yet used: there has been no Python release since it was written |

Swift ships through App Store Connect and has no GitHub release; it is not part of this.

## What a release carries

| Edition | File | Built |
|---|---|---|
| Web | `guitar-tap-web-<version>.<build>.zip` — `dist/`, the whole app: static, about 1.6 MB, runs from any folder over HTTPS (Vite `base: './'`), its Help linking to the manual on dolcesfogato.com. What Lutherie Academy installs and what is uploaded to dolcesfogato.com. | on GitHub |
| Python | `guitar-tap-<version>.<build>-x86_64.AppImage` | on GitHub (Ubuntu 22.04) |
| Python | `Guitar_Tap_V<version>.exe` | on GitHub (Windows, Inno Setup; unsigned, as now) |
| Python | `guitar-tap-<version>.<build>-x86_64.deb`, `guitar-tap-<version>.<build>-x86_64.rpm` | on GitHub (Ubuntu 22.04, from the AppImage's built app; unsigned) |
| Python | `Guitar_Tap_V<version>.dmg` | by hand: signing and notarising need the owner's Apple credentials |
| Python | `ReleaseNotes-<version>-<build>.pdf`, `GuitarTap-Quick-Start-Guide.pdf`, `GuitarTap-User-Manual.pdf` | by hand, with the `.dmg` (`build_mac`; the manual from GuitarTap) |
| Both | `SHA256SUMS` — the SHA-256 of each file the workflow attaches (not the `.dmg` or PDFs, uploaded by hand after it) | on GitHub, by the workflow |

## The process

The same in both editions:

1. **Run the edition's release workflow by hand for the tag.** It checks out the tag with its whole history (the
   build number is the commit count; at the tag the release guard passes, so a past release builds too), builds what
   can be built on GitHub, checks each build reports the tag's version and `git rev-list --count <tag>`, and creates
   a **draft** release for the tag with those files attached — or updates the tag's draft if there is one.
2. **Upload the files built by hand** to the draft (Python: the `.dmg` and the PDFs).
3. **Review the draft:** its notes — a short, marketing summary of the release's enhancements — and that every file is
   there.
4. **Publish.** The one public step. Publishing builds nothing.

The workflow takes what to build (a tag, or for a test a commit or `main`) and the draft's name (the tag's, or a test
name). A run can also keep its files as the run's artifacts, with no draft: for checking a build before any release
exists. It runs from `main`, so it builds a tag made before it existed (1.0.2).

**A test run** builds `main` into a draft named for a tag that does not exist (`release-test-<n>`): GitHub creates a
draft's tag only when the draft is published, so deleting the draft leaves nothing behind. Its check compares the
build with the commit's own version and build number. A real tag is never made for a test: the release guards read
the newest tag, and a stray one would stop every build until it was deleted from every clone. A draft is never
public, and Python's update check reads only published releases.

## Decisions (owner, 2026-10-26)

1. **The GitHub release's notes are a short, marketing summary** — the release's enhancements, not the full notes the
   apps show, which are far too long for it. Written for each release; how much of a draft can be taken from the
   release notes (their New Features and Improvements headings) is looked at when the web's 1.0.2 notes are written.
2. **The web's 1.0.1 is left as it is** (notes, no build).
3. **The web's 1.0.2 build must match what is live.** The server is not thought to have had an untagged update; the
   check confirms it. A mismatch is a failure to find before the zip is attached.
4. **A draft first, published by the owner** — the workflow makes the draft with its files; nothing is public until
   the owner has reviewed it and publishes.
5. **One process for Python and the web**, documented in `process/RELEASE-CHECKLIST.md`.
6. **Python's Windows installer is built on GitHub**; it is not signed, as now.
7. **Python's 1.0.2 is not rebuilt.** Its tag predates the packaging the workflow uses (the requirement groups,
   `849c4de`; the bash Windows build; the AppImage, #23) — run on the tag, both jobs stop at the missing
   `requirements-packaging.txt`. A release tag's build is proved by the web's 1.0.2 and, for Python, by 1.1.0's draft,
   checked before it is published.
8. **Python ships a `.deb` and an `.rpm` too**, unsigned: installed with the system's own tools, in the applications
   menu, removed cleanly. A signed `.deb`/`.rpm` checks nothing on its own (`dpkg` and `apt` do not check a single
   `.deb`'s signature; `dnf` does not check a downloaded `.rpm` by default); signing pays off only with a package
   repository — its own Issue, if Linux users ask.
9. **Every release carries `SHA256SUMS`** (Python and the web): a download can be checked against it.

## Built

- **The web's workflow** — GuitarTapWeb `.github/workflows/release.yml` (`a58b419`): run by hand with a tag, branch or
  commit (`ref`), a draft name (`release`; blank for the tag's own) and `draft`. Node from the built commit's `.nvmrc`
  (else `main`'s); `npm ci`, `npm run build`; checks a tag builds its own version and the bundle reports the version
  and the commit count; zips `dist/` with the app's files at the top; keeps it as an artifact or puts it on the draft
  (a new draft at the built commit; an existing draft gets the file; a published release is refused).
- **Python's workflow** — guitar_tap `.github/workflows/release.yml` (`df68914`), in place of `release-linux.yml`:
  the same inputs; a `linux` job (the AppImage, with every check the old workflow had), a `windows` job (PyInstaller and
  Inno Setup through `packaging/build_win`, unsigned, and a start test), each checked by `packaging/check_release_build`
  (a tag builds its own version; the build number is the commit count; the file's name carries `<version>.<build>`);
  a `draft` job attaching both. `README.md` and `packaging/build_linux` name it; #23's record too.
- **Found by the test run:** `packaging/build_win` passed ISCC a bare `/F`, which Git Bash turns into a path, so ISCC
  saw two scripts — unnoticed since the Windows build became a bash script (`849c4de`), with no Python release since.
  The `/F` is gone (`adb503a`); the installer's name comes from the `.iss`.
- **The `.deb`, `.rpm` and `SHA256SUMS`** — guitar_tap `c52cdfd`: `packaging/make_linux_package` (pdfarranger-qt's, its
  names changed; licence `GPL-3.0`, as the repo's), `packaging/build_linux [app|appimage|deb|rpm]`; the `linux` job
  installs `dpkg-dev` and `rpm`, checks all three names, installs the `.deb` with apt and starts it (the bundled
  PortAudio loaded), removes it (nothing left in `/opt`), and does the same for the `.rpm` with dnf in a
  `fedora:latest` container; the `draft` job attaches `SHA256SUMS`. GuitarTapWeb `889a0b0`: `SHA256SUMS` with the zip.

## Test run (step 3)

- **Web: passed** (owner, 2026-10-26) — draft `release-test-1` with `guitar-tap-web-1.1.0.390.zip`; the zip run from a
  plain folder reports 1.1.0 (390).
- **Python: passed** (owner, 2026-10-26) — draft `release-test-1` with `guitar-tap-1.1.0.693-x86_64.AppImage` and
  `Guitar_Tap_V1.1.0.693.exe`, both built, checked and started on GitHub; the installer installs and runs on Windows;
  the AppImage runs on Ubuntu once made executable — a downloaded AppImage is not, and a double-click on it says
  "There is no application installed for 'AppImage application bundle' files" (plan step 6).
- Both drafts deleted, never published; no `release-test-1` tag in either repo, and both repos' releases as before.

## The web's 1.0.2 (step 4)

- **Built from the tag** (run 40398568758): `guitar-tap-web-1.0.2.213.zip`; it reports 1.0.2 (213). Its 16 files are
  byte-identical to what is live at dolcesfogato.com/guitar_tap/guitar_tap_web/ — 1.0.2 as shipped.
- **The draft** (run 40398957756): the zip attached (downloaded from the draft and compared again — identical), the
  marketing notes (the owner approved them).
- **Published by the owner** (2026-10-26): https://github.com/dwsdolce/GuitarTapWeb/releases/tag/1.0.2 — the web
  edition's Latest release; the `1.0.2` tag unchanged (`1ae80f6`).
- **Its `SHA256SUMS`**, attached by hand to the published release (owner's go, 2026-10-26): the sum of the zip already
  on it, which GitHub's own digest of the zip matches.

## Test run of the `.deb`, `.rpm` and `SHA256SUMS` (step 5)

- **Both drafts built** (2026-10-26), `release-test-2`: Python's with `guitar-tap-1.1.0.694-x86_64.AppImage`, `.deb`,
  `.rpm`, `Guitar_Tap_V1.1.0.694.exe` and `SHA256SUMS`; the web's with `guitar-tap-web-1.1.0.391.zip` and
  `SHA256SUMS`.
- **On GitHub:** the `.deb` installed with apt on Ubuntu 22.04, and the `.rpm` with dnf in a Fedora container; each
  started with the bundled PortAudio and removed with nothing left in `/opt`.
- **The `.deb`: passed** (owner, 2026-10-26) — installs on Ubuntu with `sudo apt install ./<file>.deb`; a double-click
  opens it in the archive manager (plan step 6). The `.rpm` has GitHub's Fedora test only: the owner has no Fedora.
- **Found by it: the app crashed on quit** (the owner, Ubuntu, after opening the metrics panel, Settings and Saved
  Measurements; Ubuntu's crash dialog). At quit, `qapp.shutdown()` deleted every object PySide counted as Python's, in
  no set order — among them widgets built without a parent and then put in a layout, which Qt had given a parent in the
  window; deleted after the window, such a widget was deleted twice (SIGSEGV or SIGABRT). On Linux about seven quits in
  ten crashed after Saved Measurements or Settings had been opened, none after a start and quit; on macOS about one in
  eight. Not in a release: `shutdown()` came after 1.0.2 (`3892bf2`). **Fixed** — guitar_tap `57e08b1`: the main window
  is deleted first, as one tree (0 crashes in 160 quits on Linux, 30 on macOS); `tests/test_quit.py` runs the session
  five times and expects a clean exit (it failed without the fix); the `.deb` and `.rpm` tests quit as a user does.
- Both drafts deleted, never published; no `release-test-2` tag in either repo.

## Plan

1. **The web's workflow** (GuitarTapWeb `release.yml`): build, check, the zip as artifact or on the draft.
2. **Python's workflow** (guitar_tap `release.yml`, in place of `release-linux.yml`): the Linux AppImage and the
   Windows installer, checked, as artifacts or on the draft, as the web's.
3. **A test run of both**, before anything relies on them: each workflow for `main` into the draft `release-test-1`;
   the owner looks over each draft and its files; each draft deleted, never published, no tag left.
4. **The web's 1.0.2:** built from the tag, checked against what is live, the draft with its marketing notes, published
   by the owner.
5. **Python's `.deb` and `.rpm`**, made as the owner's other Python apps make them (pdfarranger-qt):
   `packaging/make_linux_package` (copied from pdfarranger-qt, its names changed) packs the PyInstaller bundle as it
   stands — under `/opt/guitar-tap`, a wrapper in `/usr/bin`, `packaging/guitar-tap.desktop`, the icon and the
   copyright — the `.deb` with `dpkg-deb` and its dependencies from `dpkg-shlibdeps` (only what the system must
   supply), the `.rpm` with `rpmbuild` and `AutoReqProv: no` (the bundled Qt not advertised); `packaging/build_linux`
   takes `[app|appimage|deb|rpm]` (default all three), a missing `dpkg-deb` or `rpmbuild` reported and that format
   skipped. In the release workflow's Linux job (Ubuntu 22.04, `dpkg-dev` and `rpm` installed): each checked (its name
   carries `<version>.<build>`; the `.deb` installs and the app starts; the `.rpm` installs in a Fedora container and
   the app starts) and attached beside the AppImage. **And `SHA256SUMS`** on every draft, Python's and the web's,
   listing each file the workflow attaches. Tested as in step 3: a test draft, the owner installs each package on
   Linux, the draft deleted.
6. **Users told how to install:** in the User Manual's installation section, §2.1 (ch02) — the Linux `.deb`
   (`sudo apt install ./<file>.deb`), `.rpm` (`sudo dnf install ./<file>.rpm`) and AppImage (made executable: the
   file manager's way beside `chmod +x`, and what a double-click shows before then), how to remove each; Windows'
   unsigned installer (More info → Run anyway). Not in the release notes, Help or the Quick Start (owner). The README
   names the files and points to §2.1. **Done** — GuitarTap `9932b83`, guitar_tap `86de6f7`.
7. **The release checklist:** §2 (Python) and §3 (the web) become the process above, the same steps in both; the
   Windows script named as it is (`packaging/build_win`, not `build_win.bat`). **Done** — hub `c93d5d4`.
8. **1.1.0** is released this way in both editions.
