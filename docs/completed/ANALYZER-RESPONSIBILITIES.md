# The analyzer holds the library and copies of settings

**Issue:** [#40](https://github.com/dwsdolce/guitar-tap-project/issues/40)

Status: **CLOSED, NOT NEEDED (owner, 2026-10-24).** The first reason below was the live peaks, published on the
analyzer every frame — fixed by #41 (`completed/LIVE-PEAKS.md`); with them gone the analyzer announces nothing per
frame (`test/detected-peaks`). The other two are known and judged not worth a restructure on their own: each setting
copy has one writer (the analyzer's setter saves it) and none has been found disagreeing with the store. Reopen if one
does, or if the library has to change for another reason.

## The problem

The analyzer (`TapToneAnalyzer` / `tap_tone_analyzer.py` / `tapToneAnalyzer.ts`) analyses the sound. It also holds
two things that are not analysis:

1. **The saved-measurements library** — the list, its storage, import, export, delete and duplicates.
2. **Copies of settings** — Peak Min, the tap-detection threshold, the annotation visibility and (Swift, Python) the
   analysis frequency range live in the settings store *and* on the analyzer, kept in step by hand: read from
   settings at startup, written back when they change. Loading a measurement also writes its Show Unknown Modes, guitar type, measurement
   type and annotation visibility into settings from inside the analyzer.

## Why it matters

- **Views redraw at FFT rate.** In Swift the analyzer is one `ObservableObject`; it announces a change for any of its
  ~50 published values, never for one, so a view watching it for a rarely-changing value redraws whenever anything
  on it changes. The only values that changed per frame were the live peaks, now their own object (#41); the library
  and the setting copies change only on the user's action.
- **One value, two places.** A setting held on the analyzer and in the settings store can disagree; every change
  has to remember to update both.
- **Responsibilities blur.** Storage, import/export and settings policy sit in the class that does the analysis.

## Where it is

| | Library | Setting copies | Settings written from the analyzer |
|---|---|---|---|
| Swift | `TapToneAnalyzer.swift:379` (`savedMeasurements`); `TapToneAnalyzer+MeasurementManagement.swift` | `TapToneAnalyzer.swift:115, 129, 132, 285, 655`; restored at `:1505–1510` | `TapToneAnalyzer.swift:117, 287, 811`; `+MeasurementManagement.swift:776–785, 920` |
| Python | `models/tap_tone_analyzer.py:337, 1583`; `tap_tone_analyzer_measurement_management.py` | `tap_tone_analyzer.py:308–313, 379` | `tap_tone_analyzer.py:1335, 1405, 1999` |
| Web | `state/tapToneAnalyzer.ts:1990` | `tapToneAnalyzer.ts:676, 1724, 2495` (the range, `:770–771`, is a constant) | `tapToneAnalyzer.ts:682, 1203, 1240, 1730, 2207, 2212, 2501` |

## The direction (to be decided)

- **The library in its own object** — a measurements library holding the list, its storage, import, export, delete
  and duplicates; Saved Measurements and the analyzer's save and load use it.
- **Settings read from the settings store, no copies** — the analyzer and the views read the store; nothing mirrors
  it. Who carries out "a loaded measurement's settings become the app's" is to be decided (whatever owns loading).
- **Swift's observation** — whether the split objects stay `ObservableObject` or the model moves to `@Observable`
  (per-property tracking; the deployment targets allow it, `GuitarTapApp.swift` already uses it) is to be decided;
  the shape of the split is the same in all three either way.
