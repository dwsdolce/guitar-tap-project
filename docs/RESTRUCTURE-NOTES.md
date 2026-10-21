# Architectural-Parity Restructure — Notes & Inventory

Status: **PLANNED (post-review).** Not started. This doc accrues the raw material; the actual
restructure gets its own **spec, reviewed before any code moves** (per "review before implementing").

## The concern

The web port structurally **diverged from Swift/Python at the view layer** — one native view is
often decomposed into several React components. This was a **choice made during the port, not a
platform constraint.** React does not require small components; a single large component mirroring
a native view file is valid React.

Why the "platform forced it" defense fails: React and SwiftUI are **both declarative component
trees** — structurally *closer* to each other than either is to Qt's imperative widgets. Python/Qt
had the harder mapping job and stayed more cohesive with Swift; the web had the easier job and
diverged more. So the divergence is React-habit (favor small components) applied without pricing in
this project's top priority.

## Why it matters (the priority that was mis-weighed)

All three code bases are maintained **in lockstep**; that is the #1 priority. Structural
parallelism directly serves it — it keeps the `@parity` map ~1:1, makes "are the three the same?"
answerable, and avoids the symbol-level / many-to-many tagging the divergence forces. Generic React
decomposition benefits (small reusable units) are worth **less** here than the parity cost they impose.

## Decision: sequencing = "option 2"

1. **Finish the comment/doc review first.** It *is* the discovery phase the restructure needs —
   every view slug records "this web component ↔ that native section." M4/M5 are the first inventory
   entries. Restructuring before the map is complete would be cutting before measuring.
2. **Then** produce a restructure spec (architectural-parity plan), review it, and execute.
3. Do **not** accept the divergence permanently (contradicts the lockstep priority).

### Lens for the remaining `view/*` review (so option 2 doesn't waste effort)
`view/*` is exactly the layer that will move, so:
- **Do:** verify feature / label / color / value / wording parity; catch real bugs (e.g. mode
  colors, the metrics health-color ramp); record the component↔section mapping (below).
- **Go light on:** deep doc-enrichment (`@param` polish, prose expansion) of web components destined
  to be merged/split — that's the wasted motion.
- **Unchanged:** DSP/model layers — already structurally parallel, nothing moves; keep the strict
  file-1:1 doc bar there.

## Forced vs. chosen (what the restructure must NOT try to unify)

- **Forced (keep divergent, documented):** reactive/threading plumbing (`@Published` ↔ Qt signals ↔
  React state/hooks); audio engine (AVAudioEngine ↔ PortAudio ↔ Web Audio). Already documented
  (see PLATFORM PLUMBING notes in the gated-capture code).
- **Chosen (candidate to unify):** component/file **granularity** at the view layer.

## Inventory — native view → web fan-out (accruing during view/* review)

| Native view (Swift / Python) | Web components today | Restructure note |
|---|---|---|
| `FFTAnalysisMetricsView` / `fft_analysis_metrics_view` | `MetricsPanel.tsx` | 1:1 — fine as-is |
| `TapAnalysisResultsView.swift` (1291 ln: peaks + Ring-Out + Tap Ratio + Plate/Brace props + export) / `tap_tone_analysis_view` guitar-summary | `AnalysisResults.tsx` (Ring-Out/Tap-Ratio only) + `PeakCard.tsx` + material panels + export bar | **fan-out** — candidate to consolidate toward a `TapAnalysisResults` component matching the native file |
| `ComparisonResultsView` (all 3) | `ComparisonResultsView.tsx` | 1:1 — fine. (But Python had copy-pasted `MultiTapComparisonResultsView`'s dead `bold`/rectangle "averaged row" logic — VCR-1, removed. Watch for similar copy-paste between the two comparison views.) |
| **`view/main`** — Swift `TapToneAnalysisView` (main + 5 extensions: Actions/Controls/Export/Layouts/SpectrumViews) / Python `tap_tone_analysis_view.py` (**6868-line MONOLITH**) | `App.tsx` (orchestrator) + child components (each its own slug: spectrum-chart, peak-card, threshold-slider, settings, save-sheet, metrics…) + hooks (useChartView/useAnnotations/useMaterialSession/useAudioEngine) | **3-way structural divergence, the marquee case.** Swift = class-extension split; Python = monolith whose own module doc says *"the full split into separate mixin files is pending"* (a documented intent to match Swift's extensions); web = component + hooks decomposition. Python monolith is **multi-slug** (inline sub-panels belong to guitar-summary / results / material-list). Restructure: split the Python monolith (it already intends to), reconcile the web decomposition, pick a common target. |
| `MultiTapComparisonResultsView` (all 3) | `MultiTapComparisonResultsView.tsx` | 1:1 — fine. Clean mapping in all three; **not** a fan-out. (Source of the dead bold/rectangle path Python copy-pasted into `ComparisonResultsView` — VCR-1.) |
| **`view/settings`** — Swift `TapSettingsView.swift` + 3 extensions (Sections/Actions/LayoutHelpers) / Python `_show_settings()` **inline in the 6868-ln monolith** (+ empty `tap_settings_view_*.py` stubs) | `SettingsPanel.tsx` | **fold-in (opposite of a fan-out).** Swift = file-per-concern split; Python UI is inline in the monolith (stubs mark a pending extraction to mirror Swift); web = one component. The `@parity view/settings` tag was mis-placed on the Python `AppSettings` STORE (mirror of Swift `TapDisplaySettings`) — re-tagged onto `_show_settings`. The store is a separate cross-platform group (Swift `TapDisplaySettings` ↔ Python `AppSettings` ↔ web `settings.ts`) that still needs its own `@parity` slug. |
| **`view/spectrum-chart` + `view/spectrum-gestures`** — Swift splits into `SpectrumView.swift` (chart) **+ `SpectrumView+GestureHandlers.swift`** (gestures) / Python `fft_canvas.py` (+ gesture handling) | **both in one file `SpectrumChart.tsx`** (chart render + wheel/drag/pinch gesture block inline) | **fold-in.** The web has full, touch-aware, region-aware gestures (wheel-zoom, drag-pan, two-finger pinch) — it just **co-locates** them with the chart instead of a separate gesture file, so `view/spectrum-gestures` showed "— no web member" (a mapping artifact, NOT missing functionality). Fix = symbol-level `@parity view/spectrum-gestures` tag on the gesture block in `SpectrumChart.tsx`. Restructure decision: keep gestures inline (web) or split to match Swift — case-by-case. |
| _(add rows as each view slug is reviewed)_ | | |

## Finding from the view/main deep dive (reassuring)

A feature-by-feature dive across `view/main` (controls, toolbar, status bar, enable-logic,
material prompts, banners) found the **user-facing content is in tight parity across all three
despite the structural divergence** — same ranges/defaults, labels, messages, step prompts, wording.
So the divergence is **structure-only**; the content-sync discipline is strong. Implication for the
restructure: it's a **code-organization** job (split Python's monolith, reconcile the web
decomposition), **not** a content-reconciliation job — low risk of behavioural change if the content
is preserved verbatim while the file/component boundaries move.

## Peak-selection & annotation ownership → analyzer (P3, from the analyzer consolidation)

Captured here per the user (2026-07-11): while aligning the analyzer with Swift, a **model↔view boundary
divergence** surfaced that belongs to this restructure, not the state/audio consolidation.

- **Swift:** `TapToneAnalyzer` OWNS the whole peak-selection subsystem — `selectedPeakIDs`, `peakModeOverrides`,
  `peakAnnotationOffsets`, `selectedPeakFrequencies`, `userHasModifiedPeakSelection` — and preserves them
  **by frequency** across the UUID churn `findPeaks` causes (`recalculateFrozenPeaksIfNeeded` /
  `applyFrozenPeakState`). Selection + annotation state is analyzer state.
- **Web:** this lives in the **view** — the `useAnnotations` hook (selection, mode overrides, dragged label
  offsets) + the App `peaks` memo. A port-time view-side choice, same class as the component-granularity
  divergence above.
- **P3 = move that subsystem onto the analyzer** with Swift's by-frequency preservation. It's the most
  view-entangled slice, so it rides with the view-layer restructure rather than the analyzer consolidation.
- **P1 + P2** (main peaks + `tapEntries`-with-peaks into the analyzer) are done first, in the analyzer
  consolidation — **spec: [TAPTONEANALYZER-CONSOLIDATION.md](TAPTONEANALYZER-CONSOLIDATION.md) § Peak analysis.**
  P3 picks up the selection/annotation remainder here.
- **Two 6-TEST parity suites ride on P3** (they exercise exactly this subsystem; testing them against the
  view-side hook now would be thrown away when it moves to the analyzer — rescheduled here 2026-07-12):
  - `frozen-peak-recalc` **selection half** — Swift PR1/PR3–PR7 (`applyFrozenPeakState` by-frequency remap of
    selection / mode-overrides / annotation-offsets). The engine half (PR-A/PR2 on `recalculatePeaks`) already
    shipped 3-way (`ad0487d`); P3 appends the selection tests to that suite.
  - `annotation-state` (whole suite — D1–D8 offsets/selection/visibility/overrides, PS1–PS6 plate-peak selection,
    D3b `userHasModifiedPeakSelection`/`resetToAutoSelection`, `AnnotationStateTests.swift`). Web-only gap until P3.
  When P3 lands, build both suites against the analyzer (mirroring Swift), so both slugs go 3-way.

## Material peaks overload the guitar peak array (natives) — here the WEB is the correct model

_Added 2026-07-21, from the loaded-plate fL bug. Prevention, not a bug fix — which is why it lives
here rather than as its own STATUS item. Fully mapped; ~50 sites._

Swift `TapToneAnalyzer.currentPeaks` and Python `current_peaks` hold **both** guitar peaks **and**
material (plate/brace) peaks. That overloading is a bug factory: a *guitar-only* filter (Peak Min)
reached into the array while a **material** measurement was loaded and deleted the fL peak (Peak Min
−60 vs fL at −62.41 dB), losing it from the peak table *and* the chart annotations. Fixed on Python
in `_emit_loaded_peaks_at_threshold`; Swift got the matching explicit guard (Stage 0).

**Note the direction of travel:** normally the web is the port catching up. Here the **web has the
right design and the natives don't** — its `peaks` array is guitar-only (`if (p.material) peaks = []`)
with material in a `matPeaks { longitudinal, cross, flc }` struct, and a *separate save builder*
`buildMaterialMeasurement` (`src/measurement/fromLive.ts:520`) that constructs the file's `peaks[]`
straight from `matPeaks` and derives `selectedPeakIDs` from the same three. The bug is structurally
impossible there. It is the reference implementation, and its files round-trip with both natives.

**Replacement source (a trap):** the per-phase lists `longitudinalPeaks`/`crossPeaks`/`flcPeaks` are
**NOT** a complete source — they are explicitly emptied on load (Swift `MeasurementManagement.swift:
566,573,580`; Python `:536-538`, comment "peaks come from currentPeaks") and exist only during a live
capture. The complete source is `selectedLongitudinalPeak`/`Cross`/`Flc` — i.e.
`materialIdentifiedPeaks` / `material_identified_peaks` — repopulated on load, and exactly the three
peaks the file format stores.

**Sharp edges (what would NOT survive a naive change):**
1. **File format.** For material, `guitarFullSavePeaks()` / `guitar_full_save_peaks()` returns
   `currentPeaks` verbatim, so `peaks[]` in every material `.guitartap` comes from it. Guitar-only ⇒
   new material files get `peaks: []`, orphaning `selectedLongitudinalPeakID`/`Cross`/`Flc`, which
   every reader (including our own load path) resolves against `peaks[]`. Backward compatibility in
   BOTH directions must be designed. Sequence it: make the material store the save/load source
   FIRST, make the array guitar-only SECOND.
2. **ID coherence** — the saved L/C/FLC ids line up with `peaks[]` today only because both come from
   the same array.
3. **~12 Swift `.disabled(currentPeaks.isEmpty)` guards** (`+Layouts.swift`/`+Controls.swift`) gate
   Save/Export for ALL types — they would silently disable Save and Export for plate/brace.
4. **Re-source, don't just guard:** the material Analysis Results table
   (`TapAnalysisResultsView.swift:391`), the plate-property fallback (`:701-714`), and PDF/image
   export (`TapToneAnalysisView+Export.swift:86,107,125,279,295,305`).

**Verification bar:** round-trip `plate-umik-1-swift-iphone-1784499360.guitartap` (the fL case),
`plate-umik-1-3-tap-swift-ipad-…` (the corrupt-aggregate heal) and the brace fixtures on all three
platforms, byte-comparing saved output before/after.

## Measured status of the Python alignment (2026-09-16)

Taken from `parity-index.json` plus the files themselves, to replace an impression ("about half
done") with something checkable. Per area, how many groups carry each edition, and how often the
Python filename mirrors the Swift one:

| area | groups | swift | python | web | python filename mirrors swift |
|---|---|---|---|---|---|
| dsp | 14 | 14 | 14 | 14 | 11/14 |
| model | 8 | 8 | 8 | 7 | **8/8** |
| state | 4 | 4 | 4 | 4 | **4/4** |
| audio | 2 | 2 | 2 | 2 | 1/2 |
| util / dead-input | 2 | 2 | 2 | 2 | 2/2 |
| **view** | **20** | 20 | 20 | 18 | **13/20** |
| test | 37 | 37 | 36 | 35 | n/a — `XxxTests.swift` vs `test_xxx.py` is convention, not drift |

**The model layer is done and the view layer is where it stops** — which matches the history: the
models were deliberately aligned, while the Python views grew from the pre-Swift version and were
never fully reorganised once Swift became canonical.

The remaining view work is concentrated in **two files**, not spread across twenty:

- `views/tap_tone_analysis_view.py` — **7,462 lines**, carrying six slugs: `view/main`,
  `view/guitar-summary`, `view/material-results`, `view/material-instructions`, `view/settings`
  and `state/button-enablement`. In Swift those are separate files (`TapToneAnalysisView`,
  `TapAnalysisResultsView` at 1,302 lines, `TapSettingsView` at 272, plus the `+SpectrumViews`
  extension).
- `views/fft_canvas.py` — 1,910 lines, carrying `view/spectrum-chart` and `view/dot-layer`,
  against Swift's `SpectrumView` (1,319) and its extensions.

Two files are **destinations that were named for their Swift counterparts and never filled** —
the names are right, the migration is what is outstanding:

- `views/spectrum_view.py` — a 20-line stub that documents the `FftCanvas` mapping and
  re-exports it. The destination for Swift's `SpectrumView` + `+ChartContent`; the chart code
  still lives in `fft_canvas.py`.
- `views/tap_analysis_results_view.py` (1,997 lines) — the destination for Swift's
  `TapAnalysisResultsView`. Today it holds the measurement **persistence** functions
  (`save_all_measurements` / `load_all_measurements` over `saved_measurements.json`) while the
  results panel itself is still inside `tap_tone_analysis_view.py`. Those persistence functions
  have a home of their own waiting too: `models/tap_tone_analyzer_measurement_management.py`
  (1,246 lines, mirroring Swift `TapToneAnalyzer+MeasurementManagement`) already **calls into
  this view module** for disk I/O, which is the inversion Swift does not have.

So each of the two is one move in, one move out:

| Move | From | To |
|---|---|---|
| Results panel (`view/guitar-summary`, `view/material-results`) | `views/tap_tone_analysis_view.py` | `views/tap_analysis_results_view.py` |
| Settings (`view/settings`) | `views/tap_tone_analysis_view.py` | a `tap_settings_view.py`, as Swift has |
| Chart + dot layer (`view/spectrum-chart`, `view/dot-layer`) | `views/fft_canvas.py` | `views/spectrum_view.py` |
| Persistence (`save_all_measurements` / `load_all_measurements`) | `views/tap_analysis_results_view.py` | `models/tap_tone_analyzer_measurement_management.py` |

Each move carries its `@parity` tag with it, so the map reports progress as it happens: a
completed move turns a monolith cell into a file whose name matches the Swift one.

So "about half done" is fair, and specific: the **skeleton is right** — the destinations exist
and carry the Swift names — while the code and the tags still sit in the two monoliths. The work
is delivering on the names, not reconsidering them.

### What this means for the Android port

Nothing blocking (see [ANDROID-PLAN.md](ANDROID-PLAN.md) § Prerequisites). Two consequences
worth expecting:

- Once Android mirrors Swift's view files, several `view/*` groups will pair Swift and Android
  one-to-one while the Python cell points at a monolith. That is this backlog becoming visible,
  not an Android defect.
- Each Swift view that Python still concentrates is a place where the Android port has no Python
  reference to check itself against. Swift is canonical there, and the web is the second opinion.

---

## Open questions for the spec (later)
- Which fan-outs earn their keep vs. should consolidate? (case-by-case, not a blanket rule)
- Does consolidating hurt React testability enough to matter here? (probably not — DSP is already
  separately testable)
- Naming: align web component filenames to native view names where consolidated.

## The observable surface — the model-layer half of this issue (2026-09-22, from #17 S6)

Everything above is about the **view** layer. This is about the seam just below it, and it arrived
from #17 rather than from a view review. Owner's call, 2026-09-22: it belongs here, not in #17.

### What was measured

Four #17 findings turned out to be one defect wearing four names — a piece of model state whose
change notification lived in a separate method, with the plain field still writable beside it:

| finding | field | edition |
|---|---|---|
| F25 | `is_measurement_complete` | Python |
| F32 | `is_ready_for_detection` | Python |
| F34 | `currentTapCount` | web |
| F38 | `number_of_taps` | Python |

Each was fixed on the field, never on the class of defect, so the next one was guaranteed. The sweep
that followed (#17, 2026-09-22) measured all three editions and found the recurrence is **Python-only
in mechanism** but **three-way in cause**.

Per edition, the "published set" — what the view is able to react to:

| edition | surface | count | shaped by |
|---|---|---|---|
| Swift | `@Published` on `TapToneAnalyzer` | 67 | **storage** — everything stored, read or not |
| web | the `cachedSnapshot` object | 37 | **consumption** — what the view actually reads, computed getters included |
| Python | `QtCore.Signal` declarations | 21 | **events** — whichever change once needed pushing to a widget |

Three different questions, three different answers. **Nobody ever decided what the observable surface
is**, which is upstream of any mechanism difference. Do not read a naive set-diff of those three lists
as a divergence list — the names and the granularity do not line up, and an early attempt to diff
them produced a meaningless overlap count.

### Three notification mechanisms — a three-way divergence

*Owner's decision, 2026-09-27 (from #17 F53's run-review): Swift and web are **divergent** here, not the
same architecture. That supersedes this section's 2026-09-22 reading, which counted them as one because
both end in the view re-reading state — the same function, not the same mechanism.*

| edition | how a change reaches the view | what a missed notification does |
|---|---|---|
| Swift | automatic: setting any `@Published` property fires the object-wide `objectWillChange`; the views re-read the analyzer's state | cannot happen — the language raises it |
| web | by hand: the analyzer calls `notify()` where it changes something; App re-reads a snapshot of the whole state | the view is stale until the next `notify()`, which re-reads everything |
| Python | by hand, per field: specific signals push specific data into copies the view keeps (`tapCountChanged` → a label, `peaksChanged` → the peak list and scatter); nothing re-reads the model | the view's copy stays wrong until some other path happens to re-send it |

The web's explicit `notify()` is deliberate batching (`setStatusMessage`'s own comment: "Callers notify …
so multi-field transitions render once") — a fact the spec must weigh when choosing how the web aligns;
it does not make the web's mechanism Swift's.

Python is the furthest out, and not because Qt lacks reactivity: its notifications are **per-field to
per-widget**. That is why it needs 21 signals where the others need one notification, why every new field
is a fresh decision made by whoever adds it, and why the same defect has now been found five times.

### What alignment means here

The owner's answer, 2026-09-22, asked as a semantic question rather than an implementation one:
**ideally the same observable set, expressed the same way — both.**

- **Same set.** Decide once which model state the view layer may depend on. Each edition then spells
  that one set in its idiom: Swift makes exactly those `@Published`, web puts exactly those in the
  snapshot, Python makes exactly those properties whose setters emit. Checkable the way `@parity`
  slugs are — the three surfaces must be the same set, and adding a field becomes a three-edition
  decision instead of a Python accident.
- **Same way.** Python goes object-level — one `changed` signal, the view re-reads what it needs —
  so the three share a notification model and not merely a list. This is the larger half: it reworks
  how every Python widget binds. The web's hand-called `notify()` against Swift's automatic
  notification is part of this too (owner, 2026-09-27): the spec decides how the web raises its
  notification, with Swift as the reference.

Both, per the owner. The second is why this is #1's work and not a #17 finding: "It is a big job
since there are a lot of other items that get attached to it."

### Carried in from the sweep, for whoever writes the spec

- Python has **8** fields already converted to property setters. Those 8 are exactly the ones that
  were converted after a bug. **5** notify-paired fields remain unenforced:
  `show_loaded_settings_warning`, `status_message`, `loaded_measurement_name`, `microphone_warning`,
  `saved_measurements`.
- The sweep's claim that two of those five had live notify gaps did **not** survive checking. The
  `microphone_warning` gap was a misread of a deliberate suppression mechanism; #17 **F41** records
  the real defect there, which is a missing reset rather than a missing signal, and is not about the
  observable surface at all. The one real instance of this shape still standing is the
  `savedMeasurements` "legacy alias" — two names bound to one list.
- That matters for the spec: the sweep looked for "field written without its notify" and found
  essentially none. Python's hand-written emits are, today, correct almost everywhere. The cost of
  the current design is not that it is broken — it is that correctness is re-established by hand at
  every write site, and the four findings above are what that costs over time.
- Swift has **zero** instances. It is the reference for "cannot be forgotten".
- **A fifth instance, 2026-09-27 (#17 F53 run-review, Python).** After F52 made a material load keep no
  guitar peak set (`loaded_measurement_peaks` None, as Swift), the Python view's load handler still asked
  for the loaded peaks through `_emit_loaded_peaks_at_threshold`, which asserted they existed. The handler
  died inside Qt, so `peaksChanged` never carried the identified L/C/FLC: no Results rows, Annotations
  cycling nothing, until a zoom's viewport refresh re-sent them. Swift's and the web's views read the
  identified peaks from the analyzer and were unaffected. Fixed in the emit; the design that made it
  possible — the view's copy fed only by the paths that remember to send — is what this section is about.
- A guard was considered and NOT written: "assert every signal has a property" would only police
  Python's existing habit, where the real check is that the three surfaces match. The guard belongs
  with the spec, not ahead of it.

### Where settings are saved — the web's settings store (2026-09-28, from #21 item 14)

Swift saves each setting in the model: the analyzer's properties write `TapDisplaySettings` in their
`didSet` (e.g. `tapDetectionThreshold`, `peakMinThreshold`), so a change from any source — a slider, the
Settings sheet, a loaded measurement — is saved the same way. Python now does the same for the two
thresholds (#21 item 14). The web keeps every setting — thresholds, measurement type, display ranges,
annotation mode and the rest — in one App-level store (`settings` / `updateSettings`); the analyzer holds
none of them, and after a load it hands App a `loadedSettings` patch which App saves.

Owner, 2026-09-28: architectural consistency is the bar, not correct behaviour; the web's store covers
every setting, so moving two thresholds alone would split the web's mechanism. The spec decides where the
web's settings live and who saves them, with Swift's model-owned settings as the reference. The owner's
concern, recorded with it: that #1 is never done and divergences keep being carried here instead of fixed.


## The numeric model — 32-bit in Swift, 64-bit in Python and the web (2026-10-01, from #17 F55)

Found while deciding how precisely the saved display range is stored (#17 F55 item 5). The editions do not compute
the same numbers:

- **Swift** holds audio, spectra, peak frequencies / magnitudes / Q / bandwidth, and the chart's range as `Float`
  (IEEE-754 binary32), and computes the FFT in single precision (`vDSP_DFT_zrop`, Accelerate).
- **Python** computes the FFT with `numpy.fft.fft`, in 64-bit (the padded buffer is created `float64`,
  `realtime_fft_analyzer.py`); its peaks and ranges are Python `float` (64-bit).
- **The web** computes its own FFT on `Float64Array` (`dsp/fft.ts`); every `number` is 64-bit.

All three start from the same 32-bit audio samples. The differences come from 32-bit vs 64-bit arithmetic: for a
real signal the magnitudes differ by around 10⁻⁶ dB, degrading only near the 32-bit FFT's floor (about 140 dB below
full scale, under any real microphone's noise); interpolated peak frequencies differ by small fractions of a hertz,
far below the 0.1 Hz shown. The cross-edition parity tests compare within tolerances (the oracle's `freqHz`,
`magDb`, `q`) for this reason. Every result is a short, one-pass computation — an FFT, peak interpolation,
averaging — with nothing iterated or integrated over time, so the differences do not grow.

What is already the same: the saved files. `.guitartap` stores Swift's `Float` fields at 32 bits in every
edition — Swift's `JSONEncoder` writes the shortest decimal that round-trips to the `Float`; Python quantises with
`np.float32` when writing (`ResonantPeak.to_dict` and the snapshot encoders), the web with `Math.fround`
(`measurement/floatJson.ts`, `f32()`); fields Swift declares `Double` (pitch, sample rate, annotation positions) stay
64-bit everywhere. F55 item 5 stores the saved display range the same way: Swift's `Float`, with Python and the web
rounding to 32 bits at the store. So the editions agree on everything saved, and differ in arithmetic.

**For the spec — the decision to make:** one numeric model for all three. Either Swift moves to 64-bit (a
double-precision FFT, `Double` for spectra, peaks and ranges, and the file format's `Float` fields — compatible as
JSON), or Python and the web emulate 32-bit throughout (`numpy.float32` arithmetic; `Math.fround` after every
operation — fragile, since one missed site lets a 64-bit value through). The owner's background in numerical
simulation (stiff systems, where precision differences grow) is the reason this is recorded rather than accepted:
"in that domain this would cause major differences."


## Who owns the analyzer — Python's chart builds it (2026-10-01, from #17 F55 item 20)

Swift's `TapToneAnalysisView.init` creates the `RealtimeFFTAnalyzer` and the `TapToneAnalyzer` and owns them;
`SpectrumView` never sees the analyzer — it is given the spectrum, the peaks and range bindings. The web's `App`
owns the analyzer (`useTapToneAnalyzer`) and the chart gets props. Python's chart owns it: `FftCanvas.__init__`
creates the engine (which picks the input device), looks up that device's calibration, creates the
`TapToneAnalyzer`, calls `analyzer.start(parent_widget=self, …)`, sets Peak Min, and re-emits 26 of the analyzer's
signals as its own. The main window then reaches the analyzer through the canvas — about 100
`fft_canvas.analyzer` / `canvas.analyzer` references in `tap_tone_analysis_view.py`, 37 connections to the
canvas's re-emitted signals, and 3 references in `fft_analysis_metrics_view.py`.

What it costs today: the canvas cannot be built in a test, since its constructor opens the audio device. F55
item 20 (Python re-detected the peaks whenever it applied a chart range, so a completed plate's peak list and dot
vanished on Reset to Saved) is fixed in the code but untested for that reason.

The hand-in, sized for the spec:

1. The main window creates the engine and the analyzer, does the calibration lookup and `start()`, then builds the
   canvas — as Swift's view `init`. The ordering needs care: the canvas is built in a deferred step after the
   window shows, and `start()` is given the canvas as its `parent_widget` today.
2. The canvas takes the analyzer: `FftCanvas(analyzer, …)`, so a test can hand it `TapToneAnalyzer.for_testing()`.
3. The main window uses its own `self.analyzer`; the canvas's 26 re-emitted signals go, and the 37 connections go to
   the analyzer's signals — or, once Python moves to one object-level `changed` signal (above), to that.
4. The metrics view is handed the engine, as Swift's `FFTAnalysisMetricsView(analyzer:)`.

Then the parked test, Python: for a completed plate, applying a chart range (a reset, a load's range, a widening,
Settings' Done) leaves the identified peaks and their ids unchanged; for a guitar, it does not re-detect. If the
spec makes the chart data-only, as Swift's `SpectrumView`, the chart can no longer re-detect at all and the test
moves to the view that applies the range.

Owner, 2026-10-01: parked here rather than done in F55 — the hand-in moves Python's startup (device selection,
calibration, `start()`), which is unrelated to the display range, and #1 does it as part of the planned
restructure. Item 20 is covered by F55's run-review (step 13) until then.
