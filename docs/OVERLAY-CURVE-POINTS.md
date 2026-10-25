# Overlaid curves: Python draws every point

**Issue:** [#45](https://github.com/dwsdolce/guitar-tap-project/issues/45)

Status: **OPEN — cause found and measured; fix not started.**

## The problem

Resizing the window with a large comparison loaded is very slow in Python: with a 49-measurement comparison, about
1.6 s per resize (owner, 2026-10-25, during #43's run-review). Panning and zooming redraw the same curves.

## What each edition draws

An overlaid curve is a comparison's measurement, a multi-tap measurement's tap, or a plate's or brace's phase. Each
spectrum holds 32,768 points; a chart shows a few hundred of them.

| | The spectrum line | Overlaid curves |
|---|---|---|
| Swift | `DisplayRange.drawnIndices(of:min:max:)`: the points in the visible range and one beyond each edge (`chartData`) | the same (`materialSpectra` series; both export charts) |
| Web | `drawnIndices` inside `drawCurve` | the same (`drawCurve` draws every curve) |
| Python | `drawn_indices` (`FftCanvas._draw_spectrum`), re-trimmed when the range changes | **every point**: `_render_comparison_curves` and `load_material_spectra` hand pyqtgraph the whole spectrum |

## Measured

The 49-measurement comparison in a 1200 × 700 chart at 60–360 Hz, offscreen, 20 resizes:

| Overlaid curves | Points drawn | Per resize |
|---|---|---|
| every point (Python now) | 1,605,640 | 1556 ms |
| trimmed with `drawn_indices` | 20,223 | 100 ms |

The legend (#43) makes no difference: 1559 ms without it, 1571 ms with it.

## Plan

1. Python's overlaid curves drawn from `drawn_indices` for the visible range and re-trimmed when the range changes,
   as its spectrum line is and as Swift's and the web's curves are: comparison curves, tap curves and material
   phases. The crosshair's snap reads the full spectra, not the drawn points — to check it still does.
2. A test of the trimmed overlay data, alongside Python's spectrum-line case.
3. Run-review: resizing, panning and zooming a large comparison and a plate in Python; the curves unchanged on screen.
