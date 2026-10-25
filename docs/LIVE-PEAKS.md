# Live peaks published on every frame

**Issue:** [#41](https://github.com/dwsdolce/guitar-tap-project/issues/41)

Status: **OPEN — built in all three editions (2026-10-24): Swift `f8aabd6`, Python `61a28ea`, web `b89644e`.**
Run-review passed on macOS and iOS in every edition (owner, 2026-10-24); Windows and Linux to run-review.

## The problem

While a tap sequence waits for a tap, every published spectrum frame goes to the analyzer's `analyzeMagnitudes`
(Swift `TapToneAnalyzer+PeakAnalysis.swift:69`; Python `tap_tone_analyzer_peak_analysis.py:35`; web
`tapToneAnalyzer.ts:1517`), which finds the live peaks and assigns them on the analyzer — `allPeaks`,
`selectedPeakIDs`, `identifiedModes` — every frame, changed or not (an empty list onto an empty list included).
In Swift each assignment announces a change of the whole `TapToneAnalyzer`; the web's ends with `this.notify()`.
So everything that watches the analyzer redraws at the frame rate — in Swift, the whole main view.

`InputLevel` and `LiveFrame` (#28) exist so that per-buffer and per-frame values reach only the views that show
them; the live peaks were left on the analyzer.

## What it breaks

**iOS: open menus are rebuilt on every frame.** Each redraw of the main view makes SwiftUI refresh any open `Menu`
in the window, sheets included (`UIContextMenuInteraction.updateVisibleMenuWithBlock:`, called from SwiftUI's
update pass). Where a menu has icons the refresh shows:
- the item under the pointer or finger loses its highlight and the menu visibly redraws — Saved Measurements'
  Sort & Filter and More (⋯), the type menu beside New Tap, the graph's ⋯;
- a toolbar menu whose button is an icon closes its open submenu — More (⋯) → Delete.

After a tap, or with a loaded measurement, nothing is assigned and the menus behave. macOS does not show it (an
open `NSMenu` is not rebuilt by SwiftUI's redraws), but the redraws still cost there.

## Evidence (iPad Pro M5, iOS 27.0.1, 2026-10-23/24)

- **Freezing the published spectrum** while Saved Measurements was open (tap detection still running): the main
  view redrew once in 29 s instead of ~20 times; SwiftUI made **no** menu refreshes; the menus behaved.
- **SwiftUI's own report** (`Self._printChanges()`) for the main view, live, no tap: 15 of its redraws say
  `_tapToneAnalyzer changed`.
- **The level meter** updates far faster and disturbs nothing — `InputLevel` redraws only the meter.
- **Icons are what makes it visible** — test menus, one feature each, during a live spectrum:

  | Test menu | Highlight | Submenu |
  |---|---|---|
  | plain text items; ticked items; sections; a destructive and a disabled item | kept | stays open |
  | in the toolbar, text button, text items; custom menu styling; a hover tooltip | kept | stays open |
  | items with icons (made fresh, or made once and kept) | lost | stays open |
  | toolbar, text button, icon items | lost | stays open |
  | toolbar, **icon button**, icon items | lost | **closes** |

- **Ruled out:** the menus' own views redrawing (isolated, they did not redraw, and still lost the highlight); the
  graph drawing (replaced by a blank panel; no change, as the main view still redrew); the sheet's presentation and
  environment. No report of this exact behaviour was found on the web; Apple's forums have related ones (a menu
  dismissed by frequent background updates, threads 738391 and 690588).

## The fix (decided: B)

- Not chosen: assigning only when the values change — it stops the redraws only while there are no live peaks; live peaks
  have new ids every frame, so they would still publish.
- **B. The live peaks get their own object**, as `InputLevel` and `LiveFrame` — observed only by the views that show
  live peaks (the graph's labels, the Results list); the main view stops redrawing at the frame rate. All three
  editions, the same mechanism (the owner, 2026-10-24).

## Survey (2026-10-24)

The values assigned every frame — and only these — are the **detected peaks**: `allPeaks`, its Peak Min projection
`peaksAbovePeakMin`, `identifiedModes` and `selectedPeakIDs`. They are the live peaks while waiting for a tap and the
measurement's peaks once it completes (selection, labels, saving, loading, export, re-analyze). The other peak state —
`highlightedPeakID`, `peakModeOverrides`, `peakAnnotationOffsets` — changes on the user's action, not per frame.

| | Where the values live | How views are told | Who reads them for display |
|---|---|---|---|
| Swift | `@Published` on `TapToneAnalyzer` | the whole analyzer announces a change (`ObservableObject`) | the main view's body (the chart's `peaks`/`annotationPeaks`/`peakModes`, `SpectrumViews.swift:219–268`; five buttons' "no peaks → disabled", `Layouts.swift:390, 527, 834`, `Controls.swift:61, 163`), the Results panel (`TapAnalysisResultsView.swift:252, 410, 523`), exports and the PDF (on demand) |
| Python | attributes on the analyzer | the analyzer's own `peaksChanged` signal — already peak-specific | the chart's scatter and labels (`fft_canvas.py`, `peak_annotations.py`), the Results panel, the main view's buttons |
| Web | fields on the analyzer | `analyzer.notify()` — every subscriber re-renders (`App` via `useTapToneAnalyzer`) | `App.tsx` (6 reads of `peaksAbovePeakMin`), the chart, the Results panel |

No Combine subscription in Swift reads these values; nothing else on the analyzer is assigned per frame (with the
spectrum frozen, the main view redrew once in 29 s).

## Design (decided by the owner, 2026-10-24 — to be refined as it is built)

1. **One home for the detected peaks, at all times** — a `DetectedPeaks` object (slug `model/detected-peaks`) holding
   `allPeaks`, `peaksAbovePeakMin`, `identifiedModes` and `selectedPeakIDs`, live and completed alike. Not a
   live-only object copied onto the analyzer at completion: that would keep the same values in two places.
2. **The analyzer keeps its API** — `analyzer.allPeaks` etc. read and write through to `analyzer.peaks`, so the model
   code is unchanged; only who is told changes: **the peaks' observers, not the analyzer's**.
3. **The views that show peaks observe `DetectedPeaks`** —
   - Swift: the chart is built inside a `PeaksReader` (as `FrameReader` reads `LiveFrame`), the Results panel
     observes `analyzer.peaks`, and the five buttons' "has peaks" goes through `PeaksReader` too — so the main view's
     body reads no peaks;
   - Python: `peaksChanged` moves to `DetectedPeaks` (the views connect to `analyzer.peaks.peaksChanged`) — the same
     behaviour, the same structure as the others;
   - web: a small store with its own `subscribe` (as `inputLevel.ts`); `analyzeMagnitudes` notifies it instead of the
     analyzer; the chart, Results panel and buttons read it through a hook.
4. **The user-driven peak state stays on the analyzer** (`highlightedPeakID`, overrides, label positions) — it does
   not change per frame. Moving it too would be consistent but is not needed for this fault.
5. **Test of who is told** (shared case, as `test/input-level`): while waiting for a tap, a frame's new peaks tell
   the peaks' observers and **not** the analyzer's; after completion nothing is told per frame.

## Plan

1. **Design** — decided by the owner (2026-10-24), to be refined as it is built.
2. **Test first** — a shared *who is told* case, as `test/input-level` / `test/live-frame`: while waiting for a tap,
   a frame's new peaks do not tell the analyzer's observers.
3. **Implement Swift, then test it on the iPad and iPhone** — the menus (highlight, the Delete submenu) and a row's
   swipe during a live spectrum. Only once Swift is shown to fix it: Python, then the web; parity tags.
4. **Run-review** (below) — iPad and iPhone: menus (highlight, Delete submenu) and a row's swipe during a live spectrum;
   the live peaks and labels as before on every edition.

## Built

| | Model | Views |
|---|---|---|
| Swift | `Models/DetectedPeaks.swift`; the analyzer's four values read and write through `peaks` | `Views/Utilities/PeaksReader.swift` (`PeaksReader`, `DisabledByPeaks`): the chart, the five annotation-visibility buttons, the Results panel (behind `AnyView`) |
| Python | `models/detected_peaks.py` (`peaksChanged` moved here); the analyzer's four values are properties onto `peaks` | every `peaksChanged` emit and connect through `analyzer.peaks` |
| Web | `state/detectedPeaks.ts` (`analyzer.detectedPeaks` — `analyzer.peaks` is the web's name for every peak); the four fields read and write through it; out of the analyzer's snapshot | `components/PeaksReader.tsx`; `App`'s peak chain is one function (`peakDisplay`) read inside the readers around the chart, the annotation button, the selection buttons, the Results list and the ratio |

Tests: `test/detected-peaks` (DP1, DP2) in all three; the live-frame tests' note corrected. Found on the way: #9's
Saved Measurements view had grown past the iPhone type-depth limit (38 of 36) — its rows now behind `AnyView`.

## Run-review

On each edition: Python on Windows, macOS and Linux; the web on a computer and on a phone or tablet; Swift on the Mac.

1. Start a guitar tap sequence and do not tap. → The spectrum and its peaks update live; peak labels appear and move;
   the Results list and the Tap Ratio follow them.
2. Zoom or pan the chart while waiting. → The Results list follows the visible range, as before.
3. Press the annotation-visibility button. → Enabled while there are peaks; it cycles All → Selected → None.
4. Tap once. → The measurement completes; peaks, labels, the Results list and the ratio hold still.
5. Deselect a peak in the Results list, then Deselect All, then Reset to Auto. → The chart's labels and the ratio
   follow each.
6. Rename a peak's mode, then drag its label. → Both show at once, and survive a Peak Min move.
7. Start a plate measurement and go through its phases. → The L / C / FLC peaks and labels show as before.
8. Load a saved measurement. → Its peaks, selection and labels show as saved.

