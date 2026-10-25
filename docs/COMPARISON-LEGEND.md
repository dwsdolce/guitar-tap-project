# The chart legend when a comparison has many measurements

**Issue:** [#43](https://github.com/dwsdolce/guitar-tap-project/issues/43)

Status: **OPEN — found 2026-10-24, nothing changed yet; decisions to be made.**

## The problem

A comparison measurement has no limit on how many measurements it holds (36 have been compared). The chart draws a
legend entry for each, and past a few dozen the legend no longer fits:

| | On screen | Exported spectrum image / PDF |
|---|---|---|
| Swift | the legend wraps onto more lines as entries are added (fine at 3, 5 and 6); at 26 it breaks the chart's layout — the chart spreads under the Results panel, its curves and labels wash out, and the legend shows as a row of coloured dashes | a "Measurements:" row under the chart (fine at 6); the PDF embeds that image and also lists every spectrum in its Peak Mode Comparison table |
| Python | one row that runs off the chart's left edge (36: the first visible entry is cut to "Mac (2)") | not yet checked with many |
| Web | **handles it reasonably**: the legend wraps onto as many lines as it needs, right-aligned above the plot, and the plot shrinks to fit below it (9 measurements: three lines, every name in full) | not yet checked with many |

A multi-tap guitar measurement's legend (Tap 1 … Tap N, Averaged) has short labels and a limited number of taps; 8
taps and the average fit.

## The questions (the owner's, 2026-10-24 — to decide)

1. **On screen:** is the chart's legend needed while the Results panel's comparison table lists every spectrum with
   its colour?
2. **The comparison table:** the same question for it (it is the list the legend duplicates).
3. **The PDF:** the legend is not required — the report's table lists every spectrum or tap.
4. **The exported spectrum image:** the legend is useful there (the image travels alone), but not practical for a
   large comparison — what should it do then?
5. **A multi-tap measurement:** its legend fits (short labels, a limited number of taps) — whether it changes with
   the rest.

Whatever is decided applies to all three editions.

## Plan

1. Check the exports (Python's, the web's) with a large comparison; record here. The web's on-screen legend is a
   candidate model for the others.
2. The owner decides 1–5.
3. Build in all three, test, run-review.
