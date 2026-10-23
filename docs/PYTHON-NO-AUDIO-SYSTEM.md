# Python: the app crashes at start when PortAudio cannot start

**Issue:** [#37](https://github.com/dwsdolce/guitar-tap-project/issues/37)

Status: **OPEN — item 1 fixed (Python `7a7fe98`); the check on Linux with no sound server to do.**

## What happens

`models/realtime_fft_analyzer.py:83` imports `sounddevice` at module level, and `sounddevice` initialises PortAudio
while it is imported. If PortAudio cannot start, the import raises:

    sounddevice.PortAudioError: Error initializing PortAudio: Unanticipated host error [PaErrorCode -9999]:
    'PulseAudio_Initialize: Can't connect to server'

and nothing that imports the audio code loads — the app does not start. Swift and the web start in the same
situation and report "Audio input unavailable" in the status bar and on the chart.

## How it was found

On 2026-10-20 GitHub's `ubuntu-latest` runner moved from Ubuntu 24.04 to 26.04. On 26.04 PortAudio connects to a
PulseAudio-protocol server when it starts (on a desktop, PipeWire's `pipewire-pulse`); the runner has none, so every
Python test that imports the audio code failed to load (Python `283b131`, run on `ubuntu-latest`). On 24.04 it fell
back to ALSA. CI now runs a sound server — PipeWire with its PulseAudio service and a dummy device — so it tests as a desktop has
it (Python `bbc8ca4`; with it, SR6 fakes its device list, which it had been reading from the machine).

**For the Linux session:** CI's Linux runner is now Ubuntu 26.04 (from 2026-10-20). Running the Python suite on a
machine without a sound server — a VM with no desktop session — fails the same way until this is fixed; on a desktop
with PipeWire running it is unaffected.

## Who it affects

A Linux machine with no sound server, or one PortAudio cannot reach. Current desktops run PipeWire, so users are
unlikely to meet it; a headless or minimal system would.

## Items

| # | Item | Status |
|---|---|---|
| 1 | The app starts when PortAudio cannot, and reports the input unavailable as Swift and the web do | fixed (Python `7a7fe98`); Linux check to do |

**1. The app starts when PortAudio cannot** (owner, 2026-10-22).
- *Cause:* `sounddevice` starts PortAudio (`_initialize()`) in the last statement of its module; two of the app's
  modules imported it as they loaded (`realtime_fft_analyzer.py`, `realtime_fft_analyzer_device_management.py`),
  so a failed start failed the import and the app. Once running, Python already reports a failed start as Swift
  and the web do: `start()` sets `input_could_not_start`, and the placeholders read "Audio input unavailable".
- *Fix:* `models/audio_backend.py` loads `sounddevice` once for every module and keeps the module when only its
  PortAudio start fails — everything in it is defined before that statement. Every import takes `sd` from there
  (the app's seven, and `test_export_e2e.py`'s — a test change: it patched the module by importing it, which
  fails the same way). PortAudio is started again where it is needed (`ensure_portaudio_started`): before each
  device listing (an error leaves the list as it was) and at the engine's start (a `PortAudioError` leaves the
  input unavailable; started there, its devices are listed first). The restart-on-plug starts PortAudio when it
  had not started, instead of failing on `_terminate()`. Python-only (`@parity none`): Swift and the web have no
  import step that can fail.
- *Tests:* `test_no_audio_system.py` — in a fresh interpreter, PortAudio's library wrapped so that its start fails
  with the same error (`PaErrorCode -9999`): a plain import fails; the app's modules load, no device is listed, a
  start raises `PortAudioError` and the input reads "Audio input unavailable"; once PortAudio can start, the next
  listing starts it. Before the fix, the analyzer's module cannot be imported under the same simulation. The
  device, restart and export tests pass (76); on the Mac PortAudio starts and lists its inputs as before.
- *To do:* the check on Linux with the sound server stopped (`systemctl --user stop pipewire pipewire-pulse`):
  the app starts and reads "Audio input unavailable"; with the server started again, a relaunch has the input
  (a failed start is not retried by itself — New Tap keeps the running processing thread — as in Swift, where
  a device change or a relaunch starts it again).
