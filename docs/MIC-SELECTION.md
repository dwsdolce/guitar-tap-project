# Microphone selection — which input the app uses, and what it remembers

**Issue:** [#21](https://github.com/dwsdolce/guitar-tap-project/issues/21)

Status: **IMPLEMENTED 2026-09-27 (items 1–12) — awaiting run-review.** Commits: Swift `fb1b27f`, Python
`aecefc3`, web `6dc6f5c`. All three editions (Swift, Python, web).

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
| 2 | Saved only on a user choice or a plug-in; never a fallback | ✅ | ✅ | ✅ |
| 3 | Plug-in: switch to the new device (and save it) | ✅ | ✅ | ✅ |
| 4 | Unplug: the startup rule again, not saved | ✅ | ✅ | ✅ |
| 5 | No built-in / external / virtual ranking | ✅ | ✅ | ✅ |
| 6 | One owner: the engine chooses and saves | ✅ | ✅ | ✅ |
| 7 | A measurement load's microphone switch is not saved | ✅ | ✅ | ✅ |
| 8 | Web: a measurement load switches to its recorded microphone | — | — | ✅ |
| 9 | Settings lists the engine's devices; opening it re-enumerates nothing | — | ✅ | ✅ |
| 10 | Python: the system default is the listed host API's default | — | ✅ | — |
| 11 | The load switch is in place before the load's calibration check | ✅ | ✅ | ✅ |
| 12 | Choosing a calibration is saved by the model, not the view | ✅ | ✅ | ✅ |

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

## Run-review steps

Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web `npm run build && npm run preview`
(Chrome — Safari rotates device ids between sessions, so a saved device is not found there). Use a USB mic
(e.g. the UMIK-1); BlackHole installed reproduces the report. Same list per edition, canonical first.

1. Settings → choose the built-in microphone. Quit and relaunch. → The built-in microphone is selected (not
   BlackHole, not the USB mic).
2. With the app running, plug in the USB mic. → The input switches to it. Quit and relaunch. → The USB mic.
3. Settings → choose the built-in microphone. Quit. Plug in the USB mic. Launch. → The built-in microphone.
4. Settings → choose the USB mic. Unplug it while the app runs. → The input switches to the system default.
   Plug it back in. → The input switches back to the USB mic.
5. Settings → choose the USB mic. Unplug it; quit. Plug it back in; launch. → The USB mic.
6. Settings → choose the USB mic. Quit. Launch with it unplugged. → The system default input. Quit; plug it
   in; launch. → The USB mic.
7. With the built-in mic chosen and the USB mic connected, load a measurement recorded with
   the USB mic. → The input switches to the USB mic. Quit and relaunch. → The built-in microphone.
8. Open Settings. → The device list shows the connected inputs and the current one selected; opening
   Settings does not change the input.
9. With the built-in mic chosen (and a calibration on it) and the USB mic connected, load a measurement
   recorded with the USB mic (web too). → The input switches to the USB mic, its calibration (or none) is
   shown, and no "different calibration" warning appears for the built-in mic's calibration.
10. Load a measurement recorded with a microphone that is not connected. → "Recorded with '…'. No connected
    microphone matches that name…"; the input is unchanged.
11. (Python, Windows) With the app running, plug in a USB mic. → The input switches to it and Settings lists
    it. Quit and relaunch. → The USB mic. With nothing saved and the USB mic unplugged, launch. → Windows'
    default recording device (not simply the first in the list).
