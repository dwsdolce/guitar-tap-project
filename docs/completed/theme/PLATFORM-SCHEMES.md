# Platform colour schemes — what the user can choose and what an app sees (researched 2026-10-04)

For the theme spec (`docs/completed/THEME-SPEC.md` §2). Every claim has a source; where documentation was silent the source is
the upstream code (Qt, KDE, GNOME, Cinnamon, xapp portal, master/dev as of 2026-10-04). *Unconfirmed* marks what no
source settled.

## Summary

| platform | user options (exact names) | scheduled switching | what an app sees | no preference | contrast |
|---|---|---|---|---|---|
| macOS | Light / Dark / **Auto** | Auto follows the Night Shift schedule | `NSAppearance` `aqua` / `darkAqua` (with Increase Contrast: `accessibilityHighContrastAqua` / `…DarkAqua`) | none — always one of the two | Increase contrast, separate (shows in the appearance name) |
| iOS / iPadOS | Light / Dark, plus **Automatic** | Sunset to Sunrise, or Custom Schedule | `userInterfaceStyle` `unspecified` / `light` / `dark` | `.unspecified` = "follow the system" (an app is handed light or dark — our reading) | Increase Contrast → `accessibilityContrast` |
| Windows 10 (1903+) / 11 | Light / Dark / **Custom** (Custom = a Windows mode and an app mode, each Light or Dark) | none built in (*unconfirmed* as a positive statement) | `UISettings` foreground colour (documented); registry `AppsUseLightTheme` — the app mode — is what Qt reads | none (boolean); Qt reports Unknown under a contrast theme | Contrast themes (Win 11: Aquatic, Desert, Dusk, Night sky) |
| GNOME 42+ | **Default / Dark** | none (*unconfirmed*) | portal `color-scheme` 0 / 1 / 2 — light mode is **0** | common (it is the default) | High Contrast; portal `contrast` |
| KDE Plasma | Global theme (Breeze / Breeze Dark / Breeze Twilight) or a colour scheme — no light/dark switch | Plasma 6.5+: by time of day | portal 1 or 2 from the window background's brightness | never 0 | separate setting *unconfirmed*; no `contrast` key from its portal |
| Linux Mint Cinnamon 5.8+ (Mint 21.2+) | Mode: **Mixed / Dark / Light**; Dark mode: **Let applications decide / Prefer dark mode / Prefer light mode** | none found | portal via xdg-desktop-portal-xapp: Mixed = 0, Dark = 1, Light = 2 | Mixed and "Let applications decide" = 0 | portal `contrast` from its high-contrast key |
| Qt 6 (PySide6) | follows the OS | — | `QStyleHints.colorScheme` Unknown / Light / Dark (6.5+), `colorSchemeChanged`; `setColorScheme` / `unsetColorScheme` (6.8+) | Unknown is frequent on GNOME and Cinnamon | `ContrastPreference` |
| Browsers | Chrome **Device / Light / Dark**; Firefox website appearance **Automatic / Light / Dark** | from the OS | `prefers-color-scheme` `light` / `dark` | `no-preference` removed — no preference is `light` | `prefers-contrast`, `forced-colors` |

## Findings for the design

1. **No platform gives an app a third scheme.** Every API reduces to light or dark (plus unknown). High contrast is
   always a separate accessibility setting.
2. **"No preference" is common on Linux.** GNOME's light mode is portal 0; Cinnamon's Mixed and "Let applications
   decide" are 0. Qt then guesses from the theme name; Adwaita and Mint-Y contain neither "light" nor "dark", so
   `colorScheme()` is Unknown. Browsers resolved this by treating no preference as light; the portal spec calls 0
   "no preference".
3. **Windows: Qt reads the app mode** (`AppsUseLightTheme`), not the Windows mode, and reports Unknown whenever a
   contrast theme is on — which beats an app's `setColorScheme`.
4. **KDE never sends 0**: its portal derives 1 or 2 from the colour scheme's window background (grey < 192 is dark).
5. **Qt can request a scheme from 6.8** (`setColorScheme`; the Python edition uses PySide6 6.11). On macOS Qt sets
   `NSApp.appearance`; on Windows it applies its own override; on GNOME/GTK3 and KDE themes it records the request
   (GTK3 falls back to the Fusion palette when it differs from the system's); the plain xdg-desktop-portal theme has
   no override. Qt: "overriding the color scheme is not supported on all platforms." The behaviour above is from Qt's
   `dev` branch; PySide6 6.11's is to be tested.

## Sources

**macOS** — appearance: <https://support.apple.com/guide/mac-help/use-a-light-or-dark-appearance-mchl52e1c2d2/mac>;
`NSAppearance.Name`: <https://developer.apple.com/documentation/appkit/nsappearance/name-swift.struct>; Increase
contrast: <https://support.apple.com/guide/mac-help/change-system-settings-for-display-accessibility-unac089/mac>; Qt's
override: <https://code.qt.io/cgit/qt/qtbase.git/plain/src/plugins/platforms/cocoa/qcocoatheme.mm?h=dev>.

**iOS / iPadOS** — <https://support.apple.com/guide/iphone/adjust-screen-brightness-color-balance-iph60ba71065/ios>,
<https://support.apple.com/guide/ipad/adjust-screen-brightness-color-balance-ipad997d972d/ipados>;
`UIUserInterfaceStyle`: <https://developer.apple.com/documentation/uikit/uiuserinterfacestyle>; Increase Contrast:
<https://support.apple.com/guide/iphone/change-display-and-text-size-iph3e2e1fb0/ios>, `UIAccessibilityContrast`:
<https://developer.apple.com/documentation/uikit/uiaccessibilitycontrast>.

**Windows** — modes: <https://support.microsoft.com/en-us/windows/change-colors-in-windows-d26ef4d6-819a-581c-1581-493cfcc005fe>,
<https://support.microsoft.com/en-us/windows/experience/personalization/personalize-your-colors-in-windows>; Windows 10
1903 (Windows Central, not Microsoft): <https://www.windowscentral.com/how-change-color-modes-windows-10-may-2019-update>;
app detection: <https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/ui/apply-windows-themes>; Qt:
<https://code.qt.io/cgit/qt/qtbase.git/plain/src/plugins/platforms/windows/qwindowstheme.cpp?h=dev>; contrast:
<https://support.microsoft.com/en-us/windows/change-color-contrast-in-windows-fedc744c-90ac-69df-aed5-c8a90125e696>,
<https://learn.microsoft.com/en-us/windows/apps/design/accessibility/high-contrast-themes>.

**GNOME** — <https://help.gnome.org/gnome-help/look-background.html>, <https://release.gnome.org/42/>; schema:
<https://gitlab.gnome.org/GNOME/gsettings-desktop-schemas/-/raw/master/schemas/org.gnome.desktop.interface.gschema.xml.in>;
panel: <https://gitlab.gnome.org/GNOME/gnome-control-center/-/raw/main/panels/background/cc-background-panel.c>; portal:
<https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.impl.portal.Settings.html>; contrast:
<https://help.gnome.org/users/gnome-help/stable/a11y-contrast.html.en>.

**KDE** — global themes: <https://invent.kde.org/plasma/plasma-workspace/-/tree/master/lookandfeel>; colours:
<https://invent.kde.org/plasma/breeze/-/tree/master/colors>; Plasma 6.5:
<https://kde.org/announcements/plasma/6/6.5.0/>; portal:
<https://invent.kde.org/plasma/xdg-desktop-portal-kde/-/raw/master/src/settings.cpp>; Qt:
<https://code.qt.io/cgit/qt/qtbase.git/plain/src/gui/platform/unix/qkdetheme.cpp?h=dev>.

**Cinnamon** — <https://github.com/linuxmint/cinnamon/blob/master/files/usr/share/cinnamon/cinnamon-settings/themes.ui>,
<https://github.com/linuxmint/cinnamon/blob/master/files/usr/share/cinnamon/cinnamon-settings/modules/cs_themes.py>;
portal: <https://github.com/linuxmint/xdg-desktop-portal-xapp/blob/master/src/settings.c>; Mint 21.2:
<https://www.linuxmint.com/rel_victoria_cinnamon_whatsnew.php>.

**Qt** — <https://doc.qt.io/qt-6/qstylehints.html>, <https://doc.qt.io/qt-6/qt.html#ColorScheme-enum>; portal theme:
<https://code.qt.io/cgit/qt/qtbase.git/plain/src/plugins/platformthemes/xdgdesktopportal/qxdgdesktopportaltheme.cpp?h=dev>;
GNOME theme: <https://code.qt.io/cgit/qt/qtbase.git/plain/src/gui/platform/unix/qgnometheme.cpp?h=dev>.

**Browsers** — <https://drafts.csswg.org/mediaqueries-5/>,
<https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme>,
<https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme>, <https://www.w3.org/TR/mediaqueries-5/>; Chrome:
<https://support.google.com/chrome/answer/9275525>, <https://wiki.archlinux.org/title/Chromium>; Firefox:
<https://support.mozilla.org/en-US/kb/change-website-appearance-settings-firefox>,
<https://bugzilla.mozilla.org/show_bug.cgi?id=1734934>.
