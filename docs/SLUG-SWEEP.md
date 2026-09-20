# Sweep every `@parity` slug

**Issue:** [#17](https://github.com/dwsdolce/guitar-tap-project/issues/17) · **Status:** ⏳ Stage 1 in progress

## The problem

`gen_parity_map.py --check` answers one question: does this slug have a test in each edition? It
cannot tell whether those tests assert the same thing, whether they reach production code at all, or
whether the behaviour still exists. And it only sees files that carry a `@parity` tag — ten do not.

So a slug can report healthy while its three tests measure three different things, or nothing.

## Why we believe that is happening

Issue #8 read **one slug out of 43** closely — `test/frozen-peak-recalc`. It found:

- eight tests that measured nothing (they exercised a helper in the test file, not the app)
- two rows pairing tests that asserted genuinely different behaviours
- a missing test in the canonical edition
- two architectural defects in the web app
- **a data bug that wrote 111 peaks into every saved measurement as 217**
- a classifier returning a guitar mode for peaks it could not classify, including material peaks
- a chart behaviour that existed in Swift and in neither port

That slug was not picked because it looked suspicious. By test-count spread it looked *healthier*
than `test/pitch`, `test/brace`, `test/plate` or `test/classify`. It was simply the one somebody read.

The remaining 42 slugs have had no equivalent reading.

## The two rules to apply

Set by the owner, 2026-09-20:

1. **Every test file carries a `@parity` tag.** `none` is a valid value when justified; absent is not.
2. **No behaviour is tested in only one edition when it exists in more.** A method name that differs
   between editions is not a missing test — look for what the code *does*.

A third, added 2026-09-20 after the measurement pass:

3. **Do not believe a comment.** Comments in tests and in production code have been wrong at least as
   often as they have been right. Verify that the code does what the comment says before using the
   comment as evidence. This applies to machine-readable comments too — see the `tests=` finding below.

## Stage 1 — sweep and triage

Go slug by slug, **within a subsystem**, reading the production code first. For each slug answer: is
every edition testing the same behaviour, against production code, for something that still exists?

Four defect shapes to look for. All four occurred in #8 and none is visible to `--check`:

| shape | what it looked like in #8 |
|---|---|
| a test-local helper reimplementing the behaviour under test | `_remap_by_freq` — six tests asserting against a copy of the logic |
| a fixture encoding a contract the app no longer sends | `peak-fullset-save` fed a filtered peak set; the app sends the full one |
| tests pinning a removed feature or an unreachable state | PS1–PS6, green for five months against deleted UI |
| an assertion that holds by construction | asserting a peak is in a list the branch just set to `[thatPeak]` |
| the same rule asserted under two slugs | `WoodQuality.color` pinned in both `test/quality-colors` and `test/plate`, which then disagreed (F8) |

[`process/PARITY-TEST-METHOD.md`](../process/PARITY-TEST-METHOD.md) is the method — eight rules,
including how to verify a test is worth keeping (mutate it) and how to avoid the false greens that
caught us three times.

### Sweep order — by subsystem, canonical first

Chosen by the owner, 2026-09-20, over "widest spread first" and "alphabetical".

> The code is the source of truth that the tests are being measured against.

Reading by subsystem means the production code is read once per subsystem rather than once per slug,
which is what makes the question "does this test reach production code?" answerable. Count spread
does not drive the order: in #8 the spread was near-balanced and the subsystem was full of defects.

The grouping below is derived from the **import graph** of the test files (Python `import` statements
and web `from '../src/…'` specifiers), not from the `tests=` attributes in the parity map — see the
finding on those below. Swift edges are not recoverable this way, because `@testable import GuitarTap`
imports the whole module; Swift is read file by file as each subsystem comes up.

| # | subsystem | production anchor (Swift / Python / web) | slugs |
|---|---|---|---|
| S1 | Material properties | `MaterialProperties.swift` / `material_properties.py` / `dsp/material.ts` | `brace` `plate` `quality-colors` |
| S2 | Mode classification | `GuitarMode.swift` / `guitar_mode.py` / `dsp/classify.ts` + `dsp/guitarModes.ts` | `classify` `mode-colors` (+ `view/dot-layer`) |
| S3 | Pitch | `Pitch.swift` / `pitch.py` / `dsp/pitch.ts` | `pitch` |
| S4 | Peak detection & analysis | `ResonantPeak.swift`, `TapToneAnalyzer+PeakAnalysis.swift` / `dsp/peaks.ts` | `peaks` `dsp` `peak-heal` (`frozen-peak-recalc` closed in #8) |
| S5 | Measurement model & persistence | `TapToneMeasurement.swift` / `measurement/*.ts` | `measurement-codable` `import-persistence` `peak-selection-persistence` `measurement-name` `measurement-type-name` `material-selection` `export-filename` `material-measurement-inputs` |
| S6 | Analyzer state machine | `TapToneAnalyzer+Control.swift` / `state/tapToneAnalyzer.ts` | `state-invariants` `scenario-trace` `measurement-complete` `start-tap-race` `tap-count-change` `status-message` `button-enablement` `session-pre-roll` `annotation-state` `effective-peak-id` `comparison` |
| S7 | Capture / DSP pipeline | `RealtimeFFTAnalyzer.swift` / `dsp/gatedCapture.ts`, `dsp/wav.ts`, `dsp/decay.ts` | `gated-fft` `tap-decisions` `tap-progress` `file-playback` `decay-tracking` |
| S8 | Settings & presentation | `TapDisplaySettings.swift`, `DisplayRange.swift`, `FieldPrecision.swift` | `display-range` `field-precision` `analysis-quality` `wav-dump-folder` |
| S9 | Oracle / baseline infrastructure | `parityRunner`, `selfBaseline`, `ParityOracle` | `oracle-sync` `self-regression` `parity-oracle` `parity-runner` `self-baseline` — **classification only**, see below |

S1 goes first: pure computation, no analyzer state, and it holds the two widest gaps in the map.

**S9 is scoped to classification, not to the oracle machinery.** Owner's call, 2026-09-20: the oracle
and baseline work is [#16](https://github.com/dwsdolce/guitar-tap-project/issues/16) and is not part
of this effort. #17 touches it only to decide what those five slugs should be *called* (F2). The
Windows and Linux baselines stay stale until #17 is finished — they will very likely need re-minting
afterwards anyway, since Stage 1 is expected to change production code, and re-minting them first
would only invalidate the work. Both platforms are out of use until then. Nothing in #17 should wait
on #16, and the parity tolerance is not #17's to touch.

### Starting picture — measured with the test runners, 2026-09-20

The earlier version of this table came from `grep`. These counts come from the runners themselves:

```
Swift   xcodebuild test-without-building -scheme guitar_tap -destination 'platform=macOS' \
          -resultBundlePath run.xcresult
        xcrun xcresulttool get test-results tests --path run.xcresult --format json
Python  .venv/bin/python -m pytest --collect-only -q      (pytest expands @parametrize)
web     npx vitest list --json                            (vitest expands generated cases)
```

Suite totals as run:

| edition | result |
|---|---|
| Swift | **516 passed** in 111 suites, 1 skipped (`GenerateParityOracle`). 517 test cases; 526 once the three `@Test(arguments:)` sites expand. |
| Python | **615 passed, 1 skipped** (616 collected, 50 files) |
| web | **433 passed, 2 skipped** (435 in 51 files). The two skips are `oracle-sync` and `mint-baseline`; neither is a behavioural test — see F2. |

Counts inside `test/*` slugs only — Swift 475 · Python 502 · web 343. The remainder sit in
non-`test/` slugs (`dead-input`, `view/dot-layer`, `tooling/*`) or under `@parity none`.

| slug | Swift | Python | web | |
|---|---:|---:|---:|---|
| `test/analysis-quality` | 6 | 6 | 20 | 3.3× — web *higher* |
| `test/annotation-state` | 44 | 42 | 32 | |
| `test/brace` | 20 | 20 | 1 | **20.0×** |
| `test/button-enablement` | 13 | 13 | 13 | |
| `test/classify` | 37 | 37 | 8 | 4.6× |
| `test/comparison` | 20 | 32 | 7 | 4.6× |
| `test/decay-tracking` | 7 | 7 | 10 | |
| `test/display-range` | 7 | 5 | 10 | 2.0× |
| `test/dsp` | 10 | 10 | 0 | **missing: web** |
| `test/effective-peak-id` | 6 | 6 | 0 | **missing: web** |
| `test/export-filename` | 6 | 6 | 6 | |
| `test/field-precision` | 13 | 13 | 13 | |
| `test/file-playback` | 8 | 8 | 11 | |
| `test/frozen-peak-recalc` | 37 | 35 | 38 | closed in #8 |
| `test/gated-fft` | 5 | 5 | 5 | |
| `test/import-persistence` | 3 | 3 | 6 | 2.0× |
| `test/material-measurement-inputs` | 6 | 6 | 6 | |
| `test/material-selection` | 1 | 1 | 1 | |
| `test/measurement-codable` | 53 | 64 | 23 | 2.8× |
| `test/measurement-complete` | 8 | 13 | 8 | |
| `test/measurement-name` | 4 | 4 | 4 | |
| `test/measurement-type-name` | 14 | 9 | 6 | 2.3× |
| `test/mode-colors` | 1 | 1 | 3 | 3.0× — web *higher* |
| `test/oracle-sync` | 0 | 1 | 1 | not a test — oracle maintenance (F2); skips in both editions that have it (F3) |
| `test/parity-oracle` | 0 | 0 | 0 | not a test — shared helper module (F2) |
| `test/parity-runner` | 0 | 0 | 0 | not a test — shared helper module (F2) |
| `test/peak-heal` | 5 | 5 | 5 | |
| `test/peak-selection-persistence` | 4 | 4 | 3 | |
| `test/peaks` | 24 | 30 | 26 | |
| `test/pitch` | 22 | 22 | 6 | 3.7× |
| `test/plate` | 28 | 28 | 3 | **9.3×** |
| `test/quality-colors` | 2 | 2 | 3 | |
| `test/scenario-trace` | 4 | 4 | 4 | |
| `test/self-baseline` | 0 | 0 | 0 | not a test — shared helper module (F2) |
| `test/self-regression` | 0 | 2 | 2 | absent from Swift **by design** — see F4; Python and web run and pass |
| `test/session-pre-roll` | 4 | 4 | 4 | |
| `test/start-tap-race` | 4 | 4 | 4 | |
| `test/state-invariants` | 7 | 7 | 7 | |
| `test/status-message` | 12 | 12 | 16 | |
| `test/tap-count-change` | 6 | 6 | 11 | |
| `test/tap-decisions` | 10 | 10 | 5 | 2.0× |
| `test/tap-progress` | 10 | 10 | 12 | |
| `test/wav-dump-folder` | 4 | 5 | 0 | **missing: web** |

**What the re-measurement changed.** Only one entry: `test/pitch` was recorded as 22/22/1 and is
really 22/22/6. Every other gap the grep table flagged is real. Of the eight slugs `--check` calls
"missing an edition", three — `parity-oracle`, `parity-runner`, `self-baseline` — are shared helper
modules rather than test files, and a fourth, `oracle-sync`, is maintenance tooling. See F2. That
leaves three real gaps: `test/dsp`, `test/effective-peak-id` and `test/wav-dump-folder` absent from
web. `test/self-regression` is absent from Swift by design (F4), so it is not one.

**A wide spread is a hint, not a verdict.** `test/frozen-peak-recalc` was 37/35/38 and was full of
defects. Two spreads run the other way: `test/analysis-quality` and `test/mode-colors` have more
tests in web than in canonical Swift, which is as interesting as the thin ones.

**Untagged test files — ten, confirmed by enumeration.** Swift is fully tagged apart from
`TestRunner.swift`.

| edition | files |
|---|---|
| Python | `test_wi1_settings_persistence`, `test_wi6_tap_display_settings`, `test_comparison_annotation_guard` |
| web | `calibration-store`, `g0-wav`, `g3a-calibration`, `g6-measurement-bridge`, `g7-measurement-4c`, `g8-material-load`, `g9-multitap` |

### Findings open from the measurement pass

Recorded here when found; each is closed in the subsystem that owns it.

**F1 — the `tests=` links in the parity map are unreliable. (open, close at end of sweep)**
`tests=` is a hand-written attribute on a production file's `@parity` tag, so it is a comment, and
rule 3 applies. Against the import graph it does not hold: sixteen `test/*` slugs have no production
group pointing at them, and twenty-six production groups claim no test evidence at all. Some of those
are plainly wrong — `test/field-precision` is "unlinked" while `field-precision.test.ts` imports
`src/precision.ts` and nothing else. This matters beyond tidiness: `doc_coverage.py` derives the
functional-block coverage metric from these links, so the coverage number is only as good as the
attribute. Do not use `tests=` as input to the sweep; repair it from the import graph at the end.

**F2 — five `test/*` slugs are not tests at all. (open, S9)**
Three are shared helper modules imported by real tests: `parity-oracle`, `parity-runner`,
`self-baseline`. Two are oracle-maintenance tooling, confirmed by the owner 2026-09-20:
`oracle-sync` checks a repo's vendored `parity-oracle.json` against canonical, and `mint-baseline`
(with `mint-oracle.sh`) regenerates the oracle and baseline files on the rare occasions they are
deliberately refreshed. None of the five asserts anything about application behaviour.

Because they carry `test/*` slugs, `--check` counts them as test evidence and `doc_coverage.py`
folds them into the functional-block coverage metric. They need a classification of their own —
`tooling/*`, or `none` — decided in S9. Nothing about the files themselves is wrong; the
classification is.

**F3 — the oracle staleness guard is not running in any edition. (open — #16's, not #17's)**
Every repo vendors its own `parity-oracle.json` so its suite runs offline, which is also the failure
mode: the copy can go stale while canonical moves on, and every test keeps passing against
yesterday's numbers. Python and web each wrap `tooling/sync-oracle.sh --check` to catch that. Both
currently skip, loudly, with *"CANONICAL ORACLE UNREACHABLE … Script said: curl: (56) The requested
URL returned error: 404"* — the published URL 404s while the hub is private, and the fallback needs
`ORACLE_SRC=<hub checkout>`. Swift has no wrapper test, though it too vendors a copy
(`GuitarTapTests/parity-oracle.json`, with its own `oracle-dest.txt` and `sync-oracle.sh`); the check
means less there, because Swift's copy is the source the hub's is published *from*.

All four copies — hub, Swift, Python, web — are byte-identical today (`md5 5880a2eb…`), so nothing
has drifted yet. The guard simply is not guarding. It is designed to start working by itself once
the hub goes public ([#11](https://github.com/dwsdolce/guitar-tap-project/issues/11)); until then the
question is whether a local-checkout fallback should be wired up rather than left to a skip.

**F4 — Swift's zero-tolerance check is the oracle itself. (closed — not a finding)**
Recorded because the count table makes it look like a gap and it is not. `test/self-regression` is
absent from Swift deliberately. `tooling/parity/README.md` states the design — *"Swift-on-macOS's
baseline **is** the oracle — it minted it"* — and `FilePlaybackRegressionTests.swift` implements it:
*"Swift MINTS the oracle, so these assert at the same-edition bar — zero."* Its eight file-playback
tests are Swift's regression check, at zero tolerance, against the file it produced.

This is also a live staleness check on the oracle, which is worth knowing. The current oracle was
minted from Swift at `5bacce4-dirty` (2026-09-18); Swift's HEAD is now `7fcf0fe`, two days and all of
#8 later. Because those eight tests pass at zero today, **Swift's current code still reproduces the
oracle exactly** — nothing in #8 moved a canonical number. `parity-report.py` lists
`swift-darwin-arm64` among the minted configurations for the same reason.

### S1 — Material properties (`brace`, `plate`, `quality-colors`)

Status: ✅ **COMPLETE** — all three slugs read, four defects found and fixed (F5–F8).
Landed as Swift `399dde2`, Python `7d7528d`, web `1a30b85`.

Full suites after the S1 work, all green:

| edition | before | after |
|---|---|---|
| Swift | 516 in 111 suites | **534 in 114 suites**, all passed |
| Python | 615 passed, 1 skipped | **633 passed, 1 skipped** |
| web | 433 passed, 2 skipped | **488 passed, 2 skipped** |

The skips are unchanged and pre-existing — Python's `oracle-sync` (F3), web's `oracle-sync` and
`mint-baseline` (F2). Per-slug, web went from barely present to level:

| slug | Swift | Python | web |
|---|---|---|---|
| `test/brace` | 20 → 24 | 20 → 24 | **1 → 23** |
| `test/plate` | 28 → 41 | 28 → 41 | **3 → 34** |
| `test/quality-colors` | 2 → 5 | 2 → 3 | 3 → 5 |

Five production files changed — `MaterialProperties.swift` and the new `ColorHex.swift` for F8,
`dsp/material.ts`, `MaterialResults.tsx` and `measurementImage.ts` for F6. Everything else is tests.
Two behaviour changes reach users: web stops rendering `"NaN"` for the radiation ratio, and the macOS
app's quality colours return to the values they had before macOS 26 moved the system palette.

**What S1 says about the rest of the sweep.** This was chosen as the cheap subsystem — three slugs,
pure arithmetic, no analyzer state. It produced four defects, two user-visible, one a change to how
the canonical app looks, and a defect shape #8 never saw. Test-count spread predicted the web gaps in
`brace` and `plate` and predicted **nothing** about F6, F7 or F8: `test/quality-colors` was 2/2/3,
among the most balanced rows in the whole table, and concealed a live cross-edition colour divergence.
Budget the remaining eight subsystems on that basis, not on their counts.

**F5 — the material fixtures were invented, and each edition invented differently. (FIXED)**

What was there. The frequency in web's `brace.test.ts`, `512.6888`, was genuine — it is the
measured peak in the hub's own `Tests/Brace/brace-umik-1-swift-mac-1778816093.guitartap`. But web
paired it with dimensions of 600 x 24 x 8.5 mm / 58 g, which is a different object: that implies
E_L 211.4 GPa and c 21 124 m/s, stiffer than steel and faster than sound in diamond. Physics settles
which geometry is real — at any spruce modulus web's bar could only ring between 100 and 141 Hz,
where the real blank's geometry rings at 512.3 Hz for E_L 10.54 GPa.

Web's plate was a near-miss of the real sample rather than a different one: length, width and mass
all within ~4%, but **thickness 2.8 mm against a real 4.85 mm**. Since E ∝ 1/t², that single field
inflated E_L from 6.11 to 31.1 GPa.

Swift and Python were not clean either. Their brace fixture was the real blank but carried
fL = 512.3, matching neither the saved measurement nor the oracle (both 512.6888) — a transcription
of the report's rounded "512.7 Hz" display. Their *plate* fixture was wholly synthetic, and outside
the app's own envelope: E_C/E_L 0.0089 against the 0.04–0.08 the UI calls typical, and E_L/E_C 113
against 12–25. Three tests had had their acceptance bands widened to fit it — one states "typical
spruce EL: 10–15 GPa" in its comment and then asserts 5–20 "for test robustness".

**The structural cause.** The oracle pins frequencies but records no sample geometry, and material
properties need both. So every material test had to source dimensions from outside the oracle, and
each edition did it differently with no provenance recorded. That is why it diverged silently for
three months.

**The fix**, owner's decision 2026-09-20 — *synthetic is fine for algebraic tests, real data for
realistic tests*. Two named fixtures per edition, and the file says which is for what:

| | fixture | source |
|---|---|---|
| real brace | 556 x 20.4 x 29.4 mm, 128 g, fL 512.6888 | `Tests/Brace/brace-umik-1-swift-mac-1778816093.guitartap` |
| real plate | 557.5 x 220.5 x 4.85 mm, 208 g, 67.11537 / 116.27016 / 35.353745 Hz, body 490 x 390, Classical Top | `Tests/Plate/plate-umik-1-swift-mac-1778816330.guitartap` |
| synthetic plate | 500 x 200 x 3 mm, 120 g | algebraic identities only — density lands on exactly 400 |

The expected values are the ones **GuitarTap itself reported** for those samples, printed in the
`.pdf` beside each file — not numbers regenerated by running the code, which is the trap
`mint-baseline` exists to avoid. Every one was verified to reproduce its report exactly.

Two things this buys beyond correctness. The real plate's anisotropy lands **inside** the app's own
typical bands (0.0734 and 13.6). And it grades **Fair** longitudinally and **Very Good** across,
blending to **Good** — so the quality classifier and its 0.7/0.3 weighting are exercised in the
middle of their range. Every previous fixture saturated at Excellent, where the assertion holds
however far the thresholds move; web's sat at a specific modulus of 446 against a threshold of 25.

**F6 — the radiation ratio and anisotropy ratios were model code in Swift and Python, view code
in web. (FIXED)**
`radiationRatioLong/Cross`, `crossLongRatio` and `longCrossRatio` are properties of
`PlateProperties`/`BraceProperties` in Swift and of the mirrored classes in Python. Web had none of
them in `dsp/material.ts`. It computed `R = c/ρ` inline at four sites and the anisotropy ratios at
two, split across `components/MaterialResults.tsx` (the live panel) and
`presentation/measurementImage.ts` (the exported image) — each with its own copy.

**That duplication already cost a user-visible defect.** Web's inline `rL = cL / rho` omitted the
zero-density guard Swift has (`guard dimensions.density > 0 else { return 0 }`). Confirmed by
running it: at zero thickness or zero mass web yields `NaN` where Swift and Python yield `0`, and
`f1(NaN)` renders the literal string `"NaN"` into both the panel and the exported image. It is
reachable — `materialMeasurementInputs.ts` defaults a missing dimension to `0`, so any material
measurement opened before its dimensions are entered hits it.

An audit of **every** division in the material code of all three editions found this to be the only
unguarded one. Swift's model is fully guarded, including the whole Gore path; Python's mirrors it;
web's `dsp/material.ts` is fully guarded too. The single unguarded division in the subsystem was the
copy that had left the model — which is the argument for the fix rather than a patch.

**The fix**, web only; Swift and Python already had all three in the model, correctly guarded.
`radiationRatio`, `crossLongRatio` and `longCrossRatio` now live in `src/dsp/material.ts`, and the
six call sites in `components/MaterialResults.tsx` and `presentation/measurementImage.ts` call them.
For the two anisotropy ratios this is a pure move — the inline copies already carried the guard, so
only the duplication goes. For the radiation ratio it is a move **plus** a behaviour fix, because the
model function carries the `rho > 0` guard the inline copies never had.

**Mutation-tested**, per method rule 2. Removing the guard from `radiationRatio` fails exactly four
tests — the zero-density and zero-mass cases in `brace.test.ts` and `plate.test.ts` — and leaves the
other 53 in those files passing. The tests are specific to the defect, not incidentally green.

**F7 — the radiation ratio had no test in any edition. (FIXED)**
Swift and Python both tested `crossLongRatio` and `longCrossRatio`; neither tested `R`, and web
tested none of the three. `R` is displayed in the Results panel and baked into the exported image in
all three editions. That is how F6 survived.

Fixed with tests only — no production change was needed for this one. Swift gains
`PlateRadiationRatio` (5) and `BraceRadiationRatio` (4), Python the mirrored
`TestPlateRadiationRatio` (5) and `TestBraceRadiationRatio` (4), web two `radiation ratio` blocks (8).
Each edition covers the same five things: R equals c/ρ, R_L exceeds R_C, R sits in the 10–15 band
for the real spruce sample, and both routes to zero density return 0 rather than NaN.

**F8 — Swift's display colours were semantic, so the OS moved them out from under the ports. (FIXED)**

`test/quality-colors` exists because a colour copy once drifted to a wrong hue with nothing to catch
it. It had still not caught the next one.

Swift resolved its five quality colours from SwiftUI's semantic system colours — `.green`, `.mint`,
`.blue`, `.orange`, `.red`. Those are supplied by the OS, so what GuitarTap draws changes when Apple
revises the palette. **macOS 26 revised it.** Measured on 26.6.2, with `NSColor.system*` probed
alongside to confirm Swift was faithfully following Apple and not mis-resolving:

| grade | Swift rendered | Python + web `light` pinned | |
|---|---|---|---|
| Excellent | `#34C759` | `#34C759` | agrees |
| Very Good | `#00C8B3` | `#00C7BE` | subtle |
| Good | `#0088FF` | `#007AFF` | **visible** |
| Fair | `#FF8D28` | `#FF9500` | **visible** |
| Poor | `#FF383C` | `#FF3B30` | subtle |

The ports were not wrong when written — they pinned the pre-26 system palette, and Apple moved.
They cannot follow an OS palette, so the three editions silently stopped agreeing.

**This is not the dark-surface difference.** Web renders on dark chrome and the natives on white, and
that shade difference is deliberate and is what the theme work formalises. The table above is three
**white** surfaces: the macOS app, the Python app, and the PDF report the web generates, which
`qualityColors.ts` pins to `light` precisely because a printed report is never themed.

**Why nothing caught it.** Swift's test asserted `WoodQuality.excellent.color == .green` — a semantic
identity that stays true whatever hue the OS hands back. It was structurally incapable of detecting
the drift, in the one group whose whole purpose is detecting drift. Same shape as F7.

**The fix**, owner's decision 2026-09-20 — *make the colours absolute; it is what the theme work will
do anyway, and the hue is only a discriminator between values, not meaning*. Swift gains
`WoodQuality.hex` holding the five values outright, with `color` derived from it through a new
`Color(sRGBHex:)` in `Models/ColorHex.swift`. The table chosen is the one Python and web already
shipped, so **only Swift changed** and its appearance returns to what it was before macOS 26.

Tests now pin the hex in all three editions rather than a semantic name, and all three run the same
three shared cases — the canonical table, every grade distinct, the five labels — plus the extras
that genuinely are edition-specific (Swift: `color` derives from `hex`, and is not a system colour;
web: the `dark` table and the scheme accessor, which the natives have no equivalent of until the
theme work lands). Swift 2 → 5, Python 2 → 3, web 3 → 5.

**Mutation-tested with the real defect.** Setting Swift's Good back to `#0088FF` — exactly what
macOS 26 did — fails `perQualityHex`: *"(WoodQuality.good.hex → "#0088FF") == "#007AFF""*. Had this
test existed in this form, the palette change would have failed the build.

**The full suite then caught a second copy.** Swift's suite failed on the first run after the fix —
`PlatePropertiesTests.swift` had its *own* colour assertions, in a `WoodQualityTests` suite, still
demanding the semantic values. So the colour rule was asserted under **two slugs**: `test/quality-colors`,
whose file is tagged for it, and `test/plate`, which had quietly acquired it. The two disagreed the
moment one was updated.

Python had the same shape more weakly — `test_plate.py` asserted only that each colour *is* a hex
string, still under `test/plate`. Web had no duplicate. Both copies are now removed, with a comment
in their place saying where the rule lives, so all three editions agree on which slug owns it.

This is a fifth defect shape, and none of the four in the table above covers it: **the same rule
asserted under two slugs**. It is invisible to `--check` (both slugs look healthy), invisible to a
per-slug reading (each file looks reasonable alone), and it only surfaces when the two copies are
made to disagree. Watch for it in the remaining subsystems — the way to find it is to run the whole
suite after every change, never just the slug's own file.

**Likely the same in `model/mode-colors`.** Swift's `GuitarMode.color` is semantic in the same way
(`.cyan`, `.green`, `.orange`, …) while Python pins RGB tuples and web pins hex, and those three sets
are visibly different from each other. Unmeasured so far — it is S2's slug, taken up there.

## Stage 2 — move case lists into shared data

Once Stage 1 has shown which slugs are case-shaped and what their cases need to express, move those
case lists into data vendored the way `parity-oracle.json` is, with one small runner per edition.
Divergence then becomes **unrepresentable** rather than merely detectable, and a fourth edition ports
one runner instead of thirty tests.

The pattern is already proven in this codebase and needs no prototype: web's `pitch.test.ts` is a row
list plus a loop that generates the cases.

**Why this comes second.** #8 designed a case schema for `test/frozen-peak-recalc` and never built
it. That was fortunate: that slug needs stateful analyzer setup, where most slugs are
input → expected output. Designing the shared format against it alone would have fitted the mechanism
to the least representative example — the same mistake that produced the original divergence, where a
fixture built for one test became the pattern for a suite.

**Relative size.** The owner's read, 2026-09-20, is that Stage 1 overwhelms Stage 2. The measurement
supports it: Stage 1 is 43 slugs across nine subsystems with production defects expected, where
Stage 2 is a mechanical move of the case-shaped subset. This bears on what #17 should gate — see
[`ANDROID-PLAN.md`](ANDROID-PLAN.md), which records that how much of #17 gates the Android port is a
judgement, not a given.

## Expect production defects, not just test cleanup

#8 was opened as a test-infrastructure issue. It ended having fixed a data-loss bug, two architecture
defects and a user-visible behaviour gap. Budget accordingly.

Per method rule 7, user-visible divergence found on the way is **fixed in the same change**, not
logged for later. Logging it is how divergence persists.

## Background

- The #8 record, which is the evidence for all of the above:
  [`docs/completed/FROZEN-RECALC-TEST-PARITY.md`](completed/FROZEN-RECALC-TEST-PARITY.md)
- Possible overlap worth checking before starting:
  [#12](https://github.com/dwsdolce/guitar-tap-project/issues/12) — restore `TEST-PLAN.md` as the
  tri-platform test definition.
