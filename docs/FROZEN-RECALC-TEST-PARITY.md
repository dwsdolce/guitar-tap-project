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

### Stage 2 findings — the behaviour table (2026-09-19)

Built by reading all three files. Legend: **✓** covered · **—** absent · **≠** covers something else.

| # | behaviour | Swift | Python | web | verification style |
|---|---|---|---|---|---|
| B01 | frozen-spectrum path detects a known peak | `frozenSpectrum_detectsKnownPeak` | `PRA1` | `PR-A1` | **detection** |
| B02 | raising the threshold removes/deprojects the weak peak | `frozenSpectrum_raisedThreshold_removesWeakPeak` | `PRA2` | `PR-A2` | **detection** |
| B03 | loaded path and Peak Min (see conflict C1) | `loadedMeasurement_filtersAboveThresholdOnly` | `PRA3` | `PR-A3` ≠ | **injection** |
| B04 | loaded, all below threshold | `loadedMeasurement_allBelowThreshold_yieldsEmpty` | `PRA4` | `PR-A4` | **injection** |
| B05 | empty frozen magnitudes → no peaks, no crash | `emptyFrozenMagnitudes_yieldsNoPeaks` | `PRA5` | `PR-A5` | **injection** |
| B06 | loaded path uses saved peaks, does NOT re-analyse | `loadedPath_usesSavedPeaks_notFrozenSpectrum` | — | `PR2c` | **injection** |
| B07 | loaded peaks above threshold are kept | `loadedPeaks_aboveThreshold_areKept` | — | `PR2 (two peaks)` | **injection** |
| B08 | loaded peaks all below → display clears, classification kept | `loadedPeaks_allBelowThreshold_clears…` | — | — | **injection** |
| B09 | material loaded peaks are never filtered by Peak Min | `loadedPeaks_material_areNeverFilteredByPeakMin` | — | `material mode yields no guitar peaks` | **injection** |
| B10 | isLoadingMeasurement suppresses recalculation | `isLoadingMeasurement_suppressesRecalculation` | — | — | **injection** |
| B11 | recalculation runs once loading completes | `afterLoadingCompletes_recalculationRuns` | — | — | **injection** |
| B12 | live path tracks the live spectrum while incomplete | `liveTapPath_annotationOffset_remappedByFrequency` (partial) | — | `live-spectrum path` | **detection** |
| B13 | Peak Min sweep preserves identity/selection/override/offset | `peakMinSweep_preservesIdentity…` | `peak_min_sweep_preserves_identity…` | `a peak hidden then revealed…` | **injection** |
| B14 | deselect survives a Peak Min sweep | — | `deselect_survives_peak_min_sweep` | — | **injection** |
| B15 | Peak Min sweep leaves tapEntries untouched | `peakMinSweep_leavesTapEntriesUntouched` | `peak_min_sweep_leaves_tap_entries…` | `recalculatePeaks does NOT re-derive tapEntries` | **injection** |
| B16 | recalculation leaves tapEntries untouched | `recalculateFrozenPeaks_leavesTapEntriesUntouched` | `recalculate_frozen_peaks_leaves…` | `processMultipleTaps finds each per-tap set once` | **injection** |
| B17 | loaded per-tap entries found once from saved spectra | — | — | `loaded per-tap entries are found once` | **injection** |
| B18 | selection resolves over the durable set, not the projection | `selectedPeaks_resolveOverDurableSet…` | `selected_peaks_resolve_over_durable_set` | `the durable set holds a sub-Peak-Min peak` | **injection** |
| B19 | re-analyze preserves state of peaks hidden by Peak Min | `reanalyzePreservesStateOfPeaksHiddenByPeakMin` | `reanalyze_preserves_state…` | `recalc does not shrink the durable set` | **detection** (the Phase 4a twin) |
| B20 | annotation offset remapped to a close new peak | `loadedPath_annotationOffset_remappedByFrequency` | `PR3a` | `an offset SURVIVES a re-mint…` | **injection** |
| B21 | offset not remapped when no close peak / survives filtering | `loadedPath_offsetForFilteredOutPeak_survives` | `PR3b` | — | **injection** |
| B22 | mode override remapped to a close new peak | `loadedPath_modeOverride_remappedByFrequency` | `PR4` | `an override SURVIVES a re-mint…` | **injection** |
| B23 | override dropped/orphaned when no close peak | `loadedPath_overrideForFilteredOutPeak_survives` ≠ | `PR4b` | `an override is ORPHANED…` | **injection** |
| B24 | manual selection carried forward by frequency | `loadedPath_manualSelection_carriedForwardByFrequency` | `PR5a` | `a MANUAL selection … carries across` | **injection** |
| B25 | selection not carried when the peak moved far | — | `PR5b` | `a selected peak that vanishes …` | **injection** |
| B26 | unmodified selection re-runs auto over the durable set | `loadedPath_autoSelection_reRunsWhenNotModified` | — | `an UNMODIFIED selection re-runs auto` | **injection** |
| B27 | empty new peaks preserves selectedPeakIDs | `liveTapPath_emptyPeaks_preservesSelectedPeakIDs` | `PR6` | — | **injection** |
| B28 | remap with empty old overrides returns empty | — | `PR6b` | — | **injection** |
| B29 | loaded branch keeps stable ids — overrides not remapped away | — | — | `the loaded branch keeps stable ids` | **injection** |
| B30 | a captured MATERIAL peak's offset lives in the same store | — | — | `a captured MATERIAL peak gets a stored id` | **injection** |
| B31 | live frozen capture can be re-analyzed | `liveFrozenCapture_canReanalyze` | `PR8a` | `PR8a` | **injection** |
| B32 | loaded measurement can be re-analyzed | `loadedMeasurement_canReanalyze` | `PR8b` | `PR8b` | **injection** |
| B33 | re-analyze is not a one-shot | `reanalyze_isNotAOneShot_buttonStaysAvailable` | `PR8c` | `PR8c` | **injection** |
| B34 | material can never be re-analyzed | `material_canNeverReanalyze` | `PR8d` | `PR8d` | **injection** |
| B35 | nothing to re-analyze without a completed measurement | `incompleteOrNoFrozenSpectrum_cannotReanalyze` | `PR8e` | `PR8e` | **injection** |

**Covered by all three: 14 of 35.** The rest are gaps or conflicts.

### Conflicts investigated — all four dissolved under inspection of the CODE

Every apparent conflict was a test-naming artefact. **The three ports agree.** What diverged was
which surface each test asserts on, and what it was called. Recorded because the investigation is
the useful part: reading the tests alone made two of these look like real divergence.

**C1 — the loaded path. WITHDRAWN: test divergence only.** All three keep the loaded peaks whole
and apply Peak Min as a display projection:

| | durable set | projection |
|---|---|---|
| Swift | `allPeaks = savedPeaks` | `peaksAbovePeakMin` |
| Python | `self.all_peaks = list(self.loaded_measurement_peaks)` | emits `peaks_above_peak_min` |
| web | `peaks = p.loadedPeaks` — *"the authoritative FULL set; Peak Min projects them for display"* | same |

Swift's `loadedMeasurement_filtersAboveThresholdOnly` asserts the *projection* while being named for
filtering, which is what made it read as contradicting web's `PR-A3`. Both are correct. Swift's code
comment says why the model matters and it is not cosmetic: assigning a filtered view to the durable
set would shrink it as Peak Min rises, **and the save path would then write the shrunken set** —
silent data loss. Shared cases must name the surface they assert on, and should cover the durable
set as well as the projection, since that is the invariant with teeth.

**C2 — `PR2c` collision. Dissolves via C3** (below): once Python's `PR2*` leave this slug, the label
is free for B06, which is what web already means by it.

**C3 — five misfiled Python tests. Duplication, not divergence.** `PR1`/`PR1b` assert only
`spectrum_snapshot is not None` / `is None`. `PR2a`/`PR2b`/`PR2c` call the local `_detect_peaks`
helper wrapping `peak_detection` / `peak_interp`. None touch `recalculate_frozen_peaks_if_needed`.
`test/peaks` already covers this ground three ways — Python's own `test_fft_peak_detection.py` has
`test_single_tone_above_threshold_detected` (= `PR2a`) and `test_below_threshold_tone_not_detected`
(= `PR2b`).

**C4 — override survives vs orphaned. WITHDRAWN: two behaviours, not one.** Swift's test puts both
peaks in `loadedMeasurementPeaks` and raises Peak Min — the peak is *hidden but present*, so the
override survives. Web's orphan case is a *re-mint* where nothing lands within ±5 Hz — the peak is
*absent*, so the override is dropped. Different inputs, both correct. Becomes two gap rows, not a
conflict.

### Decisions — MADE 2026-09-19 (owner)

**D1 — the five misfiled Python tests: extend, then delete.** `PR2c`'s case (two tones of unequal
amplitude; raising the threshold drops the weaker) is covered by **no edition** — checked Swift
`PeakFindingTests`, Python `test_fft_peak_detection.py`, web `peaks.test.ts`. It is not a duplicate;
it is the only coverage of a real gap, filed under the wrong slug. So:

- **Add** that case to `test/peaks` in **all three** editions. There is no structural obstacle — same
  file, same helpers (`_flat_spectrum` / `_add_tone` / `peak_detection`).
- **Delete** `PR2a`, `PR2b` (duplicates of existing `test/peaks` coverage) and `PR2c` (superseded by
  the new case) from the frozen-recalc suite.
- **Delete** `PR1` / `PR1b`. Fixture invariants with no Swift or web counterpart — **no edition-only
  trivia.**

**D2 — the 21 gaps must be closed, not documented.** Each row in the table must end up covered by
all three editions. "Record why this edition does not need it" is not an outcome.

**D3 — one ID convention: `PR`, flat and zero-padded — `PR01`…`PR35`.** Keeps the lineage already
present in Python and web and documented in Swift's file header, while replacing the collided,
group-based `PR1`/`PR2a`/`PR-A1` numbering with one unique id per behaviour. Every edition uses the
same id for the same row of the table.

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