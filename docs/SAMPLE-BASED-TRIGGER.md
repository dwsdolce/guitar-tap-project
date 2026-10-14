# A sample-based tap trigger — analysis, and what a plan needs

**Issue:** [#29](https://github.com/dwsdolce/guitar-tap-project/issues/29)

**Status:** 📋 OPEN — analysis only (2026-10-13). No plan, no code. This document is the input to a
plan; it does not propose one.

**Decision that opened it (owner, 2026-10-13):** *"doing chunk based first was a mistake on my part …
If I had it to do over again I would make it sample based."* The owner asked for an issue holding the
analysis and what is needed to plan the change.

**Related:** [AUDIO-BUFFER-SIZE.md](AUDIO-BUFFER-SIZE.md) (#3), whose work produced the measurements
here. All three editions; Swift is canonical.

## The idea in one paragraph

Every edition detects a tap from the loudness of whole 1024-sample chunks. Where the chunk boundaries
fall against the audio is an accident — of when the stream started, of the edition, of the run — so
the trigger lands on a different sample each time for the same tap. A sample-based trigger measures
loudness on the stream of samples and fires at one particular sample, which depends on the audio
alone. Every edition would then trigger, and start its capture, at the same sample.

## What depends on the chunk boundary today

| What | Depends on the boundary? | State on 2026-10-13 |
|---|---|---|
| The trigger sample | yes — anywhere in a 1024-sample range | unchanged; this is what a sample-based trigger removes |
| Where the capture starts (trigger − 0.2 s pre-roll) | yes, with the trigger | unchanged |
| Where the FFT window starts | no — aligned to the tap's onset | fixed under #3: the onset is found from the noise just before the tap |
| Where the window's audio ends | no | fixed under #3: a fixed length, then zeros (guitar) |
| Whether a tap is detected at all | not in any recording tested | see "Detection" below |
| The dead time before the next tap can register | by up to one chunk | unchanged |
| Ring-out time | no — measured from the samples of the tap's window | fixed under #3 (item 8) |

So the repairs made under #3 — re-chunking Swift's 4800-frame buffers to 1024, the fixed zero tail,
the onset rule — each remove a consequence of the trigger sitting on a grid. A sample-based trigger
removes the cause. With it, the capture always starts at the same sample, and the onset rule and the
fixed tail would no longer be needed for consistency (they would do no harm).

## What was measured

**Method.** `tooling/chunk-boundary-sweep.py` plays one recording at every one of the 1024 possible
positions of the chunk boundary (the recording with its first *k* samples dropped) and reports, per
tap, how many positions detect it and how many different onsets and FFT windows result. It is a
model of the editions' rules, checked against them: given the capture-probe files the editions wrote
for the same audio, it reproduces every capture start, capture buffer and FFT window bit for bit
(24 of 24 records on the 8-tap guitar recording, and each edition's 8-capture sequence).

**Recordings:** the 8-tap and 5-tap guitar fixtures, the two brace and two plate fixtures (29 taps),
and nine live taps recorded simultaneously by all three editions.

**The window (now fixed).**

| Stage | Largest disagreement between editions on one live tap |
|---|---|
| Swift re-chunked to 1024; the window's tail still varying | 0.044 Hz (a weak peak); 0.003 Hz on the strongest |
| Fixed zero tail | 0.0013 Hz; onsets 1–3 samples apart on 4 of 5 taps |
| Fixed zero tail + onset rule | none — one onset and one window at all 1024 positions, every tap |

For scale: the strongest peak of three consecutive live taps on one guitar read 240.03, 240.06 and
240.09 Hz. Tap-to-tap variation is 20–50 times the timing effect that remained after the fixed tail.

**Detection.** Every tap in every recording is detected at all 1024 positions. One non-tap is not
consistent: a handling bump in `plate-umik-1-swift-mac-1778816330.wav` is picked up at 922 of 1024
positions — under the tool's simplified plate detection (see "What the tool does not model").

> **A correction worth keeping.** An earlier run of this analysis reported that the 8-tap recording
> yields eight taps at only 41 % of positions. That was the model re-arming one chunk late. Checked
> against the editions' own captures and corrected, it yields eight at every position. **There is no
> evidence that a real tap is caught or missed by the accident of the boundary.**

## The prototype that was tried

In `tooling/chunk-boundary-sweep.py` (`sample_triggers`): a running mean-square over the last 1024
samples, updated every sample; from below the threshold, it fires once it has stayed above for 1024
samples; then nothing until the dead time has passed.

- It gives one trigger sample per tap by construction.
- It fires at the earliest of the chunk-based triggers or up to 1023 samples before — on average
  about 10 ms sooner.
- On all six fixtures it finds the same taps as the chunk-based rule (8, 5, 1, 3, 3, 9) — plus the
  plate handling bump, every time.
- With it, the old onset rule (noise at the start of the capture) already gives a single onset.

It was run offline only: not in any edition, not live, and not with the noise floor plate and brace
use.

## The case for it, and against

**For.** It is the simpler idea — detect on the audio, not on how the audio was delivered — and it
removes the reason for three repairs. It makes the dead time and the trigger latency the same in
every edition. Any future difference between editions is then a fault, never an accident of timing.

**Against.** It redefines when a tap is detected, in all three editions: every tap-detection test and
every golden value moves, and real tapping must be re-checked on every platform. The measurable gain
on the window is already had: the editions agree exactly on every tap tested. And "the same every
time" is not "right": the prototype detects the handling bump every time, where today's rule (tuned
in May 2026 to need two consecutive chunks, to reject exactly that bump) misses it some of the time.

## What a plan has to decide

1. **The loudness measure.** A running RMS over how many samples; or an envelope follower. The
   threshold's meaning must survive: users have a Tap Threshold set against today's per-chunk RMS.
2. **The confirmation rule.** Today: two consecutive chunks above the threshold after a fresh rising
   edge (≈ 43 ms). Per sample: above for how long, and how is a 1-chunk bump still rejected?
3. **Hysteresis.** Today a 3 dB margin on the main-thread detector; how it reads per sample.
4. **Plate and brace.** Their detection is relative to a noise floor tracked by an average updated
   once per chunk, re-anchored at the end of a 0.5 s warm-up. All of it steps per chunk today.
5. **The two detection paths.** Swift and Python have a per-chunk detector on the audio thread and
   another on the main thread; the web has one. A plan should say whether one remains.
6. **Where the capture starts**, and whether the pre-roll, the onset alignment, the fixed tail and
   the onset rule stay, simplify or go.
7. **The rest and re-arm.** Dead time is counted in chunks of audio today.
8. **Cost per sample** in each edition — Python in particular, where it must be done on whole
   buffers with running sums rather than a loop, with state carried across buffers.
9. **Numerical sameness across editions.** A running sum accumulates rounding differently from one
   start to another; "the same sample in every edition" needs a formulation that does not.

## What exists to test it with

- `tooling/chunk-boundary-sweep.py` — the boundary sweep, with the prototype trigger, and `--probe`
  to check the model against the editions.
- The capture probe in all three editions, and its developer switch (`CaptureProbe.liveProbe` /
  `LIVE_PROBE`), which writes each live measurement's capture fingerprints beside its recording.
- `test/guitar-capture-window` in all three: the same tap at four boundary positions gives the same
  window (GW1); the same tap captured from seven starting samples aligns to the same window (GW2).
- `test/tap-decisions`, `test/audio-clock-timers`, `test/file-playback` — the existing detection
  and lifecycle cases, which a change must keep or knowingly move.
- The file-playback fixtures. A recording the app saved has about two seconds before its first tap
  and can be shifted across a whole chunk by dropping samples; the short external guitar recordings
  (0.15 s of lead-in) cannot.

## What the tool does not model

- Plate and brace detection: it uses the threshold itself, not the moving noise floor. Their captures
  and alignment are modelled; which of their events is detected is indicative only.
- The rest after a capture, beyond a fixed dead time that re-arms on the chunk in which it ends.
- Anything live: devices, the size of delivered buffers, restarts. Live taps remain the check there.
