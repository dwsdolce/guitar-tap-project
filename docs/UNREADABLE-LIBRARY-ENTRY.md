# One unreadable measurement — skip only that entry, in the library and on import

**Issue:** [#34](https://github.com/dwsdolce/guitar-tap-project/issues/34)

Status: **OPEN — item 1 (skip only the bad entry) done in every edition (Swift `1a93221`, Python `26d0939`,
web `d863ef7`), checked on the iPad; item 2 answered — no path found.** Opened 2026-10-19.

## What happened (2026-10-19, the iPad Pro M5)

GuitarTap opened at 20:44:29 and showed "Your saved measurements could not be read, so the library starts
empty". The library — `saved_measurements.json`, 14 measurements, last written 2026-10-11 21:25 — was renamed
`saved_measurements-unreadable-20261019-204429.json` beside itself, as the app does with a library it cannot
read. Nothing was lost.

- **Why it could not be read.** Entry 7 of 14 — "DWS 2024 UMIK-1 Swift iPad", a guitar measurement of
  2026-07-29 20:22:21 — has an **empty spectrum** (`frequenciesData` and `magnitudesData` of 0 bytes), saved
  that way by the July iPad build. Swift `050217d` (2026-10-17) made "a measurement with no spectrum is not a
  measurement" a decode rule (`NoSpectrumError`), and in Swift and Python one failing entry fails the decode of
  the whole file. The other 13 entries decode. The JSON is valid and every id is a UUID. Checked by decoding
  a copy of the kept file with the app's own `decodeMeasurements` on macOS: `no spectrum`.
- **Its premise was wrong.** The decoder's comment says "No edition saves a measurement without its
  spectrum"; this file shows one did (item 2).
- **What opened the app.** The iPad's system log (`log collect` over USB): from 20:44:13 a run of ten touches on
  the screen about a second apart (the Dock's folder view opening and closing, Outlook opening), then a 0.12 s
  touch at 20:44:28.951 and SpringBoard opening GuitarTap at 20:44:29.076 ("SB link"). Touches on the iPad's
  own screen — no test runner, debugger, Universal Control or iOS launch. Not intended by the owner. Any launch
  of a build with the rule would have set the library aside.

## How each edition read a library and an import before item 1

A multi-measurement `.guitartap` comes only from Export All, which writes the library file under another
name, so the library and an import are one format, read by one decoder in each edition.

| | Library on launch | Import of a `.guitartap` |
|---|---|---|
| Swift | `loadPersistedMeasurements` → `decodeMeasurements`; any failure sets the whole file aside, the library starts empty | `importMeasurements(from:)` → `decodeMeasurements`; any failure fails the whole import |
| Python | `load_persisted_measurements` → `measurements_from_json`; as Swift | `import_measurements_from_json` → `measurements_from_json`; as Swift |
| Web | `readLibrary` — records are stored one by one; an unreadable record is left in storage untouched, kept out of the list, and one alert ("Saved Measurements Unreadable", Keep / Delete) names how many | `importMeasurements` → `parseGuitarTapFile`; any failure fails the whole import |

## Items

| # | Item | Status |
|---|---|---|
| 1 | Library load and import skip only an unreadable entry, in every edition, by one mechanism | **done** — Swift `1a93221`, Python `26d0939`, web `d863ef7`; checked on the iPad |
| 2 | Can the current code still save a measurement with an empty spectrum? | answered — no path found, no code change |

### 1 — skip only the unreadable entry

**Decisions** (owner, 2026-10-19):
- Load the readable entries and skip only the bad one — the library and imports alike, since they are one
  format. The iPad's kept library is the device test.
- **One reader in every edition, a list only.** Python and the web also read a single measurement object at
  the top of a file; Swift read only a list. No reason was recorded (both from their editions' earliest
  commits) and no edition writes one. Removed: every edition reads only a list.
- **Nothing is carried forward.** No user can repair an unreadable entry, so there is no Keep / Delete: the
  library is copied aside once, as it was, for debugging, and saved without the entry. The web keeps the
  records under a storage key of its own, as it keeps unreadable calibrations, with no way to send them
  ("do not bother").
- **The message names the place in the user's terms**, not the internal path; no "Show in Finder" (overkill
  for an alert expected almost never).
- The web told the user again after every change (it re-reads its library after each one): it now tells once,
  at launch, as the natives do.

**Behaviour, every edition:**
1. **One decode, entry by entry** — Swift `decodeLibrary(_:)`, Python `decode_library`, web `decodeLibrary`. The
   file must be a JSON list; each entry is decoded on its own; the result is the readable measurements and why
   each other entry could not be read. The strict form (`decodeMeasurements` / `measurements_from_json` /
   `parseGuitarTapFile`) throws the first reason.
2. **Library at launch.** The readable entries load. If any entry cannot be read, the library is first copied
   aside as it was — natives: `saved_measurements-unreadable-<date and time>.json` beside it; web: the records
   under `gt.measurements-unreadable-<date and time>` and out of the library — then saved without them, and one
   alert, "Saved Measurements Unreadable", OK: "1 saved measurement could not be read and was removed from the
   list. The original file was kept as saved_measurements-unreadable-….json in the GuitarTap folder in Files (On
   My iPad › GuitarTap)." (macOS and Python: "in GuitarTap's data folder, ~/…" — the whole path on Windows,
   whose Explorer does not read `~`; web: the first sentence only). If the copy cannot be made, nothing is
   written this session and the message says the file was left as it is. A file that is not a JSON list is set
   aside whole, as before; its message names the place the same way.
3. **Import.** The readable entries are imported; the picked file is not touched. The message adds "1
   measurement in the file could not be read and was not imported (no spectrum)." — the reason only when one was
   skipped, otherwise "2 measurements in the file could not be read and were not imported." If none can be read
   the import fails with the existing messages.
4. The false comment "No edition saves a measurement without its spectrum" corrected in every edition.
5. **Tests** — shared `import-persistence.json`: IP11 rewritten (it held "a file is imported whole or not at
   all"); IP15–IP16 skipped entries on import; IP17 a bare object is refused; IL1–IL3 a library at launch (one
   unreadable entry, none, all), with the new `libraryHolds` step and the `libraryMessage(StartsWith)` /
   `keptCopy` expectations. Each edition's own tests: a file none of which can be read is set aside (cut short,
   not a list); a library that cannot be kept aside is not written (folder read-only; on Windows the copy is
   refused in the test, since Windows ignores a folder's read-only flag).

**Done:** Swift `1a93221`, Python `26d0939`, web `d863ef7` (2026-10-19).

**Verification:**
- Targeted tests pass: Swift ImportPersistence (macOS); Python `test_import_persistence.py` (29) and the
  decode-using suites (213); web `import-persistence.test.ts` (28) and the 17 suites that read files (385);
  web typecheck. Swift builds for iOS.
- iPad, owner, 2026-10-19: restored the kept library and ran the Swift build — worked. That build's message
  still gave the internal path; the place-in-the-user's-terms wording came after it.

### 2 — can the app still save an empty spectrum?

**Answer: no path found; no code change.** The owner's earlier search (#17, 2026-10-17, record
`docs/completed/SLUG-SWEEP.md`) found none in any released version, and no file in GitHub had one; it
checked 700 measurements on the Mac, but not the iPad's library, which held this one.

- The entry is a **re-save from a development build**: on 2026-07-29 all six measurements of 2026-07-17 were saved
  again, 10–40 s apart, with the same names and peaks (the guitar one also with a changed selection), on a build
  before 1.0.2 shipped (2026-08-01). Only the first of the six lost its spectrum. Which state of that build did it
  is not recoverable.
- **Today's Swift** (checked 2026-10-19): Save is enabled only for a complete measurement or a comparison
  (`hasResultToSaveOrExport`); a complete guitar measurement saves its frozen spectrum, which the capture and
  `loadMeasurement` both set; a material completion clears the frozen spectrum but saves its phase spectra; a
  change between guitar and material in Settings starts a new measurement. No path leaves a complete guitar
  measurement with an empty frozen spectrum.
- If one ever appears again, item 1 costs only that entry, and the copy kept aside is the evidence.

