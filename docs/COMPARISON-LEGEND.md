# The chart legend when a comparison has many measurements

**Issue:** [#43](https://github.com/dwsdolce/guitar-tap-project/issues/43)

Status: **OPEN — built in all three editions (Swift `80b458e`, Python `b8943c6`, web `e64f9f4`); run-review passed in every edition; the export check passes in every edition; release notes in each; CI to check.**

## The problem

A comparison measurement has no limit on how many measurements it holds (36 have been compared). The chart draws a
legend entry for each, and past a few dozen the legend no longer fits:

| | On screen | Exported spectrum image / PDF |
|---|---|---|
| Swift | the legend wraps onto more lines as entries are added (fine at 3, 5 and 6); at 26 it breaks the chart's layout — the chart spreads under the Results panel, its curves and labels wash out, and the legend shows as a row of coloured dashes | a "Measurements:" row under the chart; the image widens to hold it (18 measurements: 7580 px wide instead of 2928, the plot its usual size at the left and the rest empty, every name tiny); the PDF scales that image to the page width, so the chart cannot be read |
| Python | one row that runs off the chart's left edge (36: the first visible entry is cut to "Mac (2)") | a "Measurements:" row under the chart, the image its usual size; only the names that fit whole are drawn (18 measurements: 7 drawn, 11 missing); the PDF embeds the same image |
| Web | **handles it reasonably**: the legend, in the plot's upper-right corner over the curves, wraps onto as many lines as it needs, right-aligned; the plot keeps its size, so each line covers more of its top (9 measurements: three lines, every name in full) | a "Measurements:" row under the chart, the image its usual size, cut at the right edge (18 measurements: the seventh name cut, 11 missing); the PDF embeds the same image |

A multi-tap guitar measurement's legend (Tap 1 … Tap N, Averaged) has short labels and a limited number of taps; 8
taps and the average fit.

## Decisions (owner, 2026-10-25)

- **On screen, the web's wrapping legend is the model:** in the plot's upper-right corner, over the curves, it
  wraps onto as many lines as it needs, right-aligned. Comparisons of 18 measurements read well (four lines, every
  name in full).
- **The plot keeps its size** (owner, 2026-10-25, chosen over the plot making room): the legend covers more of the
  plot's top as it grows — usually empty space. No height cap; the practical limit on measurements in a comparison
  is far below 36.
- **Colours repeating** past the palette's length is not a new problem (comparison measurements and comparison
  tables alike) — no change.
- **The exported image matches the screen:** the same wrapping legend in the plot's upper-right corner; no
  "Measurements:" row under the plot. The PDF embeds that image.
- **The legend is an overlay in every edition** (owner, 2026-10-25): drawn last, over the peak labels, mode labels
  and crosshair readout, laid out in the plot's frame. Consistency and stability over draw order: Python's legend
  has been a widget over the chart since it took Swift's appearance, which pyqtgraph's own legend cannot give.
- **One mechanism in every edition** (owner, 2026-10-25): each edition has one legend whose lines are broken by
  the same function as Swift's `TrailingFlowLayout` — Python `views/chart_legend.py`, web
  `presentation/chartLegend.ts` — used on screen and in the exported image; the web's CSS wrapping is replaced, not
  kept, though its result is the same.
- **The names may break onto different lines in different editions** (owner, 2026-10-25): each system's font sets
  the names at its own width — Qt's macOS system font about 9% narrower than SwiftUI's (the 18-compare legend
  5, 5, 6, 2 entries a line in Python, 5, 4, 5, 4 in Swift and the web), Segoe UI on Windows, Liberation Sans in
  Python's Linux export, the browser's own font on the web. The layout rules are the same everywhere; one shipped
  font in every edition is not worth it. The export check compares the entries exactly and the lines within one.
- The PDF needs no legend of its own: its Peak Mode Comparison table lists every spectrum with its colour.

## Plan

1. Exports checked in all three editions with the comparison in `Tests/18-compare-1792944381.guitartap` (spectrum
   image and PDF from each): recorded above.
2. Before more legend work, the PDFs' Frequency Range is fixed. The rule (owner, 2026-10-25): a chart has one
   range, and every export of it uses that range.
   - A comparison measurement: the chart, its image and its PDF's Frequency Range use the comparison's range — the
     view on screen, or the range saved with it; only a comparison saved before comparisons kept their range spans
     its measurements. Swift and Python printed the span of the measurements (64.1 Hz – 350.0 Hz for the 18-compare
     file, saved at 63.8 Hz – 350.1 Hz); the web printed the saved range.
   - A multi-tap measurement's tap comparison (page 2 of its PDF) uses the measurement's own range, as on screen;
     all three spanned the taps' spectra.
   - The span of the compared measurements is named `comparedSpan` (Python `compared_span`): a new comparison's
     opening range and the target of the chart menu's "Reset … to Comparison Range", in no export.
   - The 18-compare file is a `test/pdf-report` fixture in all three editions.

   The text styles were not a difference: all three PDFs set the labels and headings in Helvetica-Bold, as the
   export check measures; a renderer without the unembedded bold face drew Python's and the web's as regular.
3. Swift first (on screen and the exported image); the owner tests it before Python and the web.
4. Python and the web; the 18-compare case's expected lines taken again from Swift; the export check gains the
   18-compare case; test, run-review.

## Built

- **Swift's legend** (`Views/ChartLegend.swift`): one legend for the screen and the exported image, placed last in
  the chart's overlay by `placed(in:inset:)` — the plot's frame, its upper-right corner 8 in (10 in the export), so
  it never crosses the axes, ignoring the pointer. Its entries wrap onto right-aligned lines with the web's spacing
  (12 between entries, 4 between lines); the exported image draws it in its own larger sizes. The "Measurements:"
  row under the exported plot is gone; the "Guitar Modes:" key under a single guitar measurement's export stays.
- **Python's legend** (`views/chart_legend.py`): `ChartLegend`, a widget laid out by `TrailingFlowLayout` (a Qt
  layout whose lines come from `legend_lines`, Swift's `lines`), sizes in points with a `scale` (the export's 2,
  Swift's `ImageRenderer(scale: 2.0)`). On screen it is placed in the plot area 8 in from its upper-right corner, and
  re-placed whenever the plot resizes, a widget over the chart; the exported chart (`ExportableSpectrumChart.render`)
  draws the same widget last, in its plot, 10 in, in the export's sizes.
- **The web's legend** (`presentation/chartLegend.ts`): `legendLines` (Swift's `lines`) and `drawChartLegend`
  (`sizeThatFits` then `placeSubviews`), drawn by the chart renderer (`renderSpectrum`) in the plot area for the
  screen (8 in) and the export (10 in, the export's sizes), last, over the labels and crosshair. The HTML legend and
  its CSS are gone.
- **The export check** (`tooling/export-check/`) finds a legend inside the plot from its entries' 22 × 3 pt lines
  (a bar a line's height below the last is a piece of curve, left out) and compares its top, its entries exactly,
  its lines within `legend_lines` (1) and that it never reaches past the plot's left edge; a single guitar
  measurement's mode key is measured under the chart as before. The 18-compare file is its `large-comparison` case
  in every edition. Expected values minted from Swift's run; Swift, Python and the web each pass, 24 exports.
- **The line breaking is tested from shared cases:** `chart-legend.json` (`test/chart-legend`, CL1–CL8: one line, an
  exact fit, one point over, an entry wider than the width in the middle and first, several lines, no spacing,
  nothing to lay out) in Swift `ChartLegendTests`, Python `test_chart_legend.py` and the web's
  `chart-legend.test.ts`, linked from each legend file (`tests=test/chart-legend`). Mutation: a line breaking when
  the next entry exactly fits (`>=`) fails CL2 and CL7 in all three.
- **Plate and brace** use the same legend for Longitudinal, Cross-grain and Diagonal, so their screen and exported
  image change the same way.
- **The PDF fixtures move:** every comparison, multi-tap, plate and brace fixture's lines sit higher (the image is
  61 pt shorter without the row), taken again from Swift and copied to Python and the web; the shared
  `spectrum-export.json` sizes: a plate 2254 px high, a comparison 2016.

## Run-review

Every edition: Swift on macOS, iPad and iPhone; Python; the web — Python and the web beside Swift on the Mac with the
same measurements loaded.

- **Swift: passed** on macOS, iPad and iPhone (owner, 2026-10-25). The 18-compare legend fits on every device; a
  49-measurement comparison fits on all but the iPad in landscape, where the legend runs below the plot and is cut
  off — expected, nothing to do. With the legend as an overlay, steps 6 and 7 passed again on macOS, iPad and
  iPhone (owner, 2026-10-25): the legend draws over the labels and crosshair.
- **Python: passed** (owner, 2026-10-25).
- **Web: passed** (owner, 2026-10-25).

1. Load the 18-compare comparison. → The legend is in the plot's upper-right corner, wrapping onto about four
   right-aligned lines, every name in full. The chart keeps its size.
2. Make the window narrower and wider, with the comparison loaded and with a live comparison of the same
   measurements. → The legend re-wraps at every width; no line reaches past the plot's left edge onto the dB labels
   or runs off the chart's left edge; nothing pushes the chart out of shape.
3. Compare 26 or more measurements. → The legend wraps, and the chart keeps its layout beside the Results panel.
4. Export Spectrum from the 18-compare comparison. → The legend is inside the plot's corner, as on screen, with no
   "Measurements:" row under the plot. The image is its normal width. Python's and the web's names break onto the
   same lines as Swift's export, except where the font differs.
5. Export PDF Report from it. → The chart is full width and readable. "Frequency Range" reads 63.8 Hz – 350.1 Hz.
6. Load a plate measurement, then export its spectrum. → The three phases' legend is in the corner on screen and in
   the image, with no row under the plot; the legend draws over a peak label or the crosshair readout in the corner.
7. Load a multi-tap measurement, turn on its tap comparison, then export the PDF. → The taps' legend is in the
   corner. Page 2's "Frequency Range" matches page 1's.
