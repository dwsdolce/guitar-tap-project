# Android UI Guidelines

How the canonical Swift UI translates to Android. The counterpart of
[WEB-UI-GUIDELINES.md](WEB-UI-GUIDELINES.md), written for the port in
[ANDROID-PLAN.md](../docs/ANDROID-PLAN.md).

> **Status:** proposed 2026-09-16, as Phase 1 of the Android port. Nothing is implemented yet.

**Platform priority: tablet first, phone second.** Android tablets are the primary target — the
spectrum chart, the results panel and the measurements library all want width, which is why the
iPad layout is the rich one. Phone layouts are built and kept correct but verified on the
emulator only; no Android phone is being acquired for testing. When a phone-specific report
arrives, say so plainly rather than guessing.

**One manual, one function set, one vocabulary.** Every edition ships against the same user
manual. A feature must exist on Android under the same name it has in Swift, or not exist. Where
a macOS affordance has no Android equivalent (a menu bar, a floating window), the *function*
still ships — as a toolbar or overflow item — under its existing name.

---

## Principles

1. **Mirror the iOS branches, decided case by case.** Swift carries ~155 `#if os` /
   size-class / `UIDevice` branches across 30 files. Expanded width ↔ iPad regular; compact ↔
   iPhone. Resolve each branch on its own merits against the Swift source — never by copying
   what Python or the web did. Python once copied the iOS `compactStatusBar` gate where macOS
   used `fullStatusBar`, and the bug outlived several releases
   ([PLATFORM-PARITY-GAPS](../docs/completed/PLATFORM-PARITY-GAPS.md)).

2. **Layout selection follows Swift's predicate order.** Swift picks `phoneLandscapeLayout`
   when the device is a phone in a compact vertical size class, else `iPadHorizontalLayout`
   when it is not a phone and the horizontal size class is regular, else
   `standardVerticalLayout` (`TapToneAnalysisView`, `+Layouts.swift`). On Android:
   `WindowSizeClass` expanded width → the iPad layout (**the primary case**); compact width in
   landscape → the phone-landscape layout; otherwise the vertical layout.

3. **Results are inline on a tablet, a sheet on a phone.** In the iPad layout the results panel
   sits beside the chart at 360 dp ideal / 480 dp maximum, so the chart keeps its share of a
   wide window; it is never a sheet there. In the vertical layout results are a sheet. In phone
   landscape they slide in as a **420 pt overlay** over the chart with a dimming scrim and
   tap-off to dismiss — deliberately *not* resizing the chart, because the two are not worth
   showing together at that size (`+Layouts.swift`).

4. **A sheet never dismisses silently.** Swift marks every sheet
   `.interactiveDismissDisabled()` with an explicit **Done** button. On Android that means the
   back gesture must not discard an editing sheet: intercept it and require Done, or an
   explicit discard, matching Swift's refusal to let a swipe throw work away.

5. **The chart's gestures are zone-dependent, and the zones are generous.** A pinch anchored in
   the plot zooms both axes about the pinch centroid; a pinch that starts over the x-axis zone
   zooms frequency only; over the y-axis zone, magnitude only (`SpectrumView`,
   `+GestureHandlers.swift`). The zones are the **whole** area below and left of the plot, not
   the narrow label strips, so they are easy to hit. Clamps: frequency 0…`maxDisplayFrequency`,
   minimum span 50 Hz; magnitude −120…+20 dB, minimum span 10 dB. Pan is a drag with an 8 pt
   minimum; on iOS it pans both axes (the axis-constrained variant is macOS-only), and Android
   follows iOS.

6. **Peak annotations are draggable, resettable, and must not fight the chart.** A long-press
   menu offers *Reset Position*, disabled unless the label has moved, and a **double-tap resets
   a label** (`PeakAnnotations.swift`). Chart pan and zoom are suppressed while an annotation
   drag is in flight. Offsets are stored in absolute data space (Hz, dB), not pixels, so they
   survive zoom, rotation and reload.

7. **Secondary actions need a visible affordance, not only a long-press.** Swift exposes the
   chart's axis-reset actions through a context menu; the web guidelines require the same set
   behind an always-visible **⋯** button beside the **?** in the chart's upper right. Android
   ships the ⋯ and ? pair too: a long-press is an accelerator, never the only route.

8. **Destructive and load actions keep Swift's deliberate friction.** In the measurements list
   a single tap does nothing outside Compare mode, **double-tap loads**, long-press opens the
   row actions, and swipe-to-delete routes to a confirmation — never an immediate delete
   (`MeasurementsListView.swift`). Keep all four behaviours.

9. **Touch targets ≥ 48 dp**, the Android minimum (the web guidelines use the iOS figure of
   44 px). Applies to toolbar icons, chart controls, list-row affordances and the peak-mode
   chips.

10. **Theme comes from the [style guide](STYLE-GUIDE.md) and its role table (`tooling/parity/cases/theme.json`), not from Material dynamic colour.**
    Appearance is System (default) / Light / Dark, resolved live when the OS flips. The spec
    fixes exact hex values for chrome, chart, mode colours, the magnitude gradient, the
    multi-tap palette and the quality labels — precisely so that platforms stop substituting
    system-named colours. Encode it as a theme resource pair and assert the mode and chart
    values in a unit test. **PNG and PDF exports stay light in both themes.**

---

## Worked example: the expanded-width (tablet) screen

Top to bottom, mirroring `iPadHorizontalLayout`:

- **Tap controls row** — the regular (not compact) control set, horizontal padding, 8 dp top.
- **Divider.**
- **Row:** chart pane (with a minimum-width guard, so a zero-size measurement pass cannot
  produce NaN) plus the decay/ring-out readout · divider · **results panel**, 360 dp ideal and
  480 dp maximum.
- **Divider.**
- **Status bar** — the full variant, not the compact phone one.

Toolbar, leading: Play File · Auto dB · Crosshair · Annotations. Trailing: Save · Measurements ·
Metrics · Settings · Help. On Android these become the app bar plus an overflow menu; the names
and the order stay as they are in Swift.

## Worked example: substituting the platform pieces

| Swift (macOS/iOS) | Android |
|---|---|
| `.fileImporter` / `UIDocumentPickerViewController` | Storage Access Framework — `ACTION_OPEN_DOCUMENT`, `CreateDocument` |
| `UIActivityViewController` / `NSSharingServicePicker` | `ACTION_SEND` chooser via `FileProvider` |
| `NSSavePanel` | SAF `CreateDocument`; `ACTION_OPEN_DOCUMENT_TREE` for the WAV dump folder |
| Menu-bar shortcuts (⌘S, ⌘E, ⌘L, …) | Every command exists as a toolbar or overflow item; hardware-keyboard shortcuts on tablets are a later nice-to-have |
| Floating results window (macOS `NSWindow`) | The inline results pane of the expanded layout — not a separate window |
| `.help()` tooltips, hover, `NSCursor` | Content descriptions for accessibility; no hover states |
| Help `.popover` | A dialog or bottom sheet, same content |

**Do not invent platform behaviour.** The Swift app uses no haptics and does not disable the
idle timer. If Android wants either during capture, that is a new product decision recorded here
first, not a silent addition by the port.

## Not ported

`SpectrumScrollWheel` (the AppKit scroll-wheel bridge), `ResultsWindowPresenter` (the floating
window), the macOS `NSOpenPanel` WAV-dump picker, and tap-to-highlight-nearest-peak on the chart
— which is macOS-only in Swift by choice, and stays that way.

## Implementation status

Nothing implemented; the port has not started. When Phase 4 begins, each principle above should
be checkable against the running app, and the Phase 4 gate is a run-review on the tablet beside
Swift on iPad.
