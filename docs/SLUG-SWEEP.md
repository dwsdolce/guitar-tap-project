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

Status: ✅ **CLOSED 2026-09-24** — all 11 slugs read; every finding it produced (F23–F48) fixed, run-reviewed where it changed behaviour, and committed.

> **S6 is closed, 2026-09-24.** All 11 slugs read; F23–F48 all closed. Full suites on the committed
> tree: **Swift 605, Python 719, web 642 — all passing**; parity map 103 groups, no problems.
>
> Split out and **not** S6 work (owner, 2026-09-23): [#19](https://github.com/dwsdolce/guitar-tap-project/issues/19)
> (file-playback results depend on machine speed), and the Swift meter/detection cadence recorded under
> [#3](https://github.com/dwsdolce/guitar-tap-project/issues/3). The Windows/Linux baseline re-mint (#16)
> waits until the sweep is finished.

**Audit record (S6 closed 2026-09-24 — the sweep resumes at S7, Capture / DSP pipeline).** This table records only **what the reading
produced** — a finding number, or "clean" where none was filed. Each finding's status lives in the
finding and nowhere else; do not restate it here.

| slug | read? | produced |
|---|---|---|
| `effective-peak-id` | ✅ | coverage clean — 6/6/0 is structural, both halves of the claim verified; **F23** |
| `comparison` | ✅ | **F24**; **F31** from the F30 run-review |
| `button-enablement` | ✅ | first read said clean — 13/13/13; re-read under **F30** found both natives asserting against a retyped copy of the rule; **F32** from the F30 run-review |
| `measurement-complete` | ✅ | **F25**, **F26** |
| `annotation-state` (44/42/32) | ✅ | **F27**, **F28** |
| `status-message` (12/12/16) | ✅ | **F29**, **F30**; **F33** from the F30 run-review |
| `tap-count-change` (6/6/6 → 10/10/10) | ✅ | cases clean — 3+3 identical all three, the best-aligned slug in S6, and every case guitar; **F36**, **F37**, **F38**, **F39**, **F40**. **F34** had surfaced here from the F30 run-review, before the slug was read |
| `state-invariants` (7/7/7) | ✅ | cases identical all three (V1–V7, I1–I6); **F45** |
| `scenario-trace` (4/4/4) | ✅ | cases and traces identical all three (S1–S4); **F46** |
| `session-pre-roll` (4/4/4) | ✅ | cases identical all three; **F47** |
| `start-tap-race` (4/4/4) | ✅ | cases R1–R5 in all three; **F48** |

The unread rows' counts are Swift/Python/web. `annotation-state` is the largest and the likeliest to
show F10-shape filing differences; `status-message` was one of the two where web carried more cases
than the natives. `tap-count-change` was the other — its 6/6/**11** was already stale when the table
was written, because F30 deleted web's engine-refire layer. Measured with the runner, it is 6/6/6.

Method reminders that earned their place in S6 so far: counts mean nothing in either direction
(`effective-peak-id` 6/6/0 was correct, `measurement-complete` 8/13/8 had the LARGEST suite missing
two rules); verify a test file's own claims about why an edition differs (rule 3 applies to test
headers too); and "behaviour is equivalent today" is not a reason to close an architectural
divergence — that reading mis-filed F19 and nearly mis-filed F24.

And one more, from `tap-count-change`: **agreement between the case lists means as little as spread
between the counts.** That slug's two suites are 3 + 3 in every edition, assert identical strings,
and all reach production — and it produced five findings, two of them reachable from the UI. The
cases agreed because they were all written for guitar, against a hook three measurement types use.
S5 had already shown that a matching 6/6/6 proves nothing (`export-filename`,
`material-measurement-inputs`); this is the same lesson where the cases match too. **Ask what the
production code is used for that no case covers.**



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
(FIXED — all three, run-reviewed)**

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

**The boolean pair — decided, attempted, and RESUME HERE.** Owner's call 2026-09-21, after asking
whether the flags are "truly exclusive": do both the divergence fix and the cleanup.

*Are they exclusive?* Two different answers. `isDetecting` / `isDetectionPaused` ARE exclusive —
pause clears one and sets the other, no site sets both, and the detector's gate tests both
defensively, which is the tell. `gatedCaptureActive` is NOT: a capture runs *while* the detector
listens, and re-entry is blocked by capture id (`gatedCaptureID == lastLevelCrossingCaptureID`)
because the window can start on the audio queue and finish before the main thread's call runs. That
is a concurrency fact, not a state-machine fact, so it must stay a separate flag.

**Done and verified (web, UNCOMMITTED at the time of writing):** web's frame dispatch was
`if (capturing) feedCapture else if (detecting) detectTap` — exclusive, where Swift's
`onRmsLevelChanged` gates only on `isDetecting && !isDetectionPaused && !isMeasurementComplete` and
never on the capture flag. Web now runs the detector through a capture, with re-entry guarded in
`beginCapture`. All seven REG-* baselines pass, so the latch and noise-floor EMA behave identically
on these fixtures; the structure now matches.

**The enum — done in all three.** `DetectionState { idle, listening, paused }`, with `isDetecting`
and `isDetectionPaused` kept as derived reads so every site that only *asks* is unchanged; only the
writes moved. It is a top-level type in its own file in each edition — `Models/DetectionState.swift`,
`models/detection_state.py`, and a `DetectionState` union beside `MaterialTapPhase` in
`state/tapToneAnalyzer.ts` — which is the shape `MaterialTapPhase` and `AnalysisDisplayMode` already
have. Python could not nest it: the analyzer's mixins need the type and are themselves imported by
the analyzer, so nesting gives a circular import.

The arming `didSet` moved onto the enum keyed on `let wasDetecting = (oldValue == .listening)`, and
opens with `guard oldValue != detectionState else { return }` — which expresses structurally what the
old comment called "deliberately ignore true → true assignments". That guard also drops the old
idle→idle disarm, which is safe: the only arming site outside the `didSet` is file-playback-only, and
the `didSet`'s disarm is itself skipped during file playback, so a redundant clear could never reach a
level crossing that was actually armed.

**A fourth paired site the recipe had missed.** `handleRouteChangeRestart` reads `wasDetecting`, sets
`isDetecting = false`, and deliberately leaves `isDetectionPaused` alone — so a sequence paused across
a route change is still paused afterwards. A flat `detectionState = .idle` there would have discarded
the pause. It is now `if wasDetecting { detectionState = .idle }` in Swift and Python. The three the
recipe did list — pause, resume, and `startTapSequence`/`loadMeasurement` — were as described; in
`startTapSequence` the early pause-clear is *dropped* rather than converted, because clearing to
`.idle` there would disarm a level crossing that a restart-while-listening relies on staying armed.

**Then the same reading turned up the button rule**, on the `button-enablement` slug this sweep had
already marked clean. Web's `buttonRule` is production code in `state/buttonEnablement.ts`, imported
by `App.tsx` and by its test. Swift and Python each had the real rule inline in the view and a second,
retyped copy in the test file — and the Swift header said the duplication was deliberate, so that
drift in the view "would make one side give". It could not: the test asserted against the copy, so the
view was free to drift and the suite would stay green. That is PARITY-TEST-METHOD rule 1's headline
shape, and 26 of the 39 tests in the slug were measuring nothing about the shipping path.

Folded into F30 rather than filed separately, on the owner's call — *"this is part of what you are
doing. We do it now. Divergence is a call to action not to burying under the rug."* The rule now lives
in `Models/ButtonEnablement.swift` and `models/button_enablement.py`, the views call it, and the tests
import it. The parity map's anchor for the group moved from the two view files onto the three model
modules, so it is 1:1:1 in the same layer in all three.

The extraction also closed the drift the copies were hiding: both natives' fixtures still carried the
`displayModeIsComparison` boolean that F24 had already replaced with a required `displayMode` in web,
for the exact reason that a defaulted boolean answers for a state the caller never supplied. The
production `ButtonState` now takes `detectionState` and a required `displayMode` in all three.

It also dropped `currentTapCount`, which every edition declared on `ButtonState` and no edition's rule
ever read. `git show` on the commit that created `buttonEnablement.ts` has it declared and unused in
the same diff that introduced `numberOfTaps` and used it — dead from the first line, then copied into
both natives when their mirrors were written, and nearly copied forward again here. The rule asks only
whether the sequence is multi-step, which is `numberOfTaps`: the sequence's SHAPE. `currentTapCount` is
its PROGRESS, and progress never enters the question of which buttons are live. The tap-count control's
own lock (`currentTapCount > 0 && !isMeasurementComplete`) is a different rule about a different
control, still inline in all three views — unpinned, and noted here rather than folded in, because
putting it behind a type named for three action buttons would be the same conflation in reverse.

**The evidence.** Swift 566 tests in 117 suites, Python 670, web 598 in 53 files — each identical to
its pre-change baseline — plus all seven REG-* baselines (REG-G1, both REG-G2 cases, REG-B1, REG-B2,
REG-P1, OUT-4) and the self-regression oracle on the web side. Passing is not evidence, so the
extraction was mutation-tested on both natives: breaking `pauseEnabled` in the *production* rule fails
exactly one case (B6, the paused one) in Swift and in Python, which is the proof the tests now reach
production — the mutation would have changed nothing before. The Swift run was checked for the
count, 13 tests in 1 suite, not just the exit code.

Invariants I1/I2/I6 did NOT become vacuous, as expected: they check detecting/paused against
*completion* and *phase*, which the enum does not cover. No invariant asserted `!(detecting && paused)`,
so nothing was lost by making it unrepresentable.

**Run-review steps — specific to this finding.** No standard procedure exists; these come out of
the diff. Explanations are in the notes below, keyed by step — the steps themselves are just the
actions and what to expect.

Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview` (NOT `npm run dev`). Same list per edition, canonical first.

**Web: clear the service worker after EVERY build, before testing.** The app is a PWA
(`vite-plugin-pwa`, `dist/sw.js`), so the worker serves the cached shell and a new tab gets the OLD
bundle — opening a fresh tab does not help, and nothing fails visibly. On 2026-09-22 this silently
invalidated a run-review: steps 1–7 were run against a pre-enum bundle, and the model's
`detectionState` field did not even exist in the code under the owner's fingers. It was caught only
by walking the React fiber from the console and finding `detectionState === undefined` on an analyzer
whose other fields were all correct. Same mechanism as the stale-SW lazy-chunk bug — reproduces under
`build` + `preview`, never under `dev`.

    navigator.serviceWorker.getRegistrations()
      .then(rs => Promise.all(rs.map(r => r.unregister())))
      .then(() => caches.keys())
      .then(ks => Promise.all(ks.map(k => caches.delete(k))))
      .then(() => location.reload());

Or Develop → Empty Caches, then reload. A web result obtained without this step is not a weaker
result, it is not a result.

**Quitting the browser does NOT count as clearing it**, and neither does opening a new tab. A service
worker's registration and its Cache Storage survive a restart — that is what they are for. The config
is `registerType: 'autoUpdate'`, which makes the trap worse: the new worker installs but takes over
only once the old clients are gone, so a quit-and-reopen typically serves the OLD bundle one more
time and the load AFTER that is the fresh one. It is easy to test stale code, watch it update on the
next launch, and conclude it was a glitch.

*Detection state machine*

1. Guitar, tap count 3. Press New Tap. → "Ready…"; Pause enabled, New Tap disabled, Cancel enabled.
2. Tap once. → 1/3.
3. Press Pause. → Button reads Resume. Spectrum stays live. Tapping does not increment.
4. Press Resume. → Still 1/3. Next tap → 2/3.
5. While paused, change the audio input device. → Still paused when it settles; Resume works.
   The status still reads "Detection paused – tap freely, then resume" — not a tap prompt.
6. While paused, press Cancel. → Back to the step-1 state: tap-count label GONE, status back to
   the tap prompt, Pause enabled, New Tap disabled, Cancel enabled.
7. While paused, load a saved measurement. → Frozen on it. New Tap enabled; Pause and Cancel
   disabled; Pause reads "Pause". Live audio does not change the loaded peaks.
8. Set the tap count back to 3. New Tap, tap once (label reads 1/3), press Cancel. → Label GONE,
   status back to the tap prompt.

*Button rule*

9. Complete a 1-tap guitar measurement. → New Tap enabled; Pause and Cancel disabled.
10. With that measurement still complete, change the audio input device. → New Tap disables for
    ~3 s, then re-enables on its own. The status keeps reading "Analysis complete! N peaks
    identified…" the whole time — it must NOT change to "Ready", and must not say "Tap again".
11. New Tap, leave it listening. Measurements → **Compare…** → select 2–5 guitar measurements →
    **Compare (n)**. → Overlay on the chart. New Tap enabled; Pause and Cancel disabled.
12. Plate, 2 taps. Tap L. → Pause reads "Accept" (green), Cancel reads "Redo L", New Tap disabled.
    Accept → capturing C. Redo → re-captures L.
13. Mid-sequence, try the tap-count spinner. → Locked. Complete the measurement. → Unlocked.
14. macOS and Python only. Create a throwaway folder; turn on Dump Capture Audio and select it;
    delete the folder in Finder; press New Tap. → "Capture Audio Folder Unavailable" alert. Press **Cancel**.
    → Nothing armed: New Tap enabled, Pause and Cancel disabled.

*Web only*

15. Multi-tap guitar, live. → Count advances once per tap; no double-count, no missed tap.

**Notes on the steps.**

- **5** — `handleRouteChangeRestart` is the fourth paired site, where a flat `.idle` would drop the
  pause.
- **6, 8** — the early pause-clear was dropped from `startTapSequence`. Cancel is the way in: the
  rule disables New Tap while paused (B6) and enables Cancel, which delegates to `startTapSequence`.
  The restart is confirmed by the count label DISAPPEARING, not by it reading "0/3" — for guitar the
  label is gated on `currentTapCount > 0` (`Controls.swift:406`), so zero renders nothing. Earlier
  versions of these steps said "0/3", a display the UI cannot produce; the owner caught it,
  2026-09-22.
- **7** — a load resets to frozen, which is correct. That enablement IS the proof the load went to
  `.idle` and not `.paused`: a surviving pause would leave the sequence in flight, so Pause would
  read "Resume" and be enabled and New Tap would be disabled. It is also why the pause-clear exists —
  while paused, the analysis loop keeps overwriting the loaded peaks from live audio.
- **8** — needs its own New Tap because step 7 leaves nothing to cancel, and needs the count reset
  because loading restores the file's own tap count and type (Swift `MeasurementManagement:782`,
  Python `:749`). Cancel is only enabled for a multi-step sequence.
- **5, 10 (status)** — the settle derives the status from state instead of choosing between two
  strings (F33). Paused stays paused-worded; a completed measurement keeps its result announcement,
  because a completed measurement is not a state the settle has anything to say about. Both were
  added after the first pass, which checked only the buttons — the owner pointed out that step 10
  "says nothing about the status", 2026-09-22.
- **10** — the only route in normal use into the rule's `!(fftIsRunning && isReadyForDetection)` arm:
  `isReadyForDetection` has exactly two writes, false at `TapToneAnalyzer.swift:1821` and true again
  after `fftSettleTime` at `:1886`. It MUST be done from a completed or idle measurement, not from
  the paused sequence in step 5 — while a sequence is in flight `sequenceActive` holds New Tap
  disabled before, during and after the settle, so there is nothing to see. That was the first
  version of this step and the owner caught it, 2026-09-22. A sample-rate change or the dead-input
  watchdog's restart reach the same arm via `routeChangeRestartCount`. Denying the mic exercises the
  other term, `fftIsRunning`, but it is the same arm and B9 pins the logic, so it is optional.
- **11** — since F31 the overlay disarms the detector, so New Tap here is enabled because the
  sequence is idle, not because comparison overrides it. The override still matters for MATERIAL,
  where `sequenceActive` follows the phase rather than the detector: a plate sequence mid-phase plus
  an overlay is the case F24 was filed for.
- **14** — the disarmed-idle state that B1 and B13 pin. The guard is
  `dumpCaptureAudio && !WavDumpFolder.isReachable` (`Control.swift:104`), so the trigger is a folder
  that has become UNREACHABLE — renamed, moved, deleted, or on an ejected volume — not one that was
  never set. There is always a default folder, so "no folder set" is not a reachable state; the first
  version of this step said that and could not be run. Owner, 2026-09-22. Platform: the guard exists
  exactly where the save location is USER-CHOOSABLE — macOS (`#if os(macOS)` in `Control.swift:104`)
  and Python, which has the full equivalent: same guard (`tap_tone_analyzer.py:1311`), same dialog
  title and body, same three buttons. iOS and web write to a fixed location that cannot be changed,
  so an unreachable folder is not a state they can reach and there is nothing there to guard. The
  other two alert buttons are worth exercising while there: "Change Location…" retries and arms
  if the new folder is reachable, "Turn Off Saving" arms directly. One plumbing difference, not
  user-visible: Swift arms from the alert's button handlers, Python's helper returns a bool the
  caller acts on, plus a `pending_dump_folder_prompt` flag for a prompt needed before the view's
  signals are connected.
- **15** — detection now runs THROUGH a gated capture, with re-entry blocked in `beginCapture`. The
  REG-* baselines pass but do not exercise the live path.

Steps 5, 6 and 7 are the hand-converted sites. A failure there is a conversion mistake, not a
compiler gap.

**Run-review progress.** All three editions completed the step list (owner, 2026-09-22): Swift 1–14,
Python 1–14, web 1–13 + 15 (step 14 does not apply there — fixed save location, no folder guard).
Web's first pass was invalidated by the service worker and redone against a cleared build.

Steps 5 and 10 were then re-run on all three after F33 and F35 changed what the settle does
(owner, 2026-09-22): the status survives the settle, and so does the measurement.

F30–F35 landed together: Swift `576c3d4`, Python `a2716a5`, web `ac1925f`.

Six of the fourteen steps had to be rewritten during the review because they described what the rule
COMPUTES rather than what the screen SHOWS, or put the app in a state where the thing under test was
not observable: step 6 named a button the rule disables; the settle watch sat where a paused sequence
pins New Tap off throughout; two steps expected "0/3", which the UI cannot render because the count
label is gated on `currentTapCount > 0`; step 8 assumed a tap count that a load replaces; step 14
described an unreachable trigger on the wrong platforms. Writing steps from the model rather than
from the UI is the pattern, and it cost six round trips.

**The detector had no `@parity` group in ANY edition** — `TapToneAnalyzer+TapDetection.swift` and
`tap_tone_analyzer_tap_detection.py` were both untagged, which is why this move disturbed no group.
An untagged file is invisible to `--check`: a group that does not exist cannot be reported
divergent, which is the blind spot this sweep exists to close.

Now tagged `state/tap-detection` in all three (Swift `348f4ae`, Python `4fbf17f`, web `71408d5`),
1:1:1. It is only now worth having: until this move web's detector sat on the engine while the
natives kept theirs on the analyzer, so the group would have been lopsided.

F29 remains separately actionable and test-only — and easier now, since the seam it needs is the
same shape in all three.

**F31 — both natives leave the tap detector ARMED underneath a frozen comparison overlay, so
live audio keeps overwriting the overlay's peaks and a tap completes a measurement the user never
sees being made. (FIXED — both natives; web already disarmed. Run-reviewed, all three)**

Found at the app, by the owner, during the F30 run-review of step 10 — the step that builds a
comparison from an armed sequence. The symptom was that New Tap and **Pause** were both enabled
with a comparison showing: *"there is nothing to pause… Pressing it makes no change to the display
or state except to change the button from Pause to Resume. BUT if I then make a tap while showing
the comparison measurement the Pause button becomes disabled. Really strange state of affairs."*

The buttons were telling the truth; the model was in a state it should not have been in.
`loadComparison` sets `displayMode` and nothing else — not the detection state, not the completion
flag (Swift `MeasurementManagement:936`, Python `load_comparison`). So the detector kept listening
under a frozen overlay. Pause genuinely worked, which is why the label flipped; the chart did not
move because the chart was showing the overlay. And the tap was captured: `analyzeMagnitudes`
(`PeakAnalysis:90`) runs whenever `(isDetecting || isDetectionPaused || captureTimer != nil) &&
!isMeasurementComplete`, so it went on overwriting the displayed peaks from live audio, the tap
completed a measurement behind the overlay, and `isMeasurementComplete` going true is what
disabled Pause.

**This is a defect, not a design, and Swift already says so one function over.** `loadMeasurement`
clears to `.idle` for precisely this reason, and its comment spells it out: *"the analyzeMagnitudes
loop would otherwise keep overwriting peaksAbovePeakMin with fresh live-audio peaks on every FFT
frame."* A comparison overlay is frozen in exactly the same sense. One load path carried the guard;
its sibling did not.

**Web already had it**, with the reasoning in the comment — `if (entries.length > 0)
this.disarmDetection()`, *"An overlay is frozen, like a loaded measurement — see enterFrozen."* So
this runs the same direction F30 did: web right, both natives carrying the defect. Third time in
S6 that a native/web split turned out to be a native defect rather than a port difference.

**The fix** is the guard, in both natives: disarm when the overlay is non-empty. It deliberately
does NOT set `isMeasurementComplete` — matching web, and giving the coherent button state for a
comparison (New Tap enabled, Pause and Cancel disabled). An EMPTY comparison leaves the mode `live`,
so there is nothing to freeze and the detector is left exactly as it was: the mode follows the data,
and so does the disarm.

**Tests: CP-U9 and CP-U10, paired in all three.** CP-U9 pins the disarm, CP-U10 pins that an empty
comparison leaves a running detector alone. Python uses a real `TapToneAnalyzer` rather than the
file's `_StubAnalyzer`, because the behaviour under test IS the detection-state property. Mutation:
removing the disarm from production fails exactly CP-U9 and nothing else. Swift **569**, web
comparison suite 21 (was 19).

**A design question the run-review opened, NOT yet decided.** If Comparison is understood as a
measurement *type* rather than a display state, then "New Tap" in a comparison is a category error —
a comparison is not made by tapping, and what the button does instead is change the measurement type
without naming one. Three readings were put up: (A) today's, New Tap silently starts the current tap
type; (B) New Tap disabled in a comparison, leave it by choosing a type; (C) New Tap means "new
measurement of the current type", so in a comparison it relabels to "New Comparison" and reopens the
browser — which fits the existing idiom where Pause/Cancel relabel to Accept/Redo during a material
review. B and C both depend on measurement-type selection being a visible control rather than buried
in a Settings sheet, which is the actual blocker and is a separate piece of work. **Undecided;
recorded here so the reasoning is not lost.** The disarm above is required under all three.

**F32 — Python's `is_ready_for_detection` was a plain attribute with no notification, so the
button row went stale for the whole route-change settle and New Tap never greyed out.
(FIXED — all three, run-reviewed)**

Found at the app during the F30 run-review of step 10, on Python: *"I do not see the New Tap disable
at all."* The route-change path itself was correct — `handle_route_change_restart` stands readiness
down at `tap_tone_analyzer_control.py:359` and restores it at `:436`, 3 seconds later, mirroring
Swift's `fftSettleTime`. What was missing was anyone telling the view.

| | readiness during a route change |
|---|---|
| Swift | `@Published var isReadyForDetection`, false for a 3 s settle — every bound view re-renders, New Tap greys out |
| Python | same 3 s settle, but a plain attribute with **no signal** — nothing refreshed |
| web | **no settle at all.** `isReadyForDetection` is declared at `tapToneAnalyzer.ts:146` and never written or read: not on the snapshot, not passed to `buttonRule`. `handleDeviceChange` only sets a status message. |

`_update_tap_buttons()` only runs when something calls it, so the buttons held whatever state they
were in before the device change, through the settle and out the other side. The user-visible effect
is that Python's New Tap stays clickable for ~3 seconds while the engine is reinitialising, where
Swift and web disable it.

**The port had already solved this once, for the neighbouring flag.** `detectionStateChanged` exists
precisely because Python has no `@Published`, and its comment states the principle: *"Swift's
`detectionState` is @Published, so every view bound to it re-evaluates on ANY change… Python has no
such binding: without this signal the view could only sample the state inside some other slot, which
meant a state change alone never refreshed anything."* Readiness needed the same treatment and never
got it — the gap is the second half of a pattern whose first half is already in the file.

**The fix** follows that precedent exactly: `is_ready_for_detection` becomes a property over
`_is_ready_for_detection`, emitting a new `readyForDetectionChanged` on an actual change (same-value
assignments stay silent); `FftCanvas` relays it beside `detectionStateChanged`; the view connects it
to a slot that re-runs `_update_tap_buttons()`.

**Tests: a new 1:1:1 group, `test/notification`** — `StateNotificationTests.swift` /
`test_state_notification.py` / `state-notification.test.ts`, three cases each (N1 readiness cleared
notifies, N2 restored notifies, N3 the production route-change path clears and notifies).

They were first written Python-only, in `test_wi10_qtimer_slots.py`, tagged `@parity none`, on the
grounds that signal plumbing is PySide6-specific with no counterpart. The owner rejected that: *"they
do have an equivalent to test — when the data changes does the UI get updated — in the swift/web case
it is caused by react pattern — unless someone breaks it."* Exactly right. The contract is not "does
Qt emit" but "does a state change reach the UI", which all three implement and all three can break —
drop the `@Published`, never add the signal, leave the field off the snapshot. And `none` is the one
home where `--check` can never report a missing edition, so parking it there guaranteed the gap
stayed invisible. This is PARITY-TEST-METHOD rule 4 — *an "n/a" that rests on the view layer is a
finding, not a difference* — written into this document three screens above the place it was ignored.

**Web was a third case, and it is fixed too.** The first version of this entry claimed web was fine
because the snapshot and `notify()` cover it — asserted without checking, and wrong. Web declared
`isReadyForDetection` and no path ever wrote or read it: a dead field of exactly the shape
`currentTapCount` turned out to be on `ButtonState`. `handleDeviceChange(settling)` set a status
message and nothing else, so New Tap's enablement during a device change followed only `running`.

Owner's call: web gets the behaviour. `handleDeviceChange` now sets `isReadyForDetection = !settling`
— the method already received exactly the right boolean on both edges — the field is on the snapshot,
and `App.tsx` passes it to `buttonRule`.

**And the settle windows now match.** Swift is 3.0 s (`fftSettleTime`, commented as extended from 2 s
to absorb HALC/CoreAudio startup transients at ~2.5 s), Python mirrors it, web was **1500 ms** with no
recorded reason. The settle is how long New Tap stays disabled after a device change, so a different
number is a different user-visible behaviour, not an implementation detail. Web is now 3000 ms.

**Pre-existing, not caused by F30** — nothing in the enum or the button-rule extraction touched
`is_ready_for_detection`. It was invisible because no test constructs the view, which is the same
blind spot that let the button rule live in two copies: the rule is now production code and pinned,
but the view's WIRING to it is still unpinned in every edition.

**F33 — the device-change settle CHOSE a status string instead of deriving one, so it was wrong in
both directions: mid-sequence it gave the opening instruction, and on a finished measurement it threw
the result away. (FIXED — all three, run-reviewed)**

Found at the app during the F30 run-review of step 10 on web. The owner completed a 1-tap generic
measurement, changed the input device, and the status read **"Tap 1/1 captured. Tap again…"** on a
sequence that was done. Raising the tap count to 3 then left the progress bar showing 1/3 while the
text still said 1/1 — a consequence, not a second defect: the status is only refreshed on a count
change while armed and at zero taps (Swift `numberOfTaps.didSet`, and web's equivalent), so a string
that already embedded the wrong N simply stayed.

**The owner's framing is what settled it.** *"Swift is telling you what to do while the web's message
is telling you something you did. They are not the same state. If I have not made a tap then 'Tap 1/3
captured' is wrong and 'tap 3 times' is correct. If I have completed a tap then 'Tap 1/3' is correct
and 'tap 3 times' is wrong. So which is it?"* Both — conditioned on the count. Any message that
ignores the count is wrong half the time, and the settle was picking between exactly two:

| | at the settle |
|---|---|
| Swift / Python | `tapPrompt()` when detecting, `"Ready"` otherwise — wrong mid-sequence ("Tap the guitar 3 times…" with a tap already captured), and discards "Analysis complete! N peaks…" |
| web | `restingPrompt()` — count-aware, but with no completion check, so a finished measurement was told to tap again |

**Fixed by deriving rather than choosing**, which is the principle this project already adopted for
status (Swift's own doc comment calls `guitarLoopStatus` "status derived from the current state", and
the status state-machine alignment made the natives derived-from-state to match web). The settle was
a leftover imperative assignment that never joined that derivation — in all three editions, with
three different guesses.

`statusAfterSettle()` / `_status_after_settle()` now returns the status for the current state, or
**nothing** where the status is a RESULT announcement rather than a prompt: complete → leave it,
comparison → leave it, paused → the paused literal, detecting → `armedPrompt()`, else `"Ready"`. The
second question this raised — whether the settle should be allowed to clobber "Analysis complete!" —
is answered by construction rather than by a decision, because a completed measurement is no longer a
state the settle has anything to say about.

`armedPrompt()` was extracted from `resumeTapDetection()`, which held the only "restore a
context-appropriate prompt" logic in the app and never shared it. Resume and the settle now call one
function per edition, so they cannot drift apart again. The paused literal likewise became one
constant per edition instead of a string repeated at each site.

**A rename that had missed a site.** Extracting the prompt forced the plate longitudinal label into
the open: Swift said "Ready for fL tap" when ARMING a plate sequence and "Ready for L tap" when
RESUMING the same one, while Python and web said "fL" throughout — and web's comment claimed it
"mirrors Swift", which it did not. Python's version was `"Ready for fL tap" if is_brace else "Ready
for fL tap"`, a dead conditional with identical arms that had been sitting there looking deliberate.
Owner: *"when we renamed the way phase taps were labeled we missed one. Fix Swift."* One occurrence,
no test pinned it.

**Tests: N4–N6 added to `test/notification`, paired in all three** — a complete measurement keeps its
status, mid-sequence reports progress, idle gives "Ready". They pair only because the derivation is a
directly callable function; the first version of the web fix could be tested and the natives could
not, which was a sign the fix was in the wrong shape.

**Process note.** The first fix here was option 1 of two the owner had been offered, implemented
before the answer came back, on the reasoning that it was "the standing rule so not really a
decision". It was a decision, it was the wrong branch, and the owner's reply was an analysis rather
than a verdict. Swift **575**, Python **679**, web **607**.

**F34 — web DERIVED the progress bar at render time where Swift and Python STORE it, so raising the
tap count retroactively shrank a finished measurement's bar. (FIXED — web; the natives already
stored it and gained the regression test. Run-reviewed)**

Found at the app by the owner, on web, during the F30 run-review: complete a 1-tap generic
measurement, then increment Taps without pressing anything else. Web's full bar dropped to a third;
Swift's stayed full. *"The web changes the progress bar before New Tap is pressed while swift does
not. I believe that python follows swift."* It does.

| | `tapProgress` |
|---|---|
| Swift | STORED `@Published`, written at each capture site and pinned to `1.0` at completion (`SpectrumCapture:739`, `:1273`, `Control:438`) |
| Python | the same, at the same sites (`spectrum_capture.py:899`, `:1551`, `control.py:665`) |
| web | `get tapProgress()` — a computed getter, re-derived on EVERY render |

So in web the bar was a live function of `currentTapCount / numberOfTaps`, and the tap-count stepper
is (correctly) enabled once a measurement completes — so configuring the NEXT measurement rewrote the
record of the one just finished. The getter's own comment said it "Mirrors Swift `tapProgress`",
which it did not: rule 6 again, and the fourth confidently-wrong comment this sweep has turned up.

**Which behaviour is right** was not in doubt once stated: the bar records what was MEASURED. A later
count change configures the next measurement and has no business rewriting a completed one. Swift and
Python were correct; web was fixed to match.

**The fix, and a wrong turn worth recording.** The first attempt mirrored Swift literally — an
explicit `syncTapProgress()` after each of the twelve internal `currentTapCount` assignments. That
failed on the first test run, because App and the tests assign `currentTapCount` directly and bypassed
every one of them. `currentTapCount` is now an accessor pair whose setter snapshots `tapProgress`, so
the snapshot happens on every write regardless of origin. Swift and Python do not need this: their
external writers go through the model. The test caught it within seconds of being written, which is
the argument for writing the test before believing the fix.

**Tests: one paired case in `test/tap-progress`**, all three — a complete 1-tap measurement keeps a
full bar when Taps is raised to 3. It passes trivially on the natives; that is the point, since it
pins them against anyone making it derived later. Swift **576**, Python **680**, web **608**.

**A note on the environment, not the code.** Three Swift runs failed oddly while this landed — missing
test fixtures, then `CodeSign failed ... code object is not signed at all`. All one cause: an
`xcodebuild` and the owner's Xcode session sharing one DerivedData, which left
`GuitarTapTests.xctest` corrupt inside the app bundle and poisoned every later run. `xcodebuild clean`
cleared it. Worth checking `pgrep -fl GuitarTap.app` before believing a Swift failure is real.

**F35 — the device-change settle blanked the chart on a guard that asked the wrong field, wiping
completed measurements; `displayMode` was carrying two facts and one of them was already held by
`isMeasurementComplete`. (FIXED — all three, run-reviewed)**

Found at the app during the F30 run-review, and only because a step MOVED. The settle watch started
life as step 6, run while paused mid-sequence; the owner pointed out New Tap never toggles there, so
it became step 10 — after a completed measurement. That is the first time this path had ever been run
with a finished result on screen, and it exposed two defects at once: F33's stuck status, and this.

**The guard.** `handleRouteChangeRestart` blanked the spectrum and cleared `allPeaks` /
`identifiedModes` when `displayMode == .live`, meaning "a live spectrum is showing". But **no
completion path sets `.frozen`** — not guitar `processMultipleTaps`, not brace, not either plate
finaliser. Only `loadMeasurement` does. So a freshly captured measurement is still `.live`, got
blanked, and nothing restored it: `analyzeMagnitudes` is gated on `!isMeasurementComplete`, so the
live loop never repaints, and the settle's restore only put `displayMode` back.

**Provenance, because the owner pushed twice and was right to.** First answer was "it's pre-existing,
not in my diff" — true but not an answer to "when". `git log -S` puts it at **`a086638`, build 264,
25 April 2026**, *"Fix audio engine restart crash. Clean-up mic hot switch."* The owner's build 213
predates it and does not blank. So: a regression, eight months old, never exercised in this state.
Web never had it; Python inherited it in the port.

**The owner's test was the right one.** Comparing web against Swift — rather than before-and-after in
one edition — settled it immediately: web keeps the measurement, Swift wipes it. Third time in this
sweep that web-vs-native was the discriminating experiment.

**Why the intent was right and the guard wrong.** Blanking a LIVE spectrum during a device swap is
correct — otherwise the old device's noise floor lingers as though it were current. `displayMode ==
.live` simply is not the question; `isMeasurementComplete` is.

**Fixed in two parts.**

*One — the honest guard, and a flag for the blank.* The guard is now `!isMeasurementComplete &&
displayMode != .comparison`, and the transient blank is an explicit `isSettling` / `is_settling`
rather than a borrowed `displayMode = .frozen` write. Python needed two sites Swift did not, both of
which would have failed silently: its per-frame handler branched on `FROZEN` to emit the blank, so
without the new check it would have drawn the new device's not-yet-valid audio; and its canvas had
the mirror of Swift's chart read. Web did not blank at all — the opposite divergence — and now does.

*Two — `.frozen` deleted.* Once the settle stopped borrowing it, nothing in any edition distinguished
`.frozen` from `.live`: Swift had no production reads, web never had any, and Python's two were
redundant with `is_measurement_complete` and unreachable besides. It is runtime-only — absent from the
`.guitartap` format and from settings — so removal touches no saved data. `AnalysisDisplayMode` is now
`live | comparison` in all three; both writers per edition set `live`, Python's dead branches are gone,
and the five test assertions (Swift 2, web 3, Python 0 — the coverage was already asymmetric) now
assert `live`.

**Tests: N7 and N8, paired in all three** — a completed measurement survives a device change; a live
spectrum is blanked for the settle and restored after. Mutation: restoring the old
`display_mode == LIVE` guard fails N7 alone. That test did not exist for eight months.

**The fourth instance of one shape.** F30's `isDetecting`/`isDetectionPaused`, F33's settle choosing
between two strings, and now `displayMode`/`isMeasurementComplete` twice over — two fields describing
one fact, call sites guessing which to trust. Each time the fix was to delete the redundant one rather
than keep them in sync. Swift **578**, Python **682**, web **610**.

**`test/tap-count-change` (6/6/6) — the cases are in parity. The code under them is not.
(read 2026-09-22)**

The best-aligned slug S6 has produced: two suites per edition, 3 + 3 cases, the same three prompt
assertions and the same three OUT-5 "no implicit finalise" assertions, asserting identical strings.
All three reach production. Web's fixture is the strongest — it drives `startTapSequence` →
`beginGuitarAccumulation` → `recordGuitarTap` where both natives poke `currentTapCount` /
`captured_taps` directly.

`--check` is happy, the case lists agree, and the slug still yielded five findings. Two of them are
reachable and user-visible today. The reason is one sentence: **every case in every edition is
guitar**, and the hook they exercise is used by plate and brace as well.

Two fixture details are worth keeping, because they are what made F36 invisible rather than obvious.
Swift's prompt fixture sets `currentTapCount = 0`; Python's sets `captured_taps = []`. Each sets the
field its own edition's guard happens to read, so each passes against its own divergence and neither
could ever catch the other's. That is the "fixture encoding a contract" shape (method rule 1) turned
inward: not a contract the app no longer sends, but a contract only *this* edition has.

**F36 — the tap-count hook was written for guitar and never revisited, so changing Taps during a
plate measurement writes the guitar prompt over it. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

Start a plate measurement. Before the first tap the Taps stepper is unlocked — the lock is
`currentTapCount > 0 && !isMeasurementComplete`, and the count is 0 — and detection is listening.
Change Taps from 1 to 3:

| | what the status bar says |
|---|---|
| Swift | **"Tap the guitar 3 times..."** |
| Python | **"Tap the guitar 3 times..."** |
| web | "Ready for fL tap (×3 each for L, C)" |

Reachable from the UI, user-visible, wrong in two editions. Web is correct, and this is the fourth
time in this sweep that the web-vs-native comparison was the discriminating experiment.

**Part one — the prompt.** Both natives call `tapPrompt()` / `_tap_prompt()`, whose own docstring
calls it "the guitar resting prompt". Each edition already owns the mode-aware alternative:
`armedPrompt()` (`TapToneAnalyzer.swift:329`) and `_armed_prompt()` (`control.py:72`), **both added
three days ago by F33**, which extracted exactly this logic for exactly this reason. The hook calls
the wrong one. Web calls `restingPrompt()`, which dispatches on type and then on phase, and whose
default arm returns `materialArmPrompt()` — the string carrying the "×N each for L, C" the user just
changed.

**Part two — the zero-check.** The same guard is written three ways:

| | guard |
|---|---|
| Swift | `isDetecting && currentTapCount == 0` |
| Python | `is_detecting and len(captured_taps) == 0` |
| web | `!isMeasurementComplete && isDetecting && currentTapCount === 0` |

Python reads the **within-phase buffer**. Its own production code says why that is wrong, at
`tap_tone_analyzer_spectrum_capture.py:1259-1267`: `captured_taps` is cleared at every phase
completion, `current_tap_count` is cumulative across L → C → FLC, "the two are different things and
Swift keeps them apart", and deriving one from the other has already caused a bug once (the progress
bar resetting each phase, and a "Tap 0/N" label). So Python's guard is true at the start of *every*
phase, not only at the start of the measurement.

Web's extra `!isMeasurementComplete` term is harmless — completion sets `detectionState` to idle in
all three — but it is a third spelling of one predicate, which is how the first two came to differ.

**The fix is to call the function F33 already wrote**, and to settle the guard on the cumulative
count in all three. Needs a plate run-review: change Taps before the first tap.

**Done as described, 2026-09-22.** Both natives now call `armedPrompt()` / `_armed_prompt()` from the
hook, and all three guard on the cumulative `currentTapCount`. Web's third spelling — the extra
`!isMeasurementComplete` term — is gone: completion sets `detectionState` to idle in every edition,
so `isDetecting` already covered it, and three spellings of one predicate is how the guards came to
differ. Owner's call, 2026-09-22, on which way to level it: delete it from web, since Swift is
canonical.

**Tests: four material cases per edition**, taking `test/tap-count-change` from 6/6/6 to **10/10/10**
— the fL arm prompt after a raise, the FLC variant, the brace variant, and the guard case at a later
phase. Mutation caught all of them.

**One of those four was worthless when first written, and mutation is what said so.** The guard case
set the status to the string the derivation *also* produces, so "the hook stayed silent" and "the
hook fired" were indistinguishable and swapping the guard back to the phase buffer still passed —
PARITY-TEST-METHOD rule 1's "assertion that holds by construction", written by someone who had just
read that rule. It now uses the string a REDO leaves on screen, which the derivation never produces.

**F37 — `armedPrompt()` restores a DIFFERENT string from the one the phase actually shows, so a
device change silently rewords the instruction mid-plate. And the preserve path it was to be fixed
with was itself broken. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

Found while verifying F36's part one, in the function F36 recommends calling.

| phase | the live prompt, set when the phase begins | what the settle restores |
|---|---|---|
| capturing fC | "Rotate 90° and tap for fC" (`Control.swift:381`, `control.py:938`) | **"Ready for fC tap"** |
| capturing fLC | "Set up for fLC tap, then tap" (`Control.swift:387`, `control.py:947`) | **"Ready for fLC tap"** |

Web's `restingPrompt()` returns the same strings the phase set, so a device change mid-plate leaves
the instruction alone. Both natives replace a specific physical instruction — rotate the plate, set
up for the FLC tap — with a generic one. The user is mid-measurement and the app has just forgotten
what it told them to do.

This is inside **F33's own path**, which is marked FIXED and run-reviewed. The run-review was step 10,
executed **after a completed measurement**; mid-plate at phase C was never run. That is the same
reason F35 survived eight months — a path exercised in one state and declared correct in all of them.

Fixing F36 by routing the hook through `armedPrompt()` makes this reachable from a second direction,
so the two are one change.

**The fix is not to derive it better — it is not to derive it at all.** The owner's question,
2026-09-22: *"It may not be a divergence but it may be wrong?"* It is. Two strings are correct at
(plate, capturingCross, armed) — the advance's "Rotate 90° and tap for fC" and a redo's "Ready for fC
tap — tap again" — so the prompt is not a function of the state the analyzer holds. Modelling the
entry path would not help either: after a device swap the user has **already rotated the plate**, so
instructing them to rotate it is wrong however it is derived.

F33 had already drawn this line and filed the material prompts on the wrong side of it. Its own
comment says a completed measurement's status is "a RESULT announcement rather than a live prompt …
not re-derivable and must not be thrown away". A phase instruction is the same kind of thing.
`statusAfterSettle()` now returns nil for an armed material phase, and `restoredStatus(before:)`
puts back what was showing. Guitar still derives, and should: its prompt is a pure function of count
and total, both of which the analyzer holds.

The two callers wanted opposite things, which was the actual defect — the tap-count change must
RECOMPUTE, the settle must PRESERVE — and one function was answering both.

**The check the owner asked for before any of this was written found the preserve path broken.**
All three captured `statusMessage`, the OVERRIDE-RESOLVED string, where each keeps the underlying
value in `latestRealStatus` for exactly this purpose. So a route change while the input was clipping
preserved the warning sentinel and put it back as though the analyzer had set it. Web and Python were
worse than Swift: their write path stores the argument as the real status, so the sentinel BECAME the
real status and clearing the condition restored the warning. Already reachable before this change —
`statusAfterSettle()` has returned nil for a completed measurement since F33 — so widening it to
armed material would have widened a live defect. All three now capture `latestRealStatus`.

**And the resolver was two-of-three.** Python's `_set_status_message` resolved clipping inline and
ignored `input_appears_dead`, though `_apply_status_overrides()` sat ten lines below with Swift's
precedence — so any status write dropped the dead-input warning. Web had no resolver and **no
dead-input status at all**: its engine detects a silent input, warns to the console and retries, and
`realtimeFFTAnalyzer.ts:520` sets `inputAppearsDead` — which nothing read. The seam was even
documented, "set by the owner to surface 'no audio input' in the status line", and never wired. Web
alone told the user nothing. Now all three resolve through one precedence rule (dead input, then
clipping, then the analyzer's own status) and web has the warning, the resolver and the wiring.

Owner's call, 2026-09-22, on whether to file these separately: *"Who does that help … does it just
delay the fix?"* The Python resolver was not separable — it is one line inside the function whose
input was already changing, so filing it produces a paragraph and no work item. Web's dead input was
separable by mechanism but is a user-visible divergence, which rule 7 says is fixed in the same
change. *"Let's not create more delayed problems to fix."*

**One structural change beyond the findings.** Swift held the pre-settle status in a LOCAL where both
ports hold a field, so the capture was unobservable and only two editions could pin it. It is now a
stored property, matching Python `_status_before_settle` and web `statusBeforeSettle`.

**A residual, recorded rather than fixed.** After a redo the phase shows "Ready for fC tap — tap
again" and the ARM path would say "Rotate 90° and tap for fC". Nothing rewrites it now, because
nothing re-derives it — but the two strings still describe one phase. Not a divergence; all three
behave identically.

**Tests: N9–N12, paired in all three**, taking `test/notification` from 8/8/8 to **12/12/12**. N9 —
the settle preserves a material phase instruction. N10 — the override precedence, including that an
ordinary status write while the input is dead keeps the warning. N11 — the settle captures the real
status, not the sentinel. N12 — the phase ADVANCE and the armed DERIVATION produce the same string,
pinned from both ends.

**N12 exists because mutation found a hole the other three left.** Drifting the advance's literal
back to "Ready for fC tap" passed every test in all three editions — the exact defect F37 is, still
undetectable after the fix. Nothing had ever pinned the string the advance writes.

Swift **586**, Python **690**, web **618**. Parity map clean at 103 groups.

**The run-review this needs, which no existing step covers.** On each edition: (1) start a plate
measurement and change Taps before the first tap — the prompt must name the new count and stay a
plate prompt; (2) mid phase-C, pull the microphone — the instruction must come back unchanged, not
reworded; (3) unplug the mic entirely — all three must now show "⚠ No audio input", web included.

**F38 — Python's `number_of_taps` is a plain attribute where Swift enforces the hook on every write,
and two Python paths write it directly. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

| | the hook | fires on |
|---|---|---|
| Swift | `didSet` on `@Published var numberOfTaps` | **every assignment**, including the load and file-playback paths |
| Python | `set_tap_num()`, a method | only the spinner |
| web | `setNumberOfTaps()`, a method | the stepper and both load paths |

`load_measurement` (`tap_tone_analyzer_measurement_management.py:751`) and `play_file_for_testing`
(`tap_tone_analyzer.py:802`) both assign `self.number_of_taps` directly and skip the hook entirely.

No user-visible effect today: Swift's `didSet` fires on load but is a no-op there, because
`loadMeasurement` sets `detectionState = .idle` at `:709` — thirty-five lines before it writes
`numberOfTaps` at `:784` — so the guard is false. The correctness rests on statement order in a
method neither port shares.

This is **F25 exactly** — "Python's completion flag is a plain attribute where both other editions
enforce a setter" — which was fixed for `is_measurement_complete` by making it a property. The same
shape is still present one field over. The fix is the one already proven in this file: make
`number_of_taps` a property whose setter holds the logic, and let `set_tap_num` become a thin wrapper
or disappear.

**Done for this field, 2026-09-22.** `number_of_taps` is now a property whose setter carries the
hook, so the load and file-playback paths can no longer bypass it. The `max(1, n)` clamp in
`set_tap_num` went with it: Swift's `didSet` has no model-layer clamp, and the spinner already bounds
the value 1–10 in the view exactly as the Swift and web steppers do — keeping it was the divergence.

**And then the owner stopped the pattern.** *"Didn't we work on this early today or yesterday? Why is
it coming up again?"* It had: **F25**, **F32**, **F34** and now F38 are one defect wearing four names
— state whose notification lives in a separate method, with the plain field writable beside it. Each
was fixed on the field, never on the class, so the next was guaranteed. This finding's own text says
so and then proposes fixing one more field.

The sweep that followed measured all three editions. Its result — that Swift has zero instances, that
web is **not** an instance and must not be "fixed" into one, and that the three editions' observable
surfaces are shaped by three different questions — is recorded in
[`RESTRUCTURE-NOTES.md`](RESTRUCTURE-NOTES.md) under "The observable surface", because the owner
routed it to #1 on 2026-09-22: *"it is what I think is required — i.e. ideally it would be the same
observable set expressed the same way, so both."* Two live Python defects it turned up are **F41**.

**F39 — the tap-count lock is a fourth rule, triplicated in the views, and Python's copy reads a
view-local cache instead of the model. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

The lock is deliberately **not** part of `buttonRule` — Swift says so at `TapToneAnalysisView.swift:220`,
and the reason is sound: that rule answers which of the three action buttons are live, and a numeric
input's lock is a different question about a different control. The owner's call stands. What follows
from it is that the expression is written three times, and one of them reads a different field:

| | expression |
|---|---|
| Swift | `tapToneAnalyzer.currentTapCount > 0 && !tapToneAnalyzer.isMeasurementComplete` |
| web | `currentTapCount > 0 && !snapshot.isMeasurementComplete` |
| Python | `self._tap_count_captured > 0 and not is_complete` |

`_tap_count_captured` is a **view field**, fed by the `tapCountChanged` signal and hand-reset in five
more places. One of those five exists to paper over a model reset that emits nothing:
`load_measurement` sets `current_tap_count = 0` with no `tapCountChanged.emit`, and the view resets
its own copy at `tap_tone_analysis_view.py:4446` — where the comment says so outright. The other
three model resets do emit. Its comment claims it mirrors Swift's expression; it computes the same
value today.

Fifth instance of **two fields describing one fact**, this time across the model/view boundary rather
than within the model. The other four were each fixed by deleting the redundant field, and the same
applies: read `analyzer.current_tap_count`.

**Done, 2026-09-22 — one line.** The lock reads the model; the mirror stays for the LABEL, which is
legitimately push-fed by the signal's payload. That distinction is the whole finding: a label may
render whatever the last signal carried, but a *rule about model state* has to ask the model.

**No behaviour changed** — all four states (0/2 taps × complete/incomplete) were already correct, and
were verified so after the change. Owner's framing, 2026-09-22, on why it was still worth doing:
*"since we want to remove as much structural divergence as possible that implies that F39 should have
a change in the Python code."*

**No test.** The lock is the one rule with no coverage in any edition — it is deliberately outside
`buttonRule` (see above), and no edition tests its view-layer expression. Verified instead by driving
`_update_tap_buttons()` headlessly through the four states. Recording that gap rather than papering
over it: a Python-only test would be the kind of one-sided coverage this sweep keeps finding.

**F40 — web carries a dead copy of a native model field while the real state sits in the view, and
the slug's own test file contradicts itself. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

`TapToneAnalyzer.showLoadedSettingsWarning` (`state/tapToneAnalyzer.ts:280`) is declared `false` and
set `false` once, at `:322`. It is never set true, never read, and not in the snapshot type. The
banner the user sees is a React `useState` in `App.tsx:240`, cleared at five sites and raised at two.
Both natives hold the flag on the model and clear it from four model sites, one of which is the
tap-count hook — which is how this surfaced here rather than under a banner slug.

A small F24: state that belongs on the analyzer left in the view, with a stub on the analyzer that
makes it look otherwise. Noted rather than filed separately because it is on the path this slug
touches (`dont-fragment-work`), and because the stub is what would make a future reader believe the
web already holds the flag.

Separately, `test/tap-count-change.test.ts` disagrees with itself. Lines 20-21 say the reduce-count
branch "is NOT pinned 3-way: it diverges — Swift defers with 'All taps captured. Processing…',
Python's `set_tap_num` processes synchronously. Tracked in 6-TEST 4c." Lines 46-52 of the same file
say the branch was removed from every edition and that the tests below pin the removal. The second is
correct. The first is a load-bearing sentence that was true when written — CROSS-EDITION rule 6, and
the fifth confidently-wrong comment this sweep has turned up.

**Done, 2026-09-22 — the state moved, not the stub deleted.** Owner's call, and it corrected mine:
*"since we want to remove as much structural divergence as possible … the first option (a) for F40 is
to move the state on the web's analyzer so divergence is removed. But it is not #1 — it is finding
and fixing divergence as we can. This is not the same magnitude of work that we delayed earlier."*
That distinction is worth keeping: #1 is unifying the whole observable surface; this is one field with
a known destination, the same size as F24, which was also done here.

`showLoadedSettingsWarning` is now analyzer state and on the snapshot. The clears live where the
natives keep them — `startTapSequence` (Swift `Control.swift:149`), `setNumberOfTaps` (Swift
`numberOfTaps.didSet`), and the completion setter, which already had it. The raises live in
`loadMeasurement` and `restoreMaterial`. `App.tsx` lost the `useState`, five clear sites and two raise
sites, and the banner now renders from `showLoadedSettingsWarning && !isSavedMeasurementComparison`
— Swift's own view gate, which makes the comparison clear site unnecessary rather than merely moved.

### The divergence the move uncovered: web's banner misattributed the user's own threshold to the file

Worth stating at length, because it is the most consequential thing in F40 and neither this finding
nor the sweep predicted it.

**The banner names two numbers, and it renders the LIVE ones.** All three editions draw
"Settings from loaded measurement — Threshold: N dB · Taps: M" from current state —
`tap.tapDetectionThreshold` / `tap.numberOfTaps` in Swift
(`TapToneAnalysisView+Controls.swift:377` and `:478`), the equivalents in Python and web. Nothing
stores the file's values for display. That design is fine, and it is fine *only* because the banner
is dismissed the moment either number stops being the loaded one. **The label is a claim about
provenance; the numbers are live state; the clears are the entire mechanism keeping the claim true.**

Swift and Python clear on both numbers:

| the banner names | Swift clears at | Python clears at | web cleared at |
|---|---|---|---|
| Taps | `numberOfTaps.didSet` | `set_tap_num` | `changeTaps` (view) |
| Threshold | `tapDetectionThreshold.didSet` | `set_tap_threshold` | **nowhere** |

**So on web the banner did not go stale — it lied.** Load a measurement captured at −45 dB with 3
taps and the banner correctly reads "Threshold: −45 dB · Taps: 3". Drag the threshold slider to
−30 dB and it reads "Settings from loaded measurement — Threshold: −30 dB · Taps: 3". The user's own
value, presented as the file's.

**Why that is worse than a cosmetic defect.** The tap threshold is a capture parameter. This
application has an entire provenance apparatus — the microphone match, the calibration comparison,
the sample-rate check, `measurementWarning` — built so a luthier can tell what a saved measurement
was actually taken with, and whether a new tap is comparable to it. A banner that misreports the
file's threshold corrupts precisely the judgement that machinery exists to support, and it does so
in the one place the user is told to look.

**Why it stayed invisible.** The banner is correct when it appears and only becomes false on a later
action — moving a slider — that has nothing to do with loading. No edition tested it: web's MC8
asserted the completion clear against the dead copy (see below), and the flag had no other coverage
anywhere. And no run-review step has ever touched the threshold slider after a load.

**Why the sweep found it.** Only because moving the state forced every clear site to be laid against
the natives' one by one. **A missing clear has no line number** — it cannot be grepped for, and
reading web on its own would never have shown it. It is visible only in the diff between two
editions' lists, which is the argument for this whole issue in one sentence.

**Deliberately NOT folded in:** web's `tapDetectionThreshold` lives in `settings`, not on the
analyzer, so the view has to report the deviation where the natives do it inside the threshold's own
setter. That is a separate divergence, named in the code at `noteLoadedSettingsDeviation()` rather
than quietly widened into this change.

**MC8 had been passing against the corpse.** Web already asserted that completion clears this flag —
and had done so for months against a field the application never read. Not a test-local helper this
time (method rule 1's first shape) but its mirror image: a real production field that no production
path consumed. The test was true and meaningless.

**Tests: MC9-MC11 in web, MC9-MC10 in both natives** — a new sequence clears it, a tap-count change
clears it, and (web only, because only web's load path can be driven from a unit test) a load RAISES
it and survives the completion clear. That last one pins an ordering dependency Swift carries between
`MeasMgmt:709` and `:834`: the completion setter clears the flag, so the raise must come after.
Mutation confirms it — moving the raise one line earlier fails MC11, and the three other rules each
fail their own case when removed.

**Recommended order**, all three editions, tests paired and mutated:

1. **F36** — route the hook through `armedPrompt()`; settle the guard on the cumulative count.
2. **F37** — `armedPrompt()` returns the phase's own string. One change with F36.
3. **F38** — `number_of_taps` becomes a property in Python, as F25 did.
4. **F39** — Python's lock reads the model.
5. **F40** — delete the dead field; fix the self-contradicting comment.

1 and 2 are user-visible and are method rule 7 — fixed now, not logged. They need a **plate**
run-review, which no existing step covers: change Taps before the first tap, and pull the mic mid
phase-C. 3, 4 and 5 are structural and have no run-review. 5 is comment-and-dead-code only.

The tests to add are the ones whose absence let all of this through: **a material case in this
slug**, in all three editions.

**F41 — a loaded measurement's microphone warning is never reset, so it survives onto the NEXT
measurement and describes one that is no longer on screen. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

Found by the F38 sweep, which went looking for a different defect and produced a wrong answer twice
before this one. Both wrong answers are recorded below, because the second nearly broke working code.

**The defect.** Neither native resets `microphoneWarning` / `microphone_warning` when a measurement
loads. Both assignments sit *inside* the "does this file name a microphone?" test — Swift
`if let uid = measurement.microphoneUID {` with no `else`
(`TapToneAnalyzer+MeasurementManagement.swift:824`, `:830`), Python `if mic_uid or mic_name:`
(`tap_tone_analyzer_measurement_management.py:809`, `:823`). So:

> Load A, whose microphone does not match → the warning appears. Load B, whose file records no
> microphone at all → the block is skipped entirely, and **A's warning is still on screen**, now
> attached to a measurement that is not displayed.

**Web is correct**, and by construction rather than by care: `setLoadWarning(measurementWarning(m, …))`
runs on every load and takes `null` when there is nothing to say, so it cannot go stale. Fifth time in
this sweep that the natives are wrong and web is right, and the third time the fix is "assign
unconditionally" rather than "remember to clear".

This is a user-visible cross-edition divergence, so method rule 7 applies: it is fixed, not logged.
The fix is to compute the warning once per load in both natives, web's shape.

**Written after the owner's question settled it — one line.** *"Since the banner is modal (or at
least the popup is modal) how can anything proceed without acknowledging the microphone warning?"*
That killed the original reading: the warning IS modal in both natives, so a second load cannot
happen with the first warning still up. What remains is smaller — Swift CONSUMES the warning on
acknowledgement (its alert's OK button and the binding's setter both clear it), while Python only
displayed it and left the field set. Invisible except to the import handler, which reads the field
directly and would fold a previous measurement's warning into the success message for a file that
records no microphone of its own. Python now clears it after the dialog, guarded on the value still
matching so a newer warning raised meanwhile is not wiped.

**NOT VERIFIED — the Python suite has not been run since.** Treat the fix as unproven.

**✅ F41 RUN-REVIEWED by the owner, all three editions, 2026-09-23** (load from the list, a plate/
brace load, a saved comparison load, single-file import, library import, comparison-file import).
The review found two more, both fixed and re-verified the same day:
- **Python showed the microphone warning in the MIDDLE of a load.** The modal opened synchronously
  when the model raised the warning, so everything the view syncs after the load (ring-out, sliders,
  material results) waited behind OK. Pre-existing (the committed `_restore_measurement` had the same
  order). Now deferred one event-loop turn and shown only if still current — Swift presents its alert
  after rendering the loaded state.
- **The web's import message was an inline line of text, not a dialog** — a divergence introduced by
  this change. Now an "Import Successful" OK dialog over the list, as Swift's `.alert`; the panel stays
  open underneath. (The first web review ran a stale `dist/`: a type error in a new web test broke
  `npm run build`, and `preview` kept serving the 16:55 build.)

Committed: Swift `068f814`, Python `87e7ad7`, web `04c66b9`.

**F41 widened, 2026-09-23 — what changed (kept for the record):**
Owner's decisions: an IMPORT is a library operation and never mentions microphones; a LOAD warns.
A single-file import also loads, so its ONE dialog carries the load's warning (option (a), canonical
Swift). The test pins the OUTCOME (the message) in all three, not any clearing mechanism.
- **Swift — done, 6/6 pass.** Import-time microphone check removed from `importMeasurements`; new
  `importAndLoadMeasurements(from:) -> String` (clears the warning first, imports, auto-loads one,
  folds + consumes the load's warning); both view copies (TapToneAnalysisView open-URL,
  MeasurementsListView) now call it. `ImportMessageTests` (3) in ImportPersistenceTests.swift.
- **Python — done, 43/43 in the two affected files.** Same model method `import_and_load_measurements`;
  import-time check removed; the suppression flag moved into the model. Load made reactive: the
  analyzer emits `measurementLoadStarting` / `measurementLoaded(m)` (relayed by fft_canvas);
  `_restore_measurement` split into `_on_measurement_load_starting` + `_on_measurement_loaded`; the
  list dialog now asks the analyzer to load. `TestImportMessage` (3). Also: the `savedMeasurements`
  alias removed — one list, `saved_measurements` (a test had rebound the alias, splitting the two).
  NOT run-reviewed: loads from the list, a single-file import, and a comparison need checking.
- **Web — done, 631/632 (the one failure is F44's GFFT4 baseline, awaiting its re-mint).** Owner
  chose (a): the load moved into the analyzer. `loadMeasurement(m)` now takes the saved measurement
  and works out guitar / material / comparison record, converts it, restores itself, and records what
  it loaded — replacing ~110 lines in `App.tsx` that converted the file, wrote five pieces of React
  state and handed the analyzer the already-converted parts, which is why no other caller could
  perform a load. New analyzer state, Swift's names: `loadedMeasurementName`, `loadedNotes`,
  `loadedAxisRange`, `loadedSettings` (Swift's nine `loaded*` properties as one patch, since web
  settings are one object), `microphoneWarning`, `currentDecayTime`. The old piece-wise entry points
  are now the restore STEPS (`restoreSnapshot` / `restoreMaterial`), which is all the 14 existing test
  call sites needed. `App.tsx` applies only what lives outside the model — the settings store and the
  chart range — as Swift's `.onReceive(tap.$loaded…)` handlers do; five `useState`s went with it,
  including `showMultiTap`, a second copy of the analyzer's `showingMultiTapComparison`. Ring-out is
  ONE value on the analyzer (owner's call (i), Swift `currentDecayTime`): the engine keeps the tracker
  and pushes each value in, the load writes the file's, `startTapSequence` clears it — the view used
  to hold two and choose between them by `loadedName != null`. `loadComparison` clears the loaded
  state as Swift's does. The web gained the import success message it never had.
  **A consequence to check in the run-review:** the Measurements panel now stays OPEN after an import,
  showing the message over the list, as both natives do; it used to close itself on a single import. The web's load lives in the VIEW
  (`App.tsx onLoadMeasurement`, ~110 lines: conversion, settings patch, loaded name/notes/range/
  ring-out, the warning, engine config), so a model import method cannot load. (a) move the load into
  the analyzer as Swift (recommended; ~F40+F30 in size; web side of #1), or (b) keep the load in
  App.tsx and model only the message. Either way the web gains the import success message.
- Mutation checks done in all three (drop the pre-clear, or warn on a library import: caught, and
  each edition restored). The library-import test now SETS a stale warning first — without that the
  pre-clear mutation survived, because a load always reassigns the field.
- Full suites since: Swift **598 pass**, Python **707 pass**, web **631/632** (GFFT4 only).
  Parity map: 103 groups, no problems.
- Still open after this under F44: Python's integer level scale (option (B): floats end to end AND
  single delivery of levels/frames — Python delivers each to the analyzer twice, direct callback +
  Qt signal, with a racy dedupe guard), then the GFFT4 re-mint, then full suites.

**What the original version of this finding claimed, and why it was wrong.** The field carries a
deliberate suppression mechanism —
`_suppress_mic_warning_signal`, set by the import handler so a synchronous mid-load signal does not
raise a second dialog — and an unconditional assignment fires the change signal on a path that is
currently silent. That interaction wants checking on a clear head rather than at the end of a long
session, having already been misread once here.

**Wrong answer #1, recorded so it is not re-derived.** The first version of this finding said the
import handler clears the warning without emitting and strands the banner. It does clear without
emitting — and that is correct, because the same handler suppressed the raise, read the value
directly, and folded it into its own dialog. Raise suppressed, clear silent, no listener involved.
The code mirrors `MeasurementsListView.swift`.

**Wrong answer #2, which is the one that matters.** Acting on #1, `microphone_warning` was converted
to a property whose setter always emits — which would have defeated `_suppress_mic_warning_signal`
and produced the double dialog it exists to prevent. Reverted before it ran. The lesson is the one
CROSS-EDITION rule 6 states about comments and this file keeps relearning about code: a mechanism
that looks redundant is usually load-bearing, and "two writers, one forgets to notify" is a pattern
worth *checking* rather than a diagnosis.

**A second, smaller thing the sweep found and this one is real.** `saved_measurements` has
`self.savedMeasurements` bound beside it, commented "legacy alias" — two names for one list, in sync
only because `tap_tone_analyzer.py:1350-1351` rebinds both and every other mutation happens in place
(`.extend`, `.append`, `.pop`). Rebind one and they diverge silently. Sixth instance in this sweep of
**two names for one fact**, and the only one still standing. No behaviour is wrong today.

**F42 — web's tap detector ignored the threshold slider, and re-armed on a ring-out. Both fixed.
(✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

Two defects in one detector, found by asking a question the sweep had not asked: *who owns the tap
threshold?* Owner, 2026-09-22: *"the separate divergence of 'who owns the threshold' needs resolved
… in favour of consistency with swift/python."*

**One — the slider was dead.** Swift and Python hold `tapDetectionThreshold` on the analyzer, where
`detectTap` reads it. Web held it in `settings`, pushed it to the engine with
`setConfig({ tapDetectionThreshold })`, and its analyzer carried a field of the same name that
**nothing ever wrote**. Before #17 F30 the ENGINE detected taps and read `config.tapDetectionThreshold`
(`672ca05^`, line 1079), so the slider worked. F30 moved the detector onto the analyzer and left the
threshold behind: from that commit the detector sat at its `-40` dB default — for guitar's absolute
rule and as the base of material's relative one — while the slider went on writing two values nobody
read. **A regression introduced by this issue**, committed as `672ca05` and carried into `ac1925f`.
**Never released** — there has been no web deploy since, so no user ever had the dead slider. It
existed only in the repository, between F30 and tonight.

It survived every run-review because −40 dB is a workable default: taps register, and nothing looks
wrong unless you move the slider and expect a change. Fixed in `setSettings`, which App already calls
on every settings change, so the slider, a settings load and a measurement load's patch all arrive.

**Two — a ring-out counted as the next tap.** Asked whether the editions agreed in shape, they did
not, and the natives agreed with each other:

| | the latch | what gates firing |
|---|---|---|
| Swift / Python | `isAboveThreshold`, raised on CONFIRMATION, cleared at `falling` | the same flag — while it is up, nothing counts |
| web (was) | raised on the FIRST above-`rising` chunk | a separate `prevAbove` edge, cleared at `rising` |

Because the edge cleared at `rising` and the latch at `falling`, the 3 dB between them was a hole:
between taps of a multi-tap sequence — capture finished, signal not yet settled — a ring-out that
decayed past `rising` but never reached `falling` re-armed the detector, and its next swing up was
taken as the following tap. The sequence would finish early with a decay averaged in place of a
strike. Web now uses the natives' single-flag shape, `prevAbove` is gone, and the mid-sequence re-arm
deliberately leaves the latch alone.

**A wrong turn worth recording.** The first probe of this showed nothing — `beginCapture` refuses to
re-enter while a capture is filling, so the double-fire is masked *during* a capture, and the reading
was nearly abandoned as "not reachable". It is reachable between captures, where no guard applies.
Twice this sweep a defect has hidden behind a guard that made the symptom intermittent.

**Tests, one file per edition under `test/tap-decisions`** — the slug's existing cases pin the
detection RULE with the threshold handed to them as an argument, which is exactly why they could
never catch either defect (method rule 1: check what the APPLICATION passes). Added: three threshold
cases and two re-arm cases per edition, each driving the analyzer the way the app does. The natives
passed all five on the first run — the control working. Web failed the two that describe the defects
and passes them now. Swift **15**, Python **15**, web **627**.

A second wrong turn, also worth keeping: the Swift control fed one loud frame too many. `tapDetected`
is a per-frame flag, and the frame after a fire re-enters the latched branch and clears it — the test
failed, not the code.

**F43 — two detector divergences. BOTH TURNED OUT TO BE DEAD CODE, and the finding was wrong about
each of them in the same direction. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

Owner's instruction, 2026-09-22, on being shown both: *"Sounds like they need fixed as well. Please
add a finding so that we cannot close this slug until they are fixed."*

**What the investigation found, 2026-09-23 — both halves as written below are wrong.** Each described
a live mechanism that diverged; each was in fact code nothing calls. The descriptions are kept because
the reasoning that produced them is the thing to distrust next time: in both cases the wiring existed
and read as evidence of behaviour, and in neither case was the source ever checked.

**1. Web has a SECOND detector that still has the old shape.** `src/dsp/gatedCapture.ts` —
`findLevelCrossing` and `findAllLevelCrossings` — still uses `prevAbove` + `consecutive` with no
hysteresis latch. It is the offline scanner that finds taps in a played-back file, and it is what the
original `test/tap-decisions` cases exercise. So after F42 web is internally inconsistent: its live
detector latches, its offline detector does not.

Before fixing, settle what the natives use for the same job — **do not start from a line-by-line
comparison of the two implementations.** In the natives, level-crossing is NOT a tap decision at all:
it is the pre-roll snapshot trigger that grabs pre-onset audio so the gated window has lead-in, and
`detectTap` alone decides whether a tap happened (stated in the comment corrected under F36). If web
uses its scanner to MAKE the decision for file playback, the two are not counterparts and the
question is which edition's file-playback path is right, not which loop is.

**2. The `tapDetected` surface differs.** Swift and Python carry a per-frame `tapDetected` /
`tap_detected` flag; Python wires it through `tapDetectedSignal` → `_on_tap_detected`, which turns the
status-bar dot orange when a tap fires. **Web has no such field at all** — it signals a tap only by
beginning the capture. So the natives have a user-visible tap indication driven by a model flag that
web does not have, and the flag itself is part of the observable surface the three are supposed to
share. Check what web's status dot actually does before deciding whether the fix is a field, a
notification, or both.

Neither is run-reviewable until fixed, and both are in the same subsystem F42 just touched.

### Resolution — 2026-09-23

**Part 1 was dead code, not a second detector.** `findLevelCrossing` and `findAllLevelCrossings` had
**no production caller**, and had not had one since **2026-07-11** (`d29c654`, "remove wrong-altitude
guitar-fft/gated-capture suites"), which deleted the callers precisely because they took *"a shortcut
Swift/Python deliberately don't take"* — driving DSP on raw WAV samples instead of the engine. The
functions and their tests outlived their callers by two months. This is the sweep's own fourth defect
shape: tests keeping a removed feature alive (method rule 5).

Both functions deleted, along with the four DSP cases that only exercised them and the test helpers
left orphaned behind those. **No coverage lost, and verified rather than assumed:** the deleted cases
asserted that the brace fixture yields 1 tap and the plate 3; `REG-B1` and `REG-P1` in
`file-playback.test.ts` assert exactly that, on exactly those fixtures
(`brace-umik-1-swift-mac-1778816093.wav`, `plate-umik-1-swift-mac-1778816330.wav`), through the
engine. `d29c654`'s claim that file-playback was "a strict superset" was true — checked this time
rather than trusted (rule 6).

**Part 2 was dead in all three editions, and the finding's premise was backwards.** It claimed Python
had built a status-dot flash on `tapDetected` that Swift lacked. In fact **`tapDetectedSignal` is
never emitted anywhere** — Python had built the whole chain (signal → canvas relay → status dot) and
never connected the source, so the flash never ran. And in Swift the field was `@Published` and read
by **nothing**: no view, no model logic. Its doc comment said *"Views observe this to flash the tap
indicator."* None ever did — the sixth confidently-wrong comment this sweep has turned up.

So `tapDetected` was write-only in Swift, write-only-plus-dead-wiring in Python, and absent in web.
All of it removed: ~20 production lines per native, the Qt signal, both handlers, both connections,
and the false doc comment.

**The test suites moved onto `lastTapTime`**, 17 edits per edition. Owner's reasoning, 2026-09-23, and
it is the general rule worth keeping: *"propagating an unused variable in the application as a guide
to the testcases is just either wrong or intentional … my bias is it is wrong."* A production field
that exists only so tests can observe something is the application bending to the suite.

It also made the tests better. `tapDetected` was true for ONE frame and the next frame cleared it —
which is exactly what failed the Swift control under F42 while the code was right. `lastTapTime` is
durable. Two cases needed more than substitution: the cooldown test and the hysteresis test each have
a tap already recorded, so "no tap fired" is "the timestamp did not MOVE", not "it is nil".

Swift **593**, web **623** (four fewer than before: the deleted DSP cases).

**F44 — the epsilon clamp, the −∞ readout, and a self-regression failure that turned out to be
something else. (✅ CLOSED 2026-09-23 — fixed and run-reviewed by the owner in every edition it touched)**

Owner's observation during the #17 run-review: Swift shows **−∞** for Peak on a silent input (BlackHole
2ch), Python showed **−313.0 dB**. Owner's call: −∞ is right, because **−100 dB is a REAL reading** a
live UMIK-1 reaches in a quiet room, so a finite floor makes "no microphone" look like "a quiet one".

**State of the code RIGHT NOW (uncommitted, unverified):**

- Python: BOTH epsilon clamps removed — `dft_anal` (live, `realtime_fft_analyzer_fft_processing.py`)
  and `compute_gated_fft` (`realtime_fft_analyzer.py`). Same literal in each: `np.finfo(float).eps`.
- web: BOTH removed — `guitarFFT.ts` and `gatedFFT.ts`, plus the now-unused `EPS` constant.
- Swift: untouched; it never had a clamp.
- Python also gained a **consumer clamp**: `perform_fft` did `int(np.max(mag_y_db) + 100.0)`, which
  raised `OverflowError` on `-inf` and killed the FFT thread on every chunk (the app showed no peak
  level and never recovered). Now floors the derived integer at 0. **This bug was reported by the
  owner from a running app, not by any test.**

**What is established by experiment:**

- The clamp does NOT affect REG-G2's peaks. Four A/B arms (no clamp / live only / gated only / both)
  give byte-identical results, matching the baseline AND Swift's oracle to 16 figures.
- web's self-regression moves exactly **1 of 94** — `GFFT4/maxDb: -313.07 → -Infinity`, a deliberately
  silent synthetic fixture. That is the expected consequence.
- Python's full pipeline outside pytest — both with the owner's real settings and in a fresh sandbox —
  moves the same **1 of 94**, GFFT4 only.

**Resolution of the clamp question (2026-09-23):** the clamp removal changes **only GFFT4**, in both
Python and web, and makes both match Swift, which never clamped. The GFFT4 baselines in Python and web
must be re-minted to adopt −∞ — a change to committed baseline files, owner's approval.

**What the Python self-regression failure actually was.** Under pytest, 19 and then 21 of 94 moved —
late-sequence REG-G2 taps 7/8 and REG-P2 FLC, by an amount that varied run to run. The cause is NOT
the clamp: file playback paces audio at real time + processing time while the tap lifecycle runs on
wall-clock timers, so results depend on machine speed. Demonstrated by adding work per chunk: 0 ms
and 5 ms move nothing, 15 ms moves all 54 REG-G2 values. Swift has the same structure. It predates
the sweep (April–May 2026, shipped in 1.0–1.0.2) and hid under the old 1 Hz / 1 dB bar. The earlier
"file playback is deterministic" bullet was wrong — it was deterministic only at one speed. Moved to
[#19](https://github.com/dwsdolce/guitar-tap-project/issues/19), detail in
[`PLAYBACK-WALL-CLOCK-TIMING.md`](PLAYBACK-WALL-CLOCK-TIMING.md). **Not an S6 gate** (owner,
2026-09-23). Until #19 is fixed, a Python self-regression failure that lists only late-sequence
REG-G2/REG-P2 values is #19; anything else is not.

**Still open under F44:**
- **Python's integer level scale — ✅ RUN-REVIEWED by the owner 2026-09-23** (live guitar and plate
  taps, level readouts, file playback; owner's option (B)).
  Floats end to end AND one delivery each, as Swift: the per-chunk level reaches detection ONLY
  through the direct `rms_level_handler` on the processing thread (Swift's `rmsLevelHandler` on the
  audio queue) — `rmsLevelChanged` now carries float dB for the threshold meter only; the FFT frame
  reaches `on_fft_frame` ONLY through `fftFrameReady`, so on the main thread (Swift's Combine sink
  `.receive(on: .main)`). Removed: the int wrapper `_on_rms_level_changed_direct`, the dedupe guard
  `_last_rms_chunk_pos` (whose own comment recorded that a miss doubles the N-consecutive-chunks
  confirmation), the direct `fft_frame_handler` (every live frame had been analysed twice, once per
  thread, unguarded), `levelChanged(int)` (the material readout now updates in `_on_peak_info`,
  Swift's one guitar/material choice), the F44 `OverflowError` consumer clamp (nothing converts to
  int any more), and dead code on the path (canvas `ampChanged` relay, never-connected
  `_on_fft_frame_ready`, unused `rms_amp`). Tests: `TestPipelineDeliversOnceAndExact` (3, in
  test_tap_detection.py) — exact float level, one detection pass per chunk, one analysis per frame —
  each killed by exactly one mutation (truncation / second level delivery / second frame delivery).
  Python 707 + 3 pass; parity vs Swift's oracle passes; standalone self-baseline moves ONLY GFFT4, so
  the truncation never changed which chunk confirmed a tap in the recordings. During the review the
  owner noticed Swift's threshold meter updates less often than the other two — that is #3 (Swift's
  4800-frame buffers), not this change; recorded there as symptoms 4 and 5.
  What was there before: Python quantises two levels to whole-dB integers, `int(dB + 100)`, and converts them back at the consumer;
  Swift keeps both as `Float` end to end. It arrived with `e3b6622` (2026-04-05) and no platform
  requires it.
  - `rms_amp` — the per-chunk RMS level. **Tap detection** receives it: the direct path holds the
    float `level_db` and still converts it (`tap_tone_analyzer.py` `_on_rms_level_changed` caller),
    so detection compares whole-dB levels against threshold, noise floor and hysteresis. `int()`
    truncates toward zero, so it is biased, not just rounded (−37.6 dB reads as −38.0). The threshold
    slider's meter gets the same integer.
  - `fft_peak_amp` — the spectrum's peak. Re-derived into `_current_peak_magnitude_db`, which seeds
    `is_above_threshold` on guitar re-enable, and passed to `analyze_magnitudes` as whole dB (Swift
    passes `fft.peakMagnitude`). Its `levelChanged` signal is now only the material readout's tick.
  - Fix: floats end to end, as Swift. Changes Python's detection behaviour toward Swift; may move
    Python's REG values and require a reviewed self-baseline re-mint.
- **GFFT4 re-mint — ✅ DONE 2026-09-23, with the owner's option (i).** JSON has no infinity: the web
  wrote `null` (so its self-regression still failed after a naive re-mint) and Python wrote the
  non-standard bare `-Infinity` token. Now EVERY oracle and baseline file — all three editions and
  the hub — stores a non-finite number as the string `"-Infinity"` / `"Infinity"` / `"NaN"` and
  decodes it on load (Swift `nonConformingFloatDecodingStrategy`; Python `decode_nonfinite` /
  `encode_nonfinite` in `self_baseline.py`; web `reviveNonFinite` / `replaceNonFinite` in
  `selfBaseline.ts`; hub `parity-report.py`, which also treats equal infinities as a difference of 0).
  The oracle now records GFFT4 EXACTLY (`"maxDb": "-Infinity"`) instead of the bound `maxDbBelow:
  -100` it carried only because JSONSerialization cannot write infinity; all three GFFT4 parity tests
  and both mint plausibility checks compare exactly. Oracle minted from Swift as `576c3d4-dirty`
  (owner's choice: mint now, re-mint clean at commit time — values will be identical), published to
  the hub and synced; Python and web baselines re-minted against it, and both record that version.
  Python's mint gained a check that rewrites a baseline whose ENCODING is stale even when every value
  is identical — its reader accepts the bare token, so without it a stale file would never be
  rewritten (the owner caught me hand-converting instead of re-minting).
  **Suites: Swift 598, Python 712, web 635 — all pass, no known failures.** Parity map: 103 groups.
- Not touched, and belonging to #16: the hub's Windows and Linux baselines (minted on those
  machines) still record GFFT4 as −313.07. **Deliberately deferred until the slug sweep is finished**
  (owner, 2026-09-23) — further changes are likely, so re-minting now would only have to be repeated.
- **Done at commit:** oracle re-minted from the committed Swift tree (`068f814`, committed as
  `ee8e72f`), published and synced; both baselines re-minted against it — both mints now also rewrite
  a baseline whose recorded oracle version is stale. Commits: Swift `068f814` + `ee8e72f`, Python
  `87e7ad7`, web `04c66b9`.

**Done under F44 (2026-09-23, all three editions, run-reviewed by the owner):**
- Step 15 now passes on Python and web as well as Swift.
- Silence reads `-∞` everywhere: `FieldPrecision.string` renders ±∞ as `-∞`/`∞` in all three
  (Swift's status bar already drew `-∞`; its own Metrics panel drew `-inf`, Python `-inf`, web
  `-Infinity`).
- The live peak is owned by the FFT analyzer in all three (Swift `peakFrequency`/`peakMagnitude`,
  Python `mic.peak_frequency`/`peak_magnitude`, web `EngineMetrics`), first maximum on ties — web had
  shown "Starting..." on silence. Python's Metrics panel had read the detected-peaks list since
  `bdd6cc9` (2026-04-02) under a docstring claiming otherwise; it now reads the live peak.
- Per-chunk RMS level on true silence is Swift's −100 in all three (Python since `42ec2b7` and web,
  copied from Python, used −200). The material level READOUT alone shows `-∞` on true silence
  (`readoutLevelDB` → `displayLevelDB`); detection is unchanged. Python's material readout showed the
  spectrum's peak in whole dB; it now shows the RMS level, as Swift.

**A related divergence found on the way, worth its own fix:** Python carries `fft_peak_amp`, a 0–100
INTEGER scale (`int(peak_db + 100)`), through two Qt signal hops — and the terminal consumer converts
it straight back (`float(fft_peak_amp) - 100.0`), while the slider's own handler says *"the slider
expects dB"*. Swift has no such value; it keeps `peakMagnitude` a Float throughout. So Python
quantises its peak magnitude to whole dB for no surviving reason. It arrived with `e3b6622`
("Model changes from PYTHON_ARCHITECTURE_RESTRUCTERING_PLAN.md"), not from any platform constraint.

**Process note.** Four successive explanations of the clamp were offered and each was wrong:
"defensive idiom, safe to remove", "load-bearing for the int() conversion", "load-bearing for parity
with Swift", "the failures are load-induced" — and while chasing the failure, three more: "guitar type
from the settings file", "an unpinned setting", "an ordering leak between cases". Each was killed by a
measurement, and the measurement should have come first each time. The owner's question — *"how do these values compare
against swift?"* — was what first cut through it, and the A/B that should have preceded any edit was
run only after the edit. **Do not change a DSP path in this area again without running the A/B and
the oracle comparison first.**

**F45 — `state-invariants`: the checker is well mirrored, but mostly untested, one case tests a
hand-built state, and the web keeps a test helper in production. (✅ CLOSED 2026-09-24 — fixed in all
three and run-reviewed by the owner: web cooldown/processing, Python re-arm status. Commits: Swift
`f2b4452`, Python `9a61713`, web `307a2b6`)**

The seven tests (V1–V7) and the six invariants (I1–I6) are identical case for case in Swift
(`StateInvariantTests.swift`), Python (`test_state_invariants.py`) and web (`state-invariants.test.ts`),
and the review phases I6 guards are real and entered in all three. Three things are wrong:

1. **Web keeps the checker in production.** Swift and Python define `stateInvariantViolation` in the
   TEST file; web defines it in `src/state/tapToneAnalyzer.ts`, where nothing but the test calls it.
   Fix: move it into the web test file.
2. **Most of the checker is never exercised, in any edition.** Every case runs a guitar measurement,
   so I6 (no detection during a plate/brace review phase) is never evaluated on a material analyzer;
   and the only "the checker catches a bad state" test is V7, for I1 alone — nothing shows I2–I6
   would ever fire. Fix, all three: a material case that drives a real plate capture into a review
   phase and checks the invariants, and a flagged-state test per invariant (as V7 is for I1), each
   proven with a mutation check.
3. **V4 tests a state it built by hand.** It assigns `capturedTaps`, `currentTapCount` and
   `detectionState = listening`, then checks the invariants of that fabricated state — so it
   exercises the checker, not a production path (PARITY-TEST-METHOD rule 1). Fix: reach the
   mid-sequence state through the real capture-and-re-arm path, all three.

**What was done (2026-09-24):**
- **All three:** V4 now reaches mid-sequence through the REAL guitar capture
  (`finishGuitarGatedCapture`) and is checked twice — resting through the tap cooldown, and
  re-armed after it. New V8 drives a real plate capture into its review phase (I6's territory).
  New flagged-state tests for I2–I6, as V7 is for I1. Mutation: removing rules I2–I6 from the
  checker fails exactly those five tests in each edition; restored.
- **Web — aligned with the natives, owner's decision:** the checker moved from `src/` into the test
  file. The private `finishCapture` was split into public `finishGuitarGatedCapture(samples,
  sampleRate)` and `finishGatedFFTCapture(samples, sampleRate, phase)`, as in Swift and Python (a
  stale comment had said the FFT was "the device's job", untrue since F30). And the two waits the
  natives have and the web lacked are now there too, as the same **wall-clock** timers: after each
  mid-sequence guitar tap, detection rests for `tapCooldown` (0.5 s) and then re-arms with the latch
  re-anchored from the current level; after the last tap, "All taps captured. Processing..." shows for
  `captureWindow` (0.2 s) before averaging. Mutation: re-arming at once fails V4.
- **Why wall-clock, not audio time** (owner, 2026-09-24): non-divergence. The natives' timers are
  wall-clock; if that is wrong it is #19, and #19's fix then goes to all three at once. So every web
  playback is now PACED, as the natives' is — the parity runner (which now also waits for completion,
  like Swift's `playFileForTesting`), the ring-out tests and the F44 silence test. "Slower tests mean
  it is doing what Swift and Python do." The web inherits #19's machine-speed exposure with them.
- **Swift test-setup note:** an unstarted analyzer has no frequency bins (all 0 Hz), so a real
  spectrum put every peak at 0 Hz and `Pitch.pitch` trapped on `log2(0)`. V4 sets the bins up as
  starting the engine does. Not reachable in the app.
- Suites: Swift 604, Python 718, web 641 — all pass. Parity map 103 groups.
- **Run-review needed (web, live guitar, Taps = 3):** a second strike within half a second of a
  captured tap is ignored; after the third tap "All taps captured. Processing..." shows briefly before
  the result.
- **Web run-reviewed by the owner 2026-09-24** (a second strike inside the cooldown is ignored;
  "All taps captured. Processing..." shows before the result).
- **Python's re-arm no longer rewrites the status message** (owner: "if Python is odd man out, bring
  it back"). It used to set the loop prompt again, or "Tap N/M captured. Waiting for settle..." while
  the level was still high — text no other edition has; Swift's `scheduleGuitarReEnable` and now the
  web's touch only the latch and the detection state, and the capture's own status stands. Pinned in
  all three by a new `test/status-message` case (re-arm with the level still above the falling
  threshold leaves the status as the capture set it); putting Python's old writes back fails it.
  The Swift case was intermittent at first (2 of 3 full runs): the analyzer's clipping / dead-input
  override sinks re-resolve the status from `latestRealStatus`, which another sink keeps current
  asynchronously, and in a busy run an override delivery restored the initial "Tap the guitar to
  begin" before that sink caught up — a test-environment race (in the app the sinks settle long before
  any capture). The test now drops the analyzer's Combine sinks, as the state-invariant tests do;
  3 of 3 full runs clean, and a status write added to Swift's re-arm still fails it.
- **Suites (2026-09-24): Swift 605, Python 719, web 642 — all pass; parity map 103 groups.**

**F46 — `scenario-trace` pins a state path the tests write themselves, and part of it is a path the
app no longer takes. (✅ CLOSED 2026-09-24 — tests only, all three; no app behaviour changed. Commits:
Swift `b441119`, Python `d382280`, web `51600ae`)**

The four scenarios (S1–S4) and their expected traces are identical row for row in Swift
(`ScenarioStateTraceTests.swift`), Python (`test_scenario_state_trace.py`) and web
(`scenario-trace.test.ts`). But the slug's purpose — pin the intermediate state PATH, because the UI
reacts to it in real time — is undone by how each tap is produced: every scenario assigns the "tap
happened" state by hand (`detectionState = idle`, `capturedTaps = [...]`, `currentTapCount = n`, and in
S3/S4 `detectionState = listening`, commented "scheduleGuitarReEnable result") and then snapshots it. So
the `postCapture` / `postTap1` rows record what the TEST wrote. Only `postStart`, `postPause`,
`postResume`, `postCancel` and `postProcess` come from production (PARITY-TEST-METHOD rule 1; the same
defect F45 fixed in V4).

It is worse than tautological now: **S3/S4's `postTap1` says detection is back on the instant a tap is
captured** — a state the real code never produces, since all three editions rest for `tapCooldown`
(0.5 s) with detection OFF and only then re-arm (F45). The canonical trace documents a path the app does
not take, and passes only because the test builds it. And S1/S3 call `processMultipleTaps()` directly,
skipping the real completion (`captureWindow`, 0.2 s, "All taps captured. Processing...").

Fix, identical in all three: capture every tap through the real `finishGuitarGatedCapture` and let
completion happen on its own. S1 keeps its rows, now produced by real code. S3/S4's `postTap1` becomes
resting (`det=false`), followed by a new `postReArm` (`det=true`) after the cooldown; S3's remaining taps
go the same way. S2 keeps its simulated spurious detection (the stray detection IS the scenario) but
captures through the real path. Mutation checks: removing the cooldown, or completing immediately, must
break the trace.

**What was done (2026-09-24):** in all three, every tap goes through the real
`finishGuitarGatedCapture`, completion happens on its own after the capture window, and re-arming after
the real cooldown. The canonical traces (identical in all three): S1/S2 keep their rows, now produced by
real code; S3/S4 have `postTap1` resting (`det=false`), a new **`midCooldown`** row halfway through the
cooldown (still resting), and **`postReArm`** (`det=true`). The `midCooldown` row was added after the
first mutation run: re-arming on the next event-loop turn instead of after 0.5 s passed the Swift traces,
because nothing sampled inside the cooldown. Mutation checks, all three: cooldown → next turn fails S3/S4;
completing without the capture window fails S1/S2. Swift note: `updateFrequencyBins()` publishes the bins
via `DispatchQueue.main.async`, so the scenario SUT builds them before each scenario's existing wait.
Suites: Swift 605, Python 719, web 642 — all pass; parity map 103 groups.

**F47 — `session-pre-roll`: the web freezes the pre-roll latch in a different place, and its tests set
the latch by hand. (✅ CLOSED 2026-09-24 — web only, no behaviour change. Commit: web `afe1436`)**

The four cases are the same in Swift (`SessionPreRollTests.swift`), Python (`test_session_pre_roll.py`)
and web (`session-pre-roll.test.ts`), and so is the outcome: the latch is ARMED at session start and when
a redo of the first phase empties the buffer, in all three; and at the first tap the triggering chunk is
trimmed and the next is not, so the session WAV comes out the same length. But the FREEZE lives in
different places — Swift and Python freeze it in `maintainSessionRecording`, on the first chunk appended
while `gatedCaptureActive` (`if gatedCaptureActive { sessionPreRollActive = false }`); web freezes it in
`beginCapture`, just before setting `gatedCaptureActive = true`. Two owners of one rule.

That is what hollows out the web tests: its "first tap freezes the latch" case and the freeze step of
"fully live after the first tap" set `sessionPreRollActive = false` BY HAND and then assert it is false —
the first tests nothing at all. The natives drive both through `gatedCaptureActive`.

Fix: web moves the freeze into `maintainSessionRecording` in Swift's shape and removes it from
`beginCapture`; the web tests drive it through `gatedCaptureActive` as the natives do. Mutation check:
without the freeze in `maintainSessionRecording` the web tests must fail.

**Done (2026-09-24, owner: "the fact that they diverge is sufficient"):** the web's
`maintainSessionRecording` now freezes the latch in Swift's shape and `beginCapture` no longer touches
it; the web tests drive the freeze through `gatedCaptureActive`. Mutation: without the freeze, 2 of the 4
web tests fail — under the old hand-set tests the same removal would have gone unnoticed. Web 642 pass;
parity map 103 groups. Swift and Python unchanged. No behaviour change (the WAV comes out the same
length), so nothing to run-review.

**F48 — `start-tap-race`: the web's R4 is not the natives' test, its R1 tests nothing, and R2–R4
hand-simulate the capture. (✅ CLOSED 2026-09-24 — tests only, all three; no app behaviour changed. Commits:
Swift `867889d`, Python `7ba1083`, web `4d439fd`)**

R1–R5 exist in Swift (`StartTapSequenceRaceTests.swift`), Python (`test_start_tap_sequence_race.py`) and
web (`start-tap-race.test.ts`); R5 (a restart from paused ends listening) matches and drives production.
The rest:

1. **Web R4 is a different test.** R4 guards "the actual iPad bug": the natives capture through
   `finishGuitarGatedCapture` and assert that IT clears detection. Web R4 calls `recordGuitarTap` and then
   sets `detectionState = 'idle'` BY HAND ("the device's idle transition" — stale since F30/F45), so
   nothing on the web checks what R4 exists to guard. Web now has a public `finishGuitarGatedCapture`
   (F45), so its R4 can be the natives' test exactly.
2. **Web R1 tests nothing.** It arms, sets idle, and immediately asserts idle — no wait. The natives'
   R1 waits for deferred work (Swift `Task.sleep`, Python's event-loop drain) — that is how it catches a
   deferred re-arm, the line-304 race. Web has deferred work of its own since F45, so the wait now
   matters there too.
3. **R2/R3 hand-simulate the capture in all three** ("we simulate by populating capturedTaps", then
   `processMultipleTaps()`) — the F46 defect. The natives' R4 also calls `processMultipleTaps()` by hand
   right after the real capture, which already schedules it after the capture window — so it runs twice.

Fix, all three: R2/R3/R4 capture through the real `finishGuitarGatedCapture` and wait for the real
completion, with no hand-called `processMultipleTaps()`; web R4 becomes the natives' R4; web R1 waits
before asserting. Mutation checks: removing the detection clear in `finishGuitarGatedCapture` must fail
R4; adding a deferred re-arm to `startTapSequence` must fail R1.

**Done (2026-09-24):** in all three, R2/R3/R4 capture through the real `finishGuitarGatedCapture` and wait
for the real completion (no hand-called `processMultipleTaps()`); web R4 is now the natives' R4; web R1
waits before asserting. Mutation checks, all three: removing the detection clear in
`finishGuitarGatedCapture` fails R4 (and R2/R3 where they reach it); adding a deferred re-arm to
`startTapSequence` fails R1 and R2 — the line-304 race is guarded in every edition. Suites: Swift 605,
Python 719, web 642 — all pass; parity map 103 groups.

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
