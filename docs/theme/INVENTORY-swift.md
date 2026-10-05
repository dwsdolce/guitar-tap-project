# Colour inventory — Swift (2026-10-04)

Production code under `/Users/dws/src/GuitarTap/GuitarTap` (all 89 Swift files and `Assets.xcassets`), as found for
the theme spec (`docs/THEME-SPEC.md`, §6). Paths are relative to that folder. Line numbers as of 2026-10-04 (Swift
`7855a3d`).

Types: **SYS** — a SwiftUI system / semantic colour (adapts to appearance; the OS release can change it); **FIXED** —
a literal sRGB value (`Color(sRGBHex:)`, `Color(red:…)`, `Color(white:)`, `.white`, `.black`, `.clear`); **PINNED** —
`Palette.*` (a fixed light/dark pair chosen by appearance); **DERIVED** — from a central table.

## Asset catalog

`Assets.xcassets/AccentColor.colorset/Contents.json` has no colour value, so `.accentColor` and every untinted
control take the user's system accent colour (`TapToneAnalysisView+Controls.swift:520-523`). No other colour sets.

## Chart (`SpectrumView`, `+ChartContent`, `TapToneAnalysisView+SpectrumViews`)

panel `Color.gray.opacity(0.05)` (SpectrumViews:178); plot border `Color.gray` (SpectrumView:1015); grid and axis
labels Swift Charts defaults (1049-1063); spectrum `.red` (ChartContent:47; `primaryCurveColor` SpectrumView:214);
plate phase curves `.blue` / `.orange` / `.purple` (SpectrumViews:111-117); comparison series
`comparisonSpectra[].color`; mode boundaries `mode.color` at 0.3, label at 0.15 (ChartContent:64-80); highlighted
peak `.red` (109-113); peak points `peakColor(for:)` — guitar `mode.color`, plate `.blue/.orange/.purple/.secondary`
(236-246); Peak Min `.green.opacity(0.7)` (SpectrumViews:154); threshold label background `Color.white.opacity(0.9)`
(ChartContent:204); peak labels — mode colour (`GuitarMode.color` / `userDefinedColor`) or plate roles, pitch
`.purple`, freq `.primary`, dB `.secondary`, background `.background.secondary`, shadow `.black.opacity(0.15)`
(PeakAnnotations.swift:210-571); legend `.regularMaterial` (SpectrumView:569); crosshair `Color.primary.opacity(0.5)`
(874-947), readout freq the curve colour, dB `.secondary`, background `.regularMaterial` (905-979); overlays and
help text `.secondary`.

## Peak rows (`Views/Shared/CombinedPeakModeRowView.swift`)

mode icon/label `mode.color` or `userDefinedColor` (74-300); row tint mode colour at 0.05 (176); star `.blue` /
`.secondary` (91); in-range `.green` / `.orange` (110); freq `.primary`; pitch `.purple` (133, 138); Q/BW
`.secondary`; magnitude `magnitudeColor()` — `.green` ≥−40, `.blue` ≥−60, `.orange` ≥−80, else `.red` (309-317);
menus `.primary`, `.accentColor`; Apply `.borderedProminent` (system accent).

## Results and material (`TapAnalysisResultsView.swift`)

Taps toggle `.orange` / `.accentColor` (163); Comparison badge `Color.purple.opacity(0.2)` (176); type badge
`Color.blue.opacity(0.2)` / `Color.orange.opacity(0.2)` (183); guitar row highlight `mode.color` (527-532); ring-out
and ratio quality `Palette` (568, 596); summary bar `Color.secondary.opacity(0.07)` (611); status dot `.green` /
`.gray` (618); material stars `.blue` / `.secondary`; phase badges `.blue` / `.orange` / `.purple`, inactive
`Color.secondary.opacity(0.2)`, text `.white` / `.primary` (1187-1208); step dots `.blue .orange .purple`
(1001-1072); wood quality `WoodQuality.color` (699-918); key-metric box `Color.secondary.opacity(0.1)`; prompts
`.orange`; Gore value `.accentColor`, box `Color.accentColor.opacity(0.08)` (971-979); phase panel
`materialPhaseColor` `.gray .blue .orange .purple .green` (SpectrumViews:296-343).

## Multi-tap / comparison

`TapToneAnalyzer.multiTapPalette = [.blue, .orange, .green, .purple, .teal]`
(`Models/TapToneAnalyzer+MeasurementManagement.swift:905`), `multiTapAvgColor = Color(red: 1.0, green: 0.85, blue:
0.0)` (907); local copies at `MultiTapComparisonResultsView.swift:39`, `ExportableSpectrumChart.swift:828`,
`TapToneAnalysisView+Export.swift:353, 430`, `PDFReportGenerator.swift:1415`.

## Toolbar, controls, status bar

toolbar `.tint(.blue)` (Controls 13×, Layouts 7×); crosshair `.blue` / `.gray`; Play File `.orange` / `.blue`; New
Tap system accent; Pause→Accept `.tint(.green)`; Cancel `Color.orange` / `Color.gray`; Threshold value `.blue`; Peak
Min value `.green`; panel `Color.secondary.opacity(0.1)`; iPhone side panel `secondary 0.05`, dimming
`Color.black.opacity(0.35)`, results `Color(.systemBackground)`; progress `.tint(Palette.blue)`. Status bar:
background `Color.secondary.opacity(0.1)`; comparison icon `.accentColor`; loaded-settings `.orange` at 0.12;
"Capture audio saved" `.accentColor` at 0.12; tap dot `.green` / `.gray.opacity(0.3)`; "Tap Detected!" `.green`;
counter, progress, Peak readout `Palette.blue`; paused / Complete `.orange`; engine dot `.green` / `.red`; detecting
dot `.green` / `.orange`; message `.primary` / `.orange`. Loading overlay `Color.black.opacity(0.3)`, `.white`,
`Color.secondary.opacity(0.8)`.

## Threshold slider (`Views/Shared/ThresholdSlider.swift`)

groove `Color(white: 0.92)` (77), border `Color.gray.opacity(0.6)` (80); gradient `(0.4,0.8,1.0) → (0,0.4,0.8) →
(0,0.12,0.31)` (89-93); clip `Color.red.opacity(0.85)` (107); ticks `(0.24,0.55,0.24)` at 0.7 (116); peak hold
`(1.0,0.78,0)` with `white 0.85` (124-125); handle `Color.red`, stroke `(0.5,0,0)` (135-136).

## Metrics, settings, measurements, sheets

metrics `.green .yellow .orange .red` by band (FFTAnalysisMetricsView.swift:163-188), `.primary`/`.secondary`, dot
`.green` / `.gray`; settings `.secondary` (~38×), `.primary`; measurements list check `.accentColor` / `.secondary`;
row icons `.blue` (comparison), `.green` (waveform); detail compared colours from stored RGBA (default blue); sheets
`NSColor.textBackgroundColor`, `NSColor.separatorColor`; help icons `.accentColor`.

## PNG export (`ExportableSpectrumChart.swift`)

`ImageRenderer` calls (797, 862, 913; `TapToneAnalysisView+Export.swift:67, 179, 265, 338`) set no colour scheme.
White background (731); spectrum `.red`; border `Color.gray`; grid/axes defaults; mode boundaries `mode.color`;
`peakColor` — `GuitarMode.fromDisplayName(label)?.color ?? userDefinedColor` or plate roles; pitch `.purple`; labels
`.primary`/`.secondary` on `Color.white.opacity(0.95)`; header `.secondary`; chips mode colour at 0.1; legend
`mode.color`; saved material phases `.blue .orange .purple`; multi-tap local palette.

## PDF export (`Views/Utilities/PDFReportGenerator.swift`)

`.environment(\.colorScheme, .light)` (275, 1092, 1110, 1134); white page; title/accent/Gore `Color(red: 0.15, green:
0.35, blue: 0.75)`, Gore box at 0.07; image backing `Color(white: 0.05)`; dividers `Color.gray.opacity(0.3)`, footer
0.2, header 0.1, result boxes 0.07, dimension boxes 0.06; peak mode labels **PDF-local `modeColor()`** — air
`(0,0.5,0.8)`, top `(0.2,0.65,0.2)`, back `(0.8,0.4,0)`, dipole `(0.6,0,0.8)`, ringMode `(0.8,0,0.4)`, others
`.secondary` (598-606) — or `userDefinedColor`; role cells and step dots `.blue .orange .purple`; analysis quality
`Palette` (light); wood quality `WoodQuality.color`; comparison swatches stored RGBA; multi-tap local palette.

## Central tables

- `Views/Utilities/Palette.swift:27-38` — the F57 six (as Python and the web), adaptive by appearance.
- `Models/GuitarMode.swift:322-338` `GuitarMode.hex`: air `#00C0E8`, top `#34C759`, back `#FF8D28`, dipole `#FF383C`,
  ringMode `#CB30E0`, upperModes `#8E8E93`, unknown `#808080`; `userDefinedColor = .teal` (383).
- `Models/MaterialProperties.swift:554-569` `WoodQuality.hex`: `#34C759 #00C7BE #007AFF #FF9500 #FF3B30`.
- PDF `modeColor(_:)` — above.
- Multi-tap palette and average — above.
- Plate/brace roles `.blue .orange .purple .secondary .gray .green` — repeated inline at ChartContent:240-246,
  PeakAnnotations:223-229, ExportableSpectrumChart:191-197, 534-537, 754-760, SpectrumViews:111-117, 337-343,
  TapAnalysisResultsView:1001-1032, 1187-1194, PDFReportGenerator:570-591, 621-645.
- `Views/Utilities/Extensions.swift` `decayQualityColor` (110-125), `tapToneRatioQualityColor` (158-172).
- Magnitude colours `CombinedPeakModeRowView.swift:309-318`; metrics `FFTAnalysisMetricsView.swift:163-188`.
- Stored comparison colour fallbacks `[0,0,1,1]` and average `[1,0.85,0,1]` (MeasurementManagement:1018,
  Export:224, 363, 374, PDF:1424, 1436).
