# Live peaks published on every frame

**Issue:** [#41](https://github.com/dwsdolce/guitar-tap-project/issues/41)

Status: **OPEN — found 2026-10-24 (#9's run-review), nothing changed yet.** Decided by the owner: the live peaks get
an object of their own, in all three editions (option B below).

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

## Plan

1. **Survey and design** — `allPeaks` / `selectedPeakIDs` / `identifiedModes` are also the completed measurement's
   peaks (selection, labels, save, load), so: what the new object holds (only the per-frame live values, or the
   peak state at all times) and who reads it, in each edition. Written here for the owner's decision.
2. **Test first** — a shared *who is told* case, as `test/input-level` / `test/live-frame`: while waiting for a tap,
   a frame's new peaks do not tell the analyzer's observers.
3. **Implement** — Swift, then Python, then the web; parity tags and the case file.
4. **Run-review** — iPad and iPhone: menus (highlight, Delete submenu) and a row's swipe during a live spectrum;
   the live peaks and labels as before on every edition.
