# Screenshots and images for the 1.1.0 release

**Issue:** [#26](https://github.com/dwsdolce/guitar-tap-project/issues/26)

Status: **CLOSED (2026-10-28)** — GuitarTap `8436e9e` (the manual), guitar_tap_website `eeece1c` (the example); the owner reviewed both.

## The problem

The user manual's screenshots predate the interface work of this release and no longer match the apps: the shared
palette and the Appearance setting (System / Light / Dark), the Results panel, the Settings sheet (grouped boxes, one
row per setting, menu pickers, Appearance first in Display Settings), the measurement-type button beside New Tap, the
status bar, Saved Measurements (Sort & Filter, the Delete menu), Measurement Details, the Save and Play Audio File
sheets, the comparison legend inside the plot, and the exports' Selected Peaks. The App Store's and the website's
images show the same screens.

## Decision

The manual's images are recaptured: the manual describes the app control by control, so its images must match it.

The App Store's (18–24) and the website's (25–33) images are kept as they are. They are marketing: they show the app
in use, as Apple requires, and its layout, chart, annotations, Results cards and palette are essentially 1.1.0's. What
differs is detail a buyer does not notice and a reviewer does not reject an update for — the two export buttons (now one
Export, or Share on the iPad and iPhone), no type button beside New Tap, the Select All button, "1.0 (330)" in the
title, L / C / FLC on the plate (now fL / fC / fLC). App Store Connect carries the screenshots over to the new version.

The website's example (34) is replaced: its exports are the app's real output offered as an example, and 1.1.0 changed
what a report holds (Selected Peaks, #45). The newer measurement is three taps averaged, so its report also shows the
tap comparison page.

## The images

A manual image's chapter carries a `SCREENSHOT:` note above it
(the file, the subject, the cropping); where an image has none, the subject below is its caption.

### User manual — `GuitarTap/Documentation/Manual/images/`

All recaptured by the owner on 1.1.0 (661), 2026-10-27, reviewed and copied into the manual. Each image's chapter
carries a `SCREENSHOT:` note above it (the file, the subject, the cropping).

| # | Image | Where | Subject |
|---|---|---|---|
| 1 | `ch01-main-analysis-screen.png` | ch01 | A completed guitar measurement: spectrum with annotated peaks; the Results panel |
| 2 | `ch02-settings-sheet.png` | ch02 | Settings: Audio Input & Calibration, Measurement Type |
| 3 | `ch02-threshold-peakmin-toolbar.png` | ch02 | The spectrum with the Threshold and Peak Min sliders above |
| 4 | `ch03-results-panel.png` | ch03 | The Analysis Results panel: peak list, ring-out, tap-tone ratio, Export |
| 5 | `ch03-comparison-overlay.png` | ch03 | Three guitar spectra compared, with the Comparison Results table |
| 6 | `ch04-settings-plate.png` | ch04 | Settings with Plate selected (two halves side by side) |
| 7 | `ch04-results-panel.png` | ch04 | The plate Results panel (two halves side by side) |
| 8 | `ch05-settings-brace.png` | ch05 | Settings with Brace selected: Length, Width, Height, Mass |
| 9 | `ch05-results-panel.png` | ch05 | The brace Results panel |
| 10 | `ch06-scroll-zones.png` (source `ch06-scroll-zones.svg`) | ch06 | The chart with its three scroll-wheel zones marked |
| 11 | `ch07-measurements-list.png` | ch07 §7.2 | Saved Measurements (Mac), with a row's ⋯ menu and the Sort & Filter, Export and Delete menus |
| 12 | `ch07-measurements-list-ios.png` | ch07 §7.9 | Saved Measurements on the iPad, with the Sort & Filter menu and the ⋯ menu's Delete submenu |
| 13 | `ch08-settings-advanced.png` | ch08 §8.5 | Settings → Advanced: Display Settings and Analysis Settings |
| 14 | `ch09-iphone-portrait.png` | ch09 | iPhone portrait: toolbar, icon row, Tap Controls, spectrum |
| 15 | `ch09-iphone-landscape.png` | ch09 | iPhone landscape: Tap Controls left, spectrum right |
| 16 | `ch09-ipad.png` | ch09 | iPad: toolbar, Tap Controls, spectrum and Analysis Results |
| 17 | `ch09-desktop.png` | ch09 §9.4 | macOS with the File menu open |
| 17a | `ch09-ipad-menubar.png` | ch09 §9.4 | The iPad's menu bar with the File menu open |

Accepted as they are: the focused Length field in 6 and 8, pointer arrows in 12 and 16, the Mac menu bar's status
icons in 17, and New Tap wrapping onto two lines in 14. A later build number in the window titles does not call for a
retake.

Not screenshots — unchanged: `ch04-plate-hold-tap.png` and `ch05-brace-hold-tap.png` (drawings of where to hold and
tap), `guitar-tap.png` (the logo on the front page). The inline icons in `images/symbols/` are SF Symbols.

### App Store — `GuitarTap/Documentation/AppStoreImages/`

| # | Image | Subject |
|---|---|---|
| 18 | `macOS Classical.png` | macOS, a classical guitar measurement |
| 19 | `macOS Comparison.png` | macOS, a comparison |
| 20 | `macOS Plate.png` | macOS, a plate measurement |
| 21 | `macOS Brace.png` | macOS, a brace measurement |
| 22 | `iPad Classical.png` | iPad, a classical guitar measurement |
| 23 | `iPhone Classical Spectrum.png` | iPhone, the spectrum |
| 24 | `iPhone Classical Results.png` | iPhone, the Results |

Kept as they are (see Decision). Should any be replaced later, `ch09-ipad.png` (22) and `ch09-iphone-portrait.png` (23)
are already at Apple's sizes (2752 × 2064, 1320 × 2868); a Mac image must be 2880 × 1800, 2560 × 1600, 1440 × 900 or
1280 × 800.

### Website — `guitar_tap_website/`

25–33 are kept as they are (see Decision); 34 is exported again.

| # | Image | Subject |
|---|---|---|
| 25 | `images/macos-classical.jpg` | as the App Store's macOS Classical |
| 26 | `images/macos-comparison.jpg` | as the App Store's macOS Comparison |
| 27 | `images/macos-plate.jpg` | as the App Store's macOS Plate |
| 28 | `images/macos-brace.jpg` | as the App Store's macOS Brace |
| 29 | `images/ipad-classical.jpg` | as the App Store's iPad Classical |
| 30 | `images/iphone-spectrum.jpg` | as the App Store's iPhone Spectrum |
| 31 | `images/iphone-results.jpg` | as the App Store's iPhone Results |
| 32 | `images/web-classical.png` | the web edition, a classical guitar measurement |
| 33 | `images/og-image.png` | the link preview image |
| 34 | `examples/dws-2024-umik-1-3-tap-swift-mac-1785359425.guitartap`, `.png` and `.pdf`, and `examples.html` | A newer measurement (the three-tap UMIK-1 measurement from `Tests/AllPlatforms/`) and its Export Spectrum and Export PDF Report from 1.1.0 (662), under the file's own name; they replace `dws-2024.guitartap`, `dws-2024-spectrum.png` and `dws-2024-report.pdf`. The page's links, link preview and text updated. On upload, delete the three old files from `…/guitar_tap/examples/` |

The website changes last: after Apple approves the release and every file is on GitHub (release checklist §4).

## Plan

1. The manual's images (1–17a): recaptured and in the manual. Tall panels (2.3, 3.8, 5.4) are capped at 150 mm high
   (`screenshot-panel-tall`) and short narrow crops (5.2, 8.5) at 95 mm wide (`screenshot-panel-small`), so their text
   prints near the manual's own size; in the PDF a table breaks between rows, its header repeated. Done.
2. The website's example (34): replaced in `guitar_tap_website`. Done. A commit publishes nothing there: its files are
   uploaded by hand with the release, after Apple approves it (release checklist §4), and the three old example files
   are deleted from the server then.
