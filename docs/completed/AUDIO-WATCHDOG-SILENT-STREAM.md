# Audio watchdog — blind to a stream that delivers SILENCE

**Status:** ✅ DONE — Issue #4 closed 2026-09-17; archived here 2026-09-18. Fixed on all three
editions (Swift `61e8a5d`/`665125a`/`0fd11d4` · Python `ed9d953`/`8ff34ae`/`c74dde4` · web
`3e9493a`/`54a9a25`/`c6bd36b`) — see "Implementation" at the end. Found 2026-07-16 during 1.0.2 testing (web); **recurred on macOS/Swift
2026-08-21** during a class (idle between taps, and again after wake-from-sleep), which is what
prompted the fix. Was not blocking 1.0.2 (self-recovers, needs a contending app, corrupts no
measurement).
**Scope:** **CONFIRMED on all three** (2026-07-16, incident 3 below) — they share the stamp-on-arrival
watchdog design ([[project_buffer_delivery_watchdog]], added 2026-06-29).

## The gap, in one line

The watchdog's definition of "alive" is **chunks are arriving** — not **chunks contain audio**. A stream
delivering digital silence is indistinguishable from a healthy one, so the app goes deaf with **no
recovery and no console output**.

```js
private onChunk(data: ChunkMessage): void {
  this.lastChunkTime = performance.now()   // ← stamped on EVERY chunk, whatever it contains
  ...
  this.processChunk(data.samples, data.rms)
}
```

`checkBufferWatchdog` only fires when `performance.now() - lastChunkTime > watchdogSilenceMs` (2500 ms).
A silent-but-flowing stream refreshes that stamp every ~21 ms forever → the watchdog concludes "healthy"
and never runs. **It was built for a silently-wedged input but detects the wrong silence:** it catches
"no chunks", and misses "chunks of silence" — which is the likelier real-world failure (device
contention, route change).

## Evidence — two incidents, web, 2026-07-16

Both while **three apps shared one UMIK-1** (Swift + Python + web), which is the suspected trigger.

1. **Frozen.** Mic level dead, New Tap did nothing. Browser mic-in-use indicator **on**; Swift/Python
   kept working from the same device. **Console empty.** Reloaded to recover.
2. **Half-alive.** The Threshold/amplitude meter went **dormant** while the peak indicator kept
   **changing but below −100 dB**. Persisted several minutes, then **recovered by itself**.
   **Console empty.**
3. **ALL THREE went deaf at once — the decisive one.** Every app read ≈ −100 dB simultaneously. The
   device was **genuinely dead**: macOS **System Settings → Sound → Input showed level 0**, so no app
   could have produced audio. (System Settings only *corroborated* it — that meter is coarse and needs a
   loud sound to move at all. **Our own Threshold/VU meter is the more sensitive instrument**: it reads
   dBFS down to ≈ −100, so a live UMIK-1 visibly ticks along at the ≈ −70 room floor while a dead one
   pins near −100. The app can see this long before the OS meter would.) Yet CoreAudio still advertised the device as healthy and default —
   `Umik-1 Gain: 18dB · Default Input Device: Yes · 48000 · Transport: USB` — and **all three apps sat
   reporting ~−100 dB as though fine: no warning, no recovery attempt, no log.** Recovered by
   unplugging/replugging the UMIK-1 (USB re-enumeration). Suspected trigger: the interface wedged after
   hours with **three simultaneous clients**.

**Incidents 1–2 are per-client** (only the web went silent; Swift/Python kept working) — a wedged
`getUserMedia` stream. **Incident 3 is device-level** (all clients). Different causes, *identical*
consequence: **a dead-but-present device keeps delivering chunks — of silence — and "chunks arriving"
is the only thing the watchdog measures.** The silence was the hardware's fault; the **silent failure**
is ours. This is exactly the case the watchdog was written for, and it missed on every platform.

**The empty console is the tell.** Incident 2 is diagnostic: chunks *were* arriving and the FFT *was*
running (peak values moving) — on near-nothing. The pipeline was alive; the audio wasn't. The room's
noise floor sits near −70 dB (the Air peak measures ≈ −63), so a sustained peak below −100 dB is not a
quiet room — it is a dead stream. Incident 1 is almost certainly the same state, caught earlier.

**Hypotheses this refuted** (recorded so they aren't re-chased):
- *Suspended AudioContext (backgrounded tab)* — **refuted**: Safari sat backgrounded behind VS Code for
  minutes with all three apps still taking audio. Browsers keep a context alive when it has a live mic
  source. The watchdog also deliberately skips a non-`running` context.
- *Watchdog exhausted its 6 attempts and stopped* — **refuted**: that path logs loudly
  (`gave up after 6 attempts`). The console was empty, so it never fired at all.

## Fix — needs design, not a quick patch

Add a **signal-level** criterion alongside the arrival criterion: sustained peak/RMS below ~−100 dBFS
while armed means a dead stream, not a quiet room.

**There is ~30 dB of headroom for the threshold.** The UMIK-1's room floor sits near −70 dB and its Air
peak ≈ −63; a dead stream reads ≈ −100. Note the UMIK-1 reads *low on every host* (user, 2026-07-16) —
that is the mic's inherent sensitivity, **not** a macOS defect and not something to "fix" — so the low
absolute numbers are stable and a −100 dBFS floor is comfortably below anything real.

**The risk is false positives**, and it is real: a muted mic, an unplugged interface, or a genuinely
silent input must **not** be "recovered" in a loop. Any rule needs a long dwell time and must not fight
a user who has legitimately muted their input. Consider also surfacing it rather than only auto-healing —
**even without recovery, "no audio input" in the status line beats an app that looks alive while deaf.**

Verify on all three (the design is shared). The `dsp/`-level tests can't see this — it is an engine/stream
concern, so it needs either a fake stream that emits zeros or a live check.

## Why it isn't a 1.0.2 blocker

It self-recovers, it needs another application contending for the device, and it never produces a *wrong*
measurement — it produces *no* measurement, visibly. The user-visible harm is confusion, not bad data.

---

## Implementation (2026-08-22) — ⏳ not yet user-verified

Built to this doc's design. Where the code diverged from a first attempt, this doc's field
evidence is what corrected it.

**The criterion.** A second liveness stamp, refreshed only by chunks whose **RMS** exceeds
**1e-5 (-100 dBFS)**; no signal for **15 s** while running trips it. RMS, not peak, on all three —
the floor/peak figures above are RMS-based, and peak ≥ RMS would otherwise give the ports different
sensitivities.

**Why the threshold sits at the bottom of the headroom, not the middle.** A first cut used
-120 dBFS on the assumption that a dead stream delivers digital zero. This doc's incident 2 refutes
that — the values were *changing* below -100 dBFS, so a -120 dBFS threshold would have been cleared
by the dead stream and **would never have fired**. Corrected to -100 dBFS. It was then also tempting
to use the middle of the 30 dB headroom (-90 dBFS), but the **UMIK-1 is an unusually quiet
microphone and can sit near -90 dBFS in a silent room** (user, 2026-08-22) — that would call a quiet
workshop a dead input and restart the engine mid-measurement. The asymmetry decides it: a missed
detection costs one more watchdog cycle; a false positive interrupts real work.

**Surfacing, as this doc asked.** `inputAppearsDead` is published to the status line as
**"⚠ No audio input — check the microphone connection"**, resolved through a single
precedence point (dead input > clipping > the analyzer's own message) so the two overrides cannot
fight or leave a stale warning. This matters most for incident 3: a device-level failure **cannot**
be fixed by restarting the engine — it needed a USB re-enumeration — so recovery exhausts its six
attempts and stops, and the status line is then the only thing standing between the user and an app
that looks alive while deaf.

**Also added on Swift**, from the 2026-08-21 recurrence: an `AVAudioEngineConfigurationChange`
observer (there was none anywhere in the app) that rebuilds the engine through the hardened restart
path, and `logAudioRouteDiagnostics()` — the AUHAL's bound device vs the selected device, the
device's `IsAlive`, and AUHAL `IsRunning` — logged at the moment a wedge is detected, to separate
"the device vanished" from "the device is fine but the stream is dead".

**Web**: `track.onmute` was a deliberate no-op whose comment assumed a mute stops delivery. It does
not — a muted `MediaStreamTrack` keeps feeding zeros — so the delivery watchdog never fires. It now
back-dates the signal clock by half the window (a transient mute self-resolves; a persistent one
trips the watchdog) and `onunmute` resets it.

**Tests** (`@parity dead-input-threshold`, all three): the calibration table is pinned —
0 / -120 / -100 dBFS read as dead; **-95 and -90 dBFS read as ALIVE** (the quiet-UMIK-1 regression);
-70 / -63 / -20 dBFS read as alive; the threshold must keep ≥10 dB of margin under -90 dBFS; and the
dwell must exceed the delivery threshold. As this doc predicted, the `dsp/`-level suites can't see
the engine concern, so the criterion was extracted to a testable unit rather than tested through a
live stream.

**Not done:** verification by running. The 2026-08-21 class session ran clean with none of the new
detectors firing, so the fix is so far unexercised — absence of the failure, not proof of the cure.
