# Saved Measurements — sort, filter and delete

**Issue:** [#9](https://github.com/dwsdolce/guitar-tap-project/issues/9)

Status: **✅ COMPLETE (2026-10-24).** Decided by the owner; run-review complete. Swift `8b7ef17` (notes `b593370`),
Python `088f14b` (notes `473941c`), web `0426a39` (notes `e49b478`). Finding 1 continues as #41.

## What it does

Saved Measurements gains a **Sort & Filter** menu, and its Delete All becomes a **Delete** menu — the same menus in
every edition and on every device, the iPhone's narrow toolbar included (the pattern of the iPhone's own Files, Mail
and Photos).

```
Sort & Filter                    Delete
  Sort by                          All…
    ✓ As Added   ↑                 Duplicates…   (disabled when there are none)
      Date                         Selected…
      Name
      Type
  Show
    ✓ All
      Generic … Brace
      Comparison
```

**Sort & Filter**
- **Sort** as added, by date, name or type. Choosing a key ticks it; choosing the ticked key again reverses it; an
  arrow beside the ticked key shows which way. Sorting by type groups the list by type.
- **Show** one type, or all — one choice at a time, a single tap on a phone. A comparison is a measurement whose type
  is Comparison, so "only comparisons" is one of the choices.
- **While a filter is on**, the line above the list reads "Showing 12 of 48 · Plate", with an ⓧ that shows all
  again; otherwise it reads "Total: 48 measurements".
- **Remembered** between openings and launches, as settings.

**Delete**
- **All…** — every measurement, after a confirmation (as Delete All was).
- **Duplicates…** — every later copy of a measurement already in the library, the first copy of each kept, after a
  confirmation giving the count.
- **Selected…** — the list goes into tick mode, as Compare does, but any row can be ticked, comparisons included;
  Compare's place reads **Delete (n)** and Done reads **Cancel**; a confirmation gives the count.

Where: on the Mac (Swift), Python and the web, Sort & Filter is a button beside Compare and Delete replaces the Delete
All button; on iPad and iPhone, Sort & Filter is in the navigation bar and Delete is a submenu of More (⋯).

Not part of it, by decision: a search by name or notes; manual drag-to-reorder.

## The rules (shared by the three editions)

- **As Added** — the order the measurements were added to the library. The library keeps it (Swift and Python store
  the list in that order; the web reads its records back by their `savedAt` stamp), and sorting never changes it, so
  it is always there to return to. The default, oldest first.
- **Date** — the date the measurement was made (`timestamp`), not the date it was added.
- **Name** — case-insensitive; ties by date.
- **Type** — in the order of the measurement-type menu (Generic, Acoustic, Classical, Flamenco, Plate, Brace), then
  Comparison, then a file with no type (—); ties by date.
- **Direction** applies to the key; the tie-break by date always runs oldest first, then by position.
- **Imports** are appended to the library, as before; the list shows them where the chosen sort puts them.
- **A duplicate** is an entry whose measurement id an earlier entry already has (ids compare case-insensitively). Same
  id means same content: editing a name or notes gives a measurement a new id, so an edited copy is never a duplicate.

These are pure functions in each edition's model — the order to show (`SavedMeasurementsOrder.shown` /
`saved_measurements_order.shown` / `shownOrder`) and the duplicates (`duplicates`) — with one shared case file,
`saved-measurements-order.json`: 12 order cases (SO1–SO12) and 6 duplicates cases (SD1–SD6), run by all three.

## How it is built

- **The library does not change order.** Sorting and filtering produce the order to *show*.
- **Actions act on the library's entries.** Swift's and Python's rows carry their position in the library, the web's
  their record key, so delete, edit, details, compare and delete-selected reach the right measurement whatever the
  sort or filter. Measurement ids are not used for this, since duplicates share an id.
- **Deleting several** goes through the model in one step (`deleteMeasurements(at:)` / `delete_measurements` /
  `deleteMeasurements`), with `duplicateMeasurementIndices` and `deleteDuplicateMeasurements()` beside it.
- **The choices are settings** — Swift `TapDisplaySettings.savedMeasurementsSort` / `…Ascending` / `…Filter`, the same
  in Python's settings store and the web's `settingsStore`.
- **Compare and delete ticks follow the filter:** a measurement the filter hides cannot stay ticked.

| | files |
|---|---|
| Swift | `Models/SavedMeasurementsOrder.swift`; `Models/TapToneAnalyzer+MeasurementManagement.swift`; `Models/TapDisplaySettings.swift`; `Views/Measurements/MeasurementsListView.swift` (`SavedMeasurementsSortMenu`, `SavedMeasurementsMoreMenu`, `SavedMeasurementsDeleteMenu`) |
| Python | `models/saved_measurements_order.py`; `models/tap_tone_analyzer_measurement_management.py`; `models/tap_display_settings.py` and the settings store; `views/measurements/measurements_list_view.py` |
| Web | `src/measurement/savedMeasurementsOrder.ts`; `src/state/tapToneAnalyzer.ts`; `src/settings.ts`; `src/components/MeasurementsPanel.tsx`; the filter icon (`mdi.filter-variant`, from `tooling/parity/gen_web_icons.py`) |

## Found while building

1. **iPad and iPhone: open menus are rebuilt while the spectrum is live** — the item under the pointer loses its
   highlight; More (⋯) → Delete closes. Not #9's code: the analyzer publishes the live peaks on every frame, and on
   iOS each resulting redraw makes SwiftUI refresh the open menus (icons make it visible). The graph's ⋯ and the type
   menu show it too. **Moved to #41** (`LIVE-PEAKS.md`), which holds the evidence and the fix.
2. **Python: a compare tick could land on the wrong row** once a sort or filter was on — the row was found by its
   place in the library rather than where the list shows it. **Done:** found by where it is shown.

## Run-review

On each edition: Mac, iPad, iPhone (Swift); Windows, macOS, Linux (Python); the web on a computer and on a phone or
tablet.

1. Open Saved Measurements. → The list is in the order added, and the Sort & Filter menu shows **As Added ↑** and
   **All** ticked.
2. Choose Name, then Name again. → A to Z, then Z to A; the arrow flips.
3. Choose Type. → Grouped as Generic, Acoustic, Classical, Flamenco, Plate, Brace, then Comparison.
4. Under Show, choose a type. → Only that type is listed, with "Showing n of N · Type" and an ⓧ. Click ⓧ. → All are
   shown again.
5. Close and reopen Saved Measurements; quit and relaunch. → The same sort and filter.
6. With a sort or filter on, delete, edit or double-click a row to load it. → It acts on the row you chose.
7. iPad and iPhone, during a tap sequence: open Sort & Filter, More, and More → Delete, and move the mouse (iPad) or a
   finger over the items; swipe a row to show its Delete. → The highlight follows the pointer or finger and stays; the
   Delete submenu and the swipe stay open. (Verified under #41 — finding 1.)
8. Import the same `.guitartap` file twice; open the Delete menu. → Duplicates… is enabled. Choose it. → The
   confirmation gives the count; afterwards one copy of each is left.
9. Delete → Selected…. → Circles on every row; Compare's place reads "Delete (0)"; Done reads Cancel. Tick two and press
   Delete (2). → The confirmation says 2; those two are gone.
10. With a sort or filter on, repeat step 9. → The rows you ticked are the ones deleted.
11. Delete → Selected…, then Cancel. → The list returns to normal; nothing is deleted.
