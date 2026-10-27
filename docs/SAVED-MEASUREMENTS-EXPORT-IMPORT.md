# Saved Measurements: Export Selected, importing several files, and one meaning for Export, Save to Disk and Share

**Issue:** [#47](https://github.com/dwsdolce/guitar-tap-project/issues/47)

Status: **OPEN — exploration: what each part would take, in every edition; nothing decided.**

An enhancement in three parts, explored before anything is built. Each part is a decision for the owner once its
findings are in.

## 1. Export Selected in the Saved Measurements panel

The panel exports one measurement (its menu: **Export Measurement**) or the whole library (**Export All**), each as one
`.guitartap` file. There is no way to export some of the measurements.

The panel already has two ways of selecting several rows: **Compare** (guitar measurements only, two or more) and
**Delete → Select…**. To explore:

- How the selection is made: a third select mode beside those two, or one select mode whose actions include Export,
  Compare and Delete.
- What is written: one `.guitartap` file holding the selected measurements, as Export All writes the whole library
  (Import already reads such a file).
- The same in Swift (macOS, iPadOS, iOS), Python and the web.

## 2. Importing several files at once

**Import** takes one file in every edition: in Swift its file picker is set to one file
(`allowsMultipleSelection: false`, `MeasurementsListView.swift`). To explore:

- Choosing several `.guitartap` files in Import's file picker, each imported as one Import is now; then one message
  for the lot (what was imported, what was skipped and why).
- Swift (macOS, iPadOS, iOS), Python and the web.

The play-file pickers (`PlayFileSheet.swift`) also take one file each; they are not part of this unless the owner says
so.

## 3. One meaning for Export, Save to Disk and Share (Swift)

Swift uses the three words differently on each platform and for each kind of file:

| Where | macOS | iOS / iPadOS |
|---|---|---|
| A measurement's menu: **Export Measurement** | share sheet (AirDrop, Mail…) | share sheet |
| A measurement's menu: **Save Measurement to Disk…** | save dialog | — (not shown) |
| The panel: **Export All** | a menu: **Export All… (Share / AirDrop)** — share sheet; **Save All to Disk…** — save dialog | share sheet |
| **Export Spectrum**, **Export PDF Report** (menu and Analysis Results) | save dialog | share sheet |

So on the Mac, **Export** means the share sheet for a `.guitartap` file but a save dialog for a spectrum image or PDF,
and a `.guitartap` file has a second command, **Save … to Disk**, that the image and PDF do not. Python and the web
have only **Export**, which saves the file.

To explore: one rule for the Mac — for example **Export…** always opens a save dialog and **Share…** always opens the
share sheet, for every kind of file — and how iOS / iPadOS (where saving is the share sheet's **Save to Files**) fits
it; then the labels in Python and the web, the Help text and the User Manual.
