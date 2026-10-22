# Tap detection threading — one per-chunk sequence, as on the web

**Issue:** [#38](https://github.com/dwsdolce/guitar-tap-project/issues/38)

Status: **OPEN — plan written; decided: one per-chunk sequence on the main thread in every edition, the FFT included; waits on #35, then Python's measurements.**

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
