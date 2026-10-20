# Python: the app crashes at start when PortAudio cannot start

**Issue:** [#37](https://github.com/dwsdolce/guitar-tap-project/issues/37)

Status: **OPEN — reported; no code changed (owner, 2026-10-20).**

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
back to ALSA. CI is being given a sound server (PipeWire, a dummy device) so it tests as a desktop has it.

**For the Linux session:** CI's Linux runner is now Ubuntu 26.04 (from 2026-10-20). Running the Python suite on a
machine without a sound server — a VM with no desktop session — fails the same way until this is fixed; on a desktop
with PipeWire running it is unaffected.

## Who it affects

A Linux machine with no sound server, or one PortAudio cannot reach. Current desktops run PipeWire, so users are
unlikely to meet it; a headless or minimal system would.

## Items

| # | Item | Status |
|---|---|---|
| 1 | The app starts when PortAudio cannot, and reports the input unavailable as Swift and the web do | open |
