# Tap detection threading — one per-chunk sequence, as on the web

**Issue:** [#38](https://github.com/dwsdolce/guitar-tap-project/issues/38)

Status: **OPEN — plan written; measuring the slack on every edition and platform before the decisions.**

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

## The target: one per-chunk sequence

The web's `processAudioFrame(samples, levelDB, audioTime)` (`src/state/tapToneAnalyzer.ts`) is the model. On one
thread, for each chunk, in this order:

1. **Fill**: the pre-roll ring, the session recording, and the open capture window. A window that fills is finished
   there and then — a direct call, not a queued one.
2. **The audio clock**: `lastAudioTime`, then any timed action this chunk makes due (`runDueAudioActions`).
3. **Detect** — if no action ran and detection is listening: `detectTap`, and on a confirmed tap
   `handleTapDetection`, which sets detection idle and opens the capture from the pre-roll. The pre-roll already holds
   this chunk, so the capture lines up with the tap by construction.

Swift and Python keep their audio thread for what is heavy or must not wait — taking delivery, cutting 1,024-sample
chunks, the level, clipping, the dead-input stamp, and (see decision 1) the FFT — and hand each chunk to the main
thread in **one hop** carrying `(samples, levelDB, audioTime)`. The main thread runs the sequence above. Order replaces
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
  filling (on the audio thread in Swift and Python, within main/chunk on the web); **fft** — the FFT, wherever it runs;
  **frame** — the main thread's work on each FFT frame.

**Switching it on:**

| Edition | How |
|---|---|
| Swift | the environment variable `GT_SLACK_PROBE=1` (Xcode: the scheme's Run → Arguments → Environment Variables); the line goes to Xcode's console |
| Python | `GT_SLACK_PROBE=1 python -m guitar_tap`; the line goes to the terminal |
| Web | `?slackprobe` on the page's URL; the line goes to the browser console (on an iPhone, Safari's Web Inspector from the Mac) |

**The deciding test:** Swift and Python with `GT_SLACK_PROBE_FFT_ON_MAIN=1` as well — after each FFT frame the main
thread spins for the FFT's measured duration, the cost it would carry if the FFT ran there.

**Scenarios**, each for about 30 s, on every edition and platform (Swift: Mac, iPhone, iPad; Python: Mac, Windows,
Linux; the web: desktop and iPhone): idle listening; a guitar tap through to the results; a plate through all three
phases; zoom and pan while listening; Saved Measurements open; file playback. Swift on a Release build as well as
Debug, since the Debug build's timings are slower.

**First readings** (Mac, idle listening, 2026-10-21): Swift (Debug) — lag p99 11 ms, latency p50 0.02 ms, FFT 17.5 ms,
main busy ~0 %. Python — FFT 9–17 ms, but **the main thread's work on each FFT frame 128–145 ms**, lag max 230 ms,
latency p95 120–130 ms, main busy 6–11 %: Python's main thread already falls a few chunks behind at every frame.

## Steps

Each step is a commit in each edition it touches, then the hub with the hashes.

1. **The defect as a shared case, first.** A shared case file (`tap-capture-sequence.json`, `test/tap-capture-sequence`)
   driving each analyzer through its real per-chunk entry point: a crossing in the warm-up, a crossing below the
   relative threshold (plate, brace), a real tap — each with the expected outcome (no capture / no capture / one
   capture, detection idle on completion). The web passes it today; Swift and Python fail the first two. Linked
   under the code's parity group.
2. **Swift**: the one hop and `processAudioFrame`; delete what goes; the synchronous test helpers (`runAnalyzerStep`,
   `advanceAudio`) call `processAudioFrame`, as the app does. Unit tests, file-playback regression, capture
   alignment (`GuitarCaptureWindowTests`), the export UI tests.
3. **Python**: the same, through one queued signal; the processing thread and the file-playback thread both hand
   chunks to it. The same test set, and `TestPipelineDeliversOnceAndExact` updated for the one hop.
4. **Verification**:
   - the full suites in all three editions (on the owner's go);
   - the export and self-regression baselines — any shift listed with its cause before anything is re-minted;
   - **Python's display under load measured**: the live spectrum's frame interval and the main thread's per-chunk
     time while a tap sequence runs, before and after;
   - a run-review by platform, the physical iPhone and iPad included (a capture on a real tap; the warm-up and
     clipping cases that produced this issue; file playback of each type).
5. **Close-out**: comments and docs that describe the old mechanism (the fast-start in DocC, docstrings, the
   INVENTORY), the record, the Issue.

## Decisions to take

1. **Where the FFT runs.** The web runs it on its one thread; Swift and Python could keep it on the audio thread and
   publish its frame as today. What this issue fixes is detection and capture in one sequence; the FFT feeds the
   display and the frame-based analysis, and nothing in the defect depends on where it runs. Keeping it off the main
   thread spares Python's busier main thread its ~10 ms every 1.37 s.
2. **The order of Swift and Python** — one after the other with a run-review between, or both before one.
