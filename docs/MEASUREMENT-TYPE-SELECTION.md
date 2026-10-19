# Measurement-type selection — where it lives, and what New Tap means

**Issue:** [#18](https://github.com/dwsdolce/guitar-tap-project/issues/18)

Status: **ANALYSIS — no decision, nothing implemented.** Parked 2026-09-22 to be picked up later.
Cross-platform: any change here lands on Swift + Python + web together (and is inherited by the
Android port), per the standing "improvements go to all three" rule.

## How this came up

It was not planned work. It surfaced during the run-review of [#17](https://github.com/dwsdolce/guitar-tap-project/issues/17)
F30, at the app, from a symptom the owner hit on step 10:

> *"The New Tap button is enabled BUT the Pause button is ALSO enabled — there is nothing to
> pause… Pressing it makes no change to the display or state except to change the button from
> Pause to Resume. BUT if I then make a tap while showing the comparison measurement the Pause
> button becomes disabled. Really strange state of affairs here."*

Half of that was a straightforward defect and is **already fixed** — the detector was being left
armed underneath a frozen comparison overlay. That is #17 **F31**, fixed in both natives with paired
tests, and it is not what this document is about.

The other half is a design question the defect exposed, which no amount of bug-fixing answers:
**what does New Tap mean when what you are looking at is not a tap-made measurement?** That question
turned out to depend on a second one — **where you choose the measurement type** — and the two have
to be settled together.

## The framing that changed the question

The owner's framing, and the one this analysis proceeds from:

> A comparison is a **measurement type**, like Guitar or Plate or Brace. It is simply created by an
> action in the measurement browser rather than by responding to a tap.

Under that reading, "New Tap" in a comparison is a category error. The button means *perform a new
tap for the currently-defined measurement*; a comparison is not produced by tapping, so there is no
such thing as a new tap of one. What the button does today instead is change the measurement type
without naming a type — silently, as a side effect of a control that says something else.

An earlier version of this analysis argued from the implementation (that the type never changes,
that New Tap is the only exit) and was wrong to. Those are facts about the code, not about what a
user should expect. The owner's correction stands: *"selecting the type of tap measurement you want
to do is not obvious — it is buried in a settings form when it is NOT really a setting but a
selection mechanism for defining the action you want to perform."*

## Three readings of New Tap

**A — today.** New Tap stays enabled in a comparison and starts a sequence of the currently selected
tap type.

- One button press to get back to tapping.
- But it performs an unnamed type change, and the type you land in is invisible until you are in it.
  You can be set to Plate, compare two guitar measurements, press New Tap and get a *plate* sequence.
- It also forces New Tap to carry a second meaning no other button has: *leave this type and start
  the last one*. The rule becomes "tap actions apply to tap types, except New Tap, which also means…".

**B — disabled.** New Tap (and Pause, and Cancel) are disabled in a comparison, because no tap action
applies to it. You leave by choosing another type.

- One coherent rule, statable in a line: *tap actions apply to tap types.* It disposes of the
  "nothing to pause" oddity as a consequence rather than as a separate fix.
- Costs a dead button with no explanation unless the disabled hint says why.
- Depends entirely on type selection being obvious. Web shipped exactly this by accident once — see
  #17 F24, where New Tap came out disabled during a comparison and trapped the user with no way back
  to live. That is B without a visible type selector, and it is why B cannot ship on its own.

**C — a new one of the current type.** New Tap means *make a new measurement of the current type, by
whatever means that type is made*: tap types arm and wait for a tap; Comparison reopens the browser
in Compare mode for a fresh selection. Proposed by the owner's wife.

- Keeps one uniform rule with nothing disabled and no hidden type change.
- Fits an idiom the app already has: this button row **already relabels contextually** — during a
  material review Pause becomes Accept and Cancel becomes Redo. So New Tap reading **"New
  Comparison"** in a comparison is the existing pattern applied to a third case, and it fixes the
  label, which otherwise claims you are tapping when you are not.
- Scales unchanged if Compare is broadened beyond guitar to any set of same-type measurements.
- **But it does not answer how you get back to tapping.** C inherits B's dependency exactly.

**Where that leaves it.** B and C both require visible type selection; A only looks independent
because it uses New Tap as an accidental escape hatch, which is the very thing that makes it
incoherent. So the New Tap semantics are downstream of the type-selector question, and that is the
one to settle first. C is the current front-runner, but it is not a decision.

## The type selector

Today: a `Picker` inside the Settings sheet, applied by an explicit **Apply** that validates
everything and dismisses (`TapSettingsView+Sections.swift:36`, `TapSettingsView+Actions.swift:158`).
Changing what you are about to measure costs a sheet, a pick, and an Apply.

The objection is that this is not a setting. A setting is something you set once and forget; this is
a choice of what action you are about to perform, changed as part of the work.

### What is a type, and what is a parameter

The owner's division, which is the one to use:

> The types that require **extra information the user has to supply** are Plate and Brace — the
> material dimensions, which persist. Those are settings. The rest are just types.

| | needs user-supplied info? | |
|---|---|---|
| Generic, Classical, Acoustic, Flamenco | no — built-in frequency bands | **type** |
| Plate, Brace | yes — material dimensions, Measure FLC, panel preset | **type**, whose parameters stay in Settings |
| Comparison | n/a — created from the browser | **type**, displayed but not selectable |

So: the picker chooses the type; Settings holds the parameters a type consumes. Only two of the six
selectable types have any.

### The control

A **menu button showing the current type**, sited **with the tap controls** — the same control, the
same placement rule, on every platform.

An earlier draft proposed a three-way segmented control (Guitar / Plate / Brace) with the guitar
sub-types left in Settings, and a different compact form on iPhone portrait. Both of those were
wrong, for one reason: a segmented control pays width per option, six segments do not fit on a
phone, and everything downstream — cutting six to three, a per-platform special case — was solving a
problem the control form had created. **A menu pays no width per option**, so the count constraint
disappears and one form works everywhere.

There is no per-platform placement to invent, either. Every layout already positions the tap
controls: `headerView` on macOS and iPhone portrait, `regularTapControls` on iPad,
`landscapeTapControls` in the phone-landscape rail (`TapToneAnalysisView+Layouts.swift`). The rule
is "with the tap controls" and all four variants already solve it.

Sketch:

- One menu button, current type as its label; short name on the button, full name in the menu
  (`MeasurementType` carries both).
- Six selectable entries, sectioned Guitar / Material — mirrors the `isGuitar` split already in the
  model and keeps six entries scannable.
- **Comparison displays but is not selectable.** Choosing any of the six leaves the comparison. The
  control is therefore also the comparison indicator *and* the comparison exit — which is the
  missing piece B and C both need.
- Selecting acts immediately — the same work `onApply(measurementChanged:)` does today, minus the
  sheet.
- **Remove the Type picker from Settings.** One place, not two.

## Open questions

1. **Plate or Brace picked with no dimensions set** — arm anyway and let Results show blanks, or
   route to the dimensions first? The only case where "this type needs information" has a UX
   consequence.
2. **Switching type mid-sequence** — today Apply discards an in-flight sequence silently, and a
   one-tap menu makes that much easier to hit by accident. Confirm when `currentTapCount > 0`, or
   keep current behaviour?
3. **Which reading of New Tap** — A, B or C — once the selector is visible. C is the front-runner.
4. **Whether Compare should broaden** beyond guitar to any set of same-type measurements. The owner
   raised it as something under consideration; it makes C more valuable and makes "which type do I
   return to" answerable, since a comparison's underlying tap type would be known.

## Related

- [#17](https://github.com/dwsdolce/guitar-tap-project/issues/17) [`completed/SLUG-SWEEP.md`](completed/SLUG-SWEEP.md) — **F31** (the
  disarm defect this came from, fixed) and **F24** (`displayMode` as a required input to the button
  rule; the trap-the-user bug that is Reading B without a visible selector).
- [#1](https://github.com/dwsdolce/guitar-tap-project/issues/1) `RESTRUCTURE-NOTES.md` — the
  architectural-parity restructure, which touches the same view layer.
- `WEB-UI-GUIDELINES.md`, `ANDROID-UI-GUIDELINES.md` — the per-platform UI translation rules any
  control change has to satisfy.
- Manual and Quick-Start on all four surfaces: "go to Settings to choose a measurement type" stops
  being true, so the docs change with the control.
