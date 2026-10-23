# Swift: each spectrum update rebuilds the whole window

**Issue:** [#31](https://github.com/dwsdolce/guitar-tap-project/issues/31)

Status: ✅ **CLOSED 2026-10-22** — item 1 done: Swift `d6b6297`. Item 2 done by the live frame on its own object
(Swift `bdbcb76`): measured again, the main thread is busy 8.7 % while listening (34 % before item 1, 22 % after),
and a spectrum update no longer rebuilds the window.

Follow-on to #28 (`docs/completed/SWIFT-VIEW-UPDATE-COST.md`). Found 2026-10-14 while measuring why the Swift
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
| 2 | Each spectrum update rebuilds the whole window | done |

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
measured the same rate (≈ 1.5 / s) and left it.
- *Done* by the live frame on its own object (`LiveFrame`, Swift `bdbcb76`): the spectrum, its peak and the
  readout level are published there, observed by the chart, the status bar's readout and the metrics panel alone;
  `test/live-frame` checks, in all three editions, that a frame is announced on the live frame alone.
- *Measured (2026-10-22)* as above: the Mac app, Release, generic guitar, Taps 1, listening, nothing touched, a live
  peak at 120 Hz from the room; factory settings (Peak Min −60 dB, so one peak listed). Swift `9bd34be`.

  | | before item 1 | after item 1 | now |
  |---|---|---|---|
  | Main thread busy (Time Profiler, 20 s) | 34 % | 22 % | 8.7 % (1.78 s of 20.5 s) |
  | `TapToneAnalysisView.body` | — | ≈ 1.4 / s, ≈ 100 ms each, most of the window rebuilt | ≈ 0.7 / s, ≈ 1 ms each, nothing beneath it rebuilt |
  | SwiftUI update time (SwiftUI template) | — | ≈ 157 ms a second | ≈ 54 ms a second |

  The main window's body still runs once per FFT frame (≈ 0.73 / s at 48 kHz): the live peaks re-found on each frame
  are published on the analyzer, which the window observes. SwiftUI reuses everything beneath it — the results rows
  do not update — so it costs about 1 ms; moving the live peaks to an object of their own would save little. The
  largest remaining cost is the chart drawing each new spectrum, about 5–10 ms a frame. The threshold meter updates
  about 10 times a second, a few ms a second in all; the toolbar's buttons about 20 times a second, SwiftUI's own
  button internals, about 0.3 ms a second.
