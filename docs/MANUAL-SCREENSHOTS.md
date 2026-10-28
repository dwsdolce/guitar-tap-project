# Screenshots and images for the 1.1.0 release

**Issue:** [#26](https://github.com/dwsdolce/guitar-tap-project/issues/26)

Status: **OPEN — list made and the manual's images reviewed; nothing recaptured.**

## The problem

The user manual's screenshots predate the interface work of this release and no longer match the apps: the shared
palette and the Appearance setting (System / Light / Dark), the Results panel, the Settings sheet (grouped boxes, one
row per setting, menu pickers, Appearance first in Display Settings), the measurement-type button beside New Tap, the
status bar, Saved Measurements (Sort & Filter, the Delete menu), Measurement Details, the Save and Play Audio File
sheets, the comparison legend inside the plot, and the exports' Selected Peaks. The App Store's and the website's
images show the same screens.

## The images

Every image is recaptured from the 1.1.0 release build. A manual image's chapter carries a `SCREENSHOT:` note above it
(the file, the subject, the cropping); where an image has none, the subject below is its caption.

### User manual — `GuitarTap/Documentation/Manual/images/`

Reviewed against the apps as they are now (2026-10-25). **Out of date** means something in the image is missing,
gone, moved or renamed in the app; colour differences alone are not counted.

| # | Image | Where | Subject | Review |
|---|---|---|---|---|
| 1 | `ch01-main-analysis-screen.png` | ch01 | A completed guitar measurement: spectrum with annotated peaks; the Results panel | **Out of date:** no measurement-type button beside New Tap; the Results panel's Select All button, since removed; no chart menu (⋯) beside ⓘ; the window title reads "Guitar Tap 1.0 (324)". No `SCREENSHOT:` note — add one **#47:** Analysis Results' Export Spectrum and Export PDF buttons are now one **Export** button (with a menu). |
| 2 | `ch02-settings-sheet.png` | ch02 | Settings: Audio Input & Calibration, Measurement Type | **Compare with the app:** the same sections and rows; the empty rows between some settings may be gone. No note — add one |
| 3 | `ch02-threshold-peakmin-toolbar.png` | ch02 | The live spectrum after a tap, with the Threshold and Peak Min sliders | **Minor:** only the chart menu (⋯) beside ⓘ is missing; the sliders it shows are unchanged. No note — add one |
| 4 | `ch03-results-panel.png` | ch03 | The Analysis Results panel: peak list, ring-out, tap-tone ratio | **Out of date:** the Select All button, since removed **#47:** Export Spectrum and Export PDF are now one **Export** button. |
| 5 | `ch03-comparison-overlay.png` | ch03 | Three guitar spectra compared, with the Comparison Results table | **Out of date:** no measurement-type button beside New Tap; no chart menu (⋯) **#47 — check:** if the Results panel's foot is in the frame, its two export buttons are now one **Export**. |
| 6 | `ch04-settings-plate.png` | ch04 | Settings with Plate selected: dimensions, stiffness preset, Measure Diagonal (fLC) Tap | **Compare with the app:** as image 2 |
| 7 | `ch04-results-panel.png` | ch04 | The plate Results panel: Selected Peaks, Sample and Body Dimensions, Gore Target Thickness, Plate Properties, Process Instructions | **Current** |
| 8 | `ch05-settings-brace.png` | ch05 | Settings with Brace selected: Length, Width, Height, Mass | **Compare with the app:** as image 2 |
| 9 | `ch05-results-panel.png` | ch05 | The brace Results panel: Selected Peaks (the fL row), Sample Dimensions, Brace Properties, Process Instructions | **Current** |
| 10 | `ch06-scroll-zones.png` | ch06 | The chart with its three scroll-wheel zones marked | **Current** for what it shows; only the chart menu (⋯) is missing |
| 11 | `ch07-measurements-list.png` | ch07 §7.2 | Saved Measurements (desktop) | **Out of date:** no Sort & Filter; Delete All, which became the Delete menu (All…, Duplicates…, Selected…) (#9); no "Total: N measurements" line **#47:** **Import** is now **Import…**; **Export All** is now an **Export** menu (Export All…, Export Selected…, Share All…, Share Selected…). |
| 12 | `ch07-measurements-list-ios.png` | ch07 §7.9 | Saved Measurements on iPad / iPhone with the ⋯ menu open | **Out of date:** the ⋯ menu is not open, as the caption says; no Sort & Filter beside it; the Delete menu (#9) **#47:** the More (⋯) menu has a **Share** submenu (Share All, Share Selected) in place of Export All Measurements. |
| 13 | `ch08-settings-advanced.png` | ch08 §8.5 | Settings → Advanced: Display Settings and Analysis Settings | **Out of date:** Display Settings now opens with the Appearance row (System / Light / Dark) |
| 14 | `ch09-iphone-portrait.png` | ch09 | iPhone portrait: toolbar, icon row, the top of Tap Controls | **Out of date:** no measurement-type button beside New Tap |
| 15 | `ch09-iphone-landscape.png` | ch09 | iPhone landscape: Tap Controls left, spectrum right | **Out of date:** no measurement-type button beside New Tap; the title reads "Guitar Tap 1.0 (325)" |
| 16 | `ch09-ipad.png` | ch09 | iPad: toolbar, Tap Controls, spectrum and Analysis Results side by side | **Out of date:** no measurement-type button; the Select All button; the title reads "Guitar Tap 1.0 (325)" **#47 — check:** the Results panel's foot has one **Share** button on the iPad. |
| 17 | `ch09-desktop.png` | ch09 | macOS with the File menu open, a plate loaded | **Out of date:** no measurement-type button; the Select All button; the plate's peaks and legend read L / C / FLC, now fL / fC / fLC **#47:** the File menu shown open has **Share Spectrum Image…** and **Share PDF Report…** after its Export items; the Results panel has one **Export** button. |
| 17a | `ch09-ipad-menubar.png` (new) | ch09 §9.4 | The iPad with a keyboard or pointer, its menu bar's File menu open: Play Audio File…, Save Measurement…, Share Spectrum Image…, Share PDF Report… | **New (#47):** the iPad's menu bar has Guitar Tap's menus; the manual describes it in §9.4 without an image. Add a `SCREENSHOT:` note there |

So: **out of date — 1, 4, 5, 11, 12, 13, 14, 15, 16, 17** (ten); **new — 17a**; **compare with the app — 2, 6, 8** (the Settings
sheets); **minor — 3**; **current — 7, 9, 10**.

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

**#47 — check:** any of these that shows the foot of Analysis Results has the old Export Spectrum / Export PDF buttons — now one Export (Mac) or Share (iPad, iPhone) button.

Uploaded in App Store Connect with the release (release checklist §1c).

### Website — `guitar_tap_website/`

**#47 — check:** images 25–31 follow the App Store's, so the same check applies (the foot of Analysis Results).

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
| 34 | `examples/dws-2024-spectrum.png` and `examples/dws-2024-report.pdf` | Export Spectrum and Export PDF Report of `examples/dws-2024.guitartap` — exported again: the reports' peaks are Selected Peaks (#45) |

The website changes last: after Apple approves the release and every file is on GitHub (release checklist §4).

## Plan

1. Recapture the out-of-date manual images (1, 4, 5, 11–17), and 2, 6 and 8 if the Settings sheets differ, from the
   1.1.0 release build, following each `SCREENSHOT:` note; add the notes images 1–3 lack; regenerate the manual and
   check it.
2. Recapture images 18–24 for App Store Connect.
3. After Apple approves the release and the files are on GitHub: images 25–33 (from 18–24 and the web edition) and the
   example's exports (34) on the website.
