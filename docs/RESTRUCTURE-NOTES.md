# Architectural consistency — Swift, Python and web

**Issue:** [#1](https://github.com/dwsdolce/guitar-tap-project/issues/1)

## The goal

The three editions are one design. Swift is canonical; Python and the web are the same program in other
languages — **the same architecture throughout, not only the same behaviour**: the same types and files, the
same owners of state, the same direction of dependencies, the same way a change reaches the screen. Where a
language or platform forces a difference, it is named and kept to the smallest place it can live.

Why: the three are maintained in lockstep. When a Swift file has one Python file and one web file that hold the
same code, "are the three the same?" is a question about three files, a change is made three times in three
known places, and the parity map stays one-to-one. Every place where the structure differs is a place where a
change can be made in one edition and missed in another — which is how most cross-edition bugs so far arose.

The work is **moving code, not changing it**: each move keeps behaviour, wording and values exactly, carries its
`@parity` tag with it, and leaves the tests green.

## What "the same structure" means

1. **Files.** Each Swift source file has one Python file and one web file of the same name in the language's
   style: `TapToneAnalyzer+SpectrumCapture.swift` ↔ `tap_tone_analyzer_spectrum_capture.py` ↔
   `tapToneAnalyzer+SpectrumCapture.ts` (or the web's chosen spelling — see Web, below). A Swift type split
   across extension files is split the same way in each edition: Python already does this with mixins.
2. **Ownership.** The object that owns a piece of state in Swift owns it in every edition: the analyzer owns
   measurement state, the view that creates the analyzer owns the analyzer, view-only state stays in views.
3. **Dependencies.** Models never call into views for their work.
4. **Notification.** The same set of model state is observable in each edition, and a change reaches the view
   the same way.
5. **Numbers.** One numeric model for the arithmetic.

## Where each edition stands (measured 2026-10-23)

Swift: 103 source files, 35,436 lines. Python: 40,913 lines. Web: 20,389 lines.

### Already the same in all three

- **Peak selection and annotation state are analyzer state** — selection, mode overrides, label offsets, the
  user-modified flag, and their preservation by frequency across re-detection. The shared `annotation-state`
  (44 cases) and `frozen-peak-recalc` (51 cases) suites run against the analyzer in all three.
- **The guitar peak set is guitar-only**; plate and brace use the identified L/C/FLC
  (`materialIdentifiedPeaks`), and a material save writes those three as its peaks.
- **The web loads, clears and saves through its analyzer** (`loadMeasurement`, one `clearResult` inside
  `startTapSequence`, one `buildMeasurement` dispatching to the guitar and material builders); its settings live
  in one store outside React (`settingsStore`), and the analyzer writes them on a load.
- **The model types** — Python mirrors Swift file-for-file across `Models/`, including the ten
  `TapToneAnalyzer` files and four of the five `RealtimeFFTAnalyzer` files; the web has a file per small type
  for most of them.
- **Python's view-update contract** (`views/utilities/view_update.py`): a model change invalidates a view,
  which refreshes once per event-loop turn; keyed list updates; styles applied only on change. Views already on
  it need no reshaping beyond moving files.

### Python

The model layer is in place. What remains is the view layer, which is concentrated in three files, and two
model→view inversions.

| Python file | Lines | Holds the code of (Swift) |
|---|---|---|
| `views/tap_tone_analysis_view.py` | 6,892 | `TapToneAnalysisView` and its 5 extensions; `TapAnalysisResultsView` (the results panel); `TapSettingsView` and its 3 extensions (`_show_settings`, ~1,400 lines); `PlayFileSheet` (`_PlayFileDialog`) |
| `views/fft_canvas.py` | 2,021 | `SpectrumView` and `+ChartContent`, `+GestureHandlers`, `SpectrumScrollWheel`, `ScrollInput` — and the engine and analyzer lifecycle, which Swift keeps in `TapToneAnalysisView` |
| `views/tap_analysis_results_view.py` | 1,801 | **not** `TapAnalysisResultsView`: `PDFReportGenerator`, the measurement persistence of `TapToneAnalyzer+MeasurementManagement`, `MeasurementFileExporter`'s export directories and JSON, two of `ExportableSpectrumChart`'s renderers |

**Stubs** — files named for their Swift counterparts and never filled. Each is the destination for code that
today lives elsewhere:

| Stub | Lines | Swift | The code today |
|---|---|---|---|
| `views/spectrum_view.py` | 21 | `SpectrumView`, `+ChartContent` | `fft_canvas.py` `FftCanvas` |
| `views/spectrum_view_gesture_handlers.py` | 19 | `+GestureHandlers` (and `SpectrumScrollWheel`, `ScrollInput`) | `fft_canvas.py` mouse, wheel and viewport handlers (L1032–1134, L1313–1408) |
| `views/tap_tone_analysis_view_actions.py` | 14 | `+Actions` | `MainWindow`: start/stop/pause/cancel, open file, peak selection, devices, help |
| `views/tap_tone_analysis_view_controls.py` | 14 | `+Controls` | `MainWindow`: signal wiring, state updates, threshold, tap button and events (L2113–3380) |
| `views/tap_tone_analysis_view_export.py` | 15 | `+Export` | `MainWindow` save and export (L4036–5200) |
| `views/tap_tone_analysis_view_layouts.py` | 15 | `+Layouts` | `MainWindow` layout builders (L879–2108) |
| `views/tap_tone_analysis_view_spectrum_views.py` | 14 | `+SpectrumViews` | `MaterialInstructionsWidget`, the material instruction panel |
| `views/utilities/tap_settings_view_actions.py` | 13 | `TapSettingsView+Actions` | `_show_settings`: apply, cancel, the resets |
| `views/utilities/tap_settings_view_layout_helpers.py` | 13 | `TapSettingsView+LayoutHelpers` | `_show_settings`'s nested layout helpers |
| `views/utilities/tap_settings_view_sections.py` | 15 | `TapSettingsView+Sections` | `_show_settings`'s section bodies |
| `views/shared/combined_peak_mode_row_view.py` | 15 (re-export) | `CombinedPeakModeRowView` | `views/shared/peak_card_widget.py` (858) |
| `views/utilities/measurement_file_exporter.py` | 32 (re-export) | `MeasurementFileExporter` | `views/tap_analysis_results_view.py` |

**Names that do not match their contents:** `views/utilities/tap_settings_view.py` (631) holds the settings
*store* (`AppSettings`), not the Settings screen; `models/realtime_fft_analyzer_fft_processing.py` (113) holds
only `compute_fft`, with the rest of Swift's `+FFTProcessing` in `realtime_fft_analyzer.py`; Swift's
`+Watchdog` has no file — it is inside `realtime_fft_analyzer_engine_control.py`.

**Other Swift files with no Python file:** `PlayFileSheet`, `PDFReportGenerator`, `AppButtonStyle` (in
`palette.py`), `DocumentationLinks`, `ChartAxisTitle`.

**Model→view inversions.** Swift's models do their own work; Python's call into views for two of it:
- measurement persistence — `save_all_measurements`, `decode_library` and `measurements_file` live in
  `views/tap_analysis_results_view.py`, and the analyzer imports them (`tap_tone_analyzer_measurement_management.py`
  L86, L109; `tap_tone_analyzer.py` L1568). Swift: `TapToneAnalyzer+MeasurementManagement.swift`.
- the settings store — `AppSettings` lives in `views/utilities/tap_settings_view.py`, and six model files import
  it. Swift: `Models/TapDisplaySettings.swift`.
(The models' use of `palette` for the material colours is not an inversion: Swift's models use `Palette` the same
way.)

**Who owns the analyzer.** Swift's `TapToneAnalysisView.init` creates the engine and the `TapToneAnalyzer` and
hands them to the chart. Python's chart creates them: `FftCanvas.__init__` builds the engine and the analyzer,
attaches the analyzer to itself, sets Peak Min, and relays 23 of the analyzer's signals as its own (26 signals in
all); the main window reaches the analyzer through the canvas 115 times, and the metrics view 5 times. The chart
cannot be built in a test, because building it opens the audio device.

### Web

The web's model is consistent in what it owns but not in how it is filed; its views are decomposed differently
from Swift's.

**Model files folded together:**

| Swift | Web |
|---|---|
| `TapToneAnalyzer` + 9 extensions (10 files, 6,749 lines) | `state/tapToneAnalyzer.ts` — one file, 4,260 lines, sections marked by comments |
| `RealtimeFFTAnalyzer` + 4 extensions (5 files, 3,654 lines) | `audio/realtimeFFTAnalyzer.ts` — one file, 1,336 lines |
| `DetectionState`, `MaterialTapPhase`, `AnalysisDisplayMode` | types inside `tapToneAnalyzer.ts` |
| `MeasurementType`, `PlateStiffnessPreset`, `AnnotationVisibilityMode` | inside `settings.ts` |
| `GuitarType` | inside `dsp/guitarModes.ts` |
| `UserAssignedMode`, `ResonantPeak`, `SpectrumSnapshot` | inside the analyzer, `measurement/types.ts`, the encoders |
| `AVAudioDevice`, `TimingActivity` | inside `realtimeFFTAnalyzer.ts` |

**Model files spread out:** `TapToneMeasurement` (1 Swift file) → 7 files in `measurement/`; `GuitarMode` → 3;
`MicrophoneCalibration` → 2; `TapDisplaySettings` → `settings.ts` + `settingsStore.ts`.

**Views:**

| Swift | Web |
|---|---|
| `TapToneAnalysisView` + 5 extensions (3,720 lines) | `App.tsx` (1,527) + `hooks/useAudioEngine.ts` + `hooks/useTapToneAnalyzer.ts`; `+SpectrumViews`' material panel is `MaterialInstructionPanel.tsx` |
| `TapSettingsView` + 3 extensions | `SettingsPanel.tsx` (one file) |
| `SpectrumView` + `+ChartContent` | `SpectrumChart.tsx`, `hooks/useChartView.ts`, `presentation/spectrumRender.ts`, `presentation/chartTypes.ts` |
| `+GestureHandlers`, `SpectrumScrollWheel`, `ScrollInput` | inside `SpectrumChart.tsx` |
| `TapAnalysisResultsView` | `AnalysisResults.tsx`, `MaterialResults.tsx`, `PeakCard.tsx`, and the results list built in `App.tsx` |
| `MaterialDimensionsEditor`, `PlateBodyDimensionsEditor` | inside `MaterialResults.tsx` |
| `MeasurementsListView` + `MeasurementRowView` | `MeasurementsPanel.tsx` |
| `PDFReportGenerator` | `presentation/pdfReport.ts` + `presentation/measurementImage.ts` |

`App.tsx` also derives, for display, values Swift's views derive too (sorted and in-range peaks, markers,
comparison rows) — view work in both, so it moves with the view files rather than to the model.

**One report path or two.** Swift and Python build the PDF report with two view paths (a measurement's and a
comparison's); the web has one (`renderReportContent`). One of the two shapes is chosen and the others follow.

### Observable state — how a change reaches the view

| Edition | What the view can observe | How a change reaches it |
|---|---|---|
| Swift | 54 `@Published` properties on `TapToneAnalyzer` | automatic — setting a property notifies; views re-read the analyzer |
| web | a snapshot of ~70 fields (`getSnapshot`) | by hand — `notify()` at 65 call sites; the view re-reads the whole snapshot |
| Python | 36 per-field Qt signals on `TapToneAnalyzer` (no object-level signal) | by hand, per field — each signal carries data to the widgets that listen; 12 property setters, 7 of which emit their own signal; 5 notify-paired fields are still plain attributes (`show_loaded_settings_warning`, `status_message`, `loaded_measurement_name`, `microphone_warning`, `saved_measurements`) |

The owner's bar: **the same observable set, expressed the same way.** Decide once which model state views may
depend on; each edition exposes exactly that set; and the change reaches the view by the same mechanism —
Swift's (notify on set, the view re-reads) being the reference. For Python that means one object-level change
notification instead of per-field signals; for the web, notification raised by the setting of state rather than
by hand. Python's `Invalidator` already gives its views the re-read half.

### Numbers

Swift computes in 32-bit (`Float`, a single-precision `vDSP` FFT); Python (`numpy` `float64`) and the web
(`Float64Array`) in 64-bit. All three save the same 32-bit values, so files agree; the arithmetic does not. The
differences are tiny and do not grow (every computation is a short, one-pass one), and the shared tests compare
within tolerances — but they are a difference of architecture: either Swift moves to 64-bit (and the file
format's `Float` fields with it, compatible as JSON) or the others emulate 32-bit throughout.

## The work

In order: each step stands alone, ships alone, and is run-reviewed before the next.

**Python**

1. **Model→view inversions.** Persistence (`save_all_measurements`, `decode_library`, `measurements_file`,
   `load_all_measurements`) moves into `tap_tone_analyzer_measurement_management.py`; the settings store
   (`AppSettings`) moves into the models (beside `tap_display_settings.py`), and
   `views/utilities/tap_settings_view.py` is freed for the Settings screen.
2. **The engine's files.** `+FFTProcessing`'s code moves into `realtime_fft_analyzer_fft_processing.py`; a new
   `realtime_fft_analyzer_watchdog.py` takes the watchdog out of engine control.
3. **Who owns the analyzer.** The main window creates the engine and the analyzer, looks up the calibration and
   starts it, then builds the chart with them (`FftCanvas(analyzer, …)`); the canvas's relayed signals go and the
   main window connects to the analyzer; the metrics view is handed the engine. Then the parked test: applying a
   chart range does not re-detect peaks, and a completed plate keeps its identified peaks.
4. **The chart.** `fft_canvas.py` → `spectrum_view.py` (with `+ChartContent`) and
   `spectrum_view_gesture_handlers.py` (gestures, the wheel, scroll input).
5. **The main window.** `tap_tone_analysis_view.py` → the five extension files, by the line ranges in the stub
   table above; `_PlayFileDialog` → `play_file_sheet.py`.
6. **The results panel.** `_build_right_panel` and its refresh → `tap_analysis_results_view.py`; what that file
   holds today moves out first — the PDF report to `pdf_report_generator.py`, the export directories and JSON to
   `measurement_file_exporter.py`, the comparison renderers to `exportable_spectrum_chart.py`.
7. **Settings.** `_show_settings` → `tap_settings_view.py` and its three extension files.
8. **The remaining strays:** the peak card into `combined_peak_mode_row_view.py`; `AppButtonStyle`,
   `DocumentationLinks`, `ChartAxisTitle` files.

**Web**

TypeScript cannot spread one class over several files as Swift extensions do; the web does what Python does with
mixins — the class's methods are grouped into one file per Swift extension and attached to the class
(declaration merging plus prototype assignment), so `tapToneAnalyzer.ts` keeps the class and its stored state and
each `tapToneAnalyzer+SpectrumCapture.ts` (or the chosen spelling) holds that extension's methods.

9. **The analyzer and the engine** split into one file per Swift file, as above.
10. **The folded model types** get their own files (`detectionState.ts`, `materialTapPhase.ts`,
    `analysisDisplayMode.ts`, `measurementType.ts`, `plateStiffnessPreset.ts`, `annotationVisibilityMode.ts`,
    `guitarType.ts`, `userAssignedMode.ts`, `resonantPeak.ts`, `audioDevice.ts`); the spread-out ones are
    gathered where a Swift file is one file (`TapToneMeasurement`, `GuitarMode`) — keeping helpers that are
    TypeScript plumbing (`floatJson`, `base64`) apart.
11. **The main view.** `App.tsx` → `TapToneAnalysisView.tsx` and one module per extension (actions, controls,
    export, layouts, spectrum views), as hooks or components as each extension's content suits.
12. **The chart, settings and results:** `SpectrumChart.tsx` with gestures in their own module;
    `SettingsPanel.tsx` → `TapSettingsView.tsx` and its three parts; the results views gathered into
    `TapAnalysisResultsView.tsx` with the two dimension editors in their own files; the measurements list and row
    split; the PDF report one module.

**All three — decisions before code**

13. **The observable set and its mechanism** (above): the set first, then Python's object-level notification,
    then the web's.
14. **The numeric model:** 64-bit everywhere, or 32-bit everywhere.
15. **The report path:** one or two.

## What stays different (forced, kept small and named)

- **Platform plumbing:** the audio stacks (AVAudioEngine / PortAudio / Web Audio) behind the engine's interface;
  threading (Swift actors and the main queue / Qt threads and queued signals / the browser's single thread).
- **Platform-only files:** Swift's iOS and macOS adapters (`PointerScroll`, `SecondaryClickMenu`,
  `ResultsWindowPresenter`, `SheetTitle`); Python's Windows single-instance lock, update checker, release and
  colour guards, PortAudio loader; the web's release notes, PWA, IndexedDB store and PNG metadata.
- **Language idiom:** stand-ins for controls a toolkit lacks (Python's `ValueStepper`, `MenuPicker`; the web's
  icon set for SF Symbols); file-name spelling.
Each such file says why it has no counterpart (`@parity none` with the reason).

## Measuring progress

The parity map already shows it: a move turns a cell that points at a monolith into a file named after the
Swift one. A check worth adding to the parity tooling: list every Swift source file whose Python or web
counterpart (by `@parity` slug) is not a file of the matching name, so the remaining work is a list the tools
print, not a document to keep current.
