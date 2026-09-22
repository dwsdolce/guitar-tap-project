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

*(S5 later added `test/measurement-amend`, taking it to **40** — the amend rule had no home in any
edition and web had no implementation of it at all. See F20. Measured from the regenerated index,
not counted by hand.)*

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

Status: ✅ **COMPLETE** — all three slugs read. One finding (F14), the most serious of the sweep.
Landed as Swift `8347ca7`, Python `8c750d0`, web `7fd739e`, hub `b6492f6`.

Suites after S4: Swift **550** in 115 suites, Python **643**, web **549** across 51 files, none
skipped anywhere. Python's count **drops** — minus sixteen tests that could not fail, plus ten that
exercise the live code. A suite that shrinks while covering more is the honest outcome; adding only
the web file would have raised the total while Python still tested nothing.

**`test/peaks` — clean. (no finding)**

Recorded because it was read closely rather than skipped, and because it was the obvious place to
expect another F14: `test_peak_finding.py` carries the note from 2026-07-19 saying it "previously
did not test the code it claimed to". That rewrite **did** land. All three editions call the live
methods — `find_peaks` / `findPeaks`, `remove_duplicate_peaks`, `average_spectra` — and the
underscore-prefixed helpers are fixture builders (`_flat`, `_tap`, `_spectrum`) and assertion
helpers (`expect_no_duplicate_peaks`, which checks an invariant over `find_peaks` output), not
reimplementations of production logic.

The full-set-save rule is organised differently in each edition — inside the peak-finding file in
Swift and Python, its own file in web — but all three cover it and all three sit under this slug, so
the counts are not distorted. Now **24/24/26**, the Python figure having dropped by the six dead
`test_fft_peak_detection` tests removed under F14.

**`test/peak-heal` — clean, and the best-built slug read so far. (no finding)**

Five cases, same names, same order in all three editions, with Python and web sharing the **D8**
case IDs. All three reach production — `TapToneAnalyzer.decodeMeasurements`,
`TapToneMeasurement.from_dict`, `decodeMeasurement` — and all three load the **same fixture**,
`dws-2024-umik-1-swift-mac-1784225155.guitartap`, verified byte-identical across the three repos by
checksum rather than by filename. That last check is what F5 was about: matching names over
different bytes is how the material fixtures diverged.

This is the `view/dot-layer` pattern again — shared case IDs make a missing case a missing number —
and it is what Stage 2 is trying to generalise.

**What S4 says about the sweep.** The two slugs that looked safe were safe; the one that looked like
a missing web file was an edition testing code its app never ran. Four subsystems in, the count
spread has pointed at the actual defect **zero times out of four** — and here it pointed at the
wrong edition entirely, since `test/dsp`'s 10/10/0 read as a web gap and the defect was in Python.

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

### S5 — Measurement model & persistence (8 slugs read, 1 created)

Status: ✅ **COMPLETE** — all eight slugs read and every finding resolved. Seven defects fixed
(F15, F16, F17, F19a, F20, F21, F22); F19b deferred to the sorting work and F18 carried into
Stage 2, both by decision. `measurement-codable` (F15), `measurement-type-name` (F16, F17),
`import-persistence` (F19a, F19b, F20, F21, F22), `material-selection` and
`peak-selection-persistence` (clean).

Landed as Python `5091154`, web `9ce7825` (F15–F17), then F19a + F20 + F21 + F22 across all three —
Swift `e962caf`, Python `8a1f2eb`, web `83360a0`.

Suites at close: Swift **560** in 115 suites · Python **657** · web **581** in 52 files, nothing
skipped; parity map 99 groups, no orphans. Every rule added here was mutation-tested — broken
deliberately, confirmed failing, restored.

**Run-review**, tracked separately from sweep completion, since three changes here are user-visible
and tests alone cannot close them:

| change | status |
|---|---|
| Save disabled until the name or notes differ | ✅ owner-verified 2026-09-21 |
| notes trimming on save as well as edit | ✅ owner-verified 2026-09-21 |
| Python minting uppercase UUIDs | ✅ closed by test AND observed — see below |

The UUID row has no UI surface — the id lives in the `.guitartap` file — so it looked unclosable by
run-review. It was closed anyway, by exporting one: the owner renamed a measurement, saved and
exported it, and the file carries `id: 0F350370-57D3-4167-8DFE-EA8F4C72D934`. A new uppercase
measurement id in a real file is only producible by `with_()` minting one, so that single export
run-reviewed F20 and F22 together. Its three peak ids are lowercase — captured before F22 and
correctly not rewritten — and `selectedPeakIDs` still matches them exactly, case included, which
is the invariant that keeps old files valid. Closing it needed a test instead,
and F22 had not written one — it corrected fourteen call sites and pinned none of them, so a single
`str(uuid.uuid4())` added later would have restored the divergence with every suite still green.

`test/uuid-case` now pins it in both ports. Swift needs no counterpart, and the reason is
structural rather than a convention anyone has to remember: every persisted id there is a typed
`UUID` — `TapToneMeasurement`, `ResonantPeak`, `MicrophoneCalibration` — so lowercase is
*unrepresentable*. Measured, not assumed: 5000 draws of `uuidString` gave none, JSONEncoder emits
uppercase, and a lowercase UUID decoded from a file comes back out uppercase. The ports need a
guard because they store ids as strings, where the rule lives in a call site and one careless line
breaks it. A Swift test would only assert that Foundation is Foundation. Two cases each, and the second is the one that matters: the helper mints uppercase,
**and no module mints outside the helper** — a source scan, because the case test alone says
nothing about a direct call added elsewhere.

Writing it found the divergence F22 had left behind: web uppercased measurement ids but minted
calibration ids as raw `crypto.randomUUID()`, so moving Python to uppercase had left web the only
edition disagreeing on a field Swift and Python both uppercase. Web now mints everything through
one helper, `src/measurement/newId.ts`, mirroring Python's `utilities/new_uuid.py` — including
`rowKey`, which is library-local and would not strictly need it, because one rule with no
exceptions is cheaper to keep true than one rule and a list of places it does not apply.

**Format checks that passed**, recorded so they are not redone:

- All three editions use the **same fixture** for this slug,
  `contreras-classical-1774731564.guitartap`, verified byte-identical by checksum across the three
  repos — not merely the same filename. That is the F5 check.
- Decoding it gives **identical values** in Python and web: 44 peaks, the first eight frequencies
  agreeing to 5 dp, `numberOfTaps` 10, `peakMinThreshold` −78, `tapDetectionThreshold` −64,
  6 selected, `annotationVisibilityMode` "selected".
- A decode→encode round-trip in web preserves the format: top-level `measurementType` and
  `guitarType` survive (web stores them on the snapshot and re-derives on write — "derive, don't
  duplicate", documented in `types.ts`), `peakThreshold` is rewritten as the canonical
  `peakMinThreshold`, and `hysteresisMargin` is dropped. That last one is correct in all three: it
  is an analyzer constant (3.0), absent from Swift's `CodingKeys`, and `encode.ts` documents "no
  hysteresisMargin/maxPeaks" as deliberate. It is a legacy field from an older writer.

**F15 — a derived label was being carried through as if it were data. (FIXED)**

Every edition writes a per-peak `modeLabel` into the saved file. The precedence differs:

| edition | precedence for a guitar peak |
|---|---|
| Swift | `override` → `classifyAll` → `.unknown` |
| Python | `override` → `classify_all` → `"Unknown"` |
| **web** | `override` → **`p.modeLabel`** → `classifyAll` → `unknown` |

Web inserts the **previously-decoded label** between the override and a fresh classification
(`encode.ts:62`). The natives always reclassify. Swift's own comment states the intended rule:
*"Resolve the mode label: user override > auto-classify > plate/brace role"* — two rungs, not
three.

**Measured, same input to all three.** Two classical peaks in the Top/Back overlap, the stronger
carrying a stale `"Back"` from an older save:

| peak | Swift / Python | web |
|---|---|---|
| 210 Hz, −18 dB, stale `"Back"` | **`Top`** | **`Back`** |
| 220 Hz, −26 dB, no stale label | `Back` | `Back` |

`classifyAll` gives the stronger overlap peak **Top** in every edition, so the natives write Top and
web writes the stale Back.

**It is self-perpetuating.** Web reads `modeLabel` on decode and prefers it on encode, so once a
label is stale it survives every subsequent web save and no reclassification dislodges it. The
reachable path is ordinary: open a saved measurement, change anything that moves the
classification — Peak Min dropping a competing peak, or the guitar type — and save.

**Why it survived: Swift is the only edition that tests the rule.** Its `MeasurementExportModeLabel`
suite covers exactly the two cases that would catch this — overlap-zone peaks receiving distinct
labels, and override priority. Python asserts one fixture peak reads `"Top"`
(`test_measurement_codable.py:852`); web asserts the same on decode and encode. Neither exercises
the precedence, and neither would fail if it were wrong.

Same shape as F7 and F14: a rule the canonical edition pins and the ports do not, in code the ports
implement differently.

**It was wider than the writer.** Tracing every read of the stored label found the same mistake on
the display side, and in a second edition:

| edition | display | export |
|---|---|---|
| Swift | `override → classifyAll` | `override → classifyAll` ✓ self-consistent |
| Python | `override → mode_label → classify_all` | `override → classify_all` ✗ |
| web | `p.modeLabel ?? 'Peak'` | `override → p.modeLabel → classifyAll` ✗ |

Only Swift had display and file agreeing. Python's detail view could show a label its own writer
would never save. Web's detail view was weakest of all — no override check and no classification, so
a file carrying no `modeLabel` showed **"Peak"** where Swift classifies and shows "Top".

**What settled it.** `modeLabel` is not stored state. Python's own documentation says so: *"an
export-only convenience that Swift injects only for the top-level `peaks` array… Python-only field:
`mode_label` carries the resolved mode string **injected at serialisation time**. It is not part of
the Swift struct."* It is output, recomputed every write by design. Preferring a decoded copy
inverts that — and web's own `types.ts` states the principle for `measurementType` two files away:
*"derive, don't duplicate, since a stored copy can fall out of sync."*

The web comment claimed the code resolved the label *"exactly as the Swift writer does"* while
adding a rung Swift does not have. A comment asserting parity is still just a comment.

**The fix**, owner's decision — make all three handle it the same, with Swift as the target since it
is the only self-consistent one. One rule, `override → classify`, used by **both** display and
export in every edition, with the stored label as output only:

- **Swift** — no change; already correct.
- **Python** — `measurement_detail_view.py` drops the `peak.mode_label or` rung.
- **web** — `encode.ts` drops the rung; `MeasurementDetail.tsx` resolves through a new
  `measurementPeakModeLabels()` in `fromLive.ts`, built on the `effectiveMode` resolver this
  codebase already documents as the one place every "which mode is this peak, really" surface
  should go through. The PDF path already derived correctly and needed nothing.

**Verified on the exposing case**, which previously gave `Back`/`Back`:

```
encode   A="Top"  B="Back"     ← matches Swift and Python
display  A="Top"  B="Back"     ← matches the file
```

**Mutation-proven in both ports.** Reintroducing the rung fails `a STALE carried-through label does
not win` in Python, and in web that plus `the displayed label matches the written one` — the second
catching the display/file split specifically. Tests added in both; Swift already had its two.

**F16 — `test/measurement-type-name` drifted three ways: six shared cases, three sets of extras.
(FIXED)**

Read because 14/9/6 was the widest spread left in S5 and because Python's test imports a **view**
module (`views.measurements.measurement_detail_view._type_name`) where the slug's production anchor
is a model — the signature of F14.

**It is not F14.** Python testing a view function is correct here: Swift's equivalent is a view
function too, `MeasurementDetailView.measurementTypeName`, and Python's docstring says so and quotes
it. Each edition tests its own real implementation of the same rule; the layer differs because the
implementations differ. Checked the underlying data as well — the short-name tables are **identical**
in all three (`Generic`, `Acoustic`, `Classical`, `Flamenco`, `Plate`, `Brace`).

What is there is ordinary drift. Six cases are shared by all three — brace and plate resolving from
`longitudinalSnapshot`, guitar from `spectrumSnapshot`, `spectrumSnapshot` winning over
`longitudinal`, comparison short-circuiting before any snapshot lookup, and the em-dash fallback.
Then each edition grew extras the others never received:

| case | Swift | Python | web |
|---|---|---|---|
| the six shared resolution cases | ✓ | ✓ | ✓ |
| `everyTypeResolvesToItsShortName` — the 6-type table | ✓ | — | — |
| material flag resolves from the same snapshot | ✓ | — | — |
| unrecognised snapshot type → em-dash | — | ✓ | — |
| `None` snapshot type → em-dash | ✓ | ✓ | — |
| **loaded measurement still resolves** | — | ✓ | — |

**The last row is load-bearing and only one edition has it.** Python's
`test_loaded_measurement_still_resolves` exists because of a real defect its docstring records:
`_type_name` read the top-level `measurement_type` field, which is deliberately not set when a
measurement is created, so the Details pane showed "—" for every measurement saved in the current
session and corrected itself only after an app restart re-read the file through `from_dict`. In the
docstring's own words: *"That session-scoped behaviour is why no test caught it."*

Neither Swift nor web pins that. Both resolve from the snapshot today, so neither is broken — but
the regression that motivated the test is unguarded in two of three editions, and it is precisely
the kind that passes every test and fails in the user's hands.

**The fix: level the cases.** No production change was needed for F16 itself — the implementations
and the short-name tables already agreed. Counts went **14/9/6 → 14/10/15**.

- **web** gained the 6-type table, the unrecognised-type fallback, the undefined-type fallback, and
  the loaded-measurement regression. Writing that unrecognised-type case is what exposed **F17**, a
  genuine behavioural divergence — an argument for levelling cases even where no defect is suspected.
- **Python** gained the 6-type table.
- **Swift needed nothing, and that is a finding in itself.** Both cases it appeared to lack are
  *structurally unreachable* there. An unrecognised type cannot be constructed — `snap()` takes a
  typed `MeasurementType?`, and a bad string from a file decodes to `nil`, which
  `nilSnapshotTypeFallsBackToEmDash` already covers. And the loaded-measurement regression cannot
  happen: Swift has no stored top-level `measurementType` to read, only a **write-only**
  `CodingKey` encoded from the snapshot (`TapToneMeasurement.swift:858`). Sweep rule 2 applies — a
  case that cannot occur is not a gap, and forcing a test for it would have pinned nothing.

**One row was a filing difference, not a gap.** Swift tests the material flag
(`materialFlagResolvesFromTheSameSnapshot`) in this slug; both ports test theirs — `is_material`,
`isMaterialMeasurement` — under `test/material-selection`. All three cover the rule. That is the F10
shape, and by the rule adopted there the canonical edition decides the filing, so the ports' copies
belong here. Left as-is for now: it is pure relocation with no coverage change, and worth doing in
one pass at the end rather than slug by slug.

**F17 — web showed an unrecognised measurement type verbatim; the natives show an em-dash.
(FIXED)**

| edition | an unrecognised type in the snapshot |
|---|---|
| Swift | `resolvedMeasurementType?.shortName ?? "—"` → **`—`** |
| Python | `MeasurementType(...)` raises, caught → **`—`** |
| web | `(raw ?? '—')` → **the raw string**, e.g. `Sousaphone` |

Swift's contract is stated on `TapToneMeasurement.measurementTypeShortName`: *"Acoustic / Classical
/ Flamenco / Generic / Plate / Brace / Comparison — or '—' when no snapshot carries a type."* Six
names, Comparison, or an em-dash. Nothing else.

Narrow but user-visible: it needs a file whose snapshot carries a `measurementType` none of the six
match — a foreign writer, a corrupted field, or a future type opened by an older build. Web printed
that string into the Details pane where both natives print `—`.

**Found only by levelling F16's cases.** The unrecognised-type case existed in Python alone, so no
test in any edition compared the three. Writing the missing case into web is what surfaced it —
which is an argument for levelling cases even when no defect is suspected.

**Decided: web follows the natives.** Two reasons, the second the owner's and the more durable:
Swift is canonical and the em-dash is the documented contract; and **the natives have the larger
installed base**, so where either edition could move, the one with fewer users should. Changing the
natives' displayed label would touch more people for no gain.

There is a real argument the other way — printing the unknown string tells the user what the file
actually said, where an em-dash hides it. Recorded because if that is ever wanted, it should be
adopted in all three rather than kept as a web-only difference.

**test/material-selection and test/peak-selection-persistence — read, no defects. (no finding)**

`test/material-selection` is 1/1/1 and the single case is well-built in all three: a **genuine
iPad-corrupted file** as the fixture (`plate-umik-1-3-tap-swift-ipad-1784314709.guitartap`, verified
byte-identical across the three repos), preconditions asserted — material, three peaks present, the
corrupt aggregate holding only the cross peak — then the heal, `effectiveSelectedPeakIDs` resolving
to all three. One test, but it pins the read side of the rule against real corrupt data rather than
a constructed one.

The save side — material persisting the full peak set, never the live aggregate, which is what stops
the corruption recurring — is implemented and commented at
`TapToneAnalyzer+MeasurementManagement.swift:349`. Its coverage belongs to the persistence slugs
rather than here.

`test/peak-selection-persistence` is 4/4/3, and the missing web case is **filing, not a gap**. Swift
and Python each pin four: automatic re-selects a revealed Air, manual does not, a legacy file
defaults to manual, and the flag round-trips. Web pins persistence in this slug and the flag's
*effect* under `test/frozen-peak-recalc` — the auto path leaving the flag false, the manual
carry-forward by ±5 Hz, re-selection from the stable frequency cache, and a deselected peak staying
deselected across a Peak Min sweep. The behaviour is implemented (`tapToneAnalyzer.ts:667`,
commented as mirroring Swift's `applyFrozenPeakState` branches) and it is tested.

**Three instances of the F10 shape now, which makes it the rule rather than the exception:**

| rule | Swift files it under | the ports file it under |
|---|---|---|
| mode abbreviation / display name | `test/classify` | `test/mode-colors` (web) |
| material flag | `test/measurement-type-name` | `test/material-selection` |
| selection flag's effect | `test/peak-selection-persistence` | `test/frozen-peak-recalc` (web) |

Every one is covered in all three editions. What differs is where it is written down — and each
makes a count read as a gap in an edition that is not short. Two of the four thin-looking web slugs
examined in S5 so far have been this rather than missing coverage.

**F18 — case-level drift is endemic, and S5 is the measurement that shows it. (RESOLVED —
carried into Stage 2)**

All eight S5 slugs were read; only two have the same cases in all three editions. The
implementations agree in every case, so **no defect follows** — what follows is that the editions
pin different things, so a change that breaks one edition's rule can pass in another.

The owner's call: level them in Stage 2 with the shared case lists rather than by hand now, since
doing it by hand is Stage 2's work without Stage 2's mechanism and would be redone when the shared
lists land. The measurement, the per-slug detail and the reasoning are carried forward under
[Stage 2 → Carried in from Stage 1](#carried-in-from-stage-1) so they are not lost with this
section.


**F19a — web destroys the dataset UUID on import, and launders it into every file it exports.
(FIXED)**

Found while reading `test/import-persistence` (3/3/6), **filed wrongly twice**, and the corrections
are the useful part.

*First filing:* "equivalent behaviour by different mechanisms, no defect." Wrong — the standing rule
is that an architectural divergence is fixed, not logged, and "no observable difference today" is
not the test for one.

*Second filing:* positional-vs-id-keyed addressing, recommending the natives adopt web's id-keyed
model. Also wrong, and worse, because a future reader would have acted on it. Working through what
an `id` actually **is** showed the recommendation was backwards. Two facts settle it:

- In Swift the measurement `id` is a **write-only field**. Sweeping all 229 `.id` references in the
  app target, the only four touches of `TapToneMeasurement.id` are: assign in `init`, copy in
  `with()`, encode, decode. Nothing looks a measurement up by it. `Identifiable` is declared and
  never exercised for this type. (`ResonantPeak.id` is a different id and *is* load-bearing.)
- Its documented contract, *"Stable unique identifier"*, is false in the store: import copies the
  file's id verbatim, so a duplicate import gives two rows with one id. Positional addressing
  exists **because** of that, so the two cannot be separated.

The owner's decision: the id identifies a **dataset**, never a row — multiple loads of one file are
allowed, so an id can never address a row. Rows are addressed positionally in the natives (their
library *is* an ordered array) and by an explicit row handle in web.

**What was actually broken.** Web overwrote `id` at import (`parsed.map(m => ({...m, id:
newMeasurementId()}))`) and writes `id` on export, so **any file passing through web had its
identity replaced on the way out**. Files already exported that way are not recoverable. Web did not
choose this: IndexedDB `createObjectStore({ keyPath: 'id' })` makes a duplicate key impossible, so
re-iding was the only way to get the natives' append semantics. The storage engine forced it.

Honest about the urgency: **nothing reads the measurement id in any edition today**, so the present
observable harm was zero. The reason to fix it now is that the loss is cumulative and irreversible —
every session adds files whose identity is gone, and the id has just acquired a meaning.

**Fix.** Web's storage key became an explicit `rowKey`, freeing `id` to mean the dataset identity in
all three editions:

| | dataset identity | row handle |
|---|---|---|
| Swift / Python | `id`, preserved across export/import | array position |
| web (before) | **destroyed at import** | `id` |
| web (after) | `id`, preserved | `rowKey` — minted per insert, never written to a file |

One rule in `saveMeasurement` carries it: `rowKey: m.rowKey ?? newRowKey()`. A parsed or freshly
captured measurement has no row handle, so it lands as a new row; a stored one keeps its handle, so
an edit replaces in place. That single line gives duplicate-import-appends, edit-replaces and
heal-on-read-writes-back, with no special cases.

IndexedDB `keyPath` is immutable, so this needed a schema bump: `VERSION` 1→2 with an
`onupgradeneeded` that reads the records, drops the store, recreates it keyed by `rowKey`, and
writes them back with `rowKey` set to their old `id`. The key *values* are unchanged, so nothing
re-orders and nothing can collide. Migrated rows have `id == rowKey`, which is honest — their
original dataset id was destroyed long ago. Upgrades are transactional, so a failure leaves the
database at v1 rather than half-migrated.

Two things the migration surfaced that were already latent: `openDB` had **no `onblocked` handler**,
so a second tab holding the old version would have hung the panel silently with no error (added);
and the import logic lived in the panel while `test/import-persistence` **re-stated it** rather than
calling it — so the panel could have changed without a case failing. The storage side is now
`store.importMeasurements`, which the panel and the tests both call. That is the F14 shape found
again, in the test for the slug that found F19.

**F19b — row identity and addressing. (DEFERRED — no issue yet, nothing to do)**

Not a defect. `MeasurementsListView` iterates `savedMeasurements` directly, unsorted and unfiltered,
so the view index *is* the storage index. It matters only for a feature that does not exist yet.

The natives address rows positionally at four sites, not two: `updateMeasurement(at:)`,
`deleteMeasurement(at:)`, `ForEach(Array(...enumerated()), id: \.offset)` and
`selectedCompareIndices: Set<Int>`. The `ForEach` one is the tell — SwiftUI rows are identified by
array offset precisely *because* ids can duplicate, so duplicate ids have already propagated out of
the store into view identity and selection state.

Design input for the sorting/manual-reordering work, recorded so it is not re-derived:

- **Sort is a lens, not a commit.** Persist the *criterion*, never the resulting order. Every
  criterion is derivable from data already stored — `timestamp`, `measurementName`, storage order —
  so order can never drift from the data. "Restore what was in the file" is then just "clear the
  sort", and costs nothing: the natives' array order and web's `savedAt` are both already durable.
- **Manual reordering is the case that needs stored order.** An arrangement is not derivable. In the
  natives the storage array *is* the arrangement (`move(fromOffsets:toOffset:)` + persist — no new
  field, and the whole file is rewritten on every change anyway). Web cannot reorder an array
  because it has no array; an `order` field *inside* each record would mean a drag rewriting dozens
  of multi-MB records, so the order belongs in **one small separate record** holding row handles in
  display order — one write per move, independent of library size.
- That order record can drift from the record set after a crash mid-write; reconcile on load (drop
  keys with no record, append records with no key). The natives cannot have this failure.
- The arrangement travels between editions implicitly as the **array order in the `.guitartap`
  file**. No format field, and the row handle still never leaves the app.
- Open for the feature, not for the sweep: does a manual move permanently discard the
  as-first-imported order?

**F20 — an edit did not change the measurement's id. (FIXED, all three)**

Name and notes are part of a measurement's **data**, not annotations on top of it, so an amended
measurement is a different dataset and must carry a different identity. All three editions preserved
the id through an edit, which meant two different datasets could share one id — the id lying about
exactly the thing it exists to express.

This was first classified as a new requirement rather than a defect, and that was wrong: fixing F19a
alone would have had web faithfully preserving a value that was already untrue. The two are one
change, and there is a mechanical proof of it — in web the edit fix is **impossible** without the
row-key split, because `commitEdit` does a `put` keyed on `id`, so a new id would write a second row
and orphan the first. A duplicate on every rename.

The rule is now **same `id` ⟺ same content**, and it holds in both directions:

- Save (fresh capture, *or* a loaded measurement) stamps a new timestamp, so it is new content and
  correctly gets a new id.
- Editing name or notes changes the content, so it mints a new id. `timestamp` is preserved: it
  records when the tap was captured, which amending does not change.
- Importing the same file twice gives identical content, so the rows correctly share an id — and
  editing either one ends that.

A Save that changes *nothing* would break the rule by giving unchanged content a new identity, so
the owner's answer was to make it unreachable: **Save is disabled until the name or notes actually
differ**, in all three editions, so saving an untouched form and cancelling it are the same action.

**Where the rule lives.** It was first written as a private predicate inside each of the three
views — untestable, and restated three times, which is precisely the divergence this sweep exists
to remove. The codebase already had the answer in `isValidName`: *"Single source of truth so all
three platforms — and their tests — agree; a view must bind its Save button to this, never
re-implement it."* The amend rule now follows it, as a new group:

| | rule | amend |
|---|---|---|
| Swift | `TapToneMeasurement.isAmended(measurementName:notes:)` | `with(measurementName:notes:)` |
| Python | `is_amended` | `with_` |
| web | `isAmended` | `amendMeasurement` — **new**, web had no counterpart at all |

`model/measurement-amend` / `test/measurement-amend` (map: 97 → 99 groups). The cases moved out of
`test/measurement-codable`, which is about serialisation and was never where an identity rule
belonged; web's absence there is why the missing `amendMeasurement` went unnoticed. Each edition's
edit view now supplies normalized values and binds to the shared rule.

**F21 — the two user-entered fields normalized three different ways, and one edition disagreed
with itself. (FIXED, all three)**

Found implementing F20's Save gate, because the gate compares *stored* values and so depends on
this:

| | save path | edit path |
|---|---|---|
| Swift | no trim | no trim |
| Python | **no trim** (`notes or None`) | **strips** |
| web | trims | trims |

Names were already trimmed everywhere; notes were not. Python's two paths disagreeing is a real
defect and F20 would have exposed it: save notes with surrounding whitespace, reopen the edit
dialog, and Save lights up immediately — because the dialog normalized while the stored value had
not — offering to "amend" a field nobody touched, which under F20 mints a new id.

The owner's call was that all three trim, with Swift changing. `normalizedNotes` now sits beside
`normalizedName` in the model in each edition, and **every** path that stores notes goes through
it: Swift's two save call sites and its edit sheet, Python's `create` factory (which funnels all
six of its save call sites), and web's three `fromLive` builders. A test in each edition pins that
the two fields normalize identically, since that is the property the Save gate rests on.

**F22 — Python minted lowercase UUIDs where Swift and web mint uppercase. (FIXED)**

Swift's `UUID().uuidString` is uppercase and web mints `crypto.randomUUID().toUpperCase()`
explicitly to match it. Python minted `str(uuid.uuid4())` — lowercase — at 14 sites across 7 files.

Harmless until F20 gave `id` a meaning. Swift uppercases any UUID it decodes while the ports
preserve what the file holds, so nothing normalised it back: the same measurement exported from
Python and from Swift differed by case in the field that identifies a dataset, and anything
comparing ids as strings — which is how the web store and every test does it — would read them as
two different things.

Python now mints through one helper, `utilities/new_uuid.py`, uppercase. Case has never affected
correctness *within* a file, since a file's internal references agree with its own ids whatever
their case, so existing files stay valid and are not rewritten.

**Format note for the Android port.** `id` and `timestamp` are the `.guitartap` format's **only
mandatory fields** — every other field in Swift's decoder is `decodeIfPresent`. Swift rejects a file
missing either one; measured, it throws on a missing key, `""` and `null` alike, and accepts a
lowercase UUID (uppercasing it on read). The two ports are more tolerant — Python mints a
replacement for an absent key, web falls back to `''` — but no edition can *produce* such a file, so
those branches are unreachable and were deliberately left alone rather than levelled. Copy Swift's
rule when writing a new decoder.


### S6 — Analyzer state machine (11 slugs)

Status: ⏳ **IN PROGRESS** — 6 of 11 slugs read.

**RESUME HERE.** Audit position as of 2026-09-21. This table records only **what the reading
produced** — a finding number, or "clean" where none was filed. Each finding's status lives in the
finding and nowhere else; do not restate it here.

| slug | read? | produced |
|---|---|---|
| `effective-peak-id` | ✅ | coverage clean — 6/6/0 is structural, both halves of the claim verified; **F23** |
| `comparison` | ✅ | **F24** |
| `button-enablement` | ✅ | clean — 13/13/13 (F24's fix made `displayMode` required) |
| `measurement-complete` | ✅ | **F25**, **F26** |
| `annotation-state` (44/42/32) | ✅ | **F27**, **F28** |
| `status-message` (12/12/16) | ✅ | **F29**, **F30** |
| `tap-count-change` (6/6/11) | ☐ | |
| `state-invariants` (7/7/7) | ☐ | |
| `scenario-trace` (4/4/4) | ☐ | |
| `session-pre-roll` (4/4/4) | ☐ | |
| `start-tap-race` (4/4/4) | ☐ | |

The unread rows' counts are Swift/Python/web. `annotation-state` is the largest and the likeliest to
show F10-shape filing differences; `status-message` and `tap-count-change` are the two where web
carries more cases than the natives.

Method reminders that earned their place in S6 so far: counts mean nothing in either direction
(`effective-peak-id` 6/6/0 was correct, `measurement-complete` 8/13/8 had the LARGEST suite missing
two rules); verify a test file's own claims about why an edition differs (rule 3 applies to test
headers too); and "behaviour is equivalent today" is not a reason to close an architectural
divergence — that reading mis-filed F19 and nearly mis-filed F24.



| slug | Swift | Python | web |
|---|---|---|---|
| `annotation-state` | 44 | 42 | 32 |
| `button-enablement` | 13 | 13 | 13 |
| `comparison` | 20 | 32 | 7 |
| `effective-peak-id` | 6 | 6 | 0 |
| `measurement-complete` | 8 | 13 | 8 |
| `scenario-trace` | 4 | 4 | 4 |
| `session-pre-roll` | 4 | 4 | 4 |
| `start-tap-race` | 4 | 4 | 4 |
| `state-invariants` | 7 | 7 | 7 |
| `status-message` | 12 | 12 | 16 |
| `tap-count-change` | 6 | 6 | 11 |

**`test/effective-peak-id` (6/6/0) — web's absence is structural, and the claim checks out.
(clean)**

The test file asserts that web needs no counterpart because `identifyMaterialPeak` stores exactly
one peak per phase, so there is no intermediate auto-selection to resolve against, and web's
`selectedLongitudinalPeakID` is a persisted FILE field rather than live analyzer state. Rule 3 says
verify rather than accept, and both halves hold: `identifyMaterialPeak` returns one peak or null
into `matPeaks.longitudinal`, and every reference to `selectedLongitudinalPeakID` in web is in
`measurement/` — types, `fromLive`, `decode`, `encode`, and the detail view. **None in
`state/tapToneAnalyzer.ts`.** Nothing to test, and no gap.

**F23 — six one-line pass-throughs, six summary lines describing resolution logic that was deleted.
(FIXED — both natives)**

`effectiveLongitudinalPeakID` and its two siblings are now `selectedPhasePeak?.id`. The layers were
removed on 2026-09-20 — a user-override tier whose UI went in April 2026, and an `autoSelected*`
arm that was unreachable. The bodies are correct and identical across editions. The prose is not:

| property | summary line claims |
|---|---|
| Python longitudinal | "applying **two-layer** priority" |
| Python cross | "applying **three-layer** priority" |
| Python flc | "applying **three-layer** priority" |
| Swift longitudinal | "applying **two-layer** priority", and "the **three** underlying sources" |
| Swift cross, flc | "Priority order:" followed by **one** item |

Siblings disagreeing about identical code — two-layer here, three-layer there — is the signature of
successive edits that fixed some comments and not others. Note *which* part is wrong: the detailed
body text in both editions explains the removal accurately. It is the **one-line summary** that
lies, and that is the line an IDE tooltip and a generated doc page show, and the line a reader sees
first. No behaviour is affected.

All six now state what the property is — the phase's identified peak, or `nil`/`None` before the
phase finalises — with the longitudinal one carrying the explanation of what the removed layers
were, and its siblings pointing at it. The Python cross and FLC docstrings were worse than the
summary line: they documented the whole removed chain, `userSelectedCrossPeakID >
selectedCrossPeak.id > autoSelectedCrossPeakID`, naming symbols that no longer exist in either
edition. Comments only, so there is nothing to run-review; Swift **560** and Python **664** green.

**F24 — web keeps the display mode in the VIEW. The natives keep it on the analyzer.
(FIXED — web, run-reviewed; the general restructure remains #1)**

Surfaced by `test/comparison` (20/32/7), but this is not a `comparison` finding. Display mode is
S6's spine, and the count spread is a symptom.

| | display mode | lives in | invalid states | transitions unit-testable |
|---|---|---|---|---|
| Swift | `AnalysisDisplayMode` enum — live / frozen / comparison | the analyzer | **unrepresentable** | yes |
| Python | mirrors it | the analyzer | **unrepresentable** | yes |
| web | `displayModeIsComparison: comparison != null` | **React state in `App.tsx`** | representable | **no** |

**This is the only S6 state web left in the view.** Everything else it moved: `isMeasurementComplete`
(29 analyzer references), `currentTapCount` (30), `isDetecting` (18), `statusMessage`,
`numberOfTaps`. And `state/buttonEnablement.ts` is a *pure function extracted precisely so the view
and the test can share one rule* — which is why `test/button-enablement` is a clean 13/13/13. Web
already knows how to do this. Display mode is the piece it did not do.

Do not read "behaviour is equivalent today" as mitigation. That reading is what got F19 filed wrongly
the first time, and the same three consequences follow here:

**1. The transitions cannot be tested.** Swift drives `sut.loadComparison(…)` and reads
`sut.displayMode`. Web's equivalents are `setComparison(…)` and `onLoadMeasurement(…)` — a React
state setter and a component callback inside `App.tsx`, unreachable from a unit test. Swift's five
transition cases, the axis-union case, the empty-array case and three multi-tap-reset cases have no
web counterpart and cannot be given one while the state lives where it does.

**2. The invariant is held by convention, and nothing checks it.** Swift's enum makes "frozen AND
comparison" unrepresentable. Web reaches the same exclusivity by remembering to clear at **eight**
`setComparison` call sites — the guitar load path does it twice over, at `App.tsx:1054` and `:1074`,
which is what belt-and-braces looks like when nothing enforces a rule. Every path was checked and
every one is correct today. **No test asserts any of it.** Delete any one of the eight and the suite
stays green.

**3. It has already leaked into a rule that should not know about it.** Because the button rule
cannot read display mode from the model, it takes it as an argument — and an *optional* one, since
most callers and tests have no display mode to pass:

```ts
displayModeIsComparison?: boolean
...
if (s.displayModeIsComparison) newTapDisabled = false
```

During comparison New Tap must stay **enabled** — it is how the user leaves. Omit the optional
field and it is `undefined`, falsy, the normal rule applies, New Tap is disabled, and the user is
trapped in comparison with no way out. There is one production caller and it passes the field
correctly; the type system permits a second that does not. The natives cannot have this bug,
because there is no argument to forget.

**Recommendation: move display mode onto web's analyzer**, as a three-state value, and let the
button rule read it rather than receive it. That is the only option of the three that makes the
invalid state unrepresentable, restores the transition tests, and removes the optional argument.
`buttonEnablement.ts` is the proof the pattern works in this codebase — extracted, tagged, tested,
13/13/13.

This is [#1](https://github.com/dwsdolce/guitar-tap-project/issues/1), the view-layer restructure,
arriving with a concrete instance and a measured cost. Scope is the owner's call; whether it is a
divergence is not.

Done as recommended — owner's call, 2026-09-21: "match swift/python… full move." Web's analyzer now
owns a three-state `DisplayMode` (`'live' | 'frozen' | 'comparison'`) with `comparisonEntries` and
`showingMultiTapComparison` beside it, an `isSavedMeasurementComparison` getter, and six transition
methods — `loadComparison`, `loadComparisonRecord`, `clearComparison`, `setMultiTapComparison`,
`enterFrozen`, `enterLive` — with `loadMeasurement` and `clearResult` wired to them internally, so
"frozen AND comparison" is unrepresentable rather than merely unreached. `buttonEnablement.ts` reads
the mode instead of receiving it: the optional `displayModeIsComparison?` is now a required
`displayMode`, and the trap-the-user bug it permitted cannot be written. Web suite 593, run-reviewed
across Compare, load-during-comparison, New Tap out of comparison, and multi-tap.

The **general** restructure stays open as #1. What closed here is display mode; F26 immediately
found the next instance of the same shape, in the same subsystem.

**The fix was incomplete, and F26's run-review found it.** Owner, 2026-09-21: load a plate
measurement, compare two guitar measurements, press New Tap — the overlay stayed on screen with a
fresh capture arming underneath it. Loading the plate measurement set the type to plate, so New Tap
took the material path, `onMaterialNewTap` → `startMaterial()`, and `startMaterial` never returns to
live. The transition was wired into `clearResult()` only.

Neither native can have this bug, because neither has a material-specific start. Swift's New Tap
button goes to `requestStartTapSequence()` → `startTapSequence(initialPhase:)`; Python's `_on_new_tap`
goes to `restart_tap_sequence()` → `start_tap_sequence(initial_phase)`. One method, guitar and
material alike, clearing the comparison unconditionally — Python's even says so: *"For plate/brace,
start_tap_sequence() already transitions material_tap_phase … no separate start_plate_analysis() call
needed."* Web's fork is what made the omission available: state a start must reset now has to be
remembered twice.

Underneath it is a fourth instance of the same shape. Web **already has** `startTapSequence()` on the
analyzer, already mirroring the natives, and production does not call it. Its doc comment explains
why: the engine owns arming and "may be stopped there, so they must clear WITHOUT arming; that
clear-without-arm split is the engine/analyzer divergence tracked separately." Another accurate
description of a defect written down as a design.

**And the reason given is stale.** Both arming entry points open with
`if (!this.running || this.state === 'capturing') return` — arming a stopped engine is already a
no-op, so "must clear without arming" is not a constraint the code imposes (CROSS-EDITION rule 6).

Owner's call, 2026-09-21: fix the ownership, not the instance — "never put off to tomorrow what is
needed today." The seam turned out to be six lines in `App.tsx` (two `engine.arm()`, four
`engine.disarm()`); `armMaterial` was already model-owned, and `isDetecting` stays a mirror of engine
state, since web's tap detector genuinely lives in the engine and two owners of "is detection live"
could disagree.

Four questions were answered before any code moved, this piece having been mis-sized twice already:

- **`setDevice` always precedes the first arm.** `useAudioEngine` calls it immediately after
  constructing the engine, before `engine.start()` and before the `onStarted` arm.
- **All four `disarm()` sites are the same thing** — freezing after entering a frozen or comparison
  mode — and map onto three analyzer methods: `enterFrozen` (guitar load), `restoreMaterial`
  (material load), and `loadComparison` (which `loadComparisonRecord` delegates to).
- **Guitar `currentTapCount` is reset today by the engine**, not the analyzer: `arm()` zeroes
  `guitarTapCount` and fires `onProgress(0, n)`. Setting it in `startTapSequence` matches the natives
  and is consistent either way.
- **File playback keeps its no-arm start** (`arm: false`), because the engine owns the L→C→FLC
  auto-advance and must not be re-armed underneath it.

`startMaterial` is gone, folded into `startTapSequence({ initialPhase, arm })`, which does the shared
reset and arms the device. The disarms moved onto the three transition methods. `App.tsx` lost both
`engine.arm()` calls, all four `engine.disarm()` calls, and `onMaterialNewTap` — the New Tap button
no longer picks a handler by measurement type, which is where the fork was visible. Cancel routes
through the one restart, mirroring Swift `cancelTapSequence` → `startTapSequence`.

Web 600. The regression case is in `test/comparison.test.ts`, one per type; mutating
`startTapSequence` back to the forked shape (only guitar gets the shared reset) fails the material
case and passes the guitar one — the exact asymmetry the owner hit.

**The run-review of that move found two more things, one of them self-inflicted.**

*A disarm went missing.* `loadMeasurement` set `displayMode = 'frozen'` inline rather than calling
`enterFrozen`, so moving the guitar-load `engine.disarm()` onto `enterFrozen` put it somewhere
nothing ran: loading a guitar measurement stopped disarming, and a stray tap could capture over the
loaded result (invariant I1). `loadMeasurement` now goes through `enterFrozen`, so the freeze —
including the disarm — happens in one place. Two copies of a transition is what let the first one
lose a line.

*Arming could fail silently, and that is a real defect the natives cannot have.* Reported by the
owner: mid-plate, after accepting fC, the FLC prompt appeared with the spectrum and level meter
running normally, and no tap would ever register — only an app restart recovered it. On Swift and
Python arming is an assignment (`isDetecting = true` / `self.is_detecting = True`) that cannot be
refused. On the web the detector lives in the engine, so arming is a request, and
`armMaterial`/`arm` both opened with `if (!this.running || this.state === 'capturing') return` — no
retry, no log. A dropped request leaves the app permanently deaf while everything that does not
depend on detection keeps working, which is exactly the reported picture.

A refused arm is now remembered and applied when the capture completes, and every refusal is logged
with the state that caused it (the engine's existing `console.warn('[engine] …')` watchdog idiom).
`disarm()` cancels a pending arm, so it cannot resurrect detection over a frozen result. Pinned in
`test/engine-arming.test.ts` (`@parity none`, justified in its header: web-only compensation for a
platform difference); restoring the silent drop fails the two cases that describe the symptom.

Worth knowing for any future report: `waitingForFlcTap` and `capturingFlc` set the **identical**
status prompt, so a stuck disarmed state looks exactly like a working armed one. That matches Swift
and Python, which also reuse the prompt, so it was left alone — but it is why the screen could not
tell the owner which state it was in.

**Asking whether the natives could fail the same way found a bug in the canonical edition.** They
cannot fail that way — arming there is an assignment (`isDetecting = true`), with no second party to
refuse it, so the failure mode needs the web's engine/analyzer seam. But Swift had the mirror-image
defect on the same transition: its FLC cooldown closure carried **no cancellation guard**, and
`DispatchQueue.main.asyncAfter` cannot be cancelled — `cancelTapSequence()`'s
`captureTimer.invalidate()` reaches a different timer. So pressing Cancel or New Tap within the
0.5 s after accepting fC let the closure fire into the restarted sequence, forcing
`materialTapPhase = .capturingFlc` and `isDetecting = true` and clearing its frozen spectrum. Both
ports had always guarded; the canonical edition was the outlier. Confirmed by mutation before the
fix: removing the new guard reproduces `.capturingFlc` after a cancel. Run-reviewed on macOS by the
owner, 2026-09-21 — Cancel inside the cooldown now leaves the restarted sequence alone.

There was a Rule 3 sting in it. Python's guard is commented as mirroring "Swift's
`captureTimer?.invalidate()` cancellation idiom" — Swift uses that idiom, but not on this path, so
the comment described a protection that did not exist where it mattered.

The behaviour was tested in **no edition**: Python's only FLC-slot test covers the happy path, in a
`@parity none` Qt-mechanics file, and mentions the guard in a comment without asserting it. All
three now carry the case under `test/tap-progress`. Mutation showed the web's is protected twice —
`startTapSequence` cancels the pending timer *and* the callback guards — so single mutations survive
there and removing both is what fails it; Swift and Python have the guard alone, their scheduled
work being uncancellable. Recorded in the web test, since a case that survives mutation for a
*good* reason still needs to say so.

**F25 — Python's completion flag is a plain attribute where both other editions enforce a setter.
(FIXED — Python, run-reviewed)**

`test/measurement-complete` reads 8/13/8. Python has the **most** cases of any edition and is the
only one missing two rules — `MC6` (no taps must not complete) and `MC8` (completing clears the
loaded-settings warning). Swift and web have all eight, as a shared numbered list MC1–MC8, which is
the pattern F18 identified as the one that actually holds parity.

Python's extra five are Qt signal-emission tests, which are legitimate and have no counterpart by
design: Swift gets change notification from `@Published` and web from `notify()`. So the count is
+5 framework plumbing, −2 behaviour.

**MC8 is missing because Python cannot write it the way the others do:**

| | mechanism | can an assignment bypass it? |
|---|---|---|
| Swift | `didSet` on `isMeasurementComplete` clears the warning | **no** |
| web | `private _isMeasurementComplete` + `set isMeasurementComplete(v)` | **no** |
| Python | plain attribute, plus a `set_measurement_complete()` helper | **yes** |

Swift's and web's MC8 assign the flag and assert the warning cleared. In Python that assignment
clears nothing, so the test as written would fail — the rule lives in a helper the test would have
to call by name.

**Four production sites bypass the helper**, assigning the attribute directly:
`spectrum_capture.py:1999`, `measurement_management.py:667`, `control.py:627`, and
`views/fft_canvas.py:676` — a *view* property forwarding straight through to analyzer state. The two
completion paths compensate by clearing the warning by hand on the next line, so **behaviour today
is correct**; it is correct the way F24's web comparison was correct, by every call site
remembering.

And it reaches the tests: `sut.is_measurement_complete = True` means different things in the three
editions — in Swift it fires `didSet`, in web the setter, in Python nothing. Six Python test files
across S6 set the flag that way. Cases that read identically are not exercising the same thing.

**MC6 is a plain gap**, not structural: nothing stops Python asserting that an empty tap list does
not complete.

Recommendation: make `is_measurement_complete` a property with a setter that does what Swift's
`didSet` does, remove the now-redundant hand-clears at the two completion sites, and add MC6 and
MC8 so Python carries the same eight. That is the same fix as F24 pointing the other way — this
time it is Python relying on call sites where Swift and web enforce.

`is_measurement_complete` is now a property whose setter carries Swift's two `didSet` actions and
nothing else, so the four sites that bypassed the helper can no longer bypass the rules.
`set_measurement_complete()` is assign + emit. Python gained MC6 and MC8, giving all three editions
the same eight; the slug reads 8/16/8. Python **664 passed**, Swift **560** and web **593**
unchanged.

Two things above were not true, both found while implementing.

**The bundle had no production caller, so unbundling was a deletion, not a move.** Nothing in `src/`
calls `set_measurement_complete(False)`. The only path that drives completion False is
`start_tap_sequence()` (`tap_tone_analyzer_control.py:627`), which assigns directly and then does
its own cleanup — `clear_comparison()`, `captured_taps.clear()`, `reset_all_annotation_offsets()`,
`set_frozen_spectrum([], [])` — four of the six bundled items, in the same place Swift does them.
The other two, `loaded_measurement_peaks = None` and `set_material_spectra([])`, are **not** in
Swift's `startTapSequence` either: Swift clears loaded peaks at live-capture completion
(`+SpectrumCapture.swift:1661`) and in `+PeakAnalysis.swift:382`, and the material spectra in the
phase and load paths (`+Control.swift:495,567`). Dropping them from the `False` branch is therefore
the parity-correct outcome, not a regression, and the branch was reachable only from tests. Path 5's
`test_set_false_clears_frozen_arrays` pinned it under a docstring calling the helper "the canonical
setter"; it is now `test_set_false_does_not_reset_frozen_arrays`, pinning the Swift contract so the
bundling cannot return (METHOD rule 5).

**The emit does not belong in the setter.** The recommendation above said "plus the existing
unconditional emit", contradicting this finding's own note that two sites defer it deliberately.
Verified rather than inferred (CROSS-EDITION rule 6): both deferrals are real, each setting the flag
and emitting inside one method — `process_multiple_taps()` (set 1999, emit 2100) and
`_load_measurement_body()` (set 667, emit 856). Swift's `didSet` body contains no notification at
all; the notification comes from `@Published` → `objectWillChange`, which SwiftUI coalesces to the
end of the run loop, so the view is never told until the enclosing method has finished populating
state. A Qt signal fires synchronously, so an emit in the setter would hand the view a half-built
model at exactly those two sites. Emit-in-setter is the option that *diverges* from Swift. Owner's
call, 2026-09-21: alignment is the goal, "but it is also tempered by the difference between the
underlying frameworks — do it when swift does." The emit stays at the point Swift renders.

**An ordering dependency neither edition states.** Load sets complete **before** raising the
loaded-settings warning — Swift at 709 → 833, Python at 667 → 826 — which is the only reason a
load's own warning survives a setter that clears the warning on completion. Reversing either would
silently kill the banner.

Mutation-tested (METHOD rule 2), each confirmed with no other test failing in its place: removing
the empty-taps guard fails MC6 alone; removing the warning-clear fails both MC8 cases alone.
Run-reviewed by the owner across eight checks — load raises the banner, New Tap clears it, guitar
multi-tap completes, a plate sequence seeds Sample Dimensions from the Settings defaults on the
transition, loading a saved plate measurement shows its **stored** dimensions instead of re-seeding,
brace completes, Cancel re-arms with the frozen spectrum cleared, and New Tap clears a comparison.
The last two are what confirm the deleted bundle had no production caller.

One rule has no UI-reachable check: the warning being cleared *by completion itself*. New Tap
already clears the banner and completion can only follow New Tap, so it is unobservable from the
app. It mirrors Swift's `didSet`, is defensive, and is pinned by MC8 and mutation instead.

**F26 — Swift's completion `didSet` does two things; each port implements a different half of it
somewhere else. (FIXED — Python with F25, web separately; both run-reviewed)**

Swift `isMeasurementComplete.didSet` (TapToneAnalyzer.swift:903) does exactly two things, and
nothing else: clear the loaded-settings warning on completion, and seed Store B from Settings on a
material CAPTURE completion (guarded `!oldValue`, `!isGuitar`, `!isLoadingMeasurement`).

| | clear the warning | seed Store B |
|---|---|---|
| Swift | `didSet` | `didSet`, guarded on the **transition** |
| Python | `set_measurement_complete()` — a method, so bypassable, and 4 sites bypass it | same method |
| web | ✓ the real setter — matches | **a `useEffect` in `App.tsx`**, guarded on `matInputs == null` |

Web's effect states outright that it "Mirrors Swift isMeasurementComplete.didSet seeding
materialInputs" — it knows what it mirrors, and mirrors it in the view. That is F24's shape again:
analyzer behaviour implemented in React.

The guards are not the same predicate either. Swift and Python fire on the **transition** into
complete. Web fires whenever the phase reads complete **and** Store B happens to be null, so
anything that nulls Store B while still complete re-seeds from Settings — where the natives would
not, having already spent their one transition.

Also note what Swift's `didSet` does NOT do: clear captured taps, loaded peaks, annotation offsets,
frozen arrays, the comparison, or material spectra. Swift does all of that explicitly in `reset()`
and `cancelTapSequence()`. Python's `set_measurement_complete` bundles that reset work into its
`if not is_complete:` branch, and **that bundling is the reason it cannot be a property**: an
assignment of `False` anywhere would trigger a full reset. Unbundling is therefore the first step of
F25's fix, not a separate clean-up.

The Python half landed with F25: one setter mirroring the `didSet` now clears the warning and seeds
Store B on the transition. The web half was larger than relocating the effect — Store B was not on
web's analyzer at all, it was `useState` in `App.tsx`, making this F24's shape a second time rather
than a guard change.

Swift makes exactly three `materialInputs` writes: the `didSet` seed, the load, and the user's edit
binding. It never nulls Store B on New Tap. Web did, at `App.tsx:502`, and that null-drop and the
`matInputs == null` guard were a matched pair — both existed only because the seed lived in a view
effect. Removing the drop makes the guard *become* the transition.

**The settings path.** Swift and Python build Store B by reading a settings singleton from inside the
model (`MaterialMeasurementInputs.fromSettings(for: TapDisplaySettings.measurementType)`). The web
has no such global, which is why its helper takes settings as an argument. Three ways to give the
analyzer one: push a narrow material-defaults slice, push the whole `Settings` object, or have the
analyzer call `loadSettings()` itself. The third is a genuine trap — App keeps settings in React
state and persists them through an ordinary `useEffect`, so localStorage lags state by a render, and
a completion in the same tick as a settings change would seed from stale values. The first costs a
bespoke type to maintain and a reshaped helper.

Owner's call, 2026-09-21: push the whole object. The coupling objection did not survive the code —
only three places consume a `Settings` *instance* (the settings panel, `fromLive`, and the seed
helper); the other eight importers take types and constants. So `analyzer.settings` is pushed from
the same `useLayoutEffect` that already pushes `measurementType` and `measureFlc`, for the reason
that effect's own comment gives: the web has no analyzer-visible global.

**A load had to be given a loading window.** Swift's `loadMeasurement` holds `isLoadingMeasurement`
across the whole restore, which is what suppresses the seed. Web's material load is orchestrated
from `App.tsx` as six separate calls — `measurementToLiveMaterial`, `updateSettings`, `setMatInputs`,
`clearResult`, `restoreMaterial`, `restoreOffsets` — and never set that flag, because with the seed
in a view effect the `== null` guard was doing the job instead. `restoreMaterial` now takes the
measurement's dimensions and holds `isLoadingMeasurement` across the completion assignment. Without
it the setter's guard reads false during a load and Settings clobbers the file's stored dims — the
origin bug this whole two-store design exists to prevent.

**The slug's own test header was a rule-4 finding.** `material-measurement-inputs.test.ts` opened
with a "WEB DIVERGENCE" note recording the three canonical seed-gating cases (Swift
`doesNotSeedStoreB*`) as untestable "React behaviour, covered by the V-A / V-C run-review" — an
accurate description of a defect, written down as a design. With the seed on the analyzer they are
ordinary unit tests, and the web now carries all three, plus one for the transition guard the old
effect got wrong and one for the load window. Web 598. The `loadedNotes` state cases stay App-side
and remain run-review territory.

**F27 — six measurement-update cases are filed under `annotation-state` in both natives, three of
them re-asserting rules that `measurement-amend` already owns. (FIXED — filing only, both natives)**

`test/annotation-state` reads 44/42/32, the widest spread left in S6, and most of it is this block.
Swift's `AnnotationStateTests` carries a section headed "Update Measurement (moved from
MeasurementCodableTests)" with six `update_*` cases; Python mirrors it as `TestUpdateMeasurement`.
Web has none of them under this slug, which is the whole of the 12-case gap to Swift.

They are not annotation state. Three duplicate rules already pinned under `test/measurement-amend`,
which all three editions carry with 11 cases apiece:

| `annotation-state` (Swift/Python) | already asserted by `measurement-amend` |
|---|---|
| `update_nilValues_clearFields` | `with_clearsMeasurementNameWithNil` |
| `update_successiveEdits_eachMintANewId` | `with_successiveAmendments_eachMintANewId` |
| `update_mintsNewId_andPreservesCapturedData` | `with_preservesOtherFields` + the mint rule |

This is F8's shape — the same rule under two slugs, which is how two copies come to disagree — and
it is why the count spread reads as a web gap when web is the edition filing correctly.

The other three are **collection**-level: `update_byIndex_changesOnlyTargetedEntry`,
`update_outOfRangeIndex_isNoOp` and `update_duplicateImport_onlyEditedIndexChanges`. Those belong
with the saved-measurement library, not with per-peak annotation state.

**Two of them cannot exist on web, and that is architecture, not a gap.** The natives hold
`savedMeasurements` as an array and update by INDEX; web's store is a rowKey-addressed IndexedDB
(`src/measurement/store.ts`) with `saveMeasurement` upserting by `rowKey` and no index API at all.
So "update at index N" and "an out-of-range index is a no-op" have no web counterpart by
construction — that is [F19b](#), row identity and addressing, already deferred to the sorting work.
The third does have a web counterpart, under a different slug: `import-persistence`'s "a duplicate
import gives two rows that SHARE the id and differ by rowKey".

Done as recommended, 2026-09-21. The three collection-level cases moved to
`test/import-persistence` in both natives — `ImportPersistenceTests.swift` and
`test_import_persistence.py` — under a header saying why they live with the library and why two of
them have no web counterpart. The three duplicates were deleted. No production code moved, and
nothing was added to web.

**One of the three was not a pure duplicate, and deleting it blind would have lost a rule.**
`update_nilValues_clearFields` also asserted that clearing the fields mints a new id — "clearing the
fields is a data change too" — which `with_clearsMeasurementNameWithNil` did not. That assertion
was added to the `measurement-amend` case in all three editions *before* the delete, so the rule
now sits once, in the slug that owns it. The other two were fully covered:
`update_successiveEdits_eachMintANewId` by `with_successiveAmendments_eachMintANewId`, and
`update_mintsNewId_andPreservesCapturedData` by `with_preservesOtherFields` plus that same mint rule.

Counts: Swift 561 → 558, Python 665 → 662 — six cases deleted, three moved, one assertion added in
each edition. `test/annotation-state` now reads 39/37/32, and the remaining spread is the visibility
cycle and the offset/selection basics, which web files across its two files.

**F28 — Swift can store a mode override meaning "no override", and only its tests ever do.
(FIXED — Swift; the state is gone, the file format is unchanged)**

`peakModeOverrides` is `[UUID: UserAssignedMode]`, an enum with `.auto` and `.assigned(String)`.
Every consumer treats a stored `.auto` exactly as an absent key: `hasManualOverride` and
`overriddenPeakIDs` both test `if case .assigned`, and `effectiveModeLabel` reads
`peakModeOverrides[peak.id] ?? .auto`.

Production never stores it. The results view calls `setModeOverride(.assigned(label), …)` to set and
`resetModeOverride(for:)` — which does `removeValue(forKey:)` — to clear. The only
`setModeOverride(.auto, …)` calls in the repository are `AnnotationStateTests.swift:290` and `:391`.

Neither port can represent it. Python pops the key on reset and documents the invariant outright —
*"stores only user-assigned label strings (every entry IS an override)"* — and web is
`Map<number, string>` with `resetModeOverride` deleting. Absence is their only "auto".

So two Swift cases assert behaviour through a state the application cannot produce, one of them
(`hasManualOverride_trueForAssigned_falseForAuto`) covering a branch that is dead in production while
the live branch — the absent key — is reached by a different arm of the same guard. That is METHOD
rule 1: check what the APPLICATION passes, not what the test does.

The underlying behaviour is real and worth keeping: clearing an override reverts to the
auto-classified label. It is `resetModeOverride` that should be asserting it.

Owner's call, 2026-09-21 — "why leave an unused state that confuses things in the code? Will it ever
be used?" It will not: `resetModeOverride` removes the key, so nothing in the app can create one.
Both halves were done.

An override is now the label alone, `[UUID: String]`, on the analyzer AND on `TapToneMeasurement` —
the shape both ports already had. `setModeOverride` takes a label, `hasManualOverride` is a presence
test, `overriddenPeakIDs` is `Set(keys)`, and `effectiveModeLabel` is one `??`. Six views lost their
`if case .assigned` pattern matches. The two tests now drive `setModeOverride` and
`resetModeOverride`, which is what the results view calls. Swift 558 → 559.

**The file format is untouched.** `UserAssignedMode` survives as the wire shape and as the picker's
label catalogs: encode re-wraps each label as `.assigned`, decode unwraps it, and an `auto` entry —
which carries no label and therefore means "no override" — is DROPPED on read, exactly as Python and
web have always dropped it. The `.guitartap` JSON is byte-identical.

That last part needed its own guard, because nothing pinned the emitted shape: a silent change there
would write files both ports read as having no overrides at all. `overrides_areWrittenAsAssignedEntries`
now asserts the wrapper, and the replaced `.auto` case asserts that such an entry is dropped rather
than becoming an override.

**And the corpus had never carried one.** Asked for a real file to verify the reader against, the
corpus turned up nothing: 119 measurements, 116 with selection, 91 with annotation offsets, **zero**
with `peakModeOverrides`. Every override test in every edition had always used a hand-built fixture,
so the `.guitartap` reader had never met an override an app wrote — a gap that predated this work.

The owner captured two, saved from the running apps: `annotation-override-1790037028.guitartap`
(Swift, label "Fred") and `annotation-override-python-1790037332.guitartap` (Python, "Fred2"), with
a PDF and PNG beside each. Both editions emit the identical wire shape, and the Python file loads in
Swift by hand. All three editions now decode both files and assert the label survives as the label
alone, keyed to a peak the file still contains. The Python-written file is the one that matters for
Swift: Python's writer was untouched by this refactor, so reading it proves cross-edition parity
against bytes Swift did not produce.

**A false green nearly certified that guard.** The mutation — emit bare labels instead of the
wrapper — appeared to survive, which would have meant the test measured nothing. It had not
survived: `-only-testing:GuitarTapTests/MeasurementCodableTests` names a FILE, not a suite, matches
nothing, and exits 0 having executed 0 tests. METHOD rule 2 records this exact trap ("read the
count, not the failure list"), and it caught three false greens before this one. Re-run against the
real suite name, `ModeOverridesCodableTests`, the mutation fails both the round-trip and the new
guard.

**F29 — `status-message` 12/12/16 is not "web has four extra". Both natives have gaps, and their
test headers claim a coverage that does not exist. (FIXED — both natives)**

Swift and Python are 1:1 here — twelve cases, matching names, no drift between them. Web's sixteen
are not four extras: it MERGES four native cases into two (single/multi-tap resting prompt; plate
complete with and without FLC) and adds **six** of its own.

Five of those six pin strings that all three editions produce:

| web case | the string | asserted in Swift/Python? |
|---|---|---|
| capturing + between-taps strings | `Tap n/N capturing…` / `…captured. Tap again…` | no |
| Redo re-arms the phase | `Ready for fLC tap — tap again` | no |
| multi-tap progress then review | `fL tap n/N captured. Tap again…` | no |
| EG-1: no in-band resonance re-arms | `No signal detected — tap again` | **no — and Swift sets it at five sites** |
| file playback auto-advance | `File: fL complete, capturing fC…` | no |

The sixth is a guard that no sweep state yields a string that was removed — a shape neither native has.

**Both native headers record the exclusion as architecture.** Swift's says the per-tap progress
transients "are written deep in the gated-capture pipeline … and are **produced by** the
file-playback + gated-capture regression tests running the real capture. The web pins them directly
because it has an explicit engine-state setter (`setEngineState`); Swift/Python set them
imperatively mid-pipeline, so a state-driven suite can't reach them cleanly."

**"Produced by" is not "asserted by", and the difference is the whole finding.** `statusMessage` is
asserted in exactly two Swift test files — `StatusMessageTests` and `TapCountChangeTests` — and
**zero** times in `FilePlaybackRegressionTests`. Python is identical. Those regression tests run the
pipeline, so the strings are certainly *set*; nothing checks them. Delete `No signal detected — tap
again` from all five of its Swift sites and both native suites stay green.

So this is METHOD rule 4 again — an `n/a` resting on an architectural difference turns out to be a
finding, not a difference — compounded by rule 3: the sentence asserting the coverage is the reason
nobody looked. It is the same shape as F14, where a docstring's claim about what a helper mirrored
was why six tests asserted against a copy of the logic instead of the app.

It also inverts the count intuition a third time. `effective-peak-id` 6/6/0 was correct;
`measurement-complete` 8/13/8 had the LARGEST suite missing two rules; here 12/12/16 reads as web
carrying extras when it means the two natives share a gap.

**And the architectural barrier does not exist either.** Asked whether it could be cleaned up so the
difference stops existing, the answer is that there is nothing to restructure — the seam is already
there, in all three editions, and both natives already drive it from tests:

| | entry point a test can call with a synthetic spectrum | already called by |
|---|---|---|
| Swift | `handleLongitudinalGatedProgress(magnitudes:frequencies:)`, `handleCrossGatedProgress(…)` | `FrozenPeakRecalculationTests`, `FilePlaybackRegressionTests` |
| Python | `_handle_longitudinal_gated_progress(…)`, `_handle_cross_gated_progress(…)` | `test_frozen_peak_recalculation.py` |
| web | `recordMaterialTap(spectrum)` | `status-message.test.ts` |

`StatusMessageTests` can call exactly the methods a sibling test file in the same repository already
calls, without audio. The guitar loop strings need even less: `guitarLoopStatus(capturing:)` is
already a named helper in Swift, the counterpart of web's `setGuitarStatus`, and can be asserted
directly.

Note also that web is not as state-driven as its own header implies: only the GUITAR loop strings
come from `setEngineState`. Web's material strings — `File: fL complete…`, `fL tap n/N captured…` —
are set imperatively too, at `tapToneAnalyzer.ts:1094`, `:1132` and `:1145`. Web tests them because
its analyzer owns the material phase machine, which the natives' analyzers also own. The editions
are structurally the same here; only the test coverage differs.

Done, 2026-09-21. Six cases added to each native — the five above plus one the list missed — against
the seam their own sibling test files already use. No production code moved.

Each case drives a method another test file calls without audio: `guitarLoopStatus(capturing:)` for
the two guitar-loop strings, `redoCurrentPhase()` for the "— tap again" re-arm,
`handleLongitudinalGatedProgress` for the material progress string and the file-playback
auto-advance, and `finishGatedFFTCapture` fed silence for "No resonance detected". Mutation-tested:
four strings broken, four failures, each caught by its own case.

**A sixth gap turned up when the counts still did not match.** With five added, the slug read 17/17/16
and the owner asked why web was still different. Mapping case by case: two of the differences are
filing (web merges single/multi resting prompt into one case, and plate-complete ±FLC into another —
four native cases, two web cases, same rules), and one is correct asymmetry (web's removed-string
guard sweeps for `Requesting microphone` / `Comparing` / `Playing` / `Cancelled`, web-only inventions
the natives never had). The third was real: **`Set up for fLC tap, then tap` was asserted in no
edition but web.** Web's accept case covered BOTH transitions, fL → "Rotate 90°…" and fC → the FLC
prompt; the natives covered only the first. Both natives produce it, and it is the prompt shown
during the FLC cooldown — the same window whose missing cancellation guard F24's trail fixed in Swift
the same day. Added to both, mutation-tested.

`test/status-message` now reads **18/18/16**, with every remaining difference explained by behaviour
rather than coverage.

**Both headers now say what is true.** They claimed the transients were written too deep for a
state-driven suite and were covered by the file-playback regression tests. Neither held: those tests
run the pipeline but assert no status at all, and the handlers take a spectrum and a peak, which
`FrozenPeakRecalculationTests` and `test_frozen_peak_recalculation` have always called directly. The
rationale is replaced with what happened, because a sentence explaining a non-existent obstacle is
what kept the gap alive.

Two parity notes from writing them: Python counts material taps in `captured_taps` where Swift uses
`materialCapturedTaps` (a name difference, not a behaviour one), and Python's analyzer needs a real
`RealtimeFFTAnalyzer(for_testing=True)` for the gated transform, exactly as Swift's test passes one.

**F30 — web drew the engine/model line in a different place: its engine owned the detector, the
gated capture and the session WAV, which Swift and Python keep on the analyzer.
(FIXED — web, run-reviewed; the natives' boolean pair is left alone, see below)**

Filed after the owner pushed back on this being dismissed as "not worth chasing" — the same
"behaviour is equivalent today" reasoning that mis-filed F19 and nearly mis-filed F24.

| | model of engine/detection state | guitar loop status set at |
|---|---|---|
| web | `EngineState = 'idle' \| 'listening' \| 'capturing' \| 'paused'`, forwarded from the engine; `setEngineState` derives `isDetecting`, `isDetectionPaused` and the status string | **1 site** |
| Swift | `isDetecting` + `isDetectionPaused`, two independent `@Published` booleans | **4 sites** |
| Python | `is_detecting` + `is_detection_paused` | **4 sites** |

Swift's own comment on `guitarLoopStatus(capturing:)` calls it "the equivalent of the web
`setGuitarStatus(engineState)`" — it mirrors the string-building half and not the state-driven
dispatch that decides when to apply it.

The boolean pair can express a state that does not exist: detecting AND paused. Nothing prevents it
structurally; `pauseTapDetection()` clears one while setting the other, and every other site that
touches the pair has to do the same. Web cannot represent it — one value, both booleans derived —
which is precisely the argument F24 made for `displayMode`, where three fields became one three-state
value so "frozen AND comparison" stopped being writable. Web's invariant suite carries I1 and I2 to
catch illegal combinations; an invariant test is a workaround for a state that should not be
representable.

This is the third instance of one shape inside S6: F24 (display mode held in the view), F26 (a model
rule implemented as a view effect), and now a model rule maintained by call-site discipline rather
than by derivation. Two were fixed by moving the decision onto the model; this one is the same move
one level down.

**It is also much the largest, and it runs the other way.** F24 and F26 moved web toward the natives.
Here web has the better structure, and the natives are the ones carrying the risk — across
`isDetecting` (67 references in Swift, 65 in Python) and `isDetectionPaused` (38 / 14). A
`detectionState` enum with the booleans derived is a real refactor of canonical model code with real
behavioural risk, not a filing change.

**Asked how to move WEB onto the natives' shape, the honest answer is that it can be done — the
claim that it could not was wrong twice over.**

First this was filed recommending the natives adopt web's enum, which inverts the owner's standing
rule. Then, asked the reverse, it was defended as platform-forced on two grounds, both false:

- *"Web's detector runs in an AudioWorklet, off the main thread."* It does not. The worklet computes
  FFT and RMS and posts chunks to the MAIN thread — `port.onmessage` → `onChunk` → `processChunk` →
  `detectTap`. Detection is main-thread in web exactly as it is in Swift.
- *"An analyzer-owned `isDetecting` would reintroduce the silent-arm bug."* Circular: the
  request/refusal seam exists only BECAUSE detection was put on the engine. Move it and the seam,
  and the bug class with it, disappears.

The real difference is where each edition draws the engine/model line:

| | engine | detection + capture members on the engine | detection lives in |
|---|---|---|---|
| Swift | `RealtimeFFTAnalyzer*.swift`, 3409 lines | **1** | `TapToneAnalyzer+TapDetection.swift` (495) + `+SpectrumCapture.swift` (1713) |
| Python | `mic`/proc-thread | — | `tap_tone_analyzer_tap_detection.py`, `…_spectrum_capture.py` |
| web | `realtimeFFTAnalyzer.ts`, 1268 lines | **48** | the engine |

Swift's engine is microphone, FFT and watchdog. Web's additionally owns the detector, the
hysteresis and confirmation counters, the noise-floor EMA, the warm-up window, the capture buffers
and the gated-capture completion — the contents of Swift's two analyzer files.

That is a port choice, and it is the largest single divergence the sweep has found. It is also the
root of several smaller ones already recorded: arming as a refusable request (F24's tail),
`isDetecting` as a mirror rather than state, the four status sites web does not have (F29), and the
boolean pair above.

Moving detection and gated capture from `realtimeFFTAnalyzer.ts` into `tapToneAnalyzer.ts` would
leave the engine as mic + worklet + FFT + watchdog, matching Swift, and would retire the
`pendingArm` machinery added under F24 rather than keeping it as compensation.

Owner's call, 2026-09-21, against a recommendation to defer it: *"This needs to be done. It has been
put off for months and always delayed."* Done, and run-reviewed.

**What moved to `tapToneAnalyzer.ts`**, all of it transplanted rather than retyped so the arithmetic
is unchanged: the pre-roll ring, the capture windows, `detectTap` with its hysteresis latch,
2-chunk confirmation, noise-floor EMA and warm-up, the arming and disarming, the onset alignment and
zero-padding, the calibration APPLICATION, `tapDetectionThreshold`, and the entire session WAV —
buffer, bounded pre-roll, phase checkpoints, redo truncation and the write itself. The constants
Swift keeps on its analyzer (`hysteresisMargin`, `noiseFloorAlpha`, `warmupPeriod`) went with them.

**What stayed on the engine**: the microphone, the worklet, the FFT primitive, the calibration
*corrections*, level, clipping, decay, the watchdogs, device management and file transport. 1268
lines → 793. The five detection-result callbacks collapsed into one `onAudioFrame`, and the caller
now arms before playback — `startTapSequence({ skipWarmup })` then `playFile` — which is the order
`TapToneAnalysisView+Actions` uses.

**The evidence the DSP survived**: all seven REG-* baselines — REG-G1, both REG-G2 cases, REG-B1,
REG-B2, REG-P1 and OUT-4 — plus the self-regression oracle. One failed at first and was worth the
whole exercise: the material runner passed calibration through `playFile` while the analyzer reads
it from the device, which moved plate fL by ~1 Hz. REG-P1 caught it.

**Two things were deleted rather than moved.** `test/engine-arming.test.ts` in full: its six cases
covered the deferred-arm machinery added hours earlier under F24, which existed only because arming
was a refusable request — no request, no refusal. And `tap-count-change`'s engine layer, five cases
testing a progress re-fire its own comment called "a web-specific progress-bar mechanism
Swift/Python don't have". Both went with the divergences they compensated for.

**A caution the cleanup earned.** Cutting the engine's detector methods left its FIELDS behind, and
`playFile` went on faithfully resizing a pre-roll, allocating capture windows and resetting
`prevAbove`/`consecutive`/`guitarTapCount` that nothing read — plus a second copy of every detection
constant, live alongside the analyzer's. `tsc` is silent about assigned-but-unread state, so only
reading `playFile` line by line found it. A move is not done when the new copy works.

**Not changed**: the natives' `isDetecting` + `isDetectionPaused` pair can still express
detecting-AND-paused, and is kept consistent by every call site. Collapsing it into one value remains
available, in all three editions together, if a bug ever comes from it — none has.

**Also noticed, not acted on**: the detector has no `@parity` group in ANY edition —
`TapToneAnalyzer+TapDetection.swift` and `tap_tone_analyzer_tap_detection.py` are both untagged,
which is why this move disturbed no group. It is newly worth tagging: before it, web's detector sat
in the audio layer and a group would have been lopsided; now all three sit on the analyzer, so
`state/tap-detection` would be 1:1:1 for the first time. That is a parity-map decision, left open.

F29 remains separately actionable and test-only — and easier now, since the seam it needs is the
same shape in all three.

## Stage 2 — move case lists into shared data

Once Stage 1 has shown which slugs are case-shaped and what their cases need to express, move those
case lists into data vendored the way `parity-oracle.json` is, with one small runner per edition.
Divergence then becomes **unrepresentable** rather than merely detectable, and a fourth edition ports
one runner instead of thirty tests.

The pattern is already proven in this codebase and needs no prototype: web's `pitch.test.ts` is a row
list plus a loop that generates the cases.

### Carried in from Stage 1

**F18 — the six drifted S5 slugs, to be levelled here rather than by hand.** Stage 1 measured them;
this is where they get fixed. All eight S5 slugs were read and only **two** had the same cases in
all three editions:

| slug | counts | cases |
|---|---|---|
| `measurement-name` | 4/4/4 | **identical** |
| `material-selection` | 1/1/1 | **identical** |
| `peak-selection-persistence` | 4/4/3 | same rules, web files the effect under `frozen-peak-recalc` |
| `import-persistence` | 3/3/6 | 3 shared; web's extras guard a risk only its design had |
| `export-filename` | 6/6/6 | **counts match, cases differ** |
| `material-measurement-inputs` | 6/6/6 | **counts match, cases almost entirely different** |
| `measurement-type-name` | 14/9/6 | drifted three ways (F16), levelled |
| `measurement-codable` | 53/64/23 | organised by *type* in the natives, by *concern* in web |

The implementations were checked in each case and agree, so **no defect follows from the drift** —
what follows is that the editions pin different things, so a change that breaks one edition's rule
can pass in another. Levelling the six by hand would be doing Stage 2's work without its mechanism,
and would have to be redone once the shared case lists land.

Note that `export-filename` and `material-measurement-inputs` are both 6/6/6 and neither is in
parity. It was already known that a *spread* in the count table means little; this is the evidence
that *agreement* means little too.

The slugs already in parity — plus `view/dot-layer` and `test/peak-heal` from earlier subsystems —
all reach it the same way: **a small, shared, numbered case list**. That is the pattern to
generalise, and the reason this stage exists.

**Why this comes second.** #8 designed a case schema for `test/frozen-peak-recalc` and never built
it. That was fortunate: that slug needs stateful analyzer setup, where most slugs are
input → expected output. Designing the shared format against it alone would have fitted the mechanism
to the least representative example — the same mistake that produced the original divergence, where a
fixture built for one test became the pattern for a suite.

**Relative size.** The owner's read, 2026-09-20, is that Stage 1 overwhelms Stage 2. The measurement
supports it: Stage 1 is 40 test slugs across nine subsystems with production defects expected, where
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
