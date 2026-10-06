# Colour inventory — Python (2026-10-04)

Production code under `/Users/dws/src/guitar_tap/src/guitar_tap`, as found for the theme spec (`docs/THEME-SPEC.md`,
§6). Paths are relative to that folder; TTAV = `views/tap_tone_analysis_view.py`. Line numbers as of 2026-10-04
(Python `8837a28`).

## Overview

- 177 `setStyleSheet` calls (116 in TTAV; a few carry no colour). Elsewhere: `measurement_row_view` 12,
  `fft_canvas` 9, `peak_card_widget` 9, `measurement_detail_view` 9, `fft_analysis_metrics_view` 6,
  `material_dimensions_editor` 3, `loading_overlay` 3, `comparison_results_view` 2,
  `multi_tap_comparison_results_view` 2, `measurements_list_view` 2, one each in `plate_body_dimensions_editor`,
  `empty_state_view`, `threshold_slider`, `edit_measurement_view`. No `.qss` files; no `pg.setConfigOption`; no
  app-wide `setPalette`.
- QSS named colours resolve as SVG names: gray `#808080`, orange `#FFA500`, green `#008000`, white, red `#FF0000`.
- Only these follow the OS appearance: `palette(...)` roles (shadow, mid, text, base, alternateBase), the annotation
  card fill (`Window`), list context-menu icons (`WindowText`), the threshold slider's groove (`Mid`/`Base`), and six
  `ColorPair.on(widget)` sites (dark when the window colour's lightness < 128). Everything else is fixed — including
  the live chart's white background.

## Live chart (`views/fft_canvas.py`, `views/peak_annotations.py`, `views/shared/peaks_model.py`)

background `setBackground("w")` (256); title `#333333` (260, 973, 982); grid alpha 0.15, axes pyqtgraph default;
spectrum `mkPen("r")` (416); peak scatter `(30,100,200,200)` (421), per-peak `GuitarMode.color` (1679); selected
star pen `(180,0,0,220)` brush `(220,30,30,220)` (424-425); Peak Min `mkPen("g")`, label `(0,200,0)` (439-445);
mode bands `GuitarMode.color` (791-793); crosshair `(80,80,80,180)` (485); readout fill `(255,255,255,180)` (478),
freq `rgb(220,50,50)` or the snapped comparison colour (849, 898), dB `rgb(130,130,130)` (925); "Press Start"
`(120,120,120)` (506); ⓘ/⋯ `rgba(120,120,120,180)`, hover `rgba(60,60,60,220)` (521-538); legend
`rgba(240,240,240,210)` (1397, 1612); annotation card fill Qt `Window` (peak_annotations.py:107, 254), border and
leader the mode colour; annotation HTML pitch `rgb(120,60,180)`, freq `rgb(50,50,50)`, dB `rgb(110,110,110)`
(peaks_model.py:396-400).

## Peak rows and cards (`views/shared/peak_card_widget.py`; material rows in TTAV)

magnitude `_mag_color` ≥−40 `(40,160,40)`, ≥−60 `(40,100,210)`, ≥−80 `(200,120,30)`, else `(200,40,40)` (48-55);
pitch `rgb(130,60,200)` (188, 192); Q/BW `rgb(120,120,120)` (201); selected border `rgba(40,100,255,200)`, unselected
`rgba(180,180,180,80)` (227-229); background mode colour at 20 (232); star `rgb(30,120,255)` / `rgb(160,160,160)`
(241-243); in-range `rgb(40,160,40)` / `rgb(200,120,30)` (285). Material rows: star as above (TTAV:200, 256); text
`palette(shadow)`; fL/fC/fLC buttons `#1976D2` / `#E65100` / `#7B1FA2` with white text, inactive
`rgba(128,128,128,0.2)` (228-298).

## Results, material, instructions (TTAV)

type badges `rgba(0,100,255,0.15)` guitar, `rgba(255,140,0,0.20)` material, `rgba(160,32,240,0.20)` comparison
(1133, 3517-3525); mic label `gray`; panel icons `qta.icon(color="gray")`; multi-tap toggle active
`rgba(255,149,0,0.15/0.45)` text `rgb(200,100,0)` (4326-4333); summary box `palette(alternateBase)`; captions
`palette(shadow)`; ring-out and ratio quality `ColorPair.on`; footer dot `green` / `gray`; Auto dB icon `#27ae60`.
Material: section boxes `rgba(127,127,127,0.12)`, spec boxes `0.10`; quality labels `WoodQuality.color`; Gore box
`rgba(0,122,255,0.10)`, value `#007AFF` (1422-1434). Instructions and phase: phase markers `#1976D2 #E65100 #7B1FA2`;
phase states IDLE `gray`, L `#1976D2`, C `#E65100`, FLC `#7B1FA2`, COMPLETE `#388E3C` (3611-3757).

## Toolbar, status bar (TTAV)

toolbar buttons `rgba(0,122,255,0.12)` / border `0.35` / text `rgb(0,100,220)`, hover/pressed/checked/disabled
variants (867-887); play-file playing `rgba(255,149,0,0.15/0.45)` / `rgb(200,100,0)` (3191-3195); update banner
`rgba(10,132,255,0.12/0.45)`; accept `green`; cancel `orange` / `gray`. Status bar: progress track `palette(mid)`,
chunk `palette.BLUE.on`; peak label, tap count, step label `_system_blue` (= `palette.BLUE.on`); gray texts; idle dot
`rgba(128,128,128,77)`; tap detected `green`; frozen `orange`; detection dot `orange` / `green`; warning chip
`rgba(255,165,0,31)` with `orange`; saved chip `rgba(0,122,255,31)` with `rgb(0,122,255)`.

## Settings, dialogs, other

density/editor titles `palette(mid)`; units `palette(shadow)`; hints `gray`; threshold slider groove
`palette(mid)`/`palette(base)`, handle `red` border `#800` hover `#f44`, gradient `(102,204,255)→(0,102,204)→(0,30,80)`,
clip `(220,40,40,220)`, ticks `(60,140,60,180)`, peak hold `(255,255,255,220)`/`(255,200,0,240)`; loading overlay
scrim `(0,0,0,76)`, card `rgba(80,80,80,200)`, spinner white; metrics `gray` / `green` and `_processing_time_color` /
`_cpu_usage_color` `green yellow orange red`; help view `#444444 #555555 #0066CC #333 #ccc`; empty state `#888888`.

## Measurements list, detail, comparison tables

count/empty `#888888`; context icons `WindowText`; compare circle `#3478f6` / `#888888` / `#cccccc`; ⋯
`rgba(136,136,136,0/255)`; waveform `#28a028`; meta `#888888`; hover `QColor(0,0,0,10)`. Detail: `_mag_color`
`(40,160,40) (60,120,220) (210,130,40) (200,50,50)` (33-42); row background mode colour at 13; in-range `#28a028` /
`#d07020`; pitch `#8844cc`; captions `grey`; material `_MATERIAL_MODE_COLORS`, fallback `(150,150,150)`. Tables: dots
from the palettes; missing cells `QColor(150,150,150)`.

## PNG export (`views/exportable_spectrum_chart.py`, light)

white background (390, 814); axis pens and border `(180,180,180)`; spectrum `(210,50,50)` (431); series
`_COLOR_MAP`; mode boundaries `GuitarMode` at 80; chips mode colour at 38; material peaks L `(0,100,200)`, C
`(220,120,40)`, fLC `(130,60,200)`, fallback `(130,130,130)` (255-282); annotation card `(255,255,255,242)` border
`(0,0,0,38)`, pitch `(130,60,200)`, freq black, dB `(100,100,100)`; title `#333333`; legend `GUITAR_MODE_DISPLAY`.

## PDF export (reportlab, `views/tap_analysis_results_view.py`, light)

black text; ACCENT `Color(0.15,0.35,0.75)`; SECONDARY `(0.45,0.45,0.45)`; BG_GREY `(0.5,0.5,0.5,0.07)`; BG_LIGHT
`0.06`; BG_ACCENT `(0.15,0.35,0.75,0.07)`; DIVIDER `(0.5,0.5,0.5,0.3)`; footer rule `0.2`; image matte
`(0.05,0.05,0.05)`; table header `(0.5,0.5,0.5,0.1)`; meta `#737373`; quality `HexColor(WoodQuality.color)`; mode
colours `_mode_color` AIR `(0,0.5,0.8)`, TOP `(0.2,0.65,0.2)`, BACK `(0.8,0.4,0)`, DIPOLE `(0.6,0,0.8)`, RING
`(0.8,0,0.4)`, others SECONDARY (749-758); user-defined `USER_DEFINED_COLOR`; analysis quality `ColorPair.light`;
roles `#0077FF #FF9500 #AF52DE` (967-969); comparison report BLUE `#2659BF`, SECONDARY `0.4`, DARK `0.1`, header
`0.9`.

## Central tables

- `views/utilities/palette.py:29-34` `ColorPair(light, dark)`: the F57 six (as Swift and the web).
- `views/utilities/extensions.py`: `decay_quality_color` (46-60), `tap_tone_ratio_quality_color` (78-91).
- `models/guitar_mode.py:411-420` `GuitarMode.hex`: AIR `#00C0E8`, TOP `#34C759`, BACK `#FF8D28`, DIPOLE `#FF383C`,
  RING_MODE `#CB30E0`, UPPER_MODES `#8E8E93`, UNKNOWN `#808080`; `USER_DEFINED_COLOR (0,128,128)` (559).
- `models/material_properties.py:181-187` `WoodQuality.color`: `#34C759 #00C7BE #007AFF #FF9500 #FF3B30`.
- `views/shared/peaks_model.py:351-356` `_MATERIAL_MODE_COLORS`: Longitudinal `(50,100,220)`, Cross-grain
  `(220,130,0)`, Diagonal `(150,50,200)`, Peak `(150,150,150)`.
- Multi-tap / comparison palettes (blue, orange, green, purple, teal): `_MULTI_TAP_PALETTE`
  (`models/tap_tone_analyzer_measurement_management.py:899-905`) `(0,122,255) (255,149,0) (52,199,89) (175,82,222)
  (48,176,199)`; average `(255,217,0)` (908, again 968); local `_PALETTE` (1103-1109) the same;
  `FftCanvas._COMPARISON_PALETTE` (fft_canvas.py:239-245) the same; `multi_tap_comparison_results_view.py:30-36`
  `_PALETTE` — teal `(90,200,250)`, different; `_AVERAGED_COLOR (255,217,0)` (39).
- Material curve tuples fL `(0,122,255)`, fC `(255,149,0)`, fLC `(175,82,222)` repeated in
  `tap_tone_analyzer_spectrum_capture.py` (1591…1818), `tap_tone_analyzer_control.py` (1232…1351),
  `tap_tone_analyzer_measurement_management.py` (568-574), TTAV (4570-4578); reverse RGB→name maps TTAV 4787, 5023,
  5309.
- PNG `_COLOR_MAP` / `_LEG_COLOR_MAP` (412-418, 1015-1021): blue `(0,122,255)`, orange `(255,149,0)`, purple
  `(175,82,222)`, red `(255,59,48)`, green `(52,199,89)`; `GUITAR_MODE_DISPLAY` (780-786) `(0,183,235) (40,160,40)
  (220,120,40) (210,50,50) (130,60,200)`.

## Counts of repeated literals

`palette(shadow)` 30 (28 in TTAV); `color: gray` 21; `color: orange` 12; `color: green` 7; `palette(mid)` 10;
`#1976D2` 6; `#E65100` 5; `#7B1FA2` 5; `#888888` 7; star `rgb(30,120,255)` 3; `_system_blue` 4; `qta.icon(color="gray")`
9, `"orange"` 3.
