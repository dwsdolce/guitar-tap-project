# Project docs

Project documentation for **Guitar Tap** — the cross-platform tap-tone analyzer (Swift · Python · web,
with an Android edition proposed: [#14](https://github.com/dwsdolce/guitar-tap-project/issues/14)).

**Open work lives in GitHub, not in a markdown file:**
- **Open items / roadmap** → [Issues](https://github.com/dwsdolce/guitar-tap-project/issues) + the **Guitar Tap** Projects board. Each Issue links its detail doc (below).
- **Completed work** → closed Issues + [`completed/`](completed/) (the historical archive). A frozen pre-Issues done log is kept in [`STATUS.md`](STATUS.md).

## Reference (living — consult, don't complete)
- [`INVENTORY.md`](INVENTORY.md) — the spec extracted from canonical Swift; the contract the port is measured against.
- [`PLAN.md`](PLAN.md) — overall migration plan & parity bar.

## Open-item detail docs (each paired with its Issue — keep both directions live)
- [#1](https://github.com/dwsdolce/guitar-tap-project/issues/1) · [`RESTRUCTURE-NOTES.md`](RESTRUCTURE-NOTES.md) — architectural-parity restructure (view layer)
- [#29](https://github.com/dwsdolce/guitar-tap-project/issues/29) · [`SAMPLE-BASED-TRIGGER.md`](SAMPLE-BASED-TRIGGER.md) — a sample-based tap trigger: analysis only, the input to a plan
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

#37 (Python crashed at start when PortAudio could not start) is **closed**; its record is
[`completed/PYTHON-NO-AUDIO-SYSTEM.md`](completed/PYTHON-NO-AUDIO-SYSTEM.md) — `sounddevice` loaded once, kept
when only PortAudio's start fails; the app starts and reports "Audio input unavailable".

#36 (Swift runtime warnings) is **closed**; its record is
[`completed/SWIFT-RUNTIME-WARNINGS.md`](completed/SWIFT-RUNTIME-WARNINGS.md) — the alert bindings no longer publish
within a view update; the audio session set up once per start with one category; the activation on the main thread
accepted, as every edition starts its input synchronously.

#31 (Swift: each spectrum update rebuilt the whole window) is **closed**; its record is
[`completed/SWIFT-SPECTRUM-WINDOW-REBUILD.md`](completed/SWIFT-SPECTRUM-WINDOW-REBUILD.md) — the threshold meter's
own timer gone, and the live frame on its own object; listening, the main thread busy 34 % → 8.7 %.

#38 (tap detection threading) is **closed**; its record is
[`completed/TAP-DETECTION-THREADING.md`](completed/TAP-DETECTION-THREADING.md) — tap detection and capture are one
per-chunk sequence on the main thread in every edition, as on the web; the fast-start is gone.

#35 (zoom and pan slow with many peaks — Python's view updating) is **closed**; its record is
[`completed/RESULTS-LIST-ON-RANGE-CHANGE.md`](completed/RESULTS-LIST-ON-RANGE-CHANGE.md) — Python's views update as
Swift's do, through a shared layer (one refresh per event-loop turn, lists and labels updated in place, styles set
only on change); the spectrum drawn for its visible range only, unantialiased; every source file in the parity map;
the crosshair read as Swift's; Python's tap bar laid out as Swift's.

#32 (theme — the colours the inventories missed) is **closed**; its record is
[`completed/THEME-MISSED-COLOURS.md`](completed/THEME-MISSED-COLOURS.md) — every colour in every edition a named
role or the platform's by rule (style guide S1–S7, S1a–S1c); app-drawn buttons in four kinds; one dimming
mechanism; one plain chart menu and the chart help by device; one icon set in Python and the web, with the app's
own icons generated from the hub; "⚠" in its text form; and the defects found in its run-reviews, among them
Settings' stack overflow on an iPhone.

#34 (one unreadable measurement emptied the library) is **closed**; its record is
[`completed/UNREADABLE-LIBRARY-ENTRY.md`](completed/UNREADABLE-LIBRARY-ENTRY.md) — one reader in every edition (a
list of measurements, each entry decoded on its own): a library with an entry that cannot be read loads the rest,
keeps a copy aside once and says where in the user's terms; an import imports the rest and says what it skipped.

#16 (platform baselines) is **closed**; its record is
[`completed/PLATFORM-BASELINES.md`](completed/PLATFORM-BASELINES.md) — Windows and Linux pass against their
CI-minted baselines on the real machines; iPad and iPhone have baselines of their own (device and simulator, two
configurations); the cross-edition parity bars are set at about ten times the measured spread; CI runs Swift's
unit tests on the iPad and iPhone simulators, and its simulator export jobs no longer fail now and then.

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
- [`../process/`](../process/) — how-to & conventions: `RELEASE-CHECKLIST.md`, `DEV-DOC-STANDARD.md`, `DOC-PLACEMENT.md` (where docs live), `BUG-TRACKING.md` (intake + tracking model), `CROSS-EDITION-INVESTIGATION.md` (how to find out why two editions disagree about a number), `STYLE-GUIDE.md` (how every edition looks: platform or app, colour, opacity, type, control states, icons), `WEB-UI-GUIDELINES.md` (how the desktop/mobile UI translates to the web), `ANDROID-UI-GUIDELINES.md` (how the Swift UI translates to Android, tablet-first). The hub's own standup record is archived in [`completed/PROJECT-HUB-REPO.md`](completed/PROJECT-HUB-REPO.md).
- [`images/`](images/), [`playback-validation/`](playback-validation/) — screenshots + the playback-validation harness.
