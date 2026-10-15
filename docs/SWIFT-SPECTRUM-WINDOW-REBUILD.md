# Swift: each spectrum update rebuilds the whole window

Issue #31. Follow-on to #28 (`docs/completed/SWIFT-VIEW-UPDATE-COST.md`). Found 2026-10-14 while measuring why the Swift
Settings window opened slowly.

## What the owner saw

- Settings is slow to open in a Debug build; in Release it is more than acceptable.
- The Mac app's main thread stayed busy while listening with nothing touched.

## What was measured

Mac app, Release build, listening, nothing touched, Instruments attached.

**Opening Settings** (SwiftUI template, ~12 openings in 60 s): about 300 ms of main-thread work per opening
(250–300 ms microhangs), of which `TapSettingsView` and its sections are about 10 ms. The rest is SwiftUI and
AppKit building, laying out, presenting and drawing the sheet. No hot spot in the app's code; the cost is the
size of the sheet, and the optimizer removes most of it. Not pursued.

**Idle, 20 s, Time Profiler only:**

| | before the meter fix | after the meter fix |
|---|---|---|
| Main thread busy | 34 % (7.0 s of 20.6 s) | 22 % (4.6 s of 20.6 s) |
| SwiftUI update passes | ≈ 19 / s | ≈ 9.5 / s |

**Idle, 5 s, SwiftUI template, after the meter fix:** `ThresholdSlider` 78 body updates costing ≈ 8 ms in all.
`TapToneAnalysisView.body` ≈ 1.4 / s, and each run rebuilds most of the window — in 5 s ≈ 3,200 `Text`,
3,600 shape and 2,000 `Button` updates, the chart, the results rows (`CombinedPeakModeRowView`) and
`HelpView`: most of the 785 ms of SwiftUI update time. Each rebuild ≈ 100 ms, seen as occasional dropped frames.

## Items

| # | item | status |
|---|---|---|
| 1 | The threshold meter redrew itself 20 times a second from its own timer | done |
| 2 | Each spectrum update rebuilds the whole window | open |

**1. The threshold meter's own timer** (Swift only). `ThresholdSlider` ran
`Timer.publish(every: 0.05)` to keep the peak-hold dot decaying, and each tick wrote `@State` (a new
`lastUpdateTime` every time), so SwiftUI redrew the meter 20 times a second on top of the ≈ 10 level updates.
Python's `set_level_db` and the web's `ThresholdMeter` update the peak hold only when a level arrives, which is
every audio buffer while listening.
- *Done:* the timer is gone; the peak hold updates on every published level
  (`.onReceive(inputLevel.$inputLevelDB)`), as Python and the web do; its timing is held by reference, like the
  web's `useRef`, so only a move of the dot redraws. The meter is `view/threshold-slider`, review only in all
  three, so the check is the measurement above. Swift `d6b6297`.

**2. Each spectrum update rebuilds the whole window.** The engine publishes the spectrum about twice a second;
the main view observes the engine, so every spectrum re-evaluates the whole window, not only the chart. #28
measured the same rate (≈ 1.5 / s) and left it. The likely fix is #28's pattern: the spectrum in its own small
observed object, read by the chart alone. Before deciding: what else reads the spectrum (peak readouts, status),
and whether Python and the web rebuild more than their chart on a spectrum update. Not urgent — measurements run
on other threads, and Release is responsive.
