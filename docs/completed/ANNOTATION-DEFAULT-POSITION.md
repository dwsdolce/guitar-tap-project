# Annotation default position — where an untouched label sits, how it behaves under zoom, and how labels are clipped

**Issue:** [#25](https://github.com/dwsdolce/guitar-tap-project/issues/25)

Status: ✅ **CLOSED 2026-10-22** — Swift `00e157c`, Python `e010e82`, web `b5d6766`. A peak label is a point in chart units: its centre where it was dragged, else at its peak + 14 dB (one constant per edition, checked against `annotation-state.json`); drawn whenever the annotation mode shows it, whatever the range; labels, their lines and the mode chips cut at the plot's edges and never moved inside; the line from the dot to the label's centre, under the label. Found and fixed on the way: Swift's label hit areas, the web's stored point (bottom edge → centre) and stacking order, Python's export (Swift's old rules, no Upper Modes) and chips, and Python's labels following the results list. Full suites passed in all three; run-review passed on every edition and platform (owner, 2026-10-22). Opened 2026-10-01.
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

## The untouched position — decided (owner, 2026-10-22)

**An untouched label's centre is a fixed distance from its peak in chart units:** centre = (peak Hz + Δf,
peak dB + ΔdB), with **ΔdB = 14 dB** and **Δf = 0 Hz** (the x part kept for later use).

Why chart units (owner): the position must not depend on anything but the peak.
- **Visibility:** cycling the annotation visibility never moves a label — nothing is computed from what is drawn.
- **Range and zoom alike:** changing the range in Settings and zooming do the same to an untouched label as to a
  dragged one. A screen-unit default would keep a fixed gap when the range changes but not under a dragged label's
  rules — two behaviours. A default set once on screen and then held in chart units would depend on the window's
  size, the range, the device and the edition at the moment it was set.
- **One value, the same everywhere:** the same file shows its labels at the same Hz / dB in every edition, on
  every device and window size, and in exports; nothing beyond the one offset is kept.

Consequences:
- A label is **moved** exactly when it has an entry in `peakAnnotationOffsets`; **Reset Position** removes the
  entry. No default positions are held, set again or saved.
- Measured to the label's **centre**, as dragged positions are stored, so the two compare directly.
- 14 dB looks like Swift's 70 pt on the owner's screen; Python already uses it (`_LABEL_OFFSET_DB`).
- **Overlap is accepted:** at a wide dB range a label can cover its own peak dot, as labels already can in every
  edition; no single value or rule prevents it, and a label is easily dragged. On a narrow range a label sits far
  above its peak or off the chart, as a dragged one does — what is shown at the edges is the clipping question
  below.
- **Defined once:** a constant on each edition's analyzer, beside the dragged positions
  (`TapToneAnalyzer.defaultAnnotationOffset`, Python `DEFAULT_ANNOTATION_OFFSET`, the web's
  `DEFAULT_ANNOTATION_OFFSET`), its value stated in the shared case file `annotation-state.json` (`labelOffset`)
  and checked by each edition's annotation-state test. Not a user setting.

What changes: Swift (70 pt on screen, recomputed every render) and the web (10 px to the label's bottom edge) move
to Python's rule; Python's constant joins the case file.

## Clipping — decided (owner, 2026-10-22): Python's rule

Python's labels do not move and do not disappear; Swift's and the web's do. Every label is a point in chart units,
drawn wherever it falls and cut at the plot's edges:

1. **A label whose peak is off the chart is drawn.** Which labels exist is decided by the annotation mode alone
   (All, Selected, None; none in a comparison) — Python's `_should_show_annotation` — never by the chart's range;
   a pan or zoom only brings a label into view or out of it.
2. **Clipped at the plot's edges.** A label and its connecting line are drawn inside the plot area and cut off at
   its edges — a label can be partly visible; nothing runs over the axes.
3. **Never moved to stay inside.** Untouched or dragged, a label stays at its Hz / dB.

The mode chips are cut the same way (owner, 2026-10-06). Swift and the web change on all three points.

## Plan (2026-10-22)

One rule in every edition: a label is a point in chart units — its centre at the stored position if dragged,
else at (peak Hz + 0, peak dB + 14) — drawn whenever the annotation mode shows it, cut at the plot's edges, never
moved to stay inside. The same for the mode chips' clipping.

**Found while planning:**
- **The web stores a different point.** Swift and Python store and draw a dragged label's **centre**; the web's
  drag stores the badge's **bottom centre** (`SpectrumChart.tsx`, `anchorSY: hit.y + hit.h`) and draws it so
  (`spectrumRender.ts`, `anchorBottom`). The same file puts a dragged label half a label apart between the web and
  the others. The web moves to the centre; files the web has already saved then show those labels half a label
  lower — a decision below.
- **Swift's label hit areas are wrong for a dragged label.** `SpectrumView.annotationLabelRects` (the open-hand
  cursor, and a pan not starting over a label) reads the stored Hz / dB as a shift from the default instead of the
  label's position, so for a dragged label the area is elsewhere. Replaced by the one position rule below.
- **Swift takes `offset == .zero` as "not dragged"** (`PeakAnnotations.finalPosition`): an entry's presence decides
  it in the new rule.

**Steps** — each with its tests; full suites and a run-review on every platform at the end.
1. **The shared definition.** Done: Swift `00e157c`, Python `e010e82`, web `b5d6766`. On each analyzer, beside the dragged positions, the offset and
   one function for a label's centre in chart units — where it was dragged, else the peak plus the offset (Swift
   `annotationCentre(for:)`, Python `annotation_centre`, the web's `annotationCentre`); the analyzer, not the
   chart style, since the label positions are its state. `annotation-state.json` gains `labelOffset` [0, 14],
   checked against each constant, and a `centre` check: AS42 (an undragged label, 14 dB above its peak), AS43
   (dragged; Reset Position and Reset Labels put it back), AS44 (the annotation visibility moves no label,
   dragged or not). The range cannot enter: the function takes none. Passing in all three (Swift 44 cases and the
   offset test, Python 45, the web 48); the views take the function in steps 2–4.
2. **Swift.** Done: Swift `00e157c`.
   - The live chart and the export place a label at `TapToneAnalyzer.annotationCentre(for:offsets:)` (the rule in
     a static form, for views handed the positions) through one mapping between chart units and the plot
     (`PlotMapping`, `PeakAnnotations.swift`); "dragged" is an entry being present. Gone: the 70 pt default
     (`calculateChartPosition`, the export's `annotationPosition`), the `.zero` "not dragged" test, and the
     unused `getAnnotationOffset`.
   - The line runs from the peak's dot, unclamped, to the label's centre, under the label (it ended at the
     centre + 30 pt, the export's at + 50).
   - Labels are not filtered by the frequency range (`visiblePeaks`, live and export); the dots keep the range.
   - The labels and lines are cut at the plot's edges (`PlotArea`). The mode chips are drawn over the chart in
     plot coordinates and cut there too (`ModeChipsLayer`, live and export) — no longer Charts annotations fitted
     inside the plot, or left out when their range starts off the chart.
   - Whether the pointer is over a label (the open hand, a pan not starting there) uses the labels' frames as
     drawn, cut at the plot (`isOverLabel`), instead of estimated rectangles that read a dragged position as a
     shift.
   - Checked: macOS and iOS builds; 65 tests in the suites touching annotations, the export, the dot layer and
     the view-type depth; exports rendered and looked at — untouched labels 14 dB above their peaks, dragged
     ones where they were put, lines under the labels, a label cut at the plot's top in a narrowed range, chips
     centred on their ranges' starts and cut at the edges.
3. **Web.** Done: web `b5d6766`.
   - Each chart marker carries its label's centre (`annoCentre`, from `TapToneAnalyzer.annotationCentre(peak,
     offsets)`, the rule in a static form); a badge is drawn centred on it, its line from the dot to the centre
     under the badge. Gone: the badge's bottom just above the dot, the export's 70 px / + 50 placement, the clamp
     inside the plot's sides and the nudge below its top.
   - A drag starts from, and stores, the label's centre — the renderer reports it with the badge's hit rectangle
     (`AnnotationRect.cx/cy`); the rectangle is the part inside the plot.
   - Badges are not filtered by the frequency or dB range; badges, lines and mode chips are drawn inside the
     plot's clip; a chip is centred on its range's start, not clamped, and drawn when the start is off the
     chart.
   - **Finding (owner, 2026-10-22): the web stacked overlapping labels in another order.** Swift and Python draw
     the labels in the analyzer's order (strongest peak first, so the weakest lies on top); the web's live chart
     sorted its peaks by frequency first (`App.tsx`), so the highest-frequency label lay on top — the same
     measurement stacked differently. Its live markers were also limited to the chart's frequency range there,
     which kept a label whose peak is off the chart from being drawn. The live chart's markers are now the
     analyzer's peaks in its order, over every frequency (the unknown-mode filter only); the renderer still
     draws a dot only inside the range. The exports already followed the analyzer's or the file's order; the
     PDF peak tables stay low → high, as Swift's.
   - Checked: typecheck and lint; the annotation, dot-layer, PDF and export tests (81); the export check
     (Playwright, 20 exports, 0 failing), its guitar export looked at — the same as Swift's.
4. **Python.** Done: Python `e010e82`. Its live chart already drew labels at the peak + 14 dB, unfiltered by range,
   cut by the plot, the line to the centre; its export and its chips did not.
   - The views place a label by the analyzer's rule (`TapToneAnalyzer.annotation_centre_from`, the class-level
     form) instead of their own `_LABEL_OFFSET_DB`; "moved" — for Reset Position and Reset Labels — is a stored
     entry, as Swift's and the web's, instead of a position compared on screen. `get_annotation_offset` (unused)
     removed.
   - Its export followed Swift's old export (70 pt above the peak, the line from + 50, labels limited to the
     range, chips only at boundaries on the chart, no Upper Modes): now the rule, the line from the centre,
     labels at every frequency, the chips and labels clipped to the plot, Upper Modes among the bands.
   - Its live chips had come to be hidden when their range starts off the chart and slid to stay inside — as
     Swift's were; that override is gone, so the plot cuts them, as on 2026-10-06.
   - Checked: 246 tests (annotations, codable, results, export, the export end to end, chart style, dot layer);
     exports rendered and looked at — the same as Swift's, a chip cut at the left edge where its range starts
     just off the chart.
   - **Finding (owner, 2026-10-22): a guitar label vanished in Python when a pan took its peak off the chart**,
     where Swift and the web draw it cut at the edge. Python's chart labels came from the results list's model
     (`PeaksModel`, which emitted a label for each row its annotation mode showed), and a guitar's results list
     holds the peaks in the chart's range only — the label left with the row. A divergence of mechanism:
     Swift's chart takes its labels from the analyzer (`tap.chartAnnotationPeaks`), apart from the results
     list. Now Python's does (owner: make Python like Swift): the chart's label manager (`FftAnnotations`)
     follows the analyzer — its peaks, display mode, comparison, plate / brace phases, loads and the colour
     scheme — and labels `chart_annotation_peaks` once per event-loop turn, each label's mode name, pitch and
     override mark from the analyzer (`peak_label`, `label_html`, moved from the model). The model no longer
     emits labels or keeps an annotation mode; the view sets the analyzer's annotation visibility and asks the
     labels to refresh. Gone with it: the model's label signals, `refresh_annotations`, `update_annotation`,
     `annotation_html`, its annotation mode, `data_held`'s label handling, and the label manager's
     `hide_annotation(s)` / `show_all_annotations`.
     Test changes: `test_comparison_annotation_guard` drives the chart's labels from a stub analyzer (no label in
     a comparison; a peak outside the chart's range labelled — the regression); `test_theme` reads the label
     text from `label_html`; `test_results_update_in_place`'s held tests, which checked the model's label
     signals, check the list's held state. Checked: the 812 tests that import the views; the app launched.

**Decided (owner, 2026-10-22):**
- **Labels the web has already saved** show half a label lower once the web stores the centre. Accepted: a
  measurement file does not record the edition that wrote it, so they cannot be told apart and converted; such a
  label is put back by dragging it.
- **The connecting line** runs from the centre of the peak dot to the centre of the label, under the label's filled
  box, so it shows from the dot to the box's edge — as Python's does (`_update_arrow`; the label drawn over the
  line). Swift (to the label's centre + 30 pt) and the web (to the box's bottom edge) change to it; the line is cut
  at the plot's edges with its label.

**Full suites (2026-10-22):** Swift (macOS) 297 tests in 90 suites, the export UI tests 5 cases, 0 failing;
Python 1572 passed, 1 skipped (the capture probe, off), the export check 20 exports, 0 failing; the web 1429
passed, 1 skipped, lint and typecheck clean, the export check 20 exports, 0 failing. The parity map current.

## Run-review

Swift on macOS, the iPhone and the iPad; Python on macOS, Windows and Linux; the web on the desktop and the iPhone.
A guitar measurement with several labelled peaks, Annotations on All unless a step says otherwise.

**Passed on every edition and platform (owner, 2026-10-22)**, after the two findings it raised were fixed (the
web's stacking order; Python's labels following the results list).

1. Open the measurement. → Each untouched label sits 14 dB above its peak, centred on it; its dashed line runs
   from the dot and disappears under the label. The same heights in every edition.
2. Press the annotations button through All → Selected → None → All. → No label that comes back has moved.
3. In Settings, set the magnitude range to −70 to −30 dB and the frequency range so the Air peak is just left of
   the chart. → The labels keep their Hz / dB, moving with the spectrum as a zoom moves it; the Air peak's label
   is still drawn where it falls, cut at the plot's left edge; a label reaching the top is cut there; nothing
   slides to stay inside, and no label runs over the axes.
4. Zoom and pan over the chart (wheel, pinch, drag). → As step 3: the labels move with the spectrum and are cut
   at the plot's edges.
5. Pan until a mode's range starts just off the left edge. → Its chip is cut at the edge, the part inside
   showing; no chip slides along to stay inside.
6. Drag a label away and release it, then zoom. → It stays where it was dropped, in Hz / dB; its menu's Reset
   Position is enabled and puts it back 14 dB above its peak; Reset Labels is enabled while any label has been
   dragged.
7. Swift (macOS): move the pointer over a dragged label, then press and drag on the chart beside it. → The open
   hand shows over the label itself and nowhere else; the drag beside it pans the chart.
8. Drag a label in one edition, save, and open the file in the other two. → The label is in the same place in
   all three.
9. Export Spectrum and Export PDF. → The labels, lines and chips as on screen.

## Clipping — how a label meets the chart's edges (owner, 2026-10-01)

Labels are clipped very differently in the three editions — what each does today, the background to the decision
above.

What each edition does today (from the code; to be checked in full when this is taken up):

- **Swift** (`SpectrumView.visiblePeaks`, `PeakAnnotations`): a label is drawn for a peak inside the chart's frequency
  range; the labels are an overlay on the chart and are not clipped to the plot area.
- **web** (`spectrumRender.ts`, `drawBadge`): a label is drawn for a peak inside the frequency range and above the
  bottom of the dB range, after the plot's clip is released, so it may overflow the plot. The box is held inside the
  plot horizontally; an auto-placed box that would cross the plot's top is moved down; a dragged box keeps its
  position.
- **Python** (`peak_annotations.py`): labels are pyqtgraph items in the plot (`plot_item.addItem`), so the view box
  clips them; which peaks get a label at the edges is to be confirmed.

**Owner's position (2026-10-06): Python's clipping is right.** Python cuts both peak labels and mode chips off at the
plot's edges: a chip whose band starts left of the chart shows only the part inside the plot ("r" of Air), and the
whole chip appears once a pan brings the start into view. Swift lets labels run over the plot's edge (seen covering
the magnitude axis title), and the web lets them overflow too and leaves out a chip whose band starts off-chart. The
owner notes this is related to, but separate from, the main question of #25 — how an untouched label's position is
set and saved.
