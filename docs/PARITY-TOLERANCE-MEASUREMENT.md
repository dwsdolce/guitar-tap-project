# Measuring the cross-edition parity tolerance

**Status:** 📋 REQUIREMENTS — for review. Nothing implemented.
**Issue:** #10 (follow-on). **Depends on:** the oracle cutover, done 2026-09-18.

## Why

`tolerances` in `parity-oracle.json` is `1 dB / 1 Hz / q 1 / ringOut 0.03`. Nobody
measured that; it is a safe round number. It is almost certainly far looser than the
editions actually differ, and a tolerance that loose stops being a check — the Swift
goldens drifted by up to 0.0028 dB for an unknown length of time and nothing noticed,
because the bar was four orders of magnitude above the drift.

The aim is to **replace a guessed number with a measured one**. That requires knowing
how far apart the editions really are, on every platform they ship on.

## What this is not

- **Not** a change to what passes. No assertion changes, no tolerance changes, no test
  outcome changes. Data capture only.
- **Not** the same-edition regression check. That is settled and live in Swift:
  `selfTolerances` is **zero**, because an edition checking goldens it minted itself
  runs the same bytes through the same code on the same machine, and Swift is proven
  bit-reproducible (two mints, 140/140 identical). Any movement there is a real change.
  This document is only about the **cross-edition** bar.

## Requirements

| # | Requirement |
|---|---|
| R1 | Measurement is **live in every edition** — Swift, Python, web, and Kotlin when it exists. Not a one-off script run once on one machine. |
| R2 | Runs on **every OS each edition supports**: macOS, Windows, Linux; both browsers for web. |
| R3 | **Changes nothing about what passes.** Enabled by an env flag, absent otherwise. |
| R4 | The recorded number is **exactly what the suite compares** — measured at the assertion site, not by a parallel reimplementation that can silently diverge. |
| R5 | Each report carries **provenance**: edition, OS, arch, CPU, runtime/compiler version, the oracle's `oracleVersion`, timestamp. A delta means nothing without the machine that produced it. |
| R6 | Reports **collect in the hub** and merge across machines and dates. |
| R7 | A **summariser** reports max \|Δ\| per field class across everything collected — the number a tightened tolerance would be based on. |
| R8 | Adding a new edition or OS must not require changing the others. |

## Open decisions

1. **How the delta is captured.** Instrument the existing comparisons — replace
   `abs(x - y)` with a `delta(x, y, label)` helper that returns the same value and
   records it — versus a separate module that re-runs each case. Instrumenting costs
   ~40 mechanical edits per edition but satisfies R4 by construction; a separate module
   touches nothing but must restate each case's setup (REG-P1's phases, REG-G2's eight
   taps), and any divergence there produces numbers that are not the ones the suite
   sees. **Recommendation: instrument.**
2. **Where reports live.** Proposed `tooling/parity/measurements/<edition>-<os>-<arch>-<date>.json`
   in the hub, committed, one file per run.
3. **Whether Swift is included.** Its delta against the oracle is **zero by
   construction** — it minted it. Its value is cross-*machine*: the same Swift code on
   another Mac, another Xcode, Intel vs Apple Silicon. Worth capturing, for a different
   reason than Python's and web's.

## What the data will decide

The tolerance can be no tighter than the worst delta across every platform that must
pass. So the answer is only as good as the coverage, and the widest edition sets the
number — likely Kotlin, once it exists.

It will also force a question nobody has had to answer: **if an edition differs from
the oracle by, say, 0.05 dB, is that acceptable parity or a bug?** At 1 dB the question
never arises.
