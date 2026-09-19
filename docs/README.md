# Project docs

Project documentation for **Guitar Tap** — the cross-platform tap-tone analyzer (Swift · Python · web,
with an Android edition proposed: [#14](https://github.com/dwsdolce/guitar-tap-project/issues/14)).

**Open work lives in GitHub, not in a markdown file:**
- **Open items / roadmap** → [Issues](https://github.com/dwsdolce/guitar-tap-project/issues) + the **Guitar Tap** Projects board. Each Issue links its detail doc (below).
- **Completed work** → closed Issues + [`completed/`](completed/) (the historical archive). A frozen pre-Issues done log is kept in [`STATUS.md`](STATUS.md).

## Reference (living — consult, don't complete)
- [`INVENTORY.md`](INVENTORY.md) — the spec extracted from canonical Swift; the contract the port is measured against.
- [`PLAN.md`](PLAN.md) — overall migration plan & parity bar.
- [`WEB-UI-GUIDELINES.md`](WEB-UI-GUIDELINES.md) — how the desktop/mobile UI translates to the web (port-era).
- [`ANDROID-UI-GUIDELINES.md`](ANDROID-UI-GUIDELINES.md) — how the Swift UI translates to Android (tablet-first).

## Open-item detail docs (each paired with its Issue — keep both directions live)
- [#1](https://github.com/dwsdolce/guitar-tap-project/issues/1) · [`RESTRUCTURE-NOTES.md`](RESTRUCTURE-NOTES.md) — architectural-parity restructure (view layer)
- [#2](https://github.com/dwsdolce/guitar-tap-project/issues/2) · [`THEME-SPEC.md`](THEME-SPEC.md) — Light / Dark / System theme
- [#3](https://github.com/dwsdolce/guitar-tap-project/issues/3) · [`AUDIO-BUFFER-SIZE.md`](AUDIO-BUFFER-SIZE.md) — Swift 4800-frame buffer
- [#8](https://github.com/dwsdolce/guitar-tap-project/issues/8) · [`FROZEN-RECALC-TEST-PARITY.md`](FROZEN-RECALC-TEST-PARITY.md) — Python↔Swift test-fixture divergence
- [#6](https://github.com/dwsdolce/guitar-tap-project/issues/6) · [`RESULTS-PANEL-CONSISTENCY.md`](RESULTS-PANEL-CONSISTENCY.md) — Results panel cross-platform consistency
- [#9](https://github.com/dwsdolce/guitar-tap-project/issues/9) · [`SAVED-MEASUREMENTS-ORDERING.md`](SAVED-MEASUREMENTS-ORDERING.md) — Saved Measurements sort / reorder
- [#12](https://github.com/dwsdolce/guitar-tap-project/issues/12) · [`TEST-PLAN.md`](TEST-PLAN.md) — the tri-platform test definition — currently Swift-centric and stale
- [#15](https://github.com/dwsdolce/guitar-tap-project/issues/15) · [`guitar_tap-manual-seo-handoff.md`](guitar_tap-manual-seo-handoff.md) — `/guitar_tap/manual/` indexed as "Page with redirect"
- [#14](https://github.com/dwsdolce/guitar-tap-project/issues/14) · [`ANDROID-PLAN.md`](ANDROID-PLAN.md) — native Android (Kotlin/Compose) edition: phased port plan and architecture decisions
  - [`ANDROID-FEASIBILITY.md`](ANDROID-FEASIBILITY.md) — Phase 0 record: the two yes/no checks, device matrix, source survey
  - [`PHASE1-PORT-PREP.md`](PHASE1-PORT-PREP.md) — Phase 1 record: INVENTORY audit, parity-tooling generalisation, fixture drift check
  - Both are records of finished phases; they move to [`completed/`](completed/) with the plan when the port concludes.

One open Issue has no detail doc at all: [#11](https://github.com/dwsdolce/guitar-tap-project/issues/11)
(open-sourcing) points at the archived [`completed/PROJECT-HUB-REPO.md`](completed/PROJECT-HUB-REPO.md).
Deliberate — the design history really is finished — but an archive doing live duty is worth
re-checking whenever that Issue moves.

#5 (multi-tap material divergence) is **closed**; its record is
[`completed/MATERIAL-MULTITAP-DISCREPANCIES.md`](completed/MATERIAL-MULTITAP-DISCREPANCIES.md) — item 3's
2 dB was old code in the archived evidence; the editions agree to 0.0004 dB on a capture made today.

#7 (replay vs live capture) is **closed**; its record is
[`completed/PLAYBACK-BIT-IDENTITY.md`](completed/PLAYBACK-BIT-IDENTITY.md) — replay of an app-dumped WAV
reproduces the live capture to one float32 ULP; the apparent discrepancy came from a fixture that was
not an app dump.

#10 (oracle unification) is **closed**; its record is
[`completed/PARITY-AND-REGRESSION-BASELINES.md`](completed/PARITY-AND-REGRESSION-BASELINES.md), which
carries the two-bar model and the measured evidence behind the parity numbers. The capture-alignment
cause it uncovered is **not** finished and lives in
[#7](https://github.com/dwsdolce/guitar-tap-project/issues/7).

## Elsewhere in the hub
- [`../tooling/`](../tooling/) — the parity system (`PARITY-MAP.md`, `parity-index.json`, `parity-oracle.json`, the generators) + [`TEST-COVERAGE.md`](../tooling/TEST-COVERAGE.md).
  - `sync-oracle.sh` vendors the oracle *out* to each repo; `collect-baselines.py` pulls each configuration's self-baseline *in* to `parity/baselines/`, and `parity-report.py` turns them into the edition-vs-platform numbers behind the parity tolerance ([`completed/PARITY-AND-REGRESSION-BASELINES.md`](completed/PARITY-AND-REGRESSION-BASELINES.md)). `compare-capture-probes.py` localises a cross-edition capture difference for [#7](https://github.com/dwsdolce/guitar-tap-project/issues/7).
- [`../process/`](../process/) — how-to & conventions: `RELEASE-CHECKLIST.md`, `DEV-DOC-STANDARD.md`, `DOC-PLACEMENT.md` (where docs live), `BUG-TRACKING.md` (intake + tracking model), `CROSS-EDITION-INVESTIGATION.md` (how to find out why two editions disagree about a number). The hub's own standup record is archived in [`completed/PROJECT-HUB-REPO.md`](completed/PROJECT-HUB-REPO.md).
- [`images/`](images/), [`playback-validation/`](playback-validation/) — screenshots + the playback-validation harness.
