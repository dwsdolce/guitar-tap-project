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
- [#29](https://github.com/dwsdolce/guitar-tap-project/issues/29) · [`SAMPLE-BASED-TRIGGER.md`](SAMPLE-BASED-TRIGGER.md) — a sample-based tap trigger: analysis only, the input to a plan
- [#16](https://github.com/dwsdolce/guitar-tap-project/issues/16) · [`PLATFORM-BASELINES.md`](PLATFORM-BASELINES.md) — Windows and Linux baselines checked on the real machines, iPad and iPhone minted, the parity tolerance set
- [#32](https://github.com/dwsdolce/guitar-tap-project/issues/32) · [`THEME-MISSED-COLOURS.md`](THEME-MISSED-COLOURS.md) — theme colours the inventories missed: an edition using a default colour where Swift uses a role
- [#9](https://github.com/dwsdolce/guitar-tap-project/issues/9) · [`SAVED-MEASUREMENTS-ORDERING.md`](SAVED-MEASUREMENTS-ORDERING.md) — Saved Measurements sort / reorder
- [#12](https://github.com/dwsdolce/guitar-tap-project/issues/12) · [`TEST-PLAN.md`](TEST-PLAN.md) — the tri-platform test definition — currently Swift-centric and stale
- [#18](https://github.com/dwsdolce/guitar-tap-project/issues/18) · [`MEASUREMENT-TYPE-SELECTION.md`](MEASUREMENT-TYPE-SELECTION.md) — move measurement-type selection out of Settings; what New Tap means in a comparison
- [#25](https://github.com/dwsdolce/guitar-tap-project/issues/25) · [`ANNOTATION-DEFAULT-POSITION.md`](ANNOTATION-DEFAULT-POSITION.md) — where an untouched peak label sits, how it behaves under zoom, and how labels are clipped
- [#23](https://github.com/dwsdolce/guitar-tap-project/issues/23) · [`LINUX-APPIMAGE.md`](LINUX-APPIMAGE.md) — the Linux AppImage does not start on older Linux (built on glibc 2.39; old runtime needs `libfuse2`)
- [#15](https://github.com/dwsdolce/guitar-tap-project/issues/15) · [`guitar_tap-manual-seo-handoff.md`](guitar_tap-manual-seo-handoff.md) — `/guitar_tap/manual/` indexed as "Page with redirect"
- [#14](https://github.com/dwsdolce/guitar-tap-project/issues/14) · [`ANDROID-PLAN.md`](ANDROID-PLAN.md) — native Android (Kotlin/Compose) edition: phased port plan and architecture decisions
  - [`ANDROID-FEASIBILITY.md`](ANDROID-FEASIBILITY.md) — Phase 0 record: the two yes/no checks, device matrix, source survey
  - [`PHASE1-PORT-PREP.md`](PHASE1-PORT-PREP.md) — Phase 1 record: INVENTORY audit, parity-tooling generalisation, fixture drift check
  - Both are records of finished phases; they move to [`completed/`](completed/) with the plan when the port concludes.

One open Issue has no detail doc at all: [#11](https://github.com/dwsdolce/guitar-tap-project/issues/11)
(open-sourcing) points at the archived [`completed/PROJECT-HUB-REPO.md`](completed/PROJECT-HUB-REPO.md).
Deliberate — the design history really is finished — but an archive doing live duty is worth
re-checking whenever that Issue moves.

#17 (sweep every `@parity` slug) is **closed**; its record is
[`completed/SLUG-SWEEP.md`](completed/SLUG-SWEEP.md) — Stage 1 swept every slug for false twins, untagged files and
dead tests; Stage 2 moved each slug's cases into shared data the three editions' runners read, tagged every test
file and linked every code group to its tests, and removed the architectural divergences the sweep turned up.

#2 (Light / Dark / System theme) is **closed**; its record is
[`completed/THEME-SPEC.md`](completed/THEME-SPEC.md), with its inventories and export findings in
[`completed/theme/`](completed/theme/) — one role table shared by all three editions (`theme.json`), the scheme
followed live, exports from the light values, the export regression tests on CI, and the platform run-review.

#6 (results panel consistency) is **closed**; its record is
[`completed/RESULTS-PANEL-CONSISTENCY.md`](completed/RESULTS-PANEL-CONSISTENCY.md) — the Analysis Results panel
(guitar, plate, brace, comparison and per-tap views) takes Python's sizes and Swift's wording in all three; two
divider roles; one icon set for Python and the web; tinted buttons without outlines, with hover and a two-state
on fill.

#3 (audio buffer size) is **closed**; its record is
[`completed/AUDIO-BUFFER-SIZE.md`](completed/AUDIO-BUFFER-SIZE.md) — the same tap gives the same samples
in every edition: Swift's 4800-frame buffers cut into 1024-sample chunks, the guitar window's audio ending
at a fixed length, the onset found from the noise just before the tap, and ring-out measured from the
window's samples; verified live, the three editions' windows and ring-outs are identical.

#30 (Swift recording from the wrong microphone) is **closed**; its record is
[`completed/WRONG-INPUT-DEVICE.md`](completed/WRONG-INPUT-DEVICE.md) — after a hot-plug with another
application opening the same microphone, macOS could leave Swift's engine on the built-in microphone while
Settings showed the selected one; the watchdog now checks the device the engine is really on and restarts,
and Python checks the device it opened by name.

#20 (Windows mic level too low) is **closed**; its record is
[`completed/WINDOWS-MIC-LEVEL-AUDIO-EFFECTS.md`](completed/WINDOWS-MIC-LEVEL-AUDIO-EFFECTS.md) — the Windows
audio effects cost ~70 dB on a customer's laptop; the customer works with Audio enhancements Off, and the
Python edition now opens WASAPI in RAW mode so the setting isn't needed (a beta check by the customer is
still to come).

#24 (Python stream-restart coordination) is **closed**; its record is
[`completed/STREAM-RESTART-COORDINATION.md`](completed/STREAM-RESTART-COORDINATION.md) — a PortAudio
re-initialise skipped for a stuck close is retried; the watchdog and the hot-plug refresh follow Swift's
ordering; a settle no longer captures its own transient; Swift no longer ends up stopped after quick replugs.

#21 (microphone selection) is **closed**; its record is
[`completed/MIC-SELECTION.md`](completed/MIC-SELECTION.md) — the saved microphone wins at launch, else the
system default; every selection is saved, so what Settings shows is what the next launch uses; a device
that cannot be opened is never selected; verified on macOS, Windows and Linux (Linux without hot-plug).

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
