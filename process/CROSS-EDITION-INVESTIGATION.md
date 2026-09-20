# Investigating a cross-edition difference

How to find out why two editions disagree about a number, and how not to waste days on it.
Extracted from the #5, #7 and #10 investigations (2026-09), each of which cost far more than it
should have because one of these rules was missing.

## 1. Compare ONE recording through every edition — never each edition's own capture

A per-edition `.guitartap` comparison **cannot** separate a DSP divergence from different physical
taps, because each app recorded its own audio. Three apps in a room with one mic are three
recordings, not one experiment.

Replay a **single** file through every edition instead. Any difference that survives is the code,
and nothing else. This is what finally settled #5 after two months of a "Swift is 2 dB low"
finding that was never reproducible.

## 2. Know whether the WAV is an app dump

The app's `Dump Capture Audio` writes **mono float32**. So:

- A **mono float32** WAV beside a `.guitartap` is the samples the app actually processed. Replay
  reproduces the live capture to one float32 ULP.
- A **stereo** WAV is *not* an app dump. It came from somewhere else, and it does not contain the
  samples the live capture processed. It cannot be used as a replay-vs-live reference.

Issue #7 was founded on that exact mistake — its headline "~0.02 dB per bin, 0 of 3702 bins exact"
came from comparing the app's live input against a separate, 16-bit-quantised recording of the same
taps. Check `sf.info(path).channels` before drawing a conclusion.

## 3. Fingerprint the inputs before theorising about the arithmetic

When two editions disagree, hash what goes *into* the transform, on both sides of any windowing
step. That splits the problem three ways in one run:

| observation | where the divergence is |
|---|---|
| buffers differ | upstream — detection or buffering |
| buffers match, windows differ | the alignment/windowing step |
| both match | the arithmetic — look at the transform, not the capture |

Use FNV-1a over the IEEE-754 bit patterns, the same function in each edition, so the hex strings
compare directly (`CaptureProbe.swift` / `capture_probe.py`). Two theories died on contact with
this in #5 — "Python isn't averaging" and "they pick different taps" — both plausible, both wrong,
both cheap to disprove once the inputs were hashed.

## 4. Re-measure before acting on an archived finding

**An investigation doc records the code as it was on the day.** Three of the four findings chased
in 2026-09 had been silently fixed by intervening work:

- #5's "Swift is ~2 dB lower" — replaying the same recordings through the current build gave
  −54.00 dB where the archived live capture recorded −56.02.
- #7's premise that replay cannot reproduce live — true only for the non-app-dump fixture.
- "Swift's `measurement-type-name` test does not exist" — it had existed since `38c37a5`, and the
  parity map already listed it.

These docs even warn that their `.guitartap` evidence is transient. The warning applies to their
conclusions too. **Reproduce the finding on today's build before spending a day on its cause** —
and before overwriting a file the doc claims is missing.

## 5. A diagnostic must know which object it is measuring

A static/global collector in a **hosted** test bundle pools every live instance in the process. The
app's own analyzer runs alongside the test's, so its captures appear in the test's records — in #7
that read as a phantom 9th capture in an 8-tap measurement, intermittent, with different content
each run. Tag records with the instance that produced them and filter.

Related: `GuitarTapApp` now renders nothing when `XCTestConfigurationFilePath` is set, so the app
no longer builds an analyzer, opens the microphone, or runs FFTs during a test run.

## 6. A comment that describes how the code works is evidence with no expiry date — check it

Rule 4 covers archived *findings*. It does not cover the far more common case: a descriptive claim
in a comment, docstring or file header. Prose that explains how code works is written once, is
rarely re-read against the code, and reads as settled fact precisely because someone took the
trouble to write it down. Every false record found in 2026-09 but one was of this kind:

- `_remap_by_freq`'s docstring — *"the Python equivalent of the Swift carry-forward logic"*. It was
  a second implementation, and six tests asserted against it instead of production.
- `test_frozen_peak_recalculation.py`'s header — *"the Python remap logic lives in
  TapToneMeasurement data structures rather than in a separate recalculate method"*. False; it is
  `recalculate_frozen_peaks_if_needed`. This sentence is why the helper existed.
- `FrozenPeakRecalculationTests.swift`'s header — "Test plan coverage: PR1–PR7", after the suite had
  moved on.
- `fromLive.ts` — *"`a.peaks` (≥ Peak Min …) are kept; only the sub-Peak-Min peaks are appended"*.
  True before Phase 1. After it, that append wrote a duplicate of every sub-Peak-Min peak into every
  saved measurement: 111 peaks in, 217 out.
- The July reconciliation plan, still standing as authoritative while contradicted elsewhere.

**When a comment states what other code does, read that other code before trusting it** — especially
when it is the reason something exists. The dangerous ones are not stale notes; they are load-bearing
sentences that were true when written.

Corollary for tests: a fixture encodes a contract. When the production contract changes, a test whose
fixture still supplies the old one keeps passing while proving nothing about the shipping path.
`peak-fullset-save.test.ts` passed a Peak-Min-filtered set that `App.tsx` had long stopped sending,
and that is what hid the duplicate-peak bug. Check what the APPLICATION passes, not what the test does.
