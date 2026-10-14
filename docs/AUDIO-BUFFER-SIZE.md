# Audio buffer size — the same tap, the same samples, in every edition

**Issue:** [#3](https://github.com/dwsdolce/guitar-tap-project/issues/3)

**Status:** ⏳ Items 1–6 DONE and committed 2026-10-13, all three editions — verified live by the
owner. Open: the live taps repeated with item 4 in place; items 7 and 8. Item 9 is #29.

**Commits:** Swift `698ce7a` (code), `6489b1b` (oracle generator), `de43fc5` (oracle) · Python
`07834e4`, `93b17f3` (macOS baseline), `5ad1181` (Linux, Windows) · web `fa0414b`, `7fa96a2` (macOS
baseline), `a78e415` (Linux, Windows).

**The goal (owner, 2026-10-12):** *"to make sure that all editions and platforms trigger taps at the
same point in the audio stream. This affects the actual frequency of any peaks."* A 0.1 Hz difference
changes no lutherie decision; it matters for accuracy and for trust between the editions.

**Related:** [SAMPLE-BASED-TRIGGER.md](SAMPLE-BASED-TRIGGER.md) (#29) — the change that would remove
the cause rather than its consequences. `tooling/chunk-boundary-sweep.py` — the tool that measures
all of this without live taps.

## Root cause

**Swift's live audio arrives in 4800-frame buffers (0.1 s at 48 kHz), not the 1024 it asks for.**
The size given to `installTap` is a hint; CoreAudio decides. Python (PortAudio) and the web (its
worklet) process 1024-sample chunks. Confirmed live on 2026-10-13 — Swift now logs the delivered
size at each engine start: `Audio buffers delivered: 4800 frames`.

Everything downstream stepped once per delivered buffer: the level meter, the tap trigger, ring-out
tracking, the session recording.

**And a second cause, found while fixing the first.** Even on 1024-sample chunks, the tap trigger
lands wherever a chunk boundary happens to fall, so each edition's capture starts at a different
sample. The alignment step exists to take that out of the FFT window — and two things leaked through
it (items 3 and 4).

## What the 2026-07-16 evidence did and did not show

Two simultaneous captures by all three editions showed Swift's peaks 0.04–0.10 Hz from the other
two, which agreed with each other to under 0.001 Hz. It was attributed to the buffer size alone.
**That attribution was unproven:** at the time Swift aligned the guitar FFT window to the tap's
onset and Python and the web did not (they gained it in September, #7), so Swift differed from them
in two ways at once. The measurements below are the ones to rely on.

## Symptoms

| # | Symptom | Before | Now |
|---|---|---|---|
| 1 | Ring-out measured once per buffer | Swift exactly 0.100 s; others on a 21 ms grid | Swift on the 21 ms grid by construction — **not yet measured live** |
| 2 | Peak frequencies differ between editions | up to 0.044 Hz on one live tap | none: bit-identical FFT windows (items 1, 3, 4) |
| 3 | Session recording length | a multiple of 4800 | on the 1024 grid, as the others — verified |
| 4 | Swift's level meter updates ~10 times a second | — | **unchanged** (item 7) |
| 5 | Swift confirms a live tap up to ~200 ms late | — | the trigger is on the 1024 grid, but audio still arrives every 0.1 s (item 7) |

## Items

| # | Item | Swift | Python | Web |
|---|---|---|---|---|
| 1 | Delivered buffers are cut into 1024-sample chunks | ✅ | n/a | n/a |
| 2 | The level meter is told once per delivered buffer | ✅ | n/a | n/a |
| 3 | A guitar window's audio ends at a fixed length; zeros follow | ✅ | ✅ | ✅ |
| 4 | The onset is found from the noise just before the tap | ✅ | ✅ | ✅ |
| 5 | Capture probe: the web has it; all three can record live captures | ✅ | ✅ | ✅ |
| 6 | Golden values and baselines re-minted | ✅ | ✅ | ✅ |
| 7 | Swift's meter rate and live confirmation latency | open | — | — |
| 8 | Ring-out measured from the samples, not per chunk | open | open | open |
| 9 | A sample-based trigger | → #29 | → #29 | → #29 |

**1. Re-chunking (Swift).** `processDeliveredSamples` appends each delivered buffer to the remainder
of the last, passes every whole 1024 samples to `processRawSamples`, and keeps the rest; the
remainder is cleared at each engine start. File playback already fed 1024-sample chunks.
`RealtimeFFTAnalyzer.chunkSize` is the one constant for both.
- *Tests:* `AudioChunkingTests` — buffers of 4800, 777, 512 and 1024 frames reach the pipeline as
  whole chunks, in order; the audio clock advances a chunk at a time.

**2. One meter update per delivered buffer (Swift).** A 4800-frame buffer's four chunks are
processed in the same instant, so announcing each level redrew the meter four times in one frame
(SwiftUI: "onChange(of: Float) action tried to update multiple times per frame"). The live path
announces the loudest chunk's level once per delivered buffer; playback still announces each chunk.
- *Test:* `AudioChunkingTests` — one four-chunk buffer tells the meter once, the loudest chunk's level.

**3. The fixed zero tail (all three).** A guitar capture is exactly as long as its FFT window and
starts 0.2 s before the trigger; the window starts 0.1 s before the onset. So the capture ran out
before the window's end by an amount that depended on the chunk boundary — 2,700 to 3,700 samples of
zeros at 48 kHz, differing by up to 1023 between editions. That alone moved a weak peak by 0.044 Hz.
Now the window's audio always ends at `fftSize − (pre-roll − pre-onset)` — 60,736 samples at 48 kHz —
and exactly 4,800 zeros follow (`guitarWindowAudioSamples`).
- *Tried and dropped:* capturing 0.1 s more, as plate and brace do (0.5 s for a 0.4 s window). It
  works, but it lengthens the time before the next tap can register from about 1.7 s to about 1.8 s,
  and the 8-tap guitar recording — a master luthier's, not replaceable — has taps 1.71 s apart: taps
  were missed. *Decision (owner, 2026-10-13):* "Let's try the fixed zero tail."
- *Cost:* the last tenth of a second of a 1.4-second window is never analysed; 0.06–0.08 s of it
  already was not.
- *Test:* `test/guitar-capture-window` GW1 — one tap played with its chunk boundaries at four
  positions gives a bit-identical window.

**4. The onset rule (all three; shared with plate and brace).** The onset was the first sample above
ten times the noise measured over the first 2048 samples *of the capture* — a different stretch of
noise for each capture start, so a slightly different threshold, and an onset 1–3 samples apart
between editions (up to 10 on one tap of the 8-tap recording). Now, after that first estimate, the
noise is measured again over the 2048 samples ending 256 before the estimate and the onset found
again, until it stops moving (at most four passes).
- *Also tried:* a threshold 40 dB below the tap's own peak. Not robust — on quiet brace taps it falls
  into the noise and the onset lands thousands of samples early.
- *Decision (owner, 2026-10-13):* "implement the onset rule (it is simple and has improvement)."
- *Test:* GW2 — a tap captured from seven starting samples aligns to the same window.

**5. The capture probe.** The web gained the probe Swift and Python had (`src/state/captureProbe.ts`,
`tooling/capture-probe.sh`). All three gained a developer switch — `CaptureProbe.liveProbe`,
`LIVE_PROBE` — off in every release: with it on, and Dump Capture Audio on, each measurement's
capture fingerprints are written beside its recording as `<recording>-capture-probe.json`. A release
build refuses to proceed with the switch on (Swift: the Release configuration; Python: the packaging
builds; web: `npm run build`).

**6. Re-minting.** The oracle was re-minted from Swift at `6489b1b` and synced to Python and the
web; their macOS baselines were re-minted locally and their Linux and Windows baselines on the CI
runners (the *Mint self-baselines* workflow). What moved, identically on all three platforms: REG-G2 (the 8-tap guitar case) — 54 values, at
most 0.0013 Hz and 0.0023 dB — and one magnitude of REG-B2 (0.0005 dB). Nothing else; no gated-FFT
case. Suites: Swift 536, Python 1283, web 1164.
- *Found:* the oracle generator never re-minted REG-B2. The case was added to the oracle by hand in
  September and not to the generator's list of material cases, so its value could not follow a
  change; Swift's suite kept failing on it after the first re-mint. Added (`6489b1b`).
- *Found:* the first push left Python's and the web's CI failing on Linux and Windows — only the macOS
  baselines had been re-minted. A change that moves golden values needs all three platforms'
  baselines minted before it is pushed.

**7. Swift's meter rate and confirmation latency — open.** Cutting a buffer into chunks does not
make audio arrive more often: the screen still sees a burst every 0.1 s. Changing that means taking
audio from the system by another mechanism than the tap. Not investigated. *Owner, 2026-10-12:* "I am
less concerned with the meter update than I am with the difference calculation."

**8. Ring-out from the samples — open.** Ring-out is measured on the 21 ms chunk grid in every
edition (±21 ms). A sliding measure on the samples would be sub-millisecond and independent of
chunking. No decision.

## Measurements (2026-10-13)

Three editions on one Mac and one microphone, recording the same taps; the editions' recordings are
bit-identical audio.

| | Result |
|---|---|
| Re-chunking alone, 3 taps | Tap onset and window start at the same sample in all three editions; largest peak difference 0.044 Hz (a weak peak), 0.003 Hz on the strongest |
| + fixed zero tail, 5 taps | Largest peak difference 0.0013 Hz; editions with the same onset have bit-identical windows; onsets 1–3 samples apart on 4 of 5 taps |
| + onset rule | Every tap in the six test recordings (29 taps): one onset and one window at all 1024 chunk-boundary positions. The three editions' windows for the 8-tap recording: bit-identical, 8 of 8. **Not yet repeated with live taps.** |

For scale: the strongest peak of three consecutive taps read 240.03, 240.06 and 240.09 Hz — tap-to-tap
variation is 20–50 times the timing effect that remained after the fixed tail.

The peak figures are an FFT of each edition's window computed outside the apps, uncalibrated — not
the values the apps display.

## Run-review

1. Start Swift and read its log (debug logging on). → One `Audio buffers delivered: N frames` line.
   *Passed: 4800.*
2. With all three editions on one microphone, the web tab visible and Dump Capture Audio on, take
   several single-tap guitar measurements. → The probe files show the same window fingerprint in all
   three for each tap. *After items 1 and 3: passed where the onsets agreed. To repeat after item 4.*
3. Check Swift's recording length. → A whole number of 1024-sample chunks plus the same fraction as
   Python's, not a multiple of 4800. *Passed.*
4. Tap a guitar and read the ring-out in Swift. → Not exactly 0.100 s. *Not yet done.*

## Found while doing this

- **Swift recorded from the wrong microphone** after a hot-plug with other applications opening the
  same device — #30, [completed/WRONG-INPUT-DEVICE.md](completed/WRONG-INPUT-DEVICE.md).
- **A tool that models the editions must be checked against them before its numbers are used.** An
  early version of the boundary sweep reported that the 8-tap recording loses a tap at 59 % of
  boundary positions; it was re-arming a chunk late. `--probe` exists so the model has to reproduce
  the editions' own captures first.
