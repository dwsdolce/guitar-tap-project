# File-playback results depend on machine speed

**Issue:** [#19](https://github.com/dwsdolce/guitar-tap-project/issues/19)

**Status:** OPEN — root cause demonstrated in Python; Swift has the same structure, not yet measured;
web partly audio-clocked. No code changed. Found 2026-09-23 during #17 (S6, finding F44).

## The symptom

Python's `tests/test_self_regression.py` (zero tolerance against this machine's own baseline) fails
under pytest, but the same pipeline run as a standalone script passes against the same baseline, on
the same machine and tree. The number of moved values is **not stable**: pytest reported 19 of 94,
then 21 of 94, on the same code.

What moves (21-of-94 run, GFFT4 aside — that one is F44's deliberate −∞):

- REG-G2 **taps 7 and 8 only** — the last two of eight. Taps 1–6 are bit-identical to the baseline.
  Largest: tap 7 air +0.041 Hz / −0.457 dB; tap 8 air +0.033 Hz / −0.350 dB.
- REG-G2 averaged peaks — only because taps 7 and 8 feed the average.
- REG-P2 `flc/frequency` +0.051 Hz — FLC is the **last** phase of the plate sequence. One further
  value was past pytest's display limit and was not seen.

A DSP change would move every tap. This moves the end of a sequence, by a varying amount: a timing
signature.

## The mechanism

Two clocks run during file playback, and the tap lifecycle straddles them.

1. **Audio advances at "real time + processing time."** Playback processes a chunk and then sleeps one
   chunk's duration:
   - Python `process_file_data` —
     [`realtime_fft_analyzer_engine_control.py`](../../guitar_tap/src/guitar_tap/models/realtime_fft_analyzer_engine_control.py)
     (`process_raw_samples(chunk)` then `time.sleep(chunk_duration)` then pump the Qt loop).
   - Swift `processFileData` —
     [`RealtimeFFTAnalyzer+EngineControl.swift`](../../GuitarTap/GuitarTap/Models/RealtimeFFTAnalyzer+EngineControl.swift)
     (`processRawSamples(chunk)` then `Thread.sleep(forTimeInterval: chunkDuration)` on a background
     queue).
2. **The tap lifecycle is timed on the wall clock.** Cooldown / re-enable, capture window, safety
   timeout and the FLC cooldown are scheduled as delays:
   - Python `_main_async_after` → `QTimer.singleShot` (`tap_tone_analyzer_spectrum_capture.py`,
     `tap_tone_analyzer_tap_detection.py`, `tap_tone_analyzer_control.py`).
   - Swift `DispatchQueue.main.asyncAfter`.

So when a timer fires, how much audio has passed depends on how long each chunk took to process. A
timer landing one chunk earlier or later moves where detection re-arms and which samples a capture
takes in. The error accumulates along the sequence, which is why the last taps move first.

**Web** is partly different: detection and warm-up are timed on `audioTime`, and the parity runner
plays **unpaced** (`pace: false`) yet reproduces its baseline, so the paths the oracle exercises are
audio-clocked. It still has one wall-clock timer — the FLC cooldown `setTimeout` in
[`tapToneAnalyzer.ts`](../../GuitarTapWeb/src/state/tapToneAnalyzer.ts). The rest is not audited.

## The evidence

REG-G2 alone, fresh settings sandbox, artificial work added after each chunk in a scratch wrapper (no
edition code touched), compared to the baseline:

| added work per chunk | REG-G2 values moved |
|---|---|
| 0 ms | 0 / 54 |
| 5 ms | 0 / 54 |
| 15 ms | **54 / 54 — all 8 taps** |

The pytest run took 385 s against ≈ 4 min standalone; it sat just past the threshold, so only the
tail moved.

## Explanations ruled out — do not re-investigate

| hypothesis | how it was killed |
|---|---|
| F44's epsilon-clamp removal | A/B of none / live / gated / both clamps gives identical REG-G2 peaks; with the clamp removed only GFFT4 moves, in both environments |
| Machine load (as distinct from speed) | failed on an idle machine; the variable is processing time per chunk, which load is one cause of |
| The user's real settings vs the test sandbox | every settings read during REG-G2 logged and diffed; each differing key seeded into a sandbox one at a time and all together — 0 moved |
| Ordering leak between cases (in memory or on disk) | full `compute_all()` — all six cases in sequence — in a fresh sandbox outside pytest moves only GFFT4 |
| pytest configuration | no plugins beyond `pytest-cov`, no `addopts`, no warning filters |

A side lesson: a scratch script named `bisect.py` in `/tmp` shadowed the standard library module and
invalidated one round of results. Scratch scripts go in the session scratchpad with prefixed names.

## History — why it never failed before

| date | event |
|---|---|
| 2026-04-15 / 05-04 | Python wall-clock capture-window timer (`be0a456`, `69ed447`) |
| 2026-04-23 | Python real-time pacing sleep (`1709ce6`, `5252220`) |
| 2026-05-06 / 05-11 | Swift `Thread.sleep(chunkDuration)` pacing (`434315b`, `a17da56`) |
| 2026-06-17 → 07-31 | released in 1.0, 1.0.1, 1.0.2 |
| 2026-09-18 | parity bar tightened from **1 Hz / 1 dB** to 0.02 Hz / 0.01 dB (hub `60be927`); zero-tolerance self-baseline introduced (Python `73dee74`), both #10 |

Every observed move is far inside 1 Hz / 1 dB, so the old bar could not see it. The tightening exposed
an old defect; it did not introduce one. The tightened **parity** bar (0.01 dB) is also far below these
moves: Python's parity tests have passed only because they ran at a speed where the timers lined up.

## Open questions

1. **Magnitude.** How large do the moves get on a slower machine? Only pytest's values were measured;
   the 15 ms run showed *that* everything moved, not by how much. Is 1 Hz / 1 dB ever exceeded?
2. **A reliable test case.** The pytest failure depends on this machine's speed and could pass
   elsewhere. The injected-delay run is machine-independent but has been run once — confirm it repeats
   bit-identically before relying on it.
3. **Swift.** Same structure; not yet shown to move. Its self-baseline is bit-reproducible only at the
   speed it ran.
4. **The live app.** The same wall-clock timers run live. A slow audio callback or a pause shifts
   capture boundaries against the audio. Unmeasured.
5. **Fix direction.** Principled: drive the tap-lifecycle timers from **audio time** in all editions,
   Swift first — the same lesson as the ring-out decay fix ("a timestamp must travel WITH the sample").
   Not recommended: unpaced playback, which would make tests deterministic while leaving the live app
   exposed. Needs a design and the owner's approval; it changes canonical Swift.
6. **Tests define their full context** (owner, 2026-09-23). Every test must set its measurement type
   itself — including which of the four guitar types — never inherit it from a settings file or the
   environment. Python's runner does pass the type, but `play_file_for_testing` delivers it by writing
   the global settings store, which production then reads back in ~40 places. Swift and web not yet
   checked.

## Interim

Until this is fixed, Python's `test_self_regression` can fail under pytest for this reason alone. A
failure listing only late-sequence REG-G2 / REG-P2 values is this issue; anything else is not.
