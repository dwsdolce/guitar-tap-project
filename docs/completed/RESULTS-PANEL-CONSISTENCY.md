# Results panel (Analysis Results) — cross-platform consistency

**Status:** ✅ CLOSED 2026-10-07 — done in all three editions — Swift `7408b50`, Python `38ce6c2`, web `342a174` (2026-10-07). Every
item below was checked side by side by the owner in light and dark, on macOS, iPhone and iPad, and the web on
desktop and a real iPhone.

**Scope:** presentation only — every number already agreed across the editions (the target-thickness check in
[MATERIAL-MULTITAP-DISCREPANCIES.md](MATERIAL-MULTITAP-DISCREPANCIES.md) validated the algorithms).

## The rules (owner's decisions)

1. **Size, layout and spacing: Python's** — the most compact and useful. Swift and the web take Python's sizes
   (10 pt body, 9 pt small, 14 pt bold values), its row and section spacing.
2. **Wording and structure: Swift's** — canonical except where it is wrong.
3. **Section lines:** `divider.section` between a panel's sections (ink / white at 35 %), `divider.headerFooter`
   under the header and above the footer (text.primary's colours) — both new palette roles, in all three.
4. **Icons:** Swift keeps SF Symbols; Python and the web use the same Material Design icons (Python names them,
   the web draws the same glyphs from paths generated off Python's icon font).
5. **Tinted buttons:** the role as text, a 5 % fill, no outline (measured from Swift's `.bordered`). Where a
   pointer exists, hover raises the fill 10 points (5 → 15 %; on 28 → 38 %). A **two-state toggle** — Auto dB,
   Taps, Crosshair (iOS, touch web) — shows a stronger fill while on: 28 % in Python and the web; Swift's is the
   native toggle's own on state (about 11 % in Light — measured 2026-10-07, accepted). A multi-state control (Annotations) has none; its
   icon names the state. Recorded in [THEME-SPEC.md](../THEME-SPEC.md).
6. **New Tap is filled blue** everywhere.
7. **Deselect and Reset to Auto never show for a plate or brace** — peak selection has no purpose there.
8. **Accepted platform differences:** macOS greys an inactive window's controls (Python and the web do not imitate
   it); macOS line breaking avoids a one-word last line, so Swift's italic note can wrap one word earlier.

## Evidence

The July captures of the same completed plate measurement, one per edition — where this started:

| platform | screenshot |
|---|---|
| Swift | [`images/results-panel-plate-swift-2026-07-16.png`](../images/results-panel-plate-swift-2026-07-16.png) |
| Python | [`images/results-panel-plate-python-2026-07-16.png`](../images/results-panel-plate-python-2026-07-16.png) |
| Web | [`images/results-panel-plate-web-2026-07-16.png`](../images/results-panel-plate-web-2026-07-16.png) |

The fL / thickness differences in them (66.9 vs 67.0 Hz; 2.81 vs 2.80 mm) are the first-tap gated-window defect in
MATERIAL-MULTITAP-DISCREPANCIES.md §3, not the panel.

## The original divergences (July 2026) — all resolved

| # | divergence | resolved by |
|---|---|---|
| 1 | Web listed plate peaks in phase order (L, C, FLC), not by frequency | the web sorts identified peaks by frequency once complete, keeping the phase slots while capturing — #17 F55 (web `b7de553`) |
| 2 | "Showing …" row three ways: Swift `20.0 Hz - 200.0 Hz`, Python `20 – 200 Hz`, the web none | one `displayRangeLabel` / `display_range_label` in Swift's form in all three — #17 F55 (Python `272b361`, web `b7de553`) |
| 3 | Python nested Gore inside Plate Properties | Gore its own section — Python's two-store dimensions (`5fc9aa5`) |
| 4 | The web's Gore value unboxed | boxed, as the others (confirmed side by side, 2026-10-06) |
| 5 | The web ran "Speed of Sound" into its values, not bold | heading on its own line, bold, as Swift (this work — Property rows, below) |
| 6 | The web coloured some section titles blue | plain text.primary titles in all three (this work — G7, below) |
| 7 | Python's spacing tighter than Swift's and the web's | rule 1: Python's spacing is the reference; Swift and the web changed (this work) |

## What changed in the code (Swift `7408b50`, Python `38ce6c2`, web `342a174`)

### Guitar peak list and summary

| item | change |
|---|---|
| G1 card size and spacing | Swift and the web take Python's (10 / 9 pt, tighter rows) |
| G2 mode name | Python shows the mode's full name ("Air (Helmholtz)"), left-aligned |
| G3 in-range mark | Swift: a plain ✓ on the Q line, not a circled ✓ under the icon |
| G4 pitch | Python and the web: Swift's "G2 (-10 ¢)" |
| G5 Q / BW line | Swift and the web: no wrapping (fixed-size pieces) |
| G6 BW value | Python shows the peak's stored bandwidth, not frequency ÷ Q |
| G7 header roles | "Analysis Results" text.primary, "Showing …" text.secondary, in all three |
| G8 Ring-Out / Tap Ratio values | text.primary in all three (Python cleared a stale secondary tag) |

### Header, toolbar and icons

| item | change |
|---|---|
| New Tap | Swift's macOS bar: `.borderedProminent`, filled blue |
| Unknown-mode and ⊗ icons | Python: outline, not filled |
| Refresh, ⊗, wand | Python and the web: Swift's grey rounded square (`background.subtle`) |
| Mode, pitch, export icons | Python and the web: one Material Design set (`mdiPaths.ts` generated by the hub's `tooling/parity/gen_web_icons.py`); Swift's weight and size |
| Export buttons | Python: Swift's icons and size |
| Web header sizes | Swift's sizes for the title, microphone line, "Showing …" and summary values |
| Web title line | "Guitar Tap 1.0.3 (N)" moved from its own line into the app control bar; hidden at phone size |
| Measurements button | Swift no longer shows the count ("Measurements (88)") — the list shows the total |

### Plate and brace panels

| item | change |
|---|---|
| Type | Swift: one `MaterialType` font set at Python's sizes; the web: Python's sizes |
| Sections | Swift: each section a bold title over a grey box (`materialSection`), no `GroupBox`, no "Dimensions" sub-heading, the peak list unboxed, panel top 8 pt; the web: the boxes added; Python: each section one group — line, 12 px, title, 4 px, box |
| fL / fC / fLC buttons | Python's size (36 × 32), square, in all three |
| Number fields | Swift: `ValidatedNumberField(fontSize:)` — 10 pt fields and stiffness picker; a fixed 20 px unit column in all three so the Mass field lines up |
| Labels | Swift's wording and colons ("Cross/Long Ratio:", "Length:"); headings without colons ("Radiation Ratio (R)"); GLC on one line; Specific Modulus title bold |
| Property rows | plate: bold heading, 10 pt L / C values, 2 pt between; brace: regular label, bold value; Specific Modulus box full width, Python's spacing |
| Overall Quality | bold label everywhere; no line above it; Swift's extra padding removed |
| Python sizes | ratio labels 10 pt; frequency / dB pair centred at its own height |
| Measurement Process | Swift: stray top line removed; text fills the box (asks for 240 pt only while the `.fixedSize` macOS panel sizes itself); Python: step dots 2 px down, as Swift; footer wording Swift's (plate "…from each tap…", brace single-tap) |
| Deselect / Reset to Auto | hidden for a plate or brace in all three. Python now holds Swift's rule in one `_refresh_selection_buttons` (guitar, a non-empty results list, no per-tap table; Deselect enabled while a peak is selected, Reset while the selection is not the automatic one), run wherever its inputs change; the saved-comparison check moved into Python's results list (`_refresh_results_peaks`), where Swift and the web keep it |
| Material instructions under the chart | Python hides them in a comparison — one `_refresh_material_instructions` with Swift's `!isGuitar && displayMode != .comparison` (they stayed up from a previous brace measurement) |

### Comparison and per-tap tables

| item | change |
|---|---|
| Type and spacing | Swift's: 10 px text, 4 px around the table, 6 px title row, 5 px rows, centred titles, lines between rows only, 8 px markers (the Averaged marker square-cornered); Python via one shared `apply_results_table_style` (24 px rows, no header bar or column lines), the web on the shared table class |
| Web pane | 440 px wide in a saved comparison on desktop, so names show in full (Swift's and Python's panels widen to fit) |
| Web microphone row | shown in a comparison |
| Summary in the per-tap view | the web shows Ring-Out / Tap Ratio, as Swift's `isGuitar && (displayMode != .comparison \|\| showingMultiTapComparison)` |
| Web footer | one group under the header/footer line: the summary in a grey box, then the export row |
| Taps button | Swift a native `Toggle`; Python a plain button flipping the analyzer's `showing_multi_tap_comparison`, its on fill through `palette.set_on`; the web `.on` |
| Swift Measurements list | compare-mode clicks register at once — the row's double-click gesture is off in compare mode (SwiftUI held every single click for the double-click interval) |

### Status bar

| item | change |
|---|---|
| Web in a comparison | Swift's comparison line — waveform icon, "Comparing N measurements" / "Tap comparison — N taps + averaged", the exit hint; no progress bar |
| Python in a comparison | Swift's waveform icon; the tap-state dot and the progress bar hidden |
| Web progress bar | no longer shown over a loaded plate measurement — `restoreMaterial` zeroes `currentTapCount` / `tapProgress` (new test in `tap-progress.test.ts`) |
| Web Threshold readout | whole decibels, truncated toward zero, as Swift's `Int(tapDetectionThreshold)` |

### Buttons (rule 5)

| edition | change |
|---|---|
| Swift | `TintedButtonStyle.swift`: `.tintedBordered` keeps the native `.bordered` button and adds the hover wash in its tint; Auto dB, Taps and Crosshair are native `Toggle(.button)`s |
| Python | the tinted-button stylesheet: 5 % fill, no border, hover 15 %, pressed 22 %, on 28 %, on + hover 38 %; `palette.set_on` for a toggle whose state lives in the model |
| Web | `.btn.tint`: 5 % fill, no outline; hover only under `(hover: hover)`; `.on` 28 %, on + hover 38 %; Annotations has no on fill |

### Palette and other fixes

- New roles `divider.section` and `divider.headerFooter` in `theme.json`; the three palettes regenerated.
- Web `newId()`: falls back to a v4 UUID from `crypto.getRandomValues` where `crypto.randomUUID` is missing (any
  plain-HTTP page, e.g. the preview on a phone); HTTPS and localhost unchanged.
- Fast test runs in all three: `Tooling/test-fast.sh` (Python, Swift) and `npm run test:fast` (web) skip the
  recording replays — the playback regression and, in Python and the web, the separate self-regression.

## Verification

- Suites (last full and fast runs): Swift 523 (full) / 511 (fast); Python 1259 (full) / 1237 (fast); web 1154 (full) / 1133 (fast); colour
  guards and parity map clean; iOS build succeeds.
- Owner side by side, light and dark: guitar, plate (top and lower), brace, comparison and per-tap views; Swift on
  iPhone and iPad; the web on a real iPhone; the toolbar and Taps hover and on states.
- Deselect / Reset through a saved comparison: hidden while it shows, back with the peak list after loading a
  single guitar measurement; after New Tap, Deselect is enabled as soon as a live peak shows — the same in all three.

## Not divergences

- Badge hues (L blue, C orange, FLC purple) — the same in all three.
- The fL / thickness differences in the July captures — the gated-window defect above.
