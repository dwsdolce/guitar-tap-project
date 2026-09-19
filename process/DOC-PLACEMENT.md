# Doc placement — where does a document live?

The rule for deciding whether a document belongs in the **project hub** (`guitar-tap-project`) or in one of
the code repos. One test, not case-by-case:

> **Is it project work** — tracked as a GitHub Issue / on the "Guitar Tap" board, or a spec/analysis/record
> for such work? → **the hub**, even if it concerns only one platform.
> **Is it standing developer documentation for a single codebase** (code-architecture guideline, coding
> conventions, how to build/test/run *that* repo)? → **that repo**.

The dividing line is **project work vs. developer reference**, *not* cross-platform vs. single-platform. A
Python-only bug spec is still a project document — it's tracked work — so it lives in the hub. What stays in
a repo is the standing "how this codebase is built and worked in" material. The result: every platform repo
stays **very clean** — code, tests, and its own developer docs, nothing about the project's work.

The test is a doc's **role**, not its subject: a doc *about* architecture that is tracked work (e.g.
`RESTRUCTURE-NOTES.md`) is a project document → hub; only a standing architecture *reference/guideline* is
developer documentation → repo.

## Scope — what lives where

| Hub (`guitar-tap-project`) — **project documents** | Repo — **developer documentation** |
|---|---|
| Open-item specs, bug analyses, detail docs (`docs/`) | Code-architecture guidelines |
| Parity system — `tooling/parity/` (`PARITY-MAP.md`, `parity-index.json`, the oracle, the generators) + `tooling/TEST-COVERAGE.md` | Coding conventions / style |
| `INVENTORY.md`, `PLAN.md` — the contract the port is measured against (`docs/`) | How to build / test / run this codebase |
| Process / how-to (`process/`: RELEASE-CHECKLIST, DEV-DOC-STANDARD, BUG-TRACKING, this doc) | *(plus all code, tests, per-repo build/deploy scripts)* |
| Shared third-party reference (`references/`); manual-test corpus (`Tests/`) | |
| Cross-repo **Issues** + the Projects **board** (the tracker) | |
| The project `README` + `docs/README.md` index | |

## Hub layout (all lowercase — cross-platform case-safety)

- `docs/` — project docs; `docs/completed/` archives finished project records.
- `process/` — how-to and conventions (this doc, `BUG-TRACKING.md`, `RELEASE-CHECKLIST.md`, `DEV-DOC-STANDARD.md`).
- `tooling/` — the parity system + `TEST-COVERAGE.md` + `guitartap_matrix.py`.
- `references/` — third-party reference material.
- `Tests/` — the cross-platform manual-test corpus.

**On completion:** a finished project's doc moves to `docs/completed/`. Any *living* convention it contains
belongs in `process/` (like this doc), not buried in the archived record — and a rule about how the
parity system is *run* belongs in [`../tooling/parity/README.md`](../tooling/parity/README.md) beside
its commands. Method (how we work) and operation (how a tool is run) live apart.

Worked example: closing #5, #7 and #10 produced
[`CROSS-EDITION-INVESTIGATION.md`](CROSS-EDITION-INVESTIGATION.md) here and the oracle operating rules
in the parity README, while the measurements stayed in `docs/completed/`.
