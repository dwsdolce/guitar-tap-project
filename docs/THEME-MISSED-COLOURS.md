# Theme — colours the inventories missed

Follow-on to #2 (record: [`completed/THEME-SPEC.md`](completed/THEME-SPEC.md)). Found 2026-10-15 during the #17
load-path run-review: after a plate load, Python's Peak Min label and value were not faded as Swift's are, and
neither were in Swift's colours.

**Why #2 missed these.** Its inventories (`completed/theme/INVENTORY-*.md`) listed each edition's colour *literals*.
An item drawn in the default colour has no literal, so where Swift names a role and an edition leaves the default
(or the reverse), the item never appeared. This sweep went the other way: every place Swift sets a colour (or a
dimming opacity), and the same item in Python and the web — plus items Python or the web colour where Swift leaves
the system default. PDF/PNG exports were not swept (#2's export findings compared them).

**Already fixed** (in the #17 load-path work, uncommitted at filing): Peak Min row disabled and faded to 0.4 for
plate/brace and in a comparison (Python, web — the web hid it); the Threshold value in `accentText` and the Peak Min
value in `chartPeakMin`, medium weight (Python, web); Python's Taps / Threshold / Peak Min labels in `textSecondary`.

**Python baseline.** The application stylesheet sets every `QLabel` to `text.primary` and a tagged widget to its
role, with no `:disabled` variant (`views/utilities/palette.py` `_application_stylesheet`) — so no Python label ever
greys when disabled. That is the cause of item 1 and should be fixed in the stylesheet, not per label.

File:line references are as found on 2026-10-15; verify before editing.

## Items

| # | item | Swift | Python | web | status |
|---|---|---|---|---|---|
| **A** | **an edition leaves the default where Swift names a role** | | | | |
| 1 | Taps field dimmed while a sequence is in flight | `.disabledDimmed` 0.45 on label, value, stepper (TapToneAnalysisView+Controls.swift:817; Extensions.swift:222) | `setEnabled(False)` only — not visibly dimmed (tap_tone_analysis_view.py ~3068) | 0.45 (App.css `.field.is-disabled`) | open |
| 2 | Settings: mode-range names ("Air:", "Top:" …) | `textSecondary` (TapSettingsView+LayoutHelpers.swift:233) | default (tap_tone_analysis_view.py ~5686) | secondary (SettingsPanel.tsx:458) | open |
| 3 | Settings: active calibration details | `textSecondary` (TapSettingsView+Sections.swift:100) | default (tap_tone_analysis_view.py ~6451) | secondary (`.ts-cal-details`) | open |
| 4 | Settings: dump-folder buttons (Open Folder / Change… / Use Default) | accent tint (Sections.swift:336) | untinted (tap_tone_analysis_view.py ~6187) | no folder row | open |
| 5 | Settings: "Saved to" + path | "Saved to" secondary, path primary (Sections.swift:330–331) | one label, all secondary (tap_tone_analysis_view.py ~6180) | no folder row | open |
| 6 | Measurement Details: "No identified peaks" | `textSecondary` (MeasurementDetailView.swift:180) | default (measurement_detail_view.py:150) | secondary | open |
| 7 | Edit Measurement: Save button | `.confirmationAction` (EditMeasurementView.swift:76) | plain (edit_measurement_view.py:130); its Save sheet is accent | accent (`btn-primary`) | open |
| 8 | Notes editor border (Save, Edit sheets) | `separator` stroke (SaveMeasurementSheet.swift:109) | Qt default frame | separator | open |
| 9 | Comparison / multi-tap table cells with a frequency | `textPrimary` (ComparisonResultsView.swift:99; MultiTapComparisonResultsView.swift:132) | no foreground — platform colour (comparison_results_view.py ~172) | primary | open |
| 10 | Metrics sheet: processing time / CPU values by load | `metric.good/fair/high/overload` (FFTAnalysisMetricsView.swift:94–189) | same | default (MetricsPanel.tsx:108–124) | open |
| **B** | **the item (and so its colour) is missing** | | | | |
| 11 | Plate placeholder "Select a longitudinal (L) peak" / "Select a cross-grain (C) peak"; brace "Select the fL (L) peak…" | `statusWarning` / `textSecondary` (TapAnalysisResultsView.swift:797–803, 942) | only "Select peaks above…" | no placeholder (MaterialResults.tsx:241) | open |
| 12 | "No peaks detected in visible range" | `textSecondary` (TapAnalysisResultsView.swift:512) | absent | "No peaks above Peak Min." | open |
| 13 | Chart Options section headers | `textSecondary` (SpectrumView.swift:1291) | absent (QMenu) | secondary | open |
| 14 | Status bar "Starting..." | `textSecondary` when not running (Controls.swift:569) | blank | shown on a different condition, `status.peakReadout` | open |
| 15 | Loaded-settings banner icon | separate `statusWarning` icon, pulsing (Controls.swift:472) | same | "⚠" glyph in the text, no pulse | open |
| 16 | Measurements empty state | icon secondary, title primary semibold, message secondary (EmptyStateView.swift:24–36) | one secondary label, no icon | one secondary paragraph, no icon | open |
| 17 | Slider reset buttons | `textSecondary` (Controls.swift:615, 630) | same | absent | open |
| 18 | Loading overlay | `ProgressView` default (LoadingOverlay.swift:28) | spinner `text.onColor` | absent | open |
| **C** | **an edition names a role where Swift uses the system default — decide which way** | | | | |
| 19 | Header icon buttons (Re-analyze, Select None, wand) | `.tintedBordered`, no tint | secondary icon on `background.subtle` | same as Python | open |
| 20 | Export Spectrum / Export PDF | `.tintedBordered`, no tint | native button, primary icon | `background.picker` fill | open |
| 21 | Quick Start section headers | system list header | secondary | secondary | open |
| 22 | Material instructions box (title, surface) | GroupBox default | title secondary bold; panel + separator | same as Python | open |
| 23 | Measurement Details group boxes | GroupBox default | QGroupBox default | `background.subtle` | open |
| 24 | Hover: measurement row / row ⋯ button | none | row `background.subtle` | ⋯ subtle + border | open |
| 25 | Row menu Delete | `role: .destructive` | default | `status.error` | open |
| 26 | Cancel / Redo fill | text in role, neutral fill (Controls.swift:918) | 5 % fill in the role | tinted fill | open |
| 27 | Chart ⋯ / ⓘ buttons | secondary, plain (SpectrumView.swift:470, 491) | same | + border and readout-background circle | open |
| 28 | Material spectra legend text | series colour (SpectrumView.swift:572) | series colour | secondary, + border | open |
| **D** | **surfaces** | | | | |
| 29 | Tap-controls bar | `background.subtle`, radius 8 (Controls.swift:792) | separator bottom border only | panel + border, radius 10 | open |
| 30 | App button row | none | separator bottom border | panel + border | open |
| 31 | Settings / Measurement Details window background | `backgroundPanel` | window background | panel | open |
| 32 | Measurement Details footer | panel + divider (MeasurementDetailView.swift:43, 52) | none | panel + separator | open |
| 33 | Sheet title bar (Save / Play File / Saved Measurements) | panel + divider (SheetTitle.swift:23) | native title only | panel + separator | open |
| **E** | **Swift disagrees with itself (iOS layouts)** | | | | |
| 34 | iPhone landscape "Taps:" and "Tap n/N" labels | default (Layouts.swift:584, 711); elsewhere secondary / `status.tapCount` | — | — | open |
| 35 | iPhone landscape Threshold row dimmed 0.4 for brace | Layouts.swift:622; no other layout or edition | always enabled | always enabled | open |
| 36 | Crosshair toggle, off state | `toolbar.inactive` (Controls.swift:55, 144), nil (Layouts.swift:394, 529, 842) | — | accent | open |
| **F** | **on the chart (#2 step 5a) — slipped through** | | | | |
| 37 | Mode-boundary label chip | mode colour on mode colour at 0.15 (SpectrumView+ChartContent.swift:78) | no chip | 0.16 on screen, 0.15 export | open |
| 38 | Peak Min value label on the chart | on `chart.readout.background` (ChartContent.swift:202) | no background | same as Swift | open |
| 39 | Chart title | default (SpectrumView.swift:533) | `chart.title` | `chart.title` | open |

Weight only, noted with item 9's area: Plate Cross/Long and Long/Cross values are bold in Swift and the web, regular
in Python.
