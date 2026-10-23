# Python: the app crashes at start when PortAudio cannot start

**Issue:** [#37](https://github.com/dwsdolce/guitar-tap-project/issues/37)

Status: ✅ **CLOSED 2026-10-22** — item 1 done: Python `7a7fe98`. The app starts when PortAudio cannot and reports "Audio input unavailable", as Swift and the web do; checked on Ubuntu 26.04 with no sound server (GitHub's runner) and on Linux Mint 22.3.

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
| 1 | The app starts when PortAudio cannot, and reports the input unavailable as Swift and the web do | done |

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
- *Checked (2026-10-22):*
  - Linux Mint 22.3 (Ubuntu 24.04), the sound server stopped (its sockets too: `systemctl --user stop
    pipewire.socket pipewire-pulse.socket`, then the services) (owner): the app runs and has audio — this
    PortAudio reaches the sound card through ALSA without a server, so the failure cannot occur there.
  - GitHub's `ubuntu-latest` (Ubuntu 26.04.1), no sound server — a one-off workflow, removed after its run
    (Python `9e66ad4`, `db138ca`; run 39897796254): a plain `import sounddevice` fails with
    `PaErrorCode -9999 … 'PulseAudio_Initialize: Can't connect to server'`; the app's modules load with
    PortAudio not started, a start raises that error and the analyzer reads "Audio input unavailable"; the app
    itself, launched off-screen, is still running after 15 s.
  - A failed start is not retried by itself — New Tap keeps the running processing thread — as in Swift: a
    relaunch, or a device change, starts it again.
