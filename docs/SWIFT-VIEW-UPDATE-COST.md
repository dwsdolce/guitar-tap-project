# Sluggish UI: the input level rebuilt the whole window ten times a second

**Issue:** [#28](https://github.com/dwsdolce/guitar-tap-project/issues/28)

**Status (2026-10-11): done** — items 1–6 in all three editions (Swift `335ac2c`, Python `9dc4613`, web
`eeef676`); the owner checked them on the iPad and the Mac (the meter, clipping, Settings, the calibration
details) — "the Swift apps definitely feel less sluggish".

## What the owner saw

- On the iPad, every pull-down in Settings flickered under the pointer while the app was listening.
- The app feels sluggish at times.

## What was measured

Instruments (SwiftUI template), the Mac app in a Release build, 20 s listening for a tap, nothing touched:

| | |
|---|---|
| Main thread busy | **18.8 s of ~21 s (≈ 90 %)** |
| …of which inside SwiftUI's view-graph update | **≈ 79 %** of the main thread |
| `TapToneAnalysisView.body` evaluations | **226 in 18.5 s (≈ 12 / s)**, the chart's content rebuilt each time |
| Cost per update | ≈ 65 ms of main-thread work |
| The app's own code | small — the largest app function ≈ 1.6 % |

On the iPad, a temporary `Self._printChanges()` in Settings printed `@self, _peakMinThreshold, _dismiss,
_openURL changed` continuously while the sheet was open: the sheet is recreated on every update of the main
view too.

## Facts (checked in the code)

1. **Swift's audio arrives in 4800-frame buffers** (0.1 s at 48 kHz), not the 1024 it requests — #3,
   `docs/AUDIO-BUFFER-SIZE.md`. About 10 buffers a second.
2. **Each buffer publishes the input level** on the engine (`RealtimeFFTAnalyzer`): `inputLevelDB` every
   time, `recentPeakLevelDB` when it rises or expires, `isClipping` on a change
   (`RealtimeFFTAnalyzer+FFTProcessing.swift`, the `DispatchQueue.main.async` after `rmsLevelHandler`).
3. **The spectrum is not the fast one.** The FFT is 65536 samples (≈ 1.4 s of audio, no overlap) and is
   published at most every 0.5 s (`minPublishInterval`): `magnitudes`, `peakFrequency`, `peakMagnitude`,
   `processingTimeMs`, `avgProcessingTimeMs`, `displayLevelDB` — under one update a second.
4. **The `TapToneAnalyzer` publishes per FFT frame, not per buffer**: `averageMagnitude` every frame, and
   while a guitar sequence runs, the live peaks (`allPeaks`, `selectedPeakIDs`, `identifiedModes`). The
   per-buffer tap-detection path writes only plain properties (`lastAudioTime`, `lastChunkLevelDB`,
   `lastChunkWallTime`).
5. **`averageMagnitude` is read by nothing** — published every frame for no reader. Python has
   `average_magnitude`, declared and never written or read; the web has none.
6. **Who reads the per-buffer values:** only the threshold slider's meter — `level:` and `isClipping:`
   passed to `ThresholdSlider` from the main view's body (four layouts: `+Layouts.swift` 612,
   `+Controls.swift` 666, 833, 965). `recentPeakLevelDB` has no view reader.
7. **The main view observes the whole engine and the whole analyzer** (`@StateObject` for both in
   `TapToneAnalysisView`). With `ObservableObject`, *any* `@Published` change invalidates an observing view,
   whatever it reads. So the level, published 10×/s for one meter, rebuilds the whole window — controls,
   peak list, chart — 10×/s. The code already works around one symptom: `MenuActions` is held in `@State`
   so the Mac menu commands do not see a change "on each audio frame".
8. **Sheets:** Settings observed the whole engine (`@ObservedObject`) — rebuilt 10×/s by itself, and
   recreated with the main view. Saved Measurements, Measurement Detail and Edit observe the analyzer
   (≈ 1×/s from fact 4). Results observes both. Metrics observes the engine on purpose — it shows live
   values.
9. **#3's fix A would make this worse:** re-chunking Swift to 1024 frames gives ≈ 47 buffers a second, so
   ≈ 47 level publishes — the whole window five times as often. This plan has to land first.
10. **How the other editions delivered the level (before item 3).** Python: the processing thread's
    `rmsLevelChanged` signal went straight to the slider (`set_level_db`); Qt redraws only that widget. The
    web: `level` was React state in `useAudioEngine`, held by `App`, so every chunk's level re-rendered the
    whole app — the web's form of the same problem.

## Plan

| # | Item | Change | Done when |
|---|---|---|---|
| 1 | Settings stops observing the engine | `TapSettingsView` holds the engine as a plain `let` and keeps the four values it shows — devices, selected device, open failure, calibration — in its own `@State`, refreshed by `.onReceive` on each one's publisher. In the working tree. | the owner's two checks on the iPad (switch the input device → Sample Rate and Calibration follow; choose a calibration, then None → its details line appears and goes); no flicker — **seen** |
| 2 | `averageMagnitude` removed | Nothing read it: removed from Swift (property and computation) and Python (`average_magnitude`); the web never had it (decided, owner). | **done** — the analyzer no longer invalidates its observers on every FFT frame for it |
| 3 | The level on its own object, in all three (decided, owner) | `InputLevel` (`model/input-level`) owned by the engine as `level` — Swift `Models/InputLevel.swift`, Python `models/input_level.py`, web `src/audio/inputLevel.ts` — holding `inputLevelDB` / `input_level_db`, `isClipping` / `is_clipping`, `recentPeakLevelDB` / `recent_peak_level_db`; the engine writes them per buffer as before. The threshold meter takes the object and observes it alone: Swift `ThresholdSlider(inputLevel:)` (`@ObservedObject`), Python `ThresholdSlider.set_input_level(level)` (its `inputLevelChanged` / `clippingChanged` signals, moved off the processing-thread object), web `<ThresholdMeter inputLevel>` (`useSyncExternalStore` on `onInputLevel` / `onClipping`; `level` is no longer React state in `App`). The analyzer observes `level`'s clipping for the status override in all three (Swift `level.$isClipping` sink, Python `level.clippingChanged`, web `device.level.onClipping` in `setDevice`). Web's engine no longer resets its clipping state silently on stop — as Swift and Python. | **done** — suites: Swift 525, Python 1274, web 1159 + exports 20/20 + Playwright 11; parity map current |
| 4 | Measure again and decide | Same 20 s recording after items 1–3: main thread **4.9 s of 20 s (≈ 25 %)**, was 18.8 s (≈ 90 %); `TapToneAnalysisView.body` **42 runs** in the trace (≈ 1.5/s, start-up included), was 226 (≈ 12/s); chart content rebuilt 43×, was 227×; only `ThresholdSlider.body` runs at the buffer rate (844×, its level and its peak-hold timer). | **done** — the owner checked the app on the iPad and the Mac |
| 5 | Swift's status ping-pong (found by item 6's test) | The `$statusMessage` sink that recorded the latest real status ran asynchronously and wrote the status back: two messages written in one main-queue pass then alternated for good (≈ 160 000 writes/s, measured; arming straight after the analyzer is made did it). The status/notification tests had removed the analyzer's subscriptions, so none saw it; one re-arm test recorded a flake from it. Now `statusMessage`'s `didSet` records it synchronously, as Python's `_set_status_message` and the web's `setStatusMessage` do. Test in all three: two writes in one pass settle on the second and stay. | **done** (Swift `335ac2c`; tests Python `9dc4613`, web `eeef676`) |
| 6 | Tests for who is told (decided, owner) | `test/input-level` in all three: one buffer, while listening, is announced on the input level and by nothing else — Swift `objectWillChange` on the engine and the analyzer, Python every public signal of the analyzer and the processing thread, web every engine callback but `onAudioFrame` and the analyzer's subscribers. Each fails on a per-buffer announcement (checked). The redraw cost itself stays a manual Instruments check. | **done** |
| 7 | Python: calibration details stuck (found in the owner's check) | Settings filled the active calibration's details once, when built; choosing None left them showing, choosing one showed nothing, until Settings reopened. They now follow the model's active calibration and refresh with the picker, as Swift's and the web's do. Test `test_settings_calibration_details.py`. | **done** (Python `9dc4613`) |

**Order:** 1 → 2 → 3 → 4, then 5–7 as found. All before #3's fix A, which can now follow.

**Why the model, not the view layer, for item 3:** the alternative — the main view holding the engine
without observing it, with every read of a value that changes (≈ 490 reads of the two analyzers in six
files) moved into an observing subview — has the same effect for far more change and risk. Item 3 matches
how Python already delivers the level (fact 10).

## Decisions (owner, 2026-10-11)

1. Item 3 in all three editions, architecturally the same.
2. Python's unused `average_magnitude` removed (with Swift's `averageMagnitude`).
3. No Issue at first ("just fix it"); then opened as #28 so the doc has its Issue, as every plan doc does.
