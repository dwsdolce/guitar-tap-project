# Bug intake & tracking

**The model: many intake channels → one consolidated tracker → reply on the channel the user used.** Track
in one place; talk to each user where they reached you.

## Intake channels (where a report is born)
- **Developer-found** — the bulk. A **project** — work of several steps, decisions or sessions — is filed as a hub
  Issue. A **simple bug fix** is just fixed, in every edition the same way, with its tests and run-review, and
  committed; it gets no Issue and no detail doc (owner, 2026-10-25). When it is unclear which it is, ask.
- **Platform GitHub Issue** — a user files on `GuitarTap` / `guitar_tap` / `GuitarTapWeb`. Low-traffic
  community intake, kept (not redirected) so users can file where the code is.
- **Email** — `support@dolcesfogato.com`.
- **App Store** — no issue channel: only public Ratings & Reviews (you post a developer response the user is
  notified of) plus your support URL/email. So App Store reports arrive as a review response or, for anything
  needing back-and-forth, as email.

## Consolidation — a Projects board, not a second issue store
- The single work surface is the **GitHub Projects (v2) board** ("Guitar Tap") that pulls Issues from all
  four repos *and* holds hub-native Issues. That is the one tracking view.
- A user's **single-platform report stays as its platform Issue** — added to the board, no mirror, no
  double-entry; you reply *in place* (they're already subscribed).
- **Non-GitHub intake (email, App Store) becomes a hub Issue**, labeled with its source and carrying a
  back-reference (the email thread, the review URL).
- A **genuinely cross-platform defect gets one canonical hub Issue** that links the per-repo reports — the
  only time a GitHub-sourced bug is deliberately re-filed in the hub.

## Conventions (every tracked item)
- **Platform labels** `swift` / `python` / `web` / `android` / `all-editions`.
  `all-editions` replaces the old `all-three`, which counted a number that is no longer fixed;
  the editions themselves are declared in `tooling/parity/platforms.py`. An Android report should
  also name the device and Android version — the hardware varies far more than on the other
  editions (see [ANDROID-FEASIBILITY.md](../docs/ANDROID-FEASIBILITY.md) for what that cost
  already).
- **Source labels** `src:dev` / `src:github` / `src:email` / `src:appstore` / `src:play` (a Google Play review or Play Console report, once Android ships).
- **Type** `bug` (application defect) / `enhancement` (user-facing) / `infrastructure` (dev-facing: tests,
  tooling, parity, build, refactors — composes with the others; e.g. a test-suite bug is `bug` + `infrastructure`).
- **`needs-verification`** encodes the standing rule that nothing is done until the user has *run* it.
- Commits in any repo reference the item cross-repo: `refs dwsdolce/guitar-tap-project#N`.
- The Issue is the **addressable index**; the meaty analysis is a detail doc in the hub (`docs/`), linked from
  the Issue — for every tracked item, single-platform ones included. See
  [the lifecycle](#issue-lifecycle--the-detail-doc) below.

## Issue lifecycle — the detail doc
This holds on every machine and in every session. Session memory is local to one machine and invisible to the
others, so anything a later session needs — the diagnosis, the measurements, the decisions — goes in the hub
doc, not only in a conversation or a commit message.

**Opening.** The detail doc is written **when the Issue is opened**, before the work starts — not afterwards.
- The doc goes in hub `docs/`. Its header is the Issue link, then a `Status:` line, as in the existing docs.
- The Issue body is an **overview** that starts with the doc link, in this form:
  `Detail doc: [`docs/NAME.md`](docs/NAME.md)`. The full information lives in the doc.
- The doc is added to the **open index** in `docs/README.md`.

**Working.** The doc is kept current as the work goes: findings, decisions (with who decided and when), each
item's Done with its commit hashes, and the verification. Commit process: code → hash → doc.

**Closing** — all in one pass:
1. Close the Issue on GitHub with a resolution comment listing the commit hashes.
2. Close the loop on the origin (see [Reply-on-origin](#reply-on-origin)): for a platform Issue, a
   plain-language closing comment there — the reporter reads it, so no hashes or internal detail.
3. `git mv` the doc to `docs/completed/` and mark its `Status:` **✅ COMPLETE** with the date.
4. Fix the links: the `docs/README.md` index entry and the Issue body's `Detail doc:` link.

## Reply-on-origin
The source label says where to close the loop — GitHub comment, email reply, or App Store developer
response — while the board stays the unified work list.

## Where open work lives
Open work = **GitHub Issues + the Projects board**, the single source of truth. There is **no hand-maintained
`STATUS.md` index** alongside them (two hand-synced trackers drift — the same anti-pattern the parity oracle
removes). If an in-repo markdown roadmap is ever wanted, **generate** it from `gh issue list` — never
hand-maintain it in parallel.
