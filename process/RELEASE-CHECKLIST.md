# GuitarTap Release Checklist

The runbook for shipping a release. Four surfaces across four repos:

| Surface | Repo | Destination |
|---|---|---|
| **Mac / iOS** | `GuitarTap` | App Store Connect |
| **Python** | `guitar_tap` | GitHub `dwsdolce/guitar_tap` |
| **Web app** | `GuitarTapWeb` | `dolcesfogato.com/guitar_tap/guitar_tap_web/`, and GitHub `dwsdolce/GuitarTapWeb` (its build, for other sites to host) |
| **Marketing site** | `guitar_tap_website` | `dolcesfogato.com/guitar_tap/` |

**The notes' "reviewed through" marker (read once):** each repo's current notes section carries one line —
`<!-- Notes reviewed through commit <sha> (<date>) … -->` in `Documentation/ReleaseNotes.md` (Swift) and
`docs/ReleaseNotes.md` (Python), a `// Notes reviewed through commit <sha>` comment on the newest entry of
`src/components/ReleaseNotes.tsx` (web). Whenever the notes are brought up to date — mid-cycle or at release — read
only `git log <sha>..HEAD` for what is new, write the notes, then move the marker to the newest commit covered. It
never reaches a reader: pandoc keeps the comment out of the HTML's view and out of the PDF.

**The build-number rule (read once):** in every repo the build number is that repo's own
`git rev-list --count HEAD`, baked at build/archive time. So finish committing first, then build from
that commit, and keep each release-notes filename equal to the commit count you actually ship. Build
numbers differ across repos — that is expected.

**The release-identity guard (read once):** all three code repos now *refuse to run or build* while
the tree still claims to be a release that has already shipped. Two conditions — the version names an
already-tagged release, and the newest tag has no frozen release-notes entry — both triggered by
**HEAD having moved past the last release tag**. Both are reported together, and there is deliberately
**no override**.

| Repo | Guard | Fires on |
|---|---|---|
| `GuitarTap` | `Tooling/check-release-ready.sh` | every Xcode build (first run-script phase, before compiling) + `Distribution/build_mac` |
| `guitar_tap` | `src/guitar_tap/_release_guard.py` | `python -m guitar_tap` + every `packaging/build_*` |
| `GuitarTapWeb` | `tooling/check-release-ready.sh` | `npm run dev` / `npm run build` / `npm run preview` |

`guitar_tap_website` has no guard — nothing there derives a version from a build; its banner is a
hand-edited string.

**What this changes in this runbook:** the version bump and the notes roll-over are **no longer
release-day steps**. The guard forces them on the *first commit after the previous release* (§6), so
by the time you ship `X.Y.Z` the version is already `X.Y.Z` and the notes already carry an `X.Y.Z`
section. Release day is about **filling in the prose**, not creating the section — creating it again
leaves an empty duplicate. Nothing fires at the tag itself, so rebuilding, re-notarising or
redeploying the release you just cut still works.

**GitHub releases (Python and the web) — one process for both** (`docs/completed/GITHUB-RELEASE-PROCESS.md` in the hub): a
**Release** workflow, run by hand for the release's tag (Actions → Release → Run workflow; `ref` = the tag, `draft`
on), builds what GitHub can build, checks each file reports the tag's version and build, and creates the tag's
**draft** release with those files and their `SHA256SUMS`. The files built by hand are uploaded to the draft; you write
its notes — a short, marketing summary of the release's enhancements, not the full release notes — review it, and
publish. Publishing builds nothing. To try the workflow before a release: run it for `main` with `release` =
`release-test-<n>` (a tag that does not exist — never create a real one), then delete the draft.

> **Uploads to both `dolcesfogato.com` paths are done by hand via cPanel's File Manager.** Tip: upload a **zip** of
> the folder and use File Manager → _Extract_ in place, so the swap is effectively atomic; then delete stale hashed
> assets left from the previous build.

---

## 0. Before you start
- [ ] The **marketing version** `X.Y.Z` was chosen at the start of this cycle (§6) and is already set in all three code repos, identically. Changing it now means re-bumping all three before anything will build.
- [ ] Each repo clean and on `main`.
- [ ] Each repo's release guard passes (see §6 for the three commands) — if one blocks, the cycle-start roll was never done.

## 1. Swift — Mac/iOS → App Store  *(`GuitarTap`)*

### 1a. Version + code *(always)*
- [ ] `MARKETING_VERSION` should **already** be `X.Y.Z` in both places in `GuitarTap.xcodeproj/project.pbxproj` (Debug + Release) — rolled at the start of this cycle (§6). Confirm it; bump here only if you are changing the planned number.
- [ ] Land all app code for the release.
- [ ] Run Swift's unit suite on a **physical** iPad or iPhone (Xcode, Product → Test on the device, or
  `xcodebuild … -destination id=<UDID> test -only-testing:GuitarTapTests`). It checks the device against its own
  baseline (`GuitarTapTests/self-baseline-ios-arm64.json`), which CI cannot: CI runs simulators, whose runtime
  is a configuration of its own.

### 1b. Build & upload for testing *(optional — TestFlight / review)*
- [ ] Xcode → **Archive** → Organizer → validate → **Upload** *(team `43QHHT3XK2`, app `id6759410596`)*.
- [ ] Add TestFlight "test notes" if needed — these are **not** the App Store release notes.
- [ ] No App Store release notes are required just to upload or test a build.

### 1c. Publish a public release *(only when shipping)*
- [ ] Finish the **existing** top section of the build-less notes source `Documentation/ReleaseNotes.md`: its `{{version}}/{{build}}/{{since}}` placeholder header is already there from §6 — replace the `TODO(X.Y.Z)` marker with this release's user-facing prose. **Do not add another section**; the freeze + fresh-section step already happened at cycle start. Build the **UserManual** target/scheme for the manual (needs `.venv` + WeasyPrint + `brew install pango`). *(The macOS build auto-stamps the release-notes PDF and regenerates the Quick-Start via `generate-help.sh` → `generate-release-notes.sh` — plain pandoc, all gitignored, nothing typed or committed.)*
- [ ] **Commit the code + notes source** — this is the commit you ship (generated docs are gitignored).
- [ ] Xcode → **Archive** this final commit → Organizer → validate → **Upload**. Confirm `CFBundleVersion` (= `git rev-list --count HEAD`) **==** the `<build>` in the release-notes filename.
- [ ] In **App Store Connect** → the app's new version:
  - [ ] **Paste** the "what's new" text into the **"What's New in This Version"** field — you type/paste into the form; do **not** attach the `.md`/`.pdf`. *(The files are your cumulative source, reused on the website + Python release.)*
  - [ ] Update **screenshots** only if the UI changed (upload from `Documentation/AppStoreImages/`).
  - [ ] Select the uploaded build → **Submit for Review**.
- [ ] After approval, **Release** the version (manually, or automatic if configured).
- [ ] Tag the shipped commit and push: `git tag X.Y.Z && git push origin X.Y.Z` — bare marketing version, matching the existing `1.0.1` tag on `dwsdolce/GuitarTap`. Provenance only (the App Store doesn't consume it, unlike the Python tag); tag the commit that actually shipped, after any re-submission.

## 2. Python → GitHub  *(`guitar_tap`)*
- [ ] `src/guitar_tap/version` should **already** read `X.Y.Z` — rolled at the start of this cycle (§6). Confirm it.
- [ ] Finish the **existing** top section of the single source `docs/ReleaseNotes.md`: the placeholder header (`## Version {{version}} · Build {{build}}` / `### What's New Since Build {{since}}`) is already there from §6 — replace the `TODO(X.Y.Z)` marker with this release's prose. **Do not add another section.** No build numbers are typed for the new release; they're stamped at build.
- [ ] **Commit and push** (version + notes source). Build number = commit count, so commit *before* building; every file of the release is built from this **same commit**, or their `.<build>` suffixes diverge.
- [ ] macOS, by hand, on the Mac: `./packaging/build_mac` → `Guitar_Tap_VX.Y.Z.dmg` **plus** the stamped Quick-Start + release-notes PDFs, in one step *(codesign + notarize + staple; needs `notarytool-profile`, `create-dmg`, pandoc + LaTeX, WeasyPrint + Pango)*. Validate the PDFs first if you like — `./packaging/generate_release_notes.sh` and `./packaging/generate_guide.sh` run standalone. **Before tagging**: the release notes take "since" from the latest tag and refuse to generate once the current version is tagged.
- [ ] Tag the commit and push the tag: `git tag X.Y.Z && git push origin X.Y.Z` — **bare `X.Y.Z`** (no `v`, no build number: the in-app updater compares the tag to the `version` file).
- [ ] Run **Release** for the tag (`ref` = `X.Y.Z`, `release` blank, `draft` on). It builds, checks and attaches:
  - Linux, on Ubuntu 22.04 (the oldest supported LTS, glibc 2.35): `guitar-tap-X.Y.Z.<build>-x86_64.AppImage`, `.deb` and `.rpm` (unsigned) — each started; the `.deb` and `.rpm` installed, started, quit and removed (the `.rpm` on Fedora).
  - Windows: `Guitar_Tap_VX.Y.Z.<build>.exe` (`packaging/build_win`, Inno Setup; unsigned) — started.
  - `SHA256SUMS` for those files.
- [ ] Upload to the draft: the `.dmg`, `ReleaseNotes-X.Y.Z-<build>.pdf`, `GuitarTap-Quick-Start-Guide.pdf`, `GuitarTap-User-Manual.pdf`.
- [ ] Write the draft's notes (the marketing summary); check every file is there — the AppImage, `.deb`, `.rpm`, `.exe`, `SHA256SUMS`, the `.dmg` and the three PDFs.
- [ ] **Publish as a full release** (not pre-release) — `/releases/latest` and the in-app updater read only published releases.

## 3. Web app → `…/guitar_tap/guitar_tap_web/`  *(`GuitarTapWeb`)*
- [ ] `version` in `package.json` should **already** read `X.Y.Z` — rolled at the start of this cycle (§6). Confirm it.
- [ ] Fill in the **existing** top entry of `RELEASES` in `src/components/ReleaseNotes.tsx` — it is already the `X.Y.Z` entry with `build: __APP_BUILD__` and empty `groups` from §6; write this release's groups/items and delete the `TODO(X.Y.Z)` marker. **Do not prepend another entry**, and leave the pinned literal builds on the older entries alone.
- [ ] `npm run typecheck && npm test && npm run lint` — all green.
- [ ] **Commit and push.** *(No build number to set by hand — the newest entry's `__APP_BUILD__` resolves at build time.)*
- [ ] Tag the commit and push the tag: `git tag X.Y.Z && git push origin X.Y.Z` — bare marketing version. It marks exactly what goes live at `…/guitar_tap_web/`.
- [ ] Run **Release** for the tag (`ref` = `X.Y.Z`, `release` blank, `draft` on). It builds with the Node the commit names (`.nvmrc`), checks the bundle reports the tag's version and build, and attaches `guitar-tap-web-X.Y.Z.<build>.zip` (the app's files at its top) and `SHA256SUMS`.
- [ ] Smoke-test the zip from the draft: unzip it into an empty folder, serve it (`python3 -m http.server` there), open it — the footer and Settings show `X.Y.Z (<build>)`.
- [ ] Deploy **that zip** — the file other sites host (Lutherie Academy) is the one live here: upload it to `…/guitar_tap/guitar_tap_web/` via **cPanel File Manager** and Extract in place; delete stale old `assets/` hashes. A partial upload = blank page.
- [ ] Ensure the URL serves **with the trailing slash** (`base './'` requires it).
- [ ] Confirm a matching `GuitarTap-User-Manual-X.Y.Z.html` exists on the server (the app links to it by version).
- [ ] Write the draft's notes (the marketing summary), check the zip and `SHA256SUMS` are there, and **publish**.

## 4. Marketing website → `…/guitar_tap/`  *(`guitar_tap_website` — its own repo `dwsdolce/guitar_tap_website`; see its `DEPLOY.md`)*
- [ ] Edit the version banner: `index.html` (~line 122, `Guitar Tap X.Y.Z is now available`) — the only hand-edited version string.
- [ ] Overwrite the two **stable-named** release-notes PDFs (the links never change, the contents do):
  - [ ] `releases/GuitarTap-Swift-Release-Notes.pdf` ← latest Swift cumulative PDF (GuitarTap repo)
  - [ ] `releases/GuitarTap-Python-Release-Notes.pdf` ← latest Python cumulative PDF (guitar_tap repo)
- [ ] Copy the regenerated **self-contained** manual into `manual/` — the versioned + `…-User-Manual.html/.pdf` "latest" (from GuitarTap's `generate-manual.sh`, which embeds all images into the HTML). `manual/index.html` is the manual itself (a copy of `…-X.Y.Z.html`, not a redirect), so `…/manual/` is a real page; every copy names it as canonical. **Do NOT deploy or overwrite `manual/images/`** — new manuals are self-contained; that folder is frozen, serving only the legacy 1.0/1.0.1 external-image HTML.
- [ ] Refresh `GuitarTap-Quick-Start-Guide.pdf` if changed; screenshots only if the UI changed.
- [ ] Commit + push the repo, then **upload the changed files** to `…/guitar_tap/` via **cPanel File Manager** (banner, the two release-notes PDFs, `manual/`).
- [ ] *No edits needed:* App Store URL (`id6759410596`), GitHub-releases download link, web-app link — all stable.

## 5. Post-release verification
- [ ] **Web:** hard-reload / fresh session (defeat the stale service worker); footer + Settings show `X.Y.Z (build)`; manual link resolves.
- [ ] **Python:** launch an installed build → in-app update check offers/matches `X.Y.Z`; site download links reach the new GitHub assets.
- [ ] **Site:** banner, both release-notes PDFs, and the manual all show the new version.
- [ ] **App Store:** track review status; marketing URL resolves.

## 6. Start the next cycle *(do this immediately after tagging)*

The **first commit after a release** makes all three code repos refuse to run or build — that is the
guard doing its job, but discover it deliberately here rather than mid-task three days later. Roll
all three now, in one sitting:

- [ ] **Swift** (`GuitarTap`): bump `MARKETING_VERSION` (both configs). In `Documentation/ReleaseNotes.md`, **freeze** the shipped top section to its literals — `## Version X.Y.Z · Build <n>` / `### What's New Since Build <prev>`, both from `git rev-list --count <tag>` — then add a fresh `{{placeholder}}` section carrying a `TODO(<next>)` marker and a "Notes reviewed through commit `<tag's commit>`" line.
- [ ] **Python** (`guitar_tap`): bump `src/guitar_tap/version`. Same freeze + fresh placeholder section (with its "reviewed through" line) in `docs/ReleaseNotes.md`.
- [ ] **Web** (`GuitarTapWeb`): bump `version` in `package.json`. In `src/components/ReleaseNotes.tsx`, **pin** the shipped top entry to the literal build it went out as (`git rev-list --count <tag>`), then prepend a new entry with `build: __APP_BUILD__`, `since: '<prev>'`, `groups: []`, a `TODO(<next>)` marker and a `// Notes reviewed through commit <tag's commit>` comment.
- [ ] Confirm each tree is unblocked — all three exit 0:
  - `GuitarTap`: `./Tooling/check-release-ready.sh`
  - `guitar_tap`: `.venv/bin/python src/guitar_tap/_release_guard.py`
  - `GuitarTapWeb`: `./tooling/check-release-ready.sh`
- [ ] Commit the three rolls. (Each rolls its repo's build number — expected; nothing baked depends on it yet this early in a cycle.)

## Gotchas / notes
- **Per-repo build numbers** differ across surfaces — expected, not a bug.
- **Python build number is fully automatic**: `version_build` is gitignored (build scripts regenerate it; `_version.py` resolves it live from git when run from source, so testing shows the right build with no script/wrapper). Release-notes build numbers are stamped by `generate_release_notes.sh` from the source `docs/ReleaseNotes.md` placeholders — never typed. The generated docs (`ReleaseNotes-*.md/.pdf`, the Quick-Start `.html/.pdf`) are gitignored too — regenerated each build, distributed on the website + GitHub releases — so `build_mac` leaves a clean `git status`. Only sources are tracked (`docs/ReleaseNotes.md`, `views/help_view.py`).
- **Swift docs are automatic too** (mirrors Python): release notes stamp from `Documentation/ReleaseNotes.md` via `generate-release-notes.sh`, run from `generate-help.sh` on the macOS build (best-effort — skips if pandoc/tag missing or the version is already tagged; the release guard is the hard backstop, so a silent skip can no longer hide a stale version). Quick-Start, manual, and release-notes outputs are all gitignored; sources tracked are `Documentation/ReleaseNotes.md`, `GuitarTap/Views/HelpView.swift`, the manual `Documentation/Manual/ch*.md`.
- **Web release notes build auto-binds**: the newest `RELEASES` entry uses `build: __APP_BUILD__`, so it always equals the deployed About line — nothing to set by hand. When adding a NEWER version, give it `__APP_BUILD__` and freeze the prior top entry to its literal shipped build. The guard enforces exactly this: it blocks when the newest entry is still the shipped tag, and when more than one entry carries `build: __APP_BUILD__` (a shipped entry that still auto-binds silently re-labels itself every build).
- **The guard skips what it cannot judge** — a frozen PyInstaller bundle, a tree with no git repository, or a repository with no tags. A released app can therefore never refuse to start over this, and a fresh clone still builds. It *does* cover git worktrees.
- **Tests are deliberately unguarded** — the version means nothing to them. `pytest` and `npm test` run regardless. The exception is Swift: `xcodebuild test` builds the app target first, so it hits the guard anyway; there is no way to run Swift tests without building the app.
- **Xcode surfaces the guard as clickable issues** — it writes `error:` lines to stdout (the only form Xcode promotes to the Issue navigator; a phase failing on stderr shows nothing but an exit code), with the notes error anchored to `Documentation/ReleaseNotes.md:5`. Run from a terminal it prints the full explanation instead.
- **Stale service worker (web):** `autoUpdate` means a returning visitor may need one reload before the new build takes; always hard-reload to verify a deploy, don't conclude from a first load.
- **One-time tooling per build machine:**
  - Swift docs: pango + WeasyPrint venv, pandoc, basictex.
  - Python (Mac build machine): `.venv/bin/pip install -r requirements-packaging.txt`, `create-dmg`, Apple Developer ID certs + `notarytool-profile`, WeasyPrint + Pango (guide), pandoc + LaTeX (release notes). Windows and Linux: none for a release (the Release workflow builds them). For a local build: Windows, Inno Setup 6; Linux, the current `appimagetool` (github.com/AppImage/appimagetool), `libportaudio2` and `libxcb-cursor0`, and `dpkg-dev` and `rpm` for the `.deb` and `.rpm`.
  - Web: Node.
- **Still by hand:** the three version bumps, the macOS `.dmg` and the PDFs (Apple credentials), the App Store, and
  the cPanel uploads to two paths. The Python and web files GitHub can build are built by the Release workflows.
