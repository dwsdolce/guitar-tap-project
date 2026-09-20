# Python↔Swift test-fixture divergence — frozen-peak-recalc

**Status:** ⏳ IN PROGRESS — re-measured 2026-09-19, still live. **Stage 1 of 3 complete**
(web `4722ba4`, hub `4afd0e5`). Found 2026-07-23 during the Phase 4a Python port.
**Scope:** Python vs Swift *test infrastructure*, not production code. Production DSP is equivalent.

## The finding

The `test/frozen-peak-recalc` `@parity` slug pairs Python's `test_frozen_peak_recalculation.py`
with Swift's `FrozenPeakRecalculationTests.swift`. The tests carry the same slug and cover the same
behaviours, but they **exercise those behaviours in different ways**:

| | Swift (`FrozenPeakRecalculationTests`) | Python (`test_frozen_peak_recalculation.py`) |
|---|---|---|
| Set up a frozen measurement | `freeze(sut, peaks:)` — **injects** a pre-computed `[ResonantPeak]`, bypassing detection | `_make_spectrum_with_peak` / `_add_tone` — builds a synthetic spectrum and runs **real `find_peaks`** |
| Real-spectrum fixture | `gaussianSpectrum` / `freezeOnRealSpectrum` — **added in Phase 4a**, used by exactly one test | `_make_spectrum_with_peak` — **pre-existing**, used across the PRA integration tests |

So Python's PRA tests (`test_PRA1…`, etc.) drive the detection pipeline where Swift's inject peaks.
They are twins in **name and slug**, not in **approach**.

## Why it matters

Two tests that assert the same behaviour in different ways do not prove equivalence — they can drift
independently, and a bug present on one platform can be invisible to the "equivalent" test on the
other. The paired-test discipline exists precisely to prevent that; a divergent pair quietly defeats
it.

## Why `--check` missed it

`gen_parity_map.py --check` verifies that a slug has a test on each platform (presence), **not** that
the paired tests are behaviourally equivalent. A slug can be green while its two tests diverge in
setup, fixture, or assertion shape. This is a known limitation, not a bug in the tooling — but it is
the reason the check a week before this finding passed while the divergence existed.

## How it happened

Divergence predates this work. Python built `_make_spectrum_with_peak` when its PRA
(`recalculate_frozen_peaks_if_needed`) integration tests were written — Python chose to exercise real
detection. Swift's frozen-recalc tests injected peaks via `freeze`. Swift only needed a real-spectrum
fixture for the one new Phase-4a test (`reanalyzePreservesStateOfPeaksHiddenByPeakMin`), where it
added `gaussianSpectrum`.

## Phase 4a decision (2026-07-23, user: "do (b)")

For the one new Phase-4a test, Python **mirrors** Swift's fixture: `_gaussian_spectrum` /
`_freeze_on_real_spectrum` were added to `test_frozen_peak_recalculation.py` as faithful snake-case
ports of `gaussianSpectrum` / `freezeOnRealSpectrum`, and
`test_reanalyze_preserves_state_of_peaks_hidden_by_peak_min` uses them — so at least this test is a
true twin. The broader PRA divergence is **logged here for reconciliation**, not fixed, to keep the
peak-lifecycle work moving.

## Re-measured 2026-09-19 — still live, and larger than first recorded

Re-measured before acting, per `process/CROSS-EDITION-INVESTIGATION.md` rule 4. Unlike issues #5
and #7 — whose archived findings had been silently fixed — this one stands, and is differently
shaped than the July entry above.

| | tests | setup style |
|---|---|---|
| Swift `FrozenPeakRecalculationTests.swift` | 29 | **injects** peaks — `freeze(sut, peaks:)` **22×** |
| Python `test_frozen_peak_recalculation.py` | 29 | builds spectra, runs **real detection** — `_make_spectrum_with_peak` 3×, `_add_tone` 7× |
| web `frozen-peak-recalc.test.ts` | 28 (was 37) | neither — none of those helpers exist |

The Phase 4a patch holds: Swift and Python each use `gaussianSpectrum` / `_gaussian_spectrum`
exactly twice, the one test made a true twin.

### The gaps run BOTH ways

- Python-only, no Swift twin: `PR1b`, `PR2a`, `PR2b`, `PR2c`, `PR6b`, and a **deselect** test.
- Swift-only, no Python twin: `loadedPeaks_material_areNeverFilteredByPeakMin`,
  `loadedPath_usesSavedPeaks_notFrozenSpectrum`, `loadedPath_autoSelection_reRunsWhenNotModified`,
  `afterLoadingCompletes_recalculationRuns`.
- Same behaviour, two verification styles: Python's `PRA1`/`PRA2` build a real spectrum and run
  detection; Swift's equivalents inject. **That is what a Kotlin porter would have to arbitrate.**

### Case IDs are not the answer

Adding a per-test case ID (Python already has `PRA1`; web half does; Swift does not) would let a
generator pair cases and flag coverage drift — but a `PRA1` in two editions could still assert
different things. It **moves** the presence-not-equivalence problem down a level rather than
closing it.

### The answer is the oracle pattern

What closed this class of problem before was not checking that copies agree — it was **deleting the
copies**. The oracle turned three hardcoded numeric sets into one shared contract. These fixtures
are equally declarable: a spectrum recipe, thresholds, peak sets, expected outcomes. Shared case
data plus a small runner per edition makes divergence **unrepresentable** rather than detectable,
and lets Kotlin port one runner instead of thirty tests.

**This supersedes the July "Reconciliation" plan**, which said *"Swift leads, align Python to it"*
and *"where Swift injects, Python should too"*. That is wrong for detection tests — injection
bypasses the behaviour under test — and it treats a three-way problem as two-way.

## The plan

### Stage 1 — separate what was never a twin ✅ DONE 2026-09-19

Nine web tests exercised the analyzer's **in-memory state-store mutators** (`setModeOverride`,
`clearResult`, `restoreOverrides`, `updateAnnotationOffset`, `resetAllAnnotationOffsets`,
`restoreOffsets`, `togglePeakSelection`, `resetToAutoSelection`) with no Swift or Python
counterpart. Moved to `test/peak-state-store.test.ts` under its own slug.

The seam ran *through* the RA/RB/RC sections, not around them: those blocks also contain genuine
twins of Swift PR3–PR7 (*"an override SURVIVES a re-mint that SHIFTS the id"* is
`loadedPath_modeOverride_remappedByFrequency`). Those stayed. Checked against `test/annotation-state`
and `test/peak-selection-persistence` — neither covers the mutator surface.

The new slug shows as a **web-only orphan** in `gen_parity_map.py --check`. Deliberately not
`@parity none`: the other editions should have these tests, and the orphan stands until they do.
37 tests before, 37 after (9 + 28).

### Stage 2 — settle the shared case list

**Goal:** one agreed list of behaviours every edition must cover, with the verification style fixed
per behaviour, so nothing is left to a porter's judgement.

1. Build the three-way behaviour table from the inventory above — every test in all three files
   mapped to a behaviour, with its current setup style. Record it **in this doc**, not in an issue.
2. Resolve each gap explicitly: fill it, or record why that edition legitimately does not need it.
   Both directions — the Swift-only and Python-only lists above.
3. Fix the verification style per behaviour by this rule:
   - **detection behaviour** (does a peak appear or vanish at this threshold) → **real spectrum**.
     Injection bypasses the thing under test. `gaussianSpectrum` is already proven portable.
   - **state behaviour downstream of detection** (offset remap, override carry, selection
     preservation) → **injection**. The peaks are inputs, not the subject; deterministic and ports
     trivially.
4. Agree one case-ID scheme across the three (Python's `PRA1` style is the existing candidate).

**Done when:** this doc contains the case table, every gap has a decision, and each case names its
verification style. No test code need change in stage 2.

### Stage 3 — move the case list into shared data

**Goal:** make divergence unrepresentable, and make the fourth edition cheap.

1. Design the case schema. Setup vocabulary from the measured state surface: `frozenPeaks` or
   `spectrum` (bump recipe), `loadedPeaks`, `peakMin`, `measurementType`, `isLoading`, `offsets`,
   `overrides`, `selection`, `tapEntries`. Expectation vocabulary: displayed peaks, durable set,
   selection, offsets/overrides surviving or orphaned, `canReanalyze`.
2. Put the cases in the hub beside the oracle; vendor them the way `parity-oracle.json` is vendored.
3. Write one runner per edition that iterates the cases. Tests that genuinely do not fit the schema
   stay hand-written and are tagged honestly.
4. Retire `_make_spectrum_with_peak` / `freeze` duplicates where the runner replaces them.

**Done when:** each edition's frozen-recalc suite is a runner over shared data, adding a case is one
edit in one file, and a missing case cannot be silently absent.

### Stage 4 — sweep the other slugs

`--check` verifies presence, never equivalence, and it makes that claim for **every** slug in
`PARITY-MAP.md`. `test/frozen-peak-recalc` is simply the first anyone read closely. Sweep the rest
for the same false-twin shape, and consider whether the generator can flag paired tests whose
fixture style diverges (a heuristic on which helper each test calls would have caught this one:
22 Swift `freeze` calls against 3 Python `_make_spectrum_with_peak` calls on the same slug).

## Related
- STATUS item 2 (architectural-parity restructure) is **web-vs-native view layer** — a different
  concern; do not fold this into it.
- `PEAK-LIFECYCLE-PLAN-PYTHON.md` Phase 4a — where the mirrored fixture landed.