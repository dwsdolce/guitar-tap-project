# Project docs

Project documentation for **Guitar Tap** — the cross-platform tap-tone analyzer (Swift · Python · web).

**Open work lives in GitHub, not in a markdown file:**
- **Open items / roadmap** → [Issues](https://github.com/dwsdolce/guitar-tap-project/issues) + the **Guitar Tap** Projects board. Each Issue links its detail doc (below).
- **Completed work** → closed Issues + [`completed/`](completed/) (the historical archive). A frozen pre-Issues done log is kept in [`STATUS.md`](STATUS.md).

## Reference (living — consult, don't complete)
- [`INVENTORY.md`](INVENTORY.md) — the spec extracted from canonical Swift; the contract the port is measured against.
- [`PLAN.md`](PLAN.md) — overall migration plan & parity bar.
- [`WEB-UI-GUIDELINES.md`](WEB-UI-GUIDELINES.md) — how the desktop/mobile UI translates to the web (port-era).
- [`PROJECT-HUB-REPO.md`](PROJECT-HUB-REPO.md) — the hub's own design + standup checklist.

## Open-item detail docs (each linked from its Issue)
- [`RESTRUCTURE-NOTES.md`](RESTRUCTURE-NOTES.md) — architectural-parity restructure (view layer)
- [`THEME-SPEC.md`](THEME-SPEC.md) — Light / Dark / System theme
- [`AUDIO-BUFFER-SIZE.md`](AUDIO-BUFFER-SIZE.md) — Swift 4800-frame buffer
- [`AUDIO-WATCHDOG-SILENT-STREAM.md`](AUDIO-WATCHDOG-SILENT-STREAM.md) — watchdog blind to digital silence
- [`MATERIAL-MULTITAP-DISCREPANCIES.md`](MATERIAL-MULTITAP-DISCREPANCIES.md) — multi-tap material divergence
- [`PLAYBACK-BIT-IDENTITY.md`](PLAYBACK-BIT-IDENTITY.md) — replay ≠ live capture (~0.02 dB)
- [`FROZEN-RECALC-TEST-PARITY.md`](FROZEN-RECALC-TEST-PARITY.md) — Python↔Swift test-fixture divergence
- [`RESULTS-PANEL-CONSISTENCY.md`](RESULTS-PANEL-CONSISTENCY.md) — Results panel cross-platform consistency
- [`SAVED-MEASUREMENTS-ORDERING.md`](SAVED-MEASUREMENTS-ORDERING.md) — Saved Measurements sort / reorder

## Elsewhere in the hub
- [`../tooling/`](../tooling/) — the parity system (`PARITY-MAP.md`, `parity-index.json`, `parity-oracle.json`, the generators) + [`TEST-COVERAGE.md`](../tooling/TEST-COVERAGE.md).
- [`../process/`](../process/) — how-to docs: `RELEASE-CHECKLIST.md`, `DEV-DOC-STANDARD.md`.
- [`images/`](images/), [`playback-validation/`](playback-validation/) — screenshots + the playback-validation harness.
