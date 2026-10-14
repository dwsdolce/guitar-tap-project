# The audio comes from a microphone other than the one shown

**Issue:** [#30](https://github.com/dwsdolce/guitar-tap-project/issues/30)

**Status:** ✅ COMPLETE 2026-10-13 — fixed in Swift and Python, verified live by the owner on
macOS. Commits: Swift `c2f954a`, Python `637af16`. Web: no change needed. Four findings recorded and
left (items 5–7 and "Not established").

**In one line:** on macOS, Swift could show the USB microphone as selected while its engine was
recording the built-in one — healthy audio, no warning, and nothing in the app that could notice.

## Found

**The report (2026-10-12).** During a three-edition comparison of the same taps, Swift's results did
not match the other two. Its recordings were a different signal: 14–19 dB louder, the room noise
before the tap correlating with Python's at only 0.23–0.25 (the same microphone gives 1.0), the tap
about 2 ms later. Python's and the web's recordings were bit-identical to each other. Settings in
all three showed the UMIK-1. The owner had started Swift and then plugged the microphone in.

**What the log showed** (Swift, 2026-10-13 05:14 UTC, with the engine's own device logged at each
start and three seconds after):

| When | The engine's input device | Running inside Swift |
|---|---|---|
| At the restart on the UMIK-1 | the UMIK-1, 2 channels — the selection | the UMIK-1 |
| 3 s later | `CADefaultDeviceAggregate` (the built-in microphone + speakers), 1 channel | the aggregate; the UMIK-1 no longer |

The selection, its saving and the restart all ran as designed. macOS then moved the running engine
to its default aggregate device.

**Why nothing noticed.**
- The app asks the engine for the selected device at each start and reads the answer back once. It
  never asked again.
- macOS announces the change with `AVAudioEngineConfigurationChange`, and the app rebuilds the engine
  when it receives one (it did, correctly, at 18:54 UTC the same day). But the listener is registered
  just after each start, and here it was registered 1.7 s after — the main thread was stalled while
  macOS processed the new device. No notice was logged; it is taken to have arrived in that gap.
- Audio kept arriving, with signal, so the buffer watchdog and the dead-input watchdog both saw a
  healthy input.
- `logAudioRouteDiagnostics()` already compared the engine's device with the selection and logged
  "MISMATCH" — but only when a watchdog fired or a notice arrived.

**The trigger.** It happened when the web edition, its tab visible, opened the UMIK-1 just after
Swift had: in the failing runs another application was running the UMIK-1 three seconds after Swift's
restart. With the web's tab hidden the web stayed on the built-in microphone and four plug-ins in a
row were clean. Python was running in both. What the other application changes about the device is
not established. Any application opening the same microphone could do it; it does not need our
other editions.

**What the earlier work did not cover.** The microphone-selection record
([`MIC-SELECTION.md`](MIC-SELECTION.md)) tabulates every device event against
what is "in use" and what is "saved" — and takes "in use" to be what the app shows. Its review step
for a plug-in passes on "the input switches to it; Settings shows it", which this fault satisfies.
The reviews were run one edition at a time. Another application taking the shared microphone
"through an aggregate device" was named as a cause of stalled audio in June 2026 and of silent audio
in July; audio that stays healthy from the wrong device was not considered.

## Items

| # | Item | Swift | Python | Web |
|---|---|---|---|---|
| 1 | The watchdog checks the engine's device against the selection, and restarts on a mismatch | ✅ | n/a | n/a |
| 2 | A mismatch that restarts cannot clear is shown in the status line | ✅ | n/a | n/a |
| 3 | The engine's device is logged at each start and 3 s after | ✅ | — | — |
| 4 | A stream opened on a device other than the selected one is a failed open | n/a | ✅ | not needed |
| 5 | The configuration-change listener is registered late | left | — | — |
| 6 | iOS: three weaker spots | left | — | — |
| 7 | The web does not follow a plug-in while its tab is hidden | — | — | left |

**1. The device check (Swift, macOS).** `watchdogDecision` takes `onSelectedDevice` and has two more
outcomes: `.wrongDevice` — audio is flowing and carries signal, from another device — and
`.wrongDeviceExhausted`. Starvation and a dead input rank above it. `engineInputIsSelectedDevice()`
reads the input unit's current device on every watchdog tick; an aggregate device that contains the
selected one counts as it (after an unplug the engine sometimes runs the built-in microphone through
the aggregate, which is the selection). A mismatch goes through the same bounded restarts as the
other watchdog outcomes. Always true on iOS, where the system routes the input.
- *Tests:* `WatchdogDecisionTests` — healthy audio from another device is `.wrongDevice`; out of
  attempts it is `.wrongDeviceExhausted`; back on the selected device after that is `.healthy`;
  starvation and dead input outrank it. Removing the outcome fails a case.
- *Verified live (owner, 2026-10-13 21:11 UTC):* the engine was moved to the aggregate about three
  seconds after a plug-in; "Device watchdog: the engine's input is not the selected device —
  restarting on it" followed, and the engine was back on the UMIK-1 half a second later and stayed.
  Swift was on the wrong microphone for about six seconds — the watchdog's four-second start-up grace
  plus its tick.

**2. The warning (Swift).** `inputIsNotSelectedDevice` puts "⚠ Input is not the selected microphone —
choose it again in Settings" in the status line, below the dead-input warning and above clipping.
*Not exercised live:* one restart has always been enough.

**3. The log (Swift).** `logEngineInputState` writes, at each start and three seconds after, the
engine's device beside the selected one, the system default, the input format, and every audio
device's running state with an aggregate's sub-devices (`🔎` lines; debug logging only).

**4. The opened device (Python).** PortAudio binds a stream to its device when it opens it and does
not fall back, so the Swift fault cannot occur. But a stream is opened by PortAudio's device *index*,
a position that changes whenever PortAudio is re-initialised, and one path still opened by a stale
one: the watchdog's restart re-initialises PortAudio and re-points only the selected device, so a
device chosen afterwards from the list carried its old index. Found by reading, not reproduced.
`_verify_opened_device` reads back the device a stream was opened on and compares its name with the
selected device's; another device's stream is closed and treated as a failed open, which keeps the
previous device and shows "Microphone Unavailable".
- *Tests:* `test_mic_selection.py` MS32 (a renumbered list never leaves a stream on another device),
  MS33 (the right index opens). Removing the check fails MS32.

**Web — not needed.** A browser's audio track is bound to one device for its life, the web opens it
by exact device id, and the microphone it shows is read from the track after every open. *Not
established:* whether a track opened on the browser's default input stays on the original device
when the system default later changes.

**5. The listener (left).** Registering `AVAudioEngineConfigurationChange` before the engine starts
would close the 1.7-second gap and shorten the time on the wrong device. It was left: start-up
timing in that code has a history of faults (a heap-corruption race; a guard that read its flag too
late), and item 1 catches the fault whatever caused it.

**6. iOS (left).** *Decision (2026-09-27, [`MIC-SELECTION.md`](MIC-SELECTION.md)):*
iOS is left as it is — the system routes the input. From reading the code, not tested: the app
reacts to three kinds of route change (new device, device removed, category change) and ignores the
rest; a restart that fails after a route change is only logged, with no retry; nothing handles an
audio interruption.

**7. The web and a hidden tab (left).** Seen in the runs above; not investigated.

## Run-review

Debug logging on in Swift. A USB microphone; the built-in microphone as the system default.

1. Start the web with its tab **visible**, then Python, then Swift with the USB microphone unplugged.
   → All three on the built-in microphone.
2. Plug the USB microphone in and wait ten seconds. → Swift's log shows the engine's device "is the
   selected device" three seconds after the restart, or a "Device watchdog" line followed by a
   restart onto it. The status line shows no warning.
3. Repeat step 2 several times. → No run ends on another microphone. *Passed (owner, 2026-10-13).*

The pass criterion is the log line, not what Settings shows: Settings showed the right microphone
throughout the fault.

## Not established

- What another application changes about the device that makes macOS move the engine.
- Whether macOS could move the engine back after every restart; it has not.
- When the fault began. The last proof that Swift recorded from the UMIK-1 alongside the other
  editions is 2026-07-16.
