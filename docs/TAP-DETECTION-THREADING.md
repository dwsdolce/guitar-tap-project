# Tap detection threading — one per-chunk sequence, as on the web

**Issue:** [#38](https://github.com/dwsdolce/guitar-tap-project/issues/38)

Status: **OPEN — analysis done; plan to be written when the work starts, after #32.**

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

## Plan

To be written when the work starts.
