# Replay does not bit-reproduce the original live capture

> **The living method extracted from this record** is in
> [`process/CROSS-EDITION-INVESTIGATION.md`](../../process/CROSS-EDITION-INVESTIGATION.md) — in
> particular that a stereo WAV is not an app dump and cannot serve as a replay-vs-live reference,
> which is the premise this issue was founded on. Re-measure before acting on any figure here.


**Status: ✅ RESOLVED 2026-09-18 — the requirement is met. Replay of a WAV the app generated
reproduces the live capture to float32 precision; the residual came from the fixture, not the
pipeline.**
_Opened 2026-07-19, from the peak-finding run-review automation._

Requirement (user): **replay of a WAV must produce the exact same results as the live capture that
generated it.** It currently does not, by a small amount. Re-run harness:
[playback-validation/](playback-validation/).

## The finding

Replaying a captured guitar WAV on the same platform reproduces the saved measurement **closely but
not bit-for-bit**:

| comparison | result |
|---|---|
| replay vs replay (same WAV, twice) | **0.000 dB — deterministic** |
| replay vs saved **live** capture, at the resonances (Air/Top/Back) | ≤0.003 dB |
| replay vs saved live capture, mean over the ≥−100 dB range | **~0.02 dB, 0 of 3702 bins exact** |
| replay vs saved live capture, deep noise floor (~19 kHz) | up to ~29 dB (near-silence bins) |

So the pipeline is deterministic run-to-run, and the **signal** reproduces to f32 precision, but
**every bin differs by a small amount** — the spectrum is shifted, not identical. Since the WAV
should contain the exact samples the live capture processed, identical samples through a
deterministic pipeline must give an identical spectrum. They don't — so the replay is not processing
the identical gated window the live capture did.

## Not caused by the peak-finding fix — PROVEN

The replayed spectrum (`frozenMagnitudes`, produced upstream of `findPeaks`) is **byte-identical with
and without the duplicate fix**, on all three platforms — verified by stash-and-fingerprint:

| platform | fingerprint sum | with vs without fix |
|---|---|---|
| Web | −3.954870332583e6 | identical to full float64 |
| Python | −3.954938892872e6 | identical |
| Swift | −3.956456521702e6 | identical |

`findPeaks` consumes the spectrum; it does not produce it, and our change provably does not alter it.
So this gap lives entirely in the capture/gating/averaging path we did not touch, and is safe to
treat as independent of the peak-finding work.

## Resolution (measured 2026-09-18)

Replayed the captured WAVs under current code and compared, bin by bin, against the full spectra
stored in the `.guitartap` files saved from the original live sessions. No new recordings were
needed — `.guitartap` carries the whole spectrum as base64 float32.

| fixture | format | replay vs live, worst bin |
|---|---|---|
| `brace-umik-1-swift-mac-1778816093.wav` | **1 ch FLOAT** — app dump | **7.6e-06 dB** |
| `plate-umik-1-swift-mac-1778816330.wav` | **1 ch FLOAT** — app dump | **7.6e-06 dB** |
| `5 tap test.wav` | **2 ch FLOAT** — not an app dump | 0.0027 dB at resonances, 39.96 dB at the noise floor |

7.6e-06 dB is **one float32 ULP** at those magnitudes; mean |Δ| across all 16384 bins is 2.3e-06 dB.
The app-dumped fixtures reproduce as exactly as float32 can represent. "0 of N bins exact" still
holds for them — but it is a statement about float32 resolution, not about the pipeline.

### Why the guitar fixture looked broken

`5 tap test.wav` reproduces this item's original numbers almost exactly: ~29 dB at the deep noise
floor near 19 kHz (measured 39.96 dB at 19656 Hz), ≤0.003 dB at the resonances (measured 0.0027 dB
above −60 dB), error shrinking monotonically as signal rises. That profile is a small *linear*
difference amplified by `20·log10` wherever the magnitude approaches zero.

The source is the file. It is **two-channel**, and the channels differ by at most `0.000457764` —
exactly 15 × 1/32768, a whole number of **16-bit** LSBs — in 26.6% of samples, correlation
0.99999892. A mono source through 16-bit quantisation, duplicated with independent rounding. The
app's `Dump Capture Audio` writes **mono float32** (`numChannels = 1` in the WAV writer), so this
file was not produced by the app and does not contain the samples the live capture processed.

**The founding premise was the error.** "The WAV should contain the exact samples the live capture
processed" is true for app dumps — and they reproduce. It is false for this fixture, which is a
separate, quantised recording of the same taps.

## Fixed along the way

- **Swift read the left channel where it intended to downmix.** `readAudioFileAsMonoFloat32` set an
  ExtAudioFile client format of mono and assumed CoreAudio would mix; it returns the first channel.
  Stereo files only — never the mono app-dump path — but Swift and Python analysed different audio on
  every stereo fixture. Settled rule: **a stereo recording is two channels of the same audio, so
  average them.** Where the channels are independently quantised copies, averaging also cancels half
  the quantisation noise, so it is strictly better than picking a channel.
- **Python and web never onset-aligned the guitar capture window.** Swift did. This was the
  hypothesised mechanism, present in two of three editions. With both fixed, Swift and Python produce
  bit-identical capture buffers and bit-identical FFT windows (8/8 and 8/8 on REG-G2).
- **The app no longer runs during tests.** `GuitarTapTests` is hosted in the app, so the app's own
  `TapToneAnalyzer` ran alongside the test's — opening the microphone and running 65536-point FFTs in
  parallel with the suite. A static probe pooled both objects' records, which read as a phantom 9th
  capture in an 8-tap measurement. `GuitarTapApp` now renders nothing when
  `XCTestConfigurationFilePath` is set.

## Left open

- Verified on two **material** app dumps. A mono **guitar** dump would complete the argument, since
  the guitar path is different code (rectangular window, per-tap accumulation). Worth doing
  opportunistically, not worth blocking on.
- The **iPhone captures are uncalibrated** (`calibrationName: None`, same UMIK-1 the mac/iPad
  calibrated with `7108913`) — a data-collection gap, to be recaptured. Never part of this item.
- `MATERIAL-MULTITAP-DISCREPANCIES.md` §3 describes the same family for the Swift-vs-others material
  discrepancy (issue #5, the 4800-frame buffer). Its line calling the **guitar** path
  "chunk-triggered" is stale against the current sample-onset-aligned code. Left untouched at the
  user's request; #5 and #3 remain open and were not investigated here.
