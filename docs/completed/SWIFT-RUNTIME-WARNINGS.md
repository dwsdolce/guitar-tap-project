# Swift runtime warnings — the audio session on the main thread; a publish during a view update

**Issue:** [#36](https://github.com/dwsdolce/guitar-tap-project/issues/36)

Status: ✅ **CLOSED 2026-10-22** — item 2 done: Swift `0191911`. Item 1: steps 1–2 done, Swift `5364ecf` — one session setup per start and one category, so the category warning is gone; the activation warning accepted (owner, 2026-10-22): every edition starts its input synchronously on the main thread, and a slow activation pauses, then recovers. Checked on the iPad simulator and on the iPad with the UMIK-1.

Seen in the Xcode console while running on the iPad (owner, 2026-10-20). Not seen on macOS.

## Items

| # | Warning | Where | What it means | Status |
|---|---|---|---|---|
| 1 | AVAudioSession Hang Risk: "This method can lead to UI unresponsiveness if called on the main thread while the audio session is active" / "Consider using the asynchronous activate/deactivate API" | `TapToneAnalysisView+Actions.swift:56–57` (`setCategory(.record, mode: .measurement)`, `setActive(true)`); `RealtimeFFTAnalyzer+EngineControl.swift:191–192`; `RealtimeFFTAnalyzer+DeviceManagement.swift:556` | The session is set up on the main thread; while the system answers, the UI cannot respond — a freeze if it is slow (at start-up, a restart, a device change). iOS only: macOS has no audio session. | steps 1–2 done; the activation warning accepted |
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

## Item 1, step by step

**Step 1 — one session setup per start** (owner, 2026-10-22; Swift `5364ecf`). `startAnalyzer()` no longer sets the
category or activates the session; `TapToneAnalyzer.start()` → `RealtimeFFTAnalyzer.start()` does, as for every
other start. The view only asks the analyzer to start and the engine sets up the audio, as Python's view
(`start_analyzer` → `analyzer.start()`) and the web's (the microphone opened in `realtimeFFTAnalyzer.ts` alone).
The warnings at launch, iPad Air simulator: two activations and one category change, from three and two on the
iPad (owner, 2026-10-22). The category change left is the engine setting `.record` while the input list's
`.playAndRecord` session is active — step 2. On the iPad: two activations and one category change (owner, 2026-10-22).

**Step 2 — one category, set only when it differs** (owner, 2026-10-22; Swift `5364ecf`). Checked first on the iPad
with the UMIK-1 attached: with `.record` alone, the input list shows the UMIK-1 (`Umik-1  Gain: 18dB`) beside the
iPad Microphone with the engine stopped, and it is chosen and listed in Settings — `.playAndRecord` is not needed
to see it. The input list and the engine's start now both call `RealtimeFFTAnalyzer.setRecordingCategory`:
`.record`, mode `.measurement`, no options, set only when the session is not that already — iOS warns when the
category is set while the session is active even to the same value, and whichever comes second finds it set.
The warnings at launch: two activations and no category change, on the iPad simulator and on the iPad; unplugging
and plugging the UMIK-1 back in adds one activation each (the engine's restart), no category change; the app moves
to the iPad Microphone and back and keeps listening (owner, 2026-10-22).

With the UMIK-1 attached iOS also logs `AVAudioSessionUtilities.mm:77 -- Endpoint Value Converter failed to find a
match for string "Other"` whenever the route or the inputs are read — the system's own description of the USB
endpoint; the app passes no such string and cannot remove it.

**The activation warning — accepted** (owner, 2026-10-22). What remains is `AVAudioSession_iOS.mm:978`: the session
activated on the main thread, by the engine's start and by the input list while the engine is stopped. Only iOS has
a session, but every edition opens and starts its input the same way — Swift on macOS (the device set on the audio
unit, `audioEngine.start()`) and Python (`sd.InputStream`, `stream.start()`) synchronously on the main thread, the
web asynchronously only because the browser's `getUserMedia` and `AudioContext` give no other way. iOS alone has a
runtime check that names it. A slow activation freezes the interface while iOS's audio system answers, then
returns and the app carries on; a refusal (a call holding the microphone) returns at once with the engine-start
error. No stall has been seen.

Removing it would mean the asynchronous activation (`activate(options:completionHandler:)`, iOS 27 and later; below
27, `setActive` on a background queue) with `start()` finishing in a callback — for consistency, a start that
finishes later in every edition, and every caller (Start, the return to the foreground, the restart after a device
change and its settle, the tests) waiting for it. Not done; an issue of its own if a stall is ever seen.
