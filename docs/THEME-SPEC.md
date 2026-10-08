# Theme Spec — Light / Dark / System (Issue #2, all three editions)

Status: **APPROVED 2026-10-04** — every decision in §10 taken by the owner. Built on a full colour inventory of the
three editions (§7).
Lock-step: designed once here, built in Swift, Python and the web together, shipped together.

Why now: every colour difference the #17 slug sweep meets (mode colours, wood quality, the multi-tap palette, the
analysis-quality colours of F57) comes back to the same cause — the three editions draw on different backgrounds
and pick colours three different ways. The owner (2026-10-04): "Once color schemes are available they will both
respond to the current color scheme and have the same numbers for the same scheme … go ahead and do #2 since it
keeps coming up everytime we hit a color difference." The `mode-colors` step of Stage 2 waits on this.

## 1. The owner's three questions

1. **Can the user choose the scheme, or does it only follow the system?** The user chooses, in Settings: follow
   the operating system (the default; it changes live when the OS does), **Light** or **Dark**. The follow option is
   called **System** (owner, 2026-10-04: "System - for follow the OS is just fine").
2. **Is every colour in all three editions inventoried and assigned to what changes with the scheme?** Yes — §7
   summarises the inventory and §5 assigns every colour to a **role**. Each role has a light value and a dark
   value (equal where the colour need not change); nothing is left to a platform's own colours. The inventory
   also found duplicate and diverging copies (§6), which this work removes.
3. **Which schemes?** **Light and Dark.** Researched for macOS, iOS / iPadOS, Windows 10 / 11, GNOME, KDE,
   Cinnamon, Qt and the browsers (`docs/theme/PLATFORM-SCHEMES.md`, with sources): no platform hands an app a third
   scheme — each reduces to light or dark (plus "unknown" / "no preference"). The differences are in how the user
   picks: macOS Auto and iOS Automatic switch on a schedule; Windows Custom splits a Windows mode from an app mode;
   GNOME offers Default / Dark; KDE derives it from the chosen colour scheme; Cinnamon offers Mixed / Dark / Light.
   High contrast is a separate accessibility setting everywhere and is not part of this spec.

## 2. The setting

- **Values:** `system` (default) · `light` · `dark` — "Appearance: System / Light / Dark", stored as `appearance` in
  each edition's settings store (Swift `TapDisplaySettings`, Python `TapDisplaySettings`, web `localStorage`
  settings).
- **Resolved scheme** = the OS's when `system`, otherwise the setting. Every colour below is chosen by the
  resolved scheme.
- **What the OS reports, per edition** (`docs/theme/PLATFORM-SCHEMES.md`):
  - Swift — the SwiftUI `colorScheme` (macOS `NSAppearance` aqua / darkAqua; iOS `userInterfaceStyle`), always light
    or dark. Following: `NSApp.appearance = nil` (iOS: each window's `overrideUserInterfaceStyle = .unspecified`);
    forcing: `NSApp.appearance` aqua / darkAqua (iOS: `.light` / `.dark`) — what Qt's `setColorScheme` does on macOS.
  - Python — `QStyleHints.colorScheme()` (Qt ≥ 6.5) and `colorSchemeChanged`; forcing: `setColorScheme` (Qt ≥ 6.8;
    the edition uses PySide6 6.11). On Windows Qt reads the *app* mode; on GNOME and Cinnamon it is often **Unknown**
    (their light modes report "no preference").
  - Web — `prefers-color-scheme` (`light` / `dark`; browsers already report no preference as `light`) and its change
    event; forcing: the app's own `data-theme` and the CSS `color-scheme`.
- **Unknown / no preference resolves to Light** in all three — as browsers do, and as GNOME's and Cinnamon's
  "default" / "mixed" modes intend.
- **Where:** Settings → Advanced → Display Settings, the first row — same label, order and default (System) in all
  three. Advanced is collapsed by default, so the Help text and the user manual name Appearance among the Advanced
  settings.
- **Exports are always light** (PNG and PDF), whatever the setting — print-friendly (§5.12).

## 3. Who defines which colours: the OS or the app

Each edition draws some things itself and has the operating system (or the browser) draw others:

| drawn by the OS / browser | drawn by the app |
|---|---|
| standard controls — buttons, checkboxes, sliders, text fields, steppers, pickers, menus, scroll bars | the chart — background, grid, axes, curves, crosshair, peak labels, mode bands |
| window frames, title bars, sheets' and popovers' own chrome | peak lists and cards, results and material panels, badges |
| focus rings, text selection, the system accent colour on controls | status bar messages and dots, banners, the threshold meter |
| the platform's own window and panel backgrounds, native list and table chrome | measurements list rows, comparison and multi-tap tables |
| | the PNG and PDF exports |

The owner (2026-10-04): "one of the questions is which colors are defined by the settings in the os (such as widget
colors) and which in the app" — and then the model: "There are settings the always come from the system - i.e. the
widgets that are tied to the system. The only colors we have to define are the app specific colors for light/dark -
everything we get from the OS resolves to Light/Dark (from either us taking unknown to be light or by the OS giving
us Light/Dark)." *Agreed model:* **the app tells the OS which scheme to use** (SwiftUI
`NSApp.appearance` / the window's interface style, Qt's colour scheme, CSS `color-scheme`) **and lets the OS draw its own controls and chrome
in it; the app pins every colour it draws itself** (§5). Every colour that carries meaning is then identical across
the three editions; native controls look native on each platform. The rules below apply to the
app-drawn side.

**Accepted platform differences** (the owner, 2026-10-07: "I wonder how much to focus on the inactive appearance. It
is getting pretty detailed."). These follow from the model above and are not divergences:

- **The inactive window.** macOS greys Swift's checkboxes and `.tint` buttons when the window loses focus; Qt and the
  browser grey their own checkboxes, but the tinted buttons Python and the web draw from the palette stay coloured.
- **The native controls' own drawing** — e.g. the web's unchecked checkbox is Safari's (white with an outline), not
  AppKit's or Qt's grey square.
- **A native toggle's on state.** Swift's Auto dB / Taps / Crosshair are native button toggles, whose on fill macOS
  draws (about 11 % in Light); Python and the web draw 28 %.
- **Export All.** Swift's is a menu — Share / AirDrop, or Save All to Disk; Python and the web have no share
  sheet, so theirs saves to a file, the second of those.
- **Colour management.** Swift and Safari convert the palette's sRGB values to the display's colour space; Qt
  on macOS draws them unconverted, so Python's colours look a little more saturated on a wide-gamut display.
- **Icon glyph sizes.** SF Symbols and the Material Design glyphs sit differently in the same box (the User Manual
  icon is smaller in Swift).

What is matched is what shows with the window active: the roles, the layout, and which controls are enabled — a
disabled row dims whole in all three (Swift's `.opacity(0.4)`).

## 4. Rules

1. **Every colour is a functional role in one table.** A role names what the colour is for (the fL curve, secondary
   text, the Peak Min line) and has its own light value and its own dark value; two roles may share a value without
   being linked. This is the standard approach — Apple's semantic colours, Material 3's system tokens and design-token
   systems all switch light/dark per role. The table (§5) is canonical; each edition holds it once, in its palette
   module: Swift `Views/Utilities/Palette.swift`, Python `views/utilities/palette.py`, web
   `src/presentation/palette.ts` (the web's CSS custom properties are generated from it, per scheme). No colour
   literal outside the palette module.
2. **No platform colours.** No SwiftUI system colours (`.blue`, `.secondary`, `.accentColor`, materials, `NSColor` /
   `UIColor` semantic colours), no Qt named colours or `palette(...)` roles, no CSS named colours — they change with
   the scheme, accessibility and OS release, or are single-valued. The owner's rule (2026-10-02, F57): "we are a
   scientific application — color is just meant for discrimination between values — the exact color is really
   irrelevant — we just want it consistent."
3. **Colour is presentation, not model.** `GuitarMode` and `WoodQuality` carry no colour; their colours are roles in
   the palette.
4. **The table is shared data.** `tooling/parity/cases/theme.json` holds every role's light and dark value; each
   edition's palette test checks its table against it — the Stage 2 pattern.
5. **A source check enforces rules 1 and 2.** Each edition scans its own source and refuses to go on when a colour
   is written outside the palette module, where its release check already refuses (no edition needs the hub): Swift
   `Tooling/check-colours.sh`, a build phase beside Check Release Readiness — the build fails; Python
   `_colour_guard.py`, run beside `_release_guard.py` — a development checkout refuses to start; the web
   `tooling/check-colours.mjs`, in the `predev` / `prebuild` / `prepreview` scripts — `npm run dev`, `build` and
   `preview` stop. It looks for Swift `Color(red:…)`, `Color(white:)`, `Color(sRGBHex:)` and system
   colours (`.blue`, `.secondary`, `.accentColor`, …); Python hex strings, `rgb(…)` / `rgba(…)`, `QColor(…)`, named
   colours and `palette(…)` in stylesheets, pyqtgraph colour shorthands; the web hex and `rgb(…)` in `.ts` / `.tsx`
   and the stylesheets (CSS uses only the `var(--…)` properties generated from the palette). Allowed: Swift's
   `Color.clear`, and comment lines.

## 5. The role table

`tooling/parity/cases/theme.json` holds exactly these roles under these names. Most values are Apple's long-standing light and dark system values — the family F57 pinned for the analysis-quality
colours. The rest were settled by eye under decision 3 (§10): text on a tinted peak row reads at about 3.5 : 1 or
better, and no two modes share a colour family.

### 5.1 Chrome the app draws (panels, text)
Only where the app draws its own surface (§3); the OS draws its controls and window chrome in the resolved scheme.

| role | used for | light | dark |
|---|---|---|---|
| background.window | window and page | `#F2F2F7` | `#0B0E13` |
| background.panel | panels, cards, sheets, status bar | `#FFFFFF` | `#141A22` |
| background.control | inputs, buttons, list rows | `#FFFFFF` | `#11161D` |
| background.subtle | summary and metric boxes | `#8E8E93` at 8 % | `#8E8E93` at 10 % |
| background.picker | macOS's control fill: a menu picker's (the Settings dropdowns) and a plain bordered button's (the results panel's Export buttons); Swift's native controls draw it themselves, Python and the web draw it | `#000000` at 8 % | `#FFFFFF` at 8 % |
| separator | dividers, borders | `#D8DEE6` | `#222A33` |
| divider.section | the line between a panel's sections (the plate / brace results) — chosen by eye, 2026-10-06 | `#1A2330` at 35 % | `#FFFFFF` at 35 % |
| divider.headerFooter | the line under a results panel's header and above its footer — brighter than divider.section, so header, body and footer read as three parts; chosen by eye, 2026-10-06 | `#1A2330` | `#E7EBF0` |
| text.primary | body text | `#1A2330` | `#E7EBF0` |
| text.secondary | captions, units, hints | `#6B7785` | `#8A96A5` |
| text.onColor | text on a filled colour (an active phase badge) | `#FFFFFF` | `#FFFFFF` |
| accent | fills: toolbar tints, prominent buttons (white text on it) | `#007AFF` | `#0A84FF` |
| accent.text | accent-coloured text: links, checkmarks, the Gore value | `#007AFF` | `#409CFF` |
| toolbar.inactive | a toolbar button's tint when it has nothing to act on (Cancel) | `#8E8E93` | `#8E8E93` |
| scrim | modal backdrops, shadows | `#000000` at 30 % | `#000000` at 50 % |
| overlay.card | the loading overlay's card (white text on it) | `#3A3A3C` at 80 % | `#3A3A3C` at 80 % |

### 5.2 Chart
| role | light | dark |
|---|---|---|
| chart.background | `#FFFFFF` | `#0E1116` |
| chart.grid | `#E3E8EE` | `#1C242E` |
| chart.border | `#C2CAD4` | `#2A3543` |
| chart.axis (labels, titles) | `#6B7785` | `#8A97A6` |
| chart.title | `#1A2330` | `#DFE4EA` |
| chart.spectrum (the live / frozen curve) | `#FF3B30` | `#FF453A` |
| chart.crosshair.line | `#5A646E` at 50 % | `#96A0AA` at 55 % |
| chart.crosshair.frequency | `#FF3B30` | `#FF453A` |
| chart.readout.background (crosshair box, peak labels) | `#FFFFFF` at 96 % | `#141921` at 92 % |
| chart.peakMin (line and label) | `#34C759` | `#30D158` |
| chart.highlightedPeak | `#FF3B30` | `#FF453A` |

### 5.3 Guitar modes (decision 2)
| role | light | dark |
|---|---|---|
| mode.air | `#00B0DC` | `#64D2FF` |
| mode.top | `#269342` | `#30D158` |
| mode.back | `#BB6D00` | `#FF9F0A` |
| mode.dipole | `#FF3B30` | `#FF453A` |
| mode.ring | `#AF52DE` | `#BF5AF2` |
| mode.upper | `#A2845E` | `#AC8E68` |
| mode.unknown | `#8E8E93` | `#8E8E93` |
| mode.userDefined (a freeform label) | `#5856D6` | `#7D7AFF` |

Unknown is grey — "no mode" — and is common; Upper, which is rare, takes brown. The user-defined label is indigo so
that it stays clearly apart from Air. Top, Back and Air are darker than Apple's light values so their names read on a
tinted peak row.

### 5.4 Plate and brace
One set for curves, markers, badges, phase markers, the instruction panel and the PDF.

| role | light | dark |
|---|---|---|
| material.longitudinal (fL) | `#007AFF` | `#0A84FF` |
| material.cross (fC) | `#FF9500` | `#FF9F0A` |
| material.flc (fLC) | `#AF52DE` | `#BF5AF2` |
| material.unselected | `#6B7785` | `#8A96A5` |
| material.phaseInactive (an inactive phase badge) | `#8E8E93` at 20 % | `#8E8E93` at 20 % |
| material.goreBox (the Gore thickness box) | `#007AFF` at 8 % | `#0A84FF` at 8 % |
| phase.notStarted | `#8E8E93` | `#8E8E93` |
| phase.complete | `#34C759` | `#30D158` |

### 5.5 Peak lists
| role | light | dark |
|---|---|---|
| peak.magnitude.strong (≥ −40 dB) | `#34C759` | `#30D158` |
| peak.magnitude.moderate (≥ −60 dB) | `#007AFF` | `#0A84FF` |
| peak.magnitude.weak (≥ −80 dB) | `#FF9500` | `#FF9F0A` |
| peak.magnitude.faint (below −80 dB) | `#FF3B30` | `#FF453A` |
| peak.pitch | `#AF52DE` | `#BF5AF2` |
| peak.selectedStar | `#007AFF` | `#0A84FF` |
| peak.unselectedStar | `#6B7785` | `#8A96A5` |
| peak.inRange | `#34C759` | `#30D158` |
| peak.outOfRange | `#FF9500` | `#FF9F0A` |
| peak.rowTint (an opacity) | the row's mode colour at 10 % | at 20 % |

### 5.6 Analysis quality (ring-out, tap ratio — decided in F57)
| role | light | dark |
|---|---|---|
| quality.gray | `#8E8E93` | `#8E8E93` |
| quality.orange | `#FF9500` | `#FF9F0A` |
| quality.yellow | `#FFCC00` | `#FFD60A` |
| quality.green | `#34C759` | `#30D158` |
| quality.blue | `#007AFF` | `#0A84FF` |
| quality.red | `#FF3B30` | `#FF453A` |

### 5.7 Wood quality
| role | light | dark |
|---|---|---|
| wood.excellent | `#34C759` | `#30D158` |
| wood.veryGood | `#00C7BE` | `#63E6E2` |
| wood.good | `#007AFF` | `#0A84FF` |
| wood.fair | `#FF9500` | `#FF9F0A` |
| wood.poor | `#FF3B30` | `#FF453A` |

### 5.7a Results header
| role | light | dark |
|---|---|---|
| badge.guitar (the measurement-type badge) | `#007AFF` at 20 % | `#0A84FF` at 20 % |
| badge.material | `#FF9500` at 20 % | `#FF9F0A` at 20 % |
| badge.comparison | `#AF52DE` at 20 % | `#BF5AF2` at 20 % |
| results.tapsActive (the Taps toggle while the per-tap comparison is shown; `accent` otherwise) | `#FF9500` | `#FF9F0A` |

### 5.8 Multi-tap and comparison
| role | light | dark |
|---|---|---|
| series.1 (blue) | `#007AFF` | `#0A84FF` |
| series.2 (orange) | `#E07800` | `#FF9F0A` |
| series.3 (green) | `#269342` | `#30D158` |
| series.4 (purple) | `#AF52DE` | `#BF5AF2` |
| series.5 (cyan) | `#0090B0` | `#64D2FF` |
| series.6 (red) | `#E0302A` | `#FF453A` |
| series.7 (pink) | `#D6177A` | `#FF6FB5` |
| series.8 (brown) | `#8B6A42` | `#C29A6B` |
| series.9 (olive) | `#7A8A00` | `#B8D430` |
| series.10 (slate) | `#5E6B7A` | `#A8B4C2` |
| series.average | `#EBC300` | `#FFD900` |

Ten series, one per tap at the most taps allowed (10), so no two taps or compared measurements share a colour while
there are ten or fewer; beyond ten (comparisons only) the slot wraps (`index % 10`). Slots 1–5 keep the order the
editions used. The average is drawn thicker than the series.

### 5.9 Status and messages
| role | light | dark |
|---|---|---|
| status.running, status.tapDetected, status.complete | `#34C759` | `#30D158` |
| status.stopped, status.idle | `#8E8E93` | `#8E8E93` |
| status.paused, status.frozen, status.warning, status.playingFile | `#FF9500` | `#FF9F0A` |
| status.info, status.saved, status.progress, status.tapCount, status.peakReadout | `#007AFF` | `#0A84FF` |
| status.error | `#FF3B30` | `#FF453A` |
| status.inactiveDot (the tap dot while waiting) | `#8E8E93` at 30 % | `#8E8E93` at 30 % |
| status.messageBackground (an opacity: warning, saved, loaded settings) | its status colour at 12 % | at 12 % |

### 5.10 Threshold slider and level meter
| role | light | dark |
|---|---|---|
| meter.groove | `#EBEBEB` | `#0A0D12` |
| meter.grooveBorder | `#8E8E93` at 60 % | `#8E8E93` at 45 % |
| meter.levelTop, meter.levelMiddle, meter.levelBottom (the gradient) | `#66CCFF`, `#0066CC`, `#001E50` | the same |
| meter.clip | `#FF3B30` at 85 % | `#FF453A` at 85 % |
| meter.ticks | `#3D8C3D` at 70 % | `#3D8C3D` at 70 % |
| meter.peakHold | `#FFC700` | `#FFC700` |
| meter.peakHoldBorder | `#FFFFFF` at 85 % | `#FFFFFF` at 85 % |
| meter.thresholdHandle | `#FF3B30` | `#FF453A` |
| meter.thresholdHandleBorder | `#800000` | `#800000` |

### 5.11 Metrics (processing time, CPU)
| role | light | dark |
|---|---|---|
| metric.good | `#34C759` | `#30D158` |
| metric.fair | `#FFCC00` | `#FFD60A` |
| metric.high | `#FF9500` | `#FF9F0A` |
| metric.overload | `#FF3B30` | `#FF453A` |

### 5.12 Exports (always light)
The PNG and PDF use the light value of every role, so an exported Air is the screen's Air in light. The PDF's own
constants are roles with one value: `pdf.accent` `#2659BF`, `pdf.text` `#1C1C1E`, `pdf.secondary` `#787880`,
`pdf.divider` `#D2D2D4`, `pdf.box` `#F2F2F4`, `pdf.pill` `#ECECEE`, `pdf.goreBox` `#F7F9FD`, `pdf.chartMatte`
`#0D0D0D`.

### 5.13 Saved comparison colours (decision 4)
A saved comparison stores each entry's colour as RGBA (`colorComponents`). On load, each entry is drawn in the
resolved scheme by its series slot (by order, §5.8); the stored colour is not used for drawing. `colorComponents` is
still written (the light value) so files stay compatible.

### 5.14 Chart style (not by scheme)
How the chart draws its lines and points does not change with the scheme, but it must be the same in every edition,
so it is pinned the same way as the colours: one table per edition (Swift `ChartStyle`, Python
`views/utilities/chart_style.py`, web `src/presentation/chartStyle.ts`), checked against
`tooling/parity/cases/chart-style.json`. Widths and dashes in points, opacities applied to the line's role, point
sizes as areas (pt²); every curve and point is antialiased.

| | screen | exported image |
|---|---|---|
| spectrum line | 1 | 2 |
| overlay (comparison, multi-tap, plate/brace phase) | 1.5 | 2 |
| grid line | 1, solid, one per axis tick, no minor lines | 1 |
| mode boundary | 1.5, dash [5, 5], at 30 % | 2, dash [8, 8], at 30 % |
| Peak Min | 1.5, dash [8, 3], at 70 % | — |
| crosshair | 1, dash [4, 3] | — |
| peak-label leader | 1.5, dash [4, 3], at 40 % | 2, dash [5, 4], at 50 % |
| peak-label border | 1.5 | — |
| peak dot / highlighted star (area) | 40 / 120 | 200 |
| magnitude tick spacing | chosen from the visible range | every 20 dB |

The axis ticks — the grid lines — are Swift's `AxisTickGenerator` in all three, checked against
`tooling/parity/cases/axis-ticks.json`: frequency ticks by the nice-number rule (8 at most), labelled "100 Hz" /
"1.2 kHz" on screen and "100" / "1.2k" in the exported image; magnitude ticks every 1, 2, 5, 10, 20 or 50 dB, the
smallest giving at most 8.

## 6. Divergences the inventory found (removed by this work)

- **Mode colours** — three tables per native edition: Swift `GuitarMode.hex`, a PDF-only `modeColor()` (different
  values; Upper and Unknown `.secondary`), and the PNG legend uses `GuitarMode.color`; Python `GuitarMode.hex`, a PDF
  `_mode_color` (different values) and a PNG `GUITAR_MODE_DISPLAY` (different again); the web `MODE_COLOR` (dark) is
  also used, unchanged, on its white PNG and PDF.
- **User-defined label:** Swift `.teal`; Python `(0,128,128)`; the web `#1a9a9a` on screen but `#3bb6a6` in its
  PDF.
- **Material roles:** two or three sets per edition (§5.4).
- **Magnitude colours:** Swift system colours; Python two functions with different values (peak card / detail
  view); the web one dark set.
- **Multi-tap palette:** Swift system colours, copied in five files; Python five copies, one with a different teal;
  the web two identical copies plus two copies of the average colour.
- **Web blue:** `--system-blue` follows the OS appearance while the web's background does not (in OS light mode a
  light blue is drawn on the dark page); `#0a84ff` and `#4ea1ff` are written as literals in places that should use
  the variable.
- **Web unknown-mode peaks** fall back to `#8a96a5` rather than `MODE_COLOR.unknown`.
- **Swift accent:** `AccentColor` has no value, so every untinted control takes the user's system accent colour.
- **Swift PNG export** does not force the light scheme (its PDF does).

## 7. Inventory summary (2026-10-04)

| | Swift | Python | Web |
|---|---|---|---|
| how the scheme is chosen today | SwiftUI follows the OS; the F57 `Palette` picks light/dark by appearance; everything else system or fixed | the live chart is always white; Qt `palette(...)` roles (~45 sites) and six `ColorPair` sites follow the window's lightness; everything else fixed, light-tuned | one dark CSS theme (`color-scheme: dark`); only `--system-blue` follows the OS; light/dark tables exist but the screen always takes dark and the exports light |
| colour sites | ~300 — system colours (`.secondary` alone ~150), `Color(…)` literals, `Palette`, central tables | 177 `setStyleSheet` calls (116 in `tap_tone_analysis_view.py`), pyqtgraph pens, `QColor`s, reportlab colours | 7 CSS variables (~170 uses) and ~150 literal colours in `App.css`; tables in `presentation/`; canvas and jsPDF colours |
| central tables | `Palette`, `GuitarMode.hex`, `WoodQuality.hex`, PDF `modeColor`, `multiTapPalette` (+5 copies) | `palette.py`, `GuitarMode.hex`, `WoodQuality.color`, `_MATERIAL_MODE_COLORS`, two `_mag_color`, PDF `_mode_color`, PNG `GUITAR_MODE_DISPLAY`, multi-tap palette (+4 copies) | `palette.ts`, `MODE_COLOR`, `magnitudeColor`, `WOOD_QUALITY_COLOR`, `LIGHT_CHART` / `DARK_CHART`, `COMPARISON_PALETTE` (+1 copy), material sets A and B, `PHASE_COLOR`, PDF RGB constants |

The full per-site inventories (file:line for every colour) are in `docs/theme/INVENTORY-swift.md`, `INVENTORY-python.md` and `INVENTORY-web.md`.

## 8. Per-edition implementation

- **Swift:** the `appearance` setting and `Palette.apply` (`NSApp.appearance`; on iOS each window's interface style); `Palette` gains every role (§5),
  each an adaptive colour with the pinned light/dark pair; every system colour, `Color(…)` literal and inline role
  set is replaced by a role; `AccentColor` gets the accent role's values; colour leaves `GuitarMode` / `WoodQuality`;
  PNG renders get `.environment(\.colorScheme, .light)`. Size: medium (~300 sites, mostly mechanical).
- **Python:** the setting and the OS-scheme follow; `palette.py` gains every role and a resolved-scheme lookup;
  a per-scheme stylesheet replaces the 177 inline `setStyleSheet` colour strings; pyqtgraph background, pens and
  text from roles; `ColorPair.on(widget)` gives way to the resolved scheme; exports take the light column. Size:
  large — the long pole.
- **Web:** the setting and the media-query follow; `palette.ts` holds every role, and the CSS custom properties are
  set per scheme from it (`:root[data-theme=…]`); `App.css` literals become variables; the chart takes
  `LIGHT_CHART` / `DARK_CHART` by the resolved scheme; `MODE_COLOR` and the other dark-only tables become role
  lookups; exports take the light column. Size: medium.

## 9. Implementation plan (lock-step)

Each step is done in Swift, then Python, then the web, and verified in all three before the next step starts; each
edition's step is one commit (code → hash → this doc). Steps 5a–5f are the area-by-area re-wiring. The steps are committed to `main`;
no release is cut from any edition until step 8 (the run-review) is signed off (owner, 2026-10-04), because from step 3 to the end of
step 5 the native widgets follow the scheme while the app's own colours do not yet.

| # | step | what it delivers | done when | status |
|---|---|---|---|---|
| 1 | Lock the table | the decisions (§10) | the owner approves the spec | **done** 2026-10-04 |
| 2 | Shared data and palette modules | `tooling/parity/cases/theme.json`: every role of §5 with its light and dark value (`#RRGGBB`, or `#RRGGBBAA` where the role has an opacity; the peak-row tint and message backgrounds as opacities; the meter gradient as a list). Each palette module holds every role; a palette test in each edition checks it against `theme.json`. `quality-colors.json` and the colour part of `analysis-quality.json` fold into it. | the three palette tests pass on `theme.json` | **done** 2026-10-04 (Swift a834b3c, Python 16d4430, web 841c07c) |
| 3 | The resolved scheme | the `appearance` setting (System / Light / Dark, default System) in each settings store; the resolved scheme (OS, or the setting; Unknown → Light) and its change notification; the row in Advanced → Display Settings; the OS asked to draw its widgets in it (Swift `NSApp.appearance` / the windows' interface style, Python `setColorScheme` with the Fusion fallback on Linux, the web `data-theme` and CSS `color-scheme`). Colour still comes from the old sites. | switching the setting, and the OS, switches the native widgets on macOS (Linux and Windows are checked in step 7, from the committed code) | **done** 2026-10-04 (Swift a102504, Python 2728f22, web ab7812c) |
| 4 | Colour off the model | `GuitarMode` and `WoodQuality` lose their colours; callers take `mode.*` / `wood.*` roles; the PDF and PNG mode tables of §6 removed | no colour on either enum; the suites pass | **done** 2026-10-04 (Swift 382cfeb, Python 450e1ce, web 329a10e) |
| 5a | Re-wire: chart | background, grid, axes, spectrum, crosshair, readouts, Peak Min, mode bands, peak labels and dots, material curves, comparison and multi-tap series (10 + average); the chart style and Swift's axis ticks (§5.14) | the chart follows the scheme live in all three | **done** 2026-10-04 (Swift d2649ed, Python e1aff31, web fc25da2); run-review passed |
| 5b | Re-wire: peak lists | rows and cards: mode colour, tint (10 % / 20 %), magnitude, pitch, stars, in-range | as above | **done** 2026-10-05 (Swift 5f4be71, Python 1bdc5ff, web 6e2f40e); run-review passed |
| 5c | Re-wire: results and material | analysis and wood quality, badges, phase and step colours, Gore, summary boxes | as above | **done** 2026-10-07 (Swift abecde5, Python a25c0b9, web be62a1b; its run-review fixes Swift f69964a, Python 7d91cb2, web 3dcc139); run-review passed |
| 5d | Re-wire: toolbar, status bar, meter | toolbar tints, buttons, status messages and dots, the threshold slider / level meter, metrics; Python's qtawesome icons (26 with no colour draw a fixed near-black, 8 a fixed gray — black on a dark menu today): plain icons `text.primary`, gray ones `text.secondary`, coloured ones their status roles, recreated on `scheme_changed` | as above | **done** 2026-10-07 (Swift abecde5, Python a25c0b9, web be62a1b; its run-review fixes Swift f69964a, Python 7d91cb2, web 3dcc139); run-review passed |
| 5e | Re-wire: settings, measurements, dialogs | the app-drawn panels and text (§5.1), measurement rows and detail, comparison tables, help, loading overlay | as above; the source check (§4 rule 5) added and passing | **done** 2026-10-07 (Swift abecde5, Python a25c0b9, web be62a1b; its run-review fixes Swift f69964a, Python 7d91cb2, web 3dcc139); run-review passed |
| 5f | Re-wire: exports | PNG and PDF from the light column of every role (Swift's PNG renders forced light); saved comparisons drawn by slot (§5.13); found in 5a's run-review: Python's PNG takes the chart's current dB range (Swift and the web the measurement's), the web's PNG draws a dot for every peak in range and counts 3 peaks (Swift and Python draw and count the shown peaks), and the web's PNG annotation cards are much smaller than Swift's and Python's | exports identical whatever the setting | **done** 2026-10-07 (Swift abecde5, Python a25c0b9, web be62a1b; its run-review fixes Swift f69964a, Python 7d91cb2, web 3dcc139); run-review passed |
| 6 | Help and manual | Help text and the user manual: Appearance among the Advanced settings; what System does | the owner reviews the text | **done** 2026-10-07 (Swift b47f0aa, Python 7c01f74, web 2da0e06): Appearance in the three Quick Start Guides and the manual (§8.4); the owner reviewed the text; with it the 1.0.3 release notes; the manual's screenshots → #26 |
| 7 | Export regression tests | every export checked in all three by tests that drive the real app as the owner does — import a fixture, export the PNG and the PDF from the main window and from Saved Measurements, catch the files, measure them against Swift's expected values — run on GitHub CI (§9b) | each edition's suite runs them, locally and on CI, and they pass; a deliberate change to an export, or a wrong argument on an export path, fails them | — |
| 8 | Run-review | both schemes × three editions × {live spectrum, peak list, mode annotations, material results, multi-tap and comparison, status messages, settings, measurements list, PNG, PDF}; Python on Windows and on Linux (Cinnamon, GNOME, KDE — including the Fusion fallback of decision 9), from the committed code | the owner signs off | — |
| 9 | `mode-colors` (#17 Stage 2) | the mode-colours tests run on `theme.json` (`modeRoles`) from step 4; the #17 entry closes | #17's plan row 7 done | **done** 2026-10-04 with step 4 (Swift 382cfeb, Python 450e1ce, web 329a10e): the three `mode-colors` tests run on `theme.json`'s `modeRoles`; #17's row 7 closed 2026-10-07 |

**How each edition follows a scheme change.** One mechanism in all three, closest to Swift's: a use site names a
role, never a value; the role is resolved to a value for the current scheme in one place (the palette module); and a
scheme change reaches every colour without code at the use site, except where the edition draws for itself, which
redraws from one change point.

- **Swift:** palette colours are dynamic colours (`NSColor` / `UIColor` providers, as `Palette` already does); a view
  writes `.foregroundStyle(Palette.textSecondary)`, and SwiftUI redraws by itself when the colour scheme changes.
- **Python:** `palette.tag(widget, color=…, background=…, tint=…, border=…, prominent=…, message=…)` names a
  widget's role as a Qt property; the palette sets one application stylesheet with a rule per role
  (`*[colorRole="text.secondary"] { color: … }`; a bordered-button or progress-bar tint — Swift's `.bordered` with
  `.tint(role)`; a filled button — `.borderedProminent`; a status message's box at `status.messageBackground`),
  regenerated for every scheme. `palette.set_icon(widget, name, role)` draws a qtawesome icon in a role and draws it
  again on every change of scheme. `palette.py` also
  owns the resolved scheme and one `QObject` with a `scheme_changed(scheme)` signal. It
  emits — explicitly — when the OS scheme changes (`QStyleHints.colorSchemeChanged`) while the setting is System, or
  when the setting changes, and only when the resolved scheme actually changes; Qt's own events are not used as the
  trigger (they report only the OS, often Unknown on GNOME and Cinnamon, and vary between native styles and Fusion).
  Connected to it: one slot that regenerates the application stylesheet from the palette — widgets carry their role
  as a property (e.g. `QLabel[role="text.secondary"]`) and their inline `setStyleSheet` keeps layout only — and one
  slot per custom-drawn item (the chart `FftCanvas`: background, axes, pens, brushes; the threshold slider's painted
  parts; annotation cards), each re-taking its roles from the palette and redrawing. The export chart does not
  connect (always light).
- **Web:** `palette.ts` owns the resolved scheme and one `subscribe(listener)`, fired on the `prefers-color-scheme`
  change event while the setting is System, or when the setting changes, and only on an actual change. It sets
  `data-theme` on the root, so CSS follows through the custom properties by itself; the canvas chart and anything
  else drawn in script subscribe, re-read their roles and redraw. A tinted button is `.btn.tint` with a `tint-*`
  class naming its role — Python's tint and Swift's `.tint(role)`: the role as text and a 5 % fill, no outline
  (measured from Swift's `.bordered` button; the 35 % border first used here was not Swift's — removed 2026-10-07).
  **Hover and on (the owner, 2026-10-07), the same in all three:** a tinted button's fill rises 10 points while a
  pointer is over it, on or off (5 → 15 %, on 28 → 38 %, Python pressed 22 %) (none on touch — the web gates it on `(hover: hover)`; Swift's `.tintedBordered` adds the wash
  behind the native button); a **two-state toggle** — Auto dB, Taps, Crosshair (iOS, touch web) — shows a
  stronger fill while on: Python's and the web's 28 % (`:checked` or `palette.set_on`; `.on`); Swift's is a native
  `Toggle` with `.toggleStyle(.button)`, whose on state macOS draws — about 11 % in Light (measured 2026-10-07), an
  accepted platform difference (owner, 2026-10-07; §3). A multi-state control (Annotations: All / Selected / None) has no on fill — its icon names the state.

### 9a. Run-review steps — step 5 (5c–5f)

Launch all three from the working tree: Swift (Xcode, macOS), Python (`.venv/bin/python -m guitar_tap`), the web
(`npm run build && npm run preview`). Do each step in Light and in Dark (Settings → Advanced → Appearance), in each
edition. "Tinted" means the role as text over a faint fill of it.

**Results and material (5c)**

1. ~~Guitar: take a tap. → The results panel, its headings and text read in both schemes; the ring-out and tap-ratio
   words in their quality colours; the Guitar badge a faint blue.~~ — *passed (owner, 2026-10-07, light and dark, in the #6 side-by-sides).*
2. ~~Taps 3, complete, press Taps. → While the per-tap table is up, Taps is orange with the on fill (28 %), blue with
   the plain 5 % fill otherwise; hovering lightens it a step either way; the table's dots in the series colours.~~ — *passed (owner, 2026-10-07, light and dark, in the #6 side-by-sides).*
3. ~~Plate, Measure Diagonal on: run the three phases. → Phase markers grey before, blue (L) / orange (C) / purple~~ — *passed (owner, 2026-10-07).*
   (FLC) while active, green when done; inactive phase badges faint grey; the Plate badge faint orange.
4. ~~The plate result. → The Gore Target Thickness box faint blue, its value in the accent, readable in Dark; the
   summary boxes faint grey; the quality words in the wood colours.~~ — *passed (owner, 2026-10-07, light and dark, in the #6 side-by-sides).*
5. ~~Brace: run. → As 3–4 for the one phase.~~ — *passed (owner, 2026-10-07).*

**Toolbar, status bar, meter (5d)**

6. ~~Look at the toolbar. → Every button blue text and icon on a faint (5 %) blue fill, no outline; Python's icons
   blue, none black. Hover with a pointer → a step lighter (15 %); on touch, no hover.~~ — *passed (owner, 2026-10-07, light and dark, in the #6 side-by-sides).*
7. ~~Turn Auto dB on (and Crosshair, on iOS and the touch web). → The on state a stronger fill (28 %; Swift's the~~ — *passed (owner, 2026-10-07).*
   native on state), a step lighter again on hover. Annotations cycles All / Selected / None with its icon only — no
   on fill.
   *Finding (owner, 2026-10-07): Swift's Auto dB on is lighter than Python's and the web's. Measured: Swift ≈ 11 %,
   Python and web 28 %. The record had said Swift showed 28 %; its on state is macOS's own. Decided (owner): keep
   it — the state reads in all three; the record corrected (§9 step 5 rule, §3).*
8. ~~Play File… a WAV. → Play File tinted orange while it plays, blue after.~~ — *passed (owner, 2026-10-07).*
9. ~~Before and during a tap. → New Tap filled blue with white text; Pause tinted blue; Cancel tinted orange when it~~ — *passed (owner, 2026-10-07).*
   can act, grey when not.
10. ~~A plate phase under review. → Accept tinted green; Redo orange.~~ — *passed (owner, 2026-10-07).*
11. ~~The status bar through a tap. → Its background faint grey; the tap dot faint grey while waiting, green on a tap;
    "Tap Detected!" green; the progress bar and "Tap n/N" blue; the peak readout blue; the message in the text colour
    while detecting, orange otherwise; "Complete" orange while frozen. The web's bar no longer has a coloured left edge (web-only; removed).~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): the web's bar was an inset card with an outline, its text larger, "Tap
    Detected!" grey and "Complete" bold with no "•" after it; Python's message dot stayed green on completion and
    its message kept the cooldown's orange after re-arming, its count read "1/3"; Python's and the web's Complete
    icon plain pause bars. Done (Swift f69964a, Python 7d91cb2, web 3dcc139), to Swift's fullStatusBar: the web's bar a flat strip to the
    window's edges (background.subtle over the panel), 11 px left / 10 px right, the dot and message colours from
    detection, Swift's spacing and padding; Python's dot and message recoloured on every detection-state change,
    "Tap 1/3"; the filled pause circle in both. Qt's unmanaged colour accepted (§3).*
12. ~~Load a measurement saved with other settings. → The loaded-settings notice orange on a faint orange box, its
    icon orange.~~ — *passed (owner, 2026-10-07).*
13. ~~Dump Capture Audio on; take a tap. → The saved notice blue on a faint blue box.~~ — *passed (owner, 2026-10-07).*
14. ~~Speak, then tap hard. → The meter's groove light grey (Light) or near-black (Dark), with a border; the blue
    gradient fill; green ticks; a yellow peak-hold dot with a white rim; the red handle; the right end red while
    clipping.~~ — *passed (owner, 2026-10-07).*
15. ~~Open Metrics. → The dot green while running, grey stopped; captions secondary; the processing values (Swift,
    Python) green, yellow, orange or red by load.~~ — *passed (owner, 2026-10-07).*
16. ~~Python, an update offered. → The banner a faint blue box with a blue icon.~~ — *passed (owner, 2026-10-07).*

**Settings, measurements, dialogs (5e)**

17. ~~Open Settings. → Captions, units and hints secondary; Python's button icons in the text colour, the Help rows'
    icons blue and chevrons secondary.~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): the three Settings sheets differed in layout, lines, colours and icons; the web
    was most compact but lacked icons, Delete All Calibrations and Swift's wording. Decided from a mock-up (owner):
    Swift's structure at the web's density — each section an icon and a bold title (text.primary, not blue), its
    rows in a grey box with **no lines between rows**, a note under the box; each group inside Measurement Type
    (Mode Frequency Ranges; Sample Dimensions; Gore Body Dimensions; Plate Vibrational Stiffness; Brace Dimensions)
    its own titled box, no blank spacer rows; Swift's wording and no colons; sample rate once; icons on the action
    buttons; a fixed unit column; Cancel / Done at the bottom (top on a phone). Done (Swift f69964a, Python 7d91cb2, web 3dcc139): Swift — the
    in-section Divider rows became titled Sections, row separators hidden, the sample rate no longer repeated under
    the device; Python — the Qt lines and spacers removed, boxes and titled groups, Swift's icons (guitars / layers,
    cogs, outline info); web — the dialog rebuilt on SetSection / SetGroup / SetRow, the icons, Delete All
    Calibrations (with a confirm), Swift's note and labels, "min to max unit", the About description dropped as in
    Swift and Python. Then (owner): every setting one row, the control right-aligned — Appearance, the
    Frequency / Magnitude ranges and Peak Detection Minimum included (their fields had sat on the line below); the
    calibration buttons on one row; every action button tinted (accent), Save / Reset on one row; Python's unit
    column sized to its font ("mm" was clipped). Then (owner, side by side): Swift's native Form kept its row lines
    and padding (macOS ignores hidden row separators) — Swift's Settings now draws its own layout like the others
    (TapSettingsView+LayoutHelpers: settingsSection / settingsGroup / settingsRow / settingsToggleRow /
    settingsActionButtons / settingsLinkRow, 13 pt rows, 11 pt notes), on iOS too; one text size for every row;
    descriptions and notes secondary in Python; every toggle a right-aligned checkbox with its label and description
    on the left (a switch on iOS); Quick Start Guide / User Manual rows an accent icon, primary text and a secondary
    trailing icon (Swift's User Manual a button, not a Link); Advanced a boxed row with the chevron at the right;
    Swift's mode-range grid and wording, the calibration details and Delete All only with calibrations, in all
    three; Python's Check Now tinted. Then (owner, side by side): every Settings dropdown drawn as Swift's macOS menu
    picker — a filled box (new role `background.picker`), no border, 24 pt, radius 6, ⌃⌄ at the right; Swift's is the
    native picker, Python's a `MenuPicker` it paints, the web's a `MenuPicker` around the native select; the web's
    checkboxes in the accent; Python's Calculated Density semibold and the brace Height note under its row; Python's
    Peak Detection Minimum dims whole when off (plate / brace), as Swift's and the web's. The inactive-window look,
    native control drawing and icon glyph sizes accepted as platform differences (§3).*
18. ~~Open the Quick-Start Guide; switch Appearance with it open (Python: from the help page). → Headings, icons and
    text follow the scheme.~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): the three guides looked different — Python's headings large and its lines loose
    (Qt's rich text ignores heading sizes and paragraph borders), the web's headings blue, its body secondary and
    the three workflows as rows. Done (Swift f69964a, Python 7d91cb2, web 3dcc139): Swift's HelpView list in all three — each section a small
    secondary header (icon and title) with a line under it; the overview primary body text with plain bullets;
    each entry an 11 px semibold title over a 10 px secondary description, a line between entries; row icons in
    the accent; a line under every item, the last in a section too, so each section ends with one; a row's icons
    — several for a control that changes (Pause / Resume / Accept, Cancel / Redo, Annotations) — before its title,
    each in a 20 px slot 6 px apart (owner: the web had only one, Python's ran together). Python: styled
    paragraphs and `<hr>` lines, no in-page title (Swift's is the bar's). The web's
    Release Notes share the guide's styles and follow it. The name is "Quick Start Guide" everywhere (owner): the
    hyphen dropped from Swift's and Python's pushed-page titles, the manual (ch08) and the guide generators.
    Then (owner): the current section's header pinned at the top while it scrolls (Swift's list headers) —
    the web's sticky, Python's a strip over the view; the contents aligned row by row to Swift, keeping
    platform wording (Click / Tap, toolbar / menu bar): Swift's Menu Bar and User Manual rows moved after
    Metrics (they had sat among the toolbar buttons) and its "five menus" made four; the web's Crosshair after
    them; the web's titles Swift's (Re-analyze Peaks, Play Audio File, Step 3 — Tap New Tap, Zoom & Pan Help),
    "Chart Options" without "(⋯)"; the web's icons Swift's (Multi-Tap Comparison added; Analysis Results a
    document, Play Audio File a play circle, Compare a waveform, Zoom & Pan an info circle, Crosshair the
    viewfinder; none on Peak Labels, Toolbar and the Tap Controls rows); section icons guitars, 3-D layers and
    a closed book; the web's Zooming the Spectrum added; Zoom & Pan Help describes the ⓘ card, as Swift's;
    Swift's sentences restored (export between devices; Generic Guitar's broad ranges); Python's Analysis
    Results without the iPhone / iPad sentence.*
19. ~~Open Measurements. → Dates, counts and notes secondary; the waveform mark green; Python's ⋯ on hover; the row
    menu's icons readable in Dark.~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): the rows were separated three ways (Swift lines, Python a framed box, the web
    cards); the type marks differed (Python a 〜 character and the 📊 emoji, the web's waveform after the name and
    no comparison mark); Python's and the web's buttons had no icons, the web's sat at the top; Swift's title let
    the rows show through as they scrolled. Done (Swift f69964a, Python 7d91cb2, web 3dcc139), to Swift's list: plain rows with a line between,
    no frame or cards; Swift's marks beside the date — the waveform (has a spectrum) in status.complete, the chart
    document (a comparison) in the accent; a › chevron, ⋯ on hover (always on touch); Python's names on one line
    unless there is no room; the web's text at Swift's sizes (names 13 px bold, the rest 10 px); the buttons with
    Swift's icons and labels ("Import", not "Import…"), the web's at the foot (top on a phone); Swift's title on
    an opaque background. Export All stays one action in Python and the web (§3). Then (owner): Done follows
    what it does, as Swift's placements — a Done that commits beside Cancel (Settings) is the accent with
    white text, one that only closes (Saved Measurements, Metrics, Measurement Details, the Quick Start
    Guide) a plain button — one rule everywhere (owner); Swift's Metrics Done and its iOS guide's Done, which
    had been .confirmationAction, are now .cancellationAction; the web's Metrics Done plain. Every remaining
    accent button commits (Save, Play, Settings' Done). The web's rows 8 px between lines, as Swift's.*
20. ~~Compare: select two. → The selected circles blue, the others secondary; rows that can't be compared dimmed.~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): the selection was drawn three ways — Python ● / ○ characters, the web ☑ / ☐
    with the selected row tinted and no mark on a row that can't be compared, its other buttons hidden and
    Compare (N) blue; Python and the web hid the › chevron. Done (Swift f69964a, Python 7d91cb2, web 3dcc139), to Swift's: an empty circle in
    the secondary colour or the accent check-circle on every row, a row that can't be compared dimmed with its
    circle, no row tint, the chevron kept; the web's Import / Export All / Delete All shown disabled while
    comparing, Compare (N) plain with its icon, Cancel where Done was.*
21. ~~View Details of a guitar and of a plate measurement. → Mode names in their mode colours, magnitudes by strength,
    pitch purple; the plate's L / C / FLC names in the material colours.~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): a plate's Details showed each peak with Swift's "?" icon and a grey name (Swift
    gave plate peaks the guitar mode "unknown"); Python drew a plain dot, the web no icon; and Python's and the
    web's Details drew their own rows, not the results card. Done (Swift `9bcf4f0`, Python `fb211e8`, web `98cbe52`): Details uses the results panel's
    peak card, read-only (no star, no mode menu), in all three; a plate / brace peak shows its role's **fL / fC /
    fLC badge** — the same badge as the results panel, now one component per edition (Swift `MaterialPhaseBadge`,
    Python `phase_badge`, web `MaterialPhaseBadge`) — with its full name in the material colour. One shared
    `view/material-peak-role` holds each role's name, badge text and colour. Direction icons (⟷ ↕ ⤢) were tried and
    dropped (owner): one symbol per role everywhere, not three ways to name a tap. The web's Details classifies
    guitar modes among the shown peaks, as Swift's and Python's.*
    *Finding (owner, 2026-10-07, the rest of the form): closing differed — Swift's macOS window had no button,
    Python a Close at the bottom, the web a blue Close at the top; Measurement Info was laid out three ways and
    the web's section titles were blue and bold, its modal title much larger. Decided (owner): a Done at the
    bottom right in all three (plain — the one rule; at the top on a phone), Swift's macOS window included; the
    rest Swift's GroupBox — a plain title over a grey rounded box, Measurement Info fitting its content with a
    small secondary "Label:" before each value (the name medium weight), the peaks (and a comparison's spectra)
    in their own box; Python's scroll frame removed; the web's modal titles at the native window titles' 13 px
    bold. Done (Swift f69964a, Python 7d91cb2, web 3dcc139).*
22. ~~Open Edit, Save and Play File, and the plate and brace dimensions in Settings. → Captions and units secondary;
    fields readable.~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): the Save and Play File sheets differed in all three — Swift's title large and
    centred, unlike its other sheets; Python's fields in grey group boxes; the web's name field on its label's
    line, its hints inside the boxes, Play File's buttons at the top, and a disabled Save / Play a faded blue.
    Done (Swift f69964a, Python 7d91cb2, web 3dcc139): Swift's sheets titled as Saved Measurements (one `sheetTitle` for all three: the
    headline at the left, a line under it); Swift's form in Python and the web — a bold title above each
    full-width field, the hint as a caption under it, a file row's name (secondary while none) with Browse…
    and Clear at the right; Cancel and Save / Play at the bottom right, Save / Play the accent while they can
    act and plain while they cannot.*
23. ~~Export a PDF. → The loading overlay: the scrim, a dark grey card, white text.~~ — *passed (owner, 2026-10-07).*
24. ~~Web: look over the whole page. → Window, panels, separators and dialogs all follow the scheme; nothing left
    dark in Light.~~ — *passed (owner, 2026-10-07).*

**Exports (5f)**

25. ~~Export a PNG in Dark and in Light. → The two are the same, drawn light: white chart, light colours.~~ — *passed (owner, 2026-10-07).*
26. ~~Web, Annotations = Selected: export a PNG. → Dots only for the shown peaks; "Detected Peaks: N" counts the same
    peaks; the cards as Swift's (larger text, centred, a shadow, no border).~~ — *passed (owner, 2026-10-07).*
27. ~~Export a PDF in Dark and in Light — guitar, plate, comparison, multi-tap. → Each pair the same, drawn light.~~ — *passed (owner, 2026-10-07).*
    *Finding (owner, 2026-10-07): Python's and the web's PDFs had a much thicker dark frame round the chart than
    Swift's. Cause: step 30 gave their chart images Swift's transparent 16 pt margin, but their PDF code still
    inset the image inside the matte (written when the image was opaque, to imitate that margin), so the frame
    was doubled. Done (Swift f69964a, Python 7d91cb2, web 3dcc139): the image fills the matte at the content width, as Swift's — the margin
    alone is the frame.*
28. ~~Save a comparison; switch Appearance; load it. → Curves and table dots in the series colours by order, for the
    current scheme.~~ — *passed (owner, 2026-10-07).*
29. ~~View Details of that comparison. → The same colours by order.~~ — *passed (owner, 2026-10-07).*
30. ~~Export a PNG of the same measurement in all three. → Each matches Swift's:
    - the dB axis labelled 0 and −100 at its ends (Python's live chart too);
    - the axis titles "Frequency (Hz)" and "FFT Magnitude (dB)" — on Swift's live chart too, where they had
      gone missing since F55 clipped the plot;
    - the header "Type: … • Platform: … • GuitarTap v…", labels secondary and values in the text colour;
    - peak cards that fit their text, with a shadow and no border, the cents smaller and lighter;
    - summary chips with no border: frequency bold, mode name in its colour, dB grey;
    - the mode legend kept together on the left;
    - a clear margin around the image.~~ — *passed (owner, 2026-10-07; image and PDF exports from the main window — plate, comparison, generic — checked too).*

    ~~The web leaves out a frequency label that would run past the plot's edge, as Swift and Python do.~~
    — *passed (owner, 2026-10-07).* *(Found from this step's first run: the dB range was the same in Swift and
    Python; Python had only hidden the 0 and −100 labels.)*

    *Finding (owner, 2026-10-07): the web's PNG counted and summarised only the visible peaks inside the chart's
    range ("Detected Peaks: 3" against Swift's and Python's 6, which list 409 / 623 / 1180 Hz above a 75–350 Hz
    view). Cause: the web had no analyzer-owned `visiblePeaks`; App re-derived the annotation rule per chart
    marker, and those markers are range-limited. Done (Swift `9bcf4f0`, Python `fb211e8`, web `98cbe52`), in Swift's shape: the web analyzer owns
    `annotationVisibilityMode` (mirrored in from settings), `cycleAnnotationVisibility()`, `isUnknown` and
    `visiblePeaks`; the chart's badges and the live export read it; the saved-measurement export keeps its inline
    rule (`annotatedBy`), as Swift's does. A shared slug `state/visible-peaks` in all three, pinned by
    `test/annotation-state` (the web's tests now test the analyzer's rule, including a peak outside the range). Verified by the owner, 2026-10-07.*

    *Finding (owner, 2026-10-07, a saved comparison's PNG): the mode bands only in Swift's (both live charts
    have them; the web's live chart had none); Type "Generic Guitar" (Swift), missing (Python), "Comparison"
    (web); the list export titled "Comparison — name", the main view's "FFT Peaks — name"; the web's title and
    header larger, its date the browser's (10/7/2026, 9:22:32 PM), its legend dots; Python's and the web's
    chart titles higher, plots taller, axis titles small. Decided (owner): a comparison is always of guitars,
    so it has the bands; its Type is "Comparison" (it may hold different guitar types); one title from either
    export, the live chart's "FFT Peaks — name". Done (Swift f69964a, Python 7d91cb2, web 3dcc139): Swift `typeLabel`; Python bands on every
    guitar export, the Type, the titles, its multi-tap exports' invalid "classical" type replaced by Swift's;
    the web's bands (live and export), the app's date format; Python's and the web's images laid out on
    Swift's — the 800 pt chart frame at 169 pt, the title centred 21 pt in, the plot 219.5–930 pt, 16 pt
    medium axis titles, the header 22 / 11 pt, the legend's 10 pt marks (24 × 4 lines, 12 pt circles) at
    1030 pt. Python measured against Swift's PNG: every band within 0.5 pt but the x-axis title (4 pt high,
    pyqtgraph's own offset).*
    *Then (owner, re-export of the loaded comparison "Fred"): Python's main-view exports still had the Type
    "Generic Guitar", no Frequency Range in the PDF header (the live path passed no entries) and no date on
    the PDF's chart image. Done (Swift f69964a, Python 7d91cb2, web 3dcc139): fixed in that path — and (owner, the next re-export) in a
    third: Python's Export Spectrum has its own early branch for a saved comparison, which still titled it
    "Comparison — name" with the guitar type. Checked against the files (all three PNGs within 0.5 pt of Swift's but Python's
    x-axis title, 4 pt high; the PDFs alike): Swift's frequency labels started at their grid lines (Swift Charts'
    default), Python's and the web's were centred on them. Decided (owner): centred — Swift's x-axis marks
    `AxisMarks(preset: .aligned, …)` with the label anchored `.top` (the default preset overrode the anchor;
    `centered: true` would centre a label between two marks), in the export and the live chart; measured on
    a rendered export, each label within 1.5 px (2×) of its line (Swift f69964a, Python 7d91cb2, web 3dcc139). Apple documents neither the presets nor
    the default's override of the anchor (`AxisValueLabel.centered`: "center the label between two axis
    values"; `anchor`: "the anchor point on the bounding box … that attaches to the position"), so an OS
    update could move the labels unannounced. **Test plan (owner):** the export regression tests include
    one that renders each edition's export and asserts every frequency label's centre is within 2 px (2×)
    of its grid line — Swift's guards the undocumented preset; the main graph shares the mechanism. If it
    ever fails, the fallback is labels drawn at the chart proxy's x positions. **Test gap (owner):** the PDF test
    (`test/pdf-report`) compares only text, and nothing compares the PNG; and the main window and the Saved
    Measurements list export through separate code. A regression test must exercise both — guitar, plate /
    brace, multi-tap and saved comparison, PNG and PDF, from each — the main-window ones with the fixture
    loaded into the analyzer first. → §9 step 7, planned in §9b.*

### 9b. Step 7 — the export regression tests (plan)

Decided with the owner, 2026-10-08. Why: the run-review's export findings (§9a 27, 30) passed every suite — the PDF
test compares only text, nothing compared the PNG, and the main window and Saved Measurements export through separate
code. Several were a wrong argument on one export path, so the tests drive the app itself rather than calling the
export functions.

**What each test does** — the owner's four steps, in each edition:
1. import a fixture (`.guitartap`) through the app;
2. export — Export Spectrum (PNG) and Export PDF — from the main window (the fixture loaded) and from Saved
   Measurements (the row's menu);
3. catch the written files;
4. measure them against Swift's expected values.

**Cases:** guitar, plate, brace, multi-tap and a saved comparison — each from both paths, PNG and PDF. The fixtures
carry a fixed date, version and platform so the outputs compare.

**How each edition drives its app:**
- **Web — Playwright Test,** as in palmas: an `e2e/` suite and a `test:e2e` script beside the Vitest suite, the built
  PWA served locally, desktop Chrome first; downloads caught by Playwright.
- **Python — `pytest-qt`:** the real main window, its real buttons and menus clicked with `qtbot`; only the open and
  save file dialogs are replaced (they return a path). Everything between the click and the file is the app's code.
- **Swift — an XCUITest target:** launches the real app and drives it through accessibility. Two edges get test-only
  hooks behind a launch argument: Import takes the fixture without the file panel (or the library starts with it),
  and the save panel writes to a test folder. Everything between the click and the file is the app's code.

**One judge, three drivers** (owner, 2026-10-08): each edition's native test drives its app and writes the exported
files to a folder with a small manifest (case, path, format); one Python checker judges that folder. The checker's
source and Swift's expected values live in the hub and are copied into each edition, as `theme.json` is — each
repo's tests run on their own copy without the hub, and the hub checks the copies are identical (a byte compare, not
a review of three implementations). Its dependencies stay small: Pillow for the PNG, one PDF library for the
rectangles. The web's Playwright spec and Python's `pytest-qt` call the checker directly; Swift runs it as the step
after `xcodebuild`, in a script and on CI. Python is on every GitHub runner.

**What is measured — the shared checker,** so all three are judged by the same rules, with Swift's values the
expected ones:
- **PNG layout** (points, from the 2× image): the header title, the chart title, the plot's edges, the x-axis title
  and the legend — Swift's: 36–56.5, 181.5–199, 219.5–930, 960–974.5, 1026.5–1033.5 for a comparison; the header's
  Type, date format and rows; the legend's marks.
- **Label centring:** every frequency label's centre within 2 px (2×) of its grid line — guarding Swift's
  undocumented `AxisMarks(preset: .aligned)`; if it ever fails, the fallback is labels drawn at the chart proxy's
  x positions.
- **PDF:** the existing text comparison (`test/pdf-report`, Swift's lines, 1 pt), plus the chart image's and the
  matte's rectangles.
- **Tolerance per OS:** fonts differ by OS, so the layout checks carry a tolerance — or expected values per OS, as the
  per-OS peak baselines do (`tooling/parity/baselines/`).

**CI (a requirement):** GitHub Actions — the web on Linux; Python on Linux, macOS and Windows; Swift on macOS. Free on
GitHub's runners for public repos: `guitar_tap` and `GuitarTapWeb` are public; `GuitarTap` becomes public when its CI
is set up (owner). Linux runs Qt on its off-screen platform; macOS and Windows runners have a desktop.

**No microphone:** CI runners have no audio input; no current or planned test uses one (owner), so this is not a
limitation for the tests — the apps need only start and export without an input device.

**Progress:**
- **Web — driver done** (`52814db`): Playwright drives the built app — guitar, multi-tap, plate, brace and the saved
  comparison, each imported and exported as PNG and PDF from both the main window and Saved Measurements (11
  tests). Headless Chrome has no microphone, so the tests dismiss the Audio Engine Error as a user would, and hide
  the save picker so a save is a download the test catches. The tests found three web bugs, fixed in the same
  commit: an import's auto-load skipped App's share of the load (the measurement's type, settings, range and tap
  count), so a plate's or brace's Export PDF did nothing after an import — App now observes the analyzer's
  published load, as Swift's view does with `.onReceive`; the export double-click guard dropped a click in the
  first 0.7 s after the page loaded; and the download fallback released the file's URL at once. Not yet measured:
  the shared checker comes next.

**Size and order:** several sessions. The web's Playwright setup and the shared checker first (Playwright reaches
both export paths with no change to the app), then Python's `pytest-qt`, then Swift's UI target and its two hooks;
CI workflows as each edition's suite passes locally.

## 10. Decisions

1. ~~**The OS / app line (§3)**~~ — *decided (owner, 2026-10-04):* the system's widgets come from the system; the app
   defines only its own colours, for light and dark; everything the OS reports resolves to Light or Dark (Unknown
   taken as Light).
2. ~~**Mode colours (§5.3)**~~ — *decided (owner, 2026-10-04): "(a) is clearly what we want."* The mode roles take
   their light and dark values from the same family as the rest of the table (§5), replacing Swift's and Python's
   newest-OS values; Unknown takes the neutral grey (decision 3). Named colours were ruled out: Apple's system colours change
   with the scheme, accessibility and OS release; CSS / SVG names are fixed but single-valued and not Apple's; Qt
   palette roles differ by platform. Only explicit values are the same in all three editions.
3. ~~**The values to check (§5)**~~ — *decided (owner, 2026-10-04), by eye on a swatch page of both schemes:*
   Unknown takes the grey and Upper moves to brown; the user-defined label moves to indigo, apart from Air; Air,
   Top and Back are darker in light; the peak-row tint is 10 % light / 20 % dark; accent text gets its own role
   (`accent.text`, lighter in dark) so the button fill can keep white text; the light chrome as proposed; the dark
   surfaces stay as they are (a lighter set was tried and not preferred).
4. ~~**Saved comparison colours (§5.13)**~~ — *decided (owner, 2026-10-04):* redraw by series slot in the resolved
   scheme; "there is no need to keep the stored colour". With it, the series palette grows from 5 to 10 colours plus
   the average (§5.8), so ten taps no longer repeat colours; the light average is a yellower `#EBC300`, chosen by eye
   on the swatch page.
5. ~~**The setting's place**~~ — *decided (owner, 2026-10-04):* "Appearance: System / Light / Dark", default System,
   first row of Settings → Advanced → Display Settings, not a top-level section ("We do not need a top-level
   picker"); the Help text and the user manual mention it (§2).
6. ~~**Exports always light (§5.12)**~~ — *decided (owner, 2026-10-04): "export is always light."* PNG and PDF in
   all three editions use the light value of every role, whatever the setting.
7. ~~**A source check**~~ — *decided (owner, 2026-10-04): "Add it."* §4 rule 5.
8. ~~**Unknown → Light (§2)**~~ — *decided (owner, 2026-10-04)*, as part of the model in decision 1.
9. ~~**Qt's request on Linux**~~ — *decided (owner, 2026-10-04): (a).* Python requests the scheme with
   `setColorScheme`; on a Linux desktop where PySide6 6.11 ignores the request, Python switches to the Fusion style
   with a light or dark `QPalette` built from the role table, so its widgets follow the setting too (Qt-styled rather
   than native there). Tested on Linux Mint Cinnamon (the owner's VM), and on GNOME and KDE in VMs built for it
   (§9 step 8, from the committed code).
