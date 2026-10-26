# One GitHub release process for Python and the web

**Issue:** [#46](https://github.com/dwsdolce/guitar-tap-project/issues/46)

Status: **OPEN — plan agreed; the web workflow is being written.**

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
| Python | `Guitar_Tap_V<version>.dmg` | by hand: signing and notarising need the owner's Apple credentials |
| Python | `ReleaseNotes-<version>-<build>.pdf`, `GuitarTap-Quick-Start-Guide.pdf`, `GuitarTap-User-Manual.pdf` | by hand, with the `.dmg` (`build_mac`; the manual from GuitarTap) |

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

## Plan

1. **The web's workflow** (GuitarTapWeb `release.yml`): build, check, the zip as artifact or on the draft.
2. **Python's workflow** (guitar_tap `release.yml`, in place of `release-linux.yml`): the Linux AppImage and the
   Windows installer, checked, as artifacts or on the draft, as the web's.
3. **A test run of both**, before anything relies on them: each workflow for `main` into the draft `release-test-1`;
   a stand-in uploaded for the files built by hand, test notes written; the owner looks over each draft on GitHub,
   downloads its files (the web zip runs from a plain folder; the Windows installer and the AppImage start); then
   each draft is deleted, never published — and no tag is left in either repo.
4. **The web's 1.0.2:** the workflow for `1.0.2`, keeping the zip as an artifact; check it — it reports 1.0.2 (213),
   runs from a plain folder (`python3 -m http.server`), and its files match what is live at
   dolcesfogato.com/guitar_tap/guitar_tap_web/. Then the draft: the zip attached, its marketing notes (the owner
   reviews them); the owner publishes.
5. **Python on its `1.0.2` tag**, artifacts only (its release exists): both build from a release tag.
6. **The release checklist:** §2 (Python) and §3 (the web) become the process above, the same steps in both; the
   Windows script named as it is (`packaging/build_win`, not `build_win.bat`).
7. **1.1.0** is released this way in both editions.
