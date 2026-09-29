# Microphone selection — which input the app uses, and what it remembers

**Issue:** [#21](https://github.com/dwsdolce/guitar-tap-project/issues/21)

Status: **IMPLEMENTED 2026-09-27 (items 1–12), revised 2026-09-28 (items 13–17) — awaiting run-review.** Commits: Swift `fb1b27f`, Python
`aecefc3`, web `6dc6f5c`; items 13–14: Swift `8b76a3c`, Python `d37fb9b`, web `a8faa6e`; items 15–17: Swift `9beddbc`,
Python `e348256`, web `34eec92`; item 18: Swift `4cf0987`, Python `9dfb7be`, web `c7850c9`. All three editions (Swift, Python, web).

## Found

**The report (owner, 2026-09-25):** in the Python app, choose the built-in microphone, quit, relaunch — BlackHole
(a virtual audio device) comes back, and the saved choice is overwritten.

**Python — three selectors, eight extra writers.**
- The canvas startup code (`views/fft_canvas.py`, device resolution before the engine is built) replaces a
  saved built-in microphone with any "not built-in" device and saves it ("heal the persistence"); with nothing
  saved it applies its own default/external rule and saves that. It then derives the sample rate and the
  initial calibration from its choice, before the engine exists.
- The engine's `_auto_select_initial_device` restores the saved device — by then the canvas's replacement.
- The Settings dialog (`_show_settings`) picks a device by its own rule on every open (saved → system default)
  and calls `set_device` and saves.
- Besides the engine's `selected_input_device` setter, the views write the saved device eight times
  (`fft_canvas.py` ×2, `tap_tone_analysis_view.py` ×6).

**Swift — one path.** The engine's `selectedInputDevice.didSet` saves every assignment. Startup (macOS): saved
→ any device `isBuiltInMic` says is not built-in → system default → first. `isBuiltInMic` reads the CoreAudio
transport type, so a virtual device (BlackHole) counts as external. The doc comment on
`loadAvailableInputDevicesMacOS` lists built-in as step 2; the code takes external. Unplugging the active
device falls back (external → first) and saves the fallback.

**Web.** Startup: the saved device id, else the browser's default input. No built-in/external ranking. A new
device is switched to; an unplugged active device falls back to the default. The saved device is written by
the React hook (`useAudioEngine`, two sites), not the engine.

**Why "external first" existed.** A USB microphone that drops out is replaced by a fallback, and the fallback
is saved; if the app is quit before the microphone returns, the next launch restores the fallback. Python's
override repaired that by preferring any external device over a saved built-in one — the rule that took
BlackHole. Only Swift on macOS can tell a virtual device from a real one; Python (PortAudio) and the web see
names only.

## Decision (owner, 2026-09-27)

Saved choice always wins; no device classification. "To make it predictable and reliable requires your
proposal. Let's do it then." — then, after comparing it with the user manual (which it leaves correct: the
manual's one promise, §2.3 "persists across launches", becomes unconditional), "Do the full proposal please."

Three questions raised before implementation were taken as recommended with that go:
- a measurement load's switch to its recorded microphone is for the session, not saved (item 7);
- iOS is left as it is — the system routes the input there, and the saved device is not consulted;
- one engine method saves a choice (Swift `chooseInputDevice`, Python `choose_input_device`, web
  `chooseInputDevice`); assigning the selected device only selects.

## Items

| # | Item | Swift | Python | Web |
|---|---|---|---|---|
| 1 | Startup: saved → system default → first | ✅ | ✅ | ✅ |
| 2 | Saved only on a user choice or a plug-in; never a fallback | superseded by 13 | superseded by 13 | superseded by 13 |
| 3 | Plug-in: switch to the new device (and save it) | ✅ | ✅ | ✅ |
| 4 | Unplug: the startup rule again, not saved | superseded by 13 | superseded by 13 | superseded by 13 |
| 5 | No built-in / external / virtual ranking | ✅ | ✅ | ✅ |
| 6 | One owner: the engine chooses and saves | ✅ | ✅ | ✅ |
| 7 | A measurement load's microphone switch is not saved | superseded by 13 | superseded by 13 | superseded by 13 |
| 8 | Web: a measurement load switches to its recorded microphone | — | — | ✅ |
| 9 | Settings lists the engine's devices; opening it re-enumerates nothing | — | ✅ | ✅ |
| 10 | Python: the system default is the listed host API's default | — | ✅ | — |
| 11 | The load switch is in place before the load's calibration check | ✅ | ✅ | ✅ |
| 12 | Choosing a calibration is saved by the model, not the view | ✅ | ✅ | ✅ |
| 13 | Every selection is saved; an unplug falls to the default (revised decision) | ✅ | ✅ | ✅ |
| 14 | A threshold is saved by the model's setter, so a load's thresholds are saved | — | ✅ | #1 |
| 15 | Python: a renumbered device keeps its selection with its fresh index | — | ✅ | — |
| 16 | Python: no PortAudio terminate while a close is pending; a failed watchdog restart retries | — | ✅ | — |
| 17 | A device that fails to open is not selected or saved; the previous is kept; a popup says so | ✅ | ✅ | ✅ |
| 18 | The load's two warnings reworded, each under its own title | ✅ | ✅ | ✅ |

**1. Startup.** The saved device if present; otherwise the system default input; otherwise the first device.

**2. What is saved.** A device the user chooses, or plugs in while the app runs, is saved. A fallback (startup
default, or after an unplug) is used for the session only, so a microphone that drops out is not forgotten.

**3. Plug-in.** A newly connected device is switched to and saved. Swift keeps its exclusion of Continuity
(iPhone) devices. Virtual devices that appear on their own are not excluded (left out unless it bites).

**4. Unplug.** The active device disappearing selects by the startup rule — the saved choice if it is
present (the active device may have been a session-only one), else the system default, else the first — for
the session.

**5. No ranking.** Swift `isBuiltInMic` and Python `_is_builtin_mic` / `_BUILTIN_MIC_KEYWORDS` go.

**6. One owner.** The engine chooses and saves, as Swift's `selectedInputDevice` does. Python: the canvas
startup selection goes (sample rate and calibration follow the engine's choice); Settings shows the engine's
current device and does not choose one on open; the eight view writes go. Web: saving moves from the hook into
the engine. Swift: the device-selection doc comment describes these rules.

**7. Load switch.** Loading a measurement whose recorded microphone is connected switches to it (Swift
`setInputDevice`, Python `requestDeviceSwitch` → `set_device`) for the session; it is not saved. The web does
not switch on load (see Found, below).

## Done

- **Swift.** The saved UID moved into `TapDisplaySettings.selectedInputDeviceUID` (same key,
  `selectedInputDeviceUID`; isolated under test). `selectedInputDevice.didSet` no longer saves;
  `chooseInputDevice(_:)` selects and saves. `inputDeviceToUse(in:savedUID:systemDefaultUID:)` is the rule;
  `applyInputDeviceList(_:systemDefaultUID:isAutoSelectable:)` applies an enumerated list (first list → rule;
  new device → `chooseInputDevice`, Continuity excluded; selected device gone → rule), called by
  `loadAvailableInputDevicesMacOS` after enumeration. `isBuiltInMic` removed. The Settings picker binds
  through `chooseInputDevice`. The engine's start-time fallback reads the saved UID from `TapDisplaySettings`.
- **Python.** `input_device_to_use` is the rule; `apply_input_device_list` replaces
  `_auto_select_initial_device` / `_auto_select_on_hotplug`; `choose_input_device` selects and saves; the
  `selected_input_device` setter no longer saves. `_is_builtin_mic` / `_BUILTIN_MIC_KEYWORDS` removed. The
  engine enumerates and selects in its constructor, before its stream opens (as Swift's init does); the
  analyzer's `start` no longer enumerates. The canvas startup selection is gone; the canvas reads the
  engine's device for the initial calibration. The engine constructor's `device` parameter is gone. Settings
  shows the engine's device, selects nothing on open, and a pick calls `choose_input_device`; the combo
  rebuild shows the engine's device and switches nothing. The eight view writes are gone.
- **Web.** The engine reads and saves the device: `start()` takes no id and uses `acquireInputToUse` (saved
  if it opens, else the browser default); `setInputDevice` became `chooseInputDevice`, which saves; a plug-in
  calls it; an unplug uses `acquireInputToUse`. The hook's two saves are gone.
- **Tests.** New `test/mic-selection`, MS1–MS11, all three (web: MS1–MS3, MS6–MS10 — MS4/MS5 have no browser
  counterpart, MS11 no web load switch). Mutations — saving on every selection, a plug-in not saved (all
  three), an unplug falling to the default instead of the saved device (web) — fail them. Full suites: Swift
  669, Python 787, web 711; tsc and eslint clean.

**8–10 (owner, 2026-09-27: "you are going to fix the items you found… Please go").**
- **8.** The web matches the loaded measurement's microphone among the connected inputs (id, then name) and
  switches to it for the session, as the natives do; otherwise it warns that no connected microphone matches.
- **9.** Settings lists the engine's device list and opening it neither re-enumerates nor selects (Swift's
  picker over `availableInputDevices`). Python: the Windows PortAudio re-initialise on Settings open goes — a
  new device arrives only through the hot-plug path, which switches to it and saves it. Web: the refresh on
  Settings open goes; the list is the engine's.
- **10.** Python takes the default input of the host API its filtered list uses (WASAPI on Windows), falling
  back to PortAudio's global default.
- *Done (Python, 9 and 10):* Settings lists `mic.available_input_devices`; the Settings-open
  `reinitialize_portaudio` call is gone (the method stays — the buffer watchdog uses it); the combo rebuild
  reads the engine's list. `_system_default_fingerprint` reads the listed host API's `default_input_device`,
  then `sd.default.device`. Tests MS12–MS13 (Python only); mutation (host-API default ignored) fails MS12.
  Full suite 789.
- *Decision (owner, 2026-09-27):* the web's device handling moves to Swift's shape (option A) — "A for your
  first choice".
- *Done (web, 8 and 9):* the engine owns `availableInputDevices` (listed at start and on every hardware
  change; the attach/detach baseline), selects an input with `selectInput` — which loads that device's
  calibration from the store, Swift's `didSet` — and reports every change through `onDeviceStateChanged`;
  the hook only mirrors that state (its `applyCalibrationForDevice`, `refreshDevices` and App's
  Settings-open refresh and dead `calibrationRef` are gone; the calibration picker writes the store and
  calls `reloadDeviceCalibration`). `setInputDevice` switches for the session — selecting before its first
  await, the stream following — and `chooseInputDevice` is it plus the save. The analyzer's
  `loadMeasurement` follows Swift's block: with a recorded UID, match the connected inputs by id then
  name, switch, then compare calibration and sample rate; no match → Swift's not-found warning. The
  label-comparison helper `measurementWarning` and its tests (`g7-measurement-4c`) are gone.

**11. The load switch is in place before the check (Swift bug, verified 2026-09-27).** MS14 and MS15 failed
on Swift as found: when `loadMeasurement` returned, the engine was still on the old microphone and the
check warned against its calibration; on macOS the restart inside `setInputDevice` also ran before the
queued assignment, reopening the old device.
- *Decision (owner, 2026-09-27):* "Verify the swift bug and fix it if it is a problem - make sure
  swift/web/python agree."
- *Done:* Swift `setInputDevice` selects the device synchronously, before the restart and before it
  returns; its doc comment (split across two functions) repaired. Python's load switches itself
  (`self.set_device(match)`, then `inputDeviceSwitched` for the view's label) instead of asking the view
  to switch; the view no longer switches. Python's load acts only on a recorded UID, as Swift's does; its
  own device enumeration inside the load (unreachable now the engine enumerates at construction) is gone.
  The web's is item 8.
- *Tests:* MS14–MS17 in all three (the switch is in place when the load returns; the check reads the
  recorded microphone's calibration; no match → not-found warning, input unchanged; same microphone,
  different calibration → warning). Mutations — Swift's queued assignment, Python's switch left to the
  view, the web selecting after the stream opens — fail MS14/MS15. Full suites: Swift 673, Python 793,
  web 706; tsc and eslint clean.

**12. Choosing a calibration is saved by the model.** Swift: assigning `activeCalibration` — the picker and an
import do — makes its `didSet` save it as the global active calibration and for the selected device;
`setTemporaryCalibration` (file playback) and a device's own calibration loading save nothing. Python's
views and the web's hook wrote the store themselves.
- *Decision (owner, 2026-09-27):* "Do it."
- *Done:* Swift's `CalibrationStorage` reads and writes `TapDisplaySettings.defaults` (the standard defaults;
  an isolated suite under test — it wrote the real defaults before), and its class doc says what the lookup
  does (the device's mapping, else none; the global id records the last chosen). Python:
  `TapToneAnalyzer.choose_calibration` applies and saves (global id; the selected device's name key,
  removing any fingerprint key the lookup would read first); the import (main window and Settings), the
  picker and Clear All call it; Clear All clears the active calibration then deletes each stored one, as
  Swift's `deleteAllCalibrations` does (`CalibrationStorage.delete_all` removed); Settings shows the
  model's active calibration. Web: the engine's `chooseCalibration` applies and saves; the hook's import and
  picker call it; a delete stays a store action followed by `reloadDeviceCalibration`.
- *Tests:* MS18–MS20 in all three (a chosen calibration is saved for the device and restored on switching
  back; choosing none removes it; a temporary calibration saves nothing). Mutations — the device mapping not
  saved (all three), a temporary calibration saved (Swift) — fail them. Full suites: Swift 676, Python 796,
  web 709; tsc and eslint clean.

## Found during implementation

- **The web does not switch the input when a measurement is loaded**; both natives do → item 8.
- **The web's calibration picker wrote the store from the hook**, and so did Python's views → item 12.
- **Where a loaded threshold is saved — three ways (found 2026-09-28).** Swift: the model's `didSet` on
  `tapDetectionThreshold` / `peakMinThreshold` writes `TapDisplaySettings`. Python: the model's setters do
  not save; the view's slider handlers (`_on_tap_threshold_changed`, `_on_peak_min_changed`) write
  `AppSettings`, so a load's thresholds are saved only if those handlers run after it. Web: the analyzer
  hands App a `loadedSettings` patch and App's `updateSettings` saves it. → item 14 (Python); the web's
  settings store is recorded in #1.
- **Python's load clamps the thresholds it restores** (tap threshold to −80…−20 dB, Peak Min to −100…−20 dB);
  Swift assigns the recorded values. Not changed here.
- **The web deletes calibrations one at a time**; Swift and Python have only "Clear All Calibrations". A UI
  difference, not changed.
- **Python's Settings lists devices from its own PortAudio query**, not the engine's list → item 9.
- **Python on Windows:** the system default is found by PortAudio's global default index, which belongs to
  MME; the filtered list keeps WASAPI devices, so no default matches and the first device is used → item 10.
- **The web's device handling sits in the view layer** (found starting item 8). The React hook, not the engine,
  lists the devices (the engine keeps only their ids) and loads a device's calibration when the input changes
  (Swift: `selectedInputDevice.didSet`; Python: the `selected_input_device` setter). The web's load-time
  microphone check compares the recorded name with the current input's label; Swift and Python look for the
  recorded microphone among the connected devices, switch to it, then compare calibration and sample rate.
- **Swift's load-time calibration / sample-rate check reads the previous microphone.** `loadMeasurement` calls
  `setInputDevice(match)`, which assigns `selectedInputDevice` in `DispatchQueue.main.async`; the check that
  follows reads `fftAnalyzer.activeCalibration` and `actualSampleRate` before that runs — the microphone being
  switched away from. Python's switch (`requestDeviceSwitch`, a direct signal) completes before its check. From
  reading the code → item 11 (shown by MS14/MS15, fixed).

## Current behaviour — the cases (2026-09-28, under review)

Raised at run-review step 5 (owner, 2026-09-28): after an unplug the UI, Settings and a new measurement all
show the built-in mic, yet the next launch comes back on the USB mic. The table is the code as committed
(Swift `fb1b27f`, Python `aecefc3`, web `6dc6f5c`) — the same in all three except iOS, where the system routes
the input.

**Devices:** **B** built-in mic · **H** BlackHole (virtual, always present) · **U1**, **U2** USB mics. The
system default input is **B**. **In use** is what the app captures with — what the UI, Settings and a new
measurement show. **Saved** is what the app restores at the next launch. **⚠** marks a row where the two
differ.

### App not running → launch

| # | Situation | In use / Saved at launch | Note | Revised rule |
|---|---|---|---|---|
| 1 | Saved U1, U1 connected | **U1** / U1 | | U1 / U1 |
| 2 | Saved U1, U1 unplugged while closed | **B** / U1 ⚠ | default, not saved | B / B |
| 3 | Nothing saved (first launch), B, H and U1 present | **B** / nothing ⚠ | default; not U1, not H | B / B |
| 4 | Saved B, U1 plugged in while closed | **B** / B | | B / B |
| 5 | Saved H (the user chose BlackHole) | **H** / H | | H / H |

### App running — a device appears

| # | Before (In use / Saved) | Event | After (In use / Saved) | Note | Revised rule (After) |
|---|---|---|---|---|---|
| 6 | B / B | plug in U1 | **U1** / U1 | newest wins, saved | U1 / U1 |
| 7 | U1 / U1 | plug in U2 | **U2** / U2 | newest wins over a chosen USB mic | U2 / U2 |
| 8 | B / U1 (after a drop-out) | U1 comes back | **U1** / U1 | recovers | U1 / U1 (before: B / B — the drop-out saved B) |
| 9 | B / B | a virtual device appears (e.g. Zoom's) | **that device** / that device | ⚠ newest wins, even a virtual device | that device / that device |

### App running — a device disappears

| # | Before (In use / Saved) | Event | After (In use / Saved) | Note | Revised rule (After) |
|---|---|---|---|---|---|
| 10 | U1 / U1 | U1 unplugged or drops out | **B** / U1 ⚠ | step 5's case; relaunching with U1 connected gives U1 | B / B |
| 11 | U2 / U2, U1 also connected | U2 unplugged | **B** / U2 ⚠ | the default, **not U1**, though a USB mic is connected | B / B |
| 12 | U1 / U1, U2 also connected | U2 unplugged | U1 / U1 | not in use — nothing happens | U1 / U1 |

### App running — a Settings choice

| # | Before (In use / Saved) | Event | After (In use / Saved) | Note | Revised rule (After) |
|---|---|---|---|---|---|
| 13 | any | choose H in Settings | **H** / H | | H / H |

### App running — loading a measurement

| # | Before (In use / Saved) | Recorded with | After (In use / Saved) | Note | Revised rule (After) |
|---|---|---|---|---|---|
| 14 | B / B | U1, connected | **U1** / B ⚠ | switched for the session; relaunch gives B | U1 / U1 (saved, as the other loaded settings) |
| 15 | B / B | U1, not connected | **B** / B + warning | input **unchanged**, not the default | B / B + warning |
| 16 | U1 / U1 | U1 | U1 / U1 | warns only if calibration or sample rate differ | U1 / U1 |
| 17 | any | no microphone (a played file) | unchanged | no warning | unchanged |

### App running — a load, then New Tap

New Tap does not change the input in any edition: it captures with whatever is in use.

| # | Before (In use / Saved) | Event | After (In use / Saved) | Note | Revised rule (After) |
|---|---|---|---|---|---|
| 18 | U1 / B (after row 14's load) | New Tap, tap, save | **U1** / B ⚠ | the new measurement is captured with U1 and records U1 (and U1's calibration); Settings shows U1; relaunch gives B | U1 / U1 — a relaunch gives U1 |
| 19 | B / B (after row 15's load — U1 not connected) | New Tap, tap, save | **B** / B | captured with and records B | B / B |

### Against the owner's five points (2026-09-28)

1. **Plugging or unplugging while the app is not running has no effect** — holds (rows 2, 4).
2. **Adding or removing an external mic while running changes what is used and what is saved** — holds for
   adding (rows 6–9); **not for removing**: rows 10 and 11 change what is used but not what is saved.
3. **A load restores the recorded microphone** (easier to repeat the measurement; against: it changes the
   user's choice) — the load switches the input but does not save it (row 14): neither fully "restore" nor
   "leave alone". New Tap after it then captures with the loaded measurement's microphone (row 18), which the
   UI shows, but a relaunch returns to the one saved before the load.
4. **The selected mic missing** — at launch the fallback is the default (row 2); a load whose microphone is
   missing warns and **keeps the current input** (row 15), not the default.
5. **Drop-outs** — the conflict is visible: an added device is always taken as intent ("newest wins"), even a
   second USB mic (row 7) or a virtual device (row 9); a removed device is taken as an accident — not saved,
   and falling to the default rather than to another connected USB mic (rows 10, 11). The ⚠ rows are where
   those two views meet.

**Before #21:** Swift saved every change, so In use and Saved agreed in rows 2, 3, 10, 11 and 14 — and the
drop-out (row 10) came back on B after a relaunch. Python's startup override took any "non-built-in" device
over a saved B, so BlackHole could win over the user's choice (the #21 report).

## Revised decision — what is shown is what is saved (owner, 2026-09-28)

Run-review step 5 and the cases above showed the "a fallback is not saved" rule (item 2) leaves hidden
state: the Settings dialog, the UI and a new measurement show one microphone while the stored setting holds
another, and a later launch acts on a choice the user can no longer see — it looks like a preference for the
external mic. The owner: *"If the settings dialog shows it then it is in the settings file and used the next
time the app launches. And drop-out just has to live with it."* And for a load: *"A load of a measurement
changes the mic … just as if the user had made the selection"* — as a load does with the other settings it
restores (measurement type, guitar type, tap threshold, Peak Min; the number of taps is a main-screen
control, not a setting). *"I think I can live with this. It feels simpler and more predictable."*

**The rules (replacing items 2, 4 and 7):**
1. **Every change of input is saved** — a Settings choice, a plug-in, an unplug fallback, the launch
   default, and a load's switch. What Settings shows is what is stored and what the next launch uses.
2. **Launch:** the saved device when it is present, else the system default, else the first device.
3. **Running, a device is connected:** switch to it.
4. **Running, the device in use disappears:** the system default, else the first device.
5. **Load:** the recorded microphone connected → switch to it (saved, by rule 1), then the calibration /
   sample-rate check; not connected → keep the current input and warn.

**Accepted costs:** a microphone that drops out and does not return before quitting is replaced by the default
at the next launch; a second USB mic, or a virtual device that appears while running, takes over (row 7,
row 9) — visibly.

**Effect on the code:** the save-or-not split added for item 2 (`chooseInputDevice` / Python
`choose_input_device` / the web's save in `chooseInputDevice`, against an unsaved assignment) goes; all
three save on every selection, as Swift's `selectedInputDevice.didSet` did before #21. Tests MS6, MS9, MS11
and MS14 expect a save; MS10 goes. To confirm while implementing: that Python and the web save the same
loaded settings as Swift.

*Decision (owner, 2026-09-28):* "Please implement this."
- *Done (item 13):* Swift `selectedInputDevice.didSet` saves again and `chooseInputDevice` is gone (the
  Settings picker binds to `selectedInputDevice`; a plug-in assigns it); `applyInputDeviceList` selects the
  system default, else the first device, when the device in use disappears. Python's
  `selected_input_device` setter saves again and `choose_input_device` is gone; `apply_input_device_list`
  as Swift. Web: `selectInput` saves; `chooseInputDevice` and `switchToInputToUse` are gone (the picker and
  a plug-in call `setInputDevice`; an unplug takes the browser's default). A load's switch is saved in all
  three, as the other settings a load restores.
- *Tests:* MS6–MS11 now: the launch selection saved; a Settings selection saved; a plug-in saved; the device
  in use unplugged → the default, saved; unplugged → the default, not another connected USB mic (MS10,
  replacing "back to the saved device"); a load's switch saved (MS14 also checks it). Mutation — a selection
  not saved — fails MS6–MS11 and MS14 in all three. Full suites: Swift 676, Python 796, web 710; tsc and
  eslint clean.
- *Checked:* the web saves the same loaded settings as Swift (measurement type, tap threshold, Peak Min,
  annotation mode). Python saves the measurement and guitar type in the load; its tap threshold and Peak Min
  are saved by the view's slider handlers, not the model → item 14.

**14. Where a threshold is saved.** The revised rule relies on a load saving what it restores, as the user
setting it would. Swift saves the tap threshold and Peak Min in the model (`tapDetectionThreshold` /
`peakMinThreshold` `didSet` → `TapDisplaySettings`). Python's model setters did not save: the main window's
slider handlers and the Settings dialog wrote `AppSettings`, so a load's thresholds were saved only if a
handler happened to run after it. Python also kept Peak Min under two keys (`analysis/threshold`, 0–100, read
by the main window at start; `analysis/peak_threshold`, dB, read by the model). The web saves every setting
through App's settings store (`updateSettings`), fed after a load by the analyzer's `loadedSettings`.
- *Decision (owner, 2026-09-28):* "Being architecturally consistent is the bar to aim for… Fix python now
  since you are working on item 21." The web's settings store covers every setting, so moving two thresholds
  alone would split the web's mechanism; it is recorded in #1 (`RESTRUCTURE-NOTES.md`).
- *Done (Python):* the `tap_detection_threshold` setter saves, syncs the level-crossing threshold and ends
  the loaded-settings warning when the value moves off the loaded one (Swift's `didSet`); the
  `peak_min_threshold` setter saves and re-projects. `set_tap_threshold` / `set_threshold` only assign the
  property. The slider handlers and the Settings dialog no longer write `AppSettings` (the dialog assigns the
  model). Peak Min has one key: the main window reads `peak_min_threshold` at start, and
  `AppSettings.threshold` / `set_threshold` (`analysis/threshold`) are removed — both keys default to −60 dB.
- *Tests:* MS21 (a load saves the thresholds it restores — Swift, Python; the web checks the `loadedSettings`
  the load hands App) and MS22 (setting a threshold on the model saves it — Swift, Python; no web
  counterpart). Mutation — the setters not saving — fails MS21, MS22 and the existing D3 / D5 persistence
  tests. Full suites: Swift 678, Python 798, web 711; tsc and eslint clean.

## Run-review findings (2026-09-28, Python on macOS) — under decision

From the owner's run-review, with the debug log (`guitar_tap-debug.log`, session 18:42 UTC):

**15. Python reopens a device by a stale index after a hot-plug.** PortAudio numbers devices by their
position and renumbers them when the app re-initialises it after a hot-plug. With the MacBook mic selected
as index 2 (UMIK 0, BlackHole 1, MacBook 2), unplugging the UMIK made it index 1; the selection was still
present, so the refresh left it alone, and the stream was reopened on the old index 2 — "Could not open
'MacBook Pro Microphone' (Invalid number of channels)" — and the watchdog's recoveries failed in turn. A
stale index can equally land on another device (BlackHole, which is silent) — a possible cause of the first
failure seen (step 4: "No audio input", levels frozen). Swift and the web identify devices by stable ids
(CoreAudio device id, browser `deviceId`); Python only. Proposed: when a list is applied, re-point the
selection at the fresh entry for the same device.

**16. An unplug went unnoticed.** After the UMIK was plugged in (t=136.9 s) no further device change was
seen; a stream close before it had timed out (t=144.9 s, "abort/close timed out after 2 s"). At the load
(t=188.2 s) the app still listed the UMIK, switched to it, failed to open it ("Internal PortAudio error
-9986") and was left with no stream — New Tap hung, the watchdog restarting a device that was not there.
- *Found (2026-09-28): the freeze.* At t=144.9 s, switching to the MacBook mic, closing the UMIK's stream hung
  ("abort/close timed out after 2 s — proceeding without waiting"): the app went on, but PortAudio's abort on
  CoreAudio's I/O thread never finished. At t=191.2 s the watchdog scheduled recovery attempt 1/6; the restart
  runs on the main thread and starts by re-initialising PortAudio (`sd._terminate()` / `sd._initialize()`).
  Terminating waits for every stream — including the half-closed one — so the main thread blocked: no
  "stream restarted", no attempt 2, the window frozen. The file's own header records that `Pa_Terminate` can
  deadlock on macOS when the CoreAudio I/O thread is stuck (the exit handler is guarded with a timeout); the
  re-initialise used by the watchdog and the hot-plug refresh is not.
- *Likely link:* the missed unplug came after the same hung close; CoreAudio's notification may not have
  reached the app while its threads were stuck. Consistent with the log, not proven by it.
- *Next (owner, 2026-09-28: "yes"):* investigate why the stream close hangs, and stop PortAudio being
  terminated while a timed-out close is pending (or on the main thread) — the watchdog's re-initialise and the
  hot-plug refresh's. Not introduced by #21; #21's extra switching (the load switch, unplug fallbacks) makes
  the path more likely.

**17. A device that fails to open.** Python and Swift select and save the device before opening it; on failure
Python is left with no stream and Swift with the engine stopped. The web restores the previous input.
- *Decision (owner, 2026-09-28):* a device that fails to open is not selected and not saved — "It cannot be
  selected if it fails to open. And shouldn't be saved." The previous device stays selected and in use, and
  a popup tells the user the chosen microphone cannot be used and to check it. This arises while the app
  runs: choosing a device in Settings, or a load whose recorded microphone the system lists but which fails
  to open (then as for a missing microphone: the current input is kept). A device plugged in while running
  is switched to automatically and gets the same popup if it fails to open.
- The load of a measurement whose microphone is not listed is unchanged: the current input is kept and the
  "No connected microphone matches…" warning shown.

*Decision (owner, 2026-09-28):* "Go" — on the proposed fixes: (1) re-point a renumbered selection, and look the
selected device up again by fingerprint when re-initialising; (2) the Python watchdog restart reopens the
selected device and counts a failed open as a failed attempt, as Swift's does; (3) a pending recovery is dropped
if the input was switched since it was scheduled — Swift, Python and the web; (4) Python never terminates
PortAudio while a timed-out close is pending; (5) item 17.

- *Done (15, Python):* `apply_input_device_list` re-points a still-present selection at the fresh entry (same
  device, new index; not a new selection — nothing saved or reloaded); `reinitialize_portaudio` looks the
  selected device up again by fingerprint (`_listed_device`) before opening it.
- *Done (16, Python):* `terminate_and_reinitialize_portaudio` does nothing — and logs it — while a timed-out
  close (`_pending_stream_close`, recorded by `_close_stream_only`) is still alive; the hot-plug refresh and the
  watchdog both go through it. `reinitialize_portaudio` raises `InputDeviceOpenError` when the device is not
  listed or cannot be opened, and `_do_watchdog_restart` then retries through `_attempt_watchdog_recovery`
  instead of logging a restart that did not happen. For the missed unplug: the log now records every device
  change the system reports, a change dropped because no handler was connected, and a refresh dropped by the
  1-second cooldown (which dropped silently before).
- *Done (17, all three):* one message, "Could not open the microphone '…'. The previous input is still in use —
  please check the microphone." Swift: `switchInputDevice(to:open:)` (used by `setInputDevice`) selects the
  device, opens it, and on failure selects and reopens the previous one and rethrows; a switch through
  `selectedInputDevice` (Settings, a plug-in, a fallback) that fails to restart is reverted by
  `revertFailedInputSwitch(from:to:)`, which publishes `inputDeviceOpenFailure` — an alert on the main view and
  on the Settings sheet ("Microphone Unavailable"). Python: `set_device` reverts and raises
  `InputDeviceOpenError`; Settings shows the alert and returns the combo to the device in use; the refresh keeps
  the previous device (`_keep_previous_after_failed_open`) and emits `inputDeviceOpenFailed` for the alert. Web:
  `setInputDevice` already kept the previous input; a failed plug-in now keeps it too (it fell to the browser
  default) and reports through `onInputOpenFailed`; Settings and a plug-in show "Microphone Unavailable". A load
  whose recorded microphone cannot be opened keeps the input and its warning is the failed-open message, in all
  three.
- *Tests:* MS23 (a failed switch keeps the previous device, selected and saved — all three), MS24 (a failed
  switch while running is reverted and reported — all three), MS25 (a load whose switch fails — Python, web; a
  Swift test engine opens nothing), MS26 (a renumbered device), MS27 (no terminate while a close is pending),
  MS28 (a failed watchdog restart retries) — Python only. Mutations — no revert, no report, no rebinding, no
  pending-close guard, a failed restart reported as success — each fail their case. Full suites: Swift 680,
  Python 804, web 714; tsc and eslint clean.
- *Not done — fix (3), for the owner:* Swift's recovery stops the engine when it schedules the restart, and a
  device switch while the engine is stopped does not restart it (`didSet` restarts only when running) — so in
  Swift the pending recovery is what starts the engine on the newly selected device. Dropping it would leave
  Swift stopped. In Python the late recovery was destructive only because it re-initialised PortAudio under a
  fresh stream and reopened a stale index; with (1), (2) and (4) it now reopens the selected device, as Swift's
  does. Dropping pending recoveries in Python and the web alone would make them differ from Swift. Proposed:
  leave (3) undone in all three. *Decision (owner, 2026-09-28):* agreed — (3) is not done.

## 18. The load's warnings, reworded (2026-09-28)

Run-review (web, Safari): with the UMIK connected and in use, a measurement from another browser warned
"Microphone Not Connected — This measurement was recorded with a different sample rate". The web log showed
the load had matched the UMIK by name and the input already was it; the rates were 48000 Hz recorded (Chrome)
against 44100 Hz now (Safari — the browser's audio rate follows the output device, and the mic's 48 kHz is
resampled to it). And (Swift) a measurement from Python on Windows — `Microphone (Umik-1  Gain: 18dB)` — found
no microphone on the Mac, where the same UMIK is `Umik-1  Gain: 18dB`. Both behaviours are as decided (a
measurement from another platform does not find its microphone); the popups did not make that clear, and
both showed under "Microphone Not Connected".
- *Decision (owner, 2026-09-28):* reword both popups to be "more blatant, informative, and explicit"; the
  Results panel and the user documentation unchanged. The wording was agreed as drafted.
- *Done (all three):* the load's warning carries its own title (Swift `microphoneWarningTitle`, Python
  `microphone_warning_title`, web `microphoneWarningTitle`, set with the message):
  - **Microphone Not Found** — "This measurement was recorded with a microphone named '…'. No connected
    microphone has exactly that name, so the input has not been changed — you are still using '…'. / Each
    computer names microphones its own way. A measurement made on another computer — especially one running a
    different operating system — will usually not find its microphone even when the same one is connected. If
    it is, choose it in Settings. / Peak frequencies are still comparable; input levels, the tap threshold,
    and faint peaks (such as FLC) may differ."
  - **Recording Setup Differs** — "This measurement was made with a different setup from the current one: /
    • Calibration: recorded with '…'; the current microphone uses '…'. / • Sample rate: recorded at … Hz; audio
    is now captured at … Hz. / A tap captured now may not match the saved result. The sample rate is set
    outside Guitar Tap: in Audio MIDI Setup on a Mac, or Sound settings on Windows." (only the lines that
    differ; the web's last sentence: "In a browser, the sample rate follows your output device: set the output
    and input to the same rate in Audio MIDI Setup (Mac) or Sound settings (Windows).")
  - **Microphone Unavailable** — a load whose microphone cannot be opened (item 17).
- *Tests:* MS16 and MS17 check the title and the exact text (all three); the import tests check the folded
  message's opening. Full suites: Swift 680, Python 804, web 714; tsc and eslint clean.
- *Found, recorded, not changed:* the web captures at the browser's rate (the output device's), not the
  microphone's as Swift and Python do — the same microphone gives 48 kHz measurements in the natives and 44.1
  or 48 kHz on the web. Proposed for separate investigation: the web asking the browser for the microphone's
  rate (`new AudioContext({ sampleRate })`).

## 19. Windows watched the wrong notification (2026-09-28)

Step 2 failed on Windows: with the app running, plugging the UMIK-1 in did not switch the input.
Nothing in the selection logic was wrong — it was handed a device list that did not contain the
microphone.

**What the log showed.** Two notifications arrived, the refresh ran, and PortAudio still reported
one device:

```
🔌 Device change reported by the system      <- notification 1
🔌 Device change reported by the system      <- notification 2
🎤 Found 1 audio input device(s) total       <- the UMIK is not there yet
🔄 _on_devices_refreshed: suppressed (within 1 s of the last refresh)
```

So the refresh that ran was too early to see the microphone, and the one that would have seen it was
dropped as a duplicate. `newly_connected` was empty, the array stayed selected, and the stream
reopened on it.

**Why.** `CM_Register_Notification` on `KSCATEGORY_AUDIO` reports that a USB **device interface**
arrived. What the app needs is that an audio **endpoint became active**, which happens later. The
0.5 s settle sleep in `_notify_devices_changed` was compensation for that gap, and the 1 s cooldown
(Guard 2) existed because interface events cascade — `Pa_OpenStream` fires one itself. Both
constants were treating a symptom.

**Measured, with a standalone probe** registering `IMMNotificationClient` and re-enumerating
PortAudio at each event (UMIK-1 plug-in, then unplug):

```
t=9.275  OnPropertyValueChanged x7      <- 28 ms EARLY
t=9.303  OnDeviceStateChanged ACTIVE    <- the real event
t=9.336  OnDefaultDeviceChanged x3 (capture: console/multimedia/communications)
         PortAudio enumerates the device from here on
t=18.067 OnDeviceStateChanged NOTPRESENT  (unplug; PortAudio agrees 85 ms later)
```

Three things that shaped the fix:

* **The endpoint event and PortAudio agree.** PortAudio's WASAPI host API enumerates the MMDevice
  enumerator's active endpoints — the very list that just changed — so a refresh triggered by
  `ACTIVE` finds the device. **No settle constant is needed, and none was added.**
* **`OnDeviceAdded` never fired.** The UMIK was already known to Windows, sitting at `NOTPRESENT`, so
  its arrival is a *state change*. A monitor watching only `OnDeviceAdded` would miss every re-plug.
* **`OnPropertyValueChanged` is the trap** — 21 of the 25 events, and the first burst precedes
  `ACTIVE` by 28 ms. Acting on it reproduces the original race exactly.

**The change (Windows only).** `_start_windows_monitor` registers an `IMMNotificationClient`, with
the cfgmgr32 monitor kept as the fallback when comtypes is absent — the same optional-import shape as
`pyudev` on Linux. `comtypes` is declared in `requirements.txt` and `pyproject.toml` under a
`sys_platform == "win32"` marker. Registration happens on a dedicated thread that joins the **MTA**:
comtypes CoInitializes the importing thread as an STA, and an STA callback object only receives calls
while a message pump runs.

Actionable events are exactly those that change the device list — added, removed, state-changed.
Property changes and **default-device changes** are ignored. The latter cost a second round: acting
on them ran four full refreshes per plug-in (one `ACTIVE` + three default-role changes), each a
PortAudio re-init, stream reopen and detection reset. They report which device Windows now *prefers*,
never a change to the list; the fallback that cares about the system default reads it at enumeration
time.

The Windows hand-off skips the 0.5 s sleep (`_notify_devices_changed_now`, separate so the shared
`_notify_devices_changed` keeps the behaviour validated on macOS and Linux), and Guard 2 is skipped
only while the MMDevice monitor is active, since opening a shared-mode stream neither adds, removes
nor activates an endpoint. Guard 1 still prevents overlap, without a clock. `_start_coreaudio_monitor`,
`_start_linux_monitor` and every shared selection path are untouched.

**Result** — one event, one refresh, one restart, and audio flowing on the new device:

```
🔌 Audio endpoint change (state=1)
🎤 Found 2 audio input device(s) total
📊 Auto-loaded calibration for device 'Microphone (Umik-1  Gain: 18dB)'
🎤 New device connected, selected: Microphone (Umik-1  Gain: 18dB)
🔄 Detection re-enabled after route change (current level: -84.16 dB)
```

**Two incidental findings.**

* `gt_log` printed its emoji markers straight to stdout, so with logging enabled on a cp1252 console
  the app died at its first log line. Guarded with an ASCII fallback; the file log was always UTF-8.
  Worth knowing because the log is the field diagnostic, and it is disabled by default — the failure
  only appears when someone turns it on to investigate something else.
* On the test machine the built-in **Intel Smart Sound array delivers digital silence through WASAPI**
  (bit-exact zeros at 1 and 2 channels) while the same hardware returns signal through MME. The app's
  filter prefers WASAPI, so the built-in mic is unusable there — the same pathology the filter already
  documents for WDM-KS. Not part of #21, and not investigated further; noted because any run-review
  step that lands on that machine's built-in mic will look like a failure.

**Still open:** one case can produce two refreshes — a microphone Windows has never seen before, where
`OnDeviceAdded` and `OnDeviceStateChanged(ACTIVE)` may both fire. Harmless, and left alone rather than
suppressed with a timer.

## 20. Linux: hot-plug disabled, deliberately (2026-09-28)

**Decision (owner): disable microphone hot-plug on Linux and document it. Closed, not deferred —
there is no follow-up issue and this is not to be revisited.** macOS and Windows both work; the
Linux user base may well be empty, and the effort to make this correct is out of proportion to it.

`_start_linux_monitor` is now an explicit no-op carrying the reasoning, rather than the silent
`except ImportError: return` that hid the situation for six months.

**It had never worked.** A udev monitor was written on 2026-03-22 behind `try: import pyudev`, and
`pyudev` was never declared in `requirements.txt`, `pyproject.toml` or the PyInstaller spec. Every
install — source or AppImage — took the early return, so no user has ever had Linux hot-plug, and
the release notes only ever claimed it for Windows and macOS. Disabling it removes nothing anybody had.

**The events were solved; that was the easy half.** Measured over six plug cycles with a standalone
probe (the same approach item 19 used on Windows):

- udev emits its `sound` events **3–20 ms after** the `/dev/snd` nodes already exist — the opposite
  of Windows, where the notification preceded readiness by 28 ms.
- `card1`, `pcmC1D0c` and `controlC1` arrive within ~11 ms of each other, so **no choice among them
  marks readiness** — there is no Linux equivalent of `OnDeviceStateChanged(ACTIVE)`.
- What actually gates PortAudio is the **uaccess ACL** making those nodes readable, landing 6–10 ms
  after the event. In all three measured cycles the first enumeration begun after the ACL succeeded.
- The node→ACL interval measured **20 ms, 42 ms and 214 ms** on consecutive cycles of one idle
  machine — a 10× spread, which is what a fixed settle sleep has to cover blind.

A Linux-only notify path waiting on that condition rather than a clock was written and worked. It
was removed with the rest: correct code for a feature that is not shipping is a trap for the next
reader.

**The device list is why it cannot work as designed.**

- PortAudio's Linux enumeration lists raw ALSA `hw:` devices *alongside* PipeWire's `default`,
  `pipewire` and `sysdefault` aliases. `filter_input_devices` keeps everything with
  `max_input_channels > 0` on non-Windows — the careful Windows pruning has no Linux counterpart.
- Whenever PipeWire holds a card, that card reports 0 input channels and **drops out of the list**.
  Confirmed directly: `fuser /dev/snd/pcmC0D0c` showed `pipewire` holding it while
  `arecord -D hw:0,0` answered *"Device or resource busy"*.
- PipeWire moves its active source on its own — auto-switching to a newly plugged microphone,
  suspending idle ones — so devices enter and leave the list **with no hardware change at all**.
  One session went 5 → 4 → 3 → 2 devices.
- A device that reappears because PipeWire released it is indistinguishable from one just plugged
  in, so `apply_input_device_list`'s `newly_connected` branch selects it — and every selection is
  saved. Observed in the log: `🎤 New device connected, selected: Ensoniq AudioPCI…` with nothing
  plugged in. **That is #21's own defect, reintroduced on a third platform**, which is why
  half-working hot-plug is worse than none.

Fixing it means deciding what Linux should enumerate at all — PipeWire's sources rather than raw
`hw:` devices — a design change affecting what users can pick, needing verification on real
hardware. Not done.

**What Linux gets instead** is the contract Windows shipped with for a time: the list is built at
startup, and a microphone connected later is chosen in Settings. Documented in the Python
`docs/ReleaseNotes.md` (Known Limitations) and the user manual (§2.3 and the §10 troubleshooting
table).

**Incidental, and not chased:** measuring this was done in a VMware guest, which contributed its own
noise — USB detach reached the audio layer ~6.7 s before the guest's udev, `_close_stream_only`
timed out at 2 s on the emulated ES1371, and the buffer watchdog consequently raced the hot-plug
refresh and left PortAudio un-reinitialised. That watchdog/refresh race is **not** Linux-specific and
is the one thing here worth remembering for the other platforms.

## Run-review steps

Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web `npm run build && npm run preview`
(Safari and Chrome; the browser console shows the web's device log). Use a USB mic
(e.g. the UMIK-1); BlackHole installed reproduces the report. Same list per edition, canonical first. The rule
being checked: **what Settings shows is what the next launch uses.**

1. Open Settings. → The device list shows the connected inputs with the current one selected; opening it
   changes nothing. Choose the built-in microphone. Quit and relaunch. → The built-in microphone (not
   BlackHole, not the USB mic).
2. With the app running, plug in the USB mic. → The input switches to it; Settings shows it. Quit and
   relaunch. → The USB mic.
3. Settings → choose the built-in microphone. Quit. Plug in the USB mic. Launch. → The built-in microphone.
4. Settings → choose the USB mic. Unplug it while the app runs. → The input switches to the system default;
   Settings shows it. Plug it back in. → The input switches back to the USB mic. Unplug it again; quit; plug it
   in; launch. → The system default — what Settings showed when you quit.
5. Settings → choose the USB mic. Quit. Launch with it unplugged. → The system default; Settings shows it.
6. With the built-in mic in use and the USB mic connected, unplug the USB mic. → The input stays on the
   built-in mic and keeps working (no "Could not open", no watchdog restarts).
7. With the built-in mic chosen (with a calibration on it) and the USB mic connected, load a measurement
   recorded with the USB mic. → The input switches to the USB mic; its calibration (or none) is shown; no
   "different calibration" warning for the built-in mic's calibration. Quit and relaunch. → The USB mic.
8. Load a measurement recorded with a microphone that is not connected. → "Recorded with '…'. No connected
   microphone matches that name…". The Results panel shows the measurement's recorded (missing) microphone;
   the input in use, the microphone shown in Settings and the saved setting are all unchanged — a relaunch
   comes back on the same microphone.
9. In Settings, choose a device that cannot be opened (e.g. one another app holds exclusively, if one is
   available). → "Microphone Unavailable — Could not open the microphone '…'. The previous input is still in
   use…"; Settings still shows the previous device. Quit and relaunch. → The previous device.
10. With the USB mic in use, choose a calibration in Settings. Switch to the built-in mic. → Its own
    calibration, or none. Switch back to the USB mic. → The calibration chosen.
11. Move the Tap Threshold and Peak Min sliders; set a Peak Min value in Settings and Apply. Then load a
    measurement whose tap threshold and Peak Min differ from those. Quit and relaunch. → The loaded values are
    the current settings (as for the measurement type).
12. Windows (Python): steps 2 and 4. Then, with the saved mic unplugged, launch. → Windows' default
    recording device (not simply the first in the list).

**Run-review progress.** macOS complete (owner, 2026-09-28): Swift, Python and the web (Safari) passed
steps 1–11, including item 18's reworded messages. **Windows (Python) complete** (owner, 2026-09-28):
step 12 — steps 2 and 4, and the launch with the saved mic unplugged — passed after the monitor was
moved onto audio-endpoint events (item 19). **Linux (Python):** steps 2, 4, 6 and 7 are **not
applicable** — they test hot-plug, which is disabled on Linux by decision (item 20). The remaining
steps — 1, 3, 5, 8, 9, 10, 11 — still apply and are what a Linux run covers.

Note for a Windows or Linux run: `tests/test_self_regression.py` fails on those machines with a stale
baseline, which is #16's work and unrelated to microphone selection — it waits on #17 finishing, since
re-minting costs a pass on every configuration and is not worth doing twice.

