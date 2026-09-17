# GuitarTap Android — Phase 0 Record

What [ANDROID-PLAN.md](ANDROID-PLAN.md) Phase 0 asked, and what came back. **Status: Phase 0 complete
(2026-09-16).** Both questions are answered yes, with working hardware in hand.

**Spike:** `feasibility/` in the private [GuitarTapAndroid](https://github.com/dwsdolce/GuitarTapAndroid)
repo (see its README). App ID `com.dolcesfogato.guitartap.feasibility`. It stays as a measuring instrument
for Phase 3, not as a gate.

## The two questions

| | Question | Answer |
|---|---|---|
| 1 | Can the app capture usable audio? | ✅ **yes** — §2 |
| 2 | Can a USB measurement mic be used? | ✅ **yes, through a USB hub** — not when attached directly; §3 |

Question 2 decides whether USB mic support ships in the first release, not whether the port happens. On
this tablet a UMIK-1 works through a cheap USB 2.0 hub but not attached directly — a quirk of the tablet's
controller with full-speed devices, now measured rather than guessed (§3).

**Everything else is development work.** An earlier draft of this record set a go/no-go on comparing
Air/Top/Back against Swift on a real guitar, with per-source tap statistics. That was wrong twice over:

- **No other edition was gated that way.** Swift, Python and web were each built first and compared
  afterwards — `Tests/AllPlatforms/` was captured 2026-07-30 as a pre-ship gate for 1.0.2, not a
  prerequisite for writing any of them. Android's corpus capture belongs in the same place, at release.
- **A poor result wouldn't have stopped anything.** Every plate and brace capture in that corpus used a
  UMIK-1 (one Linux run excepted), so a weak built-in mic means "use a measurement mic for plates", as on
  every other platform.

The gate that *does* have precedent — numeric agreement with the oracle, which is what the web port's
Phase 2 required — was met before any instrument was tapped (§1).

## 1. Is the Kotlin analysis a faithful port? — ✅ yes

`core` (pure Kotlin/JVM) ports the web edition's FFT, peak finding, mode classification, spectrum averaging,
WAV codec, and guitar tap path:
- 1024-sample chunks, a 200 ms pre-roll
- absolute threshold with 3 dB hysteresis and 2-chunk confirmation
- 0.5 s warm-up on the audio clock
- a 65536-sample capture, rectangular FFT

Replaying the oracle fixtures through it (`./gradlew :core:test`):

| Case | Worst Δ frequency | Worst Δ magnitude | Oracle tolerance |
|---|---|---|---|
| REG-G1 (`Recording 5.wav`, 1 tap) | 0.0007 Hz | 0.001 dB | 1 Hz / 1 dB |
| REG-G2 (`Recording.wav`), each of 8 taps vs the Swift per-tap table | 0.0063 Hz | 0.003 dB | 1 Hz / 1 dB |
| REG-G2 power-averaged | 0.0007 Hz | 0.001 dB | 1 Hz / 1 dB |

So any difference measured on a device comes from **the audio input, not the analysis**. The session WAV writer
also round-trips bit-exactly through the decoder, so every spike recording can be replayed through the
canonical Swift app with Play File.

## 2. Device matrix

| | Lenovo Tab **TB305FU** |
|---|---|
| Android / API | 15 / 35 |
| SoC | MediaTek MT8786 |
| `SUPPORT_AUDIO_SOURCE_UNPROCESSED` | **false** |
| Output rate / frames per buffer | 48000 / 256 |
| `FEATURE_AUDIO_PRO` / `LOW_LATENCY` / `USB_HOST` | false / true / true |
| Input devices | 2 × BUILTIN_MIC (address `bottom` id 16, `back` id 17), plus telephony/submix/FM/type-28 virtual inputs |
| Mic capsule (reported) | Knowles **SPH1642HT5H** (both), omni, −41 dBFS/Pa |
| Reported frequency response | 80 Hz −2.0 dB · 100 Hz −1.3 · 500 Hz 0 · 1 kHz 0 · 5 kHz 0 · 10 kHz +1.8 |
| Rates offered | 8/16/32/44.1/48 kHz; 1–2 channels |
| Delivered rate (default request) | 48000, `bufferSizeInFrames` 48000 |
| Routing by source | UNPROCESSED / VOICE_RECOGNITION / MIC / VOICE_PERFORMANCE / VOICE_COMMUNICATION → `bottom` mic; CAMCORDER → `back` mic |
| Effects Android reports | none on any source **except** VOICE_COMMUNICATION (Acoustic Echo Canceler + Noise Suppression) |
| USB measurement mic | works **through a USB 2.0 hub**; fails attached directly. Verified with a UMIK-1 and a Blue Snowball, both full-speed — §3 |

Probe and survey reports: `GuitarTapAndroid/feasibility/results/tb305fu/reports/`.

### Source survey — TB305FU, 2026-09-15 15:19 (`survey-1789510787.txt`)

Method:
- Each source recorded 3 s in turn, with a steady broadband sound in the room, tablet unlocked and in the
  foreground. Nothing was silenced.
- Band power comes from a Welch spectrum (8192-point Hann).
- Shape is given **relative to each source's 400–1000 Hz band**, so gain differences drop out and only the
  frequency shape remains. The room sound isn't flat, so each source's shape means little alone; what
  matters is the difference **vs UNPROCESSED**, since all sources heard the same room.
- This assumes the sound stayed steady across the ~20 s run.

> The raw report's band columns read **39.1 dB high** (a missing ÷N in the spike's Welch normalisation,
> fixed afterwards). The offset is identical in every cell, so the shapes below are unaffected. Once it is
> removed, each source's band sum matches its measured RMS within 0.1 dB.

| Source | Mic | RMS dBFS | Effects reported | 20–60 | 60–150 | 150–400 | 1–4 k | 4–10 k |
|---|---|---|---|---|---|---|---|---|
| UNPROCESSED | bottom | **−69.8** | none | −16.0 | −5.1 | −0.1 | +0.1 | −8.0 |
| VOICE_RECOGNITION | bottom | −45.4 | none | −15.3 | −5.2 | +0.6 | +0.6 | −15.6 |
| MIC | bottom | −43.8 | none | −18.8 | −5.7 | −2.3 | +2.1 | −15.5 |
| CAMCORDER | **back** | −43.2 | none | −42.7 | −29.2 | −4.9 | +0.3 | −13.1 |
| VOICE_PERFORMANCE | bottom | −39.4 | none | −5.3 | −3.4 | 0.0 | 0.0 | −8.2 |
| VOICE_COMMUNICATION | bottom | −29.7 | AEC + NS | −56.3 | −18.9 | −5.1 | +0.3 | −21.8 |

Difference in shape **vs UNPROCESSED** (dB; negative = that source cuts the band):

| Source | 20–60 | 60–150 | 150–400 | 1–4 k | 4–10 k | Level vs UNPROCESSED |
|---|---|---|---|---|---|---|
| VOICE_RECOGNITION | +0.7 | −0.1 | +0.7 | +0.5 | −7.6 | +24.4 dB |
| MIC | −2.8 | −0.6 | −2.2 | +2.0 | −7.5 | +26.0 dB |
| CAMCORDER | **−26.7** | **−24.1** | −4.8 | +0.2 | −5.1 | +26.6 dB |
| VOICE_PERFORMANCE | **+10.7** | +1.7 | +0.1 | −0.1 | −0.2 | +30.4 dB |
| VOICE_COMMUNICATION | **−40.3** | **−13.8** | −5.0 | +0.2 | −13.8 | +40.1 dB |

What it shows:
- **UNPROCESSED is honoured in practice even though the device doesn't advertise it.** It is the only source
  without ~24–30 dB of gain, and it keeps the most above 4 kHz. So it is a genuinely different, less-processed
  path, not a silent alias of another source.
- **VOICE_RECOGNITION matches UNPROCESSED below 4 kHz within 0.7 dB**, down to the 20–60 Hz band. It adds
  gain and a cut above 4 kHz, which is outside the 30–2000 Hz analysis range. It is a sound fallback on this
  device, as the plan orders it.
- **MIC applies a mild EQ tilt** (−2.8 dB at 20–60 Hz, +2 dB at 1–4 kHz). Usable, but third choice, as
  planned.
- **CAMCORDER and VOICE_COMMUNICATION are unusable** for tap tones: −27 to −40 dB at 20–60 Hz and −14 to −24 dB
  at 60–150 Hz, which would take out fLC and threaten Air. CAMCORDER also moves to the back mic, so its
  low-frequency loss may be the capsule's porting rather than a filter. It is out either way. The plan's
  "never VOICE_COMMUNICATION" stands.
- **VOICE_PERFORMANCE is unexplained:** +10.7 dB at 20–60 Hz vs UNPROCESSED, and the highest gain. It may be a
  bass-shaping path, or a low-frequency disturbance during its 3 s slot. **Rerun the survey** before reading
  anything into it; it isn't in the plan's source order regardless.
- **None of the three planned sources filters out 20–60 Hz** (all within 3 dB of UNPROCESSED). That is the
  precondition for fLC. It does **not** give the capsule's absolute response at 35 Hz, because the room sound
  isn't calibrated — that shows up in the corpus capture at release time, as for every other edition.

### Findings so far

1. **The first device does not advertise `UNPROCESSED`, but honours it** (see the survey above). It records
   from the bottom mic with no reported effects, ~24 dB below the other sources, with the flattest top end.
   **The plan's fallback order is not an edge case**, and recording the source used in each measurement is
   justified.
2. **The low end is uncharacterised below 80 Hz — a device property, not a blocker.** The lowest measurement
   Guitar Tap makes is the plate
   **fLC at ~35 Hz** (34–37 Hz across the `Tests/AllPlatforms` corpus; the analysis range starts at 30 Hz).
   The mic reports −2 dB at 80 Hz and −1.3 dB at 100 Hz, which is fine for the guitar Air mode (~85–130 Hz).
   But **the reported curve stops at 80 Hz, so it says nothing about 30–60 Hz**, where MEMS capsules and input
   high-pass filters typically roll off.

   A roll-off there would hurt fLC in two ways:
   - **Detection:** the fLC tap is already the quietest, so the peak can drop below Peak Min.
   - **Frequency bias:** fLC is broad (Q ≈ 6, ~6 Hz wide), so a steep slope across it tilts the
     interpolated vertex upward.

   fLC is measured successfully on every existing platform, so this is a question about **this tablet's
   capsule**, not the method. The survey shows none of the planned sources filters 20–60 Hz, which is the
   part the software controls. Whether the capsule itself reaches 35 Hz shows up in the corpus capture at
   release — and if it falls short, the answer is a USB measurement mic, which is what every corpus plate
   and brace capture used anyway.
3. **Silencing is detectable directly.** Launched onto a locked screen, every source was silenced:
   `AudioRecordingConfiguration.isClientSilenced() == true`, and samples were exactly zero. That validates the
   plan's extra watchdog signal (Phase 3). It also means an app capture must never be tested with the screen
   locked.
4. **Point the bottom edge at the instrument.** UNPROCESSED, VOICE_RECOGNITION and MIC all record from the
   `bottom` microphone.
5. **UNPROCESSED is ~24 dB quieter than every other source.** Tap levels and peak magnitudes in dBFS will
   sit correspondingly lower. The default tap threshold (−40 dBFS) and Peak Min (−60 dB), tuned on the
   existing platforms, may be too high for it. Carried into Phase 3 as a design note, not an open question.

## 3. Can a USB measurement mic be used? - YES, through a hub (2026-09-16)

A miniDSP **UMIK-1** (`VID_2752 / PID_0007`) works on the Lenovo TB305FU **when attached through a USB 2.0
hub**, and never works attached directly.

| Attachment | Result |
|---|---|
| Mic straight into the tablet's USB-C port | powered (LED on), **never enumerates** - bus shows only the root hub, hot-plugged or across a reboot |
| Mic through a USB 2.0 hub | **enumerates and records** |
| Samsung T7 SSD straight into the tablet, same cable | enumerates (`04e8:4001`, 500 mA) |
| Mic + cable on an iPad / on the Windows PC | works |

### Why: the mic is a full-speed device

Through the hub the kernel reports it plainly:

```
05e3:0608 'USB2.0 Hub'                     speed=480
2752:0007 'Umik-1  Gain: 18dB'  speed=12   power=100mA
```

**`speed=12` - 12 Mbps, USB full speed.** The SSD that worked directly is high/super speed. MediaTek's MUSB
host does not bring up a directly attached full-speed device here; a hub carries it because the hub provides
the transaction translator. That also explains why power, cable and mic all tested fine individually while
the combination failed.

Throughout the direct-attachment failures the tablet's own side was correct - `current_mode=dfp`,
`data_role=host`, `power_role=source`, `otgenable=y`, controller `cmode=1`, role switch `host`, no USB
data-signaling restriction - and `/sys/bus/usb/devices/` held only the root hub, so enumeration never
started. `dmesg` is closed on a production build, so the kernel's own account is out of reach.

### What works, measured

With the hub in place the whole path is live, with no code change:

- Android exposes it: `USB-Audio - Umik-1  Gain: 18dB`, `card=1;device=0`, `type=USB_DEVICE`, id 29.
- **Android auto-routes recording to it** - the spike asked for no preferred device and
  `AudioRecord.getRoutedDevice()` reported the UMIK-1.
- Capture: 48 kHz mono float, `silenced=false`, `clientEffects=[]`, `deviceEffects=[]`.
- An 8-second session recorded real room noise through it (RMS -68.9 dBFS, peak -53.3 dBFS) - a plausible
  quiet-room level for a low-sensitivity measurement mic, and certainly not digital silence.
- `MicrophoneInfo` reports no sensitivity or frequency response for it, unlike the built-in capsules. The
  `.cal` file remains the only source of correction data, as on every other edition.

### A second USB mic, same story

A **Blue Snowball** (`0d8c:0005`) behaves identically: `speed=12` (full speed), invisible attached directly,
fine through the hub. Android exposed it as `USB-Audio - Blue Snowball` (`card=1;device=0`, id 66),
auto-routed capture to it, and the spike recorded 48 kHz mono float with no effects — about 8.5 dB hotter
than the UMIK-1 on the same source, as a condenser would be.

Two full-speed mics failing directly and working through a hub is the pattern, not a one-device accident.
For Guitar Tap's purposes the Snowball is a usable input for **frequencies and Q**, which are properties of
the instrument; anything in dB (Peak Min, tap-tone ratio, material magnitudes) still wants the UMIK-1 and
its `.cal` file, and fLC at ~35 Hz sits below the Snowball's usual rated range. That is the same
mic-versus-measurement-mic distinction as on every other edition, with nothing Android-specific about it.

### What this means

- **USB measurement mics are in scope for the first release.** The plate/brace workflow, which uses a UMIK-1
  on every other platform, is available on Android too.
- **Tell the user when a hub is needed.** A direct connection that silently does nothing is exactly the
  failure a luthier would blame on Guitar Tap. If no input device appears, the app should say that some
  devices only enumerate a measurement mic through a powered hub.
- **Phase 3 still needs a stable device key, and the measurement confirms which fields to use.** Across one
  unplug/replug of the mic:

  | Field | Before | After |
  |---|---|---|
  | `AudioDeviceInfo.getId()` | 29 | **40** — changed |
  | `productName` | `USB-Audio - Umik-1  Gain: 18dB` | unchanged |
  | `address` | `card=1;device=0` | unchanged |

  So the key is type + `productName` (+ `address`). Note `address` is the ALSA card index, which is stable
  for a single USB audio device but would move if a second one were attached, so `productName` is the part
  to lean on. The USB device also advertises its own capabilities — rates 8/16/32/44.1/48 kHz, 1–2
  channels, encodings 2/4/21 — unlike the built-in capsules.

### Working with the tablet over Wi-Fi

The tablet has one USB-C port, so a USB mic and a USB cable to the PC are mutually exclusive. `adb pair`
over wireless debugging failed repeatedly here ("protocol fault"), but plain `adb connect` works without
pairing, because this PC's adb key was already authorised during the earlier cable session:

```bash
adb mdns services                      # find adb-<serial> _adb-tls-connect._tcp <ip>:<port>
adb connect <ip>:<port>
```

Wireless debugging switches itself off on reboot, and the port changes every time it is re-enabled, so
rediscover with `adb mdns services` after each boot.

## 4. Recommendation

**Build it.** Both things that could have made a native Android edition pointless are settled or harmless:

- The Kotlin DSP already matches the parity oracle to 0.007 Hz and 0.003 dB (§1) — the same gate the web
  port's Phase 2 had to pass.
- The audio input path on the first device is clean (§2): float PCM at 48 kHz, unprocessed input honoured
  even though it isn't advertised, no effects, and nothing filtering 20–60 Hz on the three sources the plan
  uses.
- The USB mic question (§3) came back **yes, through a hub**, measured end to end: Android routes to the
  UMIK-1 and the spike records from it at 48 kHz with no effects. So the plate/brace workflow — which uses a
  measurement mic on every other platform — is available on Android, with a hub as the documented
  requirement on this tablet.

Carry these into Phase 3 rather than treating them as open risks:

1. **`UNPROCESSED` runs ~24 dB quieter** than the other sources. The default tap threshold (−40 dBFS) and
   Peak Min (−60 dB) are tuned for the other editions and will need attention.
2. **Source and device are measurement metadata.** Record both with every measurement, as the sample rate
   already is.
3. **`isClientSilenced` is a direct signal** for the dead-input watchdog — Android silences capture for an
   app that isn't in the foreground, which reads as pure digital silence.
4. **Not every device advertises `UNPROCESSED`** (this one doesn't, yet honours it), so the fallback ladder
   is load-bearing, not decoration.
