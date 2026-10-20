# Swift runtime warnings — the audio session on the main thread; a publish during a view update

**Issue:** [#36](https://github.com/dwsdolce/guitar-tap-project/issues/36)

Status: **OPEN — reported; no code changed (owner, 2026-10-20).**

Seen in the Xcode console while running on the iPad (owner, 2026-10-20). Not seen on macOS.

## Items

| # | Warning | Where | What it means | Status |
|---|---|---|---|---|
| 1 | AVAudioSession Hang Risk: "This method can lead to UI unresponsiveness if called on the main thread while the audio session is active" / "Consider using the asynchronous activate/deactivate API" | `TapToneAnalysisView+Actions.swift:56–57` (`setCategory(.record, mode: .measurement)`, `setActive(true)`); `RealtimeFFTAnalyzer+EngineControl.swift:191–192`; `RealtimeFFTAnalyzer+DeviceManagement.swift:556` | The session is set up on the main thread; while the system answers, the UI cannot respond — a freeze if it is slow (at start-up, a restart, a device change). iOS only: macOS has no audio session. | open |
| 2 | "Publishing changes from within view updates is not allowed, this will cause undefined behavior" | `TapToneAnalysisView.swift:633` — the microphone-warning alert: `isPresented` is bound to `microphoneWarning != nil`, and its setter clears `microphoneWarning` | A published value changes while SwiftUI updates the view — an alert that shows again or does not clear. Not iOS-specific; it fires when a microphone warning is shown. | open |

## Proposed (not decided)

1. The asynchronous session activation Apple recommends, checked on the iPad and iPhone.
2. The warning cleared outside the view update.

Done when both warnings are gone from the console on the device.
