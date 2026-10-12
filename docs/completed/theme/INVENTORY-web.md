# Colour inventory — web (2026-10-04)

Production code under `/Users/dws/src/GuitarTapWeb/src`, as found for the theme spec (`docs/completed/THEME-SPEC.md`, §6).
Paths are relative to `src/`. Line numbers are as of 2026-10-04 (web `8f31b91`).

## How light/dark works today

- **CSS:** `:root { color-scheme: dark; }` is fixed (`index.css:2`); every custom property has one dark value.
  Only `--system-blue` switches, under `@media (prefers-color-scheme: light)` (`index.css:21-25`).
- **Runtime tables:** where a light/dark table exists, a literal at the call site picks it — the screen always
  takes dark (`DARK_CHART`, `WOOD_QUALITY_COLOR.dark`, `PALETTE.*.dark`), the PNG and PDF always light
  (`LIGHT_CHART`, `WOOD_QUALITY_COLOR.light`, `PALETTE.*.light`); `drawBadge` tests `th === LIGHT_CHART`.
- **No light table:** `MODE_COLOR`, `magnitudeColor`, `USER_MODE_COLOR`, the comparison and multi-tap palettes,
  the material L/C/FLC colours, the threshold meter and every `App.css` literal.

## CSS custom properties (`index.css`)

| token | value | line | uses in App.css |
|---|---|---|---|
| `color-scheme` | `dark` | 2 | – |
| `--bg` | `#0b0e13` | 4 | `body` only (index.css:39) |
| `--panel` | `#141a22` | 5 | 5 |
| `--line` | `#222a33` | 6 | 49 |
| `--text` | `#e7ebf0` | 7 | 27 (+ `body`) |
| `--muted` | `#8a96a5` | 8 | 62 |
| `--accent` | `#4ea1ff` | 9 | 22 |
| `--system-blue` | `#0a84ff` dark / `#007aff` light (media query) | 18 / 23 | 3 |

## Central tables

- **`presentation/palette.ts:16` `PALETTE`** (light / dark): gray `#8E8E93`/`#8E8E93`, orange `#FF9500`/`#FF9F0A`,
  yellow `#FFCC00`/`#FFD60A`, green `#34C759`/`#30D158`, blue `#007AFF`/`#0A84FF`, red `#FF3B30`/`#FF453A`. Used by
  `dsp/analysisQuality.ts` (`decayQualityColor` 24-31, `tapToneRatioQualityColor` 45-51); screen `.dark`
  (`AnalysisResults.tsx:83,92`), PDF `.light` (`measurementImage.ts:285,288`).
- **`presentation/qualityColors.ts:55` `WOOD_QUALITY_COLOR`** (light / dark): Excellent `#34C759`/`#30D158`, Very
  Good `#00C7BE`/`#66D4CF`, Good `#007AFF`/`#0A84FF`, Fair `#FF9500`/`#FF9F0A`, Poor `#FF3B30`/`#FF453A`. Screen
  `.dark` (`MaterialResults.tsx:82`), PDF `.light` (`measurementImage.ts:30`).
- **`presentation/modeColors.ts`** (dark only): `MODE_COLOR` (20) air `#00C0E8`, top `#5fd07a`, back `#f0a03a`,
  dipole `#e0584a`, ring `#CB30E0`, upper `#9aa6b3`, unknown `#5a6573`; `USER_MODE_COLOR` (120) `#1a9a9a`;
  `magnitudeColor` (134-138) ≥−40 `#5fd07a`, ≥−60 `#4ea1ff`, ≥−80 `#f0a03a`, below `#e0584a`.
- **`presentation/spectrumRender.ts` `DARK_CHART` (63) / `LIGHT_CHART` (79):** bg `#0e1116`/`#ffffff`; grid
  `#1c242e`/`#e3e8ee`; border `#2a3543`/`#c2cad4`; axis `#8a97a6`/`#6b7785`; title `#dfe4ea`/`#1a2330`; curve
  `#e0584a`/`#e0584a`; badgeBg `rgba(20,25,33,0.92)`/`rgba(255,255,255,0.96)`; crosshairLine
  `rgba(150,160,170,0.55)`/`rgba(90,100,110,0.5)`; crosshairFreq `#dc6464`/`#cc3232`; crosshairDb
  `#8a97a6`/`#6b7785`; crosshairBg as badgeBg. Screen `DARK_CHART` (`SpectrumChart.tsx:185`, default 158); PNG
  `LIGHT_CHART` (`spectrumExport.ts:33`).
- **Comparison / multi-tap:** `COMPARISON_PALETTE` (`measurement/fromLive.ts:352`) `#0a84ff #ff9f0a #30d158 #bf5af2
  #40c8e0`; `MULTITAP_PALETTE` (`components/MultiTapComparisonResultsView.tsx:42`) the same; `MULTITAP_AVG_COLOR`
  `#ffd900` twice (`fromLive.ts:417`, `MultiTapComparisonResultsView.tsx:45`); stored as `colorComponents` via
  `hexToComponents` (`fromLive.ts:363`), read back by `colorComponentsToCss` (355); decode default `[0,0,1,1]`
  (`measurement/decode.ts:145`).
- **Material L/C/FLC:** set A `#4ea1ff #f0a03a #b07ad8` (chart overlays, markers, detail labels — `App.tsx:53-55`,
  `measurementImage.ts:94-96, 122-124`, `MeasurementDetail.tsx:22-25`); set B `#0a84ff #ff9f0a #bf5af2` (badges,
  steps, PDF roles — `measurementImage.ts:31-33`, `MaterialResults.tsx:107-109, 141-150`).
- **`components/MaterialInstructionPanel.tsx:11` `PHASE_COLOR`:** notStarted `#8e8e93`; L `#007aff`; C `#ff9500`;
  FLC `#af52de`; complete `#34c759`.
- **`presentation/pdfReport.ts:141-148`:** ACCENT `[38,89,191]`, SECONDARY `[120,120,128]`, PRIMARY `[28,28,30]`,
  DIVIDER `[210,210,212]`, BOX_BG `[242,242,244]`, PILL_BG `[236,236,238]`, GORE_BG `[247,249,253]`.
- **`USER_DEFINED_COLOR = '#3bb6a6'`** (`measurementImage.ts:168`) — PDF peak rows; differs from `USER_MODE_COLOR`.

## Uses by area (summary; values are fixed unless noted)

- **Chart:** canvas from the chart table; overlay curves from the palettes / set A / average; `.chart-wrap`
  `#0e1116` (App.css:1156); help/menu buttons `rgba(14,17,22,0.85)` (1260, 1284); legend `rgba(14,17,22,0.82)`
  (1315); popover/menu `#11161d`, shadow `rgba(0,0,0,0.5)` (1338-1373); menu hover text `#06121f` (1401).
- **Annotations:** mode boundaries `MODE_COLOR` at 0.5 (spectrumRender.ts:213-219); label pill `hexA(color,0.16)`
  (234-238); peak dot `m.color ?? '#8a96a5'` (307); highlighted star `#ff3b30` (303); Peak Min line
  `rgba(52,199,89,0.7)`, label bg `rgba(255,255,255,0.9)`, text `rgb(52,199,89)` (324-342); badge pitch
  `#9b51c2`/`#c389e8`, freq `#1a2330`/`#dfe4ea`, dB `#6b7785`/`#9aa6b3` by `th === LIGHT_CHART` (449-451).
- **Peak cards:** border/glyph/label `MODE_COLOR` or `USER_MODE_COLOR` (PeakCard.tsx:89-149); magnitude
  `magnitudeColor` (190); star `#4ea1ff` (App.css:1616); range ok/warn `#5fd07a`/`#f0a03a` (1643-1646); pitch
  `#c79cf0` (1685).
- **Results:** `PALETTE.*.dark`; metric dot `#6b727c`/`#3bbf63` (1882-1885); multi-tap dots and average.
- **Material:** `WOOD_QUALITY_COLOR.dark`; badges set B with `#fff` text; star `#0a84ff` (App.css:338); specmod box
  `rgba(127,127,127,0.1)` (474); `PHASE_COLOR`.
- **Toolbar / buttons:** `.btn` `#11161d` (207); `.btn-primary` accent with `#06121f`; `.btn-accept` `#2e6f3e`
  `#3a8a4e` `#eafff0` (229-231); `.btn-cancel` `#c0772a` `#f0a258` `#e08a32` (258-262); playing-file
  `rgba(255,149,0,0.15/0.45)` `#f0a258` (266-268); toggle on `color-mix(accent 22%, #11161d)`.
- **Status bar:** listening `#d8b13a`/`#e6c558`; capturing `#4ea1ff`/`#6fb6ff`; paused `#c0772a`/`#f0a258`;
  dots `#3fb950`, `#c0772a`, `#8a8a8e`; progress `var(--system-blue)` (1801-1830); `.error` `#ff8a7a`;
  load-warning `#6b5a1e #2a2410 #e6c558`; loaded-settings `#6b4a1e #2a1f10 #f0a258`; capture-audio-saved
  `#1e4a6b #10202a #8cc4f0` (1075-1116).
- **Settings:** overlay `rgba(0,0,0,0.55)`; modal `#0e1116`; inputs `#0a0d12`; textarea `#11161d`.
- **Threshold meter** (`ThresholdMeter.tsx`): groove `#0a0d12`, border `rgba(120,130,140,0.45)`; gradient
  `rgb(102,204,255)→rgb(0,102,204)→rgb(0,30,80)`; clip `rgba(220,40,40,0.85)`; ticks `rgba(61,140,61,0.7)`; peak hold
  `rgb(255,200,0)` / `rgba(255,255,255,0.86)`; handle `#ff3b3b` / `#800`.
- **Measurements list / detail:** row `#11161d`; type badges `rgba(78,161,255,0.2)`/`#9cc7ff`,
  `rgba(240,160,58,0.2)`/`#f0c089`, `#b07ad8`/`#fff`; waveform `#3bbf63`; menu `#161b22`, danger `#e0584a`; detail
  star `#0a84ff`, pitch `#b07ad8`, mode label `MODE_COLOR` / set A / accent, magnitude `magnitudeColor`.
- **PNG:** white page; `LIGHT_CHART`; chips `hexA(color,0.1)` with dark-tuned `MODE_COLOR` text; legend
  `MODE_COLOR`; set A overlays.
- **PDF:** the constants above; matte `(13,13,13)`; mode rows dark-tuned `MODE_COLOR` or `#3bb6a6`; roles set B;
  analysis and wood quality light; steps set B; comparison dots from stored RGBA.

## Duplicates and divergences

Material sets A and B; user-label teal `#1a9a9a` (screen) vs `#3bb6a6` (PDF); `COMPARISON_PALETTE` =
`MULTITAP_PALETTE`; `MULTITAP_AVG_COLOR` twice; `#0a84ff` literals (App.css:338, 716) not `var(--system-blue)`;
`#4ea1ff` literals (1616, 1738) not `var(--accent)`; unknown-mode markers fall back to `#8a96a5`.
