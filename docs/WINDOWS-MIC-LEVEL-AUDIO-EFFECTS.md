# Windows: microphone level far too low (Windows audio effects)

**Issue:** [#20](https://github.com/dwsdolce/guitar-tap-project/issues/20) · customer thread
[dwsdolce/guitar_tap#2](https://github.com/dwsdolce/guitar_tap/issues/2)

Status: **FIX COMMITTED, not yet verified by the customer.** Cause confirmed, and the customer has a
settings workaround. Python `3892bf2` (RAW mode) and `b5b98e3` (fallback hardening and tests), web
`bdd70d8`. Swift needs no change. Still open: the customer runs a build with the fix while his audio
effects are switched back on (see [Verification](#verification)).

## The customer's problem

Reported by email by Gary, on an Acer Aspire 5 laptop running Windows 11. Both of his microphones, an
Audio-Technica ATR2100x USB mic and the laptop's built-in Intel Smart Sound array, read so low in the
Python edition that no Threshold setting caught a tap. The same mics worked in Visual Analyzer, in other
recording software, in the web edition, and through a Focusrite preamp. He first saw it in 1.0.376. He
had probably never run an earlier build, so this was not a regression. The developer's Windows test
machine (UMIK-1 and its built-in mic) worked normally.

## Diagnosis

### Theories going in

- **Downmix cancellation.** Guitar Tap opens WASAPI shared mode with `channels=1`, so PortAudio averages
  a 2-channel endpoint to mono. Phase-inverted channels (a known Realtek quirk on laptop arrays) would
  cancel the tap. **Ruled out**: see below.
- **An unpinned audio stack.** `sounddevice>=0.5.5` ships its own PortAudio DLL, so a rebuild could
  change it. No audio code changed around 1.0.376. **Not the cause**, but see
  [Follow-ups](#follow-ups).

### The probe program

`Tooling/mic-probe/mic_probe.py` in guitar_tap is a standalone console program that uses only
sounddevice and numpy. It is built to `GuitarTapMicProbe.exe` by `Tooling\mic-probe\build_win.bat`,
from the release `.venv`, so it carries the same PortAudio DLL as the app. Its last change is `a70e2a4`.

It opens one microphone several ways **at the same time**, so every configuration hears the same taps:

| Label | How it opens the mic |
|---|---|
| `gtap` | exactly as Guitar Tap does: WASAPI shared, 1 ch, device default rate, float32, blocksize 1024 |
| `wasapi-N` / `mme-N` / `dsound-N` | each host API at the endpoint's native channel count (no downmix) |
| `raw-N` | WASAPI shared with the RAW stream option (added in probe 1.1) |
| `excl-N` | WASAPI exclusive: a separate 20 s take afterwards, because exclusive mode can't share the device (added in 1.1) |

The user keeps quiet for 5 s, then taps. The probe writes one WAV per configuration and `report.txt`,
then zips them to the Desktop. The report gives, per channel: peak, loudest 1024-sample chunk RMS (the
level the Threshold is compared with), noise floor, ch1/ch2 correlation (−1 means phase-inverted), and a
verdict. Probe 1.1 also flags a noise floor below −110 dB as gated or suppressed, since no real mic's
self-noise is that low.

Distribution: attached to the public customer issue, because an `.exe` attachment is blocked by mail
filters even inside a zip. Results came back by email, since they contain the customer's Windows user
name. They are kept in guitar_tap `customer_tests/` (git-ignored) on the Windows development machine.

### What the recordings showed

**Round 1 (probe 1.0)**
- `gtap` read within 0.3 dB of every other configuration, and ch1/ch2 correlation was +1.00. **How
  Guitar Tap opens the mic was not the problem, and the downmix theory was ruled out.**
- The level was already low before any app saw it. Both mics showed the same pattern: each tap decayed
  smoothly into digital silence, with floors of −124 dB (ATR2100x) and −112 dB (array). At 16-bit (MME),
  73% of the quiet samples were exactly zero. A real ATR2100x always hisses at about −80 to −95 dB, so
  something was gating the signal. The taps themselves were at about −75 to −95 dB (100 ms RMS).
- The same result on two unrelated mics and across WASAPI, MME and DirectSound pointed to processing in
  the Windows shared-mode audio path that applies to every endpoint.
- (His third file was "Stereo Mix", a loopback of what the laptop plays rather than a mic. It was
  ignored.)

**Round 2 (probe 1.1, ATR2100x only)**

| Run | `gtap` loudest chunk | `gtap` floor | `raw-2ch` | `excl-2ch` |
|---|---|---|---|---|
| Effects as shipped (`20260929-162246`) | −74.7 dB | −124.3 dB (flagged gated) | **−6.2 dB**, floor −69.6 | **−4.8 dB**, floor −70.9 |
| Audio enhancements **Off** (`20260929-163329`) | −3.6 dB | −65.4 dB | −4.3 dB | −4.3 dB |

- **The loss is about 70 dB.** With effects on, the RAW stream recorded the same taps as `gtap`, at the
  same moment, **68.5 dB louder**. With effects off, every configuration agrees to within about 2 dB.
- RAW mode bypasses the effects while staying in shared mode. Exclusive mode also bypasses them, but
  locks other apps out of the mic.
- With effects off and Input volume at 100, peaks reach −0.1 dBFS. That is at clipping, so the customer
  may want Input volume nearer 80.

## The OS setting that worked around it

Settings → System → Sound → *(the microphone)* → **Audio enhancements**. It offers **Off**, **Device
default effects** and **Voice clarity**, and it was on Device default effects. Setting it to **Off**
fixed Guitar Tap right away: background noise became visible and taps registered. The customer switched
it on and off again to confirm. The setting applied to the USB mic as well as the built-in array. That
is why a USB mic, which normally avoids a laptop's audio processing, was affected too.

Voice-oriented suppression treats a guitar tap, a short non-voice transient, as noise, and gates the
silence in between. That explains both the low taps and the impossibly low noise floor.

## The fix, so the setting isn't needed

| Edition | Change | Commit |
|---|---|---|
| Python, Windows | Open the input stream in **WASAPI RAW** mode | `3892bf2`, `b5b98e3` |
| Python, macOS / Linux | none: PortAudio opens Core Audio / ALSA with no system effects in the path | — |
| Web | add `voiceIsolation: false` to the `getUserMedia` constraints | `bdd70d8` |
| Swift, iOS | none: the session already uses mode `.measurement`, which minimises system processing | — |
| Swift, macOS | none: voice processing is never enabled, and mic modes apply only to voice-processing apps | — |

**Python.** `_open_input_stream` in `realtime_fft_analyzer_device_management.py` is now the one place
all three opens go through: start, device switch (`_open_device`) and the PortAudio re-initialise. On
Windows, for a WASAPI device, `_wasapi_raw_settings` builds `sd.WasapiSettings()` and sets
`PaWasapiStreamInfo.streamOption = eStreamOptionRaw` directly, because sounddevice has no RAW option. The
struct `version` must stay 1; PortAudio rejects version 2 with `paIncompatibleHostApiSpecificStreamInfo`,
which was found while building probe 1.1. If the device refuses RAW, the stream opens as before. If the
device can't be queried, it opens plainly and reports the device's own error. If sounddevice lacks the
internals, the log says RAW is unavailable. The log states which open was used.

*Why RAW and not exclusive:* both bypassed the effects on the customer's laptop (−6.2 and −4.8 dB).
RAW stays in shared mode, so other apps can use the mic at the same time, and it opens alongside other
streams. Exclusive mode locks the device, fails if another app holds it, and would make Guitar Tap
unusable next to a DAW or a call. For a measurement app, skipping voice processing is the right default,
and it matches what the other editions already ask for.

**Web.** The web edition already turned off `echoCancellation`, `noiseSuppression` and
`autoGainControl`, and the customer's web runs worked with the effects still on. So the browser (Chrome)
already appears to capture without the Windows effects when processing is off. This is inferred from
his result and not checked in the Chromium source. `voiceIsolation: false` also covers newer Chrome's
exposure of OS voice isolation. Browsers that don't know the constraint ignore it.

**What no edition can bypass:** DSP inside the hardware (some USB mics and headsets; Intel Smart Sound
array processing on the audio chip), or a noise-cancelled virtual mic the user picks on purpose (Krisp,
NVIDIA Broadcast, PipeWire echo-cancel).

## Verification

Done:
- **Cause:** confirmed by the customer's own switching of the setting, and by the Round 2 recordings.
- **The RAW mechanism on the affected hardware:** the probe's `raw-2ch` stream sets the same
  `streamOption` as the app. On the customer's laptop, with effects on, it recovered 68.5 dB on the same
  taps as `gtap`.
- **The app's open, on the development Windows machine:** a WASAPI device (Intel array) opens RAW and
  delivers audio. MME, the Sound Mapper and the default device take the plain path. That machine has no
  effects, so RAW and plain read the same there. This checks that the open works, not that it fixes
  anything.
- **Tests:** `tests/test_wasapi_raw_open.py` (`b5b98e3`, runs on any OS). It covers: not Windows; a
  non-WASAPI device; a WASAPI device opened RAW; RAW refused, so a plain open; a device that can't be
  queried, so a plain open; a failed plain open raises. Mutations (no RAW option, no fallback, no query
  guard) each fail a test. Python full suite 823 passed. Web `tsc` clean. In both repos, the
  self-regression baseline tests fail only because the baselines have not been re-minted, which is
  unrelated.

Not done yet:
- **A Guitar Tap build with `3892bf2` + `b5b98e3` on the customer's laptop, with Audio enhancements back
  on Device default effects.** Taps should register with no settings change, and the log should show
  "WASAPI RAW stream". The customer has offered to beta test.

## Follow-ups

- **Pin sounddevice for the Windows build.** RAW sets sounddevice's private `_streaminfo`. A release
  that renames it would silently bring the effects back: the app logs a warning and keeps working
  without RAW. `requirements.txt` still says `sounddevice>=0.5.5`.
- **Probe:** `desktop()` uses `%USERPROFILE%\Desktop`. On a OneDrive-redirected Desktop, results land
  in a folder the user doesn't see. The probe opens that folder when it finishes, so it hasn't mattered
  yet.
