# Zoom and pan slow with many peaks — the results list rebuilt on every range change

**Issue:** [#35](https://github.com/dwsdolce/guitar-tap-project/issues/35)

Status: **OPEN — items 1–3 done (Python `7e2a718`): the shared layer, the results list and the chart's labels on it; a pan step 373 → 30 ms, the main thread's work per live frame about 130 → 10 ms. Item 4 done (Python `ec604b3`): a guitar tap's completion 167 → 35 ms. Item 5 done (the web needs no change). Items 6 and 7 done (Python `ec604b3`, Swift `4d6184e`, web `e1a7afb`): every source file in the parity map; the crosshair read as Swift's. Full suites passed in all three; on-screen check on the Mac passed (owner). Left: the live review of Python on Windows and Linux.**

With a low Peak Min, so that many peaks are listed, zooming and panning the chart is unusable in Python and slow on
the web. Swift stays smooth (owner, 2026-10-20).

## Python — measured

A guitar measurement (`dws-2024-umik-1-3-tap-swift-mac-1785359425.guitartap`) open in the real window, the chart's
frequency range moved 20–30 times, each step repainted (Python `26d0939`, macOS):

| What was switched off | Time per pan step |
|---|---|
| nothing | 146–168 ms |
| the mode lines and their chips | no better |
| the spectrum curve | no better |
| the results panel's refresh | 34 ms |

| Peak Min | Peaks above Peak Min | Time per pan step |
|---|---|---|
| −60 dB | 8 | 47 ms |
| −80 dB | 46 | 146 ms |
| −100 dB | 46 | 181 ms |

**Cause.** Each change of the chart's range (`_on_canvas_freq_range_changed` → `_refresh_results_peaks` →
`peak_card_widget.update_data_with_modes`) discards and rebuilds every peak card in the list (`_rebuild_cards`), with
about 20 `setStyleSheet` calls per card — and it runs twice per change (38 rebuilds for 19 steps). The cost grows with
the number of peaks listed. The same holds at every commit back to 2026-10-08; a low Peak Min is what makes it
unusable. Swift lists the same peaks on every range change but redraws only what changed.

## Python — the same rebuild on every live frame (2026-10-21)

Found measuring #38's slack: while listening, every FFT frame (about one per 1.37 s) rebuilds the list too, and
recreates the chart's peak labels. Profiled in the running app, idle listening, 15 frames: about 115 ms of main-thread
work per frame — the peak cards rebuilt (about 22 new cards a frame, ~60 ms), the chart's labels created again
(about 22 a frame, ~35 ms), ~285 `setStyleSheet` calls a frame (~30 ms) — against about 15 ms for the analysis itself
(peak finding and classification). It holds Python's main thread about 130 ms a frame, so chunks wait that long.

## Web — to measure

Slower with many peaks, less than Python (owner). Not yet measured.

## Why Python, and not Swift or the web

The three editions run the same logic and key their rows the same way — Swift `ForEach(…, id: \.peak.id)`, the web
`key={p.id}`, Python by the peak's id — and a live frame's peaks get new ids in all three, so Swift and the web also
recreate every row on every frame. It costs them almost nothing; it costs Python about 100 ms. The difference is the
UI toolkit, on four counts:

| | SwiftUI (Swift), React (web) | Qt Widgets + pyqtgraph (Python) |
|---|---|---|
| Collecting changes | the changes of one moment produce one screen update (`@Published`, React state) | every Qt signal runs its slots at once, each refresh its own — the list refreshes twice per range change |
| Working out what changed | the framework compares the new view with the last and changes only the difference | the app's own code must, and Python's deletes and rebuilds |
| A view element | a light description, drawn by the system (GPU layers, the browser's compositor) | real widgets — about 15 per card — and scene items, with per-widget style-sheet text Qt re-parses on every set |
| Per-element computation | compiled (Swift, vDSP) or JIT-compiled JS | interpreted loops, the GIL shared with the audio thread |

Python's views were ported from Swift's logic, but SwiftUI's "describe the view; the framework updates it" became
"rebuild the widgets" in Qt — cheap in SwiftUI, costly in Qt, and nothing gathers the updates together.

## The fix — Swift's contract, with the framework's part done once

Swift's architecture is the view as a function of the model's state: a change marks the view out of date, `body` runs
at most once per screen update and derives the whole view, and the framework applies the difference. Python gets the
same contract, with a small shared layer doing what SwiftUI does underneath — so it is both aligned and fast, and
lasts beyond this issue:

| Swift | Python |
|---|---|
| a `@Published` change marks the view out of date | the model's signals only **invalidate** the view |
| `body` runs once per screen update, derived from the model's state | the view's **one `refresh()`** derives all it shows from the model's state, run **once per event-loop turn** however many signals came |
| `ForEach(items, id:)` adds, removes and updates rows by id | **one shared keyed-update helper** for every list and set of chart labels: the child whose key matches is kept and updated, the rest added or removed, and only what differs touched. Qt cannot afford SwiftUI's recreating rows whose ids changed (a live frame), so the helper reuses leftover children in order — inside the helper, as SwiftUI's own recycling is inside SwiftUI; the view code stays Swift's |
| modifiers (`.foregroundStyle(role)`) | roles through the shared stylesheet (`palette.tag`), applied only when they change; no per-widget style-sheet text |

Per-element computation is left alone unless the measurements still point at it after this: the analysis's ~15 ms per
frame is within budget.

## Items

| # | Item | Status |
|---|---|---|
| 1 | The shared layer: invalidate and one refresh per event-loop turn; the keyed-update helper; role styling applied only on change. Each with its own tests | done — Python `7e2a718` |
| 2 | The results panel's peak list on it: one `refresh()` from the analyzer's state, cards through the keyed-update helper, the cards' styling through roles. Target: a pan step near the chart's own cost (≈ 35 ms) at −100 dB, measured as above; a test that a range change and a live frame construct no new cards when the peaks' count is unchanged | done — Python `7e2a718` |
| 3 | The chart's peak labels on it the same way. Target, with item 2: the main thread's work per live frame near the analysis's (≈ 10–15 ms) while listening, measured with #38's slack probe; a test that a live frame constructs no new labels | done — Python `7e2a718` |
| 4 | Python's other often-updated views, found by measurement (the probe and a profile while listening, tapping and zooming), moved onto the layer one at a time | done — Python `ec604b3` |
| 5 | The web: measured the same way — a pan step, and the slack probe while listening; the same treatment only if it shows the cost | done — no change needed |
| 6 | Every source file in the parity map: the check covers each edition's whole source tree, not only its model folders; each untagged file read against its counterparts and put in a group, or `@parity none` with its platform reason; tests linked with `tests=` | done — Python `ec604b3`, Swift `4d6184e`, web `e1a7afb` |
| 7 | The crosshair on a held spectrum, plate / brace phases or a comparison read as Swift's: the curve interpolated between the bins either side of the pointer, and the curve followed kept until another is 12 pt nearer | done — Python `ec604b3`, Swift `4d6184e`, web `e1a7afb` |

### 1 — the shared layer

**Done** (Python `7e2a718`). `views/utilities/view_update.py`: `Invalidator` (invalidate as often as signals come; one
refresh at the end of the event-loop turn; `flush()` for a caller that needs the view current now), `sync_children`
(children kept by key and updated; the leftovers reused for the remaining items — nearest first when given a
distance, so a reused child changes little; the rest made or removed), `set_style_sheet` and `tag` (applied only
when the style or role differs). Tests: `tests/test_view_update.py` (11).

### 2 — the results list

**Done** (Python `7e2a718`). The results panel refreshes through one `Invalidator` (the peaks' change, the chart's
range change and the comparison's change all invalidate it); the cards sync by peak id, reusing the nearest in
frequency, and each card's `apply(...)` changes only what differs, its icons cached. Measured as above, Peak Min
−100 dB: a pan step **373 → 30 ms** (target ≈ 35 ms). Tests: `tests/test_results_update_in_place.py` — a live frame
and a range change construct no new cards.

### 3 — the chart's labels, and the live frame

**Done** (Python `7e2a718`). A refresh's labels reuse the last refresh's (their own peak's, else the nearest in
frequency), changing only text, style and position that differ; those left over are removed when the refresh ends.
Two more costs on each live frame, found by profiling it:

- **The curve drew every bin**, also those outside the chart's range: now only the visible range
  (`display_range.drawn_indices`, test `test_drawn_indices`).
- **The antialiased curve** took the most of the chart's paint in Qt's software renderer: 42 ms a frame
  antialiased, 9 ms without; the spectrum is straight segments and looks the same either way (owner, on screen,
  2026-10-21), so it is drawn without. OpenGL brought the paint to about 3 ms but is not used — it is unreliable on
  Linux and Windows; `GT_OPENGL=1` switches it on for trying (off by default).

Measured with #38's slack probe (Mac, live microphone, 2026-10-21; before: the main thread's work on each frame
128–145 ms, lag max 230 ms, latency p95 120–130 ms):

| Python, `7e2a718` | Lag p99 | Lag max | Latency p95 | Main busy |
|---|---|---|---|---|
| idle listening | 8–9 ms | 29–65 ms | 0.3–0.6 ms | 1.6 % |
| idle, FFT's cost on main | 7–11 ms | 28–34 ms | 0.3 ms | 0.5–0.9 % |
| tapping, FFT's cost on main | 13–28 ms | 65–408 ms | 2–142 ms | 1–8 % |

The main thread's work per live frame idle is about 10 ms (target ≈ 15 ms). The large holds while tapping are one
chunk's (main/chunk max 228–262 ms) — the chunk on which a tap's capture finishes and its results are shown: item 4.
Tests: `tests/test_results_update_in_place.py` — a live frame constructs no new labels; fewer peaks remove the labels
left over.

### 4 — Python's other views

Found from the measurements under item 3: a tap's results arriving held the main thread 228–262 ms in one chunk.
Reproduced offscreen (Mac, the real window, `5 tap test.wav` played as Play File plays it, the measurement type set
in the process only), profiled per main-thread call:

| Measurement type | The completing chunk, before | After 4a and 4b |
|---|---|---|
| Acoustic guitar | 167–170 ms | 30–35 ms |
| Plate | 6 ms | 3 ms |
| Brace | — | 3 ms |

**4a — the plate / brace peak list rebuilt while measuring a guitar.** Done (Python `ec604b3`). The list was fed every
`peaksChanged` while hidden and rebuilt every row, twice per completion (102 rows for 51 peaks, ~120 ms); Swift
builds it only for a plate or brace. Now: one refresh per event-loop turn, run only while the list is shown (a list
hidden when it changed catches up when shown); each row a `_MaterialPeakRow` updated in place by key (a peak's
frequency when complete, its phase while live), rebuilt only when the badges change; a badge switched by
`set_phase_badge_active`. Thirteen states of the list rendered before and after are pixel-identical. Test:
`tests/test_material_peak_list.py` (5).

**4b — `set_measurement_complete`: the cards' colours through roles.** Done (Python `ec604b3`). At completion the peaks'
modes change (context-aware classification) and every changed colour was a per-widget `setStyleSheet` (~0.8 ms
each, re-styling the widget's children). The cards' text colours — star, mode name, in-range mark, pitch, Q/BW,
magnitude, frequency — are now roles (`view_update.tag`, a re-polish of ~0.05 ms); each button's fixed style is set
once; a manual override's italic is the font's. Sixty-four card states, light and dark, built fresh and updated in
place, are pixel-identical before and after, and a card switched between schemes matches one built in the new one.
What is left in the completing chunk: the card backgrounds that really change (six, ~8 ms — a mode's tint at an
opacity with the highlight under it, not a single role), peak finding (~6 ms), small costs.

**4c — accepted (owner, 2026-10-22): a sequence's first live frame builds its cards and labels from nothing.** Starting a sequence empties
the list, as Swift's does, so the first live frame with peaks builds every card and label: 64–77 ms for 11 peaks
(each label ~5 ms — adding it to the chart — each card ~2 ms), once per sequence. Later frames reuse them (22 peaks a
frame: about 11 ms for the list and the labels together). Not changed: once per sequence, before its first
tap, with the chunks behind it taken in order; Swift recreates its rows there too; keeping hidden cards and labels
across a sequence's start would be a new mechanism, with their state to reset on every start.

**4d — the chart's labels refreshed once at completion.** Done (Python `ec604b3`). Holding the measurement refreshed the
labels at once, against the live peaks still listed and the held selection — matching none of them — and the results'
refresh then made them again. Now the window leaves the labels to its one results refresh, which it invalidates
(`data_held(…, refresh_labels=False)`); the chart ends with the same labels. Tests:
`tests/test_results_update_in_place.py`, `TestHeld` (3).

### 5 — the web

**Done — no change needed.** #38's probe runs show the web's main thread free while listening and through zoom and
pan (lag p99 about 4 ms, main busy 0.3 %). The pan step, measured as Python's (the same measurement imported and
loaded, Chromium headless, 1800 × 1000, 30 drag steps, each timed from the pointer event to the frame after it):

| Peak Min | Cards listed (view 75–350 Hz) | Pan step, median / max |
|---|---|---|
| −60 dB | 5 | 16.6 / 18.1 ms |
| −80 dB | 14 | 16.6 / 19.1 ms |
| −100 dB | 14 | 16.7 / 18.6 ms |

Each step takes one display frame (60 Hz). Python lists the same cards in the same view (5 / 14 / 14); the peaks
above Peak Min over the whole spectrum are 8 / 46 / 46.

### 6 — every source file in the parity map

Found while tagging item 4's files: the check required tags only in the model folders (Swift `GuitarTap/Models`,
Python `src/guitar_tap/models`, the web's `src/state`, `src/audio`, `src/measurement`, `src/dsp`) and the test
folders, by the rule "`view/*` is UI, review-only" — so views, utilities and app entry points could go untagged, and
a divergence in them did not show in the map. Review-only is about how equivalence is proven, not whether a file is
in the map (owner, 2026-10-22). Untagged across the whole source trees:

| Edition | Untagged | Where |
|---|---|---|
| Swift | 22 | `Views` 9, `Views/Shared` 2, `Views/Utilities` 6, `Utilities` 4, the app 1 |
| Python | 28 | `views` 8, `views/shared` 3, `views/utilities` 8, `utilities` 4, the package's top level 5 |
| Web | 20 | `components` 10, `hooks` 3, `presentation` 2, `diagnostics` 1, `format` 1, `src` 3 |

Among them the slack probe (#38), in all three, untagged when committed.

**Done** (Python `ec604b3`, Swift `4d6184e`, web `e1a7afb`; the tooling and the map in the hub). `platforms.py`'s `code_dirs` is each edition's whole source tree (`GuitarTap`,
`src/guitar_tap`, `src`); all 70 files read against their counterparts and tagged; the map regenerated (171 groups),
`--check` clean but for a temporary Swift UI test that is not committed. New groups: `app/entry`,
`diagnostics/slack-probe`, `util/date-display`, `util/logging`, `view/empty-state`, `view/icons` (its generated files written with their tag by `gen_web_icons.py`), `view/menu-picker`,
`view/peak-annotations`, `view/platform-adapters`, `view/play-file-sheet`. Joined existing groups: the parts of
Swift's main view, Settings and spectrum chart (`view/main`, `view/settings`, `view/spectrum-chart`,
`view/spectrum-gestures`, `view/material-instructions`) with Python's matching files, and web files into
`view/main`, `view/spectrum-chart`, `view/peak-card`, `view/material-peak-role`, `view/file-exporter`,
`view/measurements-list`; Python's `json_float.py` into `model/measurement-codable` (the web's `floatJson.ts` is
there); Python's `views/utilities/tap_settings_view.py` — the settings store, not a view — into
`state/settings-store` (owner, 2026-10-22). `@parity none`, each with its platform reason: Swift's
`ResultsWindowPresenter.swift` and `SheetTitle.swift`; Python's `_colour_guard.py`, `_release_guard.py` (Swift and the
web run those rules as tooling scripts outside their source), `_version.py`, `named_mutex.py`, `peaks_model.py`,
`value_stepper.py`; the web's `AlertModal.tsx`. No new group has tests to link.

Found in the reading:

- **Nine Python files hold no code yet** — `spectrum_view.py`, `spectrum_view_snap_interpolation.py`, the five
  `tap_tone_analysis_view_*.py` and the three `tap_settings_view_*.py`: each mirrors a Swift extension file and
  names the code still in `tap_tone_analysis_view.py` and `fft_canvas.py`. Kept, and tagged with the Swift file's
  group, as the place that code goes in #1 (owner, 2026-10-22).
- **The crosshair's reading on a held spectrum differs** — item 7.

### 7 — the crosshair read as Swift's

Found in item 6's reading; aligned with Swift (owner, 2026-10-22). Swift reads a curve at the pointer's frequency,
interpolated linearly between the bins either side (`snapToWaveform`), and with several curves — a plate's or
brace's phase spectra, a comparison — follows the nearest, kept until another is at least 12 pt nearer
(`nearestSeriesIndex`), dropped when the pointer leaves the plot. Python and the web read the nearest bin; Python
switched curves whenever the nearest was within 12 px, the web always took the nearest.

**Done** (Python `ec604b3`, Swift `4d6184e`, web `e1a7afb`; the cases in the hub). On-screen check on the Mac passed (owner, 2026-10-22). Swift's rule for which curve to follow is its own function now, `lockedSeries`, unchanged, so
it can be tested. Python's `views/spectrum_view_snap_interpolation.py` and the web's
`src/presentation/snapInterpolation.ts` hold the same `snap_to_waveform` / `snapToWaveform`, `locked_series` /
`lockedSeries` and `nearest_series_index` / `nearestSeriesIndex`; Python's `fft_canvas.py` and the web's
`spectrumRender.ts` read through them, the followed curve kept between moves (Python `_locked_series_index`, the web
`crosshairLock`) and dropped off the plot. Shared cases `tooling/parity/cases/snap-interpolation.json`
(`test/snap-interpolation`, 18 cases — interpolation, the ends, one bin, equal frequencies, empty and mismatched
arrays; the gravity rule at and around 12, ties, no candidates), Swift's values: Swift `SnapInterpolationTests`,
Python `tests/test_snap_interpolation.py`, the web `test/snap-interpolation.test.ts`, all passing. In Python's window
(offscreen): a held guitar measurement, the pointer between bins at 185.815 Hz, reads 185.8 Hz −49.5 dB (the nearest
bin read 186.04 Hz); a plate's three phase spectra, the readout on the nearest.

## Rules

Rules, as #38's: no commit until fully verified against the existing tests, which are not changed except where one
cannot run otherwise (each listed here with its reason).

**Test changes:** `tests/test_display_range_expansion.py` gained `test_drawn_indices` (the new
`display_range.drawn_indices`), its docstring updated to name it; no existing test was changed. New:
`tests/test_view_update.py`, `tests/test_results_update_in_place.py`. The full Python suite passed at `7e2a718`
(1535 passed, 1 skipped — the capture probe, off).

Items 4, 6 and 7: new `tests/test_snap_interpolation.py`, Swift `SnapInterpolationTests`, the web `test/snap-interpolation.test.ts`; new `tests/test_material_peak_list.py`; `TestHeld` added to `tests/test_results_update_in_place.py`; `tests/test_view_update.py` and
`tests/test_results_update_in_place.py` gained their `@parity none` line (a comment, which the parity check
requires), as did Swift's `GuitarTapTests/ViewTypeDepthTests.swift` (#32's). No test's code changed. Full suites at
those commits: Python 1561 passed, 1 skipped; the web 1420 passed, 1 skipped, lint clean, 11 end-to-end passed; Swift
(macOS) 295 tests in 90 suites and 1 XCTest passed — the skips are the capture probe, off.
