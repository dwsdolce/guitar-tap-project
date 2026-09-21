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

**F1 — the `tests=` links in the parity map are unreliable. (open — repaired per subsystem)**
`tests=` is a hand-written attribute on a production file's `@parity` tag, so it is a comment, and
rule 3 applies. Against the import graph it does not hold: sixteen `test/*` slugs have no production
group pointing at them, and twenty-six production groups claim no test evidence at all. Some of those
are plainly wrong — `test/field-precision` is "unlinked" while `field-precision.test.ts` imports
`src/precision.ts` and nothing else. This matters beyond tidiness: `doc_coverage.py` derives the
functional-block coverage metric from these links, so the coverage number is only as good as the
attribute. Do not use `tests=` as input to the sweep.

**Repair it at the end of each subsystem, not at the end of the sweep.** Owner's correction,
2026-09-20: the links for a subsystem's slugs are known once that subsystem has been read, and that
is the moment to fix them. Deferring the lot to the end would mean repairing from a script instead
of from knowledge, and would leave `--gaps` and the coverage metric wrong in the meantime. It also
matches the standing convention that a `@parity` change lands in the same commit as the code.

S1 needed no repair — nothing moved slugs. **S2 needed three, and they were missed** on the first
pass, which is the evidence for doing this per subsystem rather than later:

- `modeColors.ts` said `tests=test/mode-colors` after its label and display-name rules moved to
  `test/classify` under the F10 rule.
- `dsp/guitar-modes` carried `tests=test/classify` in Swift and **no `tests=` at all** in Python or
  web, though all three pin the mode bands there.

So the per-subsystem checklist gains a step: after the tests settle, re-read the `@parity` tags of
every production file the subsystem touched, and regenerate. `--check` does not catch this — a
missing or stale `tests=` is not an error, only a silently wrong coverage claim.

**F2 — four `test/*` slugs were not tests at all. (FIXED — Swift `6ead450`, Python `e6e7ddc`, web `363776f`)**

Two were helper modules imported by real tests — `parity-runner`, `self-baseline` — plus
`parity-oracle`, the vendored oracle reader. The fourth, `oracle-sync`, looked like a test because
it lives in a test file and runs in the suite, but the owner's reading settles it: **it is a tool
that is run**, not a test. What it exercises is whether a vendored file is fresh, not what the app
does.

**Why they were treated as tests: the slug prefix is the only signal.** `gen_parity_map.py` decides
on `slug.startswith("test/")` and nothing else — that stamps a group `equivalence = "test suite"`
(line 211), and puts it in the set a production file's `tests=` is allowed to point at (line 351).
These files were given the `test/` namespace because of where they live, not what they do.
`tooling/mint-baseline` and `tooling/capture-probe` already had it right.

**The harm was narrower than first recorded here, and that correction matters.** This entry
originally claimed `--check` counted them as test evidence and that the coverage metric folded them
in. Checked: **no production group links to any of them**, and they are correctly excluded from
`testable`, so no coverage claim was ever inflated. What they actually cost was:

- **Legibility.** Four slugs in the `test/*` namespace that can never have a test, reading as 0/0/0
  gaps. That is exactly what cost time at the start of this sweep — the starting picture reported
  "eight slugs missing an edition" and four of the eight were these.
- **A latent trap.** Being in `test_groups`, a `tests=test/parity-runner` written on some production
  file would have been accepted as valid evidence. Nothing did.

**The fix:** all four retagged to `tooling/*`, joining `mint-baseline` and `capture-probe` at
`equivalence = "review only"`, and excluded from the coverage maths because `tooling/` is not in
`TESTABLE_AREAS`. `test/*` now means exactly one thing — evidence about application behaviour — and
is **39 slugs, not 43**.

**A residual, found by the owner asking why web had a skipped test and the natives did not.**
Fixing the slug did not move the file. `mint-baseline.test.ts` still sat in `test/`, so vitest
collected it on every run and it reported as a permanent skip, held back by a `MINT_BASELINE=1` env
gate. The natives have no equivalent: Python's minter is `Tooling/mint-baseline.py`, which pytest
never sees, and Swift has no self-baseline minter at all (F4). `MINT_BASELINE` was never a
cross-edition convention — it existed **only** because web's minter lived inside the suite and
therefore needed a runtime flag to stop it writing.

It is now `tooling/mint-baseline.test.ts`, outside the `test/**/*.test.ts` glob, with its own
`tooling/vitest.mint.config.ts`, run by the existing wrapper. Vitest 2.x has no `--include` CLI flag
and `--dir` does not override the glob, so a second config is the way to run a file outside the
suite — verified in a scratch sandbox before committing to the approach.

Two things improve. The enablement gate is **deleted rather than obeyed**: the suite cannot load the
minter at all, which is a stronger guarantee than a flag on something already imported.
(`MINT_BASELINE_YES`, the confirm-the-diff flag, remains — it still has to reach the file, and is
what Python spells `--yes`.) And web's default run now reports **zero skips**, like Python's.

**Why bother, for one skipped test.** A standing skip in every run teaches people to scroll past
skips. That is not hypothetical here: F3 skipped *loudly*, on every machine, for months, and nobody
noticed. Leaving one permanent skip is the condition for the next one.

**F3 — the oracle staleness guard was not running anywhere, and the reason was not what it said.
(FIXED — same commits as F2)**

Every repo vendors its own `parity-oracle.json` so its suite runs offline, which is also the failure
mode: the copy can go stale while canonical moves on, and every test keeps passing against
yesterday's numbers. Python and web each wrap `tooling/sync-oracle.sh --check` to catch that. Both
skipped, loudly, with *"CANONICAL ORACLE UNREACHABLE … curl: (56) … 404"*.

**The premise recorded here was wrong.** This entry said the guard was waiting on the hub going
public ([#11](https://github.com/dwsdolce/guitar-tap-project/issues/11)). The owner's correction,
2026-09-20: the requirement was never that the hub be *public*, only that the repositories be
*reachable* — and the hub has been checked out beside the code repos the whole time. The script
simply never looked there. `fetch_canonical` went straight from "no `ORACLE_SRC` set" to curling a
URL, with no middle rung, even though the rest of the toolchain already assumes that layout
(`gen_parity_map.py` resolves the code repos as siblings of the hub the same way).

**The fix:** `fetch_canonical` now resolves canonical in precedence order — explicit `ORACLE_SRC`,
then the hub directory beside this repo, then the published URL. One change, applied to the three
byte-identical copies of the script. **Nothing is fetched or checked out**: if the file is there it is
read, and if it is not, that rung is skipped.

**And it says what it compared against.** Owner's concern, 2026-09-20: reading a directory that
happens to be on disk can give unpredictable results, because a working copy may hold edits nobody
has committed. That is real, though narrow — the hub's oracle only changes when someone re-mints, and
during that window a repo reporting drift is *correct*, since it has not synced yet. The false green
needs a specific sequence: edit the hub's oracle, sync the repos to it, then discard the edit.

Two ways to close it were considered. Reading the hub's committed content with
`git -C <hub> show HEAD:…` removes the risk but adds a git dependency to a script that uses only
`curl` and `cp`, inside a path a test runs. Weighed against how contrived the failure is, that was
over-engineering — the owner's question about what would do the reading is what exposed it.

What landed instead is honest labelling, so a passing check is self-describing:

```
✅ parity-oracle.json is in sync with canonical
   Compared against: …/guitar-tap-project/tooling/parity/parity-oracle.json
   Source:           local working copy, the hub beside this repo
```

A pass against a working copy is a statement about **this machine**; a pass against the URL is a
statement about **the project**. The reader can now tell which they have. The drift path carries the
same line. All three rungs were exercised in a scratch sandbox — in sync, drift (exit 1 with the
diff), and no hub present (exit 2, which is what makes the wrapper skip rather than fail).

Both wrappers now **run and pass** instead of skipping. That is the first time the vendored oracle
has actually been checked for drift in either edition. All four copies — hub, Swift, Python, web —
are identical, so nothing had drifted; the guard simply was not guarding.

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

### S2 — Mode classification (`classify`, `mode-colors`, + `view/dot-layer`)

Status: ✅ **COMPLETE** — all three slugs plus `view/dot-layer` read; four defects found and
fixed (F9–F12). Landed as Swift `a653caf`, Python `8137876`, web `e162237`.

Full suites after the S2 work, all green:

| edition | after S1 | after S2 |
|---|---|---|
| Swift | 534 in 114 suites | **544 in 115 suites**, all passed |
| Python | 633 passed, 1 skipped | **642 passed, 1 skipped** |
| web | 488 passed, 2 skipped | **524 passed, 2 skipped** |

Per-slug:

| slug | Swift | Python | web |
|---|---|---|---|
| `test/classify` | 37 → 43 | 37 → 43 | **8 → 44** |
| `test/mode-colors` | 1 → 5 | 1 → 4 | 3 → 3 |

Four production files changed — `GuitarMode.swift` and `guitar_mode.py` (absolute colours, and
Python's Quadrapole mapping), `modeColors.ts` (the academic-label table and two colours), and
`PeakCard.tsx` (the extended-mode picker group). Two behaviour changes reach users: the mode colours
on every chart, and web resolving academic override labels instead of silently demoting them.

**What S2 says about the sweep.** The opposite lesson to S1's, and worth both. The part flagged in
advance as the substantive risk — `classifyAll`, where #8 found a real bug — turned out **correct in
all three editions**: same algorithm, same bands across all four guitar types, same tie-break. Every
defect was in the periphery nobody was looking at: colours, label resolution, and which slug a rule
was filed under. Two subsystems in, the count spread has pointed at the defects **zero** times:
`test/classify` read 37/37/8 and hid nothing, `test/mode-colors` read 1/1/3 and hid two user-visible
divergences.

`test/classify` back-filled: web 8 → 31, Python 37 → 38, Swift 37 → 38. Web's gap was real and is
closed — it now covers acoustic and classical band classification with Swift's own cases and
frequencies, the band table for all four guitar types, and the `classifyAll` edge cases. Written as
a row list plus a loop, which is the shape Stage 2 moves every case-driven slug to.

Suites after the back-fill, all green — Swift **535** in 114 suites, Python **634 passed, 1 skipped**,
web **511 passed, 2 skipped**. Parity map current at 97 groups, 12 platform-specific, no problems.

One invariant is newly pinned in **all three**: on equal magnitude the **first** peak wins the band.
No edition pinned it before. Verified in each rather than assumed — Swift's `max(by:)` and Python's
`max()` both keep the first maximal element, and web's loop replaces only on a strict `>`. A
tie-break that differed per edition would stay invisible until a real measurement produced a tie, and
would then move which peak is "the Air peak" in one app and not the others.

**The classifier itself is sound, and that is worth recording.** `classifyAll` — the context-aware
claiming algorithm where peaks compete for mode bands, and where #8 found the Generic Top/Back
overlap problem — matches across all three editions. Same ordering by ascending lower bound, same
`max(range.lo, claimedTop + 1)` constraint on Back, same fallback for unclaimed peaks, and the same
tie-break (all three keep the *first* maximal element on equal magnitude). The mode bands match
exactly across all four guitar types:

| type | air | top | back | dipole | ring | upper |
|---|---|---|---|---|---|---|
| generic | 70–135 | 140–260 | 180–300 | 310–460 | 580–880 | 880–20000 |
| acoustic | 90–120 | 150–210 | 210–290 | 360–460 | 620–880 | 880–20000 |
| classical | 80–110 | 170–230 | 190–280 | 330–430 | 580–820 | 820–20000 |
| flamenco | 85–115 | 180–220 | 200–250 | 350–450 | 600–850 | 850–20000 |

So `test/classify`'s 37/37/8 is a **coverage** gap, not a behaviour divergence. Checked one level
down as well: web's `modeBands()` sorts in place, which would corrupt module state if it returned a
shared array — it returns a fresh deep copy per call, and the comment saying so is accurate.

**F9 — the three editions drew three different mode palettes, and only one had a reason. (FIXED)**

Measured, Swift resolved on macOS 26.6.2:

| mode | Swift | Python | web |
|---|---|---|---|
| Air | `#00C0E8` | `#00B7EB` | `#4EA1FF` |
| Top | `#34C759` | `#28A028` | `#5FD07A` |
| Back | `#FF8D28` | `#DC7828` | `#F0A03A` |
| Dipole | `#FF383C` | `#D23232` | `#E0584A` |
| Ring | `#CB30E0` | `#823CC8` | `#B07AD8` |
| Upper | `#8E8E93` | `#828282` | `#9AA6B3` |
| Unknown | `.secondary` ¹ | `#828282` | `#5A6573` |

¹ `NSColor(Color.secondary)` resolves to black in a probe because `.secondary` is a hierarchical
style rather than a plain colour. Treat that cell as unmeasured, not as "Swift draws black".

Web's palette is brightened for its dark chart, which is deliberate, documented, and is what the
theme work formalises. **Python has no such reason** — it is on white, like Swift — and its palette
is its own invention, differing substantially: Ring is `#823CC8` against Swift's `#CB30E0`. Unlike
F8, these never agreed; Python did not drift away from Swift, it never matched.

**Python cannot distinguish Upper Modes from Unknown.** Both are `(130, 130, 130)`. Swift separates
them (`.gray` vs `.secondary`) and so does web (`#9AA6B3` vs `#5A6573`). On the Python chart those
two categories are the same grey — a functional difference, not a palette preference.

Both native tests pin their own edition's values and state in a comment that the editions differ by
design. For web that is true. For Python the comment records the divergence without justifying it.

**The fix**, owner's rule 2026-09-20: *keep the web's value where the difference is the background,
follow Swift where it is not.* Measuring the hues split the table cleanly.

| mode | Swift & Python (light) | web (dark) | |
|---|---|---|---|
| Air | `#00C0E8` | `#00C0E8` | was `#4ea1ff` — a **blue**, 22° from Swift's cyan, not a dark variant |
| Top | `#34C759` | `#5fd07a` | kept — Swift's hue at 1° |
| Back | `#FF8D28` | `#f0a03a` | kept — 5° |
| Dipole | `#FF383C` | `#e0584a` | kept — 7° |
| Ring | `#CB30E0` | `#CB30E0` | was `#b07ad8` — 18° off |
| Upper | `#8E8E93` | `#9aa6b3` | kept — near-neutral, only lightness matters |
| Unknown | `#808080` | `#5a6573` | kept — near-neutral |

Swift's values are now absolute, as in F8, and Python carries them identically. Python changed most:
its whole palette was invented, and Upper Modes and Unknown are no longer the same grey. All three
editions now assert that the seven must stay tellable apart, and name that pair specifically.

Swift's `Unknown` was `.secondary` — black at 50% alpha. Resolved rather than guessed: it composites
to `#808080` on the white chart, and that is the value pinned.

**Mutation-tested with the real defect.** Setting Python's Unknown back to Upper's grey fails two
tests: the table and the distinctness check.

**One inconsistency, deliberately left.** `WoodQuality` pinned the **pre**-macOS-26 values (F8, which
restored Swift's earlier appearance) while `GuitarMode` pins the **post**-26 ones (which preserves
its current appearance). Each followed the decision made for its own case. The owner's call,
2026-09-20: leave it — the theme work restates the whole palette anyway, and levelling it now would
be churn against values that are about to change. Picked up by THEME-SPEC.md, not by #17.

**F10 — the same rules lived under different slugs in different editions, so the counts were not
comparable. (FIXED, and a rule adopted)**

`test/mode-colors` reads 1/1/3. That is not a coverage gap. Web puts three rules in that slug —
colour, abbreviation, display name. Swift and Python put colour there and assert **abbreviation and
display name under `test/classify` instead** (`GuitarModeTests.displayName_*`,
`test_guitar_mode.py::test_*_display_name`). All three editions test all three rules; they disagree
only about which slug owns them.

This is the fifth defect shape from S1 in a second form. There it was one rule under two slugs in one
edition; here it is one rule under different slugs per edition. Both make `--check` and the count
table describe something other than coverage. **Every count in the starting-picture table is suspect
for this reason**, and the sweep cannot rely on them to find gaps — only reading can.

**The rule, adopted 2026-09-20: the canonical edition decides which slug owns a rule.** Where the
editions disagree about filing, the ports move to match Swift. It is mechanical, needs no judgement
per case, and makes the counts honest again as a side effect rather than as the goal. Applied here:
web's label and display-name assertions moved from `mode-colors` to `classify`.

The owner's framing is worth keeping: the counts do not decide *what* gets checked, because every
slug is being read anyway. They matter only for whether the record reads truthfully afterwards.

**F11 — web had none of the academic mode labels, and silently downgraded them on load. (FIXED)**

Swift and Python both offer a second set of override labels in the mode picker, in the acoustical
physics T(m,n) notation, for users who prefer it: `Helmholtz T(1,1)_1`, `Top T(1,1)_2`,
`Back T(1,1)_3`, `Cross Dipole T(2,1)`, `Long Dipole T(1,2)`, `Quadrapole T(2,2)`,
`Cross Tripole T(3,1)`. Both resolve them back to real modes — Swift via
`GuitarMode.fromDisplayName`, Python via `from_mode_string`. The two lists are identical.

Web has neither half. `MODE_BY_DISPLAY_NAME` is built only from the seven current display names, so
`effectiveMode` falls through to `'unknown'`. Measured, not inferred — all seven resolve to
`unknown` in web where both natives resolve them to a mode.

Two consequences. A web user cannot assign an academic label at all, which is a missing feature. And
**a measurement saved in Swift or Python with one of those overrides loads in web as a freeform user
label** — teal user colour instead of the mode colour, and excluded from every surface that asks
"which peak is the Dipole", including the tap-tone ratio and the definitive-peak resolution. That is
a cross-edition data-fidelity difference, not a UI preference.

**The fix**, owner's decision 2026-09-20 — web matches Swift and Python, both halves.
`MODE_BY_ADDITIONAL_LABEL` carries the seven, `MODE_BY_DISPLAY_NAME` folds them in so any edition's
file resolves the same way here, and the picker gained an "Extended modes" group matching the
natives' menu structure (standard modes, separator, extended, separator, Custom).

**F12 — Swift and Python disagreed on what `Quadrapole T(2,2)` means. (FIXED)**

| label | Swift | Python |
|---|---|---|
| Helmholtz T(1,1)_1 | Air | Air | 
| Top T(1,1)_2 | Top | Top |
| Back T(1,1)_3 | Back | Back |
| Cross Dipole T(2,1) | Dipole | Dipole |
| Long Dipole T(1,2) | Dipole | Dipole |
| **Quadrapole T(2,2)** | **Ring Mode** | **Upper Modes** |
| Cross Tripole T(3,1) | Ring Mode | Ring Mode |

One entry in seven. Swift folds Quadrapole into Ring Mode; Python sends it to Upper Modes. Whichever
a user picks, the two apps then disagree about which peak is the Ring Mode peak — which propagates
into the ratio and the definitive-peak resolution.

**The fix**, owner's decision 2026-09-20: Swift is correct; Python and web follow. Quadrapole
resolves to Ring Mode in all three. Mutation-tested — reverting Python to Upper Modes fails exactly
one test, naming the label.

**Neither mapping was tested in any edition.** `fromDisplayName` / `from_mode_string` had no test in
Swift, Python or web, despite being reachable from the override picker in two of them. That is how
the two natives came to disagree, and it is the same shape as F7: a user-facing behaviour that no
edition pinned. All three now cover it — the standard names, each academic label, that every label
the picker offers resolves, and that a freeform label is `unknown` rather than falling through to the
auto mode.

**`view/dot-layer` is what parity looks like, and is the model for the rest. (no finding)**

Recorded because it is the first slug read in this sweep with nothing wrong with it, and because it
already does informally what Stage 2 proposes to do formally.

Ten cases, **DL1–DL10**, numbered identically in all three editions, in the same order, testing the
same rules with the same names: range filtering and inclusive bounds (DL1–DL2), the unknown-mode
filter and its material exemption (DL3–DL5), the dot list being independent of annotation mode,
selection and mode overrides (DL6–DL7), and a user-named out-of-band peak becoming known (DL8–DL10).

The shared case IDs are the whole trick. A reader can line the three files up side by side, and a
missing case is a missing number rather than something to be noticed. Nothing in this sweep has been
easier to verify, and it took minutes rather than the hours the material subsystem took. **Stage 2's
job is to make every case-shaped slug look like this**, with the case list in data rather than
repeated in three files — but the ID scheme alone already captures most of the benefit and costs
nothing.

### S3 — Pitch (`test/pitch`)

Status: ✅ **COMPLETE** — one finding (F13), fixed in all three editions.
Landed as Swift `b973fdf`, Python `33c4899`, web `df2b45e`.

**F13 — `test/pitch`'s 22/22/6 was a difference in SURFACE, not a gap in coverage. (FIXED)**

The widest-looking gap left in the map, and it was not what it looked like. Web's `Pitch` had five
members — `pitch`, `freq`, `note`, `freq0`, `cents` — and its six tests are table-driven over six
frequencies asserting three of them, so on the **shared** surface the editions were comparable. The
natives had three more methods: `pitchRange`, `formattedNote`, `isInTune`.

Searched wider than the exact spelling (`intune`, `formattednote`, `pitchrange`, case-insensitive,
across all Swift and Python app source plus the manual): **none of the three has a call site
anywhere outside its own definition and its tests.** Nine of Swift's 22 tests exercised them. So
roughly 40% of the natives' pitch coverage pinned code the application never calls, and that
inflation was the whole apparent gap.

**Not dead code, though.** Owner's reading: `Pitch` was written as a general package and not all of
it is used by the application — *"They still need testing."* So the question was never whether to
delete them, but whether the **package** is the same in all three editions. Owner's decision: it is.
Web gains all three.

**Porting them found a live divergence, which is the argument for that decision.** JavaScript's
`toFixed` rounds ties **away from zero**; C's `%.0f` and Python's `:.0f` round ties **to even**. A
naive port of `formattedNote` would disagree with both natives at every exact half-cent — `0.5` as
`1` against `0`, `2.5` as `3` against `2`, `-0.5` as `-1` against `-0`. Web now carries an explicit
`roundTiesToEven`, with a test pinning exactly which values the two modes disagree on (only where
the floor is even: `1.5` and `-1.5` agree). Under the other reading this would have shipped silently,
because web would simply never have had the method.

**A second finding inside the first: two of `pitchRange`'s four branches were dead.** The outer
branch on the sign of the cents offset is load-bearing — it decides whether the nearest note is the
lower or the upper bound, and forcing it always-true fails two tests by name. But the inner
`note == 11` / `note == 0` checks, commented as handling octave boundaries, did nothing:
`freq(note, octave)` is `c0 · 2^(note/12) · 2^octave` with no bounds check, so note 12 already
*means* C of the next octave and note −1 already means B of the previous one. Removing them changed
**648 bound values across C0–B8 at −30/0/+30 cents by at most 1.15e-16 relative** — 5.8e-14 Hz at
500 Hz. Eight lines became four in both natives, and the comment claiming credit for the formula's
work is gone from all three files so it does not come back.

**Found by mutation, not by reading.** `pitchRange` had **no test in any edition** despite that
branching. Six were written for it, and disabling the octave crossing still passed all 28 — which is
how the branches were discovered to be redundant. The tests were right to keep: they pin the
observable bounds, which hold however the code computes them.

Tests: Swift 22 → 28, Python 22 → 28, **web 6 → 20**. Suites: Swift **550** in 115 suites, web **539
passed, 0 skipped**.

**Three of the new web expectations were wrong when first written**, and each was checked against the
natives before anything changed: asserting `+2` where all three editions produce `+3` (a frequency
round-trip lands on 2.5000000000003633, genuinely above the tie), asserting `isInTune(f, 10)` true
where all three say false for the same reason, and asserting `toFixed` disagrees on every tie when it
only disagrees when the floor is even. Expected values must come from the canonical edition, never
from running the code under test — and that applies to the tests written *during* the sweep too.

### S4 — Peak detection & analysis (`peaks`, `dsp`, `peak-heal`)

Status: ⏳ in progress. `test/dsp` done (F14). `test/peaks` and `test/peak-heal` not yet read.

**F14 — Python's `test/dsp` tested a second implementation that the app never ran.
(FIXED — Swift `8347ca7`, Python `8c750d0`, web `7fd739e`)**

The most serious finding of the sweep, and the #8 shape at production scale rather than in a test
helper.

`test/dsp` read 10/10/0, which looked like web missing the slug. What it actually was:

| edition | what its `test/dsp` exercised | does the app call it? |
|---|---|---|
| Swift | `TapToneAnalyzer.parabolicInterpolate`, `calculateQFactor` | **yes** |
| Python | `peak_interp`, `peak_q_factor` in `realtime_fft_analyzer_fft_processing` | **no** |
| web | nothing under this slug — the live code was covered indirectly under `test/peaks` | yes |

Python carried a **second, parallel implementation** of both rules: NumPy ports of the
peak-finding section of Swift's `findPeaks`. Searched exhaustively across the whole repo — the
only references outside their own definitions were the module header's parity map and two
docstrings. No caller in `src/`, ever. Meanwhile the pair the app *does* run —
`_parabolic_interpolate` and `_calculate_q_factor`, called from
`tap_tone_analyzer_spectrum_capture.py:1444` and `tap_tone_analyzer_peak_analysis.py:608` — had
**no test at all**.

Swift and web each have exactly one implementation, and it is the live one. The duplicate was
Python-only.

**It had been found before, and half-fixed.** `test_peak_finding.py` carries a note dated
2026-07-19 recording the identical defect in `test/peaks`: *"this file previously did not test the
code it claimed to. F10–F14 exercised `peak_detection` from the FFT layer rather than
`TapToneAnalyzer.find_peaks`."* That was resolved by **relocating** the FFT-layer tests to
`test_fft_peak_detection.py` "outside this parity group" rather than repointing them — which kept
them running against dead code and left the sibling slug, `test/dsp`, with the same defect for five
months. Moving a test that measures nothing does not make it measure something.

**The fix**, per the owner: dead is dead.

- Deleted `peak_detection`, `peak_interp` and `peak_q_factor` (120 lines) and the header lines
  mapping them to Swift's `findPeaks`.
- Rewrote `test_dsp.py` against the live pair, mirroring Swift's F1–F9 case for case. `test/dsp`
  now tests what the app runs in all three editions.
- Deleted `test_fft_peak_detection.py`, whose six tests existed only to exercise `peak_detection`.
  `test/peaks` already covers the live `find_peaks`, which is what the July rewrite established.
- Removed a dead `peak_q_factor` import from `test_frozen_peak_recalculation.py` — **#8's own
  slug**, swept to completion, still carrying a stale import from the module.
- Corrected `test_peak_finding.py`'s history note, which pointed at the file just deleted.
- Added `test/dsp` to web as `test/dsp.test.ts`, 10 cases mirroring the natives. Web's
  `parabolicInterpolate` and `calculateQ` were line-for-line equivalent to Swift's and correct,
  but exercised only *indirectly* through `findPeaks`, which cannot reach the edge-bin and
  flat-top guards. Those are the paths that produce `NaN` or `Inf` and carry it into a saved
  measurement.

**Mutation-proven against the live code**, which the old tests could not have been: removing the
edge-bin guard raises `IndexError` and fails exactly the two edge-bin cases; removing the flat-top
guard raises `ZeroDivisionError` and fails F1 and F5.

**A mis-named test, found on the way.** Swift's `allBinsAboveThreshold_returnsZeroQ` and Python's
`test_F9_peak_with_all_bins_above_threshold_returns_zero` assert nothing about zero. Q is **0.505**
there, not 0 — with a flat spectrum the −3 dB walk runs to both edges, the bandwidth becomes the
whole span, and Q is centre/span. Swift's body checked only "not NaN, not Infinite", with a comment
conceding the value was "not meaningful"; Python's checked only `q >= 0`. Both now pin the real
values and are renamed. **A test name is a comment**, and rule 3 applies to it.

**Naming collision, worth knowing.** The test plans already use `F1`–`F16` as case IDs —
`test_peak_finding.py` has its own `F10–F14`, `DSPTests.swift` has `F1–F9`. The findings in this
document share that space. Always write **`SLUG-SWEEP.md F14`** in source comments, never a bare
`F14`, or a reader lands on the wrong one.

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
