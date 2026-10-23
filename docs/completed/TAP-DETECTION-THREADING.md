# Tap detection threading — one per-chunk sequence, as on the web

**Issue:** [#38](https://github.com/dwsdolce/guitar-tap-project/issues/38)

Status: ✅ **CLOSED 2026-10-22** — steps 1–5 done: Swift `58093e8`, `68ad541`, `1009a04`; Python `40f9265`, `06a13db`, `a4442f9`; web `a6c0ae8`, `ea42687`, `cf74495`. Tap detection and capture are one per-chunk sequence on the main thread in every edition, the FFT included; the fast-start is gone. Three findings fixed on the way: New Tap left disabled after a microphone change, Python's grid over the labels, Swift's Settings slow to open (the calibration's corrections now one pass in all three). Full suites passed in all three; run-reviews passed on macOS, the iPhone and iPad, Windows and Linux (owner, 2026-10-22).

Swift and Python run tap detection on a different thread from the audio it judges. The web takes every chunk in
order on one thread. The difference is the source of a recurring class of bugs in Swift and Python; this issue
brings them to the web's shape.

## How each edition is threaded

| | Where the audio arrives | Where the level, FFT and capture-filling run | Where the tap detector runs |
|---|---|---|---|
| **Web** | an AudioWorklet on the browser's audio thread, which only collects 1,024-sample chunks, takes each chunk's RMS and posts it (`public/spectrum-processor.js`) | the main thread (`port.onmessage` → `onChunk`, `src/audio/realtimeFFTAnalyzer.ts`) | the main thread, in the same step |
| **Swift** | AVAudioEngine's tap callback | a serial audio-processing queue | the main thread, dispatched per chunk (`TapToneAnalyzer.swift`, the RMS callback → `onRmsLevelChanged`) |
| **Python** | PortAudio's callback thread | `_FftProcessingThread` (a `QThread`) | the main thread, through a queued Qt signal |

Swift and Python moved the heavy per-chunk work off the main thread so it cannot stall the UI, and kept the
detector on the main thread because what it drives is main-thread state. That puts detection one hop behind the
audio. Three mechanisms exist only to cover that gap:

- **the fast-start** — the audio thread opens a capture the moment the level crosses the threshold
  (Swift `levelCrossingHandler`, Python `_level_crossing_handler`), so the audio from the tap's onset is not lost
  while the main thread catches up;
- **the deferred pre-roll** for file playback, where the audio runs ahead of the main thread;
- **the capture-ID guards** (`gatedCaptureID`, `lastLevelCrossingCaptureID`), for a capture that starts or ends
  on the audio thread before the main thread hears of it.

On the web nothing is behind anything else: the detector sees each chunk before the capture takes it, so a capture
can only start from a confirmed tap, and none of the three exists.

## The defect that prompted this

Reproduced in Swift and seen once in Python; not reproducible on the web (2026-10-21). Brace, Taps 1, New Tap, then
a sound or a clipping tap straight after: the measurement completes with detection still armed — the status dot
green, the message in `text.primary`, Pause enabled — on a spectrum of room noise. The Swift debug log of a bad run
against a good one:

```
t=31.345  🎯 Gated FFT capture (audio-queue fast-start, running) …    ← a tap was detected, then the capture
t=31.661  📊 Gated FFT complete … 807.5 Hz @ -25.0 dB                   ← a real brace tap

t=47.265  🎬 Starting tap sequence … brace mode: true                   ← New Tap
t=48.048  📊 Gated FFT complete … 128.2 Hz @ -87.7 dB                   ← room noise, 0.78 s later
          (no "Gated FFT capture …" line: handleTapDetection never ran)
```

**Cause — two triggers, only one gated:**

- **The tap detector** (`detectTap`, main thread) is held off for the 0.5 s warm-up and, for plate and brace, uses
  a threshold relative to the noise floor (at least 10 dB above it). A confirmed tap calls `handleTapDetection`,
  which sets detection idle and starts the capture.
- **The fast-start** is armed the moment detection becomes listening (Swift: `TapToneAnalyzer.detectionState`'s
  `didSet`; Python: `tap_tone_analyzer.py`, entering listening), so the warm-up does not stop it; it uses the
  absolute Threshold; its only guard is "is a phase capturing".

A crossing the detector does not count as a tap — in the warm-up, or below its relative threshold — therefore
opens a capture on its own. The capture completes, the measurement completes on noise, and detection, never set
idle, stays armed: completing a measurement does not disarm detection itself; it relies on the tap detector having
done so. The defect stands in Swift and Python until this issue is done.

## Proposal

Each edition's audio thread only hands chunks over; **one thread takes each chunk in order** — level, FFT,
detection, pre-roll and capture — as the web does. For Swift and Python that thread is the main thread, as on the
web, since detection drives main-thread state (Swift's published properties, Python's Qt signals). The fast-start,
the deferred pre-roll and the capture-ID guards go, and with them every case where the detector and the capture
disagree about which audio is which: order replaces timing.

**Affordable.** The web's FFT — the costly step, 65,536 samples, once per 1.37 s with no overlap — averages 10 ms on
a Mac and 15 ms on a slow iPhone: about 1 % of the main thread, and a single pause shorter than one 60 Hz frame.

## Risks and checks

- **A refactor of the most sensitive code** in two editions: capture alignment and file playback.
- **Python's main thread is busier than the web's** — it also paints pyqtgraph, at tens of milliseconds a frame.
  Chunks would queue and still be taken in order, so results stay right, but the live display could lag more under
  load: measure it.
- **Results may shift slightly**: captures would align from the pre-roll as the web's do. The file-playback
  regression and export baselines are re-checked; any intended shift is listed and re-minted.
- **Run-review on every platform**, iPhone and iPad included.

## Decisions

- **Separate from #29** (owner, 2026-10-21). #29 changes what triggers a tap; this changes where and in what order
  detection and capture run. This issue does not depend on #29.
- **After #32** (owner, 2026-10-21).
- **No interim fix** (owner, 2026-10-21). Counting only captures the detector confirmed would stop the defect, but
  it would be a Swift-and-Python-only change this issue deletes; the defect stands until this issue lands.
- **One per-chunk sequence on the main thread in every edition, the FFT included — exactly as on the web** (owner,
  2026-10-21), from the measurements under "Measuring the slack": the slowest Apple device measured, the iPad mini 5, has the room. Python's
  own measurements confirm it for Python once #35 is done — today its main thread rebuilds the peak list and labels
  on every FFT frame (about 115 ms), which hides everything else.
- **#35 first** (owner, 2026-10-21).

## The target: one per-chunk sequence

The web's `processAudioFrame(samples, levelDB, audioTime)` (`src/state/tapToneAnalyzer.ts`) is the model. On one
thread, for each chunk, in this order:

1. **Fill**: the pre-roll ring, the session recording, and the open capture window. A window that fills is finished
   there and then — a direct call, not a queued one.
2. **The audio clock**: `lastAudioTime`, then any timed action this chunk makes due (`runDueAudioActions`).
3. **Detect** — if no action ran and detection is listening: `detectTap`, and on a confirmed tap
   `handleTapDetection`, which sets detection idle and opens the capture from the pre-roll. The pre-roll already holds
   this chunk, so the capture lines up with the tap by construction.

Swift and Python keep their audio thread for what must not wait — taking delivery, cutting 1,024-sample chunks, the
level, clipping, the dead-input stamp — and hand each chunk to the main thread in **one hop** carrying
`(samples, levelDB, audioTime)`. The FFT runs in the sequence on the main thread, as on the web (decided below). The main thread runs the sequence above. Order replaces
timing: the main queue (Swift) and the queued signal (Python) deliver chunks in order, so nothing can start a capture
the detector did not confirm, and a capture can never fall out of step with detection.

## What goes

In Swift and Python alike:

- **The fast-start**: `levelCrossingHandler` / `_level_crossing_handler`, `levelCrossingArmed`,
  `levelCrossingThreshold`, the confirmation counter, `previousLevelDB`, and their arming in the `detectionState`
  setter.
- **The deferred pre-roll** for file playback: `pendingLevelCrossingPreRoll`, its accumulation, Python's `"_deferred_"`
  phase sentinel, and the file-playback re-arm on a capture's completion.
- **The "fast start already handled this tap" branches** in `startGatedCapture` / `startGuitarGatedCapture`, and
  `lastLevelCrossingCaptureID` with its six resets.
- **`mpmLock` / `_gated_lock`**: every field it guards — the pre-roll, the capture window, the capture id, the session
  recording — becomes main-thread state. The capture id stays, main-only, for its other job: guarding against a stale
  safety timeout.
- **The cross-thread writes** the maps found unlocked: `gatedCaptureActive`, `gatedCapturePhase`,
  `gatedCaptureSamples`, `mpmSampleRate`, `materialTapPhase` read on the audio thread, `isPlayingFile` read there.

The end of a played file needs no change of mechanism: Swift's `main.sync` and Python's blocking queued call to the
flush are queued **after** the file's last chunks, so they still run after every chunk has been taken.

## Rules for this work (owner, 2026-10-21)

- **No commit until the change is fully verified** against the existing tests. The slack probe below is the exception:
  it has to be committed to run on Windows and Linux.
- **The existing tests are not changed**, except where a test cannot run otherwise; each such change is listed here
  with its reason.
- **No decision on where work runs without measuring it** — the slack probe.

## Measuring the slack

A diagnostic in every edition (Swift `edac1c8`, Python `5ef7e8c`, web `77c003a`), off by default, prints one line every 5 s in the same form:

```
⏱ slack 5.0s: chunk 21.33 ms | lag p50 … p95 … p99 … max … | latency p50 … p95 … max … | main/chunk avg … max … n … | accumulate avg … max … n … | fft avg … max … n … | frame avg … max … n … | main busy …%
```

- **lag** — a 5 ms main-thread timer's lateness: the time the main thread was busy with something else.
- **latency** — from the audio thread handing a chunk over to the main thread taking it (the web: on the audio clock,
  from the worklet's post).
- **main/chunk** — the main thread's per-chunk work; **accumulate** — the pre-roll, session recording and capture
  filling, within main/chunk; **fft** — the FFT; **frame** — the main thread's work on each FFT frame. **main busy**
  is main/chunk, fft and frame — everything the probe times on the main thread (Swift `9bd34be`, Python `ff09985`,
  web `c5b4105`). The readings below were taken when
  main busy left out the FFT; their FFT column gives its time.

**Switching it on:**

| Edition | How |
|---|---|
| Swift | the environment variable `GT_SLACK_PROBE=1` (Xcode: the scheme's Run → Arguments → Environment Variables); the line goes to Xcode's console |
| Python | `GT_SLACK_PROBE=1 python -m guitar_tap`; the line goes to the terminal |
| Web | `?slackprobe` on the page's URL; the line goes to the browser console (on an iPhone, Safari's Web Inspector from the Mac) |

**The deciding test** (the rows "FFT's cost on main" below): before the FFT moved to the main thread, Swift and
Python had a switch that made the main thread spin, after each FFT frame, for the FFT's measured duration — the cost
it would carry if the FFT ran there. With the FFT on the main thread, the switch was removed (Swift `9bd34be`, Python `ff09985`).

**Scenarios**, each for about 30 s, on every edition and platform (Swift: Mac, iPhone, iPad; Python: Mac, Windows,
Linux; the web: desktop and iPhone): idle listening; a guitar tap through to the results; a plate through all three
phases; zoom and pan while listening; Saved Measurements open; file playback. Swift on a Release build as well as
Debug, since the Debug build's timings are slower.

**First readings** (Mac, idle listening, 2026-10-21): Swift (Debug) — lag p99 11 ms, latency p50 0.02 ms, FFT 17.5 ms,
main busy ~0 %. Python — FFT 9–17 ms, but **the main thread's work on each FFT frame 128–145 ms**, lag max 230 ms,
latency p95 120–130 ms, main busy 6–11 %: Python's main thread already falls a few chunks behind at every frame.

**Mac runs, Swift and the web (2026-10-21).** Four scenarios of 30 s each — idle listening, a guitar file played through
to its results, New Tap then zoom and pan over the chart, Saved Measurements open — driven by a temporary UI test
(Swift, Debug build) and a temporary Playwright script (the web, a visible Chromium window); the live microphone in
both. Per phase: the median of the 5 s windows' 99th-percentile lag and its worst case; the same for the latency's
95th percentile; the main thread's busy share from the probed work; the FFT's time.

| Edition | Phase | Lag p99 (median / worst), ms | Latency p95 (median / worst), ms | Main busy | FFT, ms |
|---|---|---|---|---|---|
| Swift | idle | 7 / 540 | 0.1 / 150 | 0.2 % | 17 |
| Swift | playback | 10 / 985 | 7 / 975 | 0.1 % | 15 |
| Swift | zoom and pan | **145 / 267** | **172 / 252** | 0.1 % | 12 |
| Swift | Saved Measurements | 7 / 355 | 13 / 350 | 0.1 % | 18 |
| Swift, FFT's cost on main | idle | 8 / 480 | 9 / 95 | 2.7 % | 18 |
| Swift, FFT's cost on main | playback | 11 / 906 | 19 / 841 | 2.4 % | 15 |
| Swift, FFT's cost on main | zoom and pan | 131 / 334 | 157 / 252 | 1.6 % | 10 |
| Swift, FFT's cost on main | Saved Measurements | 8 / 494 | 85 / 466 | 2.5 % | 16 |
| Web | idle | 4 / 289 | 2.7 / 269 | 0.3 % | 7 |
| Web | playback | 3.5 / 50 | 2.7 / 45 | 0.3 % | 6.5 |
| Web | zoom and pan | 3.6 / 18 | 2.7 / 8 | 0.3 % | 5 |
| Web | Saved Measurements | 4 / 10.5 | 2.7 / 2.7 | 0.3 % | 6 |

What they say:

- **The per-chunk work is negligible everywhere it was measured**: Swift's main-thread chunk work and capture filling
  under 0.2 %, the web's (all of it on its main thread) 0.3 %.
- **The FFT on Swift's main thread costs about 2.5 % and leaves the typical lag unchanged** (p99 7–11 ms either way).
- **Swift's main thread stalls for other reasons**: 130–330 ms through zoom and pan, and single stalls of 0.4–1 s as a
  phase begins (a sheet or the open panel appearing). They come from drawing, not from the probed work, and they are
  there whether or not anything moves. Under the one-sequence design a stall delays chunks — they wait in order and
  are taken after it — but cannot reorder them, so a capture still lines up with its tap. Part of the zoom-and-pan
  cost may be the UI test's own (each scroll it sends makes the app answer accessibility queries): to be repeated by
  hand, and on a Release build.
- **The web has slack to spare**: lag p99 about 4 ms, latency one render quantum (2.7 ms), its FFT 5–7 ms.

**By hand, Release builds (2026-10-21).** Swift on the Mac: zoom and pan holds the main thread 100–200 ms at a time
(lag p99 167–204 ms, latency p95 111–162 ms) with the probed work at 0.0 % — the chart's drawing, for #31, not this
issue; the FFT about 1 ms (the Debug build's 15–17 ms is the Debug build). Zoom and pan is not done while taps are
captured (owner), so it does not decide this issue; what does is listening, a tap sequence, a plate's phases and a
completion. On those:

| Device | Per-chunk main work avg / worst | Capture filling worst | FFT | Main busy | Lag p99 / worst | Latency p95 / worst |
|---|---|---|---|---|---|---|
| iPad Pro 13" (M5) | 0.01–0.05 / 2.6–5.5 ms | 2 ms | 0.5–1 ms | 0.0–0.2 % | 10–18 / 95–152 ms | 3–27 / 417 ms |
| iPad mini 5 (A12) | 0.02–0.21 / 6–11 ms | 8 ms | 1.4–4.3 ms | 0.1–1.0 % | 22–61 / 105–455 ms | 59–234 / 440 ms |

The worst per-chunk work, on the slowest device, fits inside the 21.3 ms between chunks; the FFT on the main thread would
add about 0.3 % of it. The long holds — up to 440 ms on the A12 — are drawing, and they hold detection today as well;
in one sequence they delay a capture's chunks but cannot reorder them, so a slow device makes the screen later, not
the measurement wrong.

## Steps

Each step is a commit in each edition it touches, then the hub with the hashes.

1. **The defect as a shared case, first.** Done (test code only): Swift `58093e8`, Python `40f9265`, web `a6c0ae8`. In `tap-decisions.json`
   (`test/tap-decisions`), with the detector's other decisions (owner, 2026-10-22), three cases fed through the
   microphone's path — `liveAudio`, which in Swift and Python now sends each chunk through the engine's per-chunk
   processing (`processRawSamples` / `process_raw_samples`, the fast-start included), the engine queueing each
   chunk's main-thread part as the app's does, the main thread taking the queue after the step; the web's was the
   real path already (`processAudioFrame`):
   - **T15** (brace) — a sound in the warm-up: no capture, the measurement not complete, detection listening;
   - **T16** (plate) — with the floor at −45 dB, a sound at −38 (above the −40 Threshold, below the detector's
     −35): no capture, still Capturing Longitudinal, detection listening;
   - **T17** (brace) — a real tap after the warm-up: the measurement complete, detection idle.

   The web passes all three. Swift and Python fail all three, marked as known (Swift `withKnownIssue`, Python strict
   `xfail`) until steps 2 and 3: T15 completes on the room's noise, T16 moves to Reviewing Longitudinal, and T17 —
   the main thread a capture window behind the audio, as a 400 ms hold on a slow device or in Python makes it —
   completes with detection still armed: the fast-start's capture finishes before the detector sees the tap
   (owner: keep T17 as a known failure, 2026-10-22). A new shared check, `complete`.

   Test changes: the shared steps' `liveAudio` (Swift `AnalyzerSteps.swift`, Python `analyzer_steps.py`) as above;
   Swift `TapDetectionTests.decision` async, to let the main queue run after a `liveAudio` step (as
   `FrozenPeakRecalculationTests` already did); `complete` and the known failures in the three `tap-decisions` tests.
   `frozen-peak-recalc`, the one existing case using `liveAudio`, passes in all three. Full suites at those commits:
   Swift (macOS) 295 tests and 1 XCTest, 4 known issues (T15–T17); Python 1561 passed, 1 skipped, 3 xfailed; the web
   1423 passed, 1 skipped, lint and typecheck clean.
2. **Swift**: the one hop and `processAudioFrame`; delete what goes. Done: Swift `68ad541`, with the findings below. The audio queue keeps each chunk's level, clipping, dead-input
   stamp and audio time, and hands the chunk to the main thread once (`RealtimeFFTAnalyzer.handOver`, carrying
   `(samples, levelDB, audioTime)`); there, in order, the FFT's input and the FFT (`takeChunk`), then
   `TapToneAnalyzer.processAudioFrame`: the pre-roll, the session recording and the capture filling — a filled
   capture finished there and then — then the clock, due actions and detection (`onChunkLevel`). A chunk from a
   source since replaced (mic chunks queued when a file starts, a stopped file's) is dropped by its playback
   generation; on the main thread itself a chunk is taken at once, so a pump or a test run there keeps its order.
   The end-of-file partial FFT frame is flushed on the main thread, ahead of the capture flush. Gone: the
   fast-start (`levelCrossingHandler`, `levelCrossingArmed`, `levelCrossingThreshold`, the confirmation counter,
   `previousLevelDB`, their arming in `detectionState` and syncing in `tapDetectionThreshold`), the deferred
   pre-roll (`pendingLevelCrossingPreRoll`, the file re-arm), `lastLevelCrossingCaptureID`, `mpmLock`,
   `bufferAccessQueue`, `rawSampleHandler`, `rmsLevelHandler`. `startGatedCapture` / `startGuitarGatedCapture` /
   `accumulateGatedSamples` are the web's: a capture already filling absorbs the tap; the window seeds from the
   pre-roll. `levelCrossingConfirmationChunks` stays, the detector's confirmation.

   Test changes: `AudioChunkingTests` listens on `audioFrameHandler` (the hooks it used are gone; its assertions
   unchanged); `TapDetectionTests` back to its plain form, T15–T17 passing. Results: the unit suite (macOS) 295
   tests in 90 suites, no known issues — file playback, capture alignment, self-regression included; the export UI
   tests 20 exports checked, 0 failing.
3. **Python**: the same, through one queued signal. Done: Python `06a13db`, with the findings below; the web's
   share of the findings `ea42687`. The processing thread and the
   file-playback thread keep each chunk's level, clipping, peak hold and audio time, and hand the chunk to the main
   thread once (`RealtimeFFTAnalyzer.hand_over`, the processing thread object's queued `chunkHandedOver`, carrying
   `(samples, level_db, audio_time, playback generation)`); there, in order, the FFT's input and the FFT
   (`take_chunk`), then `TapToneAnalyzer.process_audio_frame` — the pre-roll, the session recording and the capture
   filling, a filled capture finished there and then — then the clock, due actions and detection
   (`_on_chunk_level`). Stale chunks are dropped by their playback generation; on the main thread a chunk is taken
   at once. The end-of-file partial FFT frame is flushed in the main-thread end step, ahead of the capture flush.
   Gone: the fast-start (`_level_crossing_handler` and its state on the mic, the arming in `detection_state`, the
   sync in `tap_detection_threshold`), the deferred pre-roll and the `"_deferred_"` phase sentinel,
   `_last_level_crossing_capture_id`, `_gated_lock`, `raw_sample_handler`, `rms_level_handler`, `_rmsLevelOnMain`
   and `gatedCaptureComplete` (a capture is finished where it fills, and the safety timeouts finish theirs
   directly, as Swift's). The post-engine-stop step clears the pre-roll only, as Swift's.

   Test changes: `test_tap_detection.py` without the known-failure marks (T15–T17 pass) and its delivery tests'
   docstrings naming the new hand-over; `analyzer_steps.py`'s `liveAudio` note. Results: the full suite 1564
   passed, 1 skipped (the capture probe, off) — file playback, self-regression and the peak fixtures included.

   **Finding, found testing step 2 (owner, 2026-10-22): New Tap left disabled after a microphone change.** With all
   three apps sharing the input, a microphone change in Swift ended with the measurement complete, the status dot
   green and New Tap disabled for good, though audio kept coming. The device change starts a settle that disables
   New Tap and ends after 3 s of audio and the next frame; at its due time it checked that the engine was running
   and, if not, gave up — for good. A start that fails after a device switch (more likely with the input shared:
   the console's `-10877` and `HALC … error 35`) is retried with a stop and a start, and the settle falling due
   between them was never scheduled again. The same in all three editions; not caused by this issue's change.
   Fixed in all three (owner, 2026-10-22): a settle that falls due while the engine is stopped waits another 3 s of
   audio, from the restarted engine, and checks again — on the audio clock, so with no audio it waits rather than
   spins (Swift `scheduleRouteChangeSettleEnd`, Python's `_settled`, the web's `settled`). Shared case N22 in
   `notification.json` (a new shared step, `engineRunning`, stops and starts the engine as a retry does): passes in
   all three, and fails in all three with the old guard.

   **Finding, found in the macOS run-review (owner, 2026-10-22): grid lines drawn over the labels in Python.** The
   spectrum's grid showed through the peak annotations' labels and leaders. pyqtgraph draws the grid with the axes
   (z 0.5), above the plot's view box (z −100) and so above everything plotted in it. Not caused by this issue's
   change. Fixed (owner, 2026-10-22): the axes are placed beneath the view box, on the live spectrum
   (`views/fft_canvas.py`) and the exported chart (`views/exportable_spectrum_chart.py`), so the grid is beneath the
   curves and the annotations, as in Swift; verified on screen (owner, 2026-10-22). The export images change with
   it: checked in step 4.

   **Finding, found in the macOS run-review (owner, 2026-10-22): Settings slow to open in Swift, and the calibration
   not shown as selected.** In a Debug build, Settings took about 2 s to open, and the calibration picker did not
   show the calibration just chosen. Opening Settings applied the selected calibration again, and every applying
   recomputed the corrections for all 32,768 bins, each by a linear search of the calibration's points: about 1 s
   unoptimised (6 ms optimised). Not caused by this issue's change. Fixed (owner, 2026-10-22): the picker and the
   engine apply a calibration only when it differs from the one active (`TapSettingsView+Sections.swift`,
   `RealtimeFFTAnalyzer.activeCalibration`); the corrections are one pass over the ascending bins and the points
   together (`MicrophoneCalibration.corrections(for:)`, 3.8 ms unoptimised, 0.07 ms optimised), any other order
   falling back to `correction(at:)` per frequency. The three editions computed the corrections three ways — Swift
   the linear search, the web a binary search per bin, Python `np.interp`; now one (owner, 2026-10-22): the web's
   `interpolateToBins` is the same one pass, with `correctionAt` as its fallback; Python keeps `np.interp`, which is
   that pass inside numpy (as a Python loop it is 27 times slower), and gains `correction_at`. A new test in all three
   (Swift `correctionsForAllBins_areEachBinsCorrection`, Python `test_corrections_for_all_bins_are_each_bins_correction`,
   the web's in `calibration.test.ts`): the corrections for all bins at once are each bin's own, exactly, at 48 kHz and
   44.1 kHz and for unsorted frequencies; the shared CAL1–CAL3 unchanged and passing. Settings opens at once in a
   Debug build, the calibration shown as selected: verified (owner, 2026-10-22).

4. **Verification**. Done (2026-10-22):
   - the full suites in all three editions, at Swift `68ad541`, Python `06a13db`, the web `ea42687`: Swift (macOS)
     296 tests in 90 suites, no known issues; Python 1566 passed, 1 skipped (the capture probe, off); the web 1425
     passed, 1 skipped, lint and typecheck clean;
   - the export and self-regression baselines: Swift's export UI tests (macOS) 5 cases, 0 failing; the
     self-regression cases pass in all three. Python's exported images change with the grid fix, and only there:
     the three shared fixtures exported before and after differ in about 0.2 % of their pixels, all inside the
     plot — the grid beneath the curve and the mode bands, the top border in the axis colour as in Swift's export.
     Their size and pixels per inch, which the tests check, are unchanged; nothing re-minted;
   - **Python's display under load measured**: the live spectrum's frame interval and the main thread's per-chunk
     time while a tap sequence runs, before and after. Done (Mac, 2026-10-22, the slack probe; after: the real window
     offscreen, files played as Play File plays them; the start-up window left out):

     | Python, Mac | Lag p99 | Lag max | Latency p95 | Main busy | FFT |
     |---|---|---|---|---|---|
     | before — #35 item 3, tapping, the FFT's cost simulated on main | 13–28 ms | 65–408 ms | 2–142 ms | 1–8 % | ~10 ms |
     | after — guitar, `5 tap test.wav` | 5–9 ms | 14–30 ms | 0.3–0.6 ms | 1.1–1.3 % | 9–11 ms, on main |
     | after — plate, `plate-umik-1-swift-mac-1778816330.wav` | 6–13 ms | 21–212 ms | 0.5–1.1 ms | 1.4–2.4 % | 9–12 ms, on main |

     The live spectrum's frame interval is unchanged, 1.6 s; the chunk on which a capture finishes holds the main
     thread 23–35 ms at most. The before is a live microphone, the after file playback: the same conclusion, not
     the same conditions;
   - a run-review by platform, the physical iPhone and iPad included (a capture on a real tap; the warm-up and
     clipping cases that produced this issue; file playback of each type): passed on every platform (Run-review,
     below).
5. **Close-out**. Done: Swift `1009a04`, Python `a4442f9`, web `cf74495`.
   - Comments and docstrings describe the one sequence: Python's notes on Swift's names no longer name
     `rawSampleHandler` or `bufferAccessQueue`; Swift's `performFFT` runs on the main thread; the web's capture
     filling no longer mentions Swift's fast-start. Swift has no DocC catalogue in its source tree; its doc comments
     are the DocC.
   - **Finding (owner, 2026-10-22): FFT frame counters.** Swift counted FFT frames and the samples they consumed,
     and its capture-complete debug line reported that count as the file position; Python had the same two fields
     and never advanced them, reporting a per-chunk counter instead; the web has neither. Removed from Swift and
     Python; the debug line reports the analyzer's audio clock, which every edition carries.
   - The shared case files `button-style`, `chart-help`, `chart-menu` and the oracle carry no issue numbers or
     project history (owner, 2026-10-22: test code and data refer to no project document; `tooling/` and
     `process/` are permanent and may be cited).
   - Hub: `INVENTORY.md`'s tap detection is the one sequence, and it cites no memory files; `TEST-PLAN.md` and
     `ANDROID-PLAN.md` without the removed queue and fast-start.
   - Targeted tests in all three; the parity check and the fixture check clean.

## Run-review

Steps 2 and 3 and the findings' fixes, on a fresh build of each edition: Swift on macOS, the iPhone and the iPad;
Python on macOS, Windows and Linux; the web (its settle and calibration fixes) on macOS. Threshold at its default
(−40 dB) unless a step says otherwise.

Steps 1 and 2 are on macOS only (owner, 2026-10-22): elsewhere a sound within half a second of New Tap is hard to
make by hand — on the iPad, lifting the finger from the button takes most of it (the log and session recordings of
four tries: one tap within the warm-up, ignored; three at 0.62–0.78 s, past it, captured). The shared cases T15–T17
check the warm-up on every platform, through each edition's microphone path, in the suites.

| Platform | Result |
|---|---|
| macOS — Swift, Python, the web | passed, steps 1–8 (owner, 2026-10-22) |
| iPhone, iPad — Swift | passed, steps 3–8 (owner, 2026-10-22) |
| Windows, Linux — Python | passed, steps 3–8 (owner, 2026-10-22) |

1. macOS — Swift, Python, the web: Brace, Taps 1, New Tap, and within half a second make a sharp sound (a tap on
   the bench, a clap). → Nothing is captured; the status dot stays green, the message reads as listening, Pause
   stays enabled. A real tap on the brace after that is captured and completes the measurement.
2. macOS — Swift, Python, the web: the same, with a clipping tap (hard enough for the clipping warning) straight
   after New Tap. → As step 1: nothing captured until a real tap after the warm-up.
3. Brace, Taps 1, New Tap, wait a second, then tap the brace once. → One capture; the measurement completes; the
   dot is no longer green, Pause is disabled.
4. Plate, measuring fLC on, New Tap, then the three phases with a real tap each, accepting each. → fL, fC and fLC
   captured from their own taps; results as before this change.
5. Guitar, Taps 3, New Tap, three taps on the top. → Three captures, the averaged result; afterwards the dot is no
   longer green and Pause is disabled.
6. Guitar, Taps 1: tap hard enough to clip. → The clipping warning shows; the tap is captured and the measurement
   completes.
7. Play File: `5 tap test.wav` as a guitar, then a plate recording, then a brace recording. → Each plays through to
   its results, as before this change; the plate's three phases advance by themselves.
8. While a guitar sequence listens, open Settings and close it, then tap. → The tap is captured as usual.
