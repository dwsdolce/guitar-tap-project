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

Status: **agreed** (S1–S7 decided by the owner, 2026-10-20), except the text styles themselves (S4 needs an inventory
first). Where an edition does not yet follow a rule, the section says what it does today; #32
brings them in line.

## 1. Platform or app: who draws what

### 1.1 The model (agreed)

**The app tells the platform which scheme to use and lets the platform draw its own controls and chrome in it. The
app pins every colour it draws itself.**

So everything that carries meaning looks the same in every edition, and the native controls look native on each
platform. The owner put it this way: "There are settings that always come from the system — i.e. the widgets that
are tied to the system. The only colors we have to define are the app specific colors for light/dark."

| Drawn by the platform, in the app's scheme | Drawn by the app, pinned |
|---|---|
| standard controls: checkboxes, sliders, text fields, steppers, pickers, scroll bars | **buttons**, in every state (section 1.3) |
| | the chart: background, grid, axes, curves, crosshair, peak labels, mode bands |
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

**Deciding for a new element.** If it shows data, a state or a status, or it is a button, the app draws it, in a
role. Any other standard control is the platform's.

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

**Buttons are drawn by the app in every edition** (S1): fill, label and border in roles, and every state (section 5)
with the opacities of section 3. Three kinds:

- **plain:** an action with no particular meaning;
- **tinted:** a role names its colour (Cancel in `status.warning`, an accent action);
- **prominent:** the main action of a sheet (Save), filled with its role.

A toggle drawn as a button (Auto dB, Taps, Crosshair) is a tinted button with an on state.

The looks are those Python and the web draw today, measured from Swift's (owner, 2026-10-20); Swift adopts them:

- **plain:** label in `text.primary` on `background.control`, a `separator` border;
- **tinted:** label in the role on a 5 % fill of it; hover 15 %, pressed 22 %, on 28 %, on + hover 38 %;
- **prominent:** filled with the role, label in `text.onColor`; hover 85 %;
- **cannot act:** as section 5 (a prominent button shows as a plain one, dimmed).

The exact opacities become named opacities (section 3).

Today:

| | Swift | Python | Web |
|---|---|---|---|
| Plain button | platform `.bordered` (macOS: neutral bezel, label colour; iOS: label in the tint on a system fill) | platform `QPushButton` | app-drawn: `background.control` with a `separator` border; the border turns `accent.text` on hover |
| Tinted button | platform `.bordered` with `.tint(role)`, plus a 10 % hover wash in the tint | app-drawn: label in the role on a 5 % fill of it; hover 15 %, pressed 22 %, on 28 %, on + hover 38 %; disabled: 3 % fill, 40 % label | app-drawn: as Python's, but disabled dims the whole button to 0.45 |
| Prominent button | platform `.borderedProminent` | app-drawn: the role as the fill, `text.onColor` label; hover 85 %; disabled 30 % fill, 70 % label | app-drawn: `accent` fill, `text.onColor` label |
| Toggle as a button | platform toggle; macOS's on fill (about 11 % in Light) | 28 % on | 28 % on |

**Menus are the platform's, and their items carry no colour of their own** (S1a). An item's meaning is marked
semantically, never by a colour the app sets: destructive (Swift `role: .destructive`), disabled, separators and
headers. The web draws its menus itself; they follow the same rule — items in the normal item colour, the platform's
look as nearly as a browser allows (panel surface, the accent highlight on hover).

Today the web's row menu draws Delete in `status.error`, with a `status.error` fill on hover; Swift on iOS shows its
destructive items in iOS's red (an accepted platform difference, section 1.2); Swift on macOS and Python show no
colour.

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
   dividing line is `separator`, a surface is `background.window` or `background.panel`. Today Swift leaves some
   unset — text in places, `Divider()`, a default `GroupBox`, some window backgrounds (#32 M3).
3. **Colour is presentation, not model.** `GuitarMode` and `WoodQuality` carry no colour; their colours are roles.
4. **The table is shared data.** `tooling/parity/cases/theme.json` holds every role's light and dark value. Each
   edition's palette test checks its table against it.
5. **A source check enforces rules 1 and 2.**
   - Swift: `Tooling/check-colours.sh`, a build phase.
   - Python: `_colour_guard.py`, run at start-up in a development checkout.
   - Web: `tooling/check-colours.mjs`, in the `predev`, `prebuild` and `prepreview` scripts.

   Each refuses a colour written outside its palette module.
6. **Exports are drawn in the light scheme**, so they use the light values.

## 3. Opacity

**Every opacity the app applies is a named opacity** in `theme.json` (`opacities`), with a light and a dark value,
read through each palette module as a colour is; none is written in code (S3). The source check (section 2, rule 5)
is to refuse an opacity literal as it refuses a colour.

Today `theme.json` shares two: `peak.rowTint` (0.10 light, 0.20 dark) and `status.messageBackground` (0.12). These are
numbers in each edition's code, to become named opacities:

| What | Value today | Where |
|---|---|---|
| Dimmed: the control cannot act now | 0.45 | Swift `.disabledDimmed`; web `.btn:disabled`, `.field.is-disabled` |
| Not applicable: the control has no meaning here (Peak Min for a plate) | 0.4 | Swift `.opacity(… ? 1 : 0.4)`; Python opacity effects; web `.field.is-faded` and others |
| Tinted button fill / hover / pressed / on / on + hover | 5 % / 15 % / 22 % / 28 % / 38 % | Python, web |
| Hover wash on a platform button | 10 % | Swift `TintedButtonStyle` |
| Python's tinted button, disabled | 3 % fill, 40 % label | Python stylesheet |
| Python's prominent button: hover / disabled | 85 % / 30 % fill, 70 % label | Python stylesheet |
| Mode-boundary label chip | 0.15 | all three |

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

Known difference: the plate Cross/Long values are bold in Swift, regular in Python and semibold on the web (#32 F7).

## 5. Control states

**Each state has one mechanism, the same in every edition** (S5). "Cannot act now" and "does not apply" are each an
opacity on the whole group — label, control and value — with the values from section 3; in Python this is a helper,
as Swift's `.disabledDimmed`, not a stylesheet rule. A button's states follow section 1.3. **A prominent button that
cannot act shows as a plain button, dimmed**; it takes its fill when it can act (a sheet's Save before there is
anything to save). **A list row shows `background.subtle` while the pointer is over it**, in every edition.

Today:

| State | Meaning | Today |
|---|---|---|
| enabled | can be used | — |
| cannot act now | disabled for the moment (Taps while a sequence runs) | Swift: disabled + 0.45 on the whole group. Web: 0.45 on label and value. Python: disabled, but its labels keep their colour (the stylesheet has no `:disabled` rule for labels) |
| does not apply | has no meaning for this measurement (Peak Min for a plate) | Swift: 0.4 on the whole row. Python: an opacity effect of 0.4 on the group. Web: `.field.is-faded` 0.4 |
| hover | the pointer is over it | Swift: a 10 % wash on buttons, no row highlight. Python: its button hover, a `background.subtle` row. Web: its button hover, a bordered ⋯ |
| pressed | held down | Python: 22 %. Swift and the web: the platform's |
| on / selected | a toggle that is on; a selected row or peak | toggles: Swift macOS's fill (about 11 %); Python and the web 28 %. Selected peaks and rows: their own roles |
| focused | has keyboard focus | the platform's focus ring |
| highlighted | picked out on the chart or in a list (a hovered or chosen peak) | roles such as `chart.highlightedPeak` |
| inactive window | the window is not frontmost | the platform's (section 1.2) |

## 6. Icons and text symbols

**A symbol used as text is followed by U+FE0E** (the text form), so every platform draws it plain, in the text's
colour. **Where one edition draws an icon, every edition does** (S6). Each icon is the nearest equivalent of Swift's
SF Symbol.

Today:

- **Icons:**
  - Swift: SF Symbols.
  - Python: the Material Design Icons font via qtawesome (`mdi.…`).
  - Web: the same Material Design shapes as SVG paths (`tooling/parity/gen_web_icons.py`) where Python draws one;
    line icons in the Lucide style (`components/icons.tsx`) elsewhere. Both take the colour of the surrounding text
    (`currentColor`).

  The web's two icon sets are to become one.
- **Text symbols:** "⚠" appears in status messages and badges. Sometimes it is written plain and sometimes with U+FE0F
  (the emoji form), and Windows draws it as an orange emoji. The loaded-settings banner is an icon in Swift and
  Python but the symbol in the web's text (#32 M6, item 40).

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
| S1 | Buttons are drawn by the app in every edition | owner, 2026-10-20 |
| S1a | Menus are the platform's; their items carry no colour of their own, meaning marked semantically | owner, 2026-10-20 |
| S2 | A colour left unset is a platform colour | owner, 2026-10-20 |
| S3 | Every opacity is a named opacity in `theme.json` | owner, 2026-10-20 |
| S4 | Named text styles by purpose, defined after an inventory | owner, 2026-10-20 |
| S5 | One mechanism per state; "cannot act now" and "does not apply" as opacity on the whole group | owner, 2026-10-20 |
| S6 | Text symbols in the text form; an icon in every edition wherever one has it | owner, 2026-10-20 |
| S7 | This guide lives in `process/` | owner, 2026-10-20 |
