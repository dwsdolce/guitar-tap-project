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
    or dark. Following: `.preferredColorScheme(nil)`; forcing: `.preferredColorScheme(.light / .dark)`.
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
`.preferredColorScheme`, Qt's colour scheme, CSS `color-scheme`) **and lets the OS draw its own controls and chrome
in it; the app pins every colour it draws itself** (§5). Every colour that carries meaning is then identical across
the three editions; native controls look native on each platform. The rules below apply to the
app-drawn side.

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
5. **A source check enforces rules 1 and 2.** Each edition has a test that scans its production source and fails on
   a colour written outside the palette module: Swift `Color(red:…)`, `Color(white:)`, `Color(sRGBHex:)` and system
   colours (`.blue`, `.secondary`, `.accentColor`, …); Python hex strings, `rgb(…)` / `rgba(…)`, `QColor(…)`, named
   colours and `palette(…)` in stylesheets, pyqtgraph colour shorthands; the web hex and `rgb(…)` in `.ts` / `.tsx`
   and `App.css` (CSS uses only the `var(--…)` properties generated from the palette). Each test has a short,
   explicit allow list.

## 5. The role table

Most values are Apple's long-standing light and dark system values — the family F57 pinned for the analysis-quality
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
| separator | dividers, borders | `#D8DEE6` | `#222A33` |
| text.primary | body text | `#1A2330` | `#E7EBF0` |
| text.secondary | captions, units, hints | `#6B7785` | `#8A96A5` |
| accent | fills: toolbar tints, prominent buttons (white text on it) | `#007AFF` | `#0A84FF` |
| accent.text | accent-coloured text: links, checkmarks, the Gore value | `#007AFF` | `#409CFF` |
| scrim | modal backdrops | `#000000` at 30 % | `#000000` at 50 % |

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
One set for curves, markers, badges, step dots, the instruction panel and the PDF.

| role | light | dark |
|---|---|---|
| material.longitudinal (fL) | `#007AFF` | `#0A84FF` |
| material.cross (fC) | `#FF9500` | `#FF9F0A` |
| material.flc (fLC) | `#AF52DE` | `#BF5AF2` |
| material.unselected | `#6B7785` | `#8A96A5` |
| phase.notStarted | `#8E8E93` | `#8E8E93` |
| phase.complete | `#34C759` | `#30D158` |

### 5.5 Peak lists
| role | light | dark |
|---|---|---|
| peak.magnitude ≥ −40 dB | `#34C759` | `#30D158` |
| peak.magnitude ≥ −60 dB | `#007AFF` | `#0A84FF` |
| peak.magnitude ≥ −80 dB | `#FF9500` | `#FF9F0A` |
| peak.magnitude below −80 dB | `#FF3B30` | `#FF453A` |
| peak.pitch | `#AF52DE` | `#BF5AF2` |
| peak.selectedStar | `#007AFF` | `#0A84FF` |
| peak.unselectedStar | `#6B7785` | `#8A96A5` |
| peak.inRange | `#34C759` | `#30D158` |
| peak.outOfRange | `#FF9500` | `#FF9F0A` |
| peak.rowTint | the row's mode colour at 10 % | at 20 % |

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

### 5.8 Multi-tap and comparison
| role | light | dark |
|---|---|---|
| series.1 blue | `#007AFF` | `#0A84FF` |
| series.2 orange | `#E07800` | `#FF9F0A` |
| series.3 green | `#269342` | `#30D158` |
| series.4 purple | `#AF52DE` | `#BF5AF2` |
| series.5 cyan | `#0090B0` | `#64D2FF` |
| series.6 red | `#E0302A` | `#FF453A` |
| series.7 pink | `#D6177A` | `#FF6FB5` |
| series.8 brown | `#8B6A42` | `#C29A6B` |
| series.9 olive | `#7A8A00` | `#B8D430` |
| series.10 slate | `#5E6B7A` | `#A8B4C2` |
| series.average | `#EBC300` | `#FFD900` |

Ten series, one per tap at the most taps allowed (10), so no two taps or compared measurements share a colour while
there are ten or fewer; beyond ten (comparisons only) the slot wraps (`index % 10`). Slots 1–5 keep the order the
editions used. The average is drawn thicker than the series.

### 5.9 Status and messages
| role | light | dark |
|---|---|---|
| status.running / tapDetected / complete | `#34C759` | `#30D158` |
| status.stopped / idle | `#8E8E93` | `#8E8E93` |
| status.paused / frozen / warning / playingFile | `#FF9500` | `#FF9F0A` |
| status.info / saved / progress / tapCount / peakReadout | `#007AFF` | `#0A84FF` |
| status.error | `#FF3B30` | `#FF453A` |
| message background (warning, saved, loaded settings) | its status colour at 12 % | at 12 % |

### 5.10 Threshold slider and level meter
| role | light | dark |
|---|---|---|
| meter.groove | `#EBEBEB` | `#0A0D12` |
| meter.grooveBorder | `#8E8E93` at 60 % | `#8E8E93` at 45 % |
| meter.level (gradient, top to bottom) | `#66CCFF → #0066CC → #001E50` | `#66CCFF → #0066CC → #001E50` |
| meter.clip | `#FF3B30` at 85 % | `#FF453A` at 85 % |
| meter.ticks | `#3D8C3D` at 70 % | `#3D8C3D` at 70 % |
| meter.peakHold | `#FFD900` | `#FFD900` |
| meter.thresholdHandle | `#FF3B30`, border `#800000` | `#FF453A`, border `#800000` |

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

- **Swift:** the `appearance` setting and `.preferredColorScheme` at the root; `Palette` gains every role (§5),
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

## 9. Work breakdown (lock-step)

1. **Lock the table** — done: the decisions (§10).
2. **Shared data** — `tooling/parity/cases/theme.json` (every role, light and dark) and each edition's palette
   test against it.
3. **Palette modules** — every role in each edition's palette; colour off the model enums.
4. **The setting** — persistence, the Settings row, resolution, following the OS live; in Python, the Linux test
   of `setColorScheme` on Cinnamon, GNOME and KDE and the Fusion fallback where it is ignored (decision 9).
5. **Re-wire every colour site** to a role, area by area (chart, peak lists, results, material, toolbar, status
   bar, settings, measurements, exports), removing the duplicates of §6; the source check (§4 rule 5) passes at
   the end.
6. **Exports** forced light in all three.
7. **Run-review** — both schemes × three editions × {live spectrum, peak list, mode annotations, material results,
   multi-tap and comparison, status messages, settings, measurements list, PNG, PDF}.
8. **`mode-colors` (#17 Stage 2) resumes** — its case file is the mode slice of `theme.json`.

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
   (§9 step 4).
