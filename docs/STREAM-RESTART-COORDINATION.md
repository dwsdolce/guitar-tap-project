# Python: stream-restart coordination after a hung close

**Issue:** [#24](https://github.com/dwsdolce/guitar-tap-project/issues/24)

Status: **IMPLEMENTED 2026-09-29 — awaiting run-review.** Commit: Python `3b864e8`. Python only (the PortAudio edition). Follows
[#21](https://github.com/dwsdolce/guitar-tap-project/issues/21), whose record
([`completed/MIC-SELECTION.md`](completed/MIC-SELECTION.md)) found both problems and left them as items 21–22.

## Why now

There are reports of audio disappearing in the released Windows Python edition, needing the app to be
restarted. The cause of those reports is not known; these two problems are known ways for Python to lose its
audio after a stream close hangs, and the owner wants every such way minimised (owner, 2026-09-29: "doing
anything we can to minimize that makes sense to me").

## Items

| # | Item | Python |
|---|---|---|
| 1 | A PortAudio re-initialise skipped for a pending close is retried | ✅ |
| 2 | The watchdog's recovery and the hot-plug refresh follow Swift's ordering | ✅ |

**1. A skipped re-initialise is never retried** (#21 item 21). While a timed-out stream close is still
pending, `terminate_and_reinitialize_portaudio` does not terminate PortAudio (terminating would wait on the
stuck close forever — the macOS freeze of #21 item 16). Nothing retries it, so PortAudio's device list stays
as it was and a microphone connected afterwards may never appear. Seen in the Linux VM (#21 item 20).
- *Decision (owner, 2026-09-29):* retry it (a) when the pending close finishes, and (b) on the watchdog's next
  check once no close is pending, as a fallback.
- *Done:* a skipped re-initialise sets `_portaudio_reinit_owed`; a completed one clears it.
  `_retry_owed_reinit` asks for the device refresh (the same `_on_devices_changed` path a hot-plug uses, which
  re-initialises PortAudio and reopens the selected device) when a re-initialise is owed and no close is
  pending. The stuck close's own thread calls it when it finally finishes (clearing `_pending_stream_close`
  first); every watchdog tick calls it too. The debt stays until a re-initialise actually happens, so a refresh
  dropped by a guard is asked for again on the next tick.

**2. A pending watchdog recovery runs after a refresh has reopened the stream** (#21 item 22). Swift's recovery
stops the engine when it schedules its restart; a device switch while the engine is stopped only changes the
selection; the restart then opens whichever device is selected. Python's recovery leaves the stream open until
its delayed restart, and a hot-plug refresh in between opens a stream of its own — which the late restart then
tears down, re-initialising PortAudio under it. Each needless teardown is another chance of a hung close; that
is how the #21 freeze began (macOS, t=139.96 s).
- *Decision (owner, 2026-09-29):* Python follows Swift's ordering — the recovery closes the stream when it
  schedules the restart; a refresh during a pending recovery only updates the selection; the restart opens the
  selected device.
- *Done:* `_attempt_watchdog_recovery` closes the stream before scheduling `_do_watchdog_restart`.
  `_on_devices_refreshed_impl`, while `_is_recovering`, applies the device list (the selection) and opens
  nothing, logging that the pending restart will open the device. `reinitialize_portaudio` opens the selected
  device at that device's rate and calls `_on_stream_reopened`; the analyzer's handler re-reads the device name
  and recomputes the frequency bins (Swift's `start()` updating `actualSampleRate` and the bins).

## Tests

`tests/test_stream_restart_coordination.py` (Python only, `@parity none`):
- SR1 — an owed re-initialise waits while the close is pending, and is asked for once it is not.
- SR2 — a close that outlived its 2 s timeout, when it finally finishes, asks for the skipped re-initialise.
- SR3 — the watchdog tick asks for an owed re-initialise (the fallback).
- SR4 — scheduling a recovery closes the stream, then schedules the restart.
- SR5 — a refresh during a pending restart selects the new device and opens no stream.
- SR6 — the restart opens the selected device at its own rate and reports the reopen.

Mutations — the finishing close not retrying, the tick not retrying, the recovery keeping the stream open, a
refresh opening during a pending restart, the restart keeping the old rate — each fail their case (SR6's fake
stream first had to run at the rate it was opened with; a fixed-rate fake let that mutation through). Full
Python suite 810.

## Run-review steps

Launch: `.venv/bin/python -m guitar_tap`, with debug logging on (`_gt_log_enabled = True` in
`utilities/logging.py`) so the log shows these paths. macOS and Windows; a USB mic (the UMIK-1).

1. *(Observational — unbounded; nothing can force it.)* Leave the app running and in use. → Audio is never
   lost; no restart needed. If it is lost, the log from that machine is the evidence.
2. With the USB mic in use, unplug and replug it several times in quick succession. → Each time the input
   follows (built-in on unplug, the USB mic on replug) and audio keeps flowing. If the log shows "A stream close
   is still pending — PortAudio not re-initialised", a later "Retrying the PortAudio re-initialise…" follows and
   the device list is current afterwards (plugging the mic in is seen).
3. *(Observational — a pending recovery cannot be triggered by hand; SR4–SR6 test the ordering.)* If a log
   shows a watchdog recovery attempt followed by a device change before it runs, it also shows "Device refresh
   during a pending watchdog restart — the restart opens '…'", then a single restart on that device.
