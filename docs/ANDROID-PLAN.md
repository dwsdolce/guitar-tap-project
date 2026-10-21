# GuitarTap Android — Port Plan

**Status:** draft for review (2026-09-16). No Issue yet. **Phase 0 is complete**: audio capture yes, USB
measurement mic yes — a Blue Snowball attaches directly, a UMIK-1 needs any USB 2.0 hub in between
(powered or not; the cause is unknown and two explanations have already been refuted, see
ANDROID-FEASIBILITY §3). The hardware does the job; what remains is
the decision to commit to a fourth edition, then Phase 1. Findings in
[ANDROID-FEASIBILITY.md](ANDROID-FEASIBILITY.md); the throwaway spike that answered them is in
`feasibility/` of the private [GuitarTapAndroid](https://github.com/dwsdolce/GuitarTapAndroid) repo.

## Scope

A native Android port of the Swift GuitarTap app, maintained long-term alongside the other editions: the
same relationship Python and web have with Swift today.

- **Canonical reference:** Swift stays the spec for algorithm and UX. Android tracks it; behaviour changes
  start in Swift and spread outward.
- **Fourth edition:** Swift · Python · web · **Android**. Every `@parity` group gains a fourth column.
- **Native, not wrapped.** Kotlin + Jetpack Compose. A WebView wrapper around GuitarTapWeb (the Palmas
  approach) was considered and rejected. Guitar Tap *measures* the microphone signal, and a WebView can't
  control that signal:
  - It can't request `AudioSource.UNPROCESSED`, and `getUserMedia`'s processing-off constraints are hints
    an OEM may ignore.
  - The browser resamples input to the context rate (PLAN.md risk #1).
  - It can't pin a USB measurement mic.
  - The web's export path (`showSaveFilePicker` / `<a download>`) doesn't work inside a WebView.
- **Repo:** **`GuitarTapAndroid`** (decided 2026-09-15), a sibling of the other code repos
  (`~/src/GuitarTapAndroid`); a **private** GitHub repo, created 2026-09-15 to hold the Phase 0 spike. App ID
  `com.dolcesfogato.guitartap`, following Swift's `com.dolcesfogato.GuitarTap` and Palmas's
  `com.dolcesfogato.palmas`. Licence GPL-3.0, as for the other editions.

## Fidelity Bar

The same bar as [PLAN.md](PLAN.md#fidelity-bar), extended to a fourth implementation. Given the same WAV or
the same `.guitartap` file:

- **Numeric outputs** (peak frequencies, magnitudes, Q, material properties) agree to the oracle
  tolerances.
- **Categorical outputs** (peak picks, onset indices, tap decisions, peak counts, mode assignments) match
  exactly.
- **File round-trip:** a `.guitartap` written by Android reads identically in Swift, Python and web, and the
  reverse.

Not bit-identical floating point, for the reasons PLAN.md gives.

That is the whole bar, and it is the same one the other three editions meet. **There is no extra
live-capture bar for Android.** An earlier draft invented one ("within the tap-to-tap spread of Swift on
iPhone"), which had no precedent: real-instrument agreement is checked once per release through
`Tests/AllPlatforms/`, for every edition alike.

## Target Devices

- **Primary: Android tablets** (decided 2026-09-16). The app suits a tablet far better than a phone — the
  spectrum chart, the results panel and the measurements library all want the width, which is why the iPad
  regular-width layout is the rich one. It is also the only Android hardware being bought for this project.
- **Secondary:** Android phones, portrait and landscape. Built and kept working, but **verified on the
  emulator**: no Android phone is being acquired for testing, so phone layouts are never run-reviewed on
  real hardware. Say so when a phone-specific bug is reported.
- **Measurement mics:** the built-in mic, plus USB-C audio-class mics (UMIK-1 with a `.cal` file). USB
  support varies by **device and mic combination**, and is confirmed per pairing, not assumed: on the first
  test tablet a Blue Snowball attaches directly while a UMIK-1 only enumerates through a USB 2.0 hub — any
  hub, powered or not — with no descriptor difference to predict it (ANDROID-FEASIBILITY §3). Both paths
  ship, and the UI must make a mic that fails to appear diagnosable.
- **SDK levels:**
  - `targetSdk`/`compileSdk` 36, matching Palmas.
  - `minSdk` **28** proposed. 28 adds `AudioRecord.getActiveMicrophones()`, whose `MicrophoneInfo` reports
    the mic's frequency response; `UNPROCESSED` and `AudioDeviceCallback` are older. See Open Questions.

## Architecture Decisions (decided up front — each is a lesson the web port paid for)

1. **Mirror Swift's structure file-for-file.** The web port's biggest rework was structural, not numeric:
   - It merged `TapToneAnalyzer` + `RealtimeFFTAnalyzer` into one engine, then took about 10 staged steps
     to undo it ([TAPTONEANALYZER-CONSOLIDATION](completed/TAPTONEANALYZER-CONSOLIDATION.md)).
   - It split views differently from Swift ([RESTRUCTURE-NOTES](RESTRUCTURE-NOTES.md)).

   On Android, `TapToneAnalyzer` (a ViewModel exposing `StateFlow`) **owns all measurement state** and
   holds a `RealtimeFFTAnalyzer`. Swift extensions (`TapToneAnalyzer+SpectrumCapture.swift`, …) map to
   Kotlin files of the same name (`TapToneAnalyzerSpectrumCapture.kt`, …). A Swift view maps to one
   composable file of the same name. Structural identity is what prevents the bugs in
   [PLATFORM-PARITY-GAPS](completed/PLATFORM-PARITY-GAPS.md).
2. **`@parity` tags and Swift/Python test names from the first commit.** The web added tags in Phase 6 and
   used its own `g#` test names. Android starts tagged, with test names matching Swift/Python.
3. **Modules:**
   - `:core`: pure Kotlin/JVM with no Android imports. Holds the DSP, the models and the `.guitartap`
     codec, and runs as plain JVM unit tests in CI.
   - `:audio`: the Android capture engine, behind an `AudioSource` interface so file playback and tests
     drive the same pipeline.
   - `:app`: Compose UI, persistence, export.
4. **Capture engine:** `AudioRecord` with `ENCODING_PCM_FLOAT` on a dedicated thread, in blocking reads.
   Not Oboe/AAudio:
   - Guitar Tap analyses the signal, it doesn't monitor it, so low latency buys nothing.
   - `AudioRecord` keeps the app free of NDK/C++ code, and so of Play's 16 KB page-alignment rule.
   - Phase 0 confirmed `AudioRecord` gets unprocessed input on the first device; revisit only if another
     device proves otherwise.

   Source selection, in order:
   1. `UNPROCESSED`, when `AudioManager.getProperty(PROPERTY_SUPPORT_AUDIO_SOURCE_UNPROCESSED)` is true.
   2. `VOICE_RECOGNITION`, which is specified as AGC-free.
   3. `MIC`.

   **Never** `VOICE_COMMUNICATION`, which enables echo cancellation and noise suppression — verified to
   do so **even when a USB mic is attached**. **Never `CAMCORDER` either**: on the test tablet it ignored
   an attached UMIK-1 and routed to the built-in back mic, which would have a user measuring the wrong
   microphone without knowing (ANDROID-FEASIBILITY §3). The source in use, **and the device actually
   routed to**, are shown in Metrics and saved with the measurement, as the sample rate is —
   `getRoutedDevice()` is checked after start rather than assuming the request was honoured.
5. **Re-chunk to exactly 1024 samples, from day one.** Android buffer sizes vary by device. Swift on macOS
   actually receives 4800-frame buffers and cuts them into 1024-sample chunks
   ([AUDIO-BUFFER-SIZE](completed/AUDIO-BUFFER-SIZE.md), #3). Android does the same, so live and playback
   share one chunk grid.
6. **Audio clock, not wall clock.** Warm-up and cooldown run on `audioElapsed`, and each chunk carries its
   timestamp to the analyzer ([DECAY-AUDIO-CLOCK-FIX](completed/DECAY-AUDIO-CLOCK-FIX.md)); ring-out is
   measured from the samples of the tap's window ([AUDIO-BUFFER-SIZE](completed/AUDIO-BUFFER-SIZE.md) item 8).
7. **FFT:** port the existing TypeScript `src/dsp/fft.ts`. It is already oracle-validated, and a
   65536-point FFT every ~1.4 s is trivial on any phone. No third-party DSP library, which avoids licence
   and numeric-drift questions.
8. **Chart:** a custom Compose `Canvas` renderer, as the web chose (`spectrumRender.ts`), not a chart
   library. The same draw code renders to a `PdfDocument` page canvas and a `Bitmap`, so PDF, PNG and screen
   can't disagree.
9. **Material peaks are separate from guitar peaks.** Follow the web model, not Swift/Python's shared
   `currentPeaks`, which caused the loaded-plate fL loss. This is a **documented, deliberate structural
   exception** to decision 1, tagged in the code.
10. **Layout: follow the iOS branches, explicitly.** Swift has ~155 `#if os` / size-class / `UIDevice`
    branches across 30 files:
    - **Expanded width ↔ iPad regular (`iPadHorizontalLayout`) — the primary layout**, since tablets are the
      primary target. Results inline at 360–480 pt, as on iPad.
    - Compact width ↔ iPhone (`standardVerticalLayout`, `phoneLandscapeLayout`), built and kept correct but
      emulator-verified only.
    - Medium width: decide in Phase 4.

    Resolve each branch on its own merits, and never inherit the choice from Python or web. Python copying
    the wrong gate (`compactStatusBar` vs `fullStatusBar`) is a recorded parity bug.

## Prerequisites — which open Issues to finish first

The filter is not "which issues are important" but **does Android copy it, or does Android
multiply it?** Every unfinished cross-cutting item becomes a four-edition job the moment Android
exists, and anything that changes canonical Swift gets ported twice if the port starts first.

### Finish before Android code starts (Phases 2–3)

**Status 2026-10-19: all the gates are CLOSED — the three original ones, and #17, their successor (closed 2026-10-19).**

| Issue | Status | Why it gates the port |
|---|---|---|
| **#10 Unify test goldens onto the shared oracle** | ✅ **CLOSED** | The highest-leverage one. Only the web read `parity-oracle.json`; Swift and Python hardcoded the same numbers. All three suites now read the shared oracle, so Android consumes one source instead of becoming a fourth hardcoded copy. |
| **#5 Material multi-tap: Swift ~2 dB / sub-bin below Python/web** | ✅ **CLOSED** | A numeric disagreement in the code Android mirrors. Re-measured on the current build and found already fixed — the archived finding was stale. "Canonical" is now unambiguous where Android's material path is validated. |
| **#8 Python↔Swift fixture divergence (frozen-recalc)** | ✅ **CLOSED** | Android ports the tests and the fixtures. That slug is now 37 of 37 behaviours covered in all three editions, every test carrying its id. **But see #17 below — it closed this slug and opened the same question for the other 43.** |
| **#17 Sweep every `@parity` slug** | ✅ **CLOSED** (2026-10-19) | Inherits #8's reasoning and widens it. #8 read one slug out of 44 and found eight tests measuring nothing, two false-twin rows, and a data bug in shipped code — and that slug looked *healthier* than several others by test-count spread. Android ports tests and fixtures from all of them. Porting against fixtures that already disagree is how a day disappears into a phantom bug; porting against 43 unswept slugs is how a week does. |

**How much of #17 must land first is a judgement, not a given.** Its Stage 1 (sweep and triage) is
what protects the port — it is the part that says which slugs are trustworthy to port from. Its
Stage 2 (shared case data) is a *maintenance* win that would also make Android cheaper, but the port
does not strictly wait on it. A defensible middle: require Stage 1 for the slugs Android actually
ports in Phases 2–3 (DSP, capture, state), rather than all 44 before any Kotlin is written.
See [`completed/SLUG-SWEEP.md`](completed/SLUG-SWEEP.md).

### Finish before the Android UI (Phase 4)

| Issue | Why | Status |
|---|---|---|
| **#2 Theme — Light / Dark / System** | [ANDROID-UI-GUIDELINES](../process/ANDROID-UI-GUIDELINES.md) encodes the spec's exact hex values, so the theme's decisions should be made by the spec rather than accidentally by whichever edition implements first. | **Closed 2026-10-12.** Every colour role, light and dark, is in the shared table `tooling/parity/cases/theme.json`, which each edition's palette test checks — the source for Android's palette too. Record: [`completed/THEME-SPEC.md`](completed/THEME-SPEC.md). |
| **#6 Results panel cross-platform consistency** | Presentation-only, but it is the panel Android copies. Settle it once rather than porting the disagreement and then fixing it in four places. | **Closed.** Record: [`completed/RESULTS-PANEL-CONSISTENCY.md`](completed/RESULTS-PANEL-CONSISTENCY.md). |

### Not blocking

- **#1 Architectural-parity restructure (view layer)** — see below; Android is already on the
  target side of it.
- **#3 Swift audio buffer (4800 frames)** — Android re-chunks to 1024 from day one, so it is not
  waiting on this. Worth landing fix A before the Android corpus capture in Phase 6, so both are
  on the same chunk grid.
- **#4 silent-stream watchdog** ✅ **CLOSED** and **#7 replay bit-identity** ✅ **CLOSED** — both
  settled 2026-09; #7's premise turned out to hold only for a non-app-dump fixture. Android no
  longer needs to resolve either, though its 1024 re-chunking and its ability to force a silenced
  stream (background the app, which Android silences and reports through `isClientSilenced`) remain
  useful if they recur.
- **#12 TEST-PLAN.md rewrite** — stale and Swift-centric; rewrite it once as a four-edition
  document instead of doing tri-platform now and redoing it. **Check it against #17 before
  starting either** — a tri-platform test definition and a sweep of every test slug may cover
  the same ground.
- **#9 Saved Measurements sort**, **#11 open-source the repos** — orthogonal. #9 is additive:
  before Android it is three implementations, after it is four.

### Why #1 does not gate the port

The model layers across the three editions were made consistent through a lot of deliberate
work. **The view layer is the part that never converged**, for two reasons that have nothing to
do with Android: Qt is imperative where SwiftUI and React are declarative, and the Python code
predates the Swift app — it grew from an older version and was never fully reorganised to match
once Swift became canonical. That history is why view-layer "equivalence" is hard to assert, and
why the parity map is honest about `view/*` groups being **review only**.

Android changes none of that, and is not blocked by it:

- **Android can mirror Swift's view structure from the first commit — but being declarative is
  not what makes that happen.** The web was declarative (React) and greenfield too, and it still
  diverged: one Swift view became several components, and peak-selection state settled in the
  view rather than the analyzer. The framework neither caused nor prevented that; the decisions
  taken during the port did. What is different for Android is only that the failure mode is
  known in advance and the rules are stated up front — one Kotlin file per Swift view file,
  `@parity` tags and Swift/Python test names from the first commit (the web added tags in Phase 6,
  after its structure had set), and `TapToneAnalyzer` owning measurement state. Those rules are
  [Architecture Decisions 1–2](#architecture-decisions-decided-up-front--each-is-a-lesson-the-web-port-paid-for);
  if they are not held to, Android will diverge exactly as the web did, and no framework choice
  will prevent it.
- **On the one item that is really a model question, Swift is already the target.** P3 in
  [RESTRUCTURE-NOTES](RESTRUCTURE-NOTES.md) moves peak-selection and annotation ownership onto
  the analyzer *with Swift's by-frequency preservation* — because `TapToneAnalyzer` already owns
  that subsystem in Swift and the web keeps it view-side. Android mirroring Swift lands on the
  target by construction. When P3 ships, the two parked test suites go from 3-way to 4-way, with
  Android needing no rework.
- **Expect asymmetry in the map, and do not read it as a defect.** Once Android matches Swift's
  view structure, some `view/*` groups will pair Swift and Android neatly while Python's
  counterpart is shaped differently. That is the pre-existing Qt/legacy divergence becoming
  visible, not something the Android port introduced. The map asserts co-location; behaviour is
  proven by the tests and by run-review.

## Phased Plan

### Phase 0 — Two yes/no checks, then build ✅ COMPLETE (2026-09-16)

Two things could have made a native Android edition pointless. Everything else is development work, and is
verified the way the web port was: against the oracle and the shared fixtures as the code is written.

1. **Can the app capture usable audio?** — ✅ **yes.** `AudioRecord` delivers float PCM at 48 kHz from a
   selectable source with no effects applied; nothing filters 20–60 Hz on the sources the plan uses.
2. **Can a USB measurement mic be used?** — ✅ **yes.** A Blue Snowball attaches directly to the Lenovo
   TB305FU and records; a UMIK-1 takes power but never enumerates directly, and needs a USB 2.0 hub. Both
   are full-speed composite audio+HID devices declaring 100 mA, so nothing in the descriptors predicts the
   difference, and the hub does not need external power — which rules out both the speed and the current
   explanations. The cause is open; it does not block the port. Android auto-routes capture to whichever
   is attached, at 48 kHz with no effects.

Findings and device data: [ANDROID-FEASIBILITY.md](ANDROID-FEASIBILITY.md). The throwaway spike that
answered check 1 stays in `GuitarTapAndroid/feasibility/` as a measuring instrument for Phase 3.

**Deliberately NOT a gate:** comparing Air/Top/Back against Swift on a real instrument. The other editions
were built first and compared afterwards — `Tests/AllPlatforms/` was captured 2026-07-30 as a pre-ship gate
for 1.0.2, not a prerequisite for writing any of them. Android does the same: the corpus capture belongs to
the release checklist (Phase 7), not to the start. Nor would a poor result stop the port: every plate and
brace capture in the corpus was made with a UMIK-1 on every platform but one, so "this tablet's built-in mic
is weak at 35 Hz" would mean "use a measurement mic", exactly as elsewhere.

### Phase 1 — Contract refresh + tooling generalisation

Most of this pays off for all editions, not just Android.

- **Refresh [INVENTORY.md](INVENTORY.md) against current Swift.** Its content dates from 2026-06-22.
  - The DSP, detection and `.guitartap` sections are sound but must be checked against current Swift.
  - **UI Flows (~95 lines) is too thin:** it has nothing on ring-out/decay, tap-tone ratio, Quick Start, the
    chart ⋯ menu, per-phase material multi-tap, or the silent warm-up.
  - Fold in the later specs: FILE-PATHS-AND-NAMES, MEASUREMENT-DIMENSIONS, NUMERIC-PRECISION, THEME-SPEC,
    WEB-PDF-MATERIAL-LAYOUT, CALIBRATION-DEVICE-STATE, STATUS-STATE-MACHINE.
  - Add the audio-contract detail the web port had to discover: the 200 ms pre-roll, fast-start vs fallback
    seeding, onset alignment (`max(10× noise RMS, 0.001)`, back 32 samples, window starts 100 ms before),
    the gated FFT (Hann, next power of two, cap 32768), the watchdog constants.
- **`ANDROID-UI-GUIDELINES.md`:** the Android counterpart of [WEB-UI-GUIDELINES](../process/WEB-UI-GUIDELINES.md).
  - Swift view → composable map; window-size-class rules.
  - How macOS menu shortcuts and the floating Results window translate.
  - Back-gesture behaviour for sheets.
  - Minimum 48 dp touch targets.
- **Generalise the parity tooling to N editions.** Replace the three hard-coded platform lists with one
  shared platform table:
  - `gen_parity_map.py`:
    - Add `.kt`/`.kts` to the scanned extensions, and `.gradle`/`.kotlin` to the skipped directories.
    - Rewrite "proven on all three" (the literal `len(pres) == 3`) as a rule over the platform table.
    - Update the 4-column table and the prose.
  - `doc_coverage.py`: add a KDoc analyzer and a fourth column.
  - `parity_lookup.py`: add the platform.
  - `guitartap_matrix.py`: add the platform token `android` and devices `phone`/`tablet`.
- **Shared fixtures.** WAV and `.guitartap` fixtures are hand-copied into three repos today, with no sync.
  Add a hub-owned fixture set plus a `sync-fixtures` script, modelled on the web's `sync-oracle.sh --check`.
  Android is its first consumer. Set `-text` in `.gitattributes`: the web's `text=auto` gives its JSON
  fixtures CRLF line endings, so they differ on disk from Swift/Python.
- **Process docs:**
  - [BUG-TRACKING](../process/BUG-TRACKING.md): ✅ done — the doc was updated during Phase 1, and the
    GitHub labels caught up on 2026-09-18 (`android` and `src:play` created, `all-three` renamed to
    `all-editions`, which kept it on the ten Issues already carrying it).
  - [DEV-DOC-STANDARD](../process/DEV-DOC-STANDARD.md): KDoc format, and Dokka as the doc-build
    correctness gate.
  - Hub [README](../README.md): the repo table.

**Gate:** the parity map regenerates with an (empty) Android column and no other diffs; the INVENTORY
refresh has been reviewed.

### Phase 2 — Headless core (`:core`, JVM only)

Port the Swift `Models/` domain and DSP, file-for-file:

- **DSP:** `dsp/fft`, `dsp/guitar-fft`, `dsp/gated-fft`, `dsp/gated-capture`, `dsp/spectrum-average`, plus
  peaks, classify, decay, pitch, material and calibration (UMIK-1 `.cal` parsing).
- **Domain:** `TapToneMeasurement`, `SpectrumSnapshot`, `ResonantPeak`, `GuitarMode`/`GuitarType`/
  `MeasurementType`, `MaterialProperties`, `FieldPrecision`, `ExportFilename`.
- **`.guitartap` codec** (kotlinx.serialization):
  - Canonical writer; tolerant reader that accepts legacy key names.
  - Base64 little-endian float32 spectra.
  - **float32 shortest-text scalars.** Kotlin's `Float.toString()` is not guaranteed to produce the same
    text as Swift's; test it explicitly.

**Tests:**
- Consume `parity-oracle.json` via a sync script, with a `--check` mode that fails on drift.
- Port the Swift/Python tests under their names (peak-fixture regression, measurement-codable,
  field-precision, material-selection, …).
- Decode the `.guitartap` fixtures saved by all three existing editions.

**Gate:** every `dsp/*`, `model/*` and `test/*` group that exists in Swift has a green Android counterpart;
the oracle `gatedFft` cases pass; the peak-fixture baseline matches.

### Phase 3 — Capture engine + analyzer state (`:audio`, `TapToneAnalyzer`)

Mirror `RealtimeFFTAnalyzer` + its extensions (`DeviceManagement`, `EngineControl`, `FFTProcessing`,
`Watchdog`), `DeadInput`, and `TapToneAnalyzer` + its 9 extensions.

- **Pipeline per chunk** (on the audio thread, in Swift's order):
  1. raw-sample handler (pre-roll / gated capture)
  2. advance `audioElapsed`
  3. RMS dB (floor −100)
  4. liveness stamp
  5. clipping check (peak ≥ 0.99 or RMS ≥ 0 dB, held 1.5 s)
  6. level crossing (2 consecutive chunks)
  7. RMS handler with the audio timestamp
  8. accumulate → 65536 FFT, no window, no overlap

  Published state updates are throttled to 0.5 s on the main thread.
- **Tap detection:**
  - Relative noise-floor EMA, 3 dB hysteresis, 0.5 s warm-up (silent — no status message) and 0.5 s
    cooldown.
  - Guitar captures fftSize samples; plate/brace capture 500 ms, with the FFT input at 400 ms.
  - Main-thread fallback seeding with Swift's timeouts.
- **Device management** (`AudioDeviceCallback`) — built here as development work: the source-selection
  ladder above, plus USB device handling, which is verifiable on the test tablet through a hub
  (ANDROID-FEASIBILITY §3). Android auto-routes capture to an attached USB mic, so the picker's job is to
  make the active device visible and overridable. When no USB input appears, say so plainly and mention
  that some devices only enumerate a measurement mic through a hub — a silent direct connection is exactly
  the failure a luthier would blame on Guitar Tap.
  - Enumerate input devices; auto-select a newly attached external mic; fall back when the active one is
    removed.
  - **Stable device key:** `AudioDeviceInfo.getId()` is *not* stable across replug. Derive the key from
    type + `productName` (+ `address`); the USB check in ANDROID-FEASIBILITY §3 settles the exact recipe.
  - One identity, one writer, one restore path ([CALIBRATION-DEVICE-STATE-SPEC](completed/CALIBRATION-DEVICE-STATE-SPEC.md)).
  - Per-device calibration map, with the load-without-resaving guard.
- **Watchdog / dead input:**
  - 1 Hz check, skipped during playback, recovery, or the first 4 s.
  - **Starved:** no buffers for > 2.5 s.
  - **Dead:** no chunk above 1e-5 RMS for 15 s.
  - **Recovery:** backoff 0.5/1/2/4 s, max 6 attempts, then keep watching.

  Android adds two direct signals Swift lacks:
  - `AudioRecordingConfiguration.isClientSilenced()` (API 29), which Android sets when another app or the
    privacy system silences capture.
  - `AudioRecord` read errors (`ERROR_DEAD_OBJECT`).

  Both feed the same state rather than a parallel mechanism. Note the Swift slug is `dead-input` (the hub
  doc says `dead-input-threshold`; reconcile that while here).
- **Lifecycle:** stop capture in `onStop`, restart in `onStart` (the iOS `scenePhase` equivalent). Handle
  the `RECORD_AUDIO` runtime permission, including "denied — don't ask again", with a Settings deep link.
- **File playback:**
  - Swift's sequence: detach → stop → bump generation → drain → clear → post-stop handler.
  - Read the WAV mono float at its own rate; feed 1024-sample chunks paced at real time; flush the partial
    FFT and gated capture; restart the mic.
  - Optional temporary calibration.
  - The playback path uses the `AudioSource` interface, so the oracle `filePlayback` cases (REG-G1, G2,
    B1, P1) run **on the JVM without a device**.

**Gate:** the file-playback oracle cases pass on the JVM; a 30-minute live soak on a device survives
backgrounding, a USB mic unplug/replug, and permission revocation, with no leaked `AudioRecord`.

### Phase 4 — UI (Compose)

About 41 Swift view files (~17.9k lines) map to composables of the same names:

| Area | Swift source |
|---|---|
| Shell | `TapToneAnalysisView` + Actions/Controls/Export/Layouts/SpectrumViews |
| Chart | `SpectrumView` + extensions, `PeakAnnotations`, `AxixTickGenerator`, `ThresholdSlider` |
| Results | `TapAnalysisResultsView`, `ComparisonResultsView`, `MultiTapComparisonResultsView`, `FFTAnalysisMetricsView`, `CombinedPeakModeRowView`, `EmptyStateView` |
| Material | `MaterialDimensionsEditor`, `PlateBodyDimensionsEditor` |
| Settings | `TapSettingsView` + extensions, `ValidatedNumberField` (restrict-on-entry precision) |
| Library | `MeasurementsListView`, `…RowView`, `…DetailView`, `…EditView` |
| Sheets | `SaveMeasurementSheet`, `PlayFileSheet`, `HelpView` (Quick Start) |

- **Chart interaction:** pinch zoom that depends on where you touch (plot, x-axis or y-axis), pan,
  draggable annotations with per-peak offsets, crosshair readout, the ⋯ menu (Reset Labels, …).
- **Library:** long-press menus, swipe to delete.
- **Theme:** Light / Dark / System per [THEME-SPEC](completed/THEME-SPEC.md).
- **Help:** opens the versioned manual URL, as the other editions do.
- **macOS-only features** (menu shortcuts, the floating Results window, the scroll-wheel chart): not ported.
  Hardware-keyboard shortcuts on tablets are a later nice-to-have.

**Gate:**
- A run-review **on the tablet**, side by side with Swift on iPad, of guitar, plate and brace measurements
  from start to finish. That is the primary target and the only Android hardware on hand.
- The review covers expanded and landscape layouts and dark mode on the device; the compact/phone layout is
  checked on the emulator, which is honest about what it can show — layout and flow, not feel or audio.
- A green suite is not a run-review.

### Phase 5 — Persistence & export

- **Library:** one JSON document per measurement in app-private storage, encoded with the `.guitartap`
  codec, so there is no second schema to migrate. Settings and the calibration map live in DataStore.
  App-private data is deleted on uninstall; say so in the manual.
- **Import/export** via the Storage Access Framework:
  - `ACTION_CREATE_DOCUMENT` / `ACTION_OPEN_DOCUMENT` for `.guitartap`, `.wav`, `.cal`.
  - Share sheet (`ACTION_SEND` through a `FileProvider`).
  - An intent filter so tapping a `.guitartap` file in Files, Drive or email opens the app. Its MIME type
    arrives as `application/json` or `application/octet-stream`, so accept both and validate content.
- **PDF:** single, comparison, and the two-page multi-tap report, drawn with `android.graphics.pdf.PdfDocument`
  using the Phase 4 chart renderer. Port the layout from `PDFReportGenerator.swift`.
- **PNG** spectrum export for measurement, multi-tap and comparison.
- **WAV session dump** (diagnostic) to a user-picked folder (`ACTION_OPEN_DOCUMENT_TREE`), mirroring
  `WavDumpFolder`.
- **Cross-edition round trip:** add an Android-saved `.guitartap` fixture to the Swift, Python and web
  suites (`test/peaks`, `test/measurement-codable`). This closes the gap where no test writes in one
  edition and reads in another.
- **Re-entrancy:** export/save re-entrancy guard, as on the other editions.

**Gate:** each export variant reviewed against Swift's output for the same measurement; files round-trip
through all four editions.

### Phase 6 — Parity completion & documentation

- `gen_parity_map.py --check` clean with four columns; `doc_coverage.py` shows no Android `0/N` groups;
  Dokka builds clean.
- [TEST-COVERAGE.md](../tooling/TEST-COVERAGE.md) updated.
- A soak/stress harness on Android, like the other three editions.
- **Corpus capture — the pre-ship comparison, at the end, as for every other edition.** The standard six
  (guitar 1-tap and 3-tap, plate, plate 3-tap, brace, brace 3-tap) recorded on Android, named to the corpus
  convention, added to `Tests/AllPlatforms/`, and compared with `guitartap_matrix.py`. The range column is
  the bar; the existing spread is ~1.6 Hz on brace fL and ~2.4 Hz on plate fLC. This is what
  `Tests/AllPlatforms/` was made for in the 1.0.2 cycle.
- **User manual** (shared source in `GuitarTap/Documentation/Manual`) gains Android wording:
  - installing
  - microphone permission
  - USB mics
  - where files go
  - the library being lost on uninstall
- In-app help (`view/help`) and release notes (`Documentation/ReleaseNotes.md` in the Android repo, with
  the same auto-stamping as Swift).

### Phase 7 — Distribution

The machine setup, keystore and build recipes are already solved in Palmas's
[`docs/android.md`](https://github.com/dwsdolce/palmas/blob/develop/docs/android.md): JDK 21, API 36,
keystore handling, AAB via `bundleRelease`. Reuse it rather than re-deriving it.

- **Versioning:** `versionName` = `X.Y.Z` (in lockstep with the other repos); `versionCode` = the git
  commit count, which is already every edition's build number. Fail the build on a shallow clone, as Palmas
  does.
- **Release guard:** a Gradle task run before compiling that matches the other repos' release-identity
  guards (blocks the build when HEAD is past the last tag and the version or notes are stale).
- **Play Console:**
  - Store listing and screenshots (tablet first, since that is the primary target; phone from the emulator).
  - Data safety form: records audio; no data is collected or shared; all processing on the device.
  - A privacy policy URL.
  - Tracks: internal → closed → production. If the developer account is subject to Play's closed-testing
    requirement for new personal accounts, the Palmas launch will already have shown what it demands;
    plan the tester pool before 1.0.
- **Also:** a signed APK attached to a GitHub Release, for sideloading, as Palmas does.
- **[RELEASE-CHECKLIST](../process/RELEASE-CHECKLIST.md)** gains:
  - a fifth surface and guard row
  - an Android section (version, notes, Play "What's new" ≤ 500 chars, upload, review status, tag)
  - a Play badge on the site
  - the Android roll step in §6

## Keeping Up With Swift During the Port

Swift keeps changing while Android is being built.

- Port against a **pinned Swift tag**, recorded at the top of each phase doc.
- At each phase gate, diff Swift from the pinned tag to the current tag and list the parity groups that
  changed. Port those changes before moving the pin.
- Until Android reaches Phase 6, a new cross-edition change lists Android as "pending port", not as a
  blocker.

## Key Technical Risks

1. **Built-in mic low-frequency roll-off on Android hardware.** The analysis must reach the plate fLC
   (~35 Hz; range starts at 30 Hz). Android MEMS capsules and HAL input filters vary by device, and a
   roll-off below ~60 Hz can hide the (quiet) fLC or bias its broad peak upward; unprocessed input doesn't
   fix a capsule's physics. This is a **device** property, not a project risk: every plate and brace capture
   in `Tests/AllPlatforms/` was made with a UMIK-1 (one Linux run excepted), so a weak built-in mic means
   "use a measurement mic for plates", as on every other platform. Mitigations: show the active
   source/device in Metrics, and save it with the measurement.
2. **OEMs that ignore or don't offer `UNPROCESSED`.** The fallback `VOICE_RECOGNITION` is usually
   AGC-free, but that is not guaranteed. Record the source used in every measurement so a suspect file can
   be explained later. Build a device matrix from Phase 0 onward.
3. **USB mic behaviour varies by device.** Whether the native rate is delivered or resampled, whether the
   device can be pinned with `setPreferredDevice`, and whether it enumerates at all when attached directly
   (on the test tablet a Snowball does and a UMIK-1 does not) must be checked per device **and mic**.
   Calibration also depends on a stable device key: `getId()` is per-attachment, so identity comes from type + `productName`
   (+ `address`, e.g. `card=1;device=0`).
4. **Fragile threading carried over from Swift.** Several level-crossing fields are shared across threads
   without locks in Swift, and switching the RMS path to a synchronous main-thread hop deadlocked there
   before. On Android, keep audio-thread state confined to the audio thread and hand values to the analyzer
   by message (a `Channel`/`StateFlow`), rather than copying the unsynchronised pattern.
5. **Open Swift issues Android inherits:** replay ≠ live by ~0.02 dB
   ([PLAYBACK-BIT-IDENTITY](PLAYBACK-BIT-IDENTITY.md)); the silent-stream watchdog has never been confirmed
   in real use ([AUDIO-WATCHDOG-SILENT-STREAM](completed/AUDIO-WATCHDOG-SILENT-STREAM.md)). Android's 1024
   re-chunking removes the buffer-grid cause, so it may be the first edition able to isolate the replay
   difference.
6. **Float text formatting in `.guitartap`.** Kotlin's shortest-representation float printing may differ
   from Swift's in rare cases, breaking byte-level file comparisons. It is caught by a Phase 2 test,
   not discovered in the field.
7. **Maintenance load.** A fourth edition makes every future feature, fix and release step land four
   times, plus a store review. This is the real ongoing cost and belongs in the go/no-go decision, not just
   the build cost.

## Size

A comparison, not a schedule:

- Swift app: ~34k lines, plus ~10k of tests.
- Python: ~38k lines.
- Web: ~16k lines — the closest estimate for a lean Android edition.
- Swift views alone: ~17.9k lines.

The web's pure DSP core (`src/dsp`) is ~1.8k lines today.

## Open Questions

- **`minSdk`:** 28 (for `MicrophoneInfo`) or 29 (for `isClientSilenced` without a version check)? Check
  Play's device-share data for the target audience.
- **File naming for Swift extensions:** Kotlin has no `Type+Extension.swift` convention. Is the naming
  `TapToneAnalyzerSpectrumCapture.kt` (holding extension functions) enough for `@parity` pairing, or
  should the map record the Swift → Kotlin file pairing explicitly?
- **Parity rule:** what counts as "proven on all editions" while Android is partial — every edition in
  the platform table, or canonical + N? This is decided in Phase 1 when the tooling is generalised.
- **Library storage location:** keep app-private (lost on uninstall), or offer a user-chosen folder via
  `ACTION_OPEN_DOCUMENT_TREE` so a library survives reinstall?
- **Tablet medium width** (foldables, split screen): compact layout with sheets, or a narrower expanded
  layout?
- **Distribution:** Google Play only, or also F-Droid? F-Droid needs a reproducible build with no
  proprietary dependencies. The planned stack has none, but it would constrain later choices.
