# Lists that scroll more than their items

**Issue:** [#39](https://github.com/dwsdolce/guitar-tap-project/issues/39)

Status: **OPEN — found 2026-10-23, nothing changed yet.** To be worked after #9 (sort, filter and delete).

## The rule

Style guide **S8** (`process/STYLE-GUIDE.md` § 1.4): a list scrolls only its items. Everything that is not an item —
a total or count, a filter line, a notice, column headers, actions — sits fixed above or below it and never scrolls.
Saved Measurements follows it in all three editions (#9). A check of every other scrolling list (2026-10-23) found the
items below. Where the editions differ, Python is right on items 1, 2 and 4.

## Findings

| # | Where | Swift | Python | Web | Status |
|---|---|---|---|---|---|
| 1 | Comparison results: the column-header row (Spectrum / Air / Top / Back) | scrolls | fixed | scrolls | open |
| 2 | Multi-tap comparison: the column-header row | scrolls | fixed | scrolls | open |
| 3 | Multi-tap comparison: the "Averaged" row (a total, not a tap) | scrolls | scrolls | scrolls | open — decide whether it is a total |
| 4 | Analysis Results: "No peaks detected in visible range" | in the scroll | fixed above the list | in the scroll | open |
| 5 | Plate / brace results: peaks share one scroll with the dimension editors, Gore, the properties and the Measurement Process instructions | scrolls | scrolls | scrolls | open — decide: a results page, or a list with fixed sections |
| 6 | Measurement Details: the whole page scrolls (Measurement Info, section titles, "No identified peaks"); only Done is fixed | scrolls | scrolls | scrolls | open — decide |
| 7 | The chart's ⓘ help: its title scrolls with the lines | scrolls | scrolls | scrolls | open — decide whether it is a list |
| 8 | Web, a window ≤ 820 px wide (not a phone): the Analysis Results panel stops scrolling internally, so header, peaks and footer scroll together | — | — | S8 lost at that width | open |
| 9 | Swift, phone landscape: hides the mic / Re-analyze row and the Ring-Out / Tap Ratio box; the other editions have no equivalent | differs | — | — | open — decide |

### Where each is

1. Swift `Views/ComparisonResultsView.swift:27` (`headerRow`); web `components/ComparisonResultsView.tsx:24` (`.mt-head`,
   not sticky); Python `views/comparison_results_view.py:100–101` (a `QTableWidget`, its header a `QHeaderView`).
2. Swift `Views/MultiTapComparisonResultsView.swift:43`; web `components/MultiTapComparisonResultsView.tsx:76`; Python
   `views/multi_tap_comparison_results_view.py:94`.
3. Swift `MultiTapComparisonResultsView.swift:62–70`; Python `multi_tap_comparison_results_view.py:133–163` (a table row);
   web `MultiTapComparisonResultsView.tsx:91` (`.mt-avg`).
4. Swift `Views/TapAnalysisResultsView.swift:509` (inside the `ScrollView` at 280); web `App.tsx:1305` (`.results-empty`,
   inside `.results-scroll`); Python `views/shared/peak_card_widget.py:577–582` (outside its `QScrollArea`).
5. Swift `TapAnalysisResultsView.swift:280–321` (the comment at 278–279 says the properties scroll because they can be
   tall); Python `views/tap_tone_analysis_view.py:1650–1669` (`_material_scroll`); web `components/MaterialResults.tsx`
   inside `.results-scroll`.
6. Swift `Views/Measurements/MeasurementDetailView.swift:75`; Python `views/measurements/measurement_detail_view.py:63`
   (its comparison table a `QTableWidget` inside the page's `QScrollArea`); web `components/MeasurementDetail.tsx:84`.
7. Swift `Views/SpectrumView.swift:1256–1264`; Python `views/fft_canvas.py:70–88`; web `components/SpectrumChart.tsx:649–650`.
8. Web `App.css` (the ≤ 820 px rules for `.results-pane` / `.results-inner`); the phone bottom sheet keeps its internal
   scroll.
9. Swift `TapAnalysisResultsView.swift:190`, `:354`.

Not lists, so outside the rule: Settings' device and calibration choices (menu pickers in all three); Settings and
FFT Metrics (forms); the Quick Start Guide and release notes (documents — the web's and Swift's section titles stay
pinned; Python's, in a text browser, scroll).
