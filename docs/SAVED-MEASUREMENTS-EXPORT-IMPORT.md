# Saved Measurements: Export and Share, Export Selected, and importing several files

**Issue:** [#47](https://github.com/dwsdolce/guitar-tap-project/issues/47)

Status: **OPEN — built in all three editions and committed (GuitarTap `4d2b978`, guitar_tap `cde1f9a`, GuitarTapWeb `30008c8`; release-note markers moved: `d59609e`, `82a15c6`, `d6d3581`); run-review passed (owner, 2026-10-27) on macOS — Swift, Python, web — and on iPad and iPhone, the iPad's menu bar (steps 16–18) included; Windows and Linux after the commit; full suites and export UI tests green (Swift unit 309, Python 1641, web 1479; exports 24/24 on Mac, iPad, iPhone, Python, web); next: CI, then Windows and Linux.**

## The request (owner, 2026-10-26)

An enhancement, in three parts:

1. **Export Selected** in the Saved Measurements panel. A measurement's menu exports one measurement and Export All
   the whole library; nothing exports some of them.
2. **Importing several files at once.** Import's file picker takes one file, in every edition.
3. **One meaning for Export, Save to Disk and Share in Swift.** On the Mac, Export Measurement and Export All open the
   share sheet while Export Spectrum and Export PDF Report open a save dialog, and only a measurement file has a
   Save … to Disk; on iOS and iPadOS everything goes to the share sheet. Python and the web have only Export, which
   saves.

Part 1's menu items follow from part 3's rule, so the two are decided together.

## The design

**One rule.** **Export** writes a file to disk through a save dialog, in every edition. **Share** opens the system's
share sheet (AirDrop, Mail, Messages, Save to Files…), in Swift only — the Python and web editions have none. Where
both exist, both are offered; where saving *is* the share sheet (iOS and iPadOS, through Save to Files), only Share is.

| | Mac (Swift) | iOS / iPadOS (Swift) | Python, web |
|---|---|---|---|
| **A measurement's menu** (its ⋯, right-click or long press) | Export… and Share… — for the measurement, its spectrum image and its PDF report | Share — for each of the three | Export… — for each of the three |
| **The panel's menu** (Saved Measurements' toolbar) | **Export**: Export All…, Export Selected…, Share All…, Share Selected… | **Share**: Share All, Share Selected | **Export**: Export All…, Export Selected… |
| **Analysis Results** (the main window's results panel) | one **Export** button: Export Spectrum…, Export PDF Report…, Share Spectrum…, Share PDF Report… | one **Share** button: Share Spectrum, Share PDF Report | one **Export** button: Export Spectrum…, Export PDF Report… |

**"…" follows the platforms' rule** (style guide S9): an item ends in "…" when it needs more from the user before it
is done — a save dialog, the share picker, a select mode — on the Mac, Windows and Linux; on iOS and iPadOS, none, as
Apple's own menus. So Export Measurement… and Share Spectrum… on the Mac, Export All… in Python, Share All on the iPad.

**Order on the Mac: Export first, then Share**, in every menu that has both, as in Apple's menus (owner).

**Selected** works as **Delete → Selected…** does today: tick any measurements, then **Share (N)** or **Export (N)**.
All, or the selected ones, go into one `.guitartap` file.

Analysis Results' two buttons (Export Spectrum, Export PDF) become one, whose menu has the same entries as a
measurement's menu — so every place offers the same choices the same way, with no need for the Mac's menu bar. The
Mac's File menu has Share Spectrum Image… and Share PDF Report… after its Export Spectrum Image… and Export PDF
Report…, as everywhere on the Mac; Python's menu bar keeps its Export items.

**The iPad's menu bar** (iPadOS's, with a keyboard or a pointer) gets Guitar Tap's menus, found missing while adding
Share to the Mac's (owner): the application menu's **About Guitar Tap** (a sheet: the icon, the name, the version
and build, Python's description, the copyright — iPadOS supplies none) and **Settings…** (⌘,), Guitar Tap's own in
place of the system's Guitar Tap Settings…; **File** — Play Audio File…, Save Measurement…, Share Spectrum Image…,
Share PDF Report… (no Export: no save dialog); **View** and **Help** as the Mac's; the Mac's shortcuts. Its items take
"…" as the Mac's do, as Apple's own iPad menu bar items do (owner, S9).

**Import takes several files at once.** If an import brings in exactly one measurement, it is loaded into the main
view, as now; if it brings in several, none is loaded — the screen stays as it is, as importing an Export All file
does today, and the message counts what was imported. ("The last" was the alternative; it is not something a user
can predict: in a file it is the export's order, across several files the file picker's, which differs by platform
and browser. Most multi-file imports bring in several good measurements, so this is the common case.)

What goes: the Mac's **Save Measurement to Disk…** and **Save All to Disk…** (each is now an Export), and the words
"Export" for the share sheet on the Mac and on iOS.

**Considered and left out: Export Measurement in Analysis Results** (exporting a measurement that has not been
saved). A measurement becomes a file after **Save**, where it gets its name and notes; exporting an unsaved one would
either ask for them again — a second Save — or write an unnamed file. Save, then the measurement's own menu, already
does it in one more step, and an export without a save is an easy way to lose the measurement from the list.

## Why it is small

Each edition's Export All already writes whatever list it is given (Swift `encodeMeasurements(_:)`, Python
`measurements_to_json`, the web's `serializeGuitarTapFile`), so Selected passes the ticked ones; the select mode is
Delete's. Each file picker takes several files when asked (Swift `allowsMultipleSelection`, Python
`getOpenFileNames`, the web's `multiple`); the import itself, and what it loads, stay in the model, so the three
editions word the result the same way.

## Where it lives now

| | Swift | Python | Web |
|---|---|---|---|
| A measurement's menu | `SavedMeasurementMenu.swift` (case file `saved-measurement-menu.json`) | `saved_measurement_menu.py` | `savedMeasurementMenu.ts` |
| The panel's toolbar, select modes, Import | `MeasurementsListView.swift` | `measurements_list_view.py` | `MeasurementsPanel.tsx` |
| Analysis Results' two buttons | `TapAnalysisResultsView.swift` | `tap_tone_analysis_view.py` (`export_spectrum_btn`, `export_pdf_btn`) | `App.tsx` (the export footer) |
| Save dialog and share sheet | `MeasurementFileExporter.swift` — Mac: `NSSavePanel`, `NSSharingServicePicker` (today for measurement files only); iOS: `UIActivityViewController` | `measurement_file_exporter.py` (save only) | `saveFile.ts` (save only) |
| Import and what it loads | `importAndLoadMeasurements` (`TapToneAnalyzer+MeasurementManagement.swift`) | its port | its port |

## Plan

Swift first, then Python and the web the same way. Each step's tests are written first and fail.

1. **The menus as data, in shared case files.** `saved-measurement-menu.json` gives each platform's items (Mac,
   iOS / iPadOS, Python and the web): Export… and Share… for the measurement, spectrum and PDF on the Mac; Share on
   iOS; Export in Python and the web; **Save Measurement to Disk…** gone. A new `export-menus.json` gives the panel's
   menu and Analysis Results' menu the same way: the button's word (Export or Share) and its items. Each edition's
   menu tests read them.
2. **Export and Share, per file kind (Swift).** `MeasurementFileExporter` offers both on the Mac for all three kinds
   — a measurement file, a spectrum image, a PDF report: Export through the save dialog, Share through the sharing
   picker (today the Mac shares only a measurement file and saves the other two). iOS shares all three, as now.
3. **A measurement's menu** (all three editions) from step 1's data.
4. **The panel's menu and Selected** (all three): the Export (Mac, Python, web) or Share (iOS) menu with All and
   Selected; Selected uses the select mode **Delete → Selected…** has — one mode, told what it is selecting for
   (delete, export or share), its confirm button **Delete (N)**, **Export (N)** or **Share (N)**. All, or the
   selected ones, written as one `.guitartap` file through the same call Export All uses.
5. **Analysis Results' one button** (all three): Export (Mac, Python, web) or Share (iOS), its menu from step 1's
   data; the two buttons it replaces go. Its items do what the two buttons did, for the spectrum and the report.
6. **Import of several files** (all three): the file picker takes several; the model imports them all and words one
   message — how many measurements from how many files, then each file or entry it could not read, with the reason
   today's message gives; exactly one measurement imported loads it, several load none. The message's words in a
   shared case file, so the three say the same.
7. **"…" by the style guide's S9 elsewhere** (all three; checked 2026-10-26 — every button and menu item outside the
   toolbar): Saved Measurements' **Import** becomes **Import…** (a file dialog), and Settings' **Delete All
   Calibrations** becomes **Delete All Calibrations…** (it confirms first); on iOS and iPadOS neither changes. Every
   other item already follows it; toolbar buttons are exempt.
8. **Help and the Quick Start** (all three), **the User Manual** (ch07, *Save, Export and Share*, and wherever it
   names these buttons), and **1.1.0's release notes** (all three, shown to the owner before committing).
9. **Run-review** (below), then the full suites on the owner's go.

Screenshots of Analysis Results and of the measurement menu change: #26's list gets them.

**Built (2026-10-26/27):** steps 1–8 in all three editions; each edition's menu, export-menu and import
tests pass (the six multi-file cases IF1–IF6 among them), Swift builds for macOS and iOS, and the Python and web export
end-to-end tests pass (the web's 24 exports match Swift's). One selected measurement is written under its own
name, as its own Export or Share names it; two or more as `guitartap-measurements-<time>.guitartap` (all of them, as
before, `guitartap-library-<time>.guitartap`). Found and
fixed on the way: Swift had two save-or-share helpers (`FileExportHelper` for the main window's image,
`MeasurementFileExporter` for the rest) — now one, `MeasurementFileExporter.deliver(_:filename:contentType:as:)`;
Python's and the web's Delete menu had no icons, Swift's had (S6); the manual named a **File → Import Measurement**
item and drag-and-drop import, neither of which exists, and called Settings' **Delete All Calibrations** "Clear All
Calibrations".

## Run-review

**Mac (Swift)**

1. In Saved Measurements, open a measurement's menu. → Export Measurement…, Export Spectrum…, Export PDF Report…,
   Share Measurement…, Share Spectrum…, Share PDF Report…; no Save Measurement to Disk….
2. Choose Export Measurement…. → A save dialog; the file is written where chosen.
3. Choose Share Spectrum…. → The share sheet, with the spectrum image.
4. Click the panel's Export menu. → Export All…, Export Selected…, Share All…, Share Selected….
5. Choose Export Selected…, tick two measurements of different types, click Export (2). → A save dialog; the file
   holds those two (import it into an empty library to check).
6. Choose Share Selected…, tick one, click Share (1). → The share sheet with one `.guitartap` file, named as that
   measurement's own Share Measurement… names it (two or more: `guitartap-measurements-<time>.guitartap`).
7. With a measurement on screen, click Analysis Results' Export button. → Its menu: Export Spectrum…, Export PDF
   Report…, Share Spectrum…, Share PDF Report…; each does what it says.
   Then File → Share Spectrum Image… and File → Share PDF Report…. → The share sheet, with the image, then the
   report.
8. Click Import…, choose three files, each holding one measurement. → All three in the list; one message counts 3
   measurements from 3 files; the main view unchanged.
9. Click Import…, choose one file holding one measurement. → It is imported and loaded, as now.
10. In Settings → Audio Input, with a calibration stored, look at the delete button. → **Delete All Calibrations…**;
    clicking it asks first.

**iPad and iPhone (Swift)**

11. Open a measurement's menu. → Share Measurement, Share Spectrum, Share PDF Report.
12. Open the toolbar's More menu. → A Share menu: Share All, Share Selected.
13. Share Selected, tick two, Share (2). → The share sheet; Save to Files writes one `.guitartap` file.
14. Analysis Results' Share button. → Share Spectrum, Share PDF Report.
15. Import, choose three files in Files. → As step 8.
16. On the iPad with a keyboard or pointer, open the menu bar's Guitar Tap menu. → About Guitar Tap, then Settings…
    (⌘,); choosing About shows the icon, Guitar Tap, the version and build, and the copyright; Settings opens Guitar
    Tap's Settings.
17. The menu bar's File menu, with a measurement on screen. → Play Audio File…, Save Measurement…, Share Spectrum
    Image…, Share PDF Report… (no Export); each Share opens the share sheet.
18. The View and Help menus, then hold ⌘. → View: Auto dB, Cycle Annotations, Show Metrics, Show Measurements;
    Help: Quick Start Guide, User Manual; each does what it says; the shortcuts list shows the Mac's.

**Python (macOS, Windows, Linux) and the web**

19. A measurement's menu. → Export Measurement…, Export Spectrum…, Export PDF Report…; no Share.
20. The panel's Export menu. → Export All…, Export Selected…; Export Selected… as step 5.
21. Analysis Results' Export button. → Export Spectrum…, Export PDF Report….
22. Click Import… and choose several files. → As steps 8–9.
23. Settings' delete button for calibrations. → As step 10.
