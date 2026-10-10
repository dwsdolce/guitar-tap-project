# Guitar Tap — project hub

The home for everything about the **Guitar Tap** project that isn't the code itself: the open work and its
documents, the shared specifications, the parity system, the release runbook, and cross-repo bug tracking.

Guitar Tap is tap-tone analysis for luthiers, built as **one design implemented across several editions**
(Swift is canonical; Python and web mirror it), plus a marketing site. A fourth, Android, is proposed —
see `docs/ANDROID-PLAN.md`. The editions are declared for the tooling in
`tooling/parity/platforms.py`.

## Repositories

| Repo | What it is |
|---|---|
| [GuitarTap](https://github.com/dwsdolce/GuitarTap) | Swift — macOS / iOS (canonical) |
| [guitar_tap](https://github.com/dwsdolce/guitar_tap) | Python — Windows / macOS / Linux |
| [GuitarTapWeb](https://github.com/dwsdolce/GuitarTapWeb) | Web app (PWA) |
| [GuitarTapAndroid](https://github.com/dwsdolce/GuitarTapAndroid) | Android — Kotlin/Compose (**proposed**; private, holds the Phase 0 spike) |
| [guitar_tap_website](https://github.com/dwsdolce/guitar_tap_website) | Marketing site |
| **guitar-tap-project** (this repo) | Project docs, roadmap, parity, cross-repo issues |

## Setting up on a new machine

All commands run in **bash**: Terminal on macOS, a shell on Linux, Cygwin bash (or Git Bash) on Windows. Every
repo has its own Python environment, `.venv`, made from its own requirements files; nothing uses another repo's
Python or the system's. The repo's scripts find `.venv` themselves (`.venv/bin`, or `.venv/Scripts` on Windows) and
stop if it is missing; `PYTHON=…` names another interpreter.

1. **Prerequisites:** Python 3.14 and git.
2. **Python environment** — for the hub's Python tooling: the parity generators (`tooling/parity/`), the fixture and
   baseline scripts (`tooling/`), and the export checker (`tooling/export-check/`):
   ```bash
   python3.14 -m venv .venv
   .venv/bin/pip install -r requirements-dev.txt        # on Windows: .venv/Scripts/pip
   ```
3. **VS Code:** open the folder and select `.venv` as the Python interpreter.
4. **Check it works:** `tooling/export-check/sync.sh --check`.

`tooling/parity/gen_web_icons.py` and `docs/playback-validation/` run with the Python edition's `.venv`, as their
headers say — they need its qtawesome and its modules.

## What lives here

- **Open work** — [GitHub Issues](https://github.com/dwsdolce/guitar-tap-project/issues) and the **Guitar Tap**
  Projects board. Each Issue links its detail document in [`docs/`](docs/); [`docs/README.md`](docs/README.md) is
  the index, and [`docs/completed/`](docs/completed/) the archive of finished work.
- **Shared specifications** — the "design once, implement on all three" contracts (`docs/INVENTORY.md`,
  `docs/PLAN.md` and each feature's spec).
- **Parity system** — [`tooling/parity/`](tooling/parity/) (the parity map, the oracle, the per-configuration
  baselines and their generators), [`tooling/TEST-COVERAGE.md`](tooling/TEST-COVERAGE.md), and the shared export
  checker [`tooling/export-check/`](tooling/export-check/).
- **Process** — [`process/`](process/): the release runbook (`RELEASE-CHECKLIST.md`), bug tracking, the
  developer-documentation standard, and where a document belongs (`DOC-PLACEMENT.md`).
- **Shared material** — third-party references (`references/`) and the manual-test corpus of recordings and
  measurements from every edition (`Tests/`).

Docs specific to one codebase (architecture, coding conventions, how to build, test and run it) stay in that
codebase's repo. The rule ([`process/DOC-PLACEMENT.md`](process/DOC-PLACEMENT.md)): **is it project work — tracked
as an Issue, or a spec, analysis or record for one? → here, even if it concerns one edition. Is it standing
developer reference for one codebase? → that repo.**

## Reporting a bug

File it wherever is easiest — an Issue on the relevant platform repo, or email support@dolcesfogato.com.
Reports are consolidated here on a project board for tracking, and you'll get a reply on whichever channel
you used.
