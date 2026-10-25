# Lists that scroll more than their items

**Issue:** [#39](https://github.com/dwsdolce/guitar-tap-project/issues/39)

Status: **✅ COMPLETE (2026-10-24).** Items 1, 2 and 4 built: Swift `21f94aa`, web `571c91d` (Python already did
them); the rest decided as no change or outside #39; run-review passed (owner); no release-notes entry (owner); CI
green. Style guide S8 extended (headings, empty messages, scrolled pages).

## The rule

Style guide **S8** (`process/STYLE-GUIDE.md` § 1.4): a list scrolls only its items. Everything that is not an item —
a total or count, a filter line, a notice, column headers, actions — sits fixed above or below it and never scrolls.
Saved Measurements follows it in all three editions (#9). A check of every other scrolling list (2026-10-23) found the
items below. Where the editions differ, Python is right on items 1, 2 and 4.

## Findings

| # | Where | Swift | Python | Web | Status |
|---|---|---|---|---|---|
| 1 | Comparison results: the column-header row (Spectrum / Air / Top / Back) | scrolls | fixed | scrolls | decided: fixed — only the rows scroll (owner, 2026-10-24) |
| 2 | Multi-tap comparison: the column-header row | scrolls | fixed | scrolls | decided: fixed — only the rows scroll (owner, 2026-10-24) |
| 3 | Multi-tap comparison: the "Averaged" row | scrolls | scrolls | scrolls | decided: scrolls with the taps — it is a row of the same kind (owner, 2026-10-24); no change |
| 4 | Analysis Results: "No peaks detected in visible range" | in the scroll | fixed above the list | in the scroll | decided: fixed above the list, as Python — it is not an item (owner, 2026-10-24); Swift and the web change |
| 5 | Plate / brace results: the peaks (2 or 3) share one scroll with the dimension editors, Gore, the properties and the Measurement Process instructions | scrolls | scrolls | scrolls | decided: no change — a scrolled page, not a scrollable list, so S8 does not apply (owner, 2026-10-24) |
| 6 | Measurement Details: the whole page scrolls (Measurement Info, notes, the identified peaks or the compared spectra); only Done is fixed | scrolls | scrolls | scrolls | decided: no change — a report, a scrolled page like 5, not a list of items to select; the same on every device (owner, 2026-10-24) |
| 7 | The chart's ⓘ help: its title scrolls with the lines | scrolls | scrolls | scrolls | decided: no change — it fits even on an iPhone in landscape, and would scroll as a whole only on a shorter screen (owner, 2026-10-24) |
| 8 | Web, a narrow window: the panel loses its internal scroll | — | — | see status | not a #39 finding (owner, 2026-10-24): the Results panel works as decided wherever the layout fits; below roughly 900–1,060 px the web's page does not fit the window (clipped on the right; stacked and overlapping under 820 px) — a web layout problem |
| 9 | Swift, phone landscape: hides the mic / Re-analyze row and the Ring-Out / Tap Ratio box | differs | — | — | not a #39 finding (owner, 2026-10-24): a deliberate design decision for the phone's landscape layout, not a question of scrolling |

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

## Built

Swift: `ComparisonResultsView` and `MultiTapComparisonResultsView` draw their heading and rows apart
(`ComparisonTablePart`); the Results panel puts the heading, or "No peaks detected in visible range", in a fixed
strip above its scroll (`fixedAboveList`). Measurement Details and exports draw the whole table, as before. Web: the
same (`part` on both tables; a fixed strip in `App` above `.results-scroll`). Python unchanged — it already did this.

## Run-review

On Swift (Mac, iPad, iPhone) and the web (computer, phone or tablet); Python for comparison.

1. Load a comparison measurement of many measurements, so its table overflows the Results panel; scroll the table.
   → The Spectrum / Air / Top / Back heading stays put; only the rows move.
2. Load a multi-tap guitar measurement and show its table of taps (Taps); make the panel short enough to scroll
   (an iPhone, or a short window); scroll. → The Tap / Air / Top / Back heading stays put; the taps and the
   Averaged row move.
3. Narrow the chart's range until no peak is in it. → "No peaks detected in visible range" sits just under the
   panel's header, as in Python.
4. Open Measurement Details for the same comparison. → The page scrolls as a whole, as before.

