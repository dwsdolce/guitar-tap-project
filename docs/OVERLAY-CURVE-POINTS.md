# Overlaid curves: Python draws every point; one name for them in every edition; the multi-tap PDF's page 1

**Issue:** [#45](https://github.com/dwsdolce/guitar-tap-project/issues/45)

Status: **OPEN — committed: Swift `90be580`, Python `b3a98dd`, web `66165e0` (release notes `84639e9`, `15adc05`, `515ac92`); run-review passed in every edition (owner); Swift's tests pass; the export check passes in every edition; CI pending.**

## The problem

Resizing the window with a large comparison loaded is very slow in Python: with a 49-measurement comparison, about
1.6 s per resize (owner, 2026-10-25, during #43's run-review). Panning and zooming redraw the same curves.

## The chart's two kinds of curve

- **The spectrum line**: the live FFT, or a single measurement's spectrum.
- **The overlaid curves**: a comparison's measurements, a multi-tap measurement's taps (shown as a comparison), or a
  plate's or brace's phases. Each has its own colour and a legend entry. In a comparison they replace the spectrum
  line; during a plate or brace capture they sit over the live line.

Each spectrum holds 32,768 points; a chart shows a few hundred of them.

## What each edition draws

| | The spectrum line | Overlaid curves | The crosshair snaps to | Export chart |
|---|---|---|---|---|
| Swift | `DisplayRange.drawnIndices(of:min:max:)`: the points in the visible range and one beyond each edge (`chartData`) | the same (`materialSpectraContent`) | the full overlay arrays (`resolveSnapState`) | the same (`ExportableSpectrumChart.seriesData`) |
| Web | `drawnIndices` inside `drawCurve` | the same (`drawCurve` draws every curve) | the full overlay arrays | the same (`renderSpectrum`, shared with the screen) |
| Python | `drawn_indices` (`FftCanvas._draw_spectrum`), re-trimmed when the range changes | **every point**: `_render_comparison_curves` and `load_material_spectra` hand pyqtgraph the whole spectrum | the curve items' own data (`getOriginalDataset()`) | **every point**, overlays and spectrum line; its `series_data` / `chart_data` are unused and filter to inside the range, without the point beyond each edge |

In Swift and the web the full spectra are the stored data, trimming happens when a curve is drawn, and the crosshair
reads the full data.

## Measured

The 49-measurement comparison in a 1200 × 700 chart at 60–360 Hz, offscreen, 20 resizes:

| Overlaid curves | Points drawn | Per resize |
|---|---|---|
| every point (Python now) | 1,605,640 | 1556 ms |
| trimmed with `drawn_indices` | 20,223 | 100 ms |

After the change, in the real main window (offscreen, 49 measurements at 60–360 Hz, 20 resizes): the committed code
1,605,640 points, 1434 ms per resize; this change 20,223 points, 74 ms.

The legend (#43) makes no difference: 1559 ms without it, 1571 ms with it.

## Where the overlaid curves come from

- **Swift**: one list, `TapToneAnalysisView.materialSpectra`, computed from the analyzer: `comparisonSpectra` in
  comparison mode (any measurement type), else a plate's or brace's phase spectra, else none. It is handed to
  `SpectrumView` and to the export.
- **Web**: one list, `overlays` (`App.tsx`: `inComparison ? comparisonOverlays : material ? matOverlays : undefined`),
  handed to `renderSpectrum` for the screen and the export.
- **Python**: the export uses one list, `TapToneAnalysisView._chart_overlay_spectra()`, Swift's `materialSpectra`.
  The screen does not. `FftCanvas` builds comparison curves itself from `analyzer._comparison_data`
  (`_render_comparison_curves`), and material curves from a second list the analyzer stores and signals
  (`_material_spectra`, `set_material_spectra`, `materialSpectraChanged` → `load_material_spectra`). It tells the two
  apart with `_has_material_spectra`.

## The names

The name `materialSpectra` dates from the plate and brace work (`7032314`, 2026-02-26), the first measurements with
more than one curve on a chart. Comparison (`96dfdbd`, 2026-03-22) reused that list without renaming it, and
multi-tap's taps arrived through comparison. Today the overlaid curves have a different name in each edition, and
none says what they are:

| | Name now | Says |
|---|---|---|
| Swift | `materialSpectra`, `materialSpectraContent` | material phases only |
| Web | `overlays`, `SpectrumOverlay` | right, but a different word from the others |
| Python | `_comparison_curves`, `_comparison_curve_colors`; `material_spectra` (export) | comparisons only on screen, materials only in the export |

**Proposed name: "overlay spectra"**, for the list of overlaid curves, in every edition. "Overlay" is already what
the web, Python's `_chart_overlay_spectra` and this document call them, and it separates them from the spectrum line.

| | Renamed | To |
|---|---|---|
| Swift | `materialSpectra` (`TapToneAnalysisView`, `SpectrumView`, `ExportableSpectrumChart` and its factory functions' parameters) | `overlaySpectra` |
| Swift | `materialSpectraContent` | `overlaySpectraContent` |
| Web | `overlays` (render and export options, `SpectrumChart` prop) | `overlaySpectra` |
| Web | `SpectrumOverlay` | `OverlaySpectrum` |
| Python | `_chart_overlay_spectra()` | `overlay_spectra()` |
| Python | `material_spectra` (`ExportableSpectrumChart`, `make_exportable_spectrum_view` and its callers) | `overlay_spectra` |
| Python | `_comparison_curves`, `_comparison_curve_colors` (`FftCanvas`) | `_overlay_curves`, `_overlay_curve_colors` |

Names that stay, because they name one kind accurately: Swift `comparisonSpectra`, `longitudinalSpectrum`,
`crossSpectrum`, `flcSpectrum`; Python `_comparison_data`, `longitudinal_spectrum` and its siblings; web
`comparisonOverlays`, `matOverlays`. Python's `comparison_count` and `_render_comparison_curves` are settled by D1.

**Comments.** Every comment that names the overlaid curves is reread in the rename. Known to be wrong now:

- Swift `SpectrumView.swift:190` ("plate/brace measurements: L, C, FLC"); the file header of
  `TapToneAnalysisView+SpectrumViews.swift` ("Guitar measurements return an empty array") and the computed
  property's doc comment ("For guitar mode this returns only `comparisonSpectra`": comparison wins for every type);
  `ExportableSpectrumChart.swift:477` ("Per-phase spectrum series for plate/brace overlays");
  `TapToneAnalyzer.swift:1106-1108` ("merged into `materialSpectra` in guitar mode"); the `lockedSeriesIndex` and
  snap comments ("index into `materialSpectra`").
- Web `chartTypes.ts:72` ("plate/brace per-phase spectra, later comparison curves"); `spectrumExport.ts:159-161` and
  `spectrumRender.ts:273` (refer to Swift's old name).
- Python `exportable_spectrum_chart.py:175` and `:893` ("per-phase spectra … for plate/brace"),
  `tap_analysis_results_view.py:1349`, `FftCanvas.load_material_spectra`'s docstring ("(label, (r,g,b), …)": it is a
  role).

## Decision D1 (owner): one list for Python's overlaid curves on screen

Python's screen builds its overlaid curves on two paths, and its analyzer stores a list (`_material_spectra`) that
Swift's does not: Swift's analyzer has only the phase spectra, and the view assembles the list. Proposed: remove the
divergence. `FftCanvas` draws from `overlay_spectra()`, rebuilt when what it reads changes (the comparison, a phase
spectrum, the display mode), as Swift's chart redraws when `materialSpectra` changes. `_material_spectra`,
`set_material_spectra`, `materialSpectraChanged`, `load_material_spectra`, `_render_comparison_curves` and
`_has_material_spectra` go, replaced by the one path; where `_has_material_spectra` decides whether the spectrum line
is hidden, the canvas asks what Swift asks (comparison mode; reviewing a material phase).

## The multi-tap PDF's page 1 (Swift)

A multi-tap measurement's PDF is of the guitar measurement: page 1 the averaged result, page 2 the tap comparison,
both in the measurement's one range. The Taps view has no effect on it.

Swift breaks that from the main view: Export PDF Report draws page 1 (`createAveragedSpectrumView`) with the chart's
`overlaySpectra`, which while the Taps view is on are the taps — page 1 shows the tap curves with the averaged peaks'
labels on them, and "Comparing 4 measurements" (owner's export of `dws-2024-umik-1-3-tap-swift-mac`, 2026-10-25). Page
2, the range and the page's text are right.

| | From the saved list | From the main view |
|---|---|---|
| Swift | both pages from the measurement (`PDFReportGenerator.report(for:)`) | page 2 from `makeMeasurement` (the displayed range); **page 1 from the chart's state** |
| Python | both pages from the measurement (`export_report_for_measurement`) | the same split as Swift; a guitar's page 1 gets no overlaid curves, so it shows no bug, and a plate's or brace's reads the loaded measurement or the analyzer's `_material_spectra` |
| Web | both pages from the measurement (`multiTapPdfData`) | the same: the measurement as it would be saved, with the displayed range (`buildCurrentMeasurement`), through `multiTapPdfData` |

A single measurement's and a saved comparison's PDFs have one view each — the chart is the measurement — so the
Taps-view problem cannot arise there; but Swift and Python draw those from the chart too, where the web builds them
from the measurement.

The fix (owner, 2026-10-25: architecture — a PDF is a report of the measurement): every PDF from the main view, in
Swift and Python, is built as the web's is — the measurement as it would be saved, with the displayed range, exported
through the saved list's report builder (Swift `PDFReportGenerator.report(for:)`, Python
`export_report_for_measurement`). One builder per report, whichever place it is exported from. `createAveragedSpectrumView`
and Python's page-1 assembly go. Export PDF Report is enabled only with a result to save
(`hasResultToSaveOrExport`), so there is always a measurement to build.

**Export Spectrum** (the image) holds one chart, not both. From the saved list a multi-tap measurement's image is the
averaged spectrum; from the main view it is the chart on screen — the taps while the Taps view is on — in all three
editions. Decision (owner, 2026-10-25): the same from both places — the averaged spectrum. The purpose of a multi-tap
measurement is its averaged spectrum; the taps are secondary, and are on the PDF's page 2. So Export Spectrum from the
main view, in all three editions, is built from the measurement, as the saved list's (Swift
`renderSpectrumImageForMeasurement` / `renderSpectrumImageForComparison`, and each edition's equivalents). The
manual's Export Spectrum entry says so in one line.

**Peak Min in the saved list's exports.** A saved guitar measurement keeps all its peaks and its Peak Min. On screen
it shows the selected peaks at or above its Peak Min; the saved list's builders (Swift
`PDFReportData.from(measurement:)` / `renderSpectrumImageForMeasurement`, the web's `savedGuitar`, Python's
equivalents) show every selected peak in range, ignoring Peak Min — so a selected peak below Peak Min appears in the
saved list's PDF and image but not on screen, nor in Swift's and Python's main-view exports (the web's main view
already uses the saved builder). Shown with a copy of `dws-2024-umik-1-swift-mac-1785359434` at Peak Min −60 dB: the
saved-list PDF lists and labels Air at −64.2 dB. Decision (owner, 2026-10-25): the export matches the screen — a user
who set Peak Min to hide selected peaks meant it, so a guitar measurement's PDF and image show only the selected peaks
at or above its Peak Min, from either place, in all three editions. A measurement saved without a Peak Min shows all
its selected peaks.

**The Detected Peaks Summary in the image.** Its tiles are the first 8 of the annotated peaks, re-sorted by frequency
(Swift `makeExportableSpectrumView`, from the first export, `87a7410`, 2026-02-08, before peak selection and the
report's table existed) — so with annotations on All it drops selected peaks (owner's iPad export
`dws-2024-umik-1-3-tap-swift-ipad-1792974780`: Air and Ring Mode missing from the tiles, in the table). Decision (owner,
2026-10-25): the summary lists the same peaks as the report's Detected Peaks table — the selected peaks at or above
Peak Min in the range — whatever the annotation setting. What each part of an export shows, and what it is called,
is set out in the next section.

## Peaks in an export: terms and what each part shows

A guitar measurement's peaks fall into these sets. Each term below means exactly this set and nothing else.

| Term | The peaks | Limits |
|---|---|---|
| **Detected peaks** | every peak identified as a peak | at or above Peak Min; over the whole spectrum |
| **Selected peaks** | the detected peaks chosen to represent a specific mode (Air, Top, Back, Dipole, Ring Mode …) | a subset of the detected peaks |
| **In view** | (of any set) the peaks whose frequency is within the chart's range | the range on screen, or the range saved with the measurement |
| **Annotated peaks** | the peaks the chart draws an annotation card for: the detected peaks with the annotation setting on All, the selected peaks on Selected, none on None; peaks of unknown mode are left out while Show Unknown Modes is off | over the whole spectrum (a card whose peak is out of view is not drawn) |

A plate or brace has only selected peaks and annotated peaks: its identified fL (brace), or fL and fC, and fLC when
measured (plate) — a number fixed by the measurement's settings. It has no other detected peaks to count or list.

What each part of an export shows — decided (owner, 2026-10-25), in all three editions:

| Part | Guitar | Plate or brace | Shown before |
|---|---|---|---|
| The chart's annotation cards | the annotated peaks in view | the annotated peaks (fL, fC, fLC) | the same |
| "Detected Peaks: N" under the image's header | the number of detected peaks in view | no line | the number of annotated peaks over the whole spectrum, on a guitar; "Comparing N measurements" on a plate or brace, whose phases are overlaid curves |
| The summary under the chart, titled **"Selected Peaks Summary"** | the selected peaks in view, whatever the annotation setting | fL, fC, fLC | titled "Detected Peaks Summary" |
| The PDF's table, titled **"Selected Peaks"** | the selected peaks in view; with none, "No selected peaks in view." | fL, fC, fLC | titled "Detected Peaks"; with none, "No peaks detected in this measurement." |

A comparison's image keeps "Comparing N measurements", and its report its "Peak Mode Comparison" table. On screen, the
Analysis Results list's "No peaks detected in visible range" already means the detected peaks in view, and stays.
The User Manual's §7.6 and §7.7 say the same.

One name for the selected peaks everywhere (owner, 2026-10-25): the Measurement Details dialog's "Identified Peaks"
(the selected peaks, in all three) is **"Selected Peaks"**, and the User Manual's plate and brace chapters (ch04, ch05)
call the Results panel's fL / fC / fLC list the Selected Peaks (the app gives that list no title).

**Shown by** the owner's Swift exports of `dws-2024-umik-1-3-tap-swift-mac-1785359425` (build 653, 2026-10-25), the
same measurement three ways:

| Export | Range | Peak Min | Annotations | Header count | Annotated peaks in view | Summary and table |
|---|---|---|---|---|---|---|
| as saved | 1–501 Hz | −78 dB | All | 46 — every detected peak, those above 501 Hz included | the detected peaks below 501 Hz | Air, Top, Back, Dipole 320.4, Dipole 409.4 (Ring Mode, selected, is out of view) |
| "Min" | 1–501 Hz | −58 dB | All | 4 — Top 173.4, Top 197.4, Back 239.6, Dipole 409.4 | the same 4 | Top, Back, Dipole 409.4 (Air and Dipole 320.4 below Peak Min; Top 173.4 not selected) |
| "Pan" | 595 Hz–1.1 kHz | −58 dB | All | 4 — the same 4, all out of view | none | none: the summary is left out; the table reads "No peaks detected in this measurement." |

The "Pan" export shows the count is over the whole spectrum: 4, with none of the 4 in view. Python's export of
`annotation-override-1790037028` (71–346 Hz, Peak Min −77 dB) counts the same way: 33 with All (12 in view), 6 with
Selected (4 in view, the 4 its table lists).

## Plan

1. The rename and the comments, in all three editions (no behaviour change).
2. D1: Python's screen draws its overlaid curves from `overlay_spectra()`.
3. Python's overlaid curves drawn from `drawn_indices` for the visible range and re-trimmed when it changes, their full
   spectra kept beside them; the crosshair snaps from the full spectra.
4. Python's export chart draws every series and the spectrum line from `drawn_indices`, as Swift's `seriesData`.
5. Every export from the main view built from the measurement through Saved Measurements' builders, in all three; those
   builders apply the measurement's Peak Min; the export's peaks as set out in "Peaks in an export"; one name, Selected
   Peaks; the User Manual.
6. Tests, and the resize timing measured again.
7. Run-review (below).
8. Swift's unit tests and its export UI tests (they take over the mouse and keyboard); Swift's exports re-minted into
   the export check, and Python's and the web's checked against them.
9. Release notes, reviewed by the owner before committing.

## Built

- **The rename** (all three): `materialSpectra` → `overlaySpectra` and `materialSpectraContent` →
  `overlaySpectraContent` (Swift); `overlays` → `overlaySpectra`, `SpectrumOverlay` → `OverlaySpectrum` (web);
  `_chart_overlay_spectra` → `overlay_spectra`, `material_spectra` → `overlay_spectra`, `_comparison_curves` →
  `_overlay_curves` (Python); the comments listed above corrected.
- **D1** (Python): the analyzer's `longitudinal_spectrum`, `cross_spectrum` and `flc_spectrum` are properties that emit
  `phaseSpectraChanged`, Swift's `@Published`; the view hands `overlay_spectra()` to `FftCanvas.set_overlay_spectra`
  when the comparison, the display mode, a phase spectrum or the measurement type changes. `_material_spectra`,
  `set_material_spectra`, `materialSpectraChanged`, `load_material_spectra`, `_render_comparison_curves`,
  `_clear_comparison_view` and `_has_material_spectra` are gone; the spectrum line hides in a comparison or while a
  material phase is reviewed, as Swift's.
- **The overlaid curves** (Python): `set_overlay_spectra` keeps each whole spectrum (`_overlay_spectra`) beside its plot
  item, which `_draw_overlay_curves` gives only the drawn points, again on every range change; the crosshair reads
  `_overlay_spectra`. Measured: 1,605,640 points and 1434 ms per resize before, 20,223 points and 74 ms after.
- **The export chart** (Python): `series_data` / `chart_data` are `drawn_indices`, and draw every curve; its labels and
  colours use the measurement's own modes (`peak_mode_map`), as Swift's `peakModeMap`.
- **Exports from the main view** (all three): built from the measurement as it would be saved, with the displayed
  range — Swift `currentMeasurement()` → `PDFReportGenerator.report(for:)` and the saved image builders; Python
  `current_measurement()` → `export_report_for_measurement` and the same; the web's Export Spectrum through
  `measurementToImageOpts`. A comparison's is `makeComparisonMeasurement` (Swift) / `make_comparison_measurement`
  (Python), split out of saving one. Swift's `createAveragedSpectrumView` and `createExportableSpectrumView`, Python's
  `_on_export_comparison_pdf`, `_on_export_multi_tap_pdf` and `_create_exportable_spectrum_view` are gone.
- **Peaks in an export** (all three): the measurement's `peaksAbovePeakMin`, `detectedPeaksInView` and `reportPeaks`
  (Python `peaks_above_peak_min`, `detected_peaks_in_view`, `report_peaks`; web `measurementPeaksAbovePeakMin`,
  `measurementDetectedPeaksInView`, `measurementReportPeaks`) give the annotation cards, the header's count and the
  Selected Peaks Summary and table, as set out above; "Selected Peaks" in the reports and in Measurement Details.
- **The image's header line** (Swift): a plate or brace export has no count line but keeps its height, as Python's and
  the web's did (owner, 2026-10-25), so every export's header is the same height and its chart in the same place.
- **The User Manual**: §7.6, §7.7, Appendix B and the plate and brace chapters (ch04, ch05).
- **Tests:** `test/export-peaks` (shared cases `export-peaks.json`, Swift `ExportPeaksTests`, Python
  `test_export_peaks.py`, web `export-peaks.test.ts`, linked from `model/export-peaks`); `test/export-e2e` gains, in
  all three, the main window's image equal to Saved Measurements' for every case, and a multi-tap measurement's image
  the same with the Taps view on and off; Python's `test_overlay_curves.py` (the curves hold the drawn points and are
  re-trimmed); the PDF text baselines read "Selected Peaks". Swift's UI test compares two images as the same picture
  (each channel within 1: its renderer is not bit-exact between runs); Python's and the web's compare bytes. Swift's
  unit tests (307) and export UI tests (7) pass. The export check's expected values are minted again from Swift's
  exports (24); Swift, Python and the web each pass.
- **Found in the run-review** (Python):
  - With a comparison ended by a change to Plate or Brace, the Results panel showed the empty guitar peak list ("No
    peaks detected in visible range") over the plate's list, pushing it to the bottom; the guitar list now shows for a
    guitar only (`test_results_panel_lists.py`).
  - Every export with a legend printed `qt.widgets.styles.macos: drawControl: QStyle::CE_ShapedFrame invalid (nullptr)
    graphics context`, two per legend entry: the macOS style has no graphics context for a frame drawn into an image.
    The export draws its legend in the Fusion style; the images are byte-identical.
- **Found in the run-review** (Swift): clicking a peak's star in Analysis Results selected it — its card appeared on
  the chart — but the star stayed empty until anything on the analyzer itself changed (a row click, hiding the
  window). The selection is in `DetectedPeaks`; the panel's `PeaksReader` redrew, but the rows sit in the
  `ScrollViewReader`'s closure, which that redraw does not run again (shown with temporary `gtLog`s). The rows are
  built inside their own `PeaksReader` (`peaksAndModesSection`). Python and the web do not have it (owner).

## Run-review

Every edition: Swift on macOS; Python; the web, unless a step names one.

- **Passed in every edition** (owner, 2026-10-25): Swift on macOS, Python and the web.

1. Python: import hub `Tests/compare-49-1792949383.guitartap` and resize the window. → It follows the window smoothly;
   the curves look as before.
2. Python: zoom and pan that comparison. → Every curve redraws for the new range and reaches both edges of the plot.
3. Python: move the pointer over the curves. → The crosshair follows the nearest curve, in its colour.
4. Python: tap a plate (or play a plate file) through fL, fC and fLC, with a Redo. → Each phase's curve appears; the
   live line hides while a phase is reviewed and returns after Redo or Accept.
5. Load `dws-2024-umik-1-3-tap-swift-mac-1785359425`, turn the Taps view on, Export PDF Report from the main window. →
   Page 1 is the averaged spectrum, page 2 the taps.
6. With the Taps view still on, Export Spectrum. → The averaged spectrum, the same image as the row's Export Spectrum
   in Saved Measurements.
7. Import `peak-min-test-60.guitartap` (Peak Min −60 dB) and load it. → No Air label on the chart. Export PDF Report
   from the main window and from Saved Measurements. → Neither lists, labels or summarises Air.
8. Load a guitar measurement, annotations All, Export PDF Report. → The header reads "Detected Peaks: N", the peaks at
   or above Peak Min in the chart's range; the summary under the chart is titled "Selected Peaks Summary" and the table
   "Selected Peaks", both listing the selected peaks in view.
9. The same with annotations Selected, then None. → The chart's cards follow the setting (the selected peaks; none);
   the count, the summary and the table are the same as with All.
10. Pan the chart off every peak (as the "Pan" export: 595 Hz–1.1 kHz at Peak Min −58 dB) and Export PDF Report. →
    "Detected Peaks: 0", no summary, and the table reads "No selected peaks in view."
11. Export PDF Report of a plate and a brace. → No count line under the header; "Selected Peaks Summary" and "Selected
    Peaks" list fL, fC (and fLC), or fL.
12. Export Spectrum and Export PDF Report of a comparison, from both places. → "Comparing N measurements" and the Peak
    Mode Comparison table, as before.
13. Open View Details for any measurement in Saved Measurements. → Its peak list is titled "Selected Peaks".
14. Python: load a comparison, then switch the measurement type to Plate. → The Results panel shows only the plate's
    fL / fC / fLC rows, at its top.
15. Python: Export Spectrum of a plate and of a comparison, run from a terminal. → No `CE_ShapedFrame` messages.
16. Swift: load a guitar measurement and click an unselected peak's star in Analysis Results, then click it again. →
    The star fills, then empties, at once.
