# Bug intake & tracking

**The model: many intake channels → one consolidated tracker → reply on the channel the user used.** Track
in one place; talk to each user where they reached you.

## Intake channels (where a report is born)
- **Developer-found** — the bulk; filed straight as a hub Issue.
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
  the Issue — even for a single-platform bug.

## Reply-on-origin
The source label says where to close the loop — GitHub comment, email reply, or App Store developer
response — while the board stays the unified work list.

## Where open work lives
Open work = **GitHub Issues + the Projects board**, the single source of truth. There is **no hand-maintained
`STATUS.md` index** alongside them (two hand-synced trackers drift — the same anti-pattern the parity oracle
removes). If an in-repo markdown roadmap is ever wanted, **generate** it from `gh issue list` — never
hand-maintain it in parallel.
