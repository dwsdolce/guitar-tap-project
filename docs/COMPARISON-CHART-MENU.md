# The chart menu for a comparison

**Issue:** [#42](https://github.com/dwsdolce/guitar-tap-project/issues/42)

Status: **OPEN — built in all three editions (2026-10-24): Swift `0f33f1a` (notes `48b3964`), Python `b6bd987`
(notes `2e33ec8`), web `184f3cc` (notes `7f6798f`); run-review passed in every edition and on the iPhone (owner).**
To close once CI is green.

## The problem

The chart's menu offers the same resets whatever is shown: **Saved** (the range in Settings) and **Defaults** (the
range built into the app for the current measurement type). For a guitar measurement — live, loaded, or a multi-tap
measurement with its table of taps — both mean something. For a **comparison** neither does: it holds measurements
of many guitars, each with its own saved view, and it opens at the span of them all. After a zoom or pan there is no
way back to that span; **Reset Both Axes to Defaults** gave a guitar comparison the plate range (20–200 Hz) because
the type button was set to Plate.

## The decision (owner, 2026-10-24)

While a comparison is shown, the chart's menu is its own, with one group:

| Item | Returns to |
|---|---|
| **Reset Both Axes to Comparison Range** | the comparison range, both axes |
| **Reset Frequency Axis to Comparison Range** | the comparison range's frequencies |
| **Reset Magnitude Axis to Comparison Range** | the comparison range's levels |

- **The comparison range** is the span of the compared measurements: the lowest of their saved views' lower bounds
  and the highest of their upper ones, on each axis — the range a comparison opens at (Swift `DisplayRange.spanning`,
  Python `spanning_range`, the web's equivalent). Never the range a saved comparison was stored with.
- No **Saved** or **Defaults** group, and no **Reset Labels** (a comparison shows no labels).
- Every other chart — a guitar measurement, a multi-tap measurement, a plate or brace — keeps today's menu.

## Plan

1. The comparison's groups in the shared `chart-menu.json` and in each edition's chart menu (Swift `ChartMenu.swift`,
   Python `views/chart_menu.py`, web `presentation/chartMenu.ts`), with their actions.
2. Tests: the shared case file's new groups, in all three.
3. The manual's chart-menu section and each Quick Start; the release notes.
4. Run-review.
