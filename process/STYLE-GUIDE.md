# Style guide — how every edition looks

The standing rules for how Guitar Tap looks in every edition (Swift, which is canonical, then Python, the web and
Android). The guide covers:

- what the platform draws and what the app draws itself;
- colour, opacity and type;
- how controls look in each of their states;
- icons and text symbols;
- the mechanism each edition uses for each of these.

A change to how the app looks starts here. Work tracked as an Issue applies the guide; it does not redefine it.
How the UI's interaction translates to each platform (gestures, menus, layouts) is in
[`WEB-UI-GUIDELINES.md`](WEB-UI-GUIDELINES.md) and [`ANDROID-UI-GUIDELINES.md`](ANDROID-UI-GUIDELINES.md).

Status: **agreed** (S1–S7 and S1a, S1b decided by the owner, 2026-10-20; S1c, 2026-10-21), except the text styles themselves (S4 needs an inventory
first). Where an edition does not yet follow a rule, the section says what it does today.

## 1. Platform or app: who draws what

### 1.1 The model (agreed)

**The app tells the platform which scheme to use and lets the platform draw its own controls and chrome in it. The
app pins every colour it draws itself.**

So everything that carries meaning looks the same in every edition, and the native controls look native on each
platform. The owner put it this way: "There are settings that always come from the system — i.e. the widgets that
are tied to the system. The only colors we have to define are the app specific colors for light/dark."

| Drawn by the platform, in the app's scheme | Drawn by the app, pinned |
|---|---|
| standard controls: checkboxes, sliders, text fields, steppers, pickers, scroll bars | **buttons** in the content, in every state (section 1.3) |
| the buttons that close or confirm a sheet or dialog (S1b, section 1.3) | the chart: background, grid, axes, curves, crosshair, peak labels, mode bands |
| window frames, title bars, the chrome of sheets and popovers | peak lists and cards, results and material panels, badges |
| focus rings, text selection | status messages and dots, banners, the threshold meter |
| native list and table chrome | measurement rows, comparison and multi-tap tables |
| | the PNG and PDF exports |

Menus are the platform's, with items that carry no colour (S1a, section 1.3).

**The app's scheme, not the operating system's.** "Platform colour" here means the platform's colour *in the scheme
the app has chosen*. Each edition passes that scheme down:

- **Swift:** `NSApp.appearance` on macOS; each window's `overrideUserInterfaceStyle` on iOS.
- **Python:** Qt's `styleHints().setColorScheme`. On a Linux desktop that ignores the request, it uses the Fusion
  style with a palette built from the role table.
- **The web:** CSS `color-scheme` on the page.

**Why pin.** The owner: "we are a scientific application — color is just meant for discrimination between values —
the exact color is really irrelevant — we just want it consistent." Platform colours differ between platforms and
OS releases, and change with accessibility settings. So the app never uses one for anything it draws itself.

**Deciding for a new element.** If it shows data, a state or a status, or it is a button in the content, the app
draws it, in a role. Any other standard control is the platform's, and so is a button that closes or confirms a sheet
or dialog.

### 1.2 Accepted platform differences

These follow from the model; they are not divergences.

- **The inactive window.** The platform greys its own controls (checkboxes) when the window loses focus; the
  buttons the app draws stay as they are, in every edition.
- **A native control's own drawing.** For example, the web's unchecked checkbox is the browser's.
- **A destructive menu item on iOS.** iOS draws an item marked destructive in its own red; macOS and Qt draw it as an
  ordinary item.
- **Colour management.** Swift and Safari convert the palette's sRGB values to the display's colour space. Qt on
  macOS draws them unconverted, so Python's colours look slightly more saturated on a wide-gamut display.
- **Icon glyph sizes.** SF Symbols and the Material Design glyphs sit differently in the same box.

What must match is what shows with the window active: the roles, the layout, and which controls are enabled.

### 1.3 Buttons and menus

**Buttons in the content are drawn by the app in every edition** (S1): fill, label and border in roles, every state (section 5) at
the opacities of section 3, and one shape — corner radius 6, padding 3 × 8 points (a prominent button 4 × 10, an icon button 3 × 3), shared
in `theme.json` (`button`). Four kinds:

| Kind | For | Look |
|---|---|---|
| plain | an action with no particular meaning (Export Spectrum) | `text.primary` on `background.control`, a `separator` border; an accent wash at `button.plainHover` under the pointer |
| tinted | a role names its colour (Cancel in `status.warning`, an accent action) | the label in the role on the role at `button.tintFill`; `button.tintHover`, `button.tintPressed`, `button.tintOn`, `button.tintOnHover` |
| prominent | the main action in the content (New Tap); the web's confirming dialog button | filled with its role, the label in `text.onColor`; the fill at `button.prominentHover` under the pointer |
| icon | an icon with no frame (the chart's ⋯ and ⓘ, the row ⋯) | the icon in its role, no frame and no fill; under the pointer the plain button's wash (`button.plainHover`) on a patch behind it, padded 3 × 3 (`button.iconPadding`) |

A toggle drawn as a button (Auto dB, Taps, Crosshair) is a tinted button with an on state. A button that cannot act is
drawn whole at `control.dimmed`; a prominent one, as a plain button, dimmed (section 5). The rule is one function or
set of rules per edition, tested against `button-style.json` (`test/button-style`): Swift `AppButtonStyle`
(`AppButtonLook.of`), Python `palette.button_look` (the stylesheet's button rules are made from it), the web's
`.btn` rules in `App.css`.

**The buttons that close or confirm a sheet or dialog are the platform's** (S1b): Cancel, Save, Play, Done, and the
other buttons in a sheet's button row (Saved Measurements' Compare…, Import, Export All, Delete All). Each platform
draws a dialog's buttons its own way, and its users know that way from every other app:

- every button neutral except the default one — the one Return presses — which is marked (on macOS, filled with the
  accent; grey while it cannot act); a dialog with no default action has none, so all its buttons are neutral;
- Return presses the default button and Esc presses Cancel;
- the same place in every dialog (on macOS, bottom right, Cancel before the confirming button; on iOS, the sheet's
  navigation bar);
- the system's own adaptations: Increase Contrast, Button Shapes, the keyboard focus ring, each release's restyle.

The same in every edition: which buttons a dialog has, their order, which one is the default, and the keys. Only their
drawing is the platform's:

- **Swift:** toolbar placements (`.cancellationAction`, `.confirmationAction`, `.primaryAction`) — push buttons at the
  bottom of a macOS sheet, the navigation bar on iOS — or a button with no style and its
  `.keyboardShortcut(.defaultAction / .cancelAction)`.
- **Python:** Qt's native `QPushButton`, untagged, the confirming one `setDefault(True)`.
- **The web**, which has no native dialog button: app-drawn in the same pattern — the confirming button prominent
  (plain and dimmed while it cannot act), the others plain.

**A window closes with its own close; a sheet or panel with Done** (S1c). Where a view opens decides how it closes,
not which view it is:

- **a window** — Swift on macOS (the Quick Start Guide), Python's windows: the title bar's close; no button
  of the app's. macOS and GNOME keep action buttons out of an ordinary, non-modal window, and a second close control
  beside the title bar's is one too many.
- **a sheet or an in-page panel** — Swift on iOS and iPadOS, the web's panels (the Quick Start Guide, Metrics,
  Settings): no title bar to close it, so a Done in its head (Swift's `.cancellationAction`; the web's plain button),
  and Esc where there is a keyboard. Done, not Close: Apple's word for leaving a sheet.

So the same view can close two ways — the Quick Start Guide by the window's close in Swift on macOS and in Python, by
Done in Swift on iOS and on the web — and each is how every other view in that container closes on that platform.

Toolbar and title-bar buttons are the platform's too: the iPhone navigation bar's icons. They are window chrome
(section 1.1); only their colour roles are the app's.

**Menus are the platform's, and their items carry no colour of their own** (S1a). An item's meaning is marked
semantically, never by a colour the app sets: destructive (Swift `role: .destructive`), disabled, separators and
headers. The web draws its menus itself; they follow the same rule — items in the normal item colour, the platform's
look as nearly as a browser allows (panel surface, the accent highlight on hover).

Swift on iOS shows its destructive items in iOS's red (an accepted platform difference, section 1.2); Swift on macOS,
Python and the web show them as ordinary items. Each item has its icon in every edition (S6), in the item's own colour.

**An item or button ends in "…" when it needs more from the user before it is done** (S9) — a dialog that asks for
something (a save dialog, a file to open, a name), the share picker, a select mode — on macOS, Windows and Linux, as
each platform's guidelines say (Export Measurement…, Import…, Share All…, Delete → Selected…). A confirmation counts
too, so Delete All… and Duplicates… keep theirs (Microsoft's guidelines leave confirmations out; ours keep one rule).
An item that acts at once, or opens a window only to look at (View Details, Settings), has none. On iOS and iPadOS,
none, as in Apple's own menus (Share, Compare). The web follows the desktop rule. **Toolbar buttons are exempt**
(Save, Play File): they are labelled icons, often shown as the icon alone, and the menu bar's items that do the same
carry the "…" (Save Measurement…, Play Audio File…).

### 1.4 Lists

**A list scrolls only its items** (S8). The scrolling area holds the items — the measurements, the peaks, the
calibrations — and nothing else. Everything that is not an item sits fixed above or below it and never scrolls: a
total or a filter's count ("Showing 12 of 48 · Plate"), a notice or warning, the actions. The same in every edition.

A table's column headings are not items: they stay fixed while its rows scroll. A list's empty message ("No peaks
detected in visible range") is not an item either, and sits fixed above where the items would be.

**A scrolled page is not a list.** A report or results page — Measurement Details, a plate's or brace's results —
holds inputs, results and text rather than items to select, and scrolls as a whole.

## 2. Colour

1. **Every colour is a role.** A role names what the colour is for (the fL curve, secondary text, the Peak Min line)
   and has its own light value and its own dark value; two roles may share a value without being linked. Each
   edition holds the table once, in its palette module:
   - Swift: `Views/Utilities/Palette.swift`
   - Python: `views/utilities/palette.py`
   - Web: `src/presentation/palette.ts`; its CSS variables `--c-…` are generated from it.

   No colour value appears anywhere else.
2. **No platform colours** in anything the app draws: no SwiftUI system colours (`.secondary`, `.accentColor`,
   materials, `NSColor` / `UIColor` semantic colours), no Qt named colours or `palette(…)`, no CSS named colours.
   **A colour left unset is a platform colour too** (S2): text with no particular meaning is `text.primary`, a
   dividing line is `separator`, a surface is `background.window` or `background.panel`.
3. **Colour is presentation, not model.** `GuitarMode` and `WoodQuality` carry no colour; their colours are roles.
4. **The table is shared data.** `tooling/parity/cases/theme.json` holds every role's light and dark value. Each
   edition's palette test checks its table against it.
5. **A source check enforces rules 1 and 2.**
   - Swift: `Tooling/check-colours.sh`, a build phase.
   - Python: `_colour_guard.py`, run at start-up in a development checkout.
   - Web: `tooling/check-colours.mjs`, in the `predev`, `prebuild` and `prepreview` scripts.

   Each refuses a colour, or an opacity written as a number (0 and 1 excepted), outside its palette module; the
   chart-style module holds the chart's shared opacities (`chart-style.json`).
6. **Exports are drawn in the light scheme**, so they use the light values.

## 3. Opacity

**Every opacity the app applies is a named opacity** in `theme.json` (`opacities`), with a light and a dark value,
read through each palette module as a colour is; none is written in code (S3), and the source check (section 2,
rule 5) refuses one.

| Name | Value | For |
|---|---|---|
| `peak.rowTint` | 0.10 light, 0.20 dark | a peak row's tint over its mode colour |
| `status.messageBackground` | 0.12 | a status message's box |
| `control.dimmed` | 0.45 | a control that cannot act now, whole |
| `control.notApplicable` | 0.4 | a control that has no meaning here, whole |
| `button.tintFill` / `tintHover` / `tintPressed` / `tintOn` / `tintOnHover` | 0.05 / 0.15 / 0.22 / 0.28 / 0.38 | a tinted button's fill in its states |
| `button.prominentHover` | 0.85 | a prominent button's fill under the pointer |
| `button.plainHover` | 0.10 | the accent wash on a plain button under the pointer |
| `peak.rowHighlight` | 0.12 | a highlighted peak row's fill |
| `mode.chipFill` | 0.15 | a mode label's chip on the chart |
| `peak.pitchCents` | 0.8 | the cents in a peak label |
| `export.summaryChipFill` | 0.1 | an export's peak summary chip |
| `export.cardShadow` | 0.5 | an export card's shadow (the scrim) |
| `status.warningPulseLow` | 0.2 | the low point of a warning icon's pulse |

The chart's own opacities (mode boundary, Peak Min line, leader line) are in `chart-style.json`.

## 4. Type

**Text is drawn in named text styles by purpose** (S4) — caption, body, value, emphasis, heading, title — each with a
size relative to the body text, a weight, and whether it is italic; each edition maps them to its own fonts, and
the styles are shared data as the roles are. The styles themselves are defined after an inventory of each edition's
text.

Today each edition sizes and weights text in its own way:

- **Swift:** the platform's text styles (`.caption`, `.body`, `.headline`, …) and its own fonts such as
  `MaterialType.bodyBold`.
- **Python:** point sizes relative to the application font (a caption is the app size − 2), with explicit weights.
- **The web:** `rem` sizes, weights 500 and 600.

## 5. Control states

**Each state has one mechanism, the same in every edition** (S5). "Cannot act now" and "does not apply" are each an
opacity on the whole group — label, control and value — with the values from section 3; in Python this is a helper,
as Swift's `.disabledDimmed`, not a stylesheet rule. A button's states follow section 1.3. **A prominent button that
cannot act shows as a plain button, dimmed**; it takes its fill when it can act (the web's Save before there is anything
to save — in Swift and Python a dialog's default button is the platform's, section 1.3). **A list row shows `background.subtle` while the pointer is over it**, in every edition.

| State | Meaning | How |
|---|---|---|
| enabled | can be used | — |
| cannot act now | disabled for the moment (Taps while a sequence runs) | the whole group disabled and at `control.dimmed` — Swift `.disabledDimmed`, Python `disabled_dimmed`, the web's `.field.is-disabled` (`test/dimming`); a button, at `control.dimmed` (`test/button-style`) |
| does not apply | has no meaning for this measurement (Peak Min for a plate) | the whole group disabled and at `control.notApplicable` — Swift `.notApplicableDimmed`, Python `not_applicable_dimmed`, the web's `.field.is-faded` (`test/dimming`) |
| hover | the pointer is over it | a button: section 1.3. A list row: `background.subtle`. The pointer stays the arrow over every control, as each platform's guidelines have it (the pointing hand means a link); only a saved-measurement row shows the hand, as Swift's |
| pressed | held down | a tinted button: `button.tintPressed` |
| on / selected | a toggle that is on; a selected row or peak | a toggle: `button.tintOn`. Selected peaks and rows: their own roles |
| focused | has keyboard focus | the platform's focus ring |
| highlighted | picked out on the chart or in a list (a hovered or chosen peak) | roles such as `chart.highlightedPeak` |
| inactive window | the window is not frontmost | the platform's for its own controls (section 1.2) |

## 6. Icons and text symbols

**A symbol used as text is followed by U+FE0E** (the text form), so every platform draws it plain, in the text's
colour. **Where one edition draws an icon, every edition does** (S6). Each icon is the nearest equivalent of Swift's
SF Symbol.

- **Icons:**
  - Swift: SF Symbols.
  - Python and the web: one set — the Material Design icons (Python through qtawesome, `mdi.…`; the web the same
    shapes as SVG paths, `mdiPaths.ts`), and the app's own icons for the SF Symbols with no Material Design
    equivalent. Each takes its colour from its role or the surrounding text (`currentColor`).
  - The app's own icons are drawn once, as SVG in the hub's `tooling/parity/icons/` (24 × 24, stroked in
    `currentColor`), and generated into both editions by `tooling/parity/gen_web_icons.py`: the web's
    `customIcons.ts`, Python's `custom_icons.py` (drawn by `palette.icon` as `gt.<name>`). Today: `ring-mode`
    (`circle.dashed`), `plus-viewfinder` and `dot-viewfinder` (the crosshair toggle — the pair drawn alike).
    A new one is added there, never drawn in one edition's code.
- **Text symbols:** "⚠" is followed by U+FE0E wherever it is text — the status-line warnings, the import alert, the
  help text, and the shared cases — so Windows and the browsers draw it plain, in the text's
  colour, not as an orange emoji. Log lines are not user-facing and are left as they are.

## 7. How each edition applies a role

| | Swift | Python | Web |
|---|---|---|---|
| Colour | `Palette.color(role)` on the view | `palette.tag(widget, color=…, background=…, border=…)`, read by the application stylesheet; `palette.color(role)` when drawing | `var(--c-…)` in CSS; `palette.color(role)` on a canvas |
| Opacity | `Palette.color(role, opacity:)` | `palette.qss(role, opacity)` | the roles' `#RRGGBBAA` values; `color-mix` today for button tints |
| Icon | `Image(systemName:)` with a role | `palette.set_icon(widget, name, role)` | the SVG in `currentColor`, the surrounding text's role |
| Scheme | `Palette.apply` | `palette.apply` | `palette.apply` |
| Android | to be defined with the port | | |

## Decisions

| | Decision | |
|---|---|---|
| S1 | Buttons in the content are drawn by the app in every edition | owner, 2026-10-20 |
| S1a | Menus are the platform's; their items carry no colour of their own, meaning marked semantically | owner, 2026-10-20 |
| S1b | The buttons that close or confirm a sheet or dialog are the platform's; app-drawn in the same pattern on the web | owner, 2026-10-20 |
| S1c | A window closes with its own close (no app button); a sheet or an in-page panel with Done | owner, 2026-10-21 |
| S2 | A colour left unset is a platform colour | owner, 2026-10-20 |
| S3 | Every opacity is a named opacity in `theme.json` | owner, 2026-10-20 |
| S4 | Named text styles by purpose, defined after an inventory | owner, 2026-10-20 |
| S5 | One mechanism per state; "cannot act now" and "does not apply" as opacity on the whole group | owner, 2026-10-20 |
| S6 | Text symbols in the text form; an icon in every edition wherever one has it | owner, 2026-10-20 |
| S7 | This guide lives in `process/` | owner, 2026-10-20 |
| S8 | A list scrolls only its items; totals, notices, headings, empty messages and actions sit fixed above or below it; a scrolled page (a report, a results page) is not a list and scrolls as a whole | owner, 2026-10-23; 2026-10-24 |
| S9 | "…" on an item or button that needs more from the user before it is done (a dialog, the share picker, a select mode, a confirmation) on macOS, Windows, Linux and the web; none on iOS and iPadOS; toolbar buttons exempt | owner, 2026-10-26 |
