# Python↔Swift test-fixture divergence — frozen-peak-recalc

**Status:** ⏳ IN PROGRESS. **Stage 1 complete** (web `4722ba4`, hub `4afd0e5`).
**Stage 2 ✅ COMPLETE 2026-09-20. Stage 3 is next** — see RESUME HERE below. (Working record for issue #8; not an
authority and not tooling input — see "What this document is".)
Found 2026-07-23 during the Phase 4a Python port; re-measured 2026-09-19.

**Scope changed 2026-09-19.** This began as "Python vs Swift *test infrastructure*, not production
code". That is no longer true: the investigation found two architectural defects and a duplicate-peak
data bug in the web's shipping save path. Production code in `GuitarTapWeb` has changed and
**has been run-reviewed by the owner (2026-09-20) — all four checks pass on real measurements.**
See "Owner run-review of the web production changes".

---

## RESUME HERE — updated 2026-09-20

**Committed and pushed 2026-09-20**, after the owner run-review passed:

| repo | commit |
|---|---|
| `GuitarTapWeb` | `6f1975d` — analyzer owns Peak Min and the load; duplicate-peak save fixed |
| `GuitarTap` | `5adc0bf` — PR14, PR17, PR22, PR25, PR27, PR30, PR32 |
| `guitar_tap` | `b5f0cc6` — PR08, PR09, PR12, PR17, PR28, PR31, PR32 |
| `guitar-tap-project` | this doc + `process/CROSS-EDITION-INVESTIGATION.md` rule 6 |

Suites all green at the point of writing: **Swift 506 / 1 skipped · Python 617 / 1 skipped ·
web 426 / 2 skipped.** Every skip is environment-gated (`oracle-sync` needs `ORACLE_SRC` while the
hub is private; `mint-baseline` is flag-gated).

### ✅ STAGE 2 COMPLETE — 2026-09-20

**Done when:** this doc contains the case table, every gap has a decision, and each case names its
verification style. All three hold.

- **The behaviour table is 37 of 37 covered in all three editions.** No row carries an `n/a`.
- **D3 executed:** every test in all three editions now carries its table id, `PR01`–`PR37`, the
  same id for the same behaviour. Mapping from the old `B`-ids in "Renamed 2026-09-20".
- Two web architecture defects and one live data bug were found and fixed on the way, all
  owner run-reviewed.

**Next is Stage 3** — move the case list into shared data, vendored like `parity-oracle.json`, with
one runner per edition. That is the step that makes divergence unrepresentable rather than
detectable, and it is what a fourth edition would port against.

Open, independent of Stage 2:

1. **The Python flake** — `test_file_playback_regression.py` failed once in a full run (`Avg Top
   freq`, got 201.56 Hz) and has passed in isolation (8/8), paired with the frozen-recalc file
   (42/42), and in every run since. First step is to establish whether it predates this week, by
   running it on a clean checkout of `main`.

**Done 2026-09-20:** PR10 / PR11 for web — the `n/a` was withdrawn, not re-justified. The web load was
consolidated into one analyzer method under `isLoadingMeasurement` (see "The web load was five
view-orchestrated calls"), and `loadedPeaks` moved onto the analyzer. Three tests added, three of
four mutations killed; the fourth is un-killable in Python too, and that limit is recorded in ¹.

Also PR31 for Python (`test_B29_loaded_branch_keeps_stable_ids_so_overrides_are_not_remapped_away`),
mutation-verified against three breaks of the remap — ignoring the tolerance, dropping the map, and
widening the tolerance so 200 Hz and 400 Hz collide.

Also **PR22 and PR25 for Swift**. Scope was corrected on the owner's call: footnote ³ was wrong,
Swift was missing BOTH orphan halves, so the override row was split the way the offset row had
been, and two tests were written
(`remint_offsetWithNoNearbyPeak_isDropped`, `remint_overrideWithNoNearbyPeak_isOrphaned`). Both
mutation-verified; the stale-id leak they catch is caught by no other Swift test. Swift 504 → 506.

**D3, 2026-09-20.** 35 Python tests, 37 Swift, 38 web titles renamed to carry their table id. Old
ids swept from all three files and from this document; the `B`→`PR` mapping is recorded so the
commits already pushed under the old ids stay traceable.

One near-miss worth recording: `GuitarTapWeb/test/button-enablement.test.ts` has its OWN unrelated
`B1`–`B10` truth table. A repo-wide id sweep would have silently corrupted it. The rename was scoped
to the three frozen-recalc files by name; do the same if these ids are ever renumbered again.

### Owner run-review of the web production changes

Two web changes shipped into the working tree: the Peak-Min projection moving onto the analyzer, and
the load consolidating into one atomic `loadMeasurement`. **Run-review COMPLETE — owner, 2026-09-20.
All four checks pass on real measurements.**

| change | status | evidence |
|---|---|---|
| Peak Min projection on the analyzer (list, chart dots, live ratio) | ✅ **VERIFIED** | owner's manual check, plus the brace file below |
| material peak below Peak Min still shows (the guitar-only rule) | ✅ **VERIFIED** | `brace-test-for-save-1789927895.guitartap` — fL at **−61.27 dB** persisted intact with `peakMinThreshold: −41`, the 2026-07-21 regression shape |
| duplicate-peak save fixed | ✅ **VERIFIED** | `test3-1789928992.guitartap` — a real Generic Guitar capture at Peak Min −52: **195 peaks, 195 distinct ids, 0 duplicate frequencies**, 173 of them below Peak Min. On the previous build those 173 would each have been appended a second time: 368 peaks, 173 duplicated |
| PR10/PR11 load atomicity (overrides / offsets / selection survive a load) | ✅ **VERIFIED** | owner, 2026-09-20: renamed a peak's mode, dragged an annotation label, hand-edited the selection, saved and reloaded — all three survived. That is exactly the state a torn load would have wiped |

Integrity checks on `test3` also passed: all 6 `selectedPeakIDs` resolve to saved peaks, 182 peaks
carry mode labels, and magnitudes run down to −90.2 dB — consistent with detection at the −100 dB
floor rather than at Peak Min, which is what the full-set save is for.

**A non-finding worth recording, so nobody re-chases it.** The saved peaks are not in ascending
frequency order. That is correct: all three editions sort the detected set by DESCENDING MAGNITUDE
(Swift `sorted(by: { $0.magnitude > $1.magnitude })`, Python "sorted by magnitude descending", web
`.sort((a, b) => b.magnitude - a.magnitude)`). The ordering is consistent across editions and is not
a parity defect.

### What this document is

**A working record for issue #8, not an authority and not tooling input.** It is archived to
`docs/completed/` when #8 closes and does not survive the project. Nothing should be built that
reads it as a source of truth — the table has already been wrong twice in ways that hid real work
(the un-split override row's `≠` mark, PR31's double dash), and a checker built on it would just
enshrine that.

The durable artifact is **Stage 3**: the case list moves into shared data, vendored the way
`parity-oracle.json` is. That is what a generator can legitimately check, and what a fourth edition
ports against. Until then the authority is the CODE — check the table against the tests, never the
other way round.

**One list of open work, and it is RESUME HERE.** There was a second ("Not yet resolved", mid-
document); the two had to be hand-synced, drifted twice in two days, and the drift is how PR22 came
to be listed as open after it was closed and how PR31's Python half stayed invisible. The second list
is deleted. Do not add another — if something is open, it goes in RESUME HERE; everything below that
section is a dated record of what was already done.

---

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

Built by reading all three files.

Legend: **✓** covered · **—** GAP, the behaviour exists here but is untested, must be closed ·
**n/a** the MECHANISM does not exist in this edition, documented and no test written ·
**≠** covers something else.

**A gap and an n/a are not the same thing.** A gap is a behaviour the edition has and does not
test — it gets a test. An n/a is a behaviour the edition cannot have, because its architecture
has no such state to reach. An n/a must carry its reason **here in this table**, and a matching
note in that edition's test file so an auditor finds it from either direction. "Not needed" with
no reason is neither, and is not an acceptable outcome.

| # | behaviour | Swift | Python | web | verification style |
|---|---|---|---|---|---|
| PR01 | frozen-spectrum path detects a known peak | `frozenSpectrum_detectsKnownPeak` | `PRA1` | `PR-A1` | **detection** |
| PR02 | raising the threshold removes/deprojects the weak peak | `frozenSpectrum_raisedThreshold_removesWeakPeak` | `PRA2` | `PR-A2` | **detection** |
| PR03 | Peak Min projects the loaded set; never shrinks the durable set | ✓ `loadedMeasurement_peakMinProjects_andNeverShrinks…` | ✓ `PRA3_loaded_path_peak_min_projects…` | ✓ `PR-A3` | **injection** |
| PR04 | loaded, all below Peak Min → empty PROJECTION | `loadedMeasurement_allBelowPeakMin_yieldsEmptyProjection` | `PRA4` | `PR-A4` | **injection** |
| PR05 | empty frozen magnitudes → no peaks, no crash | `emptyFrozenMagnitudes_yieldsNoPeaks` | `PRA5` | `PR-A5` | **injection** |
| PR06 | loaded path uses saved peaks, does NOT re-analyse | `loadedPath_usesSavedPeaks_notFrozenSpectrum` | ✓ `test_loaded_path_uses_saved_peaks_not_the_frozen_spectrum` | `PR2c` | **injection** |
| PR07 | loaded peaks above threshold are kept | `loadedPeaks_aboveThreshold_areKept` | ✓ `test_loaded_peaks_above_threshold_are_kept` | `PR2 (two peaks)` | **injection** |
| PR08 | loaded peaks all below → display clears, classification kept | `loadedPeaks_allBelowThreshold_clears…` | ✓ `B08_loaded_all_below_peak_min…` | ✓ `PR08` ² | **injection** |
| PR09 | material loaded peaks are never filtered by Peak Min | `loadedPeaks_material_areNeverFilteredByPeakMin` | ✓ `B09_loaded_material_peaks…` | ✓ `PR09` ² | **injection** |
| PR10 | isLoadingMeasurement suppresses recalculation | `isLoadingMeasurement_suppressesRecalculation` | ✓ `test_loading_measurement_suppresses_recalculation` | ✓ `PR10` ¹ | **injection** |
| PR11 | recalculation runs once loading completes | `afterLoadingCompletes_recalculationRuns` | ✓ `test_recalculation_runs_once_loading_completes` | ✓ `PR11` ¹ | **injection** |
| PR12 | live path tracks the live spectrum while incomplete, and STOPS once complete | `liveTapPath_annotationOffset_remappedByFrequency` (partial) | ✓ `B12_live_peaks_track_the_spectrum…` | `live-spectrum path` | **detection** |
| PR13 | Peak Min sweep preserves identity/selection/override/offset | `peakMinSweep_preservesIdentity…` | `peak_min_sweep_preserves_identity…` | ✓ `PR13/PR21` ² (was identity only) | **injection** |
| PR14 | deselect survives a Peak Min sweep | ✓ `peakMinSweep_doesNotResurrectADeselectedPeak` | `deselect_survives_peak_min_sweep` | ✓ `PR14` ² | **injection** |
| PR15 | Peak Min sweep leaves tapEntries untouched | `peakMinSweep_leavesTapEntriesUntouched` | `peak_min_sweep_leaves_tap_entries…` | `recalculatePeaks does NOT re-derive tapEntries` | **injection** |
| PR16 | recalculation leaves tapEntries untouched | `recalculateFrozenPeaks_leavesTapEntriesUntouched` | `recalculate_frozen_peaks_leaves…` | `processMultipleTaps finds each per-tap set once` | **injection** |
| PR17 | loading restores the saved per-tap peaks; never re-detects | ✓ `loadMeasurement_restoresSavedTapEntryPeaks…` | ✓ `B17_loading_restores_saved_per_tap_peaks…` | `loaded per-tap entries are found once` | **injection** |
| PR18 | selection resolves over the durable set, not the projection | `selectedPeaks_resolveOverDurableSet…` | `selected_peaks_resolve_over_durable_set` | `the durable set holds a sub-Peak-Min peak` | **injection** |
| PR19 | re-analyze preserves state of peaks hidden by Peak Min | `reanalyzePreservesStateOfPeaksHiddenByPeakMin` | `reanalyze_preserves_state…` | `recalc does not shrink the durable set` | **detection** (the Phase 4a twin) |
| PR20 | annotation offset remapped to a close new peak | `loadedPath_annotationOffset_remappedByFrequency` | `PR3a` | `an offset SURVIVES a re-mint…` | **injection** |
| PR21 | an offset for a peak HIDDEN by Peak Min survives | `loadedPath_offsetForFilteredOutPeak_survives` | (clause of PR13) | ✓ `PR13/PR21` ² | **injection** |
| PR22 | an offset is DROPPED when no re-minted peak is near | ✓ `remint_offsetWithNoNearbyPeak_isDropped` | `B21_offset_is_dropped_when_no_new_peak_is_near` | ✓ `PR22` | **injection** |
| PR23 | mode override remapped to a close new peak | `loadedPath_modeOverride_remappedByFrequency` | `PR4` | `an override SURVIVES a re-mint…` | **injection** |
| PR24 | an override for a peak HIDDEN by Peak Min survives | `loadedPath_overrideForFilteredOutPeak_survives` | (clause of PR13) | ✓ `PR13/PR21` ² | **injection** |
| PR25 | an override is ORPHANED when no re-minted peak is near | ✓ `remint_overrideWithNoNearbyPeak_isOrphaned` | `B23_override_is_orphaned_when_no_new_peak_is_near` | `an override is ORPHANED…` | **injection** |
| PR26 | manual selection carried forward by frequency | `loadedPath_manualSelection_carriedForwardByFrequency` | `PR5a` | `a MANUAL selection … carries across` | **injection** |
| PR27 | selection not carried when the peak moved far | ✓ `selection_isNotCarried_whenThePeakMovedFar` | `B25_selection_is_not_carried…` | `a selected peak that vanishes …` | **injection** |
| PR28 | unmodified selection re-runs auto over the durable set | `loadedPath_autoSelection_reRunsWhenNotModified` | ✓ `B26_unmodified_selection_re_runs_auto…` | `an UNMODIFIED selection re-runs auto` | **injection** |
| PR29 | empty new peaks preserves selectedPeakIDs | `liveTapPath_emptyPeaks_preservesSelectedPeakIDs` | `B27_empty_new_peaks_preserve…` | ✓ `PR29` ⁴ | **injection** |
| PR30 | remap with empty old overrides returns empty | ✓ `remapWithNoPriorOverrides_yieldsNoOverrides` | `B28_remap_with_no_prior_overrides…` | ✓ `PR30` | **injection** |
| PR31 | loaded branch keeps stable ids — overrides not remapped away | ✓ `loadedPath_stableIDs_leaveRestoredOverridesInPlace` | ✓ `B29_loaded_branch_keeps_stable_ids…` ⁵ | `the loaded branch keeps stable ids` | **injection** |
| PR32 | a captured MATERIAL peak's offset lives in the same store | ✓ `capturedMaterialPeak_isSavedAndOwns…` | ✓ `B30_a_captured_material_peak…` | `a captured MATERIAL peak gets a stored id` | **injection** |
| PR33 | live frozen capture can be re-analyzed | `liveFrozenCapture_canReanalyze` | `PR8a` | `PR8a` | **injection** |
| PR34 | loaded measurement can be re-analyzed | `loadedMeasurement_canReanalyze` | `PR8b` | `PR8b` | **injection** |
| PR35 | re-analyze is not a one-shot | `reanalyze_isNotAOneShot_buttonStaysAvailable` | `PR8c` | `PR8c` | **injection** |
| PR36 | material can never be re-analyzed | `material_canNeverReanalyze` | `PR8d` | `PR8d` | **injection** |
| PR37 | nothing to re-analyze without a completed measurement | `incompleteOrNoFrozenSpectrum_cannotReanalyze` | `PR8e` | `PR8e` | **injection** |

**Covered by all three: 37 of 37.** The table was 18 of 35 when first built on 2026-09-19. Every
gap has since been closed, and two rows were split into their hidden-vs-absent halves —
PR21/PR22 (offset) and PR24/PR25 (override). The two not covered three ways are PR10 and PR11 (web — see
¹, SUSPECT). PR12, PR17, PR21 and PR24 are covered three ways, but one edition's coverage is a
clause of a neighbouring test, noted inline.

**² Expressible only after the web architecture fix** — see "The web analyzer did not own its
display state" below. PR08, PR09, PR13's state clauses, PR14 and PR21 were all recorded as web absences
on the grounds that Peak Min was not analyzer state. That was true, and it was the defect.

**³ PR22 / PR25 — Swift gaps, CLOSED 2026-09-20.** *(The original wording of this footnote was
wrong and is corrected here: it claimed Swift covered the override orphan half. It did not.)*

Splitting the offset row (PR21/PR22) exposed that Swift had no test for per-peak state being
DROPPED on a re-mint, and
checking the claim showed the same hole on the override side. Swift's nine offset/override tests
were all successful remaps, stable-id cases, or survives-filtering cases — not one orphan case.
`loadedPath_offsetForFilteredOutPeak_survives` and `loadedPath_overrideForFilteredOutPeak_survives`
are PR21 and PR24: the peak is HIDDEN but present. The orphan case is a different input — the peak
is ABSENT — which is exactly the distinction C4 drew and said should become two rows.

So the override row was split the same way (PR24/PR25), and both Swift halves were written:
`remint_offsetWithNoNearbyPeak_isDropped` and `remint_overrideWithNoNearbyPeak_isOrphaned`.

Both assert the map is EMPTY of the carried value rather than merely absent from the new id. That
matters: the mutation "keep the old map instead of rebuilding it" — a leak under the stale id — is
caught by these two tests and by **no other test in the Swift suite**. A negative-only assertion
would have passed it.

**⁴ PR29 was a production divergence, not a test gap.** Swift (`guard !peaks.isEmpty`) and Python
(`if not peaks: … return`) both return before the carry-forward, so an empty detection leaves the
selection untouched. Web had no such guard: `applyFrozenPeakState` ran with an empty new set and
cleared `selectedPeakIds`. The guard was added to the web analyzer; the test came after.

**⁵ PR31 — a Python gap this table hid. CLOSED 2026-09-20.** Swift's half was written on
2026-09-19 (`loadedPath_stableIDs_leaveRestoredOverridesInPlace`, whose own comment records "web
covered it, Swift and Python did not") and the row was never updated, so it read `—` for BOTH Swift
and Python. A row showing two dashes looks like a known, tracked gap; it was actually one closed
half and one genuinely open one, and the open half dropped out of every subsequent gap list.

Found 2026-09-20 by counting the table's own cells with a script instead of trusting the prose
summary above it, after a stale entry in a second open-items list showed the same drift. That second
list has since been deleted — see "What this document is". **Check the table against the code, not
against the summary.**

Python's half is now `test_B29_loaded_branch_keeps_stable_ids_so_overrides_are_not_remapped_away`,
mutation-verified against three breaks of the remap: ignoring the ±5 Hz tolerance, dropping the
override map on the loaded branch, and widening the tolerance to 500 Hz so the 200 Hz and 400 Hz
peaks collide. It catches all three.

**¹ PR10 / PR11 — the web n/a is WITHDRAWN. Closed 2026-09-20 by making the web load atomic.**

The original reason was: *Swift and Python trigger recalculation from property observers that can
fire part-way through a load, so both need a guard. Web calls `recalculatePeaks` from a single
`useLayoutEffect` keyed on `loadedPeaks`, so there is no window to guard and no state a test could
construct.*

Every sentence of that was true, and the conclusion was still wrong. Tracing the load found the
protection was real but came from the wrong place:

- `onLoadMeasurement` was ONE synchronous handler, and `setLoadedPeaks(...)` came before
  `analyzer.loadMeasurement(...)`, so React 18 batched the state updates and the
  `useSyncExternalStore` notifications and the effect first ran after the handler returned.
- So the window was closed by **React's batching plus the statement order inside a 100-line view
  handler** — not by the model. Nothing tested that order. Reordering two lines, adding an `await`
  between them, or a `flushSync` anywhere would have opened it silently.
- The failure it prevents is not cosmetic: a recalc against a torn load takes the live branch,
  re-detects on the loaded spectrum, mints fresh ids, and `applyFrozenPeakState` drops the
  overrides, offsets and selection being restored — the exact state the file exists to carry.

**Porting the flag naively would have been false parity.** Swift's and Python's `loadMeasurement` is
one method doing the whole restore, so `isLoadingMeasurement = true; defer { false }` spans it. The
web's `analyzer.loadMeasurement` only did the spectrum, per-tap entries and capture teardown;
`restoreOverrides`, `restoreOffsets` and `restoreSelection` were three further calls from App, and
`loadedPeaks` never reached the analyzer at all. A flag inside `loadMeasurement` would have been
false again before the risky window even opened — it would have looked like parity and covered
nothing.

So the fix was the same shape as the Peak Min one: **stop the view doing the model's job.**
`loadedPeaks` moved onto the analyzer (Swift `loadedMeasurementPeaks`), `loadMeasurement` now takes
the whole restore payload and applies it under `isLoadingMeasurement`, and `recalculatePeaks` guards
on the flag and reads `this.loadedPeaks`. The peaks and the spectrum can no longer be observed out
of step, because they are assigned in the same method.

**A limit worth recording, shared by all three editions.** Mutating `loadMeasurement` so it never
sets the flag kills no test — in Python either, verified by running the same mutation there. No unit
test observes the flag *during* a load, because nothing can re-enter the analyzer synchronously from
one. What the tests do pin is that the guard works when set (PR10/PR11) and that the restore is atomic
(the third web test). That is the same shape Swift and Python have; it is not a web weakness.

### Renamed 2026-09-20 — D3, and the bridge to the old ids

The behaviours were `B01`–`B35` (with `B21a`/`B21b` and `B23a`/`B23b`) until 2026-09-20. They are now
`PR01`–`PR37`, flat and zero-padded, one id per table row, the same id in all three editions.

**Why flat rather than keeping the `a`/`b` pairs.** The pairs were cheaper to rename and recorded
that two rows had been split. But a suffix invites the next one (`PR21c`), it needs special-casing
in every edition's runner once Stage 3 turns the case list into data, and the record of *why* those
rows split belongs in the prose above — C4, footnote ³ — not in the identifier. Flat is one rule to
learn and a plain integer key to sort on.

**This table is the bridge.** Commits pushed before the rename cite the old ids —
`6f1975d`, `5adc0bf`, `b5f0cc6` and everything earlier under issue #8 — as do the GitHub issue
comments. Do not delete it.

| `B01` → `PR01` | `B02` → `PR02` | `B03` → `PR03` |
| `B04` → `PR04` | `B05` → `PR05` | `B06` → `PR06` |
| `B07` → `PR07` | `B08` → `PR08` | `B09` → `PR09` |
| `B10` → `PR10` | `B11` → `PR11` | `B12` → `PR12` |
| `B13` → `PR13` | `B14` → `PR14` | `B15` → `PR15` |
| `B16` → `PR16` | `B17` → `PR17` | `B18` → `PR18` |
| `B19` → `PR19` | `B20` → `PR20` | `B21a` → `PR21` |
| `B21b` → `PR22` | `B22` → `PR23` | `B23a` → `PR24` |
| `B23b` → `PR25` | `B24` → `PR26` | `B25` → `PR27` |
| `B26` → `PR28` | `B27` → `PR29` | `B28` → `PR30` |
| `B29` → `PR31` | `B30` → `PR32` | `B31` → `PR33` |
| `B32` → `PR34` | `B33` → `PR35` | `B34` → `PR36` |
| `B35` → `PR37` |  |  |

The two splits are where the numbering shifts: `B21a`/`B21b` became `PR21`/`PR22`, `B23a`/`B23b`
became `PR24`/`PR25`, and every row after `B21` moved up by one or two.

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

Swift's `loadedMeasurement_filtersAboveThresholdOnly` asserted the *projection* while being named
for filtering, which is what made it read as contradicting web's `PR-A3`. Both were correct. Swift's
code comment says why the model matters and it is not cosmetic: assigning a filtered view to the
durable set would shrink it as Peak Min rises, **and the save path would then write the shrunken
set** — silent data loss.

**Tidied 2026-09-19 (PR03 closed).** All three PR03 tests now assert BOTH surfaces and are named for
what they assert: Swift `loadedMeasurement_peakMinProjects_andNeverShrinksTheDurableSet`, Python
`test_PRA3_loaded_path_peak_min_projects_and_never_shrinks_the_durable_set`, web `PR-A3: Peak Min
projects the loaded set for display and never shrinks the durable set`. Swift's PR04 was renamed
`…_allBelowPeakMin_yieldsEmptyProjection` for the same reason. The durable half is the assertion
with teeth — and the web's save path shipped exactly that defect in a different form, see below.

**C2 — `PR2c` collision. Dissolves via C3** (below): once Python's `PR2*` leave this slug, the label
is free for PR06, which is what web already means by it.

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

**Acted on 2026-09-20 — and it had been left undone for a week.** C4 said "two gap rows"; the table
kept a single override row with a `≠` mark, and footnote ³ then asserted Swift had coverage it did
not have. It is now split into PR24/PR25, matching the offset row, and both Swift halves are
written. The lesson is not about that row: **a conclusion recorded in this document is not a change
to it.** When an investigation
says a row should split, split the row in the same pass, or the note becomes another stale
authoritative record — the exact failure this issue exists to remove.

### Audit 2026-09-19 — 8 of Python's 28 tests never reach production code

Found while filling PR31. Python's remapping tests do not exercise
`recalculate_frozen_peaks_if_needed` or `_apply_frozen_peak_state` **at all**:

| test | what it actually exercises |
|---|---|
| `PR3a`, `PR3b`, `PR4`, `PR4b`, `PR6`, `PR6b` | `_remap_by_freq` — a **test-local reimplementation** of the carry-forward logic, whose own docstring calls it *"the Python equivalent of the Swift carry-forward logic"* |
| `PR5a`, `PR5b` | **nothing** — `assert abs(201.0 - 200.0) <= 5.0`, arithmetic on two literals. Cannot fail. |

This is a level worse than a false twin. The misfiled detection tests at least called production
`peak_detection`; these call a second implementation living in the test file, or nothing. Production
remapping could be broken in every one of these cases and all eight would still pass.

It also explains an inventory signal that was visible and not chased: Python's `PR3`–`PR6` were
tagged `inject` only — no `loadedPeaks`, no `peakMin`, no analyzer state — because they never needed
an analyzer.

**Consequence for the table: the ✓ marks for Python on PR20–PR30 were false** and are corrected below.
Python's real coverage of remapping is zero. The eight are replaced by tests that drive the
production path, not deleted — the behaviours are real and Swift/web cover them.

**Audit rule going forward:** a test under a `@parity` slug must reach production code. A helper that
reimplements the behaviour under test is not a fixture, it is a second implementation, and a test
against it measures nothing. Worth sweeping the other slugs for the same shape (stage 4).

### The web analyzer did not own its display state — FIXED 2026-09-19

Found while trying to write the web halves of PR08, PR09 and PR14. The honest answer looked like three
more `n/a` rows; the owner's call was **"a true application code architectural problem. Fix the
architecture — do not just hide it."** That was right, and the `n/a`s would have hidden a shipping
data bug.

| | durable set | Peak Min | projection | computed by |
|---|---|---|---|---|
| Swift | `allPeaks` | `peakMinThreshold` (analyzer, `didSet`) | `peaksAbovePeakMin` | `refreshDisplayedPeaks()` |
| Python | `all_peaks` | `peak_min_threshold` (analyzer, setter) | `peaks_above_peak_min` | `refresh_displayed_peaks()` |
| web, before | `peaks` | the **settings store** | **none** | a `useMemo` in `App.tsx` |

"Peak Min is guitar-only; material is never filtered" is a rule about the MEASUREMENT. In the web it
lived in the view — and, because nothing else could reach it, in two further copies: a `project()`
helper in `frozen-peak-recalc.test.ts`, and an open-coded filter in `measurement/fromLive.ts`.

**The bug it was hiding: every freshly-captured web measurement saved duplicate peaks.**

`buildGuitarMeasurement` re-ran `findPeaks` and APPENDED every peak below the current Peak Min, on
the assumption that `a.peaks` held only the peaks above it. That was true before Phase 1. Once the
analyzer's durable set became the full −100 dB set, the append wrote a second copy of every
sub-Peak-Min peak under a second UUID. Measured on the real `dws-2024-umik-1-swift-mac` capture at
Peak Min −60: **111 peaks in, 217 saved out, 106 frequencies duplicated.**

Swift deleted this same re-detect-and-append dance when `guitarFullSavePeaks()` became `{ allPeaks }`
— its comment says so. The web kept it.

**Why every signal missed it.** `peak-fullset-save.test.ts` passed `peaks: displayed` — a set
filtered at Peak Min −60, the pre-Phase-1 contract — while `App.tsx` passes `snapshot.peaks`. The
test validated the append against inputs the application never sends. Same shape as the eight purged
Python tests: green, paired, and measuring something the app does not do.

**The fix.**

| file | change |
|---|---|
| `src/state/tapToneAnalyzer.ts` | analyzer owns `peakMinThreshold`, `peaksAbovePeakMin`, `refreshDisplayedPeaks()`, `setPeakMinThreshold()`; empty-peaks guard added (PR29) |
| `src/App.tsx` | projection `useMemo` deleted, reads the snapshot; Peak Min pushed in on its OWN effect — never a `recalculatePeaks` dep, or a slider tick re-mints ids again |
| `src/measurement/fromLive.ts` | re-detect-and-append deleted; `isLoadedMeasurement` removed as meaningless once both branches save the same set |
| `test/frozen-peak-recalc.test.ts` | `project()` deleted; tests go through `setPeakMinThreshold` |
| `test/peak-fullset-save.test.ts` | passes the durable set; asserts exact count and distinct UUIDs |

**Rule this earns.** An `n/a` justified by "that edition's view drives this, so there is no state to
construct" is not a difference, it is a finding. The view driving the model is the thing to fix. See
¹ — PR10/PR11 rest on exactly that argument and are now marked suspect.

### The web load was five view-orchestrated calls — FIXED 2026-09-20

The second instance of the same architectural shape, found while re-examining the PR10/PR11 `n/a`
(footnote ¹). The Peak Min fix moved a display rule out of the view; this moved the *load* out of it.

| | "load a measurement" was |
|---|---|
| Swift | one method, `loadMeasurement`, guarded by `isLoadingMeasurement` |
| Python | one method, `load_measurement`, guarded by `is_loading_measurement` |
| web, before | `setLoadedPeaks()` (React state) + `analyzer.loadMeasurement()` + `restoreOverrides()` + `restoreOffsets()` + `restoreSelection()`, sequenced by `App.tsx` |

The peaks lived in React state while the spectrum went straight onto the analyzer, so the two were
in step only because React 18 batched the handler. Correctness of a loaded measurement's per-peak
state rested on statement order inside a 100-line view handler, untested, and a reorder or an
`await` would have opened the window silently.

**What the window costs.** A recalc against a torn load takes the live branch, re-detects on the
loaded spectrum, mints fresh ids, and `applyFrozenPeakState` drops the overrides, dragged offsets
and selection keyed to the saved ids — the state the file exists to carry.

**The fix.** `loadedPeaks` moved onto the analyzer (Swift `loadedMeasurementPeaks`).
`loadMeasurement` now takes the whole restore payload — spectrum, per-tap entries, peaks, overrides,
offsets, selection — applies it under `isLoadingMeasurement`, and notifies once.
`recalculatePeaks` guards on the flag and reads `this.loadedPeaks` rather than a caller argument, so
the branch cannot be entered with the spectrum set but the peaks missing. `restoreOverrides` /
`restoreOffsets` / `restoreSelection` stay as public methods — they are a tested surface used by
`peak-state-store` and `annotation-state` — and `loadMeasurement` calls the same assignments.

The material load path was checked and left alone: it has no frozen guitar spectrum, and
`recalculatePeaks` returns `peaks = []` with `reminted = false` for material, so it cannot clobber.

**Both web architecture fixes started as an `n/a` in this table.** PR08/PR09/PR14 and PR10/PR11 were all
recorded as "the web's architecture provides no such state". In both cases that was an accurate
description of a defect, written down as though it were a design. The pattern is worth naming: when
an edition cannot express a behaviour its siblings test, ask whether the architecture is the reason
or the finding.

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

**D2 — gaps must be closed; absences must be documented.** Clarified 2026-09-19 after PR10/PR11.
A **gap** is a behaviour the edition HAS and does not test — it gets a test, and "record why this
edition does not need it" is not an acceptable outcome for one. An **n/a** is a behaviour the
edition CANNOT have, because its architecture provides no such state; it gets no test, and instead
gets its reason recorded in the table above **and** a note in that edition's test file, so an audit
finds it from either direction. The distinction must be explicit in the table — never a bare dash.

**D3 — one ID convention: `PR`, flat and zero-padded — one id per table row.** Keeps the lineage already
present in Python and web and documented in Swift's file header, while replacing the collided,
group-based `PR1`/`PR2a`/`PR-A1` numbering with one unique id per behaviour. Every edition uses the
same id for the same row of the table.

**Do not write the upper bound into this decision.** It said `PR35`, then the table grew to 36 rows
(the offset row split) and then 37 (the override row split), and the stale number sat here being
read as settled. The range
is "however many rows the table has when the rename happens" — count it then.

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
---

## D2 progress log — 2026-09-19 (UNCOMMITTED at time of writing)

**Closed:** PR06, PR07, PR10, PR11 (Python), PR31 (Swift). **Classified n/a:** PR10, PR11 (web — mechanism
absent, reason in the table and in `test/frozen-peak-recalc.test.ts`).

**Purged and replaced — Python, 8 tests.** `PR3a`, `PR3b`, `PR4`, `PR4b`, `PR6`, `PR6b` exercised
`_remap_by_freq`, a reimplementation of the carry-forward logic living in the test file; `PR5a` and
`PR5b` asserted arithmetic on literals (`abs(201.0 - 200.0) <= 5.0`) and could not fail. All eight
deleted, `_remap_by_freq` deleted with them, and replaced by
`TestRemappingThroughProduction` (8 tests) driving `recalculate_frozen_peaks_if_needed` — re-freeze
on a shifted spectrum so detection mints genuinely new ids, then assert what production did with the
state keyed to the old ones.

**Verified by mutation, not just by passing.** Setting the production remap tolerance to `0.0` fails
exactly PR20, PR23, PR26 (the carry-forward cases) and leaves the five negative cases passing — the
correct signature. The purged eight would all have passed under that mutation. Production file
restored and verified clean afterwards.

Negative-only assertions were tightened first: `overrides.get(new.id) != "Air"` also passes on an
empty dict or a leak under the stale id, so PR25 now asserts the value is absent from the whole map.

**Counts:** Python frozen-recalc 28 → 28, composition changed entirely (8 vacuous out, 8 real in,
plus PR06/PR07/PR10/PR11 added and the 5 misfiled detection tests removed earlier).

### D2 batch 2 — 2026-09-19

**Closed, every one mutation-verified.** A test that passes is not evidence; each new test was run
against a deliberate break of the rule it claims, and had to fail for that rule and no other.

| edition | closed |
|---|---|
| Python | PR08, PR09, PR12, PR17, PR28, PR32 |
| Swift | PR14, PR17, PR27, PR30, PR32 |
| web | PR08, PR09, PR13/PR21, PR14, PR22, PR29, PR30 |

**Two tests were caught claiming more than they proved, by the mutation pass, not by review.**

- Swift/Python **PR32**'s first version asserted the captured fL peak was in `allPeaks` — but the
  brace branch assigns `allPeaks = [selPeak]`, so it held by construction and survived its mutation.
  Rewritten as a save/load round trip. The two editions need DIFFERENT assertions: Python's load
  rebuilds the offset map from `measurement.peaks`, Swift's restores it wholesale, so only Swift's
  save-side assertion has teeth. Recorded in both tests.
- Web **PR14** first survived because the test drove the bare `peakMinThreshold` property while
  `App.tsx` calls `setPeakMinThreshold`. The test was mutating a path the app does not take.
  Routed through the production entry point.

**PR14 exposed a hole in an existing Swift test.** Mutating Peak Min to re-run auto-selection — the
historical bug the whole `PeakMinDurability` suite exists for — killed ONLY the new PR14.
`peakMinSweep_preservesIdentitySelectionOverrideAndOffset` checks a SELECTED peak, which
auto-selection re-selects anyway, so it was blind to the regression it was written for. A
positive-only assertion cannot see a resurrection.

**Purged in passing.** Six empty husk classes left by the first purge (`TestLoadingGuard`,
`TestThresholdFilter`, `TestOffsetRemap`, `TestOverrideRemap`, `TestSelectionCarryForward`,
`TestEmptyPeaksGuard` — zero tests, reading as if the ground were covered); PR06/PR07/PR10/PR11
misfiled under `TestPR8CanReanalyze`, moved to a new `TestLoadedPath`.

**Both file headers were false.** Python's claimed *"the Python remap logic lives in
TapToneMeasurement data structures rather than in a separate recalculate method"* — the premise that
justified `_remap_by_freq`. Swift's claimed "Test plan coverage: PR1–PR7". Both rewritten to
describe the code as it is and to point here.

**Rule this earns.** `CROSS-EDITION-INVESTIGATION.md` rule 4 says re-measure before acting on an
archived FINDING. It does not cover descriptive claims in comments and docstrings, and that is where
most of this week's false records lived: the July reconciliation plan, C1's loaded-path claim, "the
Swift test doesn't exist", `_remap_by_freq`'s docstring, both file headers, and
`fromLive.ts`'s "already in a.peaks". Prose that describes how code works outlives the code and
reads as settled. Add the rule to that document.

**Counts after the batch:** Swift 35 in `FrozenPeakRecalculationTests` (was 30), Python 34 in
`test_frozen_peak_recalculation.py` (was 28), web 35 in `frozen-peak-recalc.test.ts` (was 28).
Suites: Swift green, Python 616 passed / 1 skipped (`oracle-sync`, private hub), web 423 passed /
2 skipped (`oracle-sync`, `mint-baseline` — both environment-gated).

**What remains is NOT listed here.** Open work lives in exactly one place, **RESUME HERE** at the
top. This is a dated log of what was done; it does not track what is left.

**Stage 4, sharpened twice over (a standing note, not an open-items entry):** sweep the other slugs for test-local helpers that
reimplement the behaviour under test — AND for tests whose fixtures encode a contract the
application no longer uses. `peak-fullset-save.test.ts` was the second kind, and it was hiding a
data-loss bug in shipped code.
