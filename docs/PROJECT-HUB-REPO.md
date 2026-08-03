# Project hub repo — spec

**Status:** 📋 SPEC (2026-08-01). Item 5 in STATUS. Design settled (see Decisions); no repo created yet.
Supersedes the 2026-07-16 idea capture.

## Purpose

A single **neutral GitHub repo** that owns what belongs to the *project* rather than to any one of its
four code repos — so cross-repo work has a real home instead of being wedged into a platform repo.

It solves two concrete problems:

1. **Project-wide docs are homeless.** `STATUS.md` and every shared spec live in the **web** repo's
   `Development/`, while the parity map + tooling + `TEST-COVERAGE.md` live in the **Swift** repo — yet all
   of these describe *all three* editions. Neither location is right.
2. **Bugs are cross-repo.** One defect is usually one bug in three codebases (the audio watchdog; the
   buffer-size issue "tracked" in the web repo today). Three separate threads drift apart.

**Enabler:** the Swift code is going open source, so the public/private asymmetry disappears — the hub can
be public, cross-repo issue references resolve for everyone, and the community can see and file.

## The doc-placement rule

Where a document lives is decided by one test, not case-by-case:

> **Is it referenced or tracked in `STATUS.md`?** → **the hub** — it's a *project document*, even if it
> concerns only one platform.
> **Is it standing developer documentation for a codebase** (code-architecture guideline, coding
> conventions, how to build/test/run)? → **that repo**.

The dividing line is **project work vs. developer reference**, *not* cross-platform vs. single-platform. A
Python-only bug spec is still a project document — it's tracked in STATUS — so it lives in the hub. What
stays in a repo is the standing "how this codebase is built and worked in" material. The result: every
platform repo is **very clean** — code, tests, and its own developer docs, and nothing about the project's
work.

The test is a doc's **role**, not its subject: a doc *about* architecture that is tracked work (e.g.
`RESTRUCTURE-NOTES.md`) is a project document → hub; only a standing architecture *reference/guideline* is
developer documentation → repo.

## Scope — what lives where

| Hub — **project documents** (anything `STATUS.md` references) | Repo — **developer documentation** |
|---|---|
| `STATUS.md` + the open-work roadmap | Code-architecture guidelines |
| Every feature/requirement spec — **including single-platform ones** | Coding conventions / style |
| Bug analyses / issue detail docs | How to build / test / run this codebase |
| Parity system: `PARITY-MAP.md`, `parity-index.json`, `TEST-COVERAGE.md` + the parity tooling | `WEB-UI-GUIDELINES.md` (web-port UI convention) |
| `INVENTORY.md`, `PLAN.md` (the contract the port is measured against) | *(plus all code, tests, per-repo build/deploy scripts)* |
| `RELEASE-CHECKLIST.md` (spans all 4 surfaces) | |
| Cross-repo Issues (the bug tracker) + a Project board | |
| A project index `README` — what it is, the four repos, how they relate, where to file | |

## Bug intake & tracking

The model: **many intake channels → one consolidated tracker → reply on the channel the user used.** Track
in one place; talk to each user where they reached you.

**Intake channels (where a report is born):**
- **Developer-found** — the bulk; filed straight as a hub Issue.
- **Platform GitHub Issue** — a user files on `GuitarTap` / `guitar_tap` / `GuitarTapWeb`. Low-traffic
  community intake, kept (not redirected) so users can file where the code is.
- **Email** — `support@dolcesfogato.com`.
- **App Store** — confirmed to offer **no** issue channel: only public Ratings & Reviews (you post a
  developer response the user is notified of) plus your support URL/email. So App Store reports arrive as a
  review response or, for anything needing back-and-forth, as email.

**Consolidation — a Projects board, not a second issue store:**
- The single work surface is a **GitHub Projects (v2) board** that pulls Issues from all four repos *and*
  holds hub-native Issues. That is the one tracking view.
- A user's **single-platform report stays as its platform Issue** — added to the board, no mirror, no
  double-entry; you reply *in place* (they're already subscribed).
- **Non-GitHub intake (email, App Store) becomes a hub Issue**, labeled with its source and carrying a
  back-reference (the email thread, the review).
- A **genuinely cross-platform defect gets one canonical hub Issue** that links the per-repo reports — the
  only time a GitHub-sourced bug is deliberately re-filed in the hub.

**Conventions (every tracked item):**
- **Platform labels** `swift` / `python` / `web` / `all-three`; **source labels** `src:dev` / `src:github` /
  `src:email` / `src:appstore`.
- A **`needs-verification`** label encodes the standing rule that nothing is done until the user has *run* it.
- Commits in any repo reference the item cross-repo: `refs dwsdolce/guitar-tap-project#N`.
- The Issue is the **addressable index**; the meaty analysis is a detail doc **in the hub** (a project
  document), linked from the Issue — even for a single-platform bug. (Commit messages are essays today
  precisely because there is nothing to reference.)

**Reply-on-origin.** The source label says where to close the loop — GitHub comment, email reply, or App
Store developer response — while the board stays the unified work list.

## Project tracking

- `STATUS.md` moves to the hub as the neutral open-work index (it already tracks all platforms; the
  status-is-status-not-detail and closeout conventions carry over unchanged).
- Pair it with a **GitHub Project** board that spans all repos, so in-flight work is visible across editions.
- Items 4 and 5 (and any future cross-repo item) become Issues once the hub exists; `STATUS.md` stays the
  human-readable index that points at them.

## Decisions

1. **Name — `guitar-tap-project`** (repo `dwsdolce/guitar-tap-project`). Distinct from the four code repos;
   reads as "the project," not a fifth app.
2. **Parity tooling lives in the hub.** It was only in the Swift repo for convenience — it isn't Swift code.
   It runs from the hub and checks the three code repos out as siblings.
3. **Generated artifacts are committed** (`PARITY-MAP.md`, coverage) — for browsability; convenience over
   purity.
4. **Fresh history, not preserved.** The docs come from several source repos and their history isn't
   load-bearing (planning/status, not code you `git blame`). A single "import" commit records each doc's
   source repo + commit SHA for provenance; deep history stays discoverable in the original repos. Mirrors
   the website extraction.

## Non-goals / until it exists

- Not a code repo; no build.
- Repo-specific design and all code stay put.
- **Until it's created:** the markdown `STATUS.md` in the web repo continues as the index, and cross-repo
  bugs keep being tracked there. The standing conventions above (one bug = one Issue + platform labels;
  meaty analyses as detail docs; `needs-verification`) hold in the interim.

## Implementation checklist

Turns the settled design into steps. Do it as one focused effort so the cut-over is clean.

**1. Stand up the repo**
- [x] Create `dwsdolce/guitar-tap-project` (done — GPL `LICENSE` in place, matching the other repos).
  Visibility follows the Swift open-sourcing (public once Swift is public; private until then).
- [x] Add a top-level `README` — the front door: what the project is, the four code repos + this hub and how
  they relate, and where to file a bug. *(drafted; pending your commit)*

**2. Wire up tracking**
- [x] Create the labels: platform (`swift` / `python` / `web` / `all-three`), source (`src:dev` /
  `src:github` / `src:email` / `src:appstore`), and `needs-verification` (+ the usual `bug` / `enhancement`).
  *(done via `gh label create`)*
- [x] Create a **GitHub Projects (v2) board** ("Guitar Tap") with an auto-add workflow. *(An auto-add
  workflow targets one repo, so it's pointed at `guitar-tap-project` with filter `is:issue`; platform-repo
  issues are added by hand on triage — matches the low community-intake volume. Add more auto-add workflows
  later if fuller automation is wanted.)*
- [x] Bug-report Issue template + `config.yml` added to **`guitar_tap`** (`.github/ISSUE_TEMPLATE/` — a
  GitHub Issue Form tailored to the Python app: version, OS, install method, mic/interface, repro; `config.yml`
  disables blank issues + adds a support-email contact link).
- [ ] Add the template (+ config) to **Swift + web** when those repos go public — deferred, *not* done: a
  private repo can't take community issues. Rides with the open-sourcing (step 1 visibility).

**3. Import the project documents (fresh history)** — organized into three top-level buckets, all lowercase:
`docs/` (project docs — STATUS, specs, work docs, `completed/` archive, `images/`, the investigation-bundled
`playback-validation/`), `process/` (how-to — `RELEASE-CHECKLIST.md`, `DEV-DOC-STANDARD.md`), `tooling/`
(`TEST-COVERAGE.md` + `parity/`: scripts, `PARITY-MAP.md`, `parity-index.json`, `doc_coverage.py`, README).
- [x] Copy the project docs into the hub: from `GuitarTapWeb/Development/` (everything except the web dev
  `README.md`) and from the Swift repo (`RELEASE-CHECKLIST.md`, `TEST-COVERAGE.md`, the parity system).
  `WEB-UI-GUIDELINES.md` came too — on review it's a port-era project doc, not standing dev guidance.
- [x] Import committed (`3398509`) + pushed. Provenance (source repo + HEAD) recorded here since the commit
  message is brief: `GuitarTapWeb` `0dda10f`, `GuitarTap` `9c84a8a` (STATUS/this-spec carried uncommitted
  working-tree edits at import).
- [x] Fix relative links inside the moved docs (STATUS `Completed/`→`completed/` + location refs;
  `DEV-DOC-STANDARD` tool paths; one `MATERIAL-MULTITAP` cross-ref). *Tooling-doc paths (`Tooling/`→`tooling/`
  in `PARITY-MAP.md`/`TEST-COVERAGE.md`/parity `README`) are regenerated in step 4 — not hand-fixed.*

**4. Wire the parity tooling in the hub**
- [ ] Make it run from the hub, checking the three code repos out as siblings.
- [ ] Regenerate `PARITY-MAP.md` + coverage and **commit them** (artifacts are tracked).

**5. Migrate tracking**
- [ ] Convert the current open (and deferred) STATUS items into hub Issues + board cards; point `STATUS.md`
  (now in the hub) at them.

**6. Cut over the source repos** *(only after the hub copies are verified)*
- [ ] Remove the migrated project docs from `GuitarTapWeb` and the Swift repo; update any pointer from a repo
  `README`/`CLAUDE.md`/memory to the hub location.
- [ ] Note: removing tracked docs is a commit, so it **rolls that repo's build number** — batch it with a
  release or land it when no build is pending (see the build-number rule in `RELEASE-CHECKLIST.md`).
