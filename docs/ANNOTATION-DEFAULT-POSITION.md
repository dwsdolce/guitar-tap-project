# Annotation default position — where an untouched label sits, how it behaves under zoom, and how labels are clipped

**Issue:** [#25](https://github.com/dwsdolce/guitar-tap-project/issues/25)

Status: **ANALYSIS — direction agreed in outline, details open, nothing implemented.** Opened 2026-10-01.
Cross-platform: Swift + Python + web together (and inherited by the Android port).

Found at the #17 F55 run-review (display range), owner, 2026-10-01: with the same measurement loaded, the peak
labels sat at different heights above their peaks in Python and the web. Moved here because it is not a
display-range question and has more to settle than F55 could.

## What each edition does today

A label the user has not dragged ("untouched") is placed by a default rule; a dragged label is stored.

| | Untouched label | Measured from | Units |
|---|---|---|---|
| Swift (`PeakAnnotations.swift`, `calculateChartPosition`) | 70 pt above the peak | the label's centre (`.position`); the connecting line runs to centre + 30, the bottom of a ~60 pt label | screen points, recomputed on every render |
| Python (`views/peak_annotations.py`, `_LABEL_OFFSET_DB = 14.0`) | 14 dB above the peak | the label's centre (`anchor=(0.5, 0.5)`) | chart units (dB) |
| web (`presentation/spectrumRender.ts`, badge anchor) | 10 px above the peak dot | the label's bottom edge | screen pixels |

So the three disagree on the distance, on the point of the label it is measured to, and on the units. On screen:
Swift's sits well clear of the peak at any zoom; Python's distance changes with the dB range and the chart's height
(on a narrow dB axis it is far above the peak, or off the chart); the web's sits just above the dot.

A dragged label is stored in **absolute chart units** (Hz, dB) in all three, and saved in the measurement file.

## The coordinate problem (owner, 2026-10-01)

In Swift, a label changes coordinate system when it is dragged: untouched, it keeps a fixed screen distance from its
peak under zoom; dragged, it is tied to its chart position, so zooming scales its distance from the peak. "Interesting
problem."

**Constraint (owner):** how dragged labels are stored does not change — "It works fine the way it is." Only how the
untouched position is set and used is in question.

## Options for the untouched position

1. **Screen distance, recomputed on every render** (Swift today). Readable at any zoom, but behaves differently from a
   dragged label.
2. **Chart-unit offset from the peak** (Python today). Behaves like a dragged label under zoom, but no single dB offset
   suits every range.
3. **Set once on screen, then held in chart units.** When the label is first drawn, place it a fixed screen gap above
   the peak, convert that to Hz / dB, and from then on use it exactly like a dragged label (without saving it).
   Untouched and dragged labels then behave the same under zoom; the only difference is who chose the spot.

**Front-runner: option 3** (owner, 2026-10-01: "That seems to make more sense. Offset on the screen a fixed amount and
then zoom like an annotation works").

### Option 3 — draft definition, to settle

- **Set:** the first time a peak's label is drawn — a fixed screen gap above the dot, converted at once to Hz / dB and
  held for that peak.
- **Set again:** when the peaks are replaced — New Tap, a load, Re-analyze, a new plate / brace phase. Not on zoom,
  pan, Settings or a widening.
- **Not saved.** Only dragged labels are written to the file, as now. A load restores the measurement's saved chart
  range, so on the same window size an untouched label is set again where it was.
- **Reset Position** sets it again from the current view.
- **"Moved"** compares against the held default (as Python's `_default_pos` does today).
- **Exports** use the held Hz / dB, as for dragged labels.

## Open questions

- **The gap**, and what it is measured to. Measuring from the dot to the label's **bottom edge** makes labels of
  different sizes (fonts, line counts) look alike across editions; about 40 px matches Swift's current look, if
  Swift's label is ~60 pt tall (to be measured).
- **Where the held defaults live** — display state that is never saved; beside the dragged offsets on the analyzer but
  kept apart from them, the same in all three?
- **Order with a widening.** A newly identified plate / brace peak widens the chart; the label must be set after the
  widening, or it is set on the narrow view.
- **Zooming in pushes an untouched label off the chart**, as it does a dragged one today — accepted with option 3?
- **"First drawn" when hidden.** A label hidden by the annotation mode and shown later — set when first shown, or when
  the peak appears?
- **Clipping — a label whose peak is off the chart:** drawn or not? *(Waits on the untouched position — see
  Clipping.)*
- **Clipping — past the plot area:** may a label extend beyond the plot, or is it clipped at the plot's edges?
  *(Waits on the untouched position.)*
- **Clipping — kept inside:** is an untouched label moved to stay inside the plot, and is a dragged label treated the
  same? *(Waits on the untouched position.)*

## Clipping — how a label meets the chart's edges (owner, 2026-10-01)

Labels are clipped very differently in the three editions. Settled **after** the untouched position: what a label
should do at an edge depends on which coordinates it is held in, so clipping cannot be designed until that is.

What each edition does today (from the code; to be checked in full when this is taken up):

- **Swift** (`SpectrumView.visiblePeaks`, `PeakAnnotations`): a label is drawn for a peak inside the chart's frequency
  range; the labels are an overlay on the chart and are not clipped to the plot area.
- **web** (`spectrumRender.ts`, `drawBadge`): a label is drawn for a peak inside the frequency range and above the
  bottom of the dB range, after the plot's clip is released, so it may overflow the plot. The box is held inside the
  plot horizontally; an auto-placed box that would cross the plot's top is moved down; a dragged box keeps its
  position.
- **Python** (`peak_annotations.py`): labels are pyqtgraph items in the plot (`plot_item.addItem`), so the view box
  clips them; which peaks get a label at the edges is to be confirmed.
