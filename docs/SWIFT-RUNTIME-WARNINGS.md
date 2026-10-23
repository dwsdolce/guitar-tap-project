# Swift runtime warnings — the audio session on the main thread; a publish during a view update

**Issue:** [#36](https://github.com/dwsdolce/guitar-tap-project/issues/36)

Status: **OPEN — item 2 done (Swift `0191911`); item 1 investigated, not changed.**

Seen in the Xcode console while running on the iPad (owner, 2026-10-20). Not seen on macOS.

## Items

| # | Warning | Where | What it means | Status |
|---|---|---|---|---|
| 1 | AVAudioSession Hang Risk: "This method can lead to UI unresponsiveness if called on the main thread while the audio session is active" / "Consider using the asynchronous activate/deactivate API" | `TapToneAnalysisView+Actions.swift:56–57` (`setCategory(.record, mode: .measurement)`, `setActive(true)`); `RealtimeFFTAnalyzer+EngineControl.swift:191–192`; `RealtimeFFTAnalyzer+DeviceManagement.swift:556` | The session is set up on the main thread; while the system answers, the UI cannot respond — a freeze if it is slow (at start-up, a restart, a device change). iOS only: macOS has no audio session. | open |
| 2 | "Publishing changes from within view updates is not allowed, this will cause undefined behavior" | `TapToneAnalysisView.swift:633` — the microphone-warning alert: `isPresented` is bound to `microphoneWarning != nil`, and its setter clears `microphoneWarning` | A published value changes while SwiftUI updates the view — an alert that shows again or does not clear. Not iOS-specific; it fires when a microphone warning is shown. | done |

## Findings (2026-10-22)

**1. The audio session.**
- Set up twice on every start: `startAnalyzer()` (the view) sets `.record` / `.measurement` and activates the
  session, then calls `TapToneAnalyzer.start()` → `RealtimeFFTAnalyzer.start()`, which does the same again. The
  restarts after a device change call `start()` alone, so the view's copy is redundant.
- The category goes back and forth: listing the inputs (`loadAvailableInputDevicesIOS`, at launch and after a stop,
  whenever the engine is not running) sets `.playAndRecord` with Bluetooth A2DP; `start()` then sets `.record`. Each
  change is a round trip to the system and a route change (reason `categoryChange`) the app checks and logs. Whether
  `.record` alone lists a USB microphone (the code's comment says `.playAndRecord` is needed) is untested.
- The asynchronous activation (`activate(options:completionHandler:)`) is iOS 27 and later; the app supports iOS 18.6
  and later. Below 27, Apple's advice is to activate off the main thread.
- `start()` is synchronous and returns with the engine running. An asynchronous activation makes the start finish
  in a callback — Start, the return to the foreground, the restart after a device change and the tests all call it.

**2. The microphone-warning alert.** Two possible causes:
- (a) OK sets `microphoneWarning = nil`; as the alert closes, SwiftUI calls the binding's setter with `false` within
  its update, which sets `nil` again — and a `@Published` property announces every assignment, even an unchanged
  one. Harmless but the warning. The view's four other alerts (import success and error, microphone unavailable,
  library unreadable) have the same binding.
- (b) A double-click in Saved Measurements dismisses the sheet and loads one main-queue turn later; on the iPad the
  sheet is still animating out, the alert cannot be presented, and SwiftUI sets its binding to `false` within its
  update — clearing the warning unseen. That would be a real bug, and would explain iPad-only.

Reproduced on the iPad simulator (iPad Air 11-inch (M4), 2026-10-22; a temporary UI test, not committed): a
measurement recorded on a UMIK-1 imported, then loaded by a double-tap in Saved Measurements. The sheet closed and
"Microphone Not Found" was shown — so not (b); pressing OK, five "Publishing changes from within view updates" at
once, as the alert closed — (a).

*Fixed (owner, 2026-10-22): Swift `0191911`.* the alert bindings clear a published value only while it is set
(`set: { if !$0, value != nil { value = nil } }`) — the microphone warning, both "Microphone Unavailable" alerts
(the main view and Settings) and "Saved Measurements Unreadable"; the bindings on `@State` values publish nothing
and are unchanged. No behaviour changes: OK, and any other way the alert closes, still clear it. The same run
again: the alert shown and closed as before, no "Publishing changes from within view updates" in the log.

## Proposed (not decided)

1. The asynchronous session activation Apple recommends, checked on the iPad and iPhone.
2. The warning cleared outside the view update.

Done when both warnings are gone from the console on the device.
