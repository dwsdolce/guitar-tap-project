# GuitarTap Android — Phase 0 Feasibility Record

The go/no-go record for [ANDROID-PLAN.md](ANDROID-PLAN.md) Phase 0. **Status: in progress (2026-09-15).** The
automated checks are done; the guitar comparison needs someone to tap the instrument.

**Spike:** `feasibility/` in the private [GuitarTapAndroid](https://github.com/dwsdolce/GuitarTapAndroid)
repo (see its README). App ID `com.dolcesfogato.guitartap.feasibility`.

## The decision this feeds

**Go** if, on the same reference guitar:
- (a) the Android spike's Air/Top/Back frequencies fall within the tap-to-tap spread of (c) the Swift
  iPhone/iPad build, **and**
- (a) is clearly better than (b) the web app in Chrome on the same Android device.

If (b) is already within the bar, reopen the WebView option before building a native edition.

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
| USB measurement mic | not yet tested |

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
  isn't calibrated; the plate test (§3 step 5) is still the real answer.

### Findings so far

1. **The first device does not advertise `UNPROCESSED`, but honours it** (see the survey above). It records
   from the bottom mic with no reported effects, ~24 dB below the other sources, with the flattest top end.
   **The plan's fallback order is not an edge case**, and recording the source used in each measurement is
   justified.
2. **The low end is unknown where it matters most.** The lowest measurement Guitar Tap makes is the plate
   **fLC at ~35 Hz** (34–37 Hz across the `Tests/AllPlatforms` corpus; the analysis range starts at 30 Hz).
   The mic reports −2 dB at 80 Hz and −1.3 dB at 100 Hz, which is fine for the guitar Air mode (~85–130 Hz).
   But **the reported curve stops at 80 Hz, so it says nothing about 30–60 Hz**, where MEMS capsules and input
   high-pass filters typically roll off.

   A roll-off there would hurt fLC in two ways:
   - **Detection:** the fLC tap is already the quietest, so the peak can drop below Peak Min.
   - **Frequency bias:** fLC is broad (Q ≈ 6, ~6 Hz wide), so a steep slope across it tilts the
     interpolated vertex upward.

   fLC is measured successfully on every existing platform, so this is a question about **Android
   hardware**, not the method. The survey shows none of the planned sources filters 20–60 Hz; the plate
   test in §3 answers whether the capsule itself reaches 35 Hz.
3. **Silencing is detectable directly.** Launched onto a locked screen, every source was silenced:
   `AudioRecordingConfiguration.isClientSilenced() == true`, and samples were exactly zero. That validates the
   plan's extra watchdog signal (Phase 3). It also means an app capture must never be tested with the screen
   locked.
4. **Point the bottom edge at the instrument.** UNPROCESSED, VOICE_RECOGNITION and MIC all record from the
   `bottom` microphone.
5. **UNPROCESSED is ~24 dB quieter than every other source.** Tap levels and peak magnitudes in dBFS will
   sit correspondingly lower. The default tap threshold (−40 dBFS) and Peak Min (−60 dB), tuned on the
   existing platforms, may be too high for it. Watch the level meter during the guitar test; if it matters,
   the real app needs per-source (or measured) level handling. This is a new item for the plan.

## 3. Still to measure (needs the guitar)

Use the same reference guitar, tap point and tap strength throughout. Keep the device at a fixed distance,
with the tablet's bottom edge toward the soundhole for Android. Take 10 taps per row.

1. ✅ **Source survey with sound present** — done 2026-09-15; results in §2. A rerun would settle the
   VOICE_PERFORMANCE low-frequency anomaly (optional).
2. **Android spike, per source.** Measure tab, label `<guitar>`, guitar type as appropriate, *Record session
   WAV* on. For each of UNPROCESSED, VOICE_RECOGNITION and MIC: Start → 10 taps → Stop. Export CSV + summary
   at the end. Statistics are grouped per source automatically.
3. **Web in Chrome on the same tablet:** the live app, guitar mode, number of taps 10. Save or export the
   result.
4. **Swift on iPhone or iPad:** guitar mode, number of taps 10. Save or export the `.guitartap` / PDF.
5. **Plate fLC (~35 Hz), the low-frequency bar.** Use the corpus reference plate (fL 67 / fC 117 / fLC 36 Hz
   on UMIK-1). With the spike recording (source UNPROCESSED, then MIC), run a full plate session: several L,
   C and FLC taps, with pauses between phases. Replay each session WAV through the Swift app's Play File
   (Material Plate, measure fLC) and compare fL/fC/fLC with the reference values and with a Swift
   iPhone/iPad measurement of the same plate. If the tablet's built-in mic loses or shifts fLC, repeat with
   the UMIK-1 on the tablet: that decides whether Android needs a USB mic for plates.
6. **Optional:** a UMIK-1 over USB-C. Plug it in with the Diagnostics tab open, which logs the device id and
   name on attach. Unplug and replug to check the name is stable. Select it as the input device and repeat
   step 2 for one source.
7. **Cross-check:** replay one spike session WAV through the Swift app (Play File, guitar, 10 taps). Its
   result should equal the spike's own power-averaged result, confirming the capture — not the port — is
   what's being measured.

Pull the Android results:

```bash
MSYS_NO_PATHCONV=1 adb -s HA2KFBS4 pull /sdcard/Android/data/com.dolcesfogato.guitartap.feasibility/files/ \
  ~/src/GuitarTapAndroid/feasibility/results/tb305fu/
```

### Results (to fill in)

Mean ± SD over 10 taps; the spread is the SD.

| Row | Air Hz | Top Hz | Back Hz | Air dB | Notes |
|---|---|---|---|---|---|
| (c) Swift iPhone/iPad | | | | | |
| (a) Android UNPROCESSED | | | | | |
| (a) Android VOICE_RECOGNITION | | | | | |
| (a) Android MIC | | | | | |
| (b) Web / Chrome on tablet | | | | | |
| (a) Android + UMIK-1 | | | | | |

Plate, reference values fL 67 / fC 117 / fLC 36 Hz (UMIK-1). Spike rows are session WAVs replayed through
Swift Play File.

| Row | fL Hz | fC Hz | fLC Hz | fLC dB | Notes |
|---|---|---|---|---|---|
| Swift iPhone/iPad (note the mic) | | | | | |
| Android UNPROCESSED, built-in mic | | | | | |
| Android MIC, built-in mic | | | | | |
| Android + UMIK-1 | | | | | |

## 4. Recommendation

*Pending the measurements in §3.*
