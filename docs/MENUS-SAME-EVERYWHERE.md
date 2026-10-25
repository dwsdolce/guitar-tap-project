# Menus the same in every edition

**Issue:** [#44](https://github.com/dwsdolce/guitar-tap-project/issues/44)

Status: **OPEN — found 2026-10-24, nothing changed yet.**

## The problem

1. **The saved-measurement row menu differs on the web.** Swift and Python: Load into View · separator · View
   Details · Edit Name & Notes · Export Measurement · Export Spectrum · Export PDF Report · separator · Delete. The
   web puts **View Details above the separator**, beside Load into View, and gives it an **ⓘ** icon where Swift has
   an eye (`eye`) and Python `mdi.eye-outline` (`components/MeasurementsPanel.tsx:735–775`).
2. **Swift on macOS shows no icons in its menus.** The row menu's items are written with icons
   (`Label("View Details", systemImage: "eye")`, `MeasurementsListView.swift:651–`) and show them on iPad and iPhone
   (iPadOS 27, iOS 27), but not on the Mac (macOS 27). The same is seen in the Delete and ⋯ menus on the Mac — likely
   every Swift menu with icons. A report says macOS 27 hides symbol images in SwiftUI menu items by default and that
   `.labelStyle(.titleAndIcon)` on the items shows them; to confirm. Style guide S6: menu items have icons.
3. **Nothing checks the row menu across the editions.** The chart's menu has a shared case file (`chart-menu.json`)
   checking its items, order, separators and icons in all three; the row menu has none, so the web's could drift.

## Plan

1. Confirm the macOS cause with one build; list every Swift menu it affects.
2. A shared case file for the row menu, as `chart-menu.json` — items, separators, icons — run by all three. Swift's
   **Save Measurement to Disk…** is the Mac's only (a recorded platform difference).
3. Fix the web's row menu (order and icon) and Swift's icons on macOS.
4. Run-review.
