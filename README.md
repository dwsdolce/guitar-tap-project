# Guitar Tap — project hub

The home for everything about the **Guitar Tap** project that isn't the code itself: the roadmap, the
shared specifications, the parity system, the release runbook, and cross-repo bug tracking.

Guitar Tap is tap-tone analysis for luthiers, built as **one design implemented across three editions**
(Swift is canonical; Python and web mirror it), plus a marketing site.

## Repositories

| Repo | What it is |
|---|---|
| [GuitarTap](https://github.com/dwsdolce/GuitarTap) | Swift — macOS / iOS (canonical) |
| [guitar_tap](https://github.com/dwsdolce/guitar_tap) | Python — Windows / macOS / Linux |
| [GuitarTapWeb](https://github.com/dwsdolce/GuitarTapWeb) | Web app (PWA) |
| [guitar_tap_website](https://github.com/dwsdolce/guitar_tap_website) | Marketing site |
| **guitar-tap-project** (this repo) | Project docs, roadmap, parity, cross-repo issues |

## What lives here

- **Roadmap / open work** — `STATUS.md`, the single index of what's active.
- **Shared specifications** — the "design once, implement on all three" feature contracts.
- **Parity system** — the parity map, coverage, and the tooling that verifies the three editions match.
- **Release runbook** — `RELEASE-CHECKLIST.md`, the four-surface release process.

Docs specific to one codebase (architecture, coding conventions, build/test how-to) stay in that codebase's
repo. The rule: **is it referenced in `STATUS.md`? → here. Is it standing developer reference for one
codebase? → that repo.**

## Reporting a bug

File it wherever is easiest — an Issue on the relevant platform repo, or email support@dolcesfogato.com.
Reports are consolidated here on a project board for tracking, and you'll get a reply on whichever channel
you used.

---

*This hub is being populated — its design and the migration steps are in the project-hub spec (imported from
the platform repos as part of standing it up).*
