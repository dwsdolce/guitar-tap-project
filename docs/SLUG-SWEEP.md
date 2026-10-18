# Sweep every `@parity` slug

**Issue:** [#17](https://github.com/dwsdolce/guitar-tap-project/issues/17) · **Status:** ⏳ Stage 2 next — Stage 1 complete 2026-10-02

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
[`PLAYBACK-WALL-CLOCK-TIMING.md`](completed/PLAYBACK-WALL-CLOCK-TIMING.md). **Not an S6 gate** (owner,
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

### S7 — Capture / DSP pipeline (5 slugs)

Status: ✅ **CLOSED 2026-09-27** — all 5 slugs read; every finding it produced (F49–F54) fixed and run-reviewed
in all three. #19 finished during it (see [`PLAYBACK-WALL-CLOCK-TIMING.md`](completed/PLAYBACK-WALL-CLOCK-TIMING.md));
its two remaining "noticed" items (the Python minter's settings sandbox, timers leaking between playback
cases) were settled in F52 item 8.

**Audit record.** As in S6, this table records only **what the reading produced** — a finding number,
or "clean" where none was filed. Each finding's status lives in the finding and nowhere else.

| slug | read? | produced |
|---|---|---|
| `gated-fft` (5/5/5) | ✅ | cases identical all three (GFFT1–5, from the oracle); **F49** |
| `tap-decisions` (14/18/6) | ✅ | **F50** |
| `tap-progress` (12/12/14) | ✅ | **F51** |
| `file-playback` (8/8/11) | ✅ | **F52**; **F53** from F52 item 2 |
| `decay-tracking` (7/8/8) | ✅ | **F54** |

**Counts, measured with the runners, 2026-09-24** (Swift: the ten S7 suites run with a result bundle,
47 tests, all pass, no argument expansion; Python: `pytest --collect-only`, 50; web: `vitest list`, 46):

| slug | Swift | Python | web | files (Swift / Python / web) |
|---|---:|---:|---:|---|
| `gated-fft` | 5 | 5 | 5 | `GatedFFTParityTests.swift` / `test_gated_fft_parity.py` / `gated-fft.test.ts` |
| `tap-decisions` | 15 | 18 | 6 | `TapDetectionTests.swift` / `test_tap_detection.py` / `tap-decisions.test.ts` |
| `tap-progress` | 12 | 12 | 14 | `TapProgressTests.swift` / `test_tap_progress.py` / `tap-progress.test.ts` |
| `file-playback` | 8 | 8 | 11 | `FilePlaybackRegressionTests.swift` / `test_file_playback_regression.py` / `file-playback.test.ts` |
| `decay-tracking` | 7 | 7 | 10 | `DecayTrackingTests.swift` / `test_decay_tracking.py` / `decay-tracking.test.ts` |

These have changed since the starting picture (2026-09-20: `tap-decisions` 10/10/5, `tap-progress`
10/10/12), through S6 work. `tap-decisions` is the widest spread, and the natives differ from each other
there too (15 vs 18). `file-playback` and `decay-tracking` have more web tests than canonical Swift. As
S6 showed, neither a spread nor a match settles anything — the reading does.

`file-playback` carries two things already split out of the sweep, and neither is a finding here:
results that depend on machine speed ([#19](https://github.com/dwsdolce/guitar-tap-project/issues/19))
and Swift's 4800-frame buffers ([#3](https://github.com/dwsdolce/guitar-tap-project/issues/3)).

**F49 — `gated-fft`: the cases match and reach production, but the transform differs in two
mechanisms, Swift's tests build a hardware analyzer, and the tests' own explanations are wrong.
(✅ closed 2026-09-25 — committed 2026-09-24: Swift `c4611e0`, Python `c3b1bff`, web `1f858f8`. Python's
self-baseline re-minted under #19 once playback was repeatable — exactly the 24 values this finding's
window moved — committed with #19 as Python `820fabd`. The owner's run-review passed in all three)**

Files: `GatedFFTParityTests.swift` / `test_gated_fft_parity.py` / `gated-fft.test.ts`. Production:
Swift `RealtimeFFTAnalyzer.computeGatedFFT` (`+FFTProcessing.swift:434`), Python
`RealtimeFFTAnalyzer.compute_gated_fft` (`realtime_fft_analyzer.py:891`), web `computeGatedFFT`
(`dsp/gatedFFT.ts`). In every edition that is the transform every plate/brace capture runs
(`finishGatedFFTCapture` → align → gated FFT → dominant peak). **Guitar never uses it:** the guitar
capture uses the live path's rectangular window at `fftSize` 65536 in all three (Swift
`finishGuitarGatedCapture` → `computeFFT(on:)`, Python `dft_anal(…, window_fcn)`, web `dftAnalRect`), so
everything in F49 — the window, the calibration move, the taper observation — concerns **plate and brace
only**, and leaves guitar results untouched.

**What is sound.** All three run the same five cases, taken from the oracle rather than retyped:
GFFT1 one tone, GFFT2 two tones at the plate-C frequencies, GFFT3 two "bin-centred" tones, GFFT4 silence
(exactly −∞ since F44), GFFT5 one "bin-centred" tone. Each builds its signal in double precision and rounds
to float32 per sample, and each calls the production transform directly. Swift asserts at zero (it mints
the oracle, F4); Python and web at `gatedFftDb`, which is **0.001 dB**.

1. **Calibration is applied in a different place.** Swift and Python add the microphone calibration inside
   the transform (`activeCalibration` / `_calibration_profile`). The web's `computeGatedFFT` returns it
   uncalibrated, and its caller `gatedCaptureResult` (`dsp/gatedCapture.ts`) adds it from the phase's
   `search.calibration`. Two owners of one step. **No test in any edition covers calibration on the gated
   path** — every GFFT case runs uncalibrated.
2. **The window is a different window.** Swift uses `vDSP_HANN_DENORM`, the *periodic* Hann
   `0.5·(1 − cos 2πn/N)`. Python (`np.hanning`) and web (a port of it) use the *symmetric* Hann
   `0.5·(1 − cos 2πn/(N−1))`. Swift's comment records the difference and that they agree to within the
   tolerance at these sizes. That is a measured agreement, not the same mechanism.
3. **Swift's tests (and the oracle minter) build a full hardware analyzer.** `RealtimeFFTAnalyzer()`
   defaults to `forTesting: false`: it enumerates input devices, registers the CoreAudio listener, and
   selecting a device **auto-loads that device's saved calibration** into `activeCalibration`, which
   `computeGatedFFT` then applies. The GFFT tests avoid it only by timing: the device selection is queued
   with `DispatchQueue.main.async`, and the tests call the transform synchronously before it can run. So
   the result depends on the machine's saved settings, held off only by the run order. Python uses
   `for_testing()`, and web a pure function, so neither is exposed. `GenerateParityOracle` builds its
   gated analyzer the same way. The pattern is wider than this slug: `RealtimeFFTAnalyzer()` appears 46
   times across 24 Swift test files.
4. **"Bin-centred to eliminate spectral leakage" is false (GFFT3/GFFT5, all three).** The Hann window
   spans the padded 32768-sample buffer, but the signal is 19200 samples (0.4 s), so no tone is periodic
   in the window and leakage is not eliminated. Measured through Python's production transform: the same
   67.3828125 Hz tone reads **−49.50 dB alone (GFFT5) and −49.70 dB with the 117 Hz tone beside it (GFFT3)**.
   That 0.2 dB is leakage from the stronger tone. It bears on the next item.
5. **Stale or wrong text in the tests and the transforms (rule 3):**
   - Swift GFFT5 explains its golden's move from −49.7 to −49.5 as float phase error in the old
     synthesis. But −49.70 is exactly this tone's value **with the 117 Hz companion (GFFT3)**, so the
     likelier story is that GFFT5's hand golden was copied from GFFT3. Unverified either way; the comment
     is not evidence.
   - Tolerance text says 1 dB: Swift GFFT5 ("within 1 dB"), Python class docstring ("within 1 dB"), web
     (`// 1.0 dB`). It is 0.001 dB. Python GFFT5's docstring still says "must read −49.70 dB" (the oracle
     says −49.50).
   - Python `compute_gated_fft`'s docstring says `np.hanning` is `0.5·(1 − cos 2πn/N)` "matching Swift's
     vDSP_HANN_DENORM". It is the `/(N−1)` form, and does not match (item 2). Swift's comment is correct.
   - Web `gatedFFT.ts` opens with a comment about an epsilon floor constant that no longer exists (F44).
   - Python `_make_proc_thread()` and the `realtime_fft_analyzer_fft_processing.py` header refer to
     `_FftProcessingThread.compute_gated_fft()`, which moved to `RealtimeFFTAnalyzer` long ago.
   - Test names carry history: Swift `afterFix_binCentred_matchesPython` / Python
     `…_matches_swift` (both now check the oracle), Swift `silence_allBinsBelowNoiseFloor` (it checks −∞
     exactly).
6. **The web keeps its test-signal generator in production source.** `makeToneSignal` / `makeSilence` live
   in `src/dsp/signal.ts`, and only `test/gated-fft.test.ts` and `test/parityRunner.ts` import them.
   Swift and Python keep theirs in the test file. **Same for `magnitudeAtFrequency`** (found while
   discussing this item): it is exported from production `src/dsp/gatedFFT.ts`, but only those two test
   files call it; Swift and Python define it in the test file. The same shape as F45 item 1, where the
   web kept `stateInvariantViolation` in `src/` and it moved into the test. The natives are not tidy
   either: each synthesises the gated signal in two test-side places (Swift `GatedFFTParityTests.swift`
   and `GenerateParityOracle.swift`; Python `test_gated_fft_parity.py` and `tests/parity_runner.py`).
7. **Tiny input differs.** Python and web return an empty spectrum for zero samples (an explicit guard) and
   for one sample (their size loop starts at 1, leaving no bins). Swift has no guard; its `nextPowerOfTwo`
   has a floor of 2, so zero or one sample gives a one-bin spectrum (−∞ for zero), and
   `vDSP_DFT_zrop_CreateSetup` accepts length 2 (checked), so the setup-failure path does not catch it.
   From two samples up, all three size the transform identically. *Correction, 2026-09-24:* this entry
   first said every caller passes a full-length window. Not so — `alignCaptureToOnset` returns the buffer
   unchanged when it is too short or has no onset. What keeps zero out is the callers: every Swift path
   into `finishGatedFFTCapture` guards `!isEmpty` (`SpectrumCapture.swift:132, 398, 457, 509`). A
   one-sample buffer is not excluded by any guard found; whether a real capture can be that short was not
   checked. No reason for Swift's shape was found: `nextPowerOfTwo` dates from 2026-02-26 (`7032314`,
   "Work on brace and plate measurements"), written for vDSP; the ports wrote their own size loop and
   added the guard.

**Outside the parity question — an observation, not a finding item.** Item 4's cause is also a property of
the production DSP, identical in all three. The Hann window is applied over the padded buffer, not over the
captured window, so the capture's end (sample 19200 of 32768) is weighted about 0.93 rather than tapered.
The Swift and Python comments justify Hann by saying the buffer "starts and ends near silence". Whether a
400 ms ring-out ends near silence is a question for the owner; changing it would move every material
number in all three editions, and the oracle with them.

**Measured 2026-09-24 — for STEADY tones.** The effective window (the periodic Hann over 32768, cut where
the 0.4 s capture ends) was measured in numpy: its gain, and how strongly a steady tone shows up N bins
away from itself, relative to its own peak. One bin is 1.46 Hz at 48 kHz. **A tap is not a steady tone —
see the correction below, which reverses the practical conclusion.**

| window | gain | +5 bins (~7 Hz) | +10 | +34 (~50 Hz) | +100 | +1000 |
|---|---:|---:|---:|---:|---:|---:|
| **app at 48 kHz** (19200 of 32768 samples) | −9.5 dB | −20.7 | −27.0 | −37.7 | −47.1 | −67.1 |
| **app at 44.1 kHz** (17640 of 32768) | −10.8 dB | −19.1 | −25.3 | −35.9 | −45.3 | −65.3 |
| **app at 96 kHz** (38400, cut to 32768) | −6.0 dB | −54.1 | −71.1 | −102.2 | −130.1 | −190.0 |
| Hann spanning only the captured 19200 | −10.7 dB | −41.5 | −58.7 | −88.7 | −116.4 | −176.1 |

What that means (all three editions alike; plate and brace only):

- **For steady tones, leakage is 20–50 dB worse than the code claims.** At 48 kHz a steady tone 7 Hz from a
  stronger one gets that one's leakage at −21 dB, where a Hann over the captured audio would give −41 dB.
  GFFT3's 0.2 dB (steady tones 50 Hz apart) is an instance. *First recorded here as a general defect; the
  decaying-tap test below shows it does not carry over to taps.*
- **The result depends on the input's sample rate.** The same tap reads about 1.3 dB higher at 48 kHz than
  at 44.1 kHz, and about 3.5 dB higher again at 96 kHz, and leakage differs far more. At 96 kHz the
  capture is also cut to 341 ms instead of 400 ms, and there, by accident, the window is correct. In the
  field that is a UMIK-1 at 48 kHz, a browser at 44.1 or 48 kHz, an interface at 96 kHz. Peak
  frequencies are affected much less than magnitudes and Q.
- **Parity tests cannot see it.** All three editions do exactly the same thing, which is why it has lasted.
- **What it does to the results that matter — measured on the real fixtures, 2026-09-24.** Young's
  modulus, shear modulus and target thickness take only the peak **frequencies** (plus dimensions and
  mass): E ∝ f², G_LC ∝ fLC², and Gore's target thickness ∝ 1/√(a weighted sum of E_L, E_C, G_LC).
  Magnitude and Q do not enter. The Python material pipeline was run on the four material fixtures twice
  — today's window, and a Hann spanning only the captured samples — through `play_file_for_testing` with
  `compute_gated_fft` patched in a scratch test (nothing in the repo changed):

  | case | peak | today | captured-only | Δf | modulus Δ (≈ 2·Δf/f) |
  |---|---|---:|---:|---:|---:|
  | REG-B1 brace | fL | 512.689 Hz | 512.724 Hz | +0.035 Hz | E +0.01% |
  | REG-B2 brace (3 taps) | fL | 553.632 | 553.645 | +0.013 | E +0.005% |
  | REG-P1 plate | fL | 67.115 | 67.445 | +0.33 | E_L +1.0% |
  | | fC | 116.270 | 116.424 | +0.15 | E_C +0.3% |
  | | fLC | 35.354 | 35.910 | +0.56 | G_LC +3.1% |
  | REG-P2 plate (3 taps) | fL | 68.259 | 68.860 | +0.60 | E_L +1.8% |
  | | fC | 117.468 | 117.740 | +0.27 | E_C +0.5% |
  | | fLC | 35.301 | 35.994 | +0.69 | G_LC +3.9% |

  **Braces: negligible.** **Plates: E_L about +1–2%, E_C +0.3–0.5%, G_LC +3–4%**; the target thickness
  moves the other way, by roughly 0.5–1% (estimated from the formula, not computed with real dimensions).
  The shifts are all upward and grow toward the lowest frequencies. Every shift is under 1 Hz, so it passed
  unseen under the old 1 Hz tolerance. Q moved a lot (REG-P1 fL 15.3 → 11.5, fC 26.3 → 15.8) and so did
  magnitude, but neither feeds the material results. **This shows the two windows differ, not which is
  right** — the fixtures have no ground truth. fLC moves most but weighs least: Gore's own note
  (`MaterialProperties.swift`) puts omitting G_LC entirely at a 5–7% thickness change, so a 3–4% change in
  G_LC is worth roughly 0.2%; the thickness change is carried mostly by fL. Near a `WoodQuality` threshold, a
  1–2% change in specific modulus could change a rating.
- **Correction, 2026-09-24 — against known frequencies, today's window is as good or better for taps.** A
  numpy test fed decaying modes at KNOWN frequencies (0.1 s pre-onset silence, then an exponentially
  decaying sine, 0.4 s at 48 kHz, peak by the production parabolic interpolation), swept across a bin and
  over phases:
  - *One mode alone* (35 Hz Q6, 67 Hz Q15, 116 Hz Q26, 513 Hz Q87): both windows are unbiased (mean error
    ≤ 0.003 Hz); worst cases today −0.08 / −0.03 / −0.02 / −0.01 Hz, captured-only about twice that.
  - *67 Hz Q15 with one neighbour* (+8/15/30/50 Hz, 0.3×/1×/3× amplitude, Q15/Q40): today's window has the
    smaller error in nearly every case. With a strong neighbour 8 Hz away, today's worst is 3.9 Hz; the
    captured-only window's worst is 31 Hz — it picks the neighbour.
  Why: a tap decays, so the signal supplies its own end taper — the hard edge at 0.93 carries almost no
  energy. The edge that matters is the tap's abrupt **onset**, 0.1 s in, and today's window weights it at
  ≈0.2 where a Hann over the capture weights it at 0.5. The Swift/Python rationale ("starts and ends near
  silence") holds for the end; the steady-tone table above overstated the practical effect. **So the
  real-fixture shifts above are not evidence that today's plate results are wrong.** What would settle the
  real fixtures is a window-free estimate — fitting decaying sinusoids to the captured audio (e.g. matrix
  pencil) — which has not been done.
- **The sample-rate dependence stands** (it is about gain and how much of the padded window the capture
  fills, not about leakage): same tap, different dB — and at 96 kHz a shorter capture (341 ms) with a
  different effective window. Its effect on the frequencies has not been measured.
- **Whether anything should change is now open, not assumed.** The windowing is not shown to be wrong for
  taps; the sample-rate dependence is real but unmeasured in frequency. Any change would move every
  plate/brace result in all three, the oracle and every baseline — the same kind of change as #19 and #16 —
  so it is not F49's. The owner's decision whether it becomes its own issue.

**Decisions (owner, 2026-09-24) — recorded as they are made; nothing implemented yet.**

- **Item 1 — the web matches Swift and Python.** No reason was found for the web to differ: its comment
  gives none, and `computeGatedFFT`'s only production caller (`gatedCaptureResult`) calibrates the result
  at once. Matching means the web applies the calibration inside the gated transform, reading the active
  calibration **when the FFT is computed**, as Swift does. Today the web copies it into the phase's search
  when the phase is armed (`matSearch`), so a calibration change between arming and capture would be
  applied differently. Swift's shape puts the transform on the web's `RealtimeFFTAnalyzer`, which holds
  the calibration. The web's file-playback harness, which sets the analyzer's calibration to the file's
  so the per-phase search picks it up, is adjusted to match. **And a calibrated gated case is added in
  all three** (owner, 2026-09-24) — no edition tests calibration on this path today.
- **Item 2 — Python and the web use Swift's periodic Hann window; comments cleaned; a window test added.**
  The symmetric window was never forced on them: `np.hanning` only makes the symmetric form, but the
  periodic one is a single numpy line (`0.5 - 0.5*np.cos(2*np.pi*np.arange(N)/N)`), and the web builds its
  window in its own loop (`denom = fftSize - 1` → `fftSize`). SciPy is not needed for either and stays
  out (removed in Python `c1de197`). Swift and the oracle do not change.
  Checked: `vDSP_HANN_DENORM` is the periodic form (max difference from `0.5·(1 − cos 2πn/N)` at 32768
  points 7×10⁻⁸, from the `/(N−1)` form 7×10⁻⁵). Through the formula, the periodic window reproduces every
  GFFT oracle value to ~4×10⁻⁶ dB; the symmetric one is off by ~1.7×10⁻⁴ dB on every case. That is under
  the 0.001 dB tolerance, which is why **no current test can tell the windows apart** and why the drift
  recurred — and the tolerance used to be 1 dB / 1 Hz, so almost any difference passed. The guard is
  therefore a **window test** in each edition, under `test/gated-fft`, comparing the gated window to the
  periodic formula, so that a return to the symmetric form fails at once. Comments cleaned with it:
  Python's docstring claiming `np.hanning` is Swift's window, the web's "numpy.hanning uses (N−1)", and
  Swift's own note that the ports use a different window. The tolerances themselves are
  [#16](https://github.com/dwsdolce/guitar-tap-project/issues/16)'s to set after the sweep, not F49's.
- **Item 3 — the wider fix (owner, 2026-09-24): every test analyzer is built with the test constructor
  unless the test genuinely needs hardware.** Swift: all 46 direct `RealtimeFFTAnalyzer()` constructions
  across 24 test files, including `GenerateParityOracle`, become `forTesting: true`. Python: the five
  `RealtimeFFTAnalyzer(None)` calls in `test_dsp.py` become `for_testing()`, and its false "opens no audio
  device" comment goes. **Each site is checked, not replaced by search**: a test that genuinely needs the
  hardware path (a device-management test, say) keeps it and states why. None found yet.

  Why the wider fix over GFFT-plus-minter only:
  1. The narrow fix leaves the hazard where it is likeliest to fire. The GFFT tests finish synchronously,
     before the queued device load runs. Many of the other sites **wait**: the S6 tests rewritten under
     F45/F46 (`StateInvariantTests.swift:27`, `ScenarioStateTraceTests.swift:62`, `StatusMessageTests.swift:43`
     and `:86`) build `RealtimeFFTAnalyzer()` and then sleep through the real cooldown and capture window.
     During that wait the `DispatchQueue.main.async` device selection runs and can load the machine's saved
     calibration into `activeCalibration` mid-test. **Not yet checked** whether that changes any of their
     results today; either way the outcome would depend on the machine running the tests.
  2. A test's result must not depend on the machine (PARITY-TEST-METHOD rule 6 — the shared-sandbox
     failure that survived every isolation check).
  3. `forTesting: true` changes only hardware: in Swift it skips device enumeration, the CoreAudio
     listener and the route observer in `init`, and the matching `stop()` / listener removal in `deinit`
     (`RealtimeFFTAnalyzer.swift:744–818`). The analysis is unchanged. `TapToneAnalyzer.forTesting()`
     already builds its analyzer this way (`TapToneAnalyzer.swift:111`), so the 46 are the odd ones out.
  4. Python's GFFT tests and the web's tests are already hardware-free; this brings Swift and the rest of
     Python into line.

  What exploring it found (checked 2026-09-24):
  - **Python:** the GFFT tests use `RealtimeFFTAnalyzer.for_testing()`, which returns before any hardware
    setup (no stream, no device enumeration, no hot-plug monitor). Even the full constructor does not
    load a calibration: it stores the device directly, bypassing the `selected_input_device` setter that
    auto-loads one. Isolated by design, not by timing.
  - **Web:** the tests call `computeGatedFFT`, a free function, so no analyzer and no calibration are
    involved. The web analyzer's constructor touches nothing either (no `AudioContext` until `start()`).
    After item 1 the transform moves onto that analyzer, so the tests will construct it — still with no
    hardware — and the new calibrated case sets the calibration explicitly.
  - **Found on the way, same shape in Python:** `test_dsp.py` (`test/dsp`, S4) calls the **full**
    constructor `RealtimeFFTAnalyzer(None)` five times. Its comment says constructing it "opens no audio
    device"; the code opens a `sounddevice.InputStream` on the default input, starts the hot-plug
    monitor, registers an `atexit` close, and on macOS runs the microphone-access check (`MacAccess`),
    which, if permission is undetermined, requests it and spins a Qt event loop until answered. At least
    one of these uses was added in S6's F36–F44 commit (`87e7ad7`, 2026-09-23) — the comment's claim was
    not verified when it was written. No calibration is loaded, so results are unaffected; the test does
    depend on the machine's audio hardware.
  - **Swift, where the calibration comes from:** `init(forTesting: false)` calls
    `loadAvailableInputDevices()`, which queues the device choice on `DispatchQueue.main.async`; assigning
    `selectedInputDevice` runs its `didSet`, which loads `CalibrationStorage.shared.calibration(forDeviceUID:)`
    into `activeCalibration` (`RealtimeFFTAnalyzer.swift:117–129`, `+DeviceManagement.swift:220–267`).
  - **The test sandbox does not cover this.** `TestSandbox` redirects only `TapDisplaySettings` (a
    per-process `UserDefaults` suite) and the saved-measurements file. `CalibrationStorage` (calibrations,
    the global active one, the device→calibration map) and the `selectedInputDeviceUID` key all use
    `UserDefaults.standard` — which, in the sandboxed test host, is the app's own container
    (`GenerateParityOracle.swift:65`). So a full analyzer under test reads **the user's real saved device and
    calibration**.
  - **And it can write the user's real setting.** `selectedInputDevice.didSet` writes
    `selectedInputDeviceUID` to `UserDefaults.standard` on every assignment. When the saved device is
    present that rewrites the same value; when it is not (the measurement mic unplugged during a test
    run), the initial load falls through to "any external mic", then the default, and **saves that as the
    user's device**. Read from the code, not observed. `activeCalibration.didSet` likewise persists the
    global active calibration and the device map unless `isLoadingDeviceCalibration` is set — whether any
    test sets a calibration on a full analyzer is not yet checked. `forTesting: true` avoids all of it,
    since no device is ever selected.
  - **Unrelated, noticed while reading:** in `RealtimeFFTAnalyzer+DeviceManagement.swift` around line 704,
    the doc comment of the device-switch function is split in two, with the doc comment for
    `setCalibrationWithoutSavingDeviceMapping` spliced into the middle of it. Comment only.
- **Item 4 — the code does not change; the comments are corrected** (owner's inclination, 2026-09-24,
  after the decaying-tap test showed today's window is as good or better for taps). In all three, GFFT3
  and GFFT5 stop claiming their tones are "bin-centred to eliminate spectral leakage": the window spans
  the padded 32768 samples and the signal only 19200, so steady tones leak (GFFT3's 0.2 dB is that). The
  oracle values stay; they pin what the transform produces. **The production comments on the gated window
  are corrected in the same change, in all three — and they matter more than the test comments** (owner,
  2026-09-24). They must say what actually happens: the Hann spans the padded 32768 samples, not the
  19200 captured; for a steady tone that leaves a hard edge (weight ≈0.93) and poor sidelobes, but for a
  tap it works, because the decay supplies the end taper and the window weights the abrupt onset at ≈0.2.
  The "~31 dB sidelobe suppression" and "the captured buffer starts and ends near silence" claims are
  replaced with that, and the sample-rate dependence of the gain is stated.
- **Item 5 — text clean-up, with three rules (owner agreed, 2026-09-24):**
  1. **Comments never state the tolerance or an expected value**; they name the oracle's field
     (`gatedFftDb`, the case's `expected`). The tolerance has moved and will move again (#16), so a number
     in a comment goes stale. Covers "within 1 dB" (Swift, Python), the web's `// 1.0 dB`, and Python's
     "must read −49.70 dB".
  2. **Swift GFFT5's history story is deleted, not rewritten** — neither its explanation nor the leakage
     one is verified, and history belongs in git. Its rationale for building the signal in Double and
     rounding to Float per sample stands on its own and stays.
  3. **Test names that carry history are renamed to say what they check, consistently in all three**
     (Swift `afterFix_binCentred_matchesPython` / Python `…_matches_swift` check the oracle; Swift
     `silence_allBinsBelowNoiseFloor` checks −∞ exactly). "Bin-centred" may stay: the frequencies are bin
     centres; only the no-leakage claim was false.
  Plain corrections with no decision: Python's window-formula docstring (true once item 2 lands), the
  web's dead epsilon comment, Python's stale `_FftProcessingThread` references.
- **Item 6 — move, and merge the duplicates (owner, 2026-09-24).** The web moves `makeToneSignal`,
  `makeSilence` and `magnitudeAtFrequency` out of `src/` into one shared helper file under `test/` (as
  `parityRunner.ts` and `selfBaseline.ts` already are); `gatedFFT.ts` then exports only the transform —
  the F45 precedent. **"Duplicates are bad no matter where they are"**: each native's two gated-signal
  builders become one — Swift `GatedFFTParityTests.swift` and `GenerateParityOracle.swift` share one
  helper; Python `test_gated_fft_parity.py` and `tests/parity_runner.py` share one helper.
- **Item 7 — Swift takes the ports' behaviour (owner, 2026-09-24):** fewer than two samples returns an
  empty spectrum. A one-bin "spectrum" of nothing is meaningless, and Swift's own caller already treats
  an empty spectrum as a failed capture ("tap again"). A change to canonical Swift, made for that
  concrete reason. A test pins it in all three.
- **The window-taper observation is not F49's.** It changes no code here (item 4). Whether it becomes its
  own issue — with the two unmeasured questions: a window-free check of the real plates, and the
  sample-rate effect on frequencies — is still the owner's to decide.

**Implementation started 2026-09-24**, in the approved order Swift → Python → web. Status: **committed in all
three** (Swift `c4611e0`, Python `c3b1bff`, web `1f858f8`), web baseline re-minted and collected into the
hub; **Python's baseline is not re-minted** (below), so its `test_self_regression` fails until #19.
*Update, 2026-09-24: done under #19 once playback was repeatable — exactly the 24 values this window
moved, agreeing with the web's to 13–14 significant digits; Python's `test_self_regression` passes
(committed with #19, Python `820fabd`).*

- **Swift:** `computeGatedFFT` returns empty for fewer than two samples; its window comments rewritten
  (plus the `window` property, documented as Hann but rectangular, and the file header). One shared
  test helper, `GatedTestSignal.swift` (`tooling/gated-signal`), used by the GFFT tests and
  `GenerateParityOracle` (whose own signal loop and `magnitudeAt` are gone). `GatedFFTParityTests`
  rewritten: renamed, text per item 5, and three new cases — the periodic window (a constant input
  leaves bins ≥ 2 below −120 dB; the symmetric window puts them near −100), fewer than two samples, and
  calibration applied inside the transform. All 40 remaining `RealtimeFFTAnalyzer()` test sites use
  `RealtimeFFTAnalyzer.forTesting()`; none used a hardware API.
- **Python:** `compute_gated_fft` uses the periodic window and a `< 2` guard; docstrings in it and in
  `realtime_fft_analyzer_fft_processing.py` rewritten (the latter also claimed `dft_anal` ran the gated
  path; it does not). `tests/gated_signal.py` shared by the GFFT tests and `parity_runner.py`. Test file
  mirrors Swift's. `test_dsp.py`'s five full constructors use `for_testing()`, and
  the false "opens no audio device" comment is gone.
- **Web:** the uncalibrated transform is `gatedHannFFT` (periodic window, `< 2` guard); the app calls
  `RealtimeFFTAnalyzer.computeGatedFFT`, which adds the active calibration at the moment of the call.
  `finishGatedFFTCapture` aligns and calls it, as Swift does; `gatedCaptureResult`, `PhaseSearch` and the
  search's `calibration` field are gone. `src/dsp/signal.ts` moved to `test/gatedSignal.ts`, with
  `magnitudeAtFrequency` from `gatedFFT.ts`; `parityRunner.ts` uses them and the analyzer's transform.
- **Mutation checks, all caught by the intended test only** (Swift also fails its zero-tolerance oracle
  cases on the window, as it should): symmetric window → the window test (in Python and web the oracle
  cases pass it at 0.001 dB — the reason the test exists); no guard with a size floor of 2 (Swift's old
  shape) → the tiny-input test; calibration skipped → the calibration test. Web only: the material
  finish path using the uncalibrated transform fails REG-B1, REG-B2, REG-P1 and REG-P2 (all calibrated);
  OUT-4 (uncalibrated) passes.
- **Suites:** Swift **608** pass (605 + 3). Python **722** (719 + 3) and web **645** (642 + 3): all pass
  except `self-regression`, which fails because the window moved their own baselines. Parity map
  **104 groups**, no problems. `tsc` clean.
- **The baseline diffs.** Web (`mint-baseline.sh`, no `--yes`): 24 values — every GFFT and every
  material value, by −0.00017 dB and a few µHz (−0.00037 dB and −1.7×10⁻⁵ Hz at most); no guitar value.
  Each new value is identical to Python's new value, and both now reproduce the oracle (e.g. GFFT1
  −15.722327). Python (`mint-baseline.py --check`): the same 24, **plus REG-G2 guitar taps 7–8 and their
  average** — that is #19, not this change: with only the window put back to `np.hanning`, the GFFT and
  material values match the baseline exactly and REG-G2 taps 7–8 still move, by a different amount on
  each run (tap 7 air −0.31, −0.40, −0.59 dB across three runs). Re-minting Python as-is would write a
  timing-dependent REG-G2 into its baseline.
- **Python re-mint: tried and abandoned (owner, 2026-09-24).** Option (a) was to re-run the minter until
  one run showed exactly the 24 window values, and adopt only that run. A scripted loop answered the
  minter's prompt "y" only on that condition: **four runs, all rejected** — REG-G2 taps 7–8 moved every
  time, and tap 6 too in one. (The minter lists at most 40 changed values; every run exceeded that.)
  Owner: "reminting from that is not reproducible or reliable". Python's baseline stays as committed and
  `test_self_regression` fails for this reason until #19 is fixed; #19's fix will move values in all three
  editions anyway, so everything is re-minted once, after it. Python being more sensitive to #19 than the
  web (whose runs have not moved REG-G2) is noted there, unexplained.
- **Noticed, not touched:** Python's `hps_peak_freq` (`realtime_fft_analyzer_fft_processing.py`) has
  no caller; the material peak finder does its own HPS.

**F50 — `tap-decisions`: the web tests a third of the detector, Swift and Python test it one level below
production, T6 does not test what it names, and production is laid out three ways. (✅ CLOSED 2026-09-25 —
all 15 items done or settled, run-reviewed in all three. Commits: Swift `fe0cfcf`, Python `dd5f608`, web
`02b762e`)**

Files: `TapDetectionTests.swift` (14) / `test_tap_detection.py` (18) / `tap-decisions.test.ts` (6 when read)
— recounted after #19 removed T4. Production: the per-chunk detector (Swift `detectTap`, Python
`detect_tap`, web private `detectTap`) and what a confirmed tap calls (Swift/Python `handleTapDetection` →
`handlePlateTapDetection`; web `beginCapture`). The detector's RULE is the same in all three — the same
thresholds, the same relative formula, `hysteresisMargin` 3, EMA α 0.05, the silent warm-up, the
post-warm-up sync frame, N-chunk confirmation, and one flag as latch and gate (the web's `prevAbove` split
was removed earlier in #17). What differs is the tests and the layout around it.

**Standing decisions (owner, 2026-09-25):** align all three to Swift unless there is a good reason not
to. Every case enters at the per-chunk production entry — Swift `onRmsLevelChanged`, Python
`_on_rms_level_changed`, web `processAudioFrame` — and a tap has fired when a capture has started
(`gatedCaptureActive`), the one effect a tap has in every edition and both capture kinds.

| # | item | status |
|---|---|---|
| 1 | The web tests a third of the detector | ✅ done (web) |
| 2 | Onset alignment: tested on the web only; the web's is a free function, the natives' a method | ✅ done (all three) |
| 3 | Two entry levels | ✅ done (all three) — one entry, one setup, one case list |
| 4 | Python's cases use a hysteresis margin production never has | ✅ done (Python; `captureWindow` all three) |
| 5 | T6 does not test relative detection (natives) | ✅ done (item 3) |
| 6 | Explanations that are wrong or stale | ✅ done |
| 7 | Production is laid out three ways; `tapDetectionLevel` unused; the settle rewrite breaks plate prompts | ✅ done (all three) |
| 8 | Python's four pipeline cases are Python-only — because of Python's own thread; an unreachable restart path dropped two warnings | ✅ docs cleaned, dead path removed (Python); owner ran the app |
| 9 | Python feeds the ring-out before detection, Swift after | ✅ done (Python) |
| 10 | The web's detection guard omits `isMeasurementComplete` | ✅ done (web) |
| 11 | The web picks relative detection by `captureKind` | ✅ done (web) |
| 12 | Onset alignment's fallbacks differ: the natives return the buffer unchanged, the web a window-sized copy | ✅ done — natives follow the web (all three tested) |
| 13 | The floor's seed at arming; the web's resume differs from Swift's; the natives keep a stale tap counter | ✅ done (all three) |
| 14 | A frequency with no pitch (0 Hz, NaN…): Swift traps, Python raises, the web prints garbage | ✅ done (all three) |
| 15 | Python's live Ring-Out box never shows a value (found by run-review step 1) | ✅ fixed (Python) and run-reviewed |

Verification: Swift **626**, Python **741**, web **675** — all pass, tsc clean; parity map regenerated.
Every rule added or changed was mutation-tested (broken deliberately, confirmed failing, restored).

**Run-review steps.** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, clearing the service worker after every build (see F30's steps).
Same list per edition, canonical first.

1. Guitar, tap count 3. New Tap, tap three times. → Each tap registers and the status counts up; the
   Ring-Out box shows a value; the result appears.
2. Plate, 2 taps per phase. Tap L once and let it ring down. → The status stays "fL tap 1/2 captured.
   Tap again..." — it must not become "Tap 1/2 captured. Tap again...". Complete L, C (and FLC). → Sensible
   peaks.
3. Guitar, tap count 3. Tap once, Pause, Resume. → Still 1/3; the next taps register normally.
4. Play a guitar file and a plate file. → Results as before.
5. Web only: during a guitar file playback, Pause, then Resume. → Playback carries on and completes
   correctly.

Python's thread start and restart (item 8) is already run-reviewed (owner, 2026-09-25).

**Run-review progress.** Step 1 on Python (owner, 2026-09-25): no ring-out — the box stayed "Waiting…"
where Swift showed a value on the same input. Item 15; fixed and re-run. All three editions then passed
the steps (owner, 2026-09-25), with one caveat: during a file playback, Pause, Resume and Cancel do
NOTHING, in all three editions (step 5) — pressing Pause, taps are still detected; Resume and Cancel have no
effect. Not from F50: no edition can pause or stop a playback (the buttons act on detection only, and
Cancel is "restart the sequence" while the file plays on), and the shared button rule does not consider
playback. The owner's options: (1) disable New Tap, Pause/Resume and Cancel during playback; (2) enable
them and make them useful (pause/resume the playback, Cancel stops it). *Decision (owner, 2026-09-25):*
decide it in the `file-playback` slug, next in S7.

**1. The web tests a third of the detector.** Its six cases were threshold wiring (= T1c–T1e), the re-arm
rule (= T1f/T1g) and onset alignment (item 2). Untested on the web: the tap's audio-time stamp (T1b),
warm-up suppression (T3), the hysteresis latch holding and clearing (T5/T5b), the post-warm-up sync frame
(T8), relative detection (T6) and the noise-floor EMA (T7).
- *Decision:* the web gains T1, T1b, T2, T3, T5, T5b, T8, T6, T7, named as in the natives. T6 is written
  correctly from the start (item 5): an elevated floor so the relative threshold differs from the absolute
  one, a level that fires under the absolute rule but not the relative one, a real capture phase, a
  capture actually started.
- *Decision — T1b needs the ring-out on the analyzer, do it now:* the web analyzer stamped no tap; its
  ring-out started in the engine from the engine's own clock. The **whole** ring-out moves onto the web
  analyzer, laid out as in Swift (moving only the start would split it, a third layout). This settles
  #19's noticed item "the web tracks the ring-out in the engine". (Owner: "it is where we are currently
  working and there is no good reason to delay the change.")
- *Done:* the analyzer has `startDecayTracking`, `stopDecayTracking`, `trackDecayFast`, `measureDecayTime`,
  `decayThreshold`, `peakMagnitudeHistory`, `decayTapAudioTime`, `tapPeakLevel`, `decayTrackingDuration`,
  `isTrackingDecay`, under `@parity dsp/decay`. A confirmed guitar tap sets `tapPeakLevel` from the
  engine's `recentPeakLevelDb` and starts tracking at the confirming chunk's audio time (from
  `detectTap`'s fire branch until item 7 gives the web `handleTapDetection`). `processAudioFrame` calls
  `trackDecayFast` after detection and outside its guards — Swift's order. The engine keeps only the peak
  hold and the audio clock; `DecayTracker`, `startDecayFromPeak`, `decayTime`, `onDecay`, its wiring in
  `useAudioEngine` and `src/dsp/decay.ts` are gone; `setDecayTime` is private. The web's self-regression
  passes unchanged — the REG-G1 ring-out did not move.
- *Done — tests:* the nine cases, all through `processAudioFrame`; T3, T8, T6, T7 arm the way the app does,
  warm-up included, and reach their states by feeding audio. `decay-tracking.test.ts` drives the
  analyzer's ring-out (vectors unchanged; the tracker's `reset` test went with the tracker — nothing in
  production called it). The web's ring-out stop moved to `audio-clock-timers.test.ts`, the natives' case
  exactly. Mutation checks, all caught: confirmation count (T1), the tap's stamp (T1b), the rising
  comparison (T2), the warm-up (T3), the falling threshold (T5), the latch clear (T5b), the sync frame
  (T8), relative detection (T6), the EMA (T7), the ring-out stop, the per-chunk ring-out feed (REG-G1).

**2. Onset alignment is tested on the web only, and laid out differently there.** The web's first case tests
`alignCaptureToOnset`, the gated capture's alignment. (First recorded as "not a detection decision" — but
Swift's own tag, `@parity dsp/gated-capture tests=test/file-playback,test/tap-decisions`, names
`tap-decisions` as where the gated capture is tested, so the case is where Swift says it belongs.) The
natives have the same function (Swift `alignCaptureToOnset`, `+SpectrumCapture.swift:773`; Python
`align_capture_to_onset`) and no test of it; Python's and the web's `dsp/gated-capture` tags name no tests.
Layout: the natives' function is a method on the analyzer, in the spectrum-capture file; the web's is a
free function in `src/dsp/gatedCapture.ts`.
- *Proposed:* the web's case (10000-sample buffer, one transient at 5000, window 4096, pre-onset 1000 →
  the transient at index 1032 = 1000 + the 32-sample backup, full amplitude) added to Swift's and Python's
  `tap-decisions`; Python's and the web's tags gain Swift's `tests=`; mutation — remove the backup.
- *Decision (owner, 2026-09-25):* the web's alignment moves onto the analyzer, unless there is a reason
  not to ("probably should have done that in F49 as well").
- *Open — scope, raised with the owner:* `gatedCapture.ts` holds more than the alignment, and Swift keeps
  the rest on the analyzer too — `findDominantPeak` (`+SpectrumCapture.swift:1035`), the capture and
  window durations and onset constants (`TapToneAnalyzer.swift` statics), the phase search bands. And
  F49's gated FFT: Swift's `computeGatedFFT` is on its FFT analyzer (`RealtimeFFTAnalyzer+FFTProcessing`),
  so the web's `gatedFFT.ts` would move onto the web ENGINE, not the analyzer.
- *Decision (owner, 2026-09-25): scope (c)* — everything in `gatedCapture.ts` that Swift keeps on the
  analyzer moves onto the web analyzer (alignment, `findDominantPeak`, the durations and onset constants,
  the search bands; the shared types stay importable), and the gated FFT moves onto the web engine, as
  Swift's `computeGatedFFT` is on its FFT analyzer. Plus the proposed test and tags.
- *Done:* **web** — `alignCaptureToOnset` and `findDominantPeak` are analyzer methods, the
  durations and onset constants analyzer statics under Swift's names (`gatedCaptureDuration`,
  `gatedFFTWindowDuration`, `preOnsetDuration`, `onsetNoiseEstimateSamples`, `onsetThresholdMultiplier`,
  `onsetMinThreshold`, `onsetBackupSamples`), the search bands the analyzer's `matSearch` laid out as
  Swift's switch; `MaterialPeak`/`DetectedMaterialPeak` are exported from the analyzer module. The
  gated transform is the engine's `computeGatedFFT` itself (with `GatedFFTResult`). `src/dsp/gatedCapture.ts`
  and `src/dsp/gatedFFT.ts` are gone, with three dead leftovers in the former (`CHUNK`,
  `LEVEL_CROSSING_CONFIRMATION_CHUNKS`, `chunkLevelDb`) and the engine's unused imports of the alignment
  and the bands. With no engine attached (tests), the analyzer uses an uncalibrated engine for the
  transform — the bare transform, as before. Tags: the web's `dsp/gated-capture` and `dsp/gated-fft` sit
  on the analyzer, as Swift's and Python's sit on their spectrum-capture files; Python's
  `dsp/gated-capture` gains `tests=test/file-playback,test/tap-decisions`. **Swift and Python** gain the
  alignment case (`onsetAlignment_placesTheTransientAtPreOnsetPlusBackup` / `test_onset_alignment`); the
  web's now calls the analyzer's method and pins the literal 1032. Mutation — the backup removed — fails
  the case in all three. Web suite 663, all pass, the self-regression unchanged (no value moved); Swift
  TapDetection 15, Python detection 20, pass. Parity map regenerated.

**3. Two entry levels.** Swift and Python call `detectTap` directly, with the warm-up, sync flag,
detection state and latch set by hand; the web drives `processAudioFrame` after `setSettings` and
`startTapSequence`. Since #19 the natives have the same entry (`onRmsLevelChanged`) and a shared audio
feed (`tooling/audio-clock-feed`).
- *Decision:* all three the same, at the per-chunk production entry (standing decisions above).
- *Consequence:* the natives' T5 fires a tap and then calls `detectTap` again; at the production entry a
  fired tap turns detection off, so the next chunk never reaches the detector. Their T5 must start latched
  above, as the web's does.
- *Also to settle here:* the entries are not quite alike. Swift's `onRmsLevelChanged` does not feed the
  ring-out (its handler closure does, after it); the web's `processAudioFrame` does, being the closure's
  body as well; Python's `_on_rms_level_changed` does not (its `_on_chunk_level_on_main` does, since item 9).
- *Decisions (owner, 2026-09-25):* (1) one per-chunk entry, the same in all three — Swift names its hop body
  `onChunkLevel(_:audioTime:)` (the closure calls it), Python renames `_on_chunk_level_on_main` to
  `_on_chunk_level`, the web's is `processAudioFrame`; the shared audio feed calls it in all three. One
  setup: arm as the app does, feed the warm-up on quiet audio, then the case — no hand-set state; "latched
  above" reached through a loud first chunk after the warm-up. One observable (a capture started), state
  read only where the case is about state. One case list, identical in all three (T1, T1b, T1c–T1g, T2, T3,
  T5, T5b, T6, T7, T8 and the three alignment cases). (2) Items 4 (for this file) and 5 are folded in:
  Python's detection cases use production's margin, and the natives' T6 becomes the corrected case.
- *Done:* **Entry** — Swift's `rmsLevelHandler` hop now calls `onChunkLevel(_:audioTime:)`
  (`onRmsLevelChanged`, then `trackDecayFast`); Python's is `_on_chunk_level`; the shared feed
  (`advanceAudio` / `advance_audio`) calls it in both, and Swift's `StatusMessageTests` (four direct calls
  to `onRmsLevelChanged`) and four comments naming the old entry now use it. **Cases** — Swift
  `TapDetectionTests.swift` and Python's detection cases rewritten to the web's setup, case for case:
  `armed` (the app's `startTapSequence`, warm-up included), `settled` (warm-up on quiet audio + one
  chunk), `latchedAbove` (warm-up, then a loud sync chunk), `chunks`; the web's cases moved to the same
  setup (they had skipped the warm-up with `arm: false`). The same 14 detector cases in all three — T1,
  T1b, T1c, T1d, T1e, T1f, T1g, T2, T3, T5, T5b, T6 (the corrected case, item 5), T7, T8 — with the same
  numbers, and Python's at production's 3 dB margin (item 4, this file), plus the three alignment cases.
  **Mutations** — eleven rules broken in turn, in all three: the confirmation count, the tap's stamp, the
  configured threshold, the latch gate, the rising comparison, the warm-up, the falling threshold, the
  latch clear, relative detection, the EMA, the sync frame. Every one caught in every edition, and the set
  of cases each one fails is the same in all three but for one difference, which found item 13. Suites:
  Swift 619, Python 731, web 665, all pass; parity map regenerated.

**4. Python's cases use a hysteresis margin production never has.** `_make_sut` defaults to 5.0, and T6/T7
set 5.0; production is 3.0 in all three and nothing writes it (Swift `let`, web `readonly`, Python a
plain attribute). So Python's T5 feeds −43 against a falling threshold of −45, Swift's −42 against −43 —
the same test name, a different case. Seven other Python test files set 5.0 as well (other slugs; the
cause is the same).
- *Done:* the detection cases moved to production's margin under item 3. The seven other files
  (`test_measurement_complete_transitions`, `test_state_invariants`, `test_start_tap_sequence_race`,
  `test_status_message`, `test_tap_count_change`, `test_wi10_qtimer_slots`, `test_scenario_state_trace`)
  no longer set 5.0; every case passed unchanged at 3, so none depended on it. Also removed: the view's
  own copy (`FftCanvas._hysteresis_margin`, from a local `_hyst = 3.0`), written and never read. Python
  suite 731, all pass.
- *Open question:* Python's `hysteresis_margin` is still a plain, writable attribute; Swift's is a `let`,
  the web's `readonly`. Nothing in production writes it, but a test could again. Python declares Swift's
  other `let` constants the same plain way (`noise_floor_alpha`, …), so making this one read-only would
  be a pattern of its own.
- *Decision (owner, 2026-09-25): (c)* — Python matches Swift on what is writable: every analyzer constant
  Swift declares `let` is read-only in Python. (History: the margin used to be a user setting; the owner
  made it a constant because it was not understood or particularly useful.)
- *Done:* Swift's five instance `let` constants — `hysteresis_margin`, `noise_floor_alpha`,
  `warmup_period`, `tap_cooldown`, `decay_tracking_duration` — are read-only properties on Python's
  analyzer (writing one raises `AttributeError`); their docs moved with them, and `tap_cooldown`'s stale
  "minimum inter-tap interval" is now what it is since #19 (the rest and the FLC hold, in audio). The web
  already declares all five `readonly`. Python suite 731, all pass.
- *Not enforceable in Python:* Swift's `static let`s (the capture durations, onset constants, status
  strings) are upper-case class constants on Python's mixins. Making a class attribute read-only needs a
  metaclass, and the analyzer is a QObject, whose metaclass it would have to combine with; the upper-case
  name is Python's convention for "do not write". Left as is.
- *Found — `captureWindow`:* Swift declared it `@Published var` (writable), the web `readonly`, Python a
  plain attribute; nothing wrote or observed it in any edition. *Decision (owner, 2026-09-25):* a constant
  in all three. *Done:* Swift `let captureWindow`, Python a read-only `capture_window` property; the web was
  already `readonly`. Its doc in both natives described a "spectrum snapshot" taken after each tap; it is
  the wait after the LAST tap before averaging, in audio (#19), as the web's doc says. Swift suite 619,
  Python 731, all pass.

**5. T6 ("plate mode uses relative detection") does not test relative detection** (Swift and Python).
With the floor at −70 and the threshold at −40, the relative rising threshold is `max(threshold, floor +
10)` = −40 — the absolute one — so the case passes under the absolute rule too. Its assertion, detection
idle, is set before the tap is routed, so it also passes if the plate tap is ignored; Python's T6 sets no
capture phase, and its tap is in fact ignored (the `NOT_STARTED` "unexpected tap" branch). The web's T6
(item 1) is the corrected case.

**6. Explanations that are wrong or stale:**
- T1f in all three says the web "splits" latch and gate through `prevAbove`; the web no longer has it, yet
  its two re-arm cases still write `s.prevAbove = true` — a field that does not exist.
- The cooldown gate's removal is explained two ways. Swift's production comment and both natives' test
  comments say nothing in production reached it; Python's says Python's file playback did — which is what
  #19 measured. The Swift wording is my first, wrong claim.
- Python: the module docstring still lists "cooldown"; `_make_sut` says "Mirrors Swift:
  sut.analyzerStartTime = …" (no such field) and "ensure measurement_type is acoustic" while setting
  CLASSICAL (Swift sets `.acoustic`, the web `'classical'`); five unused `import time` lines; "(Part 5)".
- Swift: the suite's `init()` says settings are redirected "by TestRunner.setUp()" — `TestRunner` has no
  `setUp`; `TapDisplaySettings` redirects itself. `detectTap` says the headroom is "clamped to at least
  6 dB"; the code clamps to 10.
- *Done:* the test-file items went with item 3's rewrite (T1f's `prevAbove` text and the
  web's writes to it, the natives' cooldown comments, Python's docstring, `_make_sut`, unused imports,
  "(Part 5)" there, Swift's `TestRunner.setUp` comment). Left in production and fixed: Swift's cooldown-gate
  comment now tells what #19 measured — nothing reached the gate in Swift, Python's playback did, the
  same audio was decided two ways, and the auto-advance's latch made the gate redundant in all three;
  Swift's "clamped to at least 6 dB" now says 10. Also found and fixed, the same kind: Python cited a Swift
  `analyzerStartTime` (gone since the warm-up moved to the audio clock) in four places — one stale
  duplicate comment removed, three now name `warmupStartAudioTime = fftAnalyzer.audioElapsed`; and
  `test_decay_tracking.py`'s "(Part 5)". Dead code found on the way and removed (the owner's standing
  rule): Python's `reset_tap_detector` and the view's wrapper of it — the wrapper had no caller, the
  analyzer's was called only by the wrapper, and its docstring ("called after device change, new tap
  sequence, resume, cancel") was false. The web's `prevAbove` mentions are accurate history and stay.
  Python suite 731, all pass.

**7. Production is laid out three ways** (layout is architecture):
- A confirmed tap: Swift and Python go `handleTapDetection` → (material) `handlePlateTapDetection`, which
  checks the material phase and ignores a tap in `notStarted`/`reviewing…`/`complete` with a warning. The
  web has neither function: `detectTap` turns detection off, starts the ring-out and calls one
  `beginCapture` for both kinds, with no phase check.
- Swift turns detection off twice for a material tap (both functions); Python once; the web once.
- When the signal settles, Swift and Python rewrite the status to "Tap k/N captured. Tap again..." for k
  between 1 and N−1; the web writes it only when a capture finishes.
- `tapDetectionLevel` (Swift `@Published`, Python attribute) is written every chunk and read by nothing;
  the web has none — the pattern F43 removed (`tapDetected`).
- *Decision:* make the three the same; remove `tapDetectionLevel`. Details when the item is reached.
- *Found while planning (probe, Python):* the settle rewrite is a DEFECT for plate — with 2 taps per phase,
  after fL tap 1 the prompt "fL tap 1/2 captured. Tap again..." became the guitar "Tap 1/2 captured. Tap
  again..." once the ring-out fell (the rewrite calls `guitarLoopStatus` whatever the mode). For guitar it
  writes the string the capture's finish already set. Swift has the same code (not run there).
- *Decisions (owner, 2026-09-25):* (7a) remove `tapDetectionLevel` from Swift and Python. (7b) remove
  Swift's second, redundant idle in `handlePlateTapDetection` (its only caller, `handleTapDetection`, has
  just set it). (7c) remove the settle rewrite from Swift and Python — the web's behaviour — with a test in
  all three that a plate prompt survives the ring-out's fall and a guitar prompt is unchanged. (7d) the web
  gains `handleTapDetection` and `handlePlateTapDetection` routed as Swift's, and its `beginCapture` splits
  into Swift's `startGatedCapture(phase)` and `startGuitarGatedCapture()`.
- *Done:* (7a) `tapDetectionLevel` removed from Swift (`@Published var` and its write) and
  Python (attribute, docstring entry, write). (7b) Swift's `handlePlateTapDetection` no longer sets idle; a
  comment says its only caller already has. (7c) the settle rewrite removed from Swift's `detectTap` and
  Python's `detect_tap` (the falling edge keeps only its debug line). (7d) the web: `detectTap`'s fire
  branch sets `tapPeakLevel` and calls `handleTapDetection(audioTime)` — detection idle, then plate/brace to
  `handlePlateTapDetection` (the phase switch: a capturing phase or `waitingForFlcTap` opens the capture,
  any other phase is ignored with a warning), guitar to `startDecayTracking`, the "capturing" status and
  `startGuitarGatedCapture`; `beginCapture` is split into `startGatedCapture(phase)` and
  `startGuitarGatedCapture()`, each choosing its buffer and scheduling its own stall timeout as Swift's do
  (the shared pre-roll seeding is `openCaptureWindow`), replacing `scheduleCaptureSafetyTimeout`.
  **Tests (all three):** `settle_leavesAPlatePromptAlone` and `settle_leavesAGuitarPromptAlone` (Python
  `test_settle_leaves_a_plate/guitar_prompt_alone`, web "the settle leaves a plate/guitar prompt alone"): a
  real tap, the real capture finish, the rest ending while it rings (latched above), the ring-out falling —
  the prompt is unchanged. **Mutation:** the settle rewrite put back fails the plate case in all three —
  in Swift that is its old code, so Swift had the defect too. Swift's guitar case sets up the frequency axis
  first (`actualSampleRate`, `updateFrequencyBins`, a short wait), as `StateInvariantTests` does — without
  it every peak lands at 0 Hz, which crashed the test process (item 14). Suites: Swift 621, Python 733, web
  667, all pass; parity map regenerated.
- *Not tested, noted:* the plate phase check (a tap in a non-capturing phase is ignored) has no case in any
  edition.

**8. Python's four pipeline cases are Python-only — because Python has a thread the others do not.** (First
recorded as "the other editions deliver once by construction"; that overstated it.) Python's per-chunk
path now has Swift's shape: one level outlet for the analyzer, one for the UI meter, one frame delivery.
What is Python's alone is `_FftProcessingThread`: PortAudio's callback must return at once, so a QThread
drains the queue, and — `RealtimeFFTAnalyzer` not being a QObject — that thread object carries the
pipeline's Qt signals. Each `connect()` adds a receiver, and `fftFrameReady` is connected in two places:
`_wire_pipeline_signals` (from `__init__`) and `recreate_proc_thread`, which `FftCanvas.start_analyzer`
calls to replace a running thread. The four cases guard that risk and the exact float level (F44).
- *Owner asked (2026-09-25): is this clearly documented?* No — the thread's docstring gave the reason it
  exists, but not that it carries the signals (one signal's comment did); `recreate_proc_thread` said it
  resets "all processing state" (the object holds none — `reset_state()` does the reset), that it returns
  the thread "so FftCanvas can reconnect signals" (the analyzer reconnects its own; the view only
  `finished`), and "Swift achieves equivalent reset via AVAudioEngine stop/start" without saying what;
  the view said `fftFrameReady` is connected "inside TapToneAnalyzer.start()" (it is `__init__`, through
  `_wire_pipeline_signals`); `_wire_pipeline_signals` still described the pre-#19 wiring; the test class
  said "by construction".
- *Done — documentation only (owner: "Clean up the documentation"):* the thread's docstring (it carries the
  signals, what follows from that, it holds no state); `recreate_proc_thread` (when it runs, what is and
  is not reset, which receivers it connects, the double-delivery rule); `_wire_pipeline_signals` (what it
  wires, once, from `__init__`); the two connect sites; the view's `_connect_proc_thread_signals` and
  `start_analyzer` comments; the test class docstring. No code changed.
- *Defect — found while documenting:* `recreate_proc_thread` reconnected only `fftFrameReady` and
  `gatedCaptureComplete`; `_wire_pipeline_signals` had also connected `clippingChanged` and
  `inputAppearsDeadChanged` to the original thread, and nothing reconnected them — so after a replacement
  the clipping and dead-input warnings would no longer reach the analyzer. Replacing the object was not
  needed either: it holds no processing state, `reset_state()` does the reset, and a finished QThread can
  be started again.
- *Decision (owner, 2026-09-25):* stop replacing the thread — test first, to show the defect. A new case
  ran the view's real `start_analyzer` on a RUNNING thread and **failed on the old code** ("the clipping
  warning no longer reaches the analyzer"; a control without the restart delivered both).
- *Then found: no user action reaches that path.* `start_analyzer` is called only when the thread is not
  running — at startup, on the first file playback, and from New Tap's fallback if the thread has died —
  and nothing stops the thread before shutdown (`stop_analyzer` had no caller). So the defect was real in
  code no user could reach. The owner ran the app (live tap, live capture, playback, New Tap): all worked.
- *Decision (owner, 2026-09-25):* "Dead code needs buried — remove it."
- *Done (Python):* removed `recreate_proc_thread`, `start_analyzer`'s running-thread branch,
  `stop_analyzer`, and the view's `finished` wiring (`_connect_proc_thread_signals` connected it to
  `_on_proc_thread_finished`, whose body was `pass`). The thread is created once, with the mic, and never
  replaced; every receiver is connected once, at construction. Docs match (the thread,
  `_wire_pipeline_signals`, `start_analyzer`, the test class); a stale watchdog comment corrected (it said
  the thread is rebuilt around a recovery restart; it is not). The case is now
  `test_the_started_processing_thread_reaches_the_analyzer_once`: the view's real `start_analyzer` on a
  thread not yet running — the app's path — then clipping, dead input and one frame reach the analyzer.
  Mutations, both caught: a second frame connection in `start_analyzer` ("analysed 2 times"); bringing
  back the replacement with two reconnects ("the clipping warning does not reach the analyzer"). Python
  suite 728, all pass.

**9. Python fed the ring-out before detection, Swift after.** Swift's rmsLevelHandler calls
`onRmsLevelChanged` and then `trackDecayFast`, so the confirming chunk is recorded into the new ring-out;
Python's `_on_rms_level_changed` called `track_decay_fast` before `detect_tap`, and from inside itself.
- *Decision:* as Swift — after detection, from the main-thread delivery. If Python's REG-G1 ring-out
  moves, that value is re-minted. (It did not: the self-regression passes unchanged.)
- *Done:* the queued delivery is `_on_chunk_level_on_main` — `_on_rms_level_changed`, then
  `track_decay_fast`, both with the chunk's audio time; docstrings and two test comments updated.

**10. The web's detection guard omitted `isMeasurementComplete`**, which Swift's and Python's check.
*Done:* `processAudioFrame` skips detection when the measurement is complete.

**11. The web picked relative detection by `captureKind`**; Swift and Python by the measurement type.
*Done:* `detectTap` decides by the measurement type (plate or brace).

**12. Onset alignment's fallbacks differ** (found while doing item 2). When the buffer is shorter than the
noise estimate (2048 samples), or no sample clears the onset threshold, Swift and Python return the buffer
UNCHANGED — for a material capture the whole 0.5 s (24000 samples at 48 kHz); the web returns the first
`windowSize` samples, zero-padded — 0.4 s. So in those cases the natives transform 0.5 s of audio and the
web 0.4 s: different spectra from the same capture. Present before item 2 moved the code; not changed.
- *Owner asked: which is the better answer?* The web's, for material (for guitar the two are the same
  buffer — the capture is already the window length). The pipeline assumes every material tap reaches the
  transform at one length: that fixes the bin grid (so a phase's taps can be averaged bin for bin) and the
  window's gain (F49: the Hann spans the padded length, so the gain depends on how much of it the audio
  fills). A short buffer returned unchanged (e.g. a capture the safety timeout closed early) pads to a
  different grid; the full 0.5 s returned unchanged lands on a different gain. A concrete reason not to
  follow Swift.
- *Decision (owner, 2026-09-25):* Swift and Python follow the web — both fallbacks return exactly
  `windowSize` samples, the start of the capture, zero-padded — with a test of each fallback in all three.
- *Done:* Swift `alignCaptureToOnset` and Python `align_capture_to_onset` return the start
  of the buffer, window-sized and zero-padded, in both fallbacks (a local `leadingWindow` /
  `leading_window`, as the web's inline copy); their docs say why. All three gain the same two cases — a
  1000-sample buffer (too short for the noise estimate) and a 10000-sample buffer with no onset — each
  asserting the output is exactly the window, holding the buffer's start. Mutation — each fallback put
  back to "return the buffer unchanged" — fails its case in all three. Swift's alignment cases use
  `#require` on the length first: the first mutation run read past the end of the 1000-sample result and
  trapped, crashing the test process (the owner saw the crash report); it now fails cleanly. Swift suite
  619, all pass; Python suite 731, all pass; web tap-decisions 17.

**13. The noise floor's seed when a sequence is armed differs** (found by item 3's mutations: with the
warm-up or its sync frame broken, the natives' T7 fails and the web's does not). Swift and Python seed
`noiseFloorEstimate` from the current input level (−100 when the warm-up is skipped — guitar file
playback); the web seeds a fixed −60 (`noiseFloorInitialDb`). Normally invisible: the warm-up's exit
re-anchors the floor to the real level. Same thing, a different way.
- *Found while planning:* the web arms a new sequence and a resume through one `armWarmup`; Swift keeps them
  apart, and the web's resume differs from Swift's in four ways — it resets the floor to −60 (Swift leaves
  it), skips the warm-up in guitar file playback and then starts latched above (Swift always restarts the
  warm-up with the latch down), and resets the tap-confirmation counter (Swift does not).
- *The counter (owner asked what a resume does):* Swift and Python reset it only inside the detector (a
  fall, a fired tap, a chunk below the rising threshold) — not at a pause, a resume or `startTapSequence`.
  A pause taken just after one loud chunk leaves it at 1; after the resume's warm-up and sync frame, if the
  first counted chunk is above the rising threshold, the tap fires on ONE chunk instead of two — the
  two-chunk confirmation that rejects noise bumps is bypassed. The web resets it at both, so it always
  needs two.
- *Decisions (owner, 2026-09-25):* align the web to Swift — a new sequence seeds the floor from the current
  input level (−100 when the warm-up is skipped); resume does exactly Swift's (warm-up restarted, latch
  down, floor and sync flag left alone). And Swift and Python take the web's counter reset — on resume AND
  when a new sequence starts (b): a concrete reason not to follow Swift.
- *Done:* **web** — a new sequence seeds the floor as Swift's does (`skip ? -100 :
  inputLevelDb`; the unused `noiseFloorInitialDb` constant removed); `resumeTapDetection` no longer goes
  through `armWarmup` — it restarts the warm-up at the audio time, puts the latch down and resets the
  counter, leaving the floor and the sync flag alone. **Swift and Python** — `startTapSequence` and
  `resumeTapDetection` reset the confirmation counter. **Tests (all three):** a new sequence seeds the floor
  from the input level (−100 with the warm-up skipped); a new sequence, and a resume, restart the tap
  confirmation (one chunk counted before, one after — no tap; two — a tap); a resume keeps the floor and
  puts the latch down. (A first draft of the new-sequence case fed quiet chunks between, which reset the
  count by themselves; rewritten before the mutations ran.) **Mutations — all eight caught:** each counter
  reset removed (Swift, Python, web; start and resume), the web's −60 seed put back, the web's floor reset
  on resume put back. Suites: Swift 626, Python 741, web 675, all pass; parity map regenerated.
- *Noticed:* the web also reset the counter at every material phase arm (`prepareMaterialCapture`) and
  after each guitar capture (`finishGuitarGatedCapture`); the natives do not. *Owner asked: should the
  natives do the same?* No — every one of those follows a fired tap, which sets the counter to 0, and
  detection has been off since (Accept and Redo exist only in a reviewing phase; the FLC hold, the rest and
  the auto-advance follow a capture), so a reset there does nothing. *Decision (owner, 2026-09-25):* remove
  the web's if it does nothing. *Done:* the web's start reset moved into `startTapSequence`
  itself, as Swift's and Python's are, and the resets in `prepareMaterialCapture`, `armGuitarDetection` and
  `finishGuitarGatedCapture` removed — the web now resets the counter in exactly Swift's places (a new
  sequence, a resume, and inside the detector). Mutation: the start reset removed fails "a new sequence
  restarts the tap confirmation". Web suite 675, all pass.

**14. Swift's `Pitch.pitch` traps on a 0 Hz (or NaN) frequency** (found by item 7's guitar settle test).
`Int(round(12 * log2(frequency / c0)))` — `log2(0)` is −∞, and converting it to `Int` is a fatal error, so
`findPeaks` → `makePeak` → `pitchCalculator.note` takes the process down if a peak's frequency is 0. It
happened in a test because an unstarted analyzer's frequency axis is all zeros until
`updateFrequencyBins()`'s main-queue block runs. In the app the axis is set long before a tap, so no user
path is known to reach it. Checked in all three: Python's `log2(0)` raises `ValueError` on the same path; the
web's `Math.log2(0)` gives the note "undefinedNaN" (no crash).
- *Decision (owner, 2026-09-25):* "no pitch" — an empty note, 0 cents, 0 Hz.
- *Done:* each edition's `Pitch` gains `hasPitch` / `has_pitch` (finite and positive), and
  every function answers "no pitch" for a frequency without one: `note` and `formattedNote` empty, `cents`
  and `freq0` 0, `pitchRange` (0, 0), `isInTune` false, `pitch` (0, 0) — no trap, no exception, no
  garbage. The same parametrized case in all three (0, −5, NaN, +∞). Mutation — `note`'s guard removed, so
  a frequency with no pitch reads "C0" — fails the case in all three (a mutation that brings the trap back
  was not run: it would crash the Swift test process again). Suites: Swift 622, Python 737, web 671, all
  pass.

**15. Python's live Ring-Out box never shows a value** (found by run-review step 1: "Waiting…" on Python
where Swift showed a value on the same input). Not from this finding's changes: the box listened only to
`ringOutMeasured`, and nothing had emitted it since the old DecayTracker was removed (2026-04-05,
`e3b6622`). The analyzer measured the ring-out (`current_decay_time`; file playback's REG-G1 passes, and
it is saved with a measurement), but nothing told the view. Swift's `currentDecayTime` is `@Published`;
the web's goes through its snapshot (checked by reading: engine → `processAudioFrame` → `trackDecayFast`
→ `setDecayTime` → `notify` → snapshot → `AnalysisResults`).
- *Decision (owner, 2026-09-25):* fix the Python.
- *Done:* `current_decay_time` is a property whose setter emits `currentDecayTimeChanged`
  (seconds, or None) on a change — Python's `@Published`; the canvas relays it, and the view's
  `set_ring_out` shows the value or "Waiting…" for None. One connection now covers a live measurement, a
  new tap clearing it, and a load (which writes the same property). Removed: `ringOutMeasured` (analyzer
  and canvas), the view's separate load-time write, and `_ring_out_s` / `_on_ring_out_measured` (written,
  never read). Test (Python-only — the mechanism is): `TestRingOutReachesTheView` — a decay fed through
  `_on_chunk_level` is measured and reaches the signal; the next tap sends None. Mutation: the emit
  removed fails it. Python suite 742, all pass.

**F51 — `tap-progress`: the natives' progress cases test their own arithmetic, the editions test at
different levels with hand-set state, and the web fakes an engine that no longer exists. (✅ CLOSED 2026-09-25 —
all 7 items done and run-reviewed in all three. Commits: Swift `8d3e66d`, Python `97d4a8f`, web `6135ab2`)**

Files: `TapProgressTests.swift` (12) / `test_tap_progress.py` (12) / `tap-progress.test.ts` (14).
Production: `totalPlateTaps`, `tapProgress` and the cumulative material `currentTapCount`, written by the
capture finishes, Accept/Redo and completion. The RULE is the same in all three — `totalPlateTaps` =
taps × (brace 1 / plate 2 / plate+FLC 3); progress = count ÷ (guitar ? taps : totalPlateTaps), clamped;
the material count cumulative across phases and rebased to the prior phases on Redo.

| # | item | status |
|---|---|---|
| 1 | Five native cases assert the test's own arithmetic, not production's `tapProgress` | ✅ done (all three) |
| 2 | Entry levels differ, and the natives hand-set state for Redo, the FLC cooldown and F34 | ✅ done (all three) |
| 3 | The case lists differ | ✅ done (all three) |
| 4 | The web's fake device fakes eight engine methods that no longer exist | ✅ done (web, under item 2) |
| 5 | The web's `beginGuitarAccumulation` has no production caller | ✅ done (web) |
| 6 | `tapProgress` is written two ways | ✅ done (all three) |
| 7 | Stale references | ✅ done (all three) |

**Run-review steps.** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, clearing the service worker after every build (see F30's steps).
Same list per edition, canonical first. Watch the status-bar progress bar.

1. Guitar, tap count 3. New Tap, tap three times. → The bar fills a third per tap and is full when the
   measurement completes.
2. With that measurement complete, set Taps to 5. → The bar stays full.
3. Press New Tap. → The bar empties.
4. Plate with FLC, 2 taps per phase. Tap L twice. → The bar is at a third. Accept. → Unchanged. Tap C twice,
   press Redo. → Back to a third. Tap C twice, Accept, tap FLC twice, Accept. → Full; complete.
5. Brace, 2 taps. Tap twice. → Half, then full; complete.
6. Plate, tap L once, then load a saved measurement. → The bar and the Analyzing indicator go away.

**Run-review progress.** All three editions passed steps 1–6 (owner, 2026-09-25).

**1. Five native cases assert the test's own arithmetic.** Swift and Python's "guitar divides by
numberOfTaps", "material divides by totalPlateTaps" and "clamped to 1" compute `min(1, count / total)`
inside the test and assert that; Swift's and Python's guitar case even writes `tapProgress` itself and
then reads it back. None reaches the code that writes `tapProgress`. The web's equivalents drive
production (`recordGuitarTap` / `recordMaterialTap`) — except its "never exceeds 1", which records one
tap of a 1-tap brace and asserts ≤ 1, and cannot fail.
- *Decisions (owner, 2026-09-25):* the guitar case is rewritten in all three on real guitar taps through
  the capture finish (¼, ½, ¾ of 4 taps). The material-denominator case is removed in all three: the
  count-across-phases case asserts the same thing (2/6 after L) through production. The clamp case is
  removed in all three: no production path reaches the clamp (a measurement completes on its last tap,
  and the tap count is locked mid-sequence); the clamp stays in the code as a guard. The level real taps
  enter at, for this suite (item 2's question): **(a) the capture finish** — progress changes only when a
  capture finishes, so that is where it is decided.
- *Done:* the guitar case in all three is now "guitar progress advances by numberOfTaps as
  taps are captured": a 4-tap guitar sequence, three real taps through `finishGuitarGatedCapture`, ¼ → ½ → ¾
  (Swift sets up the frequency axis first, as `StateInvariantTests` does). The natives' material and clamp
  cases and the web's clamp case are removed; the web's guitar case no longer calls
  `beginGuitarAccumulation` / `recordGuitarTap`. Mutation — the guitar denominator changed to taps + 1 —
  fails the case in all three. Counts: Swift 10, Python 10, web 13.

**2. Entry levels differ, and the natives hand-set state.** The natives' count-across-phases case drives
the real finish (`finishGatedFFTCapture`); their Redo cases, FLC-cooldown case and F34 case set the
spectra, count, phase and completion by hand. The web drives real taps everywhere, but one level below
the finish (`recordMaterialTap` / `recordGuitarTap`, with synthetic spectra), although it has had the
public finishes since F45. F50 settled the same question for `tap-decisions` (production entry, no
hand-set state).
- *Decision (owner, 2026-09-25):* test changes only, no app code: every case reaches its state through
real taps at the capture finish (item 1's level (a)) — the natives' count case arms with
`startTapSequence()`; their Redo, FLC-cooldown and F34 cases reach their phases through real taps, real
Accepts and the real FLC hold fed in audio; the web's material cases move from `recordMaterialTap` to
`finishGatedFFTCapture` with real samples, its Redo-FLC case stops skipping the hold by hand, and its F34
case becomes the natives' (a real completed 1-tap measurement). A defect exposed on the way is raised, not
fixed here.
- *Done (tests only):* all three reach every state through real taps at the capture finish,
real Accepts and the real FLC hold fed in audio — shared helpers `plateReviewingL` / `plateReviewingC`
(Python `_plate_reviewing_l` / `_c`; web `tapL` / `tapC` / `tapFlc` / `tapBrace` on `finishGatedFFTCapture`
with real samples). The natives' count case arms with `startTapSequence()`; Python's suite builds its
analyzer with `for_testing` instead of attaching a mic by hand; F34 completes a real 1-tap measurement (a
tap through the finish, then the capture window's audio) in all three. Removed: the hand-made spectrum
helpers (Swift `spec()`, Python `_spec()`, the web's `spectrum()`; the web's load cases keep a small
frozen spectrum as the load's input data). No defect exposed. **Mutations — all nine caught:** Redo's
rebase set to 0, the FLC hold's phase guard removed, a tap-count change recomputing the bar — each in
all three. Suites: Swift 624, Python 740, web 674, all pass.

**3. The case lists differ.** Web-only: two `loadMeasurement` teardown cases, the count continuing
through the FLC Accept, a brace case. The F34 case is a different case under one name: the natives
hand-set a COMPLETE measurement, the web's never completes (`isMeasurementComplete` stays false). The
FLC-cooldown case restarts with `cancelTapSequence()` in Swift, `start_tap_sequence()` in Python and
`startTapSequence({ arm: false })` on the web.
- *The F34 part is settled by item 2:* the web's case is now the natives' — a real completed 1-tap
  measurement. Still open: the web-only cases, and the FLC-hold case's three restart calls.
- *Decisions (owner, 2026-09-25):* (a) the FLC-hold case restarts with `cancelTapSequence()` in all three
  — the user action it names (the web's `{ arm: false }` goes). (b) the web's two load-teardown cases are
  kept and given to the natives: in all three, arm and tap for real, then the real `loadMeasurement` (the
  web moves from `restoreSnapshot`, and stops setting detection to listening by hand) — the same steps and
  assertions in all three. (c) the web's brace case is added to the natives, through real taps. (d) the
  natives' count case continues through Accept C, as the web's does (the count stays 4 while waiting for
  the FLC tap). With these the three case lists are identical.
- *Done (tests only):* (a) Python and the web restart with `cancelTapSequence()`, as Swift did.
  (b) the natives gain `LoadTearsDownInterruptedCaptureTests` (Python `TestLoadTearsDownInterruptedCapture`)
  and the web's two cases move to the real `loadMeasurement` — in all three: a plate sequence to "waiting
  for the FLC tap" through real taps and Accepts, then a load (count 0, progress 0, phase complete, not
  detecting, complete); and a sequence re-armed by the real rest after one tap, then a load (detection
  off). The measurement loaded is a saved classical one, built as each edition's MC7 test builds it.
  (c) the natives gain the brace case (½ → 1, complete). (d) the natives' count case continues through
  Accept C. No defect exposed. **Mutations — all caught, in all three:** the load's count reset removed,
  the count zeroed at Accept C, the brace total doubled. The three case lists are now identical — 13 cases
  each. Suites: Swift 627, Python 743, web 674, all pass; parity map regenerated.

**4. The web's fake device fakes eight engine methods that no longer exist** — `armMaterial`, `arm`,
`disarm`, `checkpointSession`, `redoSession`, `startSessionRecording`, `finishSessionRecording`,
`cancelSessionRecording`. Detection and the session moved to the analyzer (F30); the fake passes only
because nothing calls them.
- *Done under item 2:* `finishGatedFFTCapture` asks the attached device for the gated
  transform, which the fake lacked, so the fake is gone: the suite runs with no device (the analyzer's
  uncalibrated-engine fallback — the bare transform), as `tap-decisions` does.

**5. The web's `beginGuitarAccumulation` has no production caller** — only this suite and
`tap-count-change.test.ts` call it (the pattern F43 removed).
- *By the owner's standing rule* ("dead code needs buried", 2026-09-25): removed.
- *Done:* the method is removed. This suite stopped calling it under item 1; the one other call,
  in `tap-count-change.test.ts`, came straight after `startTapSequence()`, which already empties the
  captured taps (`clearResult`), so it did nothing and is removed. Web suite 674, all pass.
- *Noticed, not acted on:* that `tap-count-change` case (S6, closed) still records taps one level below the
  capture finish (`recordGuitarTap` with a synthetic spectrum) — the question item 2 settled here.

**6. `tapProgress` is written two ways.** Swift and Python write it explicitly at each site — the guitar
and material finishes, Redo's rebases, completion (pinned to 1.0), a new sequence. The web recomputes it
inside the `currentTapCount` setter on every write. The same values in every case here; a different
mechanism.
- *Found while planning:* Swift and Python write it at the SAME 11 sites (a new sequence 0; Accept completing
  a plate 1.0 ×2; the three Redo rebases; a load 0; the guitar and material finishes, count ÷ total;
  material and guitar completion 1.0). The web moved to the setter in F30 because explicit sites "missed
  external writers" — no longer so: no view writes the count, and the one outside writer,
  `setCurrentTapCount`, is called only by a `status-message` test. The web also rewrites the count at
  Accept and at file playback's auto-advance, to the value it already holds.
- *Decisions (owner, 2026-09-25 — "let's see if we can clean up the mess we made"):* (1) the web takes
  Swift's layout — `currentTapCount` a plain field, `tapProgress` written explicitly at Swift's 11 sites;
  (2) the web's no-op count rewrites at Accept and the auto-advance are removed; (3) `setCurrentTapCount`
  (dead in production) is removed, and its `status-message` test sets the count through real taps. Each
  of the 11 writes is removed in turn to confirm a case fails; where none does, a case is added in all
  three.
- *Done:* **web** — `currentTapCount` is a plain field; `tapProgress` is written at Swift's sites
  (a new sequence, the guitar and material finishes, Redo's rebase, a load, Accept completing a plate,
  brace completion, guitar completion); the setter, `syncTapProgress`, the count rewrites at Accept and at
  the auto-advance, the guitar finish's two count rewrites (to the value `recordGuitarTap` had just set) and
  `setCurrentTapCount` are gone; the `status-message` case that used it reaches its count through real
  taps. **Each write removed in turn, in all three:** the three Redo rebases, the load and the guitar and
  material finishes are caught; a new sequence's reset to 0 was NOT (every case started from a fresh
  analyzer) — a case added in all three, "a new sequence resets the bar" (a completed 1-tap measurement,
  then New Tap: 0), and removing the reset now fails it in all three. Web suite 674 → 675 with the new case.
- *The four completion pins:* the two Accepts that complete a plate, brace completion and guitar completion
  wrote 1.0. No case could catch their removal, in any edition: at each, the last tap had already written
  count ÷ total = 1 (a measurement completes on its last tap, and the tap count is locked mid-sequence), so
  the pin wrote the value the bar already had. *Decision (owner, 2026-09-25):* remove them from all three,
  as writes that do nothing (as 7b's redundant idle). *Done:* removed in Swift (2 in `+Control`, 2 in
  `+SpectrumCapture`), Python (2 in `_control`, 2 in `_spectrum_capture`) and the web (4); comments that said
  "pinned to 1.0 at completion" now say the last tap leaves it at 1. Every remaining write in every edition
  is caught by a case. Suites: Swift 628, Python 744, web 675, all pass.

**7. Stale references.** All three headers cite "Swift TapDetection:360" for `totalPlateTaps` (now line
447); Swift's cites "Controls:420" for the progress bar (now 428, with two more bars at Controls:516 and
Layouts:698). The natives' count case sets `tapDetectionThreshold = -90 // accept the synthetic taps` —
the finish path it drives does not read the threshold.
- *Done (comments and test names only):* the threshold line went with item 2's rewrite. Each
  line-number reference now names its symbol instead (`totalPlateTaps`, `redoCurrentPhase`, the status-bar
  label in `TapToneAnalysisView+Controls`), in all three headers and in two of the web's `describe` names;
  the web header's "rebases … on Accept/Redo" now says Redo (after item 6, Accept no longer rebases).

**F52 — `file-playback`: the web checks peaks it computes itself, the editions assert different things,
and every file's explanation of OUT-4 is out of date. (CLOSED — all 9 items done and run-reviewed in all three. Commits: items 1–7 Swift `61dd996`, Python `f62d43d`, web `2c7d6d2`; items 8–9 with F53 Swift `835b39c`, Python `4980c01`, web `170f8eb`)**

Files: `FilePlaybackRegressionTests.swift` (8) / `test_file_playback_regression.py` (8) /
`file-playback.test.ts` (11). Production: the whole playback path — the file read and its pacing, detection,
the gated captures, averaging, peak selection and mode classification, the material auto-advance. All three
play the same fixtures against the same oracle (REG-G1, REG-G2, REG-B1, REG-B2, REG-P1, REG-P2, OUT-4).

| # | item | status |
|---|---|---|
| 1 | The web's guitar cases check peaks the test computes, not the analyzer's | ✅ done (all three) |
| 2 | The assertions differ, and the web wraps results in a test-only type kept in the engine | ✅ done (all three) |
| 3 | The case lists differ | ✅ done (all three) |
| 4 | Tolerance use differs | ✅ done (all three) |
| 5 | The playback harness sits in production code in the natives, in the test on the web | ✅ done (all three) |
| 6 | Swift prints plate diagnostics and reads the debug log on every plate run | ✅ done (Swift) |
| 7 | Stale explanations | ✅ done (all three) |
| 8 | Carried in: the playback controls, and two items from #19 | ✅ done (all three) |
| 9 | The web never names the file being played | ✅ done (web) |

**1. The web's guitar cases check peaks the test computes, not the analyzer's.** REG-G1 and REG-G2 run
`modePeaksFromSpectrum` on the frozen spectrum, with the test's own Peak Min and guitar type, and assert
that. The natives read what the app shows: `getPeak(for:)` — the Results panel's API — and, per tap,
`TapEntry.resolvedModePeaks()`, the path the multi-tap view and the PDF take.
- *Found while planning:* the web analyzer has both answers — `definitivePeak(mode)` (Swift's `getPeak(for:)`
  rule; it feeds the Results panel and the Averaged row) and `tapEntries[i].peaks`, resolved by the free
  function `resolvedModePeaks(peaks, guitarType)` (what the multi-tap view shows). `playGuitar` is shared
  with the web's self-baseline mint, so the baseline's guitar values would switch to the analyzer's too.
- *Decisions (owner, 2026-09-25):* the web's REG-G1/REG-G2 assert the analyzer's own peaks; and the web's
  names and shape are aligned with Swift's — `definitivePeak` becomes `getPeak`, and per-tap resolution
  becomes a method on the entry, `entry.resolvedModePeaks()`, as Swift's is. If the baseline's guitar values
  move, stop and show the owner.
- *Found while planning — behaviour, not only shape:* Swift's `TapEntry` (built in `processMultipleTaps`)
  carries `id`, `tapIndex`, a `snapshot` recording the guitar type at capture, `peaks` and `selectedPeakIDs`
  (`guitarModeSelectedPeakIDs`, one per mode); `resolvedModePeaks()` resolves over the SELECTED peaks with the
  snapshot's guitar type, and a load restores all of it from the file. The web's entry has only a spectrum
  and peaks: its rows resolve over ALL peaks, and a load re-finds the peaks from the saved spectra. (Both
  classify the rows with the CURRENT guitar type: Swift's table passes `TapDisplaySettings.guitarType` to
  `resolvedModePeaks(guitarType:)`; the snapshot's type is only the default. Corrected during implementation —
  first recorded as a web-only difference.) The web's file model `TapEntryModel`
  already has Swift's fields; the analyzer's `TapEntry` does not use them.
- *Decision (owner, 2026-09-25 — "it also aligns the behavior with swift — that is a good thing"):* full
  alignment — the web's `TapEntry` takes Swift's shape and behaviour (fields, construction, restore on load,
  `entry.resolvedModePeaks(guitarType?)` over the selected peaks), and `definitivePeak` becomes `getPeak`.
- *Found while planning:* the web already has a free `getPeak(peaks, mode, guitarType)` (`dsp/classify.ts`)
  whose comment claims to mirror Swift's `getPeak(for:)` but does not — it resolves over ALL peaks, override-
  blind. Its one production caller is `modePeaksFromSpectrum` (`dsp/guitarFFT.ts`), whose only callers are
  the two test uses item 1 replaces. And a peak's id: Swift's `ResonantPeak.id` is a `UUID`, Python's a UUID
  string, one type in memory and on file; the web alone keeps a numeric id in memory (unique only within one
  `findPeaks` call) and mints UUIDs at save (`fromLive.ts`), mapping back on load, with a separate file type.
- *Decisions (owner, 2026-09-25 — "We are cleaning up code by reviewing slugs. That is the whole point"):*
  the free `getPeak` and `modePeaksFromSpectrum` are removed (their unit tests move onto
  `resolvedModePeaks`); and the web's peak id becomes a UUID string, as Swift's is — in memory, in the
  selection, overrides and annotation offsets, and in `TapEntry.selectedPeakIDs`.
- *Done (web; Python: one docstring):* **ids** — `findPeaks` and the material store mint each peak's id with
  `newId()`; save writes a peak under its own id and load restores it under that id (the numeric↔UUID maps
  and the classification "adapters" in `fromLive`/`encode` are gone); every id-keyed map, set and chart type
  is `string`. **`TapEntry`** — a class in `measurement/types.ts` (Swift keeps it in its measurement model
  file) with `id`, `tapIndex`, `snapshot`, `peaks`, `selectedPeakIDs` and `resolvedModePeaks(guitarType?)`;
  `processMultipleTaps` builds it as Swift does (floor peaks, `guitarModeSelectedPeakIds`, a snapshot of the
  display settings and type at capture); save writes it as it is; load restores it (the re-find is gone).
  `definitivePeak` → `getPeak`; the free `getPeak` and `modePeaksFromSpectrum` are removed (their classify
  cases use `resolvedModePeaks`); `guitarTypeNameFromRaw` is one function (was a map in `fromLive` and a copy
  in `encode`). **Tests** — REG-G1/G2 and the self-baseline read `analyzer.getPeak` and
  `tapEntries[i].resolvedModePeaks()`; `playGuitar` returns the analyzer, sets the type to Generic and Peak
  Min as the natives do, and runs the peak recalculation App runs at completion; the web's PR17 is now the
  natives' case (a saved 777 Hz peak the snapshot cannot produce comes back on load); fixtures use string
  ids. **The self-regression passes at zero tolerance — no baseline value moved.** Full web suite 677/677;
  tsc clean. **Mutations — 9 of 10 caught:** `getPeak` ignoring selection, load or save minting fresh ids
  (guitar and material), load re-detecting or dropping the entries, save dropping the selection, capture
  selecting nothing, `resolvedModePeaks` ignoring the snapshot's type. **Survived:** `resolvedModePeaks`
  over ALL of a tap's peaks — at capture the selection IS the strongest per mode, so no case tells them
  apart. Uncommitted.
- *Found while implementing:* (a) the surviving mutation above; (b) Swift's `processMultipleTaps` finds the
  averaged peaks, auto-selects them, resets the selection state and sets "Analysis complete" itself — the
  web does that in `recalculatePeaks`, which App calls after completion (with an `analysisAnnounced` latch),
  so the harness has to make App's call; (c) Swift has one peak type, `ResonantPeak`, in memory and on file
  — the web still has two, `Peak` and `ResonantPeakModel` (timestamp and pitch fields); (d) Swift's
  `TapEntry.peaks` / `selectedPeakIDs` comments say they are recomputed when Peak Min changes — nothing
  does.
- *Decisions (owner, 2026-09-25):* all four. (a) a case in all three that tells the selected peaks from all
  peaks; (b) the web's completion does what Swift's does, in `processMultipleTaps`; (c) one peak type on the
  web, as Swift's; (d) fixed now, not left for item 7.
- *Found while planning (b):* Swift sets the peaks at the event, and only there — a live frame
  (`analyzeMagnitudes`), completion (`processMultipleTaps`), a load (`loadMeasurement`), Re-analyze
  (`reanalyzePeaks`, the ONLY caller of `recalculateFrozenPeaksIfNeeded`), a guitar-type change
  (`reclassifyForGuitarTypeChange` — re-classifies, never re-detects). The web recomputes from one App layout
  effect on any change of frozen spectrum, loaded peaks, live spectrum, guitar type or material: it re-detects
  on the frozen spectrum at completion (announcing through a latch) and on every guitar-type change (fresh ids,
  per-peak state carried by frequency).
- *Decision (owner, 2026-09-25):* the full event-driven version — the effect goes; the web sets the peaks at
  Swift's events, in Swift's methods.
- *Done (d):* Swift's comments say what happens — found once at capture, at the detection floor, never
  re-derived.
- *Done (a):* PR38 in all three (`FrozenPeakRecalculationTests` / `test_frozen_peak_recalculation` /
  `frozen-peak-recalc`): a tap whose selected Top is the weaker of two Top-band peaks resolves to that one.
  The surviving mutation (resolve over all of a tap's peaks) is now caught in all three.
- *Done (b), web:* App's recalculation effect is gone. `onFftFrame` → `analyzeMagnitudes` (wired from the
  engine's spectrum callback): live peaks at Peak Min, all selected, only while a sequence runs and never over
  a complete result; material frames leave no guitar peaks. `processMultipleTaps` finds the averaged peaks
  at the floor, auto-selects over the full set, resets the selection state and loaded peaks, classifies and
  announces "Analysis complete!" (the `analysisAnnounced` latch is gone). A load sets the saved peaks and
  classifies them (material and comparison loads clear them). `reanalyzePeaks` (App's Re-analyze calls it)
  drops the loaded peaks and manual selection and runs `recalculateFrozenPeaksIfNeeded` — Swift's name and
  guards, now reached only from there. `reclassifyForGuitarTypeChange` re-classifies (`reclassifyPeaks`)
  instead of the effect re-detecting. The settle clears the live peaks. `playGuitar` no longer makes App's
  call. The two status tests and PR12 now drive completion, Re-analyze and live frames.
- *Done (c), web:* one peak type, `ResonantPeak`, in `measurement/types.ts` (where the web mirrors Swift's
  model structs) — `Peak`, `ResonantPeakModel`, `MaterialPeak` and `DetectedMaterialPeak` are gone.
  `makeResonantPeak` gives a new peak its id and time, as Swift's init does; `findPeaks` and
  `findDominantPeak` fill the pitch fields (the analyzer has Swift's `pitchCalculator`), so a peak is saved
  and loaded as it is — the save-time pitch/timestamp stamping, the load-time field stripping,
  `identifyMaterialPeak`, the file-only `modeLabel` field (the writer derives the label; nothing read it)
  and the save's now-unused `modeByPeak` argument are removed.
- **Results:** web 677/677 + PR38, tsc clean, self-regression at zero tolerance unchanged; Python and Swift
  PR38 pass. **Mutations, second round — caught:** PR38's in all three; completion finding no peaks or not
  announcing; a live frame selecting nothing; a material frame keeping guitar peaks. **Survived:** a live
  frame overwriting a complete result; a type change not re-classifying; a load not setting the peaks; the
  settle keeping the peaks; Re-analyze keeping the loaded peaks; found peaks carrying no pitch. None of the
  six is pinned in Swift or Python either (the nearest Swift cases check a neighbouring fact).
- *Decision (owner, 2026-09-25):* a case for each, in all three.
- *Done (the six cases):* PR39 (a live frame never overwrites a complete result), PR40 (a load puts the saved
  peaks in place), PR41 (Re-analyze drops the loaded peaks and re-detects) in the frozen-peak-recalc suites;
  a Phase7 case (a guitar-type change re-classifies — 160 Hz is Top on Acoustic, not on Classical); F17 in
  find-peaks (a found peak carries its pitch: 440 Hz → A4); N8 now also checks that the settle clears the live
  peaks. The web's N7 gained the peak check Swift's and Python's N7 already make. **Mutations — all 18 caught**
  (each of the six, in each edition). Full suites: Swift 634, Python 750, web 683 — all pass; tsc clean;
  parity map regenerated (`guitarFFT.ts` leaves `audio/tap-analyzer` with the tag it no longer carries).
  Python's PR17 docstring names the web case it now mirrors.

**2. The assertions differ.** The natives assert completion in every case — the phase `.complete`,
`isMeasurementComplete`, the tap count or tap entries. The web asserts none of that for material (only how
many phases produced a spectrum), and for guitar only implicitly (`playGuitar` returns null if the
measurement did not complete). The web's material results come back as `MaterialCaptureResult`, a type
declared in the production engine file (`realtimeFFTAnalyzer.ts`) that nothing in the app uses.
- *Found while reading:* per case, the natives assert completion (`materialTapPhase == .complete`,
  `isMeasurementComplete`), REG-G1's captured-tap count, each material phase's peak LIST non-empty, and OUT-4's
  noise floor converged to −60…−40 dBFS; the web asserts none of those (its `noiseFloorEstimate` is private).
  `MaterialCaptureResult.phase`'s comment says the engine sets it — the harness does. `engine.playFile`'s
  `material` option now only sets the calibration (`brace`/`measureFlc` are unread) and its comment says the
  engine owns the material session and auto-advances — the analyzer has since F30.
- *Found while reading — architecture:* Swift keeps a full peak list per material phase (`longitudinalPeaks`,
  `crossPeaks`, `flcPeaks`, built by `buildAllPeaks`) beside the selected peak, and `allPeaks` holds it; the web
  keeps only the selected peak per phase (`matPeaks`). The natives' "peak list non-empty" has nothing to point
  at on the web.
- *Decision (owner, 2026-09-26):* the architectural divergence is fixed first — the web takes Swift's
  per-phase peak lists — together with the rest: `playMaterial` returns the analyzer and
  `MaterialCaptureResult` goes; the web asserts what the natives assert (completion, REG-G1's tap count,
  OUT-4's noise floor — `noiseFloorEstimate` readable); `playFile`'s `material` option folds into
  `calibration` and the stale comments are corrected.
- *Corrected on tracing (2026-09-26 — the owner challenged "more peaks show"):* Swift's full per-phase lists
  are never shown or saved. `allPeaks` holds a full list only between a phase's capture and its Accept
  (`reviewing…`); at completion `finalisePlateNoFLC` / `finalisePlateWithFLC` set it to the 1–3 identified
  peaks (`resolvedPlatePeaks`) and brace to `[selPeak]`, so the save writes 1–3 peaks — as the web does. The
  chart draws `materialIdentifiedPeaks` (the 1–3 selected) and annotates the same (`visiblePeaks`); the
  results panel shows the slot rows until complete, then `allPeaks` (1–3). Every other use — the PDF, the
  results-view property calc, the chart-widening subscription — is a lookup of the identified peak by id,
  which `selected…Peak` already holds (the web's `matPeaks`). So the web's material behaviour and file
  content match Swift's; the difference is state Swift carries that nothing displays: the three lists, the
  `autoSelected…PeakID`s, `buildAllPeaks`, `combinePlatePeaks`, the full `allPeaks` during review, and live
  material frame peaks (`analyzeMagnitudes`' median-threshold path — the chart never draws them). Swift's
  comments ("for display/manual override", "so the user can see and manually select any peak") describe a
  manual selection that does not exist. Python mirrors all of it. The decision above rested on the wrong
  reading and is reopened.
- *History (Swift git):* `c0db6ea` (16 Feb) — `longitudinalPeaks` = `findPeaks` on the phase, strongest = fL,
  the chart showed the list. `7032314` (26 Feb) — `buildAllPeaks` "so the user can see and manually select any
  peak"; the panel listed every phase peak with fL/fC/fLC buttons (`selectLongitudinalPeak` …) to reassign.
  `c88e5e1` (17 Apr) — the reassign buttons removed; badges display-only, Redo is the remedy. `0b5089a`
  (18 Jul, 1.0.2) — no per-peak selection for material; chart and annotations draw the identified peaks; the
  save writes the identified set. The lists outlived both changes. The web was written after 1.0.2.
- *Decision (owner, 2026-09-26):* remove the unused per-phase peak sets from Swift and Python; the end state is
  one consistent material-peak architecture across Swift, Python and the web. The other recommendations
  above stand.
- *Found while planning:* the natives hold a finished material measurement's identified peaks twice — the
  three `selected…Peak`s, and a copy in `allPeaks` / `selectedPeakIDs` that `resolvedPlatePeaks` re-sets at
  each phase end and at completion. The copy is not Redo's (Redo never touches `allPeaks`, which keeps the
  rejected peak until the next phase end); it is left from the first version, where each phase wrote into the
  guitar peak channel (`currentPeaks`), and the generic readers still read it for material — the save
  (`allPeaks`, with `selectedPeakIDs` derived), the load (`allPeaks = measurement.peaks`, then `selected…Peak`
  by id), the finished results panel (`peaksAbovePeakMin`), the PDF / property lookup. The chart and
  annotations moved to `materialIdentifiedPeaks` in 1.0.2; these did not. The web holds them once
  (`matPeaks`; `peaks` empty for material).
- *Decision (owner, 2026-09-26) — option B, one source:* in all three the three selected peaks are the only
  material peak state; `allPeaks` / `selectedPeakIDs` are guitar-only; the save, load, results panel, chart
  and PDF read the identified peaks (Swift `materialIdentifiedPeaks`); the natives lose the copy and its
  re-sync; the web takes Swift's names (`selectedLongitudinalPeak` / `selectedCrossPeak` / `selectedFlcPeak`)
  for `matPeaks`. In all three: the per-phase lists, `buildAllPeaks`, `combinePlatePeaks`, the
  `autoSelected…PeakID`s, the material live-frame peak finding and the "manually select" comments go.
- *Found while planning:* the natives' material live-frame peaks are never drawn (owner confirmed on screen:
  only fL/fC/fLC ever show). Their one effect is the results panel's switch — slot rows when `allPeaks` is
  non-empty, otherwise an inline process block (plate) or "No peaks detected in visible range" (brace) —
  reachable only before the first frame. *Decision (owner, 2026-09-26):* no effect that matters; material
  shows the slot rows until complete, as the web does.
- *Found while implementing (Swift):* the natives' material `peaksAbovePeakMin` also gates the Annotations
  button (six sites, one per layout — enabled during a material capture by the live peaks) and fills the PDF
  peak table (both export paths). The web gates Annotations on the identified peaks (`materialMarkers`) and
  its PDF reads the identified peaks; Save is enabled only when complete in all three.
- *Decision (owner, 2026-09-26):* the same mechanism in all three, nothing edition-only — Annotations is
  enabled when `peaksAbovePeakMin` (guitar) / `materialIdentifiedPeaks` (material) is non-empty; the PDF
  peak table reads the same; the web gains `materialIdentifiedPeaks` over the three `selected…Peak`s. In Swift
  and Python, Annotations is then disabled during a material capture until fL is identified, as on the web.
- *Found while implementing:* the web's Redo never cleared the redone phase's spectrum or identified peak
  (Swift and Python do), so the old fL stayed in the slot row, chart and annotations while re-tapping;
  Python's Redo cleared the peak but never told the view, so its dot and label stayed until the next event.
  Both aligned to Swift here (the same material peak state). Python never gated Annotations on peaks at all
  (only "not comparing") — now the agreed rule.
- *Done (all three):* **Swift** — the per-phase lists, `autoSelected…PeakID`s, `buildAllPeaks`,
  `resolvedPlatePeaks`, `combinePlatePeaks` and the material live-frame branch of `analyzeMagnitudes` are gone;
  each phase end sets its `selected…Peak` and nothing else; the finalisers, Redo and the phase reset no longer
  touch `allPeaks` / `selectedPeakIDs`; the save writes `materialIdentifiedPeaks` for material (all marked
  selected); the load keeps `allPeaks`, `selectedPeakIDs` and `loadedMeasurementPeaks` guitar-only and restores
  the three peaks by id from the file; the results panel shows the slot rows until complete, then the
  identified peaks (the inline plate process block and the brace "No peaks detected" line are gone); the plate
  and brace property calcs, both PDF paths (peak table and selection) and the six Annotations gates read the
  identified peaks; the chart widening subscribes to `selected…Peak` (so it also runs on a load, as the web's
  does); stale comments (the model header's "two-layer selection", `peakProximityHz`, `analyzeMagnitudes`,
  `recalculateFrozenPeaksIfNeeded` "called from the Peak Min didSet") corrected. **Python** — the same, plus
  Redo emits so the view drops the redone peak, the view emits that also fire for material (zoom, Peak Min,
  leaving comparison) carry the identified peaks, a load emits `materialPeakIdentified` for each restored peak,
  and Annotations is gated. **Web** — `matPeaks` → Swift's three `selected…Peak`s and `materialIdentifiedPeaks`
  (analyzer, snapshot, material restore); Redo clears the phase's spectrum and peak; the Annotations gate is the
  same rule (comparison, or no guitar projection / identified peaks — the `!running` term is gone); the chart
  widening reads `materialIdentifiedPeaks`; `playFile`'s `material` option is gone (one `calibration` option; App
  makes one call); `MaterialCaptureResult` is removed; `noiseFloorEstimate` is readable. **Tests** — the natives'
  "peak list non-empty" became "the fL/fC/fLC peak is identified"; REG-B1 and the Swift minter read the
  selected peak (no value moved — REG-B1 passes at zero tolerance); PR32 (Swift, Python) saves what the save now
  writes; Python's effective-id twin drops the auto ids; the web's `playMaterial` / `playGuitar` return the
  analyzer and REG-G1/G2, REG-B1/B2, REG-P1/P2 and OUT-4 assert what the natives assert (completion, the phase,
  REG-G1's one captured tap, OUT-4's noise floor converged to −60…−40 dBFS). Full suites: Swift 634, Python 750,
  web 683 — all pass; the web self-regression passes at zero tolerance.
- *Mutations, first round (stopped early by owner decision — the answer was already clear):* every model
  mutation survived in Swift (save writes `allPeaks` for material; load finds fL in `allPeaks`; material live
  frames set peaks; a material load fills `allPeaks`; Redo keeps fL) and in Python (the same five) — the new
  material peak model was pinned nowhere. *Decision (owner, 2026-09-26):* cases for them in all three.
- *Done (cases):* PR42 (saving a material measurement writes its identified peaks, all selected), PR43 (loading
  one restores the identified peaks by id and leaves the guitar peak state empty), PR44 (a material live frame
  leaves no peaks — the web's existing "material mode yields no guitar peaks" case, renamed as the twin), PR45
  (Redo clears the phase's identified peak and spectrum; Python also checks the view is told) — beside PR32 in
  the frozen-peak-recalc suites. A shared capture helper per edition drives the real gated path; PR45 taps at
  60 Hz, inside the plate fL band the web's route applies.
- *Mutations, second round:* Swift 5/5 and Python 6/6 caught (Python's sixth: Redo not telling the view).
  Web: Redo keeping fL caught; `materialIdentifiedPeaks` without its guitar guard survived — an equivalent
  mutant (the three material peaks are always null in guitar mode; the paradigm switch resets them), and the
  natives' guards are the same; a load dropping fC survived — PR43 was a brace, which has no fC.
  *Decision (owner, 2026-09-26):* PR43 becomes a plate. *Done:* PR43 captures fL (60 Hz), Accepts, captures
  fC (150 Hz), Accepts (no FLC — complete, as Save requires), saves, reloads, and checks both roles by id, in
  all three. A load dropping fC is now caught in all three (web, and the matching Swift and Python mutations).
- *Results:* full suites Swift 638, Python 754, web 686 — all pass; the web self-regression passes at zero
  tolerance; parity map regenerated. The view-level changes (the material results panel, the Annotations gate,
  the live material PDF, the chart widening on a material load, Redo clearing fL on the web and in Python) are
  for the run-review. Uncommitted.
- *Found while writing PR43:* Swift's and Python's `saveMeasurement` do not read the analyzer's own identified
  peaks for the file's `selectedLongitudinalPeakID` / `…Cross…` / `…Flc…` — they take them as parameters
  (default nil) that the view passes (`tap.effectiveLongitudinalPeakID` …); a model save called without them
  writes no roles. The web's save is built in App from the analyzer's peaks. Raised, not changed.

**3. The case lists differ.** REG-G2 is one case in the natives (averaged and per-tap), two on the web. The
REG-G ring-out case is here in the natives but in `decay-tracking.test.ts` on the web. The web's three
session-WAV cases (6f — one WAV labelled `Guitar_1tap` / `Guitar_8tap`, none when the diagnostic is off)
have no native counterpart anywhere.
- *Found while reading:* the web's first REG-G2 case alone asserts completion; `parityRunner.ts` plays the
  ring-out a second time for the baseline mint (`ringOutSec`); Python's ring-out case is a module-level function
  beside a class of methods; the natives' session-pre-roll suites test the recording buffer's bounds, not the
  WAV emitted or its label; and the three editions order the cases differently (Swift: B2, B1, G1, ring-out, G2,
  P1, OUT-4, P2).
- *Decision (owner, 2026-09-26):* merge the web's REG-G2 into one case; move the web's ring-out case into
  file-playback and share one playback with the baseline mint; Python's ring-out goes into the class; the
  three session-WAV cases get native twins; the cases take Swift's order in all three.
- *Found while planning the twins:* the natives' WAV dump folder is not sandboxed under tests — Swift's
  `WavDumpFolder` resolves the user's custom folder (a bookmark in `UserDefaults.standard`) or the app's
  `Documents/GuitarTap`, so a native case with dump on would write session WAVs into the owner's real folder.
  The measurements file already has a test sandbox (`measurementsFileURL` → a per-process temp path when
  `TestSandbox.isActive`). *Decision (owner, 2026-09-26):* sandbox the dump folder the same way in both natives;
  the twins read back what lands there.
- *Done (all three):* **web** — the two REG-G2 cases are one (averaged and per-tap, completion asserted);
  the ring-out case moved from `decay-tracking.test.ts` into file-playback (the REG-G1 playback via
  `playGuitar`), and the baseline mint reads the ring-out off the same REG-G1 playback — `ringOutSec`, its
  second playback, is gone (the zero-tolerance self-regression is unchanged); every case is in one group in
  Swift's order (B2, B1, G1, ring-out, G2, P1, OUT-4, P2), then the three session-WAV cases.
  **Python** — the ring-out case is a method of the class (its constants beside the G1 ones); the cases take
  Swift's order; the three session-WAV twins added. **Swift** — the three session-WAV twins added after P2.
  **Both natives** — `WavDumpFolder`'s default folder is a per-process temp folder under test and a custom
  folder is ignored there (Swift `hasCustomFolder` false under `TestSandbox`; Python via `sandbox_id`),
  so no test writes into the owner's folder (checked: nothing new in `~/Documents` or the app container).
  The twins turn "save capture audio" on (or off), play REG-G1 / REG-G2, and read the session WAVs back from
  the sandbox folder: one `Guitar_1tap` at the file's rate, more than 8192 samples and no more than the file;
  one `Guitar_8tap`; none with the setting off. **Mutations — all four caught:** the session label ignoring
  the tap count, and the dump not gated by the setting, in Swift and in Python.
  Full suites: Swift 641, Python 757, web 685 (the merge and the move leave the web one case fewer) — all
  pass; the web self-regression passes at zero tolerance; parity map regenerated. Uncommitted.

**4. Tolerance use differs.** Swift asserts at zero (it mints the oracle); Python and the web at the
cross-edition tolerances; Swift compares with `≤`, Python and the web with `<`. The tolerances themselves
are #16's; noted only.
- *Found while reading:* the bars differ by design — Swift's playback cases ask "does Swift reproduce
  itself" (`selfTolerances`, all zero, exact equality, so `≤`); Python's and the web's ask "do they agree with
  Swift" (the cross-edition `tolerances`), their own zero-bar check being the self-regression (the oracle's
  `_selfToleranceNote`). The differences: `<` vs `≤`; a dead per-case override — Python's `tol("REG-P2",
  "magDb")` and the web's `reg.tolerances?.magDb ?? TOL.magDb` exist for a REG-P2 bar the oracle no longer
  declares (both fall back to the global), and Swift keeps a `plate3TapMagTolerance` equal to `magTolerance`;
  and comments describing the old bars ("same ±1 tolerances", "±0.5 dB … the single-tap cases allow 1.0",
  "tighter than the generic ±1.0 dB", "0.0853 s ± 0.03 s … Python ~0.091").
- *Decisions (owner, 2026-09-26):* `≤` in all three (Swift's); the per-case override path and the extra
  constants removed — the global bar; the tolerance comments corrected here, with the code they describe.
- *Done (tests only):* Python's and the web's playback comparisons are `≤` (37 in Python, 18 on the web);
  Python's `tol()` (in `parity_oracle.py`) and `PLATE_3TAP_MAG_TOLERANCE`, the web's `P2_MAG_TOL` and Swift's
  `plate3TapMagTolerance` are gone — REG-P2 uses the global magnitude bar like every case; the comments now
  say what each edition's bar is (Swift: zero, it mints the oracle; Python/web: cross-edition, with their own
  zero-bar self-regression) and the ring-out notes say it is measured on the audio clock with the oracle's
  value; the "± 1" case docs say "match the oracle". No production code changes, so no mutation round.
  Swift and web playback suites pass (11 each); Python's full suite 757. Uncommitted.

**5. The playback harness sits in production code in the natives.** Swift's `playFileForTesting` and
Python's `play_file_for_testing` are methods on the analyzer; the web's harness is in the test
(`playGuitar` / `playMaterial` / `waitForCompletion` in `parityRunner.ts`), driving the real
`engine.playFile`.
- *Found while reading:* the natives' harnesses do not call the app's file path — they re-implement it. The
  app's path is sequenced by the view (`openAudioFile` / `_open_audio_file`: the calibration, `startTapSequence`
  with the warm-up rule, then `fft.startFromFile`); the harness repeats the first two, sets `mpmSampleRate` by
  hand and calls `prepareForFilePlayback` / `processFileData` directly, skipping `startFromFile`'s engine stop,
  drain and `postEngineStopHandler`. Every playback regression runs a parallel, hand-maintained path. Its
  `plateTapPhase` parameter has no caller. The web's harness drives the app's `engine.playFile`, but repeats
  App's arming steps. "Play a file" is sequenced by the view in all three — the F41 / F53 shape.
- *Feasibility (checked):* Swift's `startFromFile` restarts the mic when playback ends (`try? self.start()`),
  and `start()` does not check `isForTesting` — the one headless fix needed; Python's `start_from_file`
  already tolerates no stream (its stream stop/start are guarded) and plays on a worker thread as in the app.
- *Decision (owner, 2026-09-26 — option 2):* an analyzer "play a file" method in all three doing what the view
  does (the file's calibration for the playback, arming with the warm-up rule, starting the file, restoring
  the calibration at the end); the views and the tests call it; `playFileForTesting` / `play_file_for_testing`
  and `plateTapPhase` are deleted; Swift's post-playback mic restart skips the hardware under test. If a
  regression value moves, stop and show the owner.
- *Progress (2026-09-26):* Swift and Python done — `playFile(url:calibrationURL:completion:)` /
  `play_file(path, calibration_path, on_finished)` on the analyzer; the views call it; the harnesses are
  deleted; the tests call `playFileAndWait` / `play_file_and_wait` (`PlaybackTestSupport.swift`,
  `tests/playback_support.py`), which set the type and tap count, call the real method and wait. Python's
  mic restart skips the hardware under test as Swift's does, and its main-thread event pump in
  `process_file_data` (only the harness ran it on the main thread) is removed. FilePlaybackRegression 11/11 in
  both, at zero tolerance — no value moved. Python's view no longer shows a dialog for an unreadable
  calibration file; the model logs it, as Swift does.
- *Found doing the web (raised 2026-09-26):* (a) the calibration is applied inside the engine's `playFile`, not
  by the analyzer, and with no calibration file the web plays UNCALIBRATED (`{ calibration: null }` clears the
  mic's calibration for the playback) where Swift and Python keep the mic's active calibration. (b)
  `startTapSequence`'s `initialPhase` (all three) was only there for the deleted harness's `plateTapPhase`; no
  caller passes anything but the default. Its comments say "phase-targeted file-playback tests". The web's
  `arm: false` doc says it is "for file playback" — it is now used only by tests without a device.
- *Decision (owner, 2026-09-26 — (a)):* a played file uses the calibration the user gives for it, or none. The
  microphone that recorded the file is unknown, so the live input's calibration never applies. The web was
  right; Swift and Python were wrong. (b) (owner, 2026-09-26): delete `initialPhase` in all three.
- *Done (a) and the web's part:* in all three the analyzer's play-file method sets the playback's calibration —
  the file's, or none (an unparsable file is logged and plays uncalibrated) — and restores the input's when
  playback ends. Web: `TapToneAnalyzer.playFile(samples, rate, calibration)` arms and plays as Swift's does;
  App and the tests (`playGuitar`, `playMaterial`, the session-WAV helper) call it; the engine's `playFile`
  loses its `calibration` option, and App's redundant `clearResult` goes (`startTapSequence` clears). New twin
  cases in all three: with no calibration file the playback is uncalibrated and the input's calibration
  returns; with one, it is used and the input's returns. Mutation (skip the override when no file is given)
  fails the first case in all three. Swift 13/13 and Python 13/13 playback cases (11 + 2), web 13/13; no
  regression value moved.
- *Done (b):* `startTapSequence`'s `initialPhase` / `initial_phase` deleted in all three; a material sequence
  starts at its first phase. Swift's one test caller passed the default and now passes nothing. The web's
  `arm: false` doc now says it is for tests without a device (the natives have no such parameter). Full suites:
  Swift 643, Python 759, web 687 — all pass; tsc and eslint clean.

**6. Swift prints plate diagnostics on every plate run.** `printPlateDiagnostics` (REG-P1, REG-P2) prints the
analyzer's state and the tail of the debug log it reads from `~/Documents/GuitarTap`. No other edition does.
- *Found (checked with a REG-P1 run, 2026-09-26):* the test host is the sandboxed app, so the log it reads is
  the app container's real field log (`~/Library/Containers/com.dolcesfogato.GuitarTap/Data/Documents/
  GuitarTap/GuitarTap-debug.log`, 3.2 MB). Under test the logger writes nothing (the XCTest guard in
  `Logging.swift`), so the tail is always the owner's last app session — 466 lines of it in that run — never
  the test's. The detection trace (`TAP_DEBUG`) is off anyway. The state block prints on pass and fail alike;
  on a failure the assertions already give expected and actual. Nearby stale comments: the REG-B1 doc comment
  sits above REG-B2's test; REG-P2's says its expected values are "the WEB capture's" (the oracle's, minted
  by Swift); the helper's speaks of comparing "P1, P2, and P3" (no P3).
- *Decision (owner, 2026-09-26 — option 1):* delete the helper and its two calls; clean up the stale comments.
- *Done:* `printPlateDiagnostics` and its REG-P1/REG-P2 calls deleted (Swift `FilePlaybackRegressionTests.swift`).
  REG-B1's comment moved to REG-B1; REG-B2 given its own; REG-P2's file-level and doc comments now say the
  recording is the web app's and the values the oracle's; the `MARK: - Tests (REG-B1)` label corrected.
  FilePlaybackRegression 13/13; no diagnostic output.

**7. Stale explanations.**
- OUT-4, in all three: "Swift/Python detect … against an EMA-tracked noise floor; the web port uses a fixed
  absolute dBFS threshold", and the web "saturates … captures nothing". The web has had relative detection
  since OUT-4, and its own OUT-4 case asserts all three phases captured. The analysis link,
  `GuitarTapWeb/Development/OUT-4-DETECTION-SPEC.md`, is pre-migration (now hub
  `docs/completed/OUT-4-DETECTION-SPEC.md`).
- The ring-out (Swift, Python): "wall-clock decay … at real-time pace" and "0.0853 s ± 0.03 s" — the ring-out
  runs on the audio clock, and the tolerance comes from the oracle.
- Python's REG-B1 and REG-P1 blocks quote literal expected values and "±1.0 Hz, ±1.0 dB, ±1.0 Q".
- The web header: "same ±1 tolerances", and the warm-up called wall-clock-dependent (audio clock since #19).
- Swift's header lists "Hann window" for the whole pipeline (the guitar capture is rectangular — F49); its
  REG-B1 doc comment sits above the REG-B2 test (done in item 6).
- *Checked against the code (2026-09-26):* the ring-out text is already right in all three (fixed in items 3–4);
  the "±1" wording is gone. Still stale:
  - (a) OUT-4, all three: "the web port uses a fixed absolute dBFS threshold"; Swift's "(The web's counterpart
    test asserts exactly that failure.)" and Python's "the web port does exactly that — this is its failing
    counterpart test" — the web's case asserts all three phases captured. The analysis link is
    `GuitarTapWeb/Development/…` (Swift, Python, web header) or `Development/…` (web) — that folder is gone;
    the doc is hub `docs/completed/OUT-4-DETECTION-SPEC.md`.
  - (b) Headers, Swift and Python: "Hann window" for the whole chain; "Unlike FilePlaybackPipelineTests
    (FP1–FP5)" / "test_file_playback.py (FP1–FP15)" — neither file exists in any edition; "Expected values were
    established by running the file through the app … Both Swift and Python … use the same … values" — the
    values are the oracle's, minted by Swift and read by all three; the coverage list names six cases and
    omits the ring-out, OUT-4, session-recording and playback-calibration cases.
  - (c) Python's REG-B1 and REG-P1 blocks quote reference values from the `.guitartap` files; REG-P1's fC
    (116.27016 Hz, −52.80130 dB) is not the oracle's (116.27019, −52.800247).
  - (d) Python's REG-P2 block: "Expected values are the averaged-spectrum peaks (the web .guitartap …)" and the
    history of the last-tap bug — the Swift twin was corrected in item 6.
  - (e) Web header: the warm-up called "wall-clock-dependent" (audio clock since #19).
- *Decision (owner, 2026-09-26):* correct (a), (b), (d), (e) in place, (b) and (d) matching Swift's wording;
  for (c) remove the quoted numbers and keep the pointer to the source `.guitartap`.
- *Done:* (a) the OUT-4 blocks in all three say all three editions detect against the noise floor; the claims
  about the web's case are gone; the analysis link is hub `docs/completed/OUT-4-DETECTION-SPEC.md`. (b) The
  Swift and Python headers give the chain with its two windows, say the values are the oracle's, and list
  every case; the FP references are gone. (c) Python's REG-B1 and REG-P1 blocks name their source file only.
  (d) Python's and the web's REG-P2 comments say the values are the oracle's. (e) The web header no longer
  calls the warm-up wall-clock-dependent. The same "reference values from the .guitartap" wording on REG-G1,
  REG-G2 and REG-P1 (Swift, Python) now says the oracle's values came from it. Playback suites 13/13 in all
  three; tsc and eslint clean.
- *Noticed (raised 2026-09-26):* 28 more pre-migration `Development/` / `Completed/` doc links across the three
  editions' other files (Swift tests 5, Python tests 8, web src 8, web tests 7).
- *Decision (owner, 2026-09-26):* the application code must not link to `Development/` or `Completed/` — remove
  the references.
- *Done:* all 28 removed, each sentence reworded to stand without the link (e.g. "D3 + D5 + D6 of …" → "The
  duplicate-peak defect: fixture regressions."); the hub `docs/completed/OUT-4-DETECTION-SPEC.md` links this
  item had just added went too. None remain in any edition. Full suites: Swift 643, Python 759, web 687; tsc
  and eslint clean.
- *Noticed (raised 2026-09-26):* bare doc-name references with no folder ("See OUT-4-DETECTION-SPEC.md", "See
  SLUG-SWEEP.md F13") remain — about 97 across the three editions' code and tests (Swift app 13, Swift tests 10,
  Python src 18, Python tests 17, web src 23, web tests 16), not counting the shipped `Documentation/` files.
- *Decision (owner, 2026-09-26):* application code must not reference project documents — remove them too.
- *Done:* all 95 removed (the count of 97 included two hits that were not references). "See SLUG-SWEEP.md
  Fnn." phrases dropped; the others reworded so the comment stands alone — the silent-input incidents are
  named by date instead of by their hub doc; Python's device-management header lost its "Recommendations from
  docs/DEVICE_MANAGEMENT_REFACTORING.md" tracker (Rec 1–4, three DONE, one "PENDING" that is done). Kept:
  the user manual (`Documentation/Manual/…`) and the other shipped `Documentation/` files, the release-notes
  file the release guard reads, and "the canonical file in the hub" in the oracle-sync tests (a data file).
  Full suites: Swift 643, Python 759, web 687; tsc and eslint clean.
- *Decision (owner, 2026-09-26):* issue and finding references go too — "The documentation should NOT be in
  the code - it should be in the project documents" — and a comment says what the code does: "not what it did
  - not why it changed - but what it does."
- *Done (2026-09-26/27):* in all three editions every comment carrying an issue or finding reference (`#17 F52`,
  `(#19)`, `issue #8`, `guitar-tap-project#10`) was rewritten to say what the code does, or deleted where
  nothing present-tense remained — about 600 lines. A second pass did the same for finding and project labels
  without a `#` ("Phase N" of the peak-lifecycle work, `WI-n`, `6-TEST 3c-…`, `EG-n`, `PC-n`, `RA`/`RB`/`RC`,
  `RESPIN-1.0.2, fix M/R`, "run-review", commit hashes, "project memory" pointers) and for the history
  comments the first pass listed. `FILE-PATHS-AND-NAMES-SPEC §n`, `WEB-UI-GUIDELINES item 6` and bare `§n`
  section numbers were removed. Kept: test-plan case IDs shared across the editions (F1–F17, A1–A5, PR*,
  REG-*, D*, DL*, B*, IP-*, OUT-4 — `OUT-5` was removed in all three so the editions agree), mirror notes,
  `@parity` tags, book citations (Gore & Gilet, Blevins), the shipped user manual and `Documentation/` files,
  colour codes and note names. Also fixed along the way: Swift `resetToAutoSelection`'s doc comment sat on
  the function above it (moved); Swift AnnotationStateTests' unclassified-peak comment sat on the wrong test
  (moved); the web's unused `prevTaps` in `setConfig` deleted; Python's `test_status_message` module docstring
  no longer contradicts what it pins; an orphaned Swift FrozenPeakRecalculationTests comment under its old id
  PR4b ("the custom mode name on a peak hidden by Peak Min SURVIVES") was deleted — that behaviour is PR24,
  tested in all three (Swift `PR24_loadedPath_overrideForFilteredOutPeak_survives`, Python `test_PR13_…`,
  web `PR13/PR21/PR24`). Full suites: Swift 643, Python 759, web 687; tsc and eslint clean. The passes covered
  every comment that carried a reference, a label or a doc name.
- *Decision (owner, 2026-09-27):* no full sweep for the remaining unreferenced history comments — low payback.
  The rule applies to every comment written or edited from now on.

**8. Carried in.** The playback controls (F50's run-review): during a file playback New Tap, Pause/Resume
and Cancel do nothing in all three — the owner's options (1) disable them, (2) make them control the
playback. From #19's noticed list: timers scheduled in one playback case fire during the next, and the
Python minter sets up no settings sandbox.
- *Found (2026-09-27):* Pause does nothing during a playback because a recording delivers taps back to back:
  after each tap the detector is idle (rest, capture, re-arm), Pause acts only while it is listening — so the
  button is mostly disabled and a press in the gaps is a no-op, and the next re-arm carries on. A Python probe
  (pause after tap 1 of REG-G2's 8-tap file) counted all eight taps. No edition can stop or pause a playback.
  Changing the measurement type does not stop one either: Apply only re-arms a sequence (`requestStartTapSequence`),
  the file plays on into the new measurement, and the chart keeps the file's title until it ends.
- *Decision (owner, 2026-09-27 — option 2):* during a playback Cancel is enabled and stops the file — the partial
  result is discarded and the app returns to live input; Pause/Resume are disabled ("make little sense during a
  playback"); New Tap is disabled.
- *Decision (owner, 2026-09-27):* a measurement-type change during a playback stops the file first, then arms
  the new measurement.
- *Done (playback controls):* the button rule takes whether a file is playing; while one plays, Cancel is
  enabled and Pause/New Tap are disabled (B14–B16 in all three). Each engine gains "stop the file"
  (Swift/Python `stopFilePlayback` / `stop_file_playback`, web `stopFilePlayback`): the generation token
  ends the pump, nothing of the rest of the file is processed and no capture is flushed, the mic returns,
  and the playback's completion runs (the input's calibration returns). Cancel stops the file, then
  restarts on live input; a measurement-type change stops it before arming. Python moved from its flag +
  thread-identity supersession to Swift's generation token (needed to stop without flushing). Python has
  no `requestStartTapSequence`, so its stop sits in `FftCanvas.restart_tap_sequence` (New Tap and the
  type change both re-arm there); the web gained `requestStartTapSequence`, App's Cancel now calls the
  analyzer's `cancelTapSequence`, and the snapshot carries `isPlayingFile`. Tests: Cancel and a type
  change mid-playback in all three; mutation (the stop removed) fails both in all three. Full suites:
  Swift 648, Python 764, web 692.
- *Noticed:* Play File stays enabled during a playback in all three; opening a second file replaces the
  first without running the first's completion (unchanged). In Python a Cancel in the last milliseconds of
  a file can still let that file's final capture through (its flush runs on the worker, not the main
  thread as in Swift) — a window of one chunk.
- *Found (carry-in: Python minter):* `Tooling/mint-baseline.py` sets no settings sandbox — a standalone
  mint reads the user's real Python settings and, since item 5, writes to them: `play_file_and_wait` sets
  the measurement type and tap count and does not restore them. Swift mints in its test target
  (sandboxed); the web has no persisted settings under Node.
- *Found (carry-in: timers across cases):* the lifecycle timers run on the audio clock and end with their
  playback. What remains on the wall clock is the gated capture's stall check (all three) and, in Python,
  the queued file-end release; a check can fire once into the next test case. Each re-checks that its
  capture is still relevant and acts only on its own (previous) analyzer, so it cannot change a result.
- *Found (2026-09-27):* the architectural difference behind both: Swift runs the end-of-file step — flush the
  unfinished capture, finish it, release the pending audio actions — as ONE synchronous step on the main
  thread (the worker waits in `DispatchQueue.main.sync`), guarded by the generation; the web does the same
  on its one thread. Python runs the flush on the playback worker, finishes the capture through a queued
  signal and releases through a second queued main-thread call. That queued release is the callback that
  can outlive a test case, and the flush on the worker is what leaves Python's one-chunk Cancel window.
- *Decision (owner, 2026-09-27):* fix the minter (sandbox it); align Python's end-of-file step with Swift's.
- *Done:* `Tooling/mint-baseline.py` claims the per-process settings sandbox (`GT_TEST_SANDBOX`) before
  anything imports settings, as `tests/conftest.py` does. Checked: a standalone `--check` run with no sandbox
  variable set left the real `com.dolcesfogato.guitar_tap` settings unchanged (94 values, identical to the
  baseline). Python's end-of-file step: the worker hands one step to the main thread and waits
  (`runOnMainBlocking`, a BlockingQueuedConnection — Swift's `main.sync`); it checks the generation, flushes
  the unfinished capture, finishes it directly (`finish_gated_fft_capture`, as Swift calls
  `finishGatedFFTCapture`) and releases the pending actions (Swift's `defer`). The queued release is gone,
  and the one-chunk Cancel window is closed. The mic restart and the finished callback run on the main
  thread too (`runOnMain` — Swift's `main.async`). New Python test: the end-of-file step runs on the main
  thread (mutation — the step run on the worker — fails it). Playback suite 16/16 at zero tolerance; full
  Python suite 765. The gated capture's wall-clock stall check stays, as in Swift and the web.
- *Noticed:* `~/Library/Preferences` holds ~35 leftover `com.dolcesfogato-tests-<name><n>` settings files
  from earlier ad-hoc runs with named sandboxes (`g2alone`, `repeat`, `leak`, `busy`, `speed`, `probe`,
  `mintcheck`, …); the conftest reaper removes only numeric-pid ones. *Owner (2026-09-27): clean them* —
  all 35 deleted; the real settings files are untouched.

**9. The web never names the file being played** (found at the web run-review, step 2, owner, 2026-09-27).
Swift and Python title the chart `playingFileName ?? loadedMeasurementName ?? "New"`: the file's name is set
when it starts, kept after it ends, and cleared by a new sequence, Stop or stopping the playback; Play File is
tinted orange while a file plays. The web titled it `loadedName ?? 'New'`, its engine was never given the
file's name, and Play File had no playing state — a divergence older than this slug.
- *Decision (owner, 2026-09-27):* fix it now.
- *Done (web):* the engine holds `playingFileName` (Swift's name): `playFile` takes it, keeps it after the file
  ends, and `stopFilePlayback` clears it; `analyzer.playFile` passes the file's name (without its extension,
  as Swift) and `startTapSequence` clears it, as Swift's does; the snapshot carries it. App's chart title and
  the live PDF's use `playingFileName ?? loadedName ?? 'New'`, and Play File is tinted orange while
  `isPlayingFile`. Tests: a played file is named while it plays and after it ends, a new sequence clears it,
  and Cancel mid-playback clears it; mutation (neither clears it) fails both. Web suite 697; tsc and eslint
  clean.

**F53 — the save takes state the model already owns from the view, and the web's save is built in the
view. (CLOSED — all 6 items done and run-reviewed in all three. Commits: Swift `835b39c`, Python `4980c01`, web `170f8eb`)**

Found writing F52's PR43. Files: Swift `TapToneAnalyzer+MeasurementManagement.swift` (`saveMeasurement`) and
`TapToneAnalysisView+Actions.swift` (its caller) / Python `tap_tone_analyzer_measurement_management.py`
(`save_measurement`) and `tap_tone_analysis_view.py` (its caller) / web `App.tsx` (the save handler) and
`measurement/fromLive.ts` (`buildGuitarMeasurement` / `buildMaterialMeasurement`).

| # | item | status |
|---|---|---|
| 1 | The natives' save takes the identified material peak ids from the view | ✅ done (all three) |
| 2 | The natives' save takes other model-owned state from the view | ✅ done (all three) |
| 3 | The web's save is built in App, not by the analyzer | ✅ done (all three) |
| 4 | Two save parameters no caller uses; the save's docs are misplaced or wrong | ✅ done (all three) |
| 5 | A measurement made from a played file records the live input's provenance | ✅ done (all three) |
| 6 | The Results panel, a re-save and the live PDF show the live input for a loaded measurement | ✅ done (all three) |

**1. The natives' save takes the identified material peak ids from the view.** `saveMeasurement` (Python
`save_measurement`) writes the file's `selectedLongitudinalPeakID` / `…Cross…` / `…Flc…` from parameters that
default to nil; the view passes `tap.effectiveLongitudinalPeakID` and its siblings — the model's own state,
read back and handed in. A save called without them writes no roles (PR43 did, until it passed them). The
rest of the save already reads the model: the peaks, the guitar selection, overrides, decay, the per-phase
spectra. Python's docstring says the save "reads … directly from model state — not passed by the view".
- *Recommendation:* the save reads the identified peaks itself; the parameters go.

**2. The natives' save takes other model-owned state from the view.** The view also passes
`annotationOffsets: tap.peakAnnotationOffsets`, and the microphone name / UID, calibration name and sample
rate from `fft` — the analyzer's own `fftAnalyzer`. (The measurement name, notes and the displayed axis range
are the view's and stay parameters.) To be read in full, all three editions, before deciding.

**3. The web's save is built in App, not by the analyzer.** App assembles the measurement from the snapshot
and calls `buildGuitarMeasurement` / `buildMaterialMeasurement`; there is no analyzer save. It is the save-side
counterpart of what F41 fixed for the load, which moved "load a measurement" out of App into
`analyzer.loadMeasurement`.
- *Recommendation:* an analyzer-owned save, as Swift's and Python's, reading its own state.

*Read in full (2026-09-27), all three editions:*

- **Item 1** stands as recorded, in both natives: the view reads `effective…PeakID` off the analyzer and hands
  it back. On the web, App passes `matPeaks` (built from the analyzer's snapshot) to `buildMaterialMeasurement`.
- **Item 2.** Swift's view passes `annotationOffsets: tap.peakAnnotationOffsets` (the save already falls back to
  that); Python's view does not pass it. Both views pass the microphone name and UID, the calibration name and
  the sample rate, read from the analyzer's own engine (`fft` / `analyzer.mic`, `analyzer._active_calibration_name`).
  Swift documents `sampleRate: nil` as "falls back to the engine's actual rate"; the code writes nil. The
  measurement name, notes and the displayed axis range are the view's and stay parameters.
- **Item 4.** `includeSpectrum` / `include_spectrum` (the view passes `true`, the default) and
  `spectrumSnapshot` / `spectrum_snapshot` (no caller) are unused in both natives. Python's docstring says
  `spectrum_snapshot` is "used by the import path" — import builds its measurements directly and never calls
  the save. Swift's parameter documentation for `saveMeasurement` sits above `guitarFullSavePeaks`, whose own
  comment tells the history of how it came to return `allPeaks`.
- **Item 3.** App's `buildCurrentMeasurement` assembles the measurement from the snapshot plus view state and
  calls `buildGuitarMeasurement` / `buildMaterialMeasurement` (material dimensions fall back to the Settings
  "defensively" if the measurement's own are unset); `saveMeasurement(m)` writes it to the store. The same
  builder feeds the live PDF export. Swift's comparison save is `tap.saveComparison`; the web's is the same
  builder's comparison branch.
- **Item 5 (found reading item 2).** The save records the microphone, calibration and sample rate current at
  SAVE time. After a playback those are the live input's again — the file's calibration is removed when the
  playback ends — so a measurement made from a played file records the input's microphone and calibration,
  not the recording's. All three editions.
- *Found (item 5, 2026-09-27):* a measurement with no microphone recorded already reads as "unknown" on load, in
  all three: no device switch, no microphone warning, and the calibration / sample-rate difference checks are
  skipped (they run only when the recorded microphone is found). Display differs: Measurement Details shows
  Microphone and Calibration as separate rows, each only when set; the PDF report shows the calibration only
  as a suffix of the Microphone row ("… · calibrated (X)" / "… · uncalibrated"), which appears only when a
  microphone is recorded — so without one the PDF shows neither.
- *Decision (owner, 2026-09-27 — item 5 display):* when no microphone is recorded, present the microphone as
  "unknown" — Details "Microphone: unknown", PDF "Microphone: unknown · calibrated (X)" / "… · uncalibrated".
- *Decision (owner, 2026-09-27):* all five as recommended — "Yes. go".
- *Done:*
  - Items 1, 2, 4 (natives): `saveMeasurement` / `save_measurement` take only the view's state — the name, the
    notes and the displayed axis range. The save reads the identified peaks (`selected…Peak?.id`), the
    annotation offsets and the provenance itself; `includeSpectrum` / `spectrumSnapshot` and the id /
    offsets / microphone / calibration / sample-rate parameters are gone, and the views pass only their own
    state. Swift's parameter docs now sit on `saveMeasurement`; `guitarFullSavePeaks`'s comment says what it
    does; Python's docstring no longer claims an import path; Python's identified-peak section lost its
    history comments.
  - Item 3 (web): `TapToneAnalyzer.buildMeasurement(name, notes, view)` builds the guitar or material
    measurement from the analyzer's own state (its `measurementType` is the authority), and
    `saveMeasurement(name, notes, view)` builds and stores it. App passes only the view's state; a comparison
    stays App's, as Swift's view branches to `saveComparison`; the live PDF export uses the same builder.
    The analyzer's gated-capture rate field was renamed `mpmSampleRate` (Swift's name), freeing
    `captureSampleRate` for the provenance getter.
  - Item 5 (all three): the analyzer holds `playbackProvenance` — the calibration a file was played with (or
    none) and its sample rate — set by the play-file method and cleared by every new sequence. `capture…`
    accessors (microphone name / UID, calibration name, sample rate) give the file's provenance with an
    unknown microphone after a playback, the input's otherwise; the save and the live PDF export read them.
    Measurement Details shows "Microphone: unknown" for a single measurement without one (not for a
    comparison — it has no microphone of its own; owner, 2026-09-27), and the PDF's Microphone row always appears ("unknown · calibrated (X)" /
    "… · uncalibrated"). Python's engine now sets the file's sample rate before its worker starts, as Swift's
    `prepareForFilePlayback` does — the analyzer's frequency-axis recompute had been racing the worker for it.
  - Tests: PR42/PR43 save through the model with no ids passed (all three); new: a save after a playback
    records the file's provenance and an unknown microphone, and a new sequence saves the input's (all
    three). Mutations — the fL role not written, the provenance not set — fail them in all three. Full
    suites: Swift 650, Python 767, web 694; tsc and eslint clean.

**6. The Results panel, a re-save and the live PDF show the live input for a loaded measurement.** Found at
run-review step 7 (Swift, owner, 2026-09-27): after loading a saved plate made from a played file (no
microphone), the Results panel named the built-in microphone. All three editions read the Results panel's
microphone from the current input device (Swift `fftAnalyzer.selectedInputDevice?.name`, Python
`_update_mic_name_label`, web App's `deviceLabel`), whatever the result came from. The item-5 provenance covers
live input and a played file; a loaded measurement falls through to the live input, so a re-save of it and its
live PDF export record the current microphone and calibration too.
- *Decision (owner, 2026-09-27):* the analyzer's provenance covers the loaded measurement as a third source — on
  load it takes the file's microphone name and UID, calibration and sample rate (a missing microphone is
  unknown) — and the Results panel, the save and the live PDF export read the same `capture…` values: live →
  the input device; a played file → unknown; a loaded measurement → its recorded microphone, or unknown.
- *Done:* item 5's `playbackProvenance` became `resultProvenance` (Swift `ResultProvenance`, Python a
  `ResultProvenance` named tuple, web an object) — microphone name and UID, calibration name, sample rate. The
  play-file method sets it (no microphone); `loadMeasurement` sets it from the file (Python before anything the
  load emits); a comparison load and every new sequence clear it. The `capture…` accessors return it when set,
  the live input otherwise. The Results panel shows `captureMicrophoneName`, or "unknown" when a result's
  provenance has no microphone (Swift `TapAnalysisResultsView`; Python `_update_mic_name_label`, now also
  refreshed when a playback starts or ends; web App from the snapshot's `resultProvenance`, the live device
  label otherwise). New test, all three: a loaded measurement reports its recorded provenance and a re-save
  keeps it; mutation (load not setting it) fails it. Full suites: Swift 651, Python 768, web 695.

**Run-review steps (F52 and F53).** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, clearing the service worker after every build (see F30's steps). Same
list per edition, canonical first. The recordings are the test fixtures: `Recording.wav` (8 guitar taps),
`plate-umik-1-swift-mac-1778816330.wav` (plate, L/C/FLC) and the calibration `7108913.txt`.

1. Guitar, Taps 8. Play File `Recording.wav`, no calibration file. → While it plays: Pause and New Tap are
   disabled, Cancel is enabled.
2. Press Cancel partway through. → The file stops at once (Play File is no longer tinted, the chart title no
   longer names the file), the result clears, and a live tap on the microphone is detected.
3. Play `Recording.wav` again; partway through, change Measurement Type to Plate and Apply. → The file stops;
   the status reads "Ready for fL tap"; no guitar tap from the file reaches the plate.
4. Plate with FLC, 1 tap per phase. Play File the plate recording with `7108913.txt`. → The Results rows for L,
   C and FLC show a dash until their phase is captured, then the identified peak; the measurement
   completes. Annotations is enabled once a peak is shown.
5. Save it; open its Measurement Details. → Microphone: unknown; Calibration: the `7108913` calibration.
6. Export its PDF report. → The Microphone row reads "unknown · calibrated (…7108913…)".
7. New Tap, then load the saved plate. → fL, fC and fLC are shown as saved; no microphone warning; the input
   device is unchanged.
8. Guitar, Taps 8. Play File `Recording.wav` (no calibration) to the end; Save; open Details. → Microphone:
   unknown; no Calibration row. Its PDF → "unknown · uncalibrated".
9. Live: New Tap, tap once, Save; open Details. → Your microphone and its calibration, as before.
10. Plate, live: before any tap, Annotations is disabled; tap L. → The L row shows the peak; Annotations is
    enabled.

**Run-review progress.** Swift and Python passed steps 1–10 (owner, 2026-09-27), after item 6 (Swift, step 7)
and the Python material-load fix (step 7: the view's load handler died on `_emit_loaded_peaks_at_threshold`'s
assert — no Results rows, Annotations inert). The web passed steps 1–10 after F52 item 9 (step 2: it never
named the played file). **Run-review complete — all three editions pass (owner, 2026-09-27).**

**F54 — `decay-tracking`: the web's new sequence keeps tracking the old tap's ring-out, the editions test
different cases, and the natives' tests set state by hand. (CLOSED — all 6 items done and run-reviewed in all
three. Commits: Swift `71049ad`, Python `eb0797c`, web `71a4d78`)**

Files: `DecayTrackingTests.swift` (7) / `test_decay_tracking.py` (7 + 1 view case) / `decay-tracking.test.ts` (8).
Production: `TapToneAnalyzer+DecayTracking.swift` / `tap_tone_analyzer_decay_tracking.py` / the web analyzer's
"Ring-out (decay) tracking" section. The three implementations match: the ring-out lives on the analyzer in
all three (the web's former engine-side `DecayTracker` is gone); `startDecayTracking` seeds the history with
the tap's peak-held level at its audio time; `trackDecayFast` stops — without recording — once a chunk is
3 s of audio after the tap, keeps 5 s of history and re-measures once it holds more than 10 entries;
`measureDecayTime` goes from the post-tap peak to the first later entry below `peak − decayThreshold` (15 dB).

| # | item | status |
|---|---|---|
| 1 | The web's new sequence does not stop the ring-out tracking or clear its history | ✅ done (all three) |
| 2 | The case lists differ | ✅ done (all three) |
| 3 | The natives' guard cases set the tracker's state by hand, one of them a state production never makes | ✅ done (all three) |
| 4 | Assertions differ: tolerances where the value is exact, and a case that checks only "positive" | ✅ done (all three) |
| 5 | Stale explanations in the natives | ✅ done (all three) |
| 6 | The 5 s history trim is unreachable | ✅ done (all three) |

**1. The web's new sequence does not stop the ring-out tracking or clear its history.** Swift's
`startTapSequence` sets `currentDecayTime = nil`, `peakMagnitudeHistory = []` and calls `resetDecayTracking()`
(`isTrackingDecay = false`); Python's does the same. The web's sets only `currentDecayTime = null`. A New Tap
(or Cancel, or a type change) within 3 s of a tap leaves the tracker running on the old tap: the next chunks
are recorded against it and `trackDecayFast` writes a ring-out back into the new sequence.
- *Recommendation:* the web's `startTapSequence` resets the tracker as Swift's does — the history cleared and a
  `resetDecayTracking()` that stops tracking. A case, all three: a new sequence within 3 s of a tap measures no
  ring-out from the old tap.
- *Decision (owner, 2026-09-27):* as recommended — fix it.
- *Done:* the web's `startTapSequence` clears `peakMagnitudeHistory` and calls a new private
  `resetDecayTracking()` (stops tracking), in Swift's order after `currentDecayTime = null`. New case DK8, all
  three: a new sequence started within 3 s of a tap, then twelve below-threshold chunks through the production
  per-chunk entry (Swift `onChunkLevel`, Python `_on_chunk_level`, web `processAudioFrame`) → not tracking, no
  ring-out. It failed on the web before the fix; with the reset removed it fails in Swift and Python. Python's
  `start_tap_sequence` also moved its `result_provenance` reset beside the playing-file-name clear, where
  Swift has it (it sat between the ring-out clears). Full suites: Swift 652, Python 770, web 698.

**2. The case lists differ.** Swift and Python: DK1 empty history, DK2 all samples before the tap, DK3 never
decays, DK4 normal decay, DK5 immediate decay, DK6 not tracking is a no-op, DK7 tracking with no tap time.
Web: DK4, DK5, the 15 dB default, never decays, the rising transient (measured from the post-tap peak, not the
tap), samples before the tap ignored, a streamed ring-out through `startDecayTracking` + `trackDecayFast`, and
a no-op before tracking starts. The web has no DK1 or DK7; the natives have no default-threshold, rising-
transient or streamed case. No edition tests the 3 s stop, the 5 s trim, or the reset on a new sequence
(item 1). Python also has `TestRingOutReachesTheView` — the ring-out reaching the Ring-Out box through
`currentDecayTimeChanged`; Python-specific by nature (its view is fed by that signal).
- *Recommendation:* one list in Swift's order, the same ids and the same cases in all three, including the
  cases no edition has.
- *Decision (owner, 2026-09-27):* items 2–5 together, as recommended.

**3. The natives' guard cases set the tracker's state by hand.** DK6 sets `isTrackingDecay = false` and DK7
sets `isTrackingDecay = true` with `decayTapAudioTime = nil` directly, then call `trackDecayFast`. DK7's state
is one production never makes: `startDecayTracking` always sets both. The web's no-op case uses a fresh
analyzer, and its streamed case goes through `startDecayTracking`.
- *Recommendation:* the guard cases reach their state through production — a fresh analyzer (not tracking),
  `startDecayTracking`, and the 3 s stop; DK7 goes.
- *Decision (owner, 2026-09-27):* items 2–5 together, as recommended.

**4. Assertions differ.** DK4 allows ±0.05 s around a value that is exactly 0.5 s (the web asserts it to six
digits); DK5 asserts only "positive" where the value is exactly 0.1 s (the web asserts 0.1).
- *Recommendation:* exact values in all three, as the web does.
- *Decision (owner, 2026-09-27):* items 2–5 together, as recommended.

**5. Stale explanations in the natives.**
- Both headers: "The tracking timer runs for 3 seconds" — there is no timer; tracking stops on the audio
  clock.
- Both `trackDecayFast`s: "The web's DecayTracker stops here too" — the web has no `DecayTracker`.
- Swift `stopDecayTracking`'s doc: "diagnostic information is printed to the console explaining whether the
  signal never peaked…" — it prints nothing; it refers to `trackDecayFast(inputLevel:)`, the old signature.
- Swift `trackDecayFast`'s doc: "called … from the `$inputLevelDB` Combine subscription" — it is called from
  `onChunkLevel`. `startDecayTracking` ends in a "Debug output removed" comment.
- Python `stop_decay_tracking` carries `@Slot()`, but nothing connects to it; it is called directly.
- *Recommendation:* correct them to say what the code does; drop the unused decorator.
- *Decision (owner, 2026-09-27):* items 2–5 together, as recommended.

**6. The 5 s history trim is unreachable** (found designing item 2's list, 2026-09-27). `trackDecayFast` keeps
only entries less than 5 s older than the current chunk. Only `startDecayTracking` turns tracking on, and it
also sets the tap time and seeds the history with one entry at that time; `trackDecayFast` appends only while
a chunk is under 3 s of audio after the tap and stops, without recording, at 3 s; nothing else writes the
history but the clear on a new sequence. So the history never spans 3 s and the trim never removes an entry —
in all three. It was added 2026-04-01 (Swift `f505c6d`), when a wall-clock timer ended the tracking; #19
(`58796ac`, 2026-09-25) replaced that timer with the audio-clock stop, which left the trim nothing to do.
- *Decision (owner, 2026-09-27):* remove it, in all three.

*Done — items 2–6, all three (2026-09-27):*
- One list, the same ids, cases and values in Swift's order: DK1 empty history, DK2 all before the tap, DK3
  never decays, DK4 normal (0.5 s), DK5 immediate (0.1 s), DK6 a fresh analyzer records nothing, DK7 a new
  sequence stops the old tap's ring-out (item 1's case), DK8 the 15 dB default (0.3 s), DK9 the rising
  transient timed from the peak (0.2 s), DK10 pre-tap entries ignored (0.2 s), DK11 a streamed ring-out
  (0.4 s), DK12 tracking stops at 3 s of audio without recording, DK13 no ring-out until more than 10
  entries. DK11–DK13 are new to the natives; DK1, DK2, DK12 and DK13 new to the web. The old DK7 (tracking
  with no tap time) is gone.
- The tracking cases (DK6, DK7, DK11–DK13) reach their state through production — a fresh analyzer,
  `startDecayTracking`, `startTapSequence` and the per-chunk entry (Swift `onChunkLevel`, Python
  `_on_chunk_level`, web `processAudioFrame`) — none sets tracker state by hand. Every value is asserted to
  1e-6 in all three.
- Comments say what the code does: the "3-second timer", the web `DecayTracker`, the Swift diagnostics claim,
  the Combine caller, the old signature and the "Debug output removed" line are gone; Python's unused
  `@Slot()` is dropped.
- The 5 s trim is removed from all three.
- Mutations: the 3 s stop made `>` instead of `>=` fails DK12, and "more than 10" made "10 or more" fails
  DK13, in all three. Python keeps its view case. Full suites: Swift 657, Python 775, web 702; tsc and
  eslint clean.

**Run-review steps.** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, clearing the service worker after every build (see F30's steps).

1. Guitar, Taps 1: New Tap, tap once and let it ring out; before 3 s have passed, press New Tap. → The
   Ring-Out box goes back to "Waiting…" and stays there until the next tap.

**Run-review progress.** All three editions passed step 1 (owner, 2026-09-27).

### S8 — Settings & presentation (6 slugs)

Status: ✅ **CLOSED 2026-10-02** — all 6 slugs read; every finding it produced (F55–F59) fixed and run-reviewed in
all three. F58 closed 2026-09-30 (Swift `b23445e`, Python `0d2279e`, web `d8aa7c8`); F55 closed 2026-10-01 (Swift
`e3d52ec`, Python `272b361`, web `b7de553`); F56 closed 2026-10-01 (Swift `a8ff669`, Python `0ca9d22`, web
`2e84a8d`); F57 closed 2026-10-02 (Swift `6a5e500`, Python `0104cf0`, web `ac95203`); F59 closed 2026-10-02 (Swift
`c4fdc3d`, Python `c5c6ce9`, web `a4c5ad7`). The fifth and sixth slugs, `view/pdf-report` (added 2026-10-01) and
`view/spectrum-export` (2026-10-02), were added in F59 for the PDF report and the image it embeds, which no slug
covered. S8 completes Stage 1; #17 has Stage 2 (the shared case lists) to do.

**Audit record.** As in S6–S7, this table records only what the reading produced.

| slug | read? | produced |
|---|---|---|
| `display-range` (7/5/10) | ✅ | **F55** |
| `field-precision` (14/14/14) | ✅ | **F56** |
| `analysis-quality` (6/6/20) | ✅ | **F57** |
| `wav-dump-folder` (4/5/—) | ✅ | **F58** |
| `view/pdf-report` (1/18/18; added 2026-10-01) | tagged in F59, with `test/pdf-report` | **F59** |
| `view/spectrum-export` (1/3/3; added 2026-10-02) | tagged in F59, with `test/spectrum-export` | **F59** (item 7) |

**Counts, measured 2026-09-29** (Swift: `@Test`s in the files, none argument-expanded; Python: `pytest
--collect-only`; web: `vitest list`):

| slug | Swift | Python | web | files (Swift / Python / web) |
|---|---:|---:|---:|---|
| `display-range` | 7 | 5 | 10 | `DisplayRangeExpansionTests.swift` + `DisplayRangeTests.swift` / `test_display_range_expansion.py` / `display-range.test.ts` |
| `field-precision` | 14 | 14 | 14 | `FieldPrecisionTests.swift` / `test_field_precision.py` / `field-precision.test.ts` |
| `analysis-quality` | 6 | 6 | 20 | `AnalysisQualityTests.swift` / `test_analysis_quality.py` / `analysis-quality.test.ts` |
| `wav-dump-folder` | 4 | 5 | — | `WavDumpFolderTests.swift` / `test_wav_dump_folder.py` / — (the web downloads the WAV; no folder) |
| `view/pdf-report` (tests `test/pdf-report`, measured 2026-10-02) | 1 | 18 | 18 | `PDFReportTests.swift` (one `@Test` over 18 fixtures) / `test_pdf_report.py` / `pdf-report.test.ts` |
| `view/spectrum-export` (tests `test/spectrum-export`, measured 2026-10-02) | 1 | 3 | 3 | `SpectrumExportTests.swift` (one `@Test` over 3 cases) / `test_spectrum_export.py` / `spectrum-export.test.ts` |

How it was read: one reader per slug across the editions, then the claims that decide a finding checked by hand
(marked *checked*); the rest are the reading's, marked *to confirm* where a change would rest on them.

**F55 — `display-range`: the widening rule is tested well in all three, but the slug also carries the per-type
display-range store, the three editions trigger and land the widening differently, and comments cite code that
does not exist. (CLOSED — all 23 items done and run-reviewed in all three. Commits: Swift `e3d52ec`,
Python `272b361`, web `b7de553`)**

Production: `DisplayRange.expanded(toInclude:min:max:)` / `expanded_to_include` / `expandedToInclude` — the same
rule in all three (pad 10 %, widen only, floor 1 Hz); the app's only callers go through it. Tests: the five
widening cases (above, below, inside, the 1 Hz floor, at the boundary) are the same in all three and call
production.

| # | item | status |
|---|---|---|
| 1 | The slug carries a second rule: the per-type display-range settings store | done |
| 2 | Three mechanisms trigger the widening and three places receive it | done |
| 3 | Nothing tests the caller (the guitar guard, the trigger) | done |
| 4 | Comments: history, a nonexistent Swift publisher, a missing file, phase labels | done |
| 5 | The stored range: Swift's Save Current View stores it unrounded; Python truncates to whole Hz; the web rounds | done — revised: stored exactly |
| 6 | Python's chart range is whole Hz (canvas `minFreq`/`maxFreq` are `int`; a load sets the axis with `int(...)`); Swift's is `Float` | done |
| 7 | Swift falls back to an untyped range key no other edition has | done |
| 8 | Settings' Done moves the chart to the saved range even when the range did not change (Swift, Python) | done |
| 9 | After a load, New Tap / Play File: the web returns to the saved range; Swift and Python keep the loaded range | done |
| 10 | Python's Settings validates the range differently from Swift (the web not yet checked) | done |
| 11 | A load widened the chart onto the peaks it restored, so a saved view did not come back as saved | done |
| 12 | Python enforces the chart's 50 Hz / 10 dB minimum span on every range, not only on zoom | done |
| 13 | Swift and the web drop the spectrum's points beyond the range, leaving the line short of the edges; Swift also flattens magnitudes onto the dB edges | done |
| 14 | Settings, zoom/pan and widening each enforce their own chart limits; a 20–30 Hz range cannot be zoomed at all | done |
| 15 | Python's load does not publish the loaded range, and its measurement-type handling resets the chart | done |
| 16 | The return to the saved view fires on different events; the web's comparison sets the chart, not the loaded range | done |
| 17 | Python's chart starts from the untyped range keys Swift removed (item 7) | done |
| 18 | The "Showing …" label above the peak list shows a different range, formatted differently, in each edition | done |
| 19 | The web's guitar peak list is filtered by the saved range; Swift's and Python's by the chart's live range | done |
| 20 | Python re-detects the peaks whenever it applies a range; a plate's peak list and dot vanish on Reset to Saved | done — test parked in #1 |
| 21 | The web shows the range line, and its selection buttons, only in the guitar peak view; Swift and Python always show the line, and Swift shows the buttons by its results list | done |
| 22 | The annotation and crosshair frequencies are formatted three ways; Python's annotations never show kHz | done |
| 23 | The web lists a completed plate's peaks as fL, fC, fLC; Swift and Python by frequency | done |

**1. A second rule under this slug.** Swift `DisplayRangeTests.swift` tests `TapDisplaySettings`'s per-type
ranges (defaults, set one type without clobbering another) — the file is tagged `test/display-range`, and
`TapDisplaySettings.swift` says `@parity state/settings-store tests=test/display-range`. Python's twin of those
two cases is in `test_wi6_tap_display_settings.py`, untagged. The web has five settings cases (three more than
the natives: the default fallback, a stored read, a partial merge) and its "no clobber" case uses other values.
- *Recommendation:* a `test/settings-store` slug for the store, in all three, with one case list.
- *Revised (2026-10-01, against the owner's rules — the same algorithm in every edition, and the same architecture
  except where a platform forces a difference):* the web's five cases all test behaviour every store has (factory
  defaults; the default when nothing is stored; a stored value read back; one type not clobbering another; a partial
  edit keeping the other bound). The web store's shape — one `{minHz, maxHz}` object per type behind
  `displayRangeFor` / `setDisplayRangePatch` — is an architecture difference no platform requires. The web store
  takes Swift's shape (per-type min and max accessors with the default fallback, Swift's names), and all five cases
  run in all three under `test/settings-store`; the partial edit becomes "setting the minimum leaves the maximum".

**2. Trigger and destination differ** (*to confirm*). Swift: the view's `.onReceive` of the analyzer's
`$selectedLongitudinalPeak` / `$selectedCrossPeak` / `$selectedFlcPeak` writes view `@State` `minFreq`/`maxFreq`
(Float). Python: the analyzer emits a dedicated `materialPeakIdentified` signal from capture and load, and the view
calls `update_axis(int(lo), int(hi))` — truncated. Web: a `useEffect` over all identified peaks writes the
persisted per-type settings (`updateDisplayRange`). Open questions: does Swift widen on a manual L/C/FLC
reassignment (its publishers would fire; Python emits only at capture and load)? Does Swift persist the widened
range, as the web does?
- *Recommendation:* settle what Swift does on both questions, then bring Python and the web to its mechanism.
- *Settled (2026-10-01):* Swift widens at capture and at load — the three peaks are written only there and by the
  redo's clear (ignored); material has no manual L/C/FLC reassignment in any edition. Swift never saves the widened
  range: only Settings writes the per-type store. So the web, which saves it, differs in behaviour; Python truncates
  to whole Hz (`int(lo)`), Swift does not; and Python's dedicated `materialPeakIdentified` signal is a different
  mechanism from observing the peaks, though it fires at the same moments.
- *Revised:* Python gives the three peaks a change signal emitted at every write (the Qt counterpart of
  `@Published`), and the view's slot widens the canvas's live range — no truncation; `materialPeakIdentified` goes.
  The web moves the widening into `useChartView`, which owns the live chart range (Swift's `@State`), observing the
  analyzer's three peaks — the `App.tsx` effect that widened the saved settings goes.

**3. The wiring is untested** in every edition — only the pure rule is.
- *Recommendation:* one case per edition through the analyzer: a material peak outside the range widens it; a
  guitar measurement does not.
- *Revised:* no edition can test its view's widening — Swift's `.onReceive` and `@State` work only in a rendered
  view, the web's tests run in Node without React rendering, and nothing builds Python's main window. So the same
  split in all three: one shared function in `DisplayRange` / `display_range` / `displayRange.ts` makes the whole
  decision — given a peak, the measurement type and the current range, the widened range, or the range unchanged
  for a guitar (the guitar check moves into it from each view) — and each view only observes the peaks and applies
  the result to its live range. Tests, one case list: the function (material outside widens, inside unchanged,
  guitar unchanged, with the five rule cases); the analyzer announces each peak change (capture, load, clear).

**4. Comments.** `DisplayRange.swift:17-19` is project history ("Extracted from … on 2026-09-20 …"); `:25` speaks
of a "log-ish axis" (log frequency was removed — *to confirm*); `TapToneAnalysisView+Actions.swift:236` gives
project rationale; `DisplayRangeExpansionTests.swift:14` is history. Python `tap_tone_analysis_view.py:3742` and
web `App.tsx:457` say Swift uses `.onReceive(tap.$autoSelected*PeakID)` — *checked*: no `autoSelected` exists in
Swift. `DisplayRangeTests.swift:9` and `test_wi6…:220` cite `test/settings-display-range.test.ts`, which does not
exist. `display-range.test.ts:12` and `test_wi6…:217` carry the phase label "(6h)". `test_wi6…:226-229` says
"import via the bare `models.` path" and the code does not. *Checked:* the log-frequency axis was removed, so
"log-ish axis" is stale.

*Decision (owner, 2026-10-01):* all four as revised — "Please update your recommendations in the SLUG-SWEEP.md and
then implement them", and "Yes" to the shared-function split for item 3.

**5–7. The range's precision and an old key** (found implementing items 1–3, 2026-10-01). **5.** Swift stores the
range as given (`setMinFrequency(_:for:)` takes a `Float`); Python stores whole Hz (`set_f_min(int(v))`, read back
with `int(...)`); the web stores what Settings' fields give, but Save Current View rounds to whole Hz. **6.** Python's
canvas reports its range as whole Hz (`minFreq` / `maxFreq` return `int`) and a load sets the axis with
`int(snap.min_freq)`; Swift's chart range is `Float` throughout, rounded only where it is shown as text (`"%.0f"`).
**7.** Swift reads a type's range, when none is stored, from the untyped key `displayMinFreq` / `displayMaxFreq`
before the default. Swift wrote that key from `19f5184` (2026-02-14) to `7b037c5` (2026-02-26) — only
`Beta_release_1.0` (2026-02-20) shipped with it; 1.0.1 onward write per-type keys. Python and the web never had it.
- *Decision (owner, 2026-10-01):* 5–6 — the range is a float everywhere, stored and on the chart, rounded only where
  shown as text, as Swift; 7 — remove Swift's fallback, so all three read the per-type value or the type's default.
- *Revised (owner, 2026-10-01), item 5:* `FieldPrecision` — the same table in all three — says one precision per field
  governs "input (round-on-commit), storage, and display", and the display frequency range is 0 dp: the stored range
  is whole Hz by that rule. Swift's Settings keeps it (whole-number fields); Swift's Save Current View breaks it
  (stores the chart range unrounded); Python truncates rather than rounds; the web keeps it. "(a). If it is really
  an integer then store it as such — this is on range only — clearly captured frequencies are float." So the stored
  range is whole Hz, rounded half away from zero, stored as an integer, in all three; the chart's live range and
  captured frequencies stay float (item 6 stands).
- *Revised again (owner, 2026-10-01), item 5 — superseding the whole-Hz rule above:* at the Swift run-review the
  owner noted that pan and zoom make ranges between whole numbers, so rounding a saved view moves its edges by up to
  half a unit — a peak sitting on the edge of a zoomed view appears or disappears, from the chart and the results
  list, when the view is saved and restored. "We need to change our minds and save the ranges in their native values
  … limit data entry to integral numbers in the settings panel but the value actually stored is full range — same in
  what goes on disk." Checked: the range is display-only (the chart's dots, the exported chart, the results list);
  no analysis result reads it. The editions' native widths differ (Swift `Float`, Python/web 64-bit), and the file
  format already resolves that by storing Swift's `Float` fields at 32 bits in every edition. So: the saved range —
  frequency per type and the dB range — is stored exactly, in Swift's `Float` (Python and the web round to 32 bits at
  the store, as they do for files); Settings' fields take whole numbers and display at their precision, and Done
  writes a bound only if its field was edited — an untouched field keeps the exact stored value. The 32-bit vs
  64-bit arithmetic of the editions is recorded for #1 (`RESTRUCTURE-NOTES.md`, "The numeric model"). "Yes to
  both."

**8–10. When the chart's range moves** (found at the Swift run-review, step 4, 2026-10-01). The owner pressed
**New Tap** expecting the chart to return to the saved range; it did not. Traced in all three:

| Behaviour | Swift | Python | Web |
|---|---|---|---|
| Settings **Done** | always writes the saved range to the chart (`applySettings`) | always (`update_axis`) | only when the saved range changed (the view follows `effectiveDefault`) |
| A peak re-widening after Done | no (run-review check, owner) | no — signals fire on writes only | no — each effect runs when its peak changes |
| **New Tap** / **Play File** after a play | leaves the range | leaves it | leaves it |
| **New Tap** / **Play File** after a load | leaves the loaded range | leaves it | returns to the saved range (`setLoadedView(null)`) |
| Load | the loaded range, then the peaks widen it | same order | same result |
| Settings range validation | clamp 20–20000 Hz, ≥ 10 Hz apart, else keep the saved | ≥ 1 Hz apart only | not yet checked |

The owner's questions, and the answers agreed (2026-10-01):
- *Should Done with no range change reset the chart?* No. Swift does it because `applySettings` writes every
  field back, changed or not — a side effect, not a design; it throws away a zoom whenever Settings is closed for an
  unrelated change. Done moves the chart only when the range changed (the web's behaviour).
- *What range should New Tap and Play File give?* The one on the chart: a new tap or a played file is more data in
  the same view, and a view zoomed to repeat a tap must survive it. After a load, the loaded range was the
  measurement's, not the user's — as the manual says New Tap starts "fresh with your own values" — so the chart
  returns to the saved view, unless the user has zoomed or panned since the load.
- *What is the saved range for?* Each measurement type's home view: where the chart starts at launch and on a type
  switch, and what Reset to Saved returns to. A starting point, not a limit; changed only by Settings' range fields
  and Save Current View.

The principle: the chart's live range moves only when the user moves it (zoom, pan, a reset, a new range in
Settings), when the app must show something (a loaded measurement's range; a newly identified plate or brace peak),
or on a measurement-type switch (to that type's saved view). Nothing else — not New Tap, not Play File, not a Done
that changed no range.
- *Decision (owner, 2026-10-01):* "I do agree with everything you said." The principle goes in the user manual (§6.8,
  rewritten; §8.4) as the intent described to the user. Items 8–10 implement it. Presented, then: Play File after a
  load follows the New Tap rule — "Yes"; the magnitude range follows items 8 and 10 as the frequency range does —
  "Yes"; "Go ahead and implement".

**11. A load widened the chart** (found at the Swift run-review, step 6, owner, 2026-10-01). A plate saved with the
chart at 20–50 Hz loaded widened to its peaks. The load restores the three peaks, and the view cannot tell a restore
from a capture's identification, so it widened — Swift's original behaviour, carried into all three, and against
the principle (widening is for a *newly identified* peak; the manual's §6.8 already says a load "shows the range
that measurement was saved with"). "I would have thought that the idea of saving a chart includes any zoom so that
when I restore the chart it is identical to the image that was saved."
- *Decision (owner, 2026-10-01):* (b) — the analyzer records whether its material peaks came from a load (one
  flag, set by a load before it writes the peaks, cleared when a sequence starts), and the widening decision does
  not widen a restored peak. Not (a), skipping widening while a load is in progress: the web's effects run after the
  load has finished, so that would need a different mechanism there.

**12. Python's minimum span** (found at the Python run-review, step 1, owner, 2026-10-01): a 20–50 Hz range showed as
10–60. All three refuse a zoom step that would leave the span at 50 Hz / 10 dB or less (Swift `applyFrequencyZoom`:
`if newMaxFreq > newMinFreq + 50`; the web's `FREQ_MIN_SPAN` / `DB_MIN_SPAN`), but Python sets the limit on the
pyqtgraph ViewBox (`setLimits(minXRange=50, minYRange=10)`), which widens *every* range — Settings, Reset to Saved, a
load, a widening — about its centre.
- *Decision (owner, 2026-10-01):* as Swift — the minimum applies to zoom gestures only.

**13. The spectrum at the chart's edges** (found at the Swift run-review, owner, 2026-10-01: a 28–38 Hz view's line
stopped short of both sides). Swift (`SpectrumView.chartData`, the plate/brace series, `ExportableSpectrumChart`) and
the web (`spectrumRender.ts` `drawCurve`) draw only the points inside the range, so the segments that cross an edge
are missing — a gap of up to one bin at each side. Swift also clamps magnitudes into the dB range
(`clampedMagnitude`), so a peak above the top is drawn flat along it; the web clips (`ctx.clip()`). Python gives
pyqtgraph the whole spectrum and the view clips it — correct on both axes.
- *Decision (owner, 2026-10-01):* draw through the edges and clip, as Python does, in all three.

**14. One set of chart limits** (found at the Swift run-review, owner, 2026-10-01: with the range set to 20–30 Hz,
the mouse-wheel zoom did nothing). Zoom refused any step whose result was not wider than 50 Hz — zooming *out* from a
10 Hz range included, since one step reaches only ~11.5 Hz — in all three (Python since item 12). And the limits
differed by control:

| | Lowest frequency | Highest | Minimum span | Magnitude | Minimum dB span |
|---|---|---|---|---|---|
| Settings (Done) | 20 Hz | 20000 Hz | 10 Hz (≥) | −120…20 dB | 10 dB (≥) |
| Zoom / pan | 0 Hz | 5000 Hz | 50 Hz (>) | −120…20 dB | 10 dB (>) |
| Widening onto a peak | 1 Hz | none | none | — | — |

- *Decision (owner, 2026-10-01):* one set of limits for Settings' validation, zoom, pan and widening, in all three:
  frequency 1–5000 Hz ("there is no useful data and the displays get funky if it is so high" above 5 kHz; 20 kHz
  came from the analysis range, no longer a setting), magnitude −120…20 dB, a minimum span of 10 Hz and 10 dB ("now
  that display is fixed … I see no reason to limit zoom to 50 Hz instead of 10"), compared the same way everywhere
  (a span of exactly 10 is allowed).

**15. Python's load does not publish its range** (found at the Python run-review, step 6, owner, 2026-10-01: after a
load, New Tap stayed on the loaded view). Swift's load calls `setLoadedAxisRange` with the snapshot's four bounds (or,
with no snapshot, the saved range), and the view remembers that as the loaded range. Python's load set the axis
itself, from the view (`canvas.update_axis(int(…))`, `setYRange`), never through `loadedAxisRangeChanged`, so the
canvas had no loaded range to compare at New Tap; a comparison's range was truncated to whole Hz. And Python's
measurement-type handling (`_apply_measurement_type_to_ui`, which a load also runs) reset the chart to the saved
range — a second move Swift does not make; Swift moves the chart on a type switch only through Settings' Done.
- *Decision (owner, 2026-10-01):* "Go" — as Swift; then "Yes" to removing the type handling's reset.

**16. What returns the chart to the saved view** (found from the owner's question, 2026-10-01: "Why was it based on a
complete measurement before? Also, if I do a comparison measurement from the measurement browser what is the
display range that is used?"). Swift watched `isMeasurementComplete` change from true to false, and the web an
effect on the same transition; Python's canvas acts on every `start_tap_sequence`. So a sequence start that found
the measurement already not complete — Cancel, a re-arm, New Tap during a comparison, which is not a complete
measurement — returned to the saved view in Python only. Swift's `startTapSequence` sets
`isMeasurementComplete = false` on every start, so the event is there; only `.onChange` hides the repeats. And the
web's two comparison paths (`onLoadMeasurement` with comparison entries, `onCompare`) set the chart directly
(`setView`), so it never held a loaded range and New Tap after a comparison stayed on the comparison's range;
Swift's `loadComparison` and Python's go through `setLoadedAxisRange`.
- *Decision (owner, 2026-10-01):* every sequence start is the event, in all three ("The fact that it is a simple
  change does not mean it has simple implications"; then "Go"), with the web's comparison fix.

**17. Python's startup range** (found while doing item 7). Python's window reads `AppSettings.f_min()` /
`f_max()` with no measurement type at startup (`tap_tone_analysis_view.py`, `self._f_range`), which reads the
untyped `display/f_min` / `display/f_max` keys — the keys Swift's item 7 removed — and the canvas sets its first range
from them (`fft_canvas.py`, `setXRange(frange["f_min"], …)`) before the startup reset moves it to the type's saved
range. The web has no untyped key.
- *Decision (owner, 2026-10-01):* "Yes" — as Swift and the web: the chart is built on the current type's saved range,
  with no startup move, and the untyped keys go.

**18. The "Showing …" label** (found while doing item 17), above the peak list:

| | Range shown | Format | Source |
|---|---|---|---|
| Swift | the chart's live range — follows zoom, pan, a load, a widening | `formattedAsFrequency`: "25.0 Hz - 45.0 Hz", kHz from 1000 | `TapAnalysisResultsView` `minFreq` / `maxFreq` |
| Python | the chart's live range | after a view change, whole Hz, truncated (`freqRangeChanged` is `Signal(int, int)`); after Settings' Done and at startup, `FieldPrecision` ("25") | `_on_canvas_freq_range_changed`, `_update_freq_range_label` |
| web | the **saved** range — does not follow zoom, pan or a load | the number as stored | `App.tsx` `displayMinHz` / `displayMaxHz` |

- *Decision (owner, 2026-10-01):* "Yes" — all three show the chart's live range the Swift way
  (`formattedAsFrequency`, which Python and the web gain); Python's signal carries floats.

**19. The web's guitar peak list** (found while doing item 18). Swift lists a guitar's peaks within the chart's live
range (`TapAnalysisResultsView`: `peak.frequency >= minFreq && peak.frequency <= maxFreq`, the view's range), and
Python re-filters on every view change (`_refresh_results_peaks` on `freqRangeChanged`). The web filters by the
saved range (`App.tsx` `displayPeaksInRange`, on `displayMinHz` / `displayMaxHz`), so zooming, panning, a load or
a widening does not change which peaks are listed — the list and the label (now the live range) can disagree.
- *Decision (owner, 2026-10-01):* "Fix the web as well to match swift."

**20. Python re-detects the peaks when the chart moves** (found at the Python run-review, step 13, owner,
2026-10-01: after Reset Frequency Axis to Saved, a completed plate's peak list and its fFLC dot disappeared; zooming
to the same view brought them back). Python's `FftCanvas.update_axis` called
`analyzer.recalculate_frozen_peaks_if_needed()` on every range it applied — the resets, a load's range, a widening, Settings' Done — and Settings' Done
called it again directly ("mirroring Swift's recalculateFrozenPeaksIfNeeded() calls in applySettings()", which
have none). For a plate, that re-ran `find_peaks` on the frozen spectrum (new peak ids) and emitted
`peaks_above_peak_min`, the guitar projection, so the list and the dot matched nothing. A zoom or pan
(`_refresh_peaks_for_viewport`) emits `material_identified_peaks` and never re-detects. In Swift and the web the
recalculation has one caller, Re-analyze (`reanalyzePeaks`); applying a range changes the view only. Older than
F55 — from when the analysis range followed the display range; it is now the constant 30–2000 Hz.
- *Decision (owner, 2026-10-01):* "So, please fix python."

**21. Where the web shows the range line** (found at the web run-review, owner, 2026-10-01: a plate in review showed
no "Showing …" line). Swift's `TapAnalysisResultsView` shows the line in its results header with no condition —
guitar, plate, brace, a comparison, the per-tap table — and Python's `freq_range_label` is always shown. The web
wrapped the whole row, the line and the selection buttons, in `!comparison && !material && !showMultiTap`. Not from
F55: the committed code has the same condition. The buttons' rule differed too: Swift shows them when
`!sortedPeaksWithModes.isEmpty && !showingMultiTapComparison` — its results list, which is empty in a saved
comparison, a plate's or brace's every peak above Peak Min, a guitar's listed peaks — with Deselect All disabled
for a plate or brace and Reset to Auto guitar-only; the web showed them in the guitar view even with no peaks.
- *Decision (owner, 2026-10-01):* "Both please" — the line always, and the buttons by Swift's rule.

**22. The annotation and crosshair frequency** (found at the run-review, owner, 2026-10-01: Python's annotations show
Hz where Swift's and the web's show kHz). Annotations: Swift `formattedAsFrequency` ("1.4 kHz"); Python
`peaks_model.py` `f"{freq:.1f} Hz"`, never kHz; the web `spectrumRender.ts` `fmtFreq`, kHz with two decimals
("1.40 kHz"). Crosshair: two decimals in kHz in all three, each its own code (Swift `formatCursorFrequency` /
`formatCrosshairFrequency`, Python `fft_canvas.py`, the web `spectrumRender.ts`). Also found: two Swift doc comments
still gave the old limits (`SpectrumView.swift`: 20 Hz – 20 kHz; `SpectrumView+GestureHandlers.swift`: 0 Hz – 5 kHz,
minimum span 50 Hz), and the web's `spectrumExport.ts` cited `fmtFreq` in `pdfReport.ts`, gone since item 18.
- *Decision (owner, 2026-10-01):* "the crosshair should be the same precision as well. So, use a shared formatter for
  both annotation and crosshair frequency. Clean up the comments."

**23. A completed plate's peak rows** (found at the run-review, owner, 2026-10-01). Swift's `materialPeakRows`
lists the fixed slot rows during capture and, once complete, the identified peaks in frequency order; Python the
same. The web's `MaterialResults` always listed the slots in fL, fC, fLC order.
- *Decision (owner, 2026-10-01):* "re-order the plate peaks by frequency to agree with swift."

**Moved out: the annotation default position** (found at the run-review, owner, 2026-10-01). The three editions place
an untouched label differently, and its behaviour under zoom differs from a dragged label's. Not a display-range
question, and more to settle than this finding can: hub Issue #25, `docs/ANNOTATION-DEFAULT-POSITION.md`.

*Done — items 1–14 (2026-10-01):*
- **1.** The web store takes Swift's shape: `defaultMinFrequency` / `defaultMaxFrequency`, `minFrequency` /
  `maxFrequency` (stored or default), `setMinFrequency` / `setMaxFrequency` (each bound per type; returning the
  settings patch, since web settings are an immutable value), and `setFrequencyRange` composing the two for the
  callers that store both (Settings' Reset, Save Current View, `updateDisplayRange`). Each bound is stored on its
  own, so one never stored reads its default as in Swift; the saved JSON shape is unchanged. `displayRangeFor`,
  `setDisplayRangePatch` and `defaultDisplayRange` are gone. The store's tests have their own slug,
  `test/settings-store` — Swift `SettingsStoreTests.swift` (was `DisplayRangeTests.swift`), Python
  `test_settings_store.py` (moved out of `test_wi6_tap_display_settings.py`), web `settings-store.test.ts` — the same
  five cases: the per-type defaults; a type with nothing stored reads its default; a stored range reads back;
  storing one type does not change another; storing one bound leaves the other. The store's production tag points
  at it in all three (`tests=test/settings-store`).
- **2–3.** One decision function in all three — Swift `DisplayRange.widened(onto:for:min:max:)`, Python
  `widened_onto`, web `widenedOnto`: for a plate or brace, `expanded`; for a guitar, the range unchanged. Each view
  only applies it: Swift's `expandFreqRangeToInclude` (its guitar check moved into the function); Python's
  `_on_material_peak_changed`, connected to new `selectedLongitudinalPeakChanged` / `selectedCrossPeakChanged` /
  `selectedFlcPeakChanged` signals that the analyzer's three peak properties emit on every write (capture, load,
  redo's clear) — `materialPeakIdentified` and its four emits are gone, and the range is no longer truncated to whole
  Hz; the web's `useChartView`, which observes the snapshot's three peaks (one effect each) and widens its live view —
  the `App.tsx` effect that widened the saved settings is gone, so the saved range no longer changes. Tests, the
  same in all three: the decision (material outside widens, inside unchanged, guitar unchanged — with the five rule
  cases); the announcement (`MaterialPeakAnnouncementTests.swift`, `test_material_peak_announcement.py`,
  `material-peak-announcement.test.ts`): loading a plate announces each of its peaks; redoing a phase announces its
  peak cleared.
- **4.** The history and the "log-ish axis" are gone from `DisplayRange.swift`; the project rationale from
  `TapToneAnalysisView+Actions.swift`; the history from `DisplayRangeExpansionTests.swift`; the citations of
  `$autoSelected*PeakID` (Python view and analyzer signal comments; the web's went with its effect); the nonexistent
  `test/settings-display-range.test.ts`; the "(6h)" labels; the import note.
- **5.** The store rounds at its one write point, so Settings and Save Current View both go through it: Swift
  `setMinFrequency` / `setMaxFrequency` store `Int(FieldPrecision.rounded(value, frequencyHz))`; Python
  `AppSettings.set_f_min` / `set_f_max` store `int(fp.rounded(v, FREQUENCY_HZ))` (was `int(v)`, truncating); web
  `setMinFrequency` / `setMaxFrequency` store `FieldPrecision.rounded(value, frequencyHz)`, and the two
  `Math.round`s in Save Current View are gone. Python's Save Current View and Apply show the values through
  `FieldPrecision` (`fp.string`). A sixth `settings-store` case in all three: a stored range is whole Hz (15.5 → 16,
  180.4 → 180).
- **5, as revised.** The store keeps the range exactly: Swift `setMinFrequency` / `setMaxFrequency` store the `Float`
  as given (the whole-Hz rounding is gone); Python `AppSettings.set_f_min` / `set_f_max` / `set_db_min` /
  `set_db_max` store `float(np.float32(v))`; web `setMinFrequency` / `setMaxFrequency` and a new `setMagnitudeRange`
  store `Math.fround(v)`, and Save Current View's `Math.round`s are gone. One shared rule for a Settings field on
  Done — `DisplayRange.enteredValue(text, stored, decimals)` / `entered_value` / `enteredValue`: the stored value,
  exactly, if the field still shows it; otherwise the number typed; none if not a number. Swift's `applySettings`
  and Python's `_apply_settings` read all four range fields through it; the web's Done through it on the draft's
  display; the web's range fields display through `FieldPrecision.string`. Tests, all three: "a stored range keeps
  its exact value" (15.37 / 180.43 read back at `Float` precision) replaces the whole-Hz case; an untouched field keeps
  the exact stored value; an edited field is the number typed; a field that is not a number gives none. Mutation:
  the rule always reading the text (each edition) — killed. Suites: Swift 732, Python 852, web 751; with items
  12–13, Swift 735, Python 855, web 754; with item 14, Swift 739, Python 857, web 760.
- **6.** Python's canvas `minFreq` / `maxFreq` return the float range (`update_axis` takes floats); a load sets the axis
  from the snapshot's range as is; `AppSettings.f_min` / `f_max` read as float; the "Showing … Hz" label formats
  through `FieldPrecision`.
- **7.** Swift's `minFrequency(for:)` / `maxFrequency(for:)` read the per-type key or the type's default; the untyped
  keys and their fallback are gone, and the header's key note says so.
- **6, completed with 8–10.** Python's canvas also rounded its range to whole Hz whenever the view changed
  (`_refresh_peaks_for_viewport`: `int(round(x0))`), right after a load or a widening set it; it now keeps the
  view's floats. The model's `loadedAxisRangeChanged` signal carried the frequencies as `int`; now `float`.
- **8–10.** The decisions are shared, in `DisplayRange` / `display_range` / `displayRange.ts`, with the chart's four
  bounds as `ChartRange` (Swift, Python) / the web's existing `ChartView`: `onSettingsDone(saved, previouslySaved,
  typeChanged)` — the saved range if it or the type changed, else none; `onNewMeasurement(current, loaded, saved)` —
  the saved range if the chart is still showing the loaded range, else none; `loadedAfterWidening(loaded, before,
  after)` — a widening of the loaded view is remembered as the loaded view. Each view keeps the loaded range it is
  showing (Swift `@State loadedChartRange`, Python canvas `_loaded_chart_range`, web `useChartView`'s `loadedRef`):
  set when a load's range is applied, carried through a widening, compared with the chart when the measurement
  stops being complete (Swift `.onChange(of: isMeasurementComplete)`, Python `set_measurement_complete(False)`, web an
  effect on the snapshot's `isMeasurementComplete`) and then cleared. A user move needs no hook: the chart no
  longer equals the loaded range. Settings' Done: Swift `applySettings` and Python `_apply_settings` persist, read
  the saved range back and apply `onSettingsDone`; the web's chart applies it when its saved range or type changes,
  and no longer follows "loaded range, else saved". Python no longer resets the dB axis to −100…0 at every new
  measurement (`set_measurement_complete(False)`). Validation: Python's Done calls `validate_frequency_range` /
  `validate_magnitude_range` (it had its own ±1 rule); the web gains `validateFrequencyRange` /
  `validateMagnitudeRange` in `settings.ts`, which its Done applies (it had none). Python's Done shows the ranges
  through `FieldPrecision`. Tests, the same in all three: nine decision cases (`test/display-range`) — Done with
  nothing changed / a changed frequency range / a changed magnitude range / a changed type; a new measurement with
  no load / while showing the load / after the user moved the chart; widening while showing the load / after a move —
  and twelve validation cases (`test/settings-store`; moved from Python's `test_wi6`, new in Swift and the web):
  frequency and magnitude — valid, clamped low, clamped high, inverted and too narrow read the saved range, exactly
  10 apart accepted.
- **11.** `materialPeaksFromLoad` / `material_peaks_from_load` on the analyzer (web: in the snapshot), set by a load
  before it writes the peaks and cleared in `startTapSequence` / `start_tap_sequence`. The decision takes it:
  `widened(onto:for:fromLoad:min:max:)` / `widened_onto(frequency, type, from_load, …)` / `widenedOnto(frequency,
  type, fromLoad, …)` leaves the range unchanged for a restored peak; each view passes the analyzer's flag (the web
  reads it from the same snapshot as the peaks). Tests, all three: a peak restored by a load leaves the range; loaded
  peaks are marked as from a load until a new sequence. Mutation: the decision ignoring the flag (each edition)
  — killed.
- **12.** Python's `setLimits` keeps only the bounds (0–5000 Hz, −120…20 dB); the minimum span moved to the zoom
  gestures: the ViewBox's `scaleBy` (which pyqtgraph's wheel, drag and axis zooms all call) is wrapped to refuse, per
  axis, a step that would leave 50 Hz / 10 dB or less, and the ⌘/Ctrl-scroll zoom applies the same check —
  `zoom_keeps_minimum_span(lo, hi, scale, min_span)`, Swift's `newMax > newMin + 50`. Tests:
  `test_chart_zoom_limits.py` (`@parity none` — Swift's twin is `SpectrumViewGestureTests` C3 and its magnitude case).
  Mutation: `>` → `>=` — killed.
- **13.** `DisplayRange.drawnIndices(of:min:max:)` / web `drawnIndices` — every point inside the range plus the one
  beyond each edge. Swift's `chartData`, plate/brace series and both export charts use it; the magnitude clamps are
  gone and the plot area is `.clipped()` (live chart and export). The web's `drawCurve` uses it inside its existing
  clip. Python unchanged. Tests: `DrawnPointsTests.swift` / `drawn-points.test.ts` (`@parity none` — pyqtgraph clips
  the whole spectrum itself): the point beyond each edge is included; a range between two points draws the segment
  across it; a range wider than the spectrum draws every point. Mutation: no beyond-the-edge point (Swift, web) —
  killed.
- **14.** The limits are defined once per edition: Swift `DisplayRange.frequencyBounds` (1…5000), `magnitudeBounds`
  (−120…20), `minFrequencySpan` / `minMagnitudeSpan` (10); Python `display_range.MIN_/MAX_FREQUENCY_HZ`,
  `MIN_/MAX_MAGNITUDE_DB`, `MIN_FREQUENCY_SPAN_HZ` / `MIN_MAGNITUDE_SPAN_DB`; the web `presentation/chartLimits.ts`
  (a module of its own so `settings.ts` and `displayRange.ts` need not import each other). Settings' validation
  (`validateFrequencyRange` / `validateMagnitudeRange` in all three), zoom (Swift `applyFrequencyZoom` /
  `applyMagnitudeZoom`; Python's wrapped `scaleBy` and ⌘/Ctrl-scroll; the web's new `zoomedRange`, pulled out of
  `SpectrumChart` so it can be tested), pan (Swift `handlePan`; Python `setLimits`; the web's `panFreqBy` / `panDbBy`)
  and the widening (`expanded` now stops at 5000 Hz) all read them, and the span is compared the same way everywhere
  (`>=`): a zoom to exactly 10 is allowed, and a 10 Hz range can be zoomed out. Swift's global
  `maxDisplayFrequency` is gone; its gesture doc no longer claims 20 Hz–20 kHz. Tests: the validation cases'
  bounds (below 1 Hz, above 5 kHz) in all three; a widening stops at 5 kHz (all three); zoom — Swift
  `SpectrumViewGestureTests` (zoom-in refused at the minimum, zoom to exactly the minimum allowed, zoom-out from the
  minimum allowed, frequency and dB; pan stops at 1 Hz), Python `test_chart_zoom_limits.py`, the web's new
  `chart-zoom-limits.test.ts` (`@parity none`, as Swift's and Python's gesture tests). Mutation: `>=` → `>` (each
  edition) — killed.
- Parity map regenerated (`tooling/parity`): `test/settings-store` in all three; `test/display-range` gains the
  announcement tests; `--check` clean. It also now lists the two edition-only test files from #20 and F58.
- Mutations, each killed: the guitar check removed from the decision (Swift, Python, web); the Python peak setter not
  announcing; the web max setter overwriting the stored min (after the one-bound case was made to store a min first
  — from nothing stored it could not tell); the rounding removed from each store's setter (Swift, Python, web);
  `onSettingsDone` always moving (Swift), `onNewMeasurement` ignoring a move (Python), the web's validation not
  clamping. Suites (with item 11): Swift 729, Python 849, web 748.

*Done — items 15–16 (2026-10-01):*
- **15.** Python's load publishes the snapshot's four bounds through `set_loaded_axis_range` (with no snapshot, the
  saved range), as Swift; `loadedAxisRangeChanged` carries four floats and the canvas applies them and remembers
  them as its loaded range. A comparison's range is no longer truncated to whole Hz. The view's own axis setting
  during a load is gone, and `_apply_measurement_type_to_ui` no longer resets the chart — the one startup reset
  moved to startup. `test_loaded_range.py`: a load publishes its snapshot's range; a load with no snapshot
  publishes the saved range.
- **16.** Swift: `.onReceive(tapToneAnalyzer.$isMeasurementComplete) { if !$0 { applyNewMeasurementRange() } }`,
  which hears every `startTapSequence`, replaces the `.onChange`. Python unchanged (`start_tap_sequence`). Web: the
  analyzer counts sequence starts (`sequenceStarts`, in the snapshot, advanced in `startTapSequence`), and
  `useChartView` acts when the count changes — a snapshot can show only a change, so the count stands for Swift's
  repeated `false`. Both web comparison paths set the loaded range (`setLoadedView`), as Swift's
  `setLoadedAxisRange`. `test_comparison_mode.py` now drives `TapToneAnalyzer.for_testing()` (it had three stand-in
  classes of its own). Web test: each sequence start is counted, even when the measurement was not complete.
  Suites: web 761.

*Done — item 17 (2026-10-01):* Python's window builds the chart from `TapDisplaySettings.min_frequency()`
/ `max_frequency()` — the current type's saved range, as Swift's `@State` from `TapDisplaySettings.minFrequency` and
the web's initial `defaultView` — and the startup `_reset_both_to_saved()` is gone. The startup "Showing …" label
formats through `FieldPrecision`, as the label's Settings path (item 18 is the label's own difference). `AppSettings.f_min` / `f_max` / `set_f_min` / `set_f_max` require the type; the
untyped `display/f_min` / `display/f_max` keys are gone. Suites: Python 860.

*Done — item 18 (2026-10-01):* Swift unchanged. Python gains `formatted_as_frequency` in
`views/utilities/extensions.py` (Python's `Extensions.swift`), and the web `formattedAsFrequency` in
`presentation/frequencyFormat.ts`; each PDF's private copy of the same function (Python `_fmt_freq` in
`tap_analysis_results_view.py`, web `fmtFreq` in `pdfReport.ts`) is replaced by it — the same output. The label
reads "Showing 25.0 Hz - 45.0 Hz" in all three: Python's three writers (startup, Settings' Done, a view change) use
it, and `freqRangeChanged` is `Signal(float, float)`; the web's label shows `view.minHz` / `view.maxHz`, the chart's
live range.
- *Tests (owner, 2026-10-01: "The fact that swift does not have one is not sufficient reason not to have one"):*
  the label is one function in all three — Swift `displayRangeLabel(minFreq:maxFreq:)` in `Extensions.swift`, Python
  `display_range_label` in `extensions.py`, web `displayRangeLabel` in `frequencyFormat.ts` — which Swift's
  `TapAnalysisResultsView`, Python's three writers and the web's `App.tsx` call. New slug `view/frequency-format`
  (the formatter and the label) with `test/frequency-format`: `FrequencyFormatTests.swift` /
  `test_frequency_format.py` / `frequency-format.test.ts`, the same five cases — below 1 kHz is Hz with one decimal;
  from 1 kHz is kHz with one decimal; the label shows both bounds; a zoomed range keeps its fraction (25.37–44.81 →
  "Showing 25.4 Hz - 44.8 Hz"); a range crossing 1 kHz mixes units. Parity map regenerated; `--check` clean.
  Suites (with item 19): Swift 747, Python 865, web 766.

*Done — item 20 (2026-10-01):* `update_axis` sets the range only (its `init` flag, which skipped the
recalculation, is gone). Settings' Done applies Peak Min through the canvas's `set_threshold` — the slider's path,
which re-projects the displayed peaks and tells the view — instead of re-detecting. The recalculation's only caller
is now `reanalyze_peaks`, as in Swift and the web. Swift and the web unchanged. Suites: Python 865.
- *Test — parked in #1 (owner, 2026-10-01: "I agree"):* the canvas cannot be built in a test, since it creates and
  starts the analyzer itself and so opens the audio device; Swift's and the web's views are handed theirs. Handing
  Python's canvas the analyzer moves Python's startup, which is #1's work, so the test waits for it
  (`RESTRUCTURE-NOTES.md`, "Who owns the analyzer"). Until then, run-review step 13 covers item 20.

*Done — item 21 (2026-10-01):* web `App.tsx` — the range line is always shown; the buttons show when
`resultsListPeaks` (Swift's `sortedPeaksWithModes`: none in a saved comparison, `peaksAbovePeakMin` for a plate or
brace, `displayPeaksInRange` for a guitar) has peaks and the per-tap table is not up; Deselect All is disabled for a
plate or brace, with Swift's help text, and Reset to Auto is guitar-only. Swift and Python unchanged. No unit test:
the rule is inline in the view in all three; run-review step 1. Suites: web 766.

*Done — items 22–23 (2026-10-01):*
- **22.** The annotation label and the crosshair readout use item 18's shared formatter in all three: Swift
  `formattedAsFrequency` (its two private crosshair formatters are gone; the macOS cursor and the iOS crosshair both
  call it); Python `formatted_as_frequency` (`peaks_model.py`, `fft_canvas.py`); the web `formattedAsFrequency`
  (`spectrumRender.ts`; its `fmtFreq` is gone). So the crosshair now reads one decimal in kHz, as the labels. The two
  Swift comments give `DisplayRange`'s limits (1 Hz – 5 kHz, 10 Hz / 10 dB spans); the web's `spectrumExport.ts`
  comment names `formattedAsFrequency`. The formatter is tested (`test/frequency-format`); the call sites are inline in
  the views.
- **23.** The web's `MaterialResults`: once complete, the identified peaks in frequency order; the slot rows during
  capture unchanged. Swift and Python unchanged.
- Builds: Swift macOS and iOS Simulator. Suites: Swift 747, Python 865, web 766.

*Done — item 19 (2026-10-01):* the web's `displayPeaksInRange` filters on `view.minHz` / `view.maxHz`,
the chart's live range, as Swift's `sortedPeaksWithModes` on the view's `minFreq` / `maxFreq` (it moved below
`useChartView`, which provides the view). Swift and Python unchanged. No unit test: in all three the filter is
inline in the view; run-review step 20.

**Run-review steps.** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, clearing the service worker after the build. Same list per edition, Swift first.
The plate recording is `plate-umik-1-swift-mac-1778816330.wav` with the calibration `7108913.txt`. The chart's
range is reset from the chart's menu (right-click, or its … button): **Reset Frequency Axis to Saved**.

1. Settings: Measurement Type Plate; set the frequency range to 20–50 Hz; **Done**. → The chart shows 20–50 Hz, and
   the line above the peak list reads "Showing 20.0 Hz - 50.0 Hz".
2. **Play File** the plate recording with `7108913.txt`. → As each of fL, fC (and fFLC) is identified, the chart
   widens to show it, with a little room past the peak.
3. Open Settings. → The range still reads 20–50 Hz. **Done** without changing anything. → The chart stays widened.
4. **Reset Frequency Axis to Saved**. → The chart shows 20–50 Hz.
5. Zoom the chart to about 25–45 Hz; **Save** the measurement. **New Tap**. → The chart stays as you zoomed it.
6. Load the saved plate. → The chart shows exactly the range it was saved with (about 25–45 Hz) — not widened to
   its peaks — and the peak list shows its peaks in frequency order. **New Tap**. → The chart returns to the saved view, 20–50 Hz.
7. Load it again; zoom or pan the chart; **New Tap**. → The chart stays where you put it.
8. Load it again; **Play File** the plate recording. → The chart returns to 20–50 Hz, then widens as each peak is
   identified.
9. Settings: change the range to 20–60 Hz; **Done**. → The chart moves to 20–60 Hz.
10. Settings: Measurement Type Generic; **Done**. → The chart moves to Generic's saved range. Tap a guitar whose
    peaks reach above it. → The chart is not widened.
11. Settings (Generic): set the range to 80–300; **Done**. Reopen Settings and enter minimum 500, maximum 100
    (inverted); **Done**; reopen Settings. → The range reads 80–300 — the saved range, kept because the entry was
    invalid; not 100–500 (the entry is never swapped).
    Then enter minimum 0, maximum 300; **Done**; reopen Settings. → The range reads 1–300: a minimum below 1 Hz is
    raised to 1 (the chart's limits are 1–5000 Hz). Enter maximum 6000; **Done**; reopen. → 1–5000.
12. Settings: enter magnitude minimum −50, maximum −45 (the right way round, but only 5 dB apart — the bounds must
    be at least 10 apart); **Done**; reopen Settings. → The magnitude range reads the saved range again, not −50 to
    −45.
13. Plate: zoom in until an identified peak sits just inside the chart's edge; Settings → **Save Current View**;
    **Done**. → The chart does not move, and the peak is still just inside. Pan away, then **Reset Frequency Axis to
    Saved**. → The same view comes back, with the peak still just inside. Reopen Settings. → The range fields show
    whole numbers; **Done** without editing them. → The chart does not move.
14. Settings (Plate): set the range to 28–38 Hz (10 Hz — the narrowest allowed); **Done**. → The chart shows
    28–38 Hz. Scroll to zoom in. → Nothing changes (it is already at the minimum). Scroll to zoom out. → The chart
    widens. Try a range of 28–35 in Settings. → It is refused: the saved range is kept.
15. Plate, still at 28–38 Hz: **Play File** the plate recording (the chart widens onto its peaks), then **Reset
    Frequency Axis to Saved**. → The chart shows 28–38 Hz, and the line reaches both side edges, with no gap.
    Settings: set the magnitude range so a peak rises above its top; **Done**. → The line is cut off at the top edge
    where it crosses it, not drawn flat along the edge.
16. Put the ranges back: Settings → Display → **Reset to Defaults**, once with Plate selected and once with Generic.
17. Settings: Measurement Type Generic; **Done**. Measurements → **Compare…** → select two guitar measurements saved
    with different ranges. → The chart shows a range covering both. **New Tap**. → The chart returns to Generic's
    saved range, 75–350 Hz. Compare the same two again; zoom or pan; **New Tap**. → The chart stays where you put it.
18. Settings: Measurement Type Plate; set the range to 25–45 Hz; **Done**. Quit and relaunch. → The chart opens at
    25–45 Hz. Settings → Display → **Reset to Defaults** (Plate).
19. Settings: Measurement Type Generic; **Done**. → The line above the peak list reads "Showing 75.0 Hz - 350.0 Hz".
    Zoom and pan the chart. → The line follows the chart, still one decimal. Zoom out until the chart's right edge
    passes 1000 Hz. → The upper bound reads in kHz (e.g. "1.2 kHz"); a peak label above 1000 Hz and the crosshair
    readout over it read the same way, one decimal.
20. Generic: tap a guitar, or load a guitar measurement, so peaks are listed. Zoom the chart so some listed peaks fall
    outside it. → They leave the peak list; the list holds only peaks within the "Showing …" range. Zoom back out. →
    They return.

**Run-review progress.** Swift passed steps 1–14 (owner, 2026-10-01) — before item 5 was revised to exact storage;
steps 11–13 were reworded during the run. After the revision: Swift passed step 13 again (owner, 2026-10-01).
Python stopped at step 1 (item 12). Swift found item 13, and item 14 (a 20–30 Hz range would not zoom). After items
12–14: Swift steps 11, 14–15; Python and the web steps 1–16. Python passed steps 6–7 after item 15 (owner,
2026-10-01). After items 15–19: Swift steps 6–8 (Swift's trigger changed, item 16), 11 and 14–20; Python steps 1–5
and 8–20; the web steps 1–20. Python found item 20 at step 13 (owner, 2026-10-01). Swift and Python done (owner,
2026-10-01). The web found item 21 at step 1; after it, the web steps 1–20. **All three editions pass steps 1–20 (owner,
2026-10-01).** Items 22–23 came after that pass; their checks are step 6 (the plate's rows) and step 19 (the labels
and the crosshair). All three pass steps 6 and 19 after items 22–23 (owner, 2026-10-01). **Run-review complete —
all three editions pass.**

**F56 — `field-precision`: identical tests on an identical table, but most of the table is used by nothing,
every screen formats its own numbers, and the web rounds halfway values differently. (CLOSED — all items done and run-reviewed in all three. Commits: Swift `a8ff669`,
Python `0ca9d22`, web `2e84a8d`)**

Production: `FieldPrecision` (Swift) / `field_precision` (Python) / `precision.ts` (web) — the same 13-entry
table and `string` / `rounded` / `decimalsWithin` in all three. Tests: the same 14 cases, same inputs and expected
values, all calling production.

How it was analysed (2026-10-01): a census, per edition, of every place the app shows a computed value — peak
frequency and magnitude, Q and bandwidth, the moduli, speed of sound, density, ring-out and tap ratio, Gore
thickness — with its format, and every reference to each table constant; the claims below checked by hand
(*checked*), the rounding by running each language's formatter.

| # | item | status |
|---|---|---|
| 1 | The computed-value entries are used by nothing; every display hard-codes its decimals | done |
| 2 | Python's field validation does not call the function the tests test | done |
| 3 | Halfway values and 32-bit values format differently in the three | done |
| 4 | The web's number fields show the value without its precision ("557.5" for 557.50) | done |
| 5 | Python's peak table text gives Q 0 decimals — but no screen shows that text | done |
| 6 | Test tolerances differ; the headers overstate what the table governs | done |
| 7 | The stored magnitude range | superseded by F55 item 5 — what remains was done with item 6 |
| 8 | Python's Save Current View and Reset write the dB fields with 1 decimal into 0-decimal fields | done |
| 9 | The Metrics panel's frequencies: Sample Rate in Hz but Bandwidth (half of it) in kHz with 2 decimals; Settings shows the sample rate three more ways | done |
| 10 | Swift's compact status line shows the level with 0 decimals; its other layout and the others with 1 | done |
| 11 | Dead code: Swift `TapToneAnalysisView+Actions.formatFrequency`; Python's peak CSV export | done |
| 12 | Python's Metrics Bin Count always uses a comma; Swift and the web follow the locale | done |

**1. The computed-value entries are used by nothing** (*checked*, all three). Of the seven computed entries only
`peakMagnitudeDB` has callers (Swift: the Metrics panel; Python: the status bar and Metrics; web: the level readout,
status bar and Metrics). `peakFrequencyHz`, `qFactor`, `youngsModulusGPa`, `speedOfSoundMS`, `densityGPerCm3` and
`decayRatio` have none. Every other display hard-codes its decimals — about 50 sites per edition: the peak rows and
cards, the material rows, annotations, exports, the comparison and multi-tap tables, the measurement list and
detail, the results panel and the PDF.
- The decimals agree across the three at every site the census found, and with the table where it has an entry. So
  the editions show the same numbers today; what is missing is the single source the table claims to be.
- Values with no entry, each the same in all three: shear modulus GLC 3, specific modulus 1, bandwidth 1, Gore
  thickness 2, radiation ratio 1, cross/long ratio 3, long/cross ratio 1, ring-out time 2 (`decayRatio` is the tap
  ratio).
- Infinity: `FieldPrecision.string` shows "-∞"; sites that bypass it show the language's own — Swift's C formatter
  "-inf" (the crosshair magnitude, the material peak rows, the PDF peak table), Python's "-inf", the web's
  "-Infinity".
- *Recommendation:* route every display of a computed value through `FieldPrecision.string` with its entry, in all
  three, and add the missing entries. Item 3's fix lives in `string`, so it reaches only the displays that go
  through it — without this, the web's halfway rounding stays wrong at ~50 sites. The suffixes stay as each screen
  has them ("1.23s" on screen, "1.23 s" in the PDF — the same in all three).
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**2. Python's field validation** (*checked*). Swift's field asks `FieldPrecision.decimalsWithin` on each keystroke
(`ValidatedNumberField`: the iOS delegate and the macOS formatter's `isPartialStringValid`); the web's `NumberField`
does the same. Python's field installs a `QRegularExpressionValidator` built from `input_regex` — the same pattern,
but Qt applies it, and `decimals_within` is called only by the tests. The behaviour is the same (every prefix of an
accepted entry is accepted, so Qt's "intermediate" changes nothing); the mechanism is not.
- *Recommendation:* Python's field gets a `QValidator` whose `validate` calls `decimals_within`, as Swift's
  formatter does; the tests then test the function the field uses.
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**3. Halfway values and 32-bit values** (*checked*, by running each formatter):

| value, decimals | Swift (`Float`, `String(format:)`) | Python (`float`, f-string) | web (`toFixed`) |
|---|---|---|---|
| 2.5, 0 | 2 | 2 | **3** |
| 0.125, 2 | 0.12 | 0.12 | **0.13** |
| 0.15, 1 | **0.2** | 0.1 | 0.1 |

Two causes. The web's `toFixed` rounds an exact tie up; C and Python round it to even. And Swift formats a 32-bit
`Float` — 0.15 as a `Float` is 0.150000006, which rounds up, where the 64-bit 0.15 is 0.149999999999999994 — so
Python and the web show "0.1" where Swift shows "0.2". (The numeric model is recorded for #1 in
`RESTRUCTURE-NOTES.md`; this is where it reaches the screen.) `Intl.NumberFormat` with `roundingMode: 'halfEven'`
does not fix the web: it rounds the shortest decimal form, giving "0.2" for the 64-bit 0.15.
- *Recommendation:* `string` formats the value as Swift's `Float`, rounding exact ties to even, in all three —
  Python formats `float(np.float32(v))`; the web formats `Math.fround(v)` from its exact decimal expansion
  (`toPrecision`) with ties to even. Tests, all three: 2.5 → "2", 0.125 → "0.12", 0.15 → "0.2".
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**4. The web's number fields** (*checked*; the record's first reading corrected). All three commit a field's value
on every edit, rounded to its precision (Swift `MaterialDimensionsEditor` `.onChange`, Python `textEdited`, web
`onChange`) — not a difference. The difference is the display: Swift and Python seed a field with
`FieldPrecision.string` whenever the value differs from what the field reads (Swift `seedField`, Python
`_seed_field`), so a plate length reads "600.00" and a mass "208.0"; the web's `NumberField` seeds and re-syncs on
blur with `String(value)`, so it reads "600" / "557.5" / "208" — visible in the F55 run-review screenshots.
- *Recommendation:* the web's `NumberField` seeds with `FieldPrecision.string`, and only when the value differs from
  the field's number, as Swift's `seedField`.
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**5. Python's Q with 0 decimals** (*checked*). `peaks_model.py` gives the Q column's display text with 0 decimals,
but nothing shows that text: the peak list draws cards (`peak_card_widget.py`, Q with 1 decimal, as Swift and the
web), and the model's CSV export writes raw values (`data_value`). The display text is left from the old table view.
- *Recommendation:* remove the model's unused display-text formatting (or route it through `string` if it is kept
  for accessibility). No visible change.
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation." — removed (not routed).

**6. Tolerances and comments** (*checked*). The `rounded` cases compare within 0.001 in Swift and Python and within
5e-6 in the web (`toBeCloseTo(x, 5)`). The headers in all three say one precision "governs input, storage, and
display … the saved measurement, and the PDF" — storage holds for the dimensions (rounded on entry) but not for the
display range (F55 item 5: stored exactly), and display is true only once item 1 is done. Swift's header has
history ("Replaces the scattered ad-hoc literals"). `frequencyHz`'s doc says it covers "tap/peak thresholds" —
thresholds are dB, under `magnitudeDB`.
- *Recommendation:* one tolerance in all three (1e-5 — tight enough to catch an unrounded result, loose enough for
  `Float`); the headers say what the table governs once items 1–3 are decided; the history line and the
  `frequencyHz` doc corrected.
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**7. The stored magnitude range** (found in F55, 2026-10-01). *Superseded:* F55 item 5 stores the range exactly in
all three; what remains — the comments — is in item 6.

**8. Python's dB fields after Save Current View and Reset** (found by the census). Swift writes the four range
fields with `FieldPrecision.string` at `frequencyHz` / `magnitudeDB` (0 decimals). Python's Save Current View writes
the dB fields with 1 decimal (`tap_tone_analysis_view.py`, `f"{y_range[0]:.1f}"`) and its Reset writes the dB
defaults the same way — "-45.3" in a field that accepts no decimal point.
- *Recommendation:* Python writes them with `fp.string(…, fp.MAGNITUDE_DB)`, as Swift.
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**9. The Metrics panel's frequencies** (found by the census; corrected by the owner, 2026-10-01). The panel shows
five values in Hz or kHz, the same way in all three:

| Value | Shown as | Code |
|---|---|---|
| Frequency Resolution | "0.7 Hz" | the panel's private formatter (below) |
| Sample Rate | "48,000 Hz" — whole Hz, thousands separator | Swift `Int.formatted()`, Python `f"{sr:,.0f}"`, web `toLocaleString()` |
| Bandwidth | "24.00 kHz" | the private formatter |
| Frame Rate | "21.5 Hz" | 1 decimal, its own format |
| Peak Frequency | "123.4 Hz" | the private formatter |

The private formatter — Swift `FFTAnalysisMetricsView.formatFrequency`, Python `fft_analysis_metrics_view._fmt_freq`,
web `MetricsPanel` `freq` — gives 1 decimal in Hz below 1000 and **2 decimals in kHz from 1000**. So Peak Frequency
reads "1.23 kHz" only for a peak at or above 1 kHz, which a guitar tap's strongest peak rarely is (this item first
said it was the peak frequency that showed 2 decimals; the owner did not see it, rightly — it is rare). Bandwidth
is always above 1 kHz, so it always shows 2 decimals. The owner's point: "bandwidth is 1/2 of sample rate and one is
in Hz and the other KHz. That is the inconsistency."

Settings shows the sample rate differently again: Swift's device list "Sample Rate: 48 kHz" (`%.0f` of kHz, so
44.1 kHz reads "44 kHz"), Swift's selected-device row "48000 Hz" (`%.0f`, no separator), Python's "48000 Hz"
(`f"{…:.0f} Hz"`, no separator), the web's "48.0 kHz" (`toFixed(1)`).
- *Decision (owner, 2026-10-01):*
  - "sample rate and bandwidth in Hz with , everywhere on all editions" — whole Hz with the thousands separator,
    following the locale ("Follow the locale"), through one shared function per edition, used by the Metrics panel
    and Settings. Python's always-comma `f"{sr:,.0f}"` changes to the locale's separator.
  - Peak Frequency uses `formattedAsFrequency`, as the annotations and the crosshair ("I meant formattedAsFrequency —
    same as the crosshairs/annotations"); Frequency Resolution and Frame Rate use it too — always below 1000, so 1
    decimal in Hz, as today. No new table entries.
  - `formattedAsFrequency` takes its decimal from the table: `FieldPrecision.string(…, peakFrequencyHz)`, so every
    displayed frequency's precision comes from one place.
  - The panel's private formatters go.

**10. Swift's compact status line** (found by the census). `TapToneAnalysisView+Controls.swift` shows the level with
0 decimals in one layout (`specifier: "%.0f"`) and 1 in the other; Python and the web show it with
`peakMagnitudeDB` (1).
- *Recommendation:* both Swift layouts use `FieldPrecision.string(…, peakMagnitudeDB)`.
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**11. Dead code** (found by the census). Swift `TapToneAnalysisView+Actions.formatFrequency` has no callers.
Python's `PeakListWidget.save_peaks` (a CSV export of the peak list) has no callers, and no other edition has one.
- *Recommendation:* remove both.
- *Decision (owner, 2026-10-01):* "Agreed on 1-8, 10, 11 with your recommendation."

**12. Python's Bin Count** (found while doing item 9, 2026-10-01). The Metrics panel's Bin Count is grouped by the
locale in Swift (`frequencies.count.formatted()`) and the web (`toLocaleString()`), but always with a comma in Python
(`f"{bin_count:,}"`).
- *Decision (owner, 2026-10-01):* fixed in #17 under item 9's decision ("Follow the locale").

*Done — items 1–6 and 8–12 (2026-10-01):*
- **Before/after check.** Before any change, each edition wrote the PDF of every `.guitartap` fixture (seven files —
  plates and guitars) and, on the web, the text its chart canvas draws; after the change, again. Their text is
  identical in all three but for the PDF's generation time. A throwaway harness in the scratchpad (a temporary test
  per edition, deleted), not committed.
- **1.** The table gains `bandwidthHz` 1, `shearModulusGPa` 3, `specificModulus` 1, `radiationRatio` 1,
  `crossLongRatio` 3, `longCrossRatio` 1, `goreThicknessMM` 2, `decayTimeS` 2 (Python `BANDWIDTH_HZ` …), with
  `decayRatio` documented as the tap-tone ratio. Every display of a computed value formats through `string` with its
  entry, in all three: the peak rows and cards, the material peak rows, annotations, the crosshair magnitude, exports,
  the comparison and multi-tap tables, the measurement list and detail, the results panels, the status bar and
  material status messages, and the PDF. The web's `f0`–`f3` helpers and the local `hz` helpers' literals are gone.
  Swift's range-field strings in `TapToneAnalysisView` use `string` with `frequencyHz` / `magnitudeDB`. The crosshair
  magnitude, the material peak rows and the PDF now show infinity as "-∞" in Swift (they used the C formatter's
  "-inf").
- **2.** Python's `ValidatedNumberField` installs a `QValidator` whose `validate` calls `decimals_within` (the
  `QRegularExpressionValidator` is gone); typing behaves as before (checked: "29.356" stops at "29.35", "abc" is
  refused, "-" and "29." are accepted, a 0-decimal field refuses the point).
- **3.** `string` formats the value as Swift's `Float`, an exact tie to even: Python `f"{float(np.float32(v)):.Nf}"`;
  the web `fixedHalfEven(Math.fround(v), N)`, from the double's exact binary value (BigInt); Swift unchanged.
  Checked on 14 values (ties, 32-bit cases, negatives, -0, large and tiny values) — Python and the web identical.
  Tests, all three: an exact tie rounds to even (2.5 → "2", 0.125 → "0.12"); the 32-bit value is shown (0.15 → "0.2").
- **4.** The web's `NumberField` fills its text with `FieldPrecision.string` when the value differs from the number the
  field reads (Swift `seedField`), so a plate's length reads "557.50" and its mass "208.0"; the focus tracking and the
  re-fill on blur are gone.
- **5.** Python's peaks model no longer formats display text for the frequency, magnitude, Q, pitch and cents
  columns, nor keeps `data_value` and `q_value`, which only the export used.
- **6.** One tolerance, 1e-5, for the `rounded` cases in all three. The headers say what the table governs — input
  precision and the decimals every display shows; the saved display range is stored exactly — and the history line
  and `frequencyHz`'s "thresholds" are gone.
- **8.** Python's Save Current View and Reset write the dB fields with `fp.string(…, fp.MAGNITUDE_DB)`.
- **9.** `formattedAsFrequency` takes its decimals from `peakFrequencyHz`; a new `formattedAsWholeHertz` (Swift
  `formattedAsWholeHertz(_:locale:)` in `Extensions.swift`, Python `formatted_as_whole_hertz` with a `QLocale`, web
  `formattedAsWholeHertz` with the browser's locale) gives whole hertz with the locale's separator. The Metrics panel:
  Sample Rate and Bandwidth whole hertz; Frequency Resolution, Frame Rate and Peak Frequency `formattedAsFrequency`;
  the panel's private formatters gone. Settings' sample rate: whole hertz in all three (Swift's device list and
  selected-device row, Python's label, the web's readout). Tests (`test/frequency-format`, all three): grouped by the
  locale (en-US "48,000 Hz", "22,050 Hz"; de-DE "48.000 Hz"); rounded to the nearest hertz (44100.4 → "44,100 Hz").
- **10.** Swift's compact (iPhone) status line shows the level with `string` at `peakMagnitudeDB`, as the full one.
- **11.** Removed: Swift `TapToneAnalysisView+Actions.formatFrequency`; Python `PeakListWidget.save_peaks`.
- **12.** Python's Bin Count reads `QtCore.QLocale().toString(bin_count)` ("32,768"; "32.768" in German), as Swift and
  the web.
- Mutations, each killed: Python's `string` without the 32-bit step (the 0.15 case fails); the web's `string` back
  to `toFixed` (the tie and 32-bit cases fail).
- Builds: Swift macOS and iOS Simulator. Suites: Swift 751, Python 869, web 770. Parity map `--check` clean.

**Run-review steps.** Launch: Xcode scheme `guitar_tap` (macOS; step 5 on an iPhone or the iPhone simulator) ·
`.venv/bin/python -m guitar_tap` · web `npm run build && npm run preview`, clearing the service worker after the
build. Same list per edition, Swift first.

1. Open **Metrics**. → Bin Count reads with your region's separator ("32,768"); Sample Rate and Bandwidth read whole
   hertz the same way ("48,000 Hz", "24,000 Hz"); Frequency Resolution, Frame Rate and Peak Frequency read one decimal in Hz (a peak at or above
   1000 Hz reads in kHz, one decimal).
2. Settings → Audio Input & Calibration. → The sample rate reads the same way ("48,000 Hz") — in Swift both in the
   device list and on the selected device.
3. Settings: Measurement Type Plate; load a plate measurement. → In the results, the sample dimensions read with all
   their decimals ("557.50 mm", "4.85 mm", "208.0 g"). Change one (e.g. thickness to 4.9). → The results recompute.
4. Python only: Settings → **Save Current View**. → The magnitude fields show whole numbers (no decimal point).
5. Swift on iPhone: watch the status line at the bottom while tapping. → The level reads with one decimal ("-45.3 dB").
6. With the plate loaded, look over the results and **Export PDF**. → The speeds, moduli, density, ratios and Gore
   thickness read as before (whole m/s; GPa with two decimals, GLC three; density three).

**Run-review progress.** All three editions pass steps 1–6 (owner, 2026-10-01): "all tests on all platforms done and
they pass." **Run-review complete.**

**F57 — `analysis-quality`: Swift's PDF grades a loaded guitar by the current guitar-type setting, the web's
colours are not the natives', and values outside the bands differ. (CLOSED — all 6 items done and run-reviewed in all three. Commits: Swift `6a5e500`,
Python `0104cf0`, web `ac95203`)**

Production: Swift `Float.decayQuality` / `decayQualityColor` / `tapToneRatioQuality` / `tapToneRatioQualityColor`
(`Views/Utilities/Extensions.swift`), thresholds on `GuitarType.decayThresholds`; Python the same four functions,
thresholds on `GuitarType`; web `dsp/analysisQuality.ts` with its own private threshold table (same values).
Tests call production in all three; none reimplements it. Reviewed again 2026-10-02 at the owner's request: item 2's
first recommendation ignored the backgrounds, items 5 and 6 had none, and item 4 did not say it meant the tests.

| # | item | status |
|---|---|---|
| 1 | Swift's PDF uses the current guitar-type setting, not the measurement's | done |
| 2 | The web's colours differ from the natives' | done |
| 3 | Values outside the bands: Swift "Unknown"/grey, Python and web fall through | done |
| 4 | The test case lists differ | done |
| 5 | Where the thresholds live, and the fallback type, differ | done |
| 6 | Comments | done |

**1. Swift PDF grading** (*checked*). On screen Swift is right: a load sets `TapDisplaySettings.guitarType` to the
measurement's type (`TapToneAnalyzer+MeasurementManagement.swift`), and the live screen grades by the current type.
A PDF exported from the measurement list or detail without loading is not: `PDFReportData.from(measurement:)` holds
the measurement's `guitarType`, but the report grades with the no-argument `decayQuality` / `decayQualityColor`
(`PDFReportGenerator.swift`), which read the current setting — a classical measurement exported while the setting
is flamenco is graded as flamenco. Python and the web grade a PDF by the measurement's type.
- *Recommendation:* the PDF grades with the report's type — `decay.decayQuality(for: data.guitarType)` and its
  colour; F59's PDF tests pin it.
- *Decision (owner, 2026-10-02):* approved.

**2. Colours** (*checked*). Python hard-codes Swift's light-mode system colours; the web uses its own (`#8a8a8e`,
`#e08a00`, `#c0a000`, `#2c9c3c`, `#0a6cd8`, `#d83a30`) while its header says they "match the native apps exactly".
Swift's are semantic: each has a light and a dark value, chosen by the appearance. The backgrounds differ — Swift and
Python draw on a light window, the web on a dark one (`#0b0e13`) — so copying the natives' light values to the web
would not make them look the same (owner, 2026-10-02: "Changing the web to the native colors can only work if the
background is the same"). The precedent: Swift's system blue is mirrored as a light/dark pair — the web's
`--system-blue` (dark by default, light under `prefers-color-scheme: light`), Python's `_system_blue` (by the
window's lightness).

| band | light | dark |
|---|---|---|
| gray | `#8E8E93` | `#8E8E93` |
| orange | `#FF9500` | `#FF9F0A` |
| yellow | `#FFCC00` | `#FFD60A` |
| green | `#34C759` | `#30D158` |
| blue | `#007AFF` | `#0A84FF` |
| red | `#FF3B30` | `#FF453A` |

- *Recommendation:* one table of Apple's system colours with both values, chosen by the background as system blue
  is: on screen, Swift as now, Python by the window's lightness, the web dark by default and light under
  `prefers-color-scheme: light`. A PDF is printed on white, so all three use the light values. To confirm: that
  Swift's PDF renderer draws with the light values when the Mac is in dark mode; if not, it is pinned to light.
- *Decision (owner, 2026-10-02):* "have the PDF use the same color as the app — which should be the same on all
  platforms when printing on light background": the light values, Apple's yellow included, in every PDF; the
  rest as recommended.
- *Found while implementing (2026-10-02):* Swift's system colours are semantic, so they follow the running OS, and
  Apple changed several in its newest release. On this Mac SwiftUI resolves orange to `#FF8D28` / `#FF9230`, blue
  `#0088FF` / `#0091FF`, red `#FF383C` / `#FF4245`, dark gray `#98989D`, dark yellow `#FFD600` — not the table's
  long-standing values, which an older OS still shows and which Python and the web pin. Swift's `.tint(.blue)`
  progress bar likewise no longer matches the pinned system blue of Python and the web.
- *Decision (owner, 2026-10-02):* pin the colours in Swift too — one fixed table in all three (option 1 of three
  presented). "We are not a graphic arts application — we are a scientific application — color is just meant for
  discrimination between values — the exact color is really irrelevant — we just want it consistent." The table's
  long-standing values are the pinned set (what Python and the web's system blue already use); system blue follows
  the same table.

**3. Out of band** (*checked*). Swift returns "Unknown" / grey for a negative or NaN value; Python and the web fall
through — a negative decay reads "Very Short", a NaN decay "Excellent", a NaN ratio "High" in red. Neither occurs in
normal use; untested everywhere.
- *Recommendation:* Swift's behaviour in all three, with cases.
- *Decision (owner, 2026-10-02):* approved.

**4. The test case lists** (the tests, not the application code — all three applications have every band). Swift does
not test the ratio boundaries 1.7 and 2.3 or the upper orange band (2.1–2.3); the web tests three of the five ratio
colours and does not pin its threshold table; no edition tests the flamenco, acoustic or generic thresholds beyond
one 0.5 s case.
- *Recommendation:* one case list, the same in all three: the thresholds of all four guitar types; every label
  boundary; every colour band, decay and ratio; item 3's out-of-band cases; both colour values of item 2.
- *Decision (owner, 2026-10-02):* approved.

**5. Thresholds and fallback.** Swift keeps the thresholds on `GuitarType.decayThresholds`, Python on `GuitarType`;
the web in a private table in `analysisQuality.ts`, apart from its other per-type data (the mode ranges in
`guitarModes.ts`, its counterpart of Swift's `GuitarType`). The fallback type, for a measurement with none: a PDF —
Swift Classical (`PDFReportData.from`), Python Classical (`pdf_report_data_from_measurement`), the web Generic
(`measurementImage.ts`); on screen the ring-out and ratio show only for guitar types, so no fallback is reached.
- *Recommendation:* the web's thresholds move into `guitarModes.ts` beside the mode ranges; a PDF falls back to
  Classical in all three, as Swift; on screen no change.
- *Decision (owner, 2026-10-02):* the thresholds as recommended; "make the fall back Generic in all 3 instead of
  Classical" — Swift's and Python's PDF fall back to Generic, as the web's.
- *Decision, widened (owner, 2026-10-02):* "the fallback for no type should be generic throughout. The change is due
  to there originally being no generic type and classical made sense. When generic was added it should have become
  the default/fallback everywhere but it was not. It is currently the recommended setting to start with." Every
  default and every fallback for a missing or unreadable measurement type or guitar type becomes Generic, in all
  three. Found by survey (2026-10-02):
  - **Swift** — the settings already default to Generic (`TapDisplaySettings.measurementType` / `guitarType`).
    Classical: `PDFReportData.from` (measurement type and guitar type); `ExportableSpectrumChart` — the
    single-measurement export's `snap.measurementType ?? .classical`, and the comparison and multi-tap exports, which
    pass `.classical`; the export chart's `measurementType` defaults to `.acoustic` (property and parameter).
  - **Python** — the settings' measurement type defaults to **Acoustic** (`AppSettings.measurement_type`; Swift's
    is Generic; the stored guitar type already defaults to Generic). The analyzer starts at Classical
    (`_measurement_type`). Classical fallbacks: the PDF data (`pdf_report_data_from_measurement`, measurement and
    guitar type, and its comparison twin); the measurement model's classification (`tap_tone_measurement.py`, three
    places); the analyzer's peak analysis and save path; the canvas's dot filter; the measurement list and detail
    views (`_resolve_guitar_type`); the export chart. `MeasurementType.from_string` already falls back to Generic.
  - **web** — the settings already default to Generic, and so do its guitar-type and PDF fallbacks. The analyzer
    starts at Classical (`measurementType = 'classical'`); `buttonEnablement` falls back to Classical; App passes
    `'classical'` as the stand-in guitar type to the button rule.

**6. Comments.** `analysisQuality.ts:1-7` ("used by the PDF report" — the screen uses it too; "match … exactly" —
false; port history); `analysis-quality.test.ts:10-12` and its closing note (stale, history); `extensions.py:7-8`
(history); `AnalysisQualityTests.swift` ("Python/web port these exactly" — false for the web). The Python tag sits at
the module top, so it also covers `vsep` / `hsep`.
- *Recommendation:* each comment says what the code does. The tag stays: tags are per file, and Swift's
  `Extensions.swift` likewise holds more than this slug (frequency formatting, view helpers), so the files
  correspond.
- *Decision (owner, 2026-10-02):* approved.

*Done — items 1–6 (2026-10-02):*
- **2.** One pinned palette in all three, slug `view/palette` (tested in `test/analysis-quality`): Swift
  `Views/Utilities/Palette.swift` (`Palette.gray` … `Palette.red`, each a `Color` that takes its light or dark value
  by the colour scheme — `NSColor` / `UIColor` dynamic providers over fixed sRGB values), Python
  `views/utilities/palette.py` (`ColorPair`; `on(widget)` takes the value for the window's lightness), web
  `presentation/palette.ts` (`PALETTE`). The quality colours come from it in all three: Swift's
  `decayQualityColor` / `tapToneRatioQualityColor` return `Palette` colours; Python's and the web's return the pair,
  and the caller takes the value for its background — Python `on(self)` on screen, the web `dark` on screen (its
  background is dark, as `qualityColors.ts` does for wood quality), both `light` in the PDF. Swift's PDF renderers
  draw in the light scheme (`.environment(\.colorScheme, .light)` on the report views), so its PDF prints the light
  values whatever the Mac's appearance. System blue: Swift's progress bars and the status-bar phase and peak
  labels use `Palette.blue`; Python's `_system_blue` is `palette.BLUE.on(widget)`; the web's `--system-blue` holds
  the same pair.
- **1.** Swift's PDF grades the ring-out by the report's `guitarType` (`decayQuality(for:)` /
  `decayQualityColor(for:)`).
- **3.** Python and the web return "Unknown" / gray for a negative or NaN decay or ratio, as Swift.
- **4.** The same eight cases in all three: the thresholds of every guitar type; classical decay labels at every
  boundary; each other type at its thresholds; every decay colour; ratio labels at every boundary; every ratio
  colour; negative and NaN; the palette's light and dark values (Swift reads them back through SwiftUI's colour
  resolution in each scheme).
- **5.** The web's decay thresholds moved to `guitarModes.ts` (`decayThresholds(type)`, beside the mode ranges).
  Generic throughout: Swift — `PDFReportData.from` (measurement and guitar type), the chart export's fallback, the
  comparison and multi-tap exports (were Classical), the export chart's default (was Acoustic); Python — the settings'
  measurement-type default (was Acoustic), the analyzer's starting type, the PDF data, the measurement model's
  classification, peak analysis and the save path, the canvas's dot filter, the measurement list and detail, the
  export chart (all were Classical); web — the analyzer's starting type, the button rule's fallback and App's
  stand-in type (were Classical).
- **6.** The comments say what the code does: `analysisQuality.ts`, `analysis-quality.test.ts`, `extensions.py`
  (module docstring and the helpers' header), `AnalysisQualityTests.swift`, and Swift's quality-colour doc
  comments. The Python tag stays at the module top.
- Builds: Swift macOS and iOS Simulator. Suites: Swift 753, Python 871, web 758 (the web file had one test per case; it now has the eight shared cases). Parity map: 112 groups, `--check` clean.

- *Moved to the theme spec (owner, 2026-10-02):* three colour questions found while doing item 2 — the web's
  `--system-blue` follows the OS appearance while its background stays dark; Swift's other semantic `.blue` uses;
  the wood-quality colours, semantic in Swift — are in #2's `THEME-SPEC.md` (§5.1 accent, §5.7 wood quality, §6).

**Run-review steps.** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, clearing the service worker after the build. Same list per edition, Swift first.

1. Settings: Measurement Type Generic; tap a guitar so Ring-Out and Tap Ratio show their quality words. → Each word
   is coloured (gray, orange, yellow, green or blue for Ring-Out; red, orange or green for Tap Ratio), and the
   same word has the same hue in all three editions.
2. **Export PDF** of that result. → The quality words in the Analysis Results boxes are coloured, in the same colours
   in all three editions.
3. Swift only: switch macOS to Dark appearance; **Export PDF** again. → The colours in the PDF are the same as in
   step 2 (the PDF ignores the screen's appearance).
4. Swift only: Settings: Measurement Type Classical; tap and save a measurement whose Ring-Out is between 0.35 and
   0.55 s (it reads "Moderate").
   Settings: Measurement Type Flamenco; Measurements → that measurement → **Export PDF**. → Its Ring-Out reads
   "Moderate", graded as classical (as flamenco it would read "Good").
5. Tap a few times. → The progress bar and the tap/phase label beside it are the same blue in all three editions.

**Run-review progress.** All three editions pass steps 1–5 (owner, 2026-10-02). **Run-review complete.**

**F58 — `wav-dump-folder`: the Swift tests clear the user's real chosen dump folder, cannot reach the
custom-folder branch, and the arm check lives in the model in Swift but in the view in Python. (CLOSED — all 9 items
done and run-reviewed in all three. Commits: Swift `b23445e`, Python `0d2279e`, web `d8aa7c8`)**

Production: Swift `WavDumpFolder` (macOS: a security-scoped bookmark and the chosen path in `UserDefaults`);
Python `wav_dump_folder` (a plain path in QSettings `dump/folder`). The capture's WAV write goes through it in
both. The web downloads the file (`dumpWav.ts`, `@parity none`) — no folder, so "none" is right.

| # | item | status |
|---|---|---|
| 1 | Swift's tests clear the user's real chosen dump folder | done |
| 2 | Swift cannot test the custom-folder branch; its tests pass by construction | done |
| 3 | The arm check: Swift in the model, Python in the view | done |
| 4 | Python "Reveal" re-creates a custom folder that was renamed away | done |
| 5 | Reachability does not check writability; Python's test hard-codes the settings key | done |
| 6 | Comments | done |
| 7 | The folder button: "Show in Finder" in Swift (selects the folder in its parent), "Open Folder" in Python (opens it) | done |
| 8 | A capture's audio could be lost with no sign: dropped when the folder went away mid-sequence (natives); not recorded when saving was turned on mid-sequence (web) | done |
| 9 | A successful save shows nothing on Swift and Python (the web, since item 8, says "Capture audio saved"); a forgotten Dump Capture Audio writes files unnoticed | done |

*Decision (owner, 2026-09-29):* all six as recommended — "Do them all." Items 3 and 4, marked *to confirm*, were
confirmed first: Python has no `request_start_tap_sequence` (New Tap checks in the view, the launch through a
separate `pending_dump_folder_prompt` flag); Python's `reveal_in_finder` calls `mkdir` on the current folder,
Swift's falls back to the default. Item 5: correct the docstrings to what is checked rather than add a
writability check. Swift's custom folder being macOS-only is a platform difference, left as it is.

**1. Real settings cleared** (*checked*): `WavDumpFolderTests.init()` calls `WavDumpFolder.useDefaultFolder()`,
which removes the bookmark and path keys from `UserDefaults.standard`. The tests are hosted in the app, and only
reads are guarded (`hasCustomFolder` is false under test) — not this write. So every Swift test run clears a dump
folder chosen in the real app. The standing rule is that tests never write the owner's real settings.
`MeasurementFileExporter`'s last-used directory also uses `UserDefaults.standard`, but its test only reads.
- *Recommendation:* keep the bookmark and path in `TapDisplaySettings.defaults` (an isolated suite under test), as
  #21 did for the calibration store and the selected input device.

**2. Untestable branch.** Because `hasCustomFolder` is forced false under test, the Swift reachable / current /
acquire tests pass whatever is stored, and the gone-folder case exists only in Python (the Swift header says it is
"checked by hand"). With item 1 the custom-folder branch becomes testable.
- *Recommendation:* the gone-folder and custom-folder cases in both, through the isolated store.

**3. The arm check** (*to confirm*): Swift's `requestStartTapSequence` sets a `@Published` flag the view alerts on
(macOS only); Python's New Tap checks in the view (`_ensure_dump_folder_reachable`), and its launch uses a separate
analyzer flag. Swift offers the custom folder and the check only on macOS; Python on every platform.
- *Recommendation:* Python's check moves into the analyzer's `request_start_tap_sequence`, as Swift's.

**4. Python Reveal** (*to confirm*): `mkdir` on `current_folder()` re-creates a renamed-away custom folder, against
its own `is_reachable` docstring; Swift falls back to the default.
- *Recommendation:* as Swift.

**5.** Both `isReachable` docstrings say "can be written to"; neither checks. Python's gone-folder test writes the
literal `"dump/folder"` into its own `QSettings(...)` rather than through production.

**6. Comments.** Stale "~/Documents/GuitarTap" (Python `tap_tone_analyzer_spectrum_capture.py:160-161`; Swift
`+SpectrumCapture.swift:137`); history in `wav_dump_folder.py:9-10`; the Python fixture credits the wrong sandbox
mechanism.

**7. The folder button** (found writing the run-review steps, 2026-09-30). Swift's Settings folder row has *Show in
Finder*, which opens Finder with the folder selected in its parent (`activateFileViewerSelecting`); Python's has
*Open Folder*, which opens the folder itself (`QDesktopServices.openUrl`). The manual (§8.8) listed them per edition
and called Python's "the same" controls. It is the only place either edition names the file manager.
- *Decision (owner, 2026-09-30):* *Open Folder* in every edition and on every platform — accurate everywhere,
  with no need to name each desktop's file manager. Swift changes to open the folder itself; the code names follow
  (`openFolder` / `open_folder`, `folderToOpen` / `folder_to_open`); the manual describes one desktop control.

**8. A capture's audio lost with no sign** (found at the Swift run-review, step 3, owner, 2026-09-30). The owner turned
saving on while a sequence was listening, the folder was then renamed, and the tap's recording was not saved — only
the log said so ("WAV dump skipped — the chosen folder is no longer reachable"). The arm-time check had passed
before saving was on, and a folder that goes away after arming is never checked: the write was skipped by design,
with nothing shown. The web can lose a recording differently: it recorded a session only if saving was on when the
sequence started, so turning saving on mid-sequence saved nothing (and turning it off mid-sequence still downloaded);
and it released the download's file at the click, which can cut the download off. A browser can also block an
automatic download without the page being told.
- *Decision (owner, 2026-09-30):* a recording is never lost without the user being told. Swift and Python hold a
  recording that can't be written and show the same alert — Change Location… writes it to the chosen folder, Turn
  Off Saving and Cancel let it go. The web records every sequence and reads the setting when the session finishes
  (Swift's mechanism), keeps the file alive after the click, and names the file it handed to the browser.
- *Changed (owner, 2026-10-07, at the Theme (#2) run-review):* recording every sequence kept the session buffer
  growing without limit, even with saving off (a Safari reload was traced to it). Since then a sequence records only
  if Dump Capture Audio is on when the sequence starts — owner: "If it is turned on in the middle of a sequence why
  capture anything until a new sequence is started." All three: Swift `e441f2b`, Python `7d91cb2`, web `3dcc139`.
- *Changed again (owner, 2026-10-14):* turning the setting on before the sequence's first tap saves that sequence —
  see Stage 2 step 9, item (7).

**9. A save is not shown** (owner, 2026-09-30). With Dump Capture Audio on, Swift and Python write each measurement's
WAV with nothing on screen, so a setting left on is easy to forget; since item 8 the web shows "Capture audio saved:
… (Downloads)" above the status bar.
- *Decision (owner, 2026-09-30):* "I like the web message. Do the same in swift and python."

*Done — items 1–9 (2026-09-29/30; items 8–9 also on the web). Swift `b23445e`, Python `0d2279e`, web `d8aa7c8`:*
- **1.** Swift's bookmark and path keys are kept in `TapDisplaySettings.defaults` (an isolated suite under test),
  not `UserDefaults.standard`; `hasCustomFolder` no longer needs its under-test guard. A new
  `setCustomFolder(_:)` stores a folder; `chooseFolder` uses it. Python gains `set_custom_folder` the same way.
- **2.** The same nine cases in both: default folder; no custom folder reachable and current; no custom folder
  by default; acquire with none; a custom folder reachable, current and acquired; renamed — unreachable, acquire
  skips, current still names it; deleted — unreachable, acquire skips; Reveal with a renamed folder opens the
  default and does not re-create it; Use Default forgets the folder. Plus the arm check (item 3): unreachable —
  flagged, not armed; reachable — armed. 11 each. The Swift header's "checked by hand" now covers only the picker.
- **3.** Python `request_start_tap_sequence()` on the analyzer: stops a playing file, checks the folder, emits a
  new `dumpFolderUnreachable` signal and returns without arming, or arms. New Tap, the settings re-arm, the launch
  auto-arm and the prompt's Change Location retry go through it (via `FftCanvas.restart_tap_sequence`); Turn Off
  Saving arms directly (`FftCanvas.start_tap_sequence`), as Swift's calls `startTapSequence`. Both canvas paths
  share the ring-buffer reset. The launch auto-arm is now scheduled on the main loop, as Swift's
  `DispatchQueue.main.async`, so the view is connected when the signal fires; `pending_dump_folder_prompt` is
  gone. The view's prompt is a slot on the signal. The settings re-arm in Python did not check the folder before;
  it does now, as Swift's. The playback type-change test now calls `request_start_tap_sequence()`, as Swift's.
  - *Decision (owner, 2026-09-29):* New Tap's hand reset of view copies moved onto the model's signals, so the
    view follows the model on every arm, as Swift's view does: the comparison curves are removed in the canvas's
    `comparisonChanged(False)` slot (its `clear_comparison` wrapper is gone); the loaded measurement is dropped on
    `measurementComplete(False)`, which only `start_tap_sequence` emits (before, only New Tap dropped it); the
    tap count and bar follow `tapCountChanged` alone (the hand resets in New Tap, Cancel and the settings restart
    are gone); "paused" is read from the analyzer's `detection_state`, as Swift derives it, instead of a stored
    copy.
- **4.** The folder button in both goes through `folderToOpen` / `folder_to_open` (named after item 7): the
  custom folder if reachable, else the default, created if missing; a renamed-away folder is never re-created.
- **5.** Both `isReachable` docstrings say what is checked (still at the chosen path; write permission not checked,
  a failed write is logged). Python's tests store a folder through `set_custom_folder`, not the literal key.
- **6.** Both capture comments name the dump folder instead of `Documents/GuitarTap`; the history line and the
  fixture's sandbox credit are gone.
- **7.** *Open Folder* in both. Swift's button was *Show in Finder* and selected the folder in its parent; it now
  opens the folder itself (`NSWorkspace.shared.open`), as Python's does. Renamed: `revealInFinder` →
  `openFolder`, `folderToReveal` → `folderToOpen` (Python `reveal_in_finder` → `open_folder`,
  `folder_to_reveal` → `folder_to_open`), and the test in both (`…opensTheDefault_notANewOne`). Manual §8.8:
  one desktop bullet for *Open Folder* / *Change…* / *Use Default*, the default folder per build, and the
  fallback to the default when the chosen folder is gone. Swift 11 and Python 11 dump-folder tests pass.
- **8.** Swift and Python: `dumpCaptureWAV` / `_dump_capture_wav` builds a `CaptureRecording` (samples, rate, label,
  capture time — the file is named for when it was captured) and `writeCaptureRecording` / `write_capture_recording`
  writes it, returning whether it did. One that isn't written is appended to `heldCaptureRecordings` /
  `held_capture_recordings` and `captureRecordingHeld` is raised (Swift `@Published`, Python a signal relayed by the
  canvas). The view's alert, "Capture Audio Folder Unavailable" ("The captured audio of this measurement couldn't be
  saved to: …"): Change Location… → choose a folder, then `saveHeldCaptureRecordings` / `save_held_…` (raises the
  alert again if still not written, e.g. the picker was cancelled); Turn Off Saving → setting off and
  `discardHeldCaptureRecordings` / `discard_held_…`; Cancel → discard. Swift holds on macOS only — on iOS the folder
  is the app's own Documents and can't go away; it keeps its log line. Web: `startSessionRecording` records every
  sequence and `finishSessionRecording` reads the setting; `dumpCaptureWav` returns the file name and releases the
  file's URL after 60 s; the analyzer's `captureAudioSaved` drives a dismissible notice above the status bar
  ("Capture audio saved: … (Downloads)"), cleared by a new sequence. Removed as dead: the web engine's
  `dumpCaptureAudio` config and its plumbing (`useAudioEngine`'s `dumpCaptureRef`, App's sync effect), and App's
  unused copy of `dumpCaptureWav`. Tests — Swift and Python: saving turned on after arming saves that sequence; an
  unwritable recording is held and flagged; a held recording is saved to the folder the user then chooses; a
  discarded one is not written (Swift 15, Python 15 dump-folder tests). Web (`test/capture-audio.test.ts`): saving
  turned on mid-sequence saves; turned off mid-sequence saves nothing; the file is named, and dismiss or a new
  sequence clears it; the URL is not released at the click. Mutations, each killed — Swift and Python: drop instead
  of hold; save without writing; record only if saving was on at arming. Web: gate at start; no check at finish;
  release at the click; notice not cleared by a new sequence. Suites: Swift 695, Python 827, web 719.
- **9.** Swift and Python show the web's notice. The analyzer's `captureAudioSaved` / `capture_audio_saved` (Swift
  `@Published`; Python with `captureAudioSavedChanged`, relayed by the canvas) is the file name of the last WAV
  written — set by `writeCaptureRecording` / `write_capture_recording`, so a held recording saved later shows too;
  cleared by `dismissCaptureAudioSaved` / `dismiss_capture_audio_saved` and by a new sequence. The row sits under the
  loaded-settings warning, above the status line: "Capture audio saved: `<file>` (`<folder name>`)" with a dismiss
  button. Swift shows it in the full status bar (macOS, iPad); the iPhone's compact bar is a fixed single row and
  does not. Tests, both: the notice names the file, until dismissed or a new sequence; not shown with saving off;
  a held recording saved later is named (Swift 17, Python 17 dump-folder tests). Mutations, each killed, both: not
  set on a write; not cleared by a new sequence. Suites: Swift 697, Python 829.
- Mutations, each killed: Swift's path comparison removed (renamed case fails); Swift's arm check removed
  (unreachable case fails); Python's folder button on the current folder (its renamed-folder case fails); Python's arm check removed
  (unreachable case fails). Suites: Swift 691 passed, Python 817 passed.

**Run-review steps.** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap`. Swift and Python —
the web has no capture-audio folder. Steps 1–9 in both, Swift first; steps 10–14 exercise Python's view
following the model (item 3's decision) and are run in Python, with Swift as the reference.

The controls are in Settings, below Peak Min: the **Dump Capture Audio** checkbox and, while it is checked, a
"Saved to" folder row with **Open Folder**, **Change…** and **Use Default**. The checkbox takes effect when
Settings is closed with **Done**; the three folder buttons act at once.

1. Settings: check **Dump Capture Audio**; **Change…** → create and choose a new folder `~/Desktop/GTDump`;
   **Done**. → Reopening Settings, the folder row reads "Saved to" `…/Desktop/GTDump`.
2. Settings → **Open Folder**. → Finder opens the `GTDump` folder itself (not its parent with it selected).
3. Close Settings. Set **Taps:** to 1 and tap once, so the measurement completes (New Tap is disabled while
   a sequence is listening). In Finder, rename `GTDump` to `GTDump2`; press **New Tap**. → An alert "Capture
   Audio Folder Unavailable", naming `…/Desktop/GTDump`, with Change Location…, Turn Off Saving and Cancel.
4. **Cancel**. → The screen is unchanged; no new sequence starts.
5. Settings → **Open Folder**. → Finder opens the default folder (`Documents/GuitarTap`
   — on macOS Swift, the app's container Documents); no `GTDump` folder is re-created on the Desktop.
6. Close Settings; **New Tap** → alert → **Change Location…** → choose `GTDump2`. → A sequence starts; tap
   once. → A `.wav` file appears in `GTDump2`.
7. Rename `GTDump2` to `GTDump3` in Finder; quit and relaunch Guitar Tap. → The alert appears at launch.
   **Turn Off Saving**. → A sequence starts; in Settings, **Dump Capture Audio** is unchecked.
8. Settings: check **Dump Capture Audio** again (the chosen folder is still the renamed-away `GTDump2`); set
   Measurement Type Guitar → Plate; **Done**. → The alert appears (Python did not check here before).
   **Cancel**; set Measurement Type back to Guitar; **Done**. → The alert appears again (every re-arm
   checks). **Turn Off Saving**. → A guitar sequence starts; Dump Capture Audio is off for the steps below.
9. Swift only: run the test suite (Product → Test), then open Settings. → The folder chosen in step 6 is
   still shown — the tests no longer clear it.
10. Open two saved guitar measurements in a comparison (select two in the Measurements list → **Compare**);
    then **New Tap**. → The comparison curves go; a fresh sequence starts.
11. Compare two saved guitar measurements again; Settings → Measurement Type Guitar → Plate → **Done**.
    → The comparison curves go. (Set it back to Guitar.)
12. Load a saved guitar measurement; then **Play File** `Recording.wav` (no calibration) to the end;
    **Export PDF**. → The PDF shows the played file's result, not the loaded measurement's.
13. **New Tap**; **Pause**; **Cancel**; **Pause**. → Detection pauses (the status reads paused), rather
    than trying to resume. **Cancel**. → Listening again.
14. Set the **Taps:** stepper (beside New Tap) to 4. Tap twice. → The tap count reads 2 of 4 and the progress
    bar shows it. **Cancel**. → The tap count and the progress bar disappear, and come back at 1 of 4 on the
    next tap. Tap four times. → The measurement completes. **New Tap**. → The tap count and the progress bar
    disappear, and come back at 1 of 4 on the next tap.

Item 8 — a recording that can't be written is held, and the user is asked (Swift and Python):

15. Settings: check **Dump Capture Audio**; **Change…** → create and choose a new folder `~/Desktop/GTDumpW`;
    **Done**. Set **Taps:** to 1; if the measurement is complete, press **New Tap**, so a sequence is listening.
    In Finder, rename `GTDumpW` to `GTDumpW2`. Tap once. → When the measurement completes, an alert "Capture
    Audio Folder Unavailable": the captured audio of this measurement couldn't be saved to `…/Desktop/GTDumpW`.
16. **Change Location…** → choose `GTDumpW2`. → A WAV named for the time of the tap
    (`…_session_Guitar_1tap_<time>.wav`) appears in `GTDumpW2`; no further alert.
17. **New Tap**; rename `GTDumpW2` to `GTDumpW3` in Finder; tap once. → The alert. **Change Location…**, then
    cancel the folder picker. → The alert appears again. **Cancel**. → No WAV is written; the log reads "WAV
    dump discarded by the user — 1 recording(s) not saved".
18. Settings: uncheck **Dump Capture Audio**; **Done**; **New Tap**, so a sequence is listening with saving
    off. Settings: check **Dump Capture Audio**; **Use Default**; **Done**. Tap once. → A WAV for that tap
    appears in the default folder (**Open Folder**).

19. (Swift, Python) Settings: **Dump Capture Audio** on, **Use Default**; **Done**. Complete a measurement. → Under
    the status-bar warnings, "Capture audio saved: `…_session_Guitar_1tap_<time>.wav` (`GuitarTap`)". The × closes
    it. Complete another; **New Tap**. → The notice goes when the new sequence starts.

Web — the save is visible (build: `npm run build && npm run preview`, clearing the service worker after the
build; run in Safari and in Chrome):

**W1.** Settings: check **Dump Capture Audio**; **Done**. Complete a measurement (Taps 1, one tap). → A WAV
    downloads, and a notice above the status bar reads "Capture audio saved: `web_session_Guitar_1tap_….wav`
    (Downloads)". × dismisses it.

**W2.** **New Tap**; tap. → The notice goes at New Tap; after the tap a second WAV arrives in Downloads and the
    notice names it. (If the browser asks to allow multiple downloads, allow it.)

**W3.** Settings: uncheck **Dump Capture Audio**; **Done**. **New Tap**, and don't tap. → A sequence is listening
    with saving off.

**W4.** Without tapping yet: Settings: check **Dump Capture Audio**; **Done**. Now tap. → A WAV downloads for
    that tap, and the notice names it (before, a sequence started with saving off saved nothing).

Turn **Dump Capture Audio** off (or leave it on, with the folder at **Use Default**) when done.

**Run-review progress.** Python passed steps 1–14 (owner, 2026-09-30), after corrections to the steps
themselves (steps 3, 8, 13 and 14; the app's behaviour was right). Swift stopped at step 3, which found item 8.
After items 8–9: Swift from step 1; Python steps 15–19; web W1–W4. **Run-review complete — all three editions pass
(owner, 2026-09-30):** Swift steps 1–19, Python 15–19, web W1–W4.

**F59 — `view/pdf-report`: the PDF report is in no slug and has no tests in any edition, and Python's plate
report lists fewer peaks than Swift's and the web's. (CLOSED — all 7 items done and run-reviewed in all three. Commits:
Swift `c4fdc3d`, Python `c5c6ce9`, web `a4c5ad7`)**

Found while checking F56 (2026-10-01): to show that F56's routing changed no output, each edition wrote the PDF of
every `.guitartap` fixture before and after, through a throwaway harness. That showed the report is untested
everywhere, and it showed the peak-list difference below.

Production: Swift `PDFReportGenerator.swift` (`PDFReportData.from(measurement:)`, `generate(data:)`,
`generateMultiTapReport`, `generateComparison`); Python `tap_analysis_results_view.py` (`pdf_report_data_from_measurement`,
`export_pdf`, `comparison_pdf_report_data_from_measurement`, `export_comparison_pdf`, `export_multi_tap_pdf`); web
`presentation/pdfReport.ts` (`generatePdfReport`, `generateMultiTapPdfReport`) with `presentation/measurementImage.ts`
(`measurementToPdfData`, `multiTapPdfData`). None carries an `@parity` tag. Tests: none.

| # | item | status |
|---|---|---|
| 1 | The PDF report is in no slug — untagged in all three, so the parity map does not see it | done |
| 2 | No edition tests its PDF | done |
| 3 | Python's plate report lists one peak where Swift's and the web's list three; Python's exported chart likewise | done |
| 4 | The web builds a material report's peak rows from the L/C/FLC roles; Swift filters the peaks by the effective selection | done |
| 5 | Which measurements the PDF tests use | done |
| 6 | The three editions lay the report out differently | done |
| 7 | The exported spectrum PNG's resolution and its stated pixels per inch differ | done |

**1. No slug** (*checked*). The report files carry no `@parity` tag, so the sweep — slug by slug — never reaches them,
and `--check` cannot report a difference. Neither does the exported spectrum chart, which the PDF embeds and Export
Spectrum saves: Swift `ExportableSpectrumChart.swift`, Python `exportable_spectrum_chart.py`, web
`presentation/spectrumExport.ts`.
- *Recommendation:* tag the report `view/pdf-report` (tests `test/pdf-report`) — Swift `PDFReportGenerator.swift`;
  Python `tap_analysis_results_view.py` (it holds the report's functions, and also the measurement persistence — a
  file can carry more than one slug); web `pdfReport.ts` and `measurementImage.ts`. Tag the exported chart
  `view/spectrum-export` in the same way, so it too is in the map; its tests are a separate question (its text is
  drawn into an image, which a test cannot read back except on the web).
- *Decision (owner, 2026-10-02):* "I agree with all the recommendations."

**2. No tests.** Owner, 2026-10-01: "I want … a set of tests for PDF files." The F56 harness shows what each edition
needs: Swift renders the report and reads its text with PDFKit; Python renders it headlessly (offscreen Qt) and
needs a text extractor; the web renders it under Node only with a stand-in for the browser's chart canvas and the
build-time version constants, and needs a text extractor. The editions lay the text out differently — line breaks
and order differ (Swift breaks "f_vs" across lines; the web puts several properties on one line) — so the three
texts cannot be compared whole — until item 6 makes the layout one.
- *Recommendation (revised with item 6):*
  - **What is checked.** For each shared fixture, the report's text, line by line, against one ordered list of
    expected lines — the same list in all three, since the layout is the same (item 6). Whitespace within a line is
    normalised, since each edition's PDF reader groups words on a line its own way. The date and the
    "Generated by … (build)" line are not checked. The expected lines are Swift's, once items 3 and 6 are done.
  - **The same cases in all three**, as a row list (fixture → expected strings) with one loop — the `pitch.test.ts`
    pattern — so Stage 2 can move it into shared data unchanged.
  - **Each fixture through the report its kind uses:** single, multi-tap (two pages), comparison.
  - **Text extraction:** Swift PDFKit (built in); Python `pypdf` (pure Python, a test-only dependency); web
    `pdfjs-dist` (Mozilla's PDF.js, a dev-only dependency).
  - **The web's environment:** the version constants defined in the test config; a test helper standing in for
    the browser canvas (it records the text the chart draws and returns an empty image) — a stand-in for the
    browser, not for app code.
- *Decision (owner, 2026-10-02):* "I agree with all the recommendations."

**3. Python's plate peaks** (*checked*). For `plate-umik-1-3-tap-swift-ipad-1784314709.guitartap` the "Detected
Peaks" table lists 36.3, 67.2 and 117.2 Hz in Swift and the web, and only 117.2 Hz in Python. The file's
`selectedPeakIDs` holds one id (117.2 Hz, the fC peak) — the corrupt aggregate an intermittent iPad
phase-transition write leaves. The rule all three already have (`effectiveSelectedPeakIDs` /
`effective_selected_peak_ids` / the web's): a material measurement shows all its peaks, ignoring the saved
selection. Swift's report uses it (`PDFReportData.from`: `measurement.effectiveSelectedPeakIDs`); Python's
`pdf_report_data_from_measurement` reads `m.selected_peak_ids` raw, and so does Python's exported chart
(`exportable_spectrum_chart.py`).
- *Recommendation:* both use `m.effective_selected_peak_ids`, as Swift; item 2's tests pin the peak list.
- *Decision (owner, 2026-10-02):* "I agree with all the recommendations."

**4. The web's material peak rows** (*checked*). Swift's report lists `data.peaks` filtered by the effective
selection and sorted by frequency; for a plate or brace that is the measurement's peaks. The web's
`measurementToPdfData` builds a material report's rows from the selected L / C / FLC peaks and their roles. The
same rows for a well-formed file — but a different mechanism, and a file whose peaks include more than the three
would differ.
- *Recommendation:* the web lists the material peaks the way Swift does — the measurement's peaks by the effective
  selection, sorted, each with its role — so the mechanism is the same.
- *Decision (owner, 2026-10-02):* "I agree with all the recommendations."

**5. Fixtures** (*checked*; first reading corrected by the owner, 2026-10-02: "Look at ALL the tests in the hub").
The seven fixtures vendored into all three editions' test folders are one plate, four single guitar measurements and
two multi-tap guitar measurements — no brace and no comparison. But the hub's `Tests/` holds far more (counted by
measurement, library files included): 20 braces, 26 plates, 3 comparisons (`5-guitar-comparison-1776708138.guitartap`
and two `guitartap-library-*` files), 20 multi-tap guitars and 52 single guitars. `Tests/AllPlatforms/` has the same
brace, plate and DWS 2024 guitar measured on every edition and device — Swift on Mac, iPad and iPhone; Python on
Mac, PC and Linux; the web on Mac — each single and 3-tap. Some measurements already have an exported PDF beside
them (`brace-1774731638.pdf`, `5 tap test.pdf`, `plate-classical-1774731675.pdf`, …), from older builds.
- *Recommendation:* the PDF tests use a set chosen from the hub's `Tests/`, vendored into each edition's fixtures
  as the existing ones are: from `AllPlatforms/`, the brace, plate and guitar — single and 3-tap — as saved by one
  edition, and the same measurement as saved by another edition, so a report is checked against a file from each;
  plus `5-guitar-comparison-1776708138.guitartap` for the comparison report. The exact list is set when the tests
  are written and recorded here.
- *Decision (owner, 2026-10-02):* "I agree with all the recommendations."

**6. The layout** (found while answering the owner, 2026-10-02: "all three editions should lay out the PDF
identically. Is this not possible?"). The F56 captures of the plate report show real differences, not only how each
PDF reader groups text: Python lists Mass first in Sample Dimensions where Swift and the web start with Length; the
web sets the plate properties several to a line ("Young's Modulus (L):6.13 GPa", a space missing) where Swift and
Python set one per line, and places GLC differently; Python's plate report adds the "Three-Tap Measurement Process"
instructions; Python writes "Young’s" with a curly apostrophe. And the fonts differ: Swift draws in Apple's system
font, which Python and the web cannot use.
- *Recommendation:* one layout in all three — Swift's: the same page size and margins, sections in the same order,
  the same labels and punctuation, the same rows and columns, the same font sizes — in Helvetica, which all three
  have (jsPDF's and reportlab's default; on macOS and iOS), so Swift's report changes typeface slightly. Python's
  report and the web's are rebuilt section by section to follow Swift's. With one font, sizes and widths, long text
  (notes, instructions) wraps in the same places but for each library's own wrapping rule. Then item 2's tests
  check one ordered list of lines.
- *Decision (owner, 2026-10-02):* "Yes."
- *Run-review (owner, 2026-10-02):* the text read the same in all three and Swift's and Python's pages looked alike,
  but the web's chart image was shorter and its lines spaced differently — "ignore the chart differences and just
  deal with image height, spacing from swift, and a position check in the tests." The image's height comes from
  Export Spectrum's proportions: Swift renders its export at a fixed 1464 × 1069 pt (a 1400 × 800 chart frame with
  its header and legend; 1188 with the peak summary), whatever the on-screen chart, and its PDF embeds that image at
  the content width. Python's export was 1448 × 1076 / 1192; the web's 1480 × 876 / 986, and its PDF re-rendered the
  chart shorter still. *Recommendation:* the web's and Python's Export Spectrum take Swift's fixed size, and their
  PDFs embed that image, as Swift's. *Decision (owner, 2026-10-02):* "Do your recommendation."

**7. The exported PNG's resolution** (found at run-review step 7, owner, 2026-10-02: "The DPI is different on
swift from the other two … all 3 behave differently when I tell it is zoom all in Preview"). With item 6 the three
PNGs have the same proportions, but not the same pixels or the same stated size: Swift renders at 2×, 2928 × 2376
pixels, and writes 144 pixels per inch in the PNG (`pHYs` 5669 per metre); Python renders the same pixels but
writes 72 (Qt's default), so a viewer that honours the figure shows it twice Swift's size; the web draws at 1×,
1464 × 1188, and writes none (read as 72) — Swift's size, half its detail. The figure is written by each edition,
not taken from the screen or the system, so each edition's file is the same on every machine; macOS Preview and
document editors (Word, Pages, LibreOffice) honour it, most Windows and Linux viewers and browsers show pixels
1:1. The PDFs are unaffected (each scales the image to the page width).
- *Recommendation:* the web and Python write Swift's file: 2928 × 2376 (2928 × 2138 without the peak summary)
  marked 144 pixels per inch. Python sets the mark on its image; the web draws at 2× and adds the mark to the PNG
  after the browser encodes it (the browser's encoder cannot set it).
- *Decision (owner, 2026-10-02):* "Sounds good. Please do so." And: "a test could be created so that checks the
  DPI and resolution."
- *Done (2026-10-02):* Python marks its image 144 pixels per inch (`exportable_spectrum_chart.py`,
  `setDotsPerMeterX/Y` 5669). The web draws its export at 2× (`spectrumExport.ts`, `PIXEL_SCALE`) and marks the PNG
  in `spectrumPng`, which Export Spectrum saves, through a web-only helper that adds the `pHYs` chunk after the
  browser encodes the file (`pngPixelsPerInch.ts`, `@parity none`, with its own test of the chunk, its checksum and
  its replacing an earlier one). The PDF embeds the 2× image, as Swift's. A new test slug, `test/spectrum-export`
  (the export tagged `tests=test/spectrum-export`): `SpectrumExportTests.swift` / `test_spectrum_export.py` /
  `spectrum-export.test.ts`, the same three cases — the iPad plate and a single guitar, 2928 × 2376, and the
  5-guitar comparison, 2928 × 2138 — each at 144 pixels per inch, through the renderer Export Spectrum uses (the
  web reads the pixels from its canvas, since under Node the browser's encoder is a stand-in). Mutation, killed:
  Python marking 72. Parity map: 116 groups, 25 platform-specific, `--check` clean.

*Done — items 1–6 (2026-10-02):*
- **One entry point per edition for a saved measurement's report**, so the tests run production: Swift
  `PDFReportGenerator.report(for:)` (with `multiTapComparisonData(for:)` and `comparisonData(for:)`), which the
  measurement list and detail now call — the three builders that were inline in `MeasurementsListView` and
  `MeasurementDetailView` moved there; Python `export_report_for_measurement(m, path)` (with
  `multi_tap_comparison_pdf_report_data_from_measurement` and `report_basename`), which the measurement list now
  calls — its inline multi-tap builder moved there; web `reportForMeasurement(m)` in `measurementImage.ts`, which
  the measurement list now calls. A measurement with tap entries gets the two-page report in all three, as Swift
  (the web's list and live export required more than one); Python's list asks for the file once, as Swift's.
- **1.** Tagged `view/pdf-report` (tests `test/pdf-report`): Swift `PDFReportGenerator.swift`; Python
  `tap_analysis_results_view.py`; web `pdfReport.ts`, `measurementImage.ts`. Tagged `view/spectrum-export`: Swift
  `ExportableSpectrumChart.swift`, Python `exportable_spectrum_chart.py`, web `spectrumExport.ts`. Parity map: 115
  groups, `--check` clean.
- **2.** `PDFReportTests.swift` / `test_pdf_report.py` / `pdf-report.test.ts`: the same fixtures (a row list and
  one loop), each through `report(for:)` and its counterparts — 17, and 18 with the long-name comparison — read back line by line — PDFKit in Swift, `pypdf` in
  Python (a test dependency, in `requirements-dev.txt` and `pyproject.toml`), `pdfjs-dist` on the web (a dev
  dependency) — and compared with `<fixture>.guitartap.pdf.txt`, Swift's lines, vendored beside the fixtures in all
  three. Each expected line is its page, its height on the page and its words: the height is its baseline's distance
  from the page's top (for a line mixing sizes, the baseline of its largest text, since PDFKit reads such a line as
  one) and must be within 1 pt; the words are compared with whitespace removed, in Unicode compatibility form. The
  measurement's date and the "Generated by" line are checked by position only (`<date>`, `<generated>`). The web's
  test runs the chart's drawing against a canvas stand-in (`test/support/canvasStandIn.ts`), and `vitest.config.ts`
  defines the build-time version constants. Mutations, each killed: Python's report reading the raw selection (the
  iPad plate fails); the web computing the note (the web-saved plate fails); the web's metadata rows 1 pt further
  apart (all 17 fail); Python's gap after the metadata 2 pt larger (all but the comparison, which it does not
  touch).
- **3.** Python's report and its exported chart read `m.effective_selected_peak_ids`; so does the multi-tap
  averaged row, which also read the raw selection.
- **4.** The web's material peak rows are the measurement's peaks in the frequency range by the effective selection,
  sorted, each with its role by id (fL, fC, fLC for a plate; fL for a brace) or "–", as Swift's `peakRoleCell`.
  Every peak row prints the peak's stored note, as Swift (`peak.pitchNote ?? "–"`) — the web computed it, so a file
  saved without notes (an older web build) read differently.
- **5.** Ten measurements from the hub's `Tests/` vendored into all three: from `AllPlatforms/` the brace, plate and
  DWS 2024 guitar, single and 3-tap, as saved by Swift on Mac, and the brace (Python), plate (web) and 3-tap guitar
  (web) as saved by another edition; `5-guitar-comparison-1776708138`. With the seven already shared: 17.
- **6.** Swift's report draws in Helvetica (`pdfFont`: Helvetica, Helvetica-Bold, Helvetica-Oblique). Comparing the
  three editions' reports of all 17 fixtures line by line (read by position) found, and fixed to Swift's layout:
  Python — "Young’s" with a curly apostrophe; the analysis box's "Ideal: 1.9–2.1" at the box's foot rather than
  under the quality words; the comparison page's date as "2026-04-20 18:02" (now the display format), its header
  laid out apart from the main report's (now the same), its range as "75 Hz" (now `formatted_as_frequency`), and its
  date the time of export (now the measurement's, as Swift). Web — the header date on the title's line (now
  top-aligned, as Swift); the comparison page with the single report's header (now "Comparison Report",
  "Comparison:", Notes before Spectra); the meta values 2 pt left of Swift's column; no gap between a property's
  label and value; the analysis box's rows; the footer dated with the measurement's date (now the time of export,
  as Swift).
  Then, from the run-review: the web's and Python's Export Spectrum are a fixed 1464 × 1069 pt (1188 with the peak
  summary), as Swift's — the web's bands resized to add up to it (`spectrumExport.ts`, its unused `width` and
  `chartHeight` options removed); Python's composite set to that size with Swift's 32 pt sides
  (`exportable_spectrum_chart.py`) — and both PDFs embed it at the content width, the dark matte the size of Swift's
  image. Both renderers place text as SwiftUI does: a line exactly its font size tall, the baseline 0.77 × the size
  below its top, wrapped lines a font size apart, and every gap Swift's stack spacing or padding. The web
  (`pdfReport.ts`) places each line by its top (`textAt`); its pagination code, never run since every page grows to
  fit, is removed. Python (`tap_analysis_results_view.py`) uses a Paragraph raised to Swift's baseline (`_text`) in
  tables with no cell padding (`_grid`), its two reports sharing the header, metadata and footer. Also to Swift:
  Python's peak tables lose their row striping, its Sample Dimensions heading is 10 pt bold, a lone analysis box spans
  the width, and the separator after the Gore target stays when there is no target; the web's quality words in the
  analysis boxes are regular weight. And Swift's text never leaves one word alone on a paragraph's last line (Apple's
  push-out line breaking: the plate instructions end "Measures / shear stiffness.", not "Measures shear /
  stiffness."); the web's and Python's wrapping now do the same (`wrapLines`, `_SwiftText.breakLines`). Every line
  of all 17 reports is at Swift's height within 1 pt, with Swift's words.
- *Raised (2026-10-02), not changed:* two differences no fixture reaches. With no ring-out time and no tap ratio,
  Swift's Analysis Results is empty; the web writes "No analysis values available." A long spectrum name on the
  comparison page is cut to one line with "…" in Swift; the web cuts it at a word with no "…", and Python wraps it.
- *Decision (owner, 2026-10-02):* "We need to make swift/python/web the same." The empty analysis: "follow swift"
  — the web drops its sentence. The long name: "I like the wrap idea because it does not loose information while
  swift and web throw information away" — all three wrap it.
- *Recommendation (the wrap's alignment):* a wrapped name makes its row taller. Swift's row is an HStack centred
  vertically, so as it stands the dot and the Air / Top / Back values would sit level with the middle of the name.
  Recommended: top-align the row — the dot and the three values level with the name's first line, as the tap
  instructions' dot sits beside its title — in all three.
- *Decision (owner, 2026-10-02):* "I agree with your top alignment."
- *Done (2026-10-02):* the web's Analysis Results with no box is the heading alone, as Swift's.
  The comparison page's name wraps in all three: Swift's row is top-aligned (`HStack(alignment: .top)`, the dot
  1 pt down to sit on the first line, no line limit); the web wraps it (`wrapLines`) and grows the row; Python
  already wrapped and top-aligned, but over 6 pt more than Swift's column (now the column padded 6 each side). A
  new fixture, `comparison-long-name-1776708138.guitartap` — the 5-guitar comparison with one spectrum named
  "DWS 2024 dreadnought, Adirondack spruce top with scalloped X bracing, Indian rosewood back and sides" — is in
  all three PDF tests: three lines, the values on the first; the other 17 reports are unchanged.
- Builds: Swift macOS and iOS Simulator. Suites: Swift 755 (its PDF test is one test of 18 cases, its export test one of 3), Python 892, web 782, after the run-review work, the long-name case and item 7. Parity map: 116 groups, `--check` clean.
- *Raised (2026-10-02):* the web's footer read "Generated by GuitarTap Web 1.0.3 (build)", Swift's and Python's
  "Generated by GuitarTap 1.0.3 (build)". And Swift's `MeasurementDetailView` has no PDF or export control, so its
  `generatePDFReport` — rewritten in this finding to call `report(for:)` — and its `exportMeasurement` were never
  called, before this finding as after. The owner: "Why does any detail view have export controls? … Are the detail
  views not identical?" — they are: all three are read-only, with Load / Edit / Export / PDF on the list row's menu
  (Swift `MeasurementDetailView.swift`, Python `measurement_detail_view.py`, web `MeasurementDetail.tsx` each say so);
  only Swift carried the unused code.
- *Decision (owner, 2026-10-02):* the footer names the edition — "GuitarTap Web / Python / Swift (as appropriate)";
  Swift's unused export code goes. The owner also asked whether the header date is the measurement's and the footer
  date the report's, in all three: Swift yes; the web's footers showed the measurement's date (fixed above, item 6);
  Python's comparison page — page 2 of a multi-tap report too — showed the measurement's date and no version.
- *Done (2026-10-02):* footers read "Generated by GuitarTap Swift …" (both Swift reports), "GuitarTap
  Python …" (both Python reports), "GuitarTap Web …" (unchanged). Python's comparison footer gives the version and
  the time of export, as its single report's. Swift's `MeasurementDetailView` loses `exportMeasurement`,
  `generatePDFReport` and their `isExporting` / `isGeneratingReport` flags, and its header comment no longer
  describes toolbar Load / Export / PDF actions. Swift's `loadMeasurement()` there was likewise never called (its
  `showingLoadConfirmation` drove nothing); the owner: "Dead code needs buried." — removed with its flag. Run-review step 5 checks the footers.

**Run-review steps.** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, clearing the service worker after the build. Import into each edition from its
own test folder — Swift `GuitarTap/GuitarTapTests/`, Python `guitar_tap/tests/`, web `GuitarTapWeb/test/fixtures/`:
`plate-umik-1-3-tap-swift-ipad-1784314709.guitartap`, `brace-umik-1-swift-mac-1785359411.guitartap`,
`dws-2024-umik-1-3-tap-swift-mac-1785359425.guitartap`, `5-guitar-comparison-1776708138.guitartap` and
`comparison-long-name-1776708138.guitartap`. Same list per edition, Swift first; lay the three PDFs of each step side
by side.

1. Measurements → the iPad plate → **Export PDF Report**. → The three PDFs look the same: header, meta, chart, a
   Detected Peaks table listing 36.3, 67.2 and 117.2 Hz with their roles, the dimensions, the plate properties, the
   instructions. Python lists all three peaks (it listed one).
2. Measurements → the brace → **Export PDF Report**. → The same in all three; "Young's Modulus (E): 10.64 GPa" with
   a straight apostrophe and a gap after the colon.
3. Measurements → the 3-tap DWS 2024 guitar → **Export PDF Report**. → Two pages in all three. Page 1's Ring-Out and
   Tap Ratio boxes read the same, with "Sustain quality" and "Ideal: 1.9–2.1" under the quality words. Page 2 is
   headed "Comparison Report", then "Comparison: DWS 2024 UMIK-1 3 Tap Swift Mac", dated with the measurement's date.
4. Measurements → the 5-guitar comparison → **Export PDF Report**. → The same in all three: "Comparison Report",
   "Comparison:", "Notes:", "Spectra: 5 spectra compared", "Frequency Range: 75.0 Hz – 350.0 Hz", the measurement's
   date in the header.
5. Each PDF's footer. → "Generated by GuitarTap Swift …", "GuitarTap Python …" or "GuitarTap Web …", and the time
   you exported it — on both pages of the 3-tap guitar and on the comparison; the header's date is the
   measurement's.
6. Lay each step's three PDFs side by side at the same zoom. → The chart image is the same height in all three, and
   every line sits at the same height; the plate's last instruction ends "Measures / shear stiffness.".
7. Measurements → the iPad plate → **Export Spectrum**, in each edition. → The three PNGs have the same
   proportions (the chart inside them still differs, as agreed), and Python's chart labels all three peaks, as Swift's
   and the web's (item 3).
8. Measurements → the long-name comparison → **Export PDF Report**. → In all three the second spectrum's name wraps
   over three lines ("… spruce top / with scalloped X bracing, Indian rosewood back / and sides"), its dot and its
   Air / Top / Back values level with the first line; the rows below move down to make room.
9. Measurements → the iPad plate → **Export Spectrum**, in each edition; open each PNG's Get Info (or Preview's
   Inspector). → All three 2928 × 2376 pixels at 144 pixels per inch; in Preview at Actual Size they show at the
   same size.

**Run-review progress.** All three editions passed steps 1–9 (owner, 2026-10-02). Step 7's Python check — the chart
labels all three peaks — was a separate step that an edit of this list displaced below it, so it was not run as a
step; the owner's step-7 PNGs show it (36.3, 67.2 and 117.2 Hz labelled in all three).

*Noticed at run-review (owner, 2026-10-02), not taken up:* the app's comparison table (`view/comparison-results`)
cuts a long spectrum name in all three — Swift and Python with "…", the web after a few letters — with no way to
read the rest but the chart's legend. *Decision (owner, 2026-10-02):* "I do not agree with doing an F60. I think the
web is so narrow that wrapping is useless. There is a way to find the name - look at the graph legend. I think we
ignore it for now."

### S9 — Oracle / baseline infrastructure (5 slugs, classification only)

Status: ✅ **CLOSED 2026-09-20** — scoped by the owner to classification only (what its five slugs are called); the
oracle and baseline machinery is #16, not #17. Settled by two findings at the start of the sweep:
F2 (fixed, Swift `6ead450`, Python `e6e7ddc`, web `363776f`) — `parity-runner`, `self-baseline`,
`parity-oracle` and `oracle-sync` were not tests, and are now `tooling/*`; and F4 (closed, not a finding) —
`test/self-regression` is a test, run by Python and the web and absent from Swift by design, since Swift's baseline
is the oracle. Recorded here 2026-10-02, when Stage 1 closed; it had no section of its own until then.

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

### Stage 2 plan — what is left

The steps to finish Stage 2, in order. Each step's status is kept current here; what was done and decided is in
the progress table and the entries below. Stage 2 is finished when every row says *done* or *nothing to do*.

| # | step | slugs | status |
|---|---|---|---|
| 1 | Group A — same cases in all three, moved as they are | 19 slugs (progress table) | done |
| 2 | Oracle slugs — case list from the oracle | `gated-fft`, `file-playback` | done |
| 3 | B — `pitch` | `pitch` | done |
| 4 | B — `plate` and `brace` | `plate`, `brace` | done |
| 5 | B — `dsp` | `dsp` | done — identical in all three; peak analysis and the live FFT are analyzer methods in all three; one live-spectrum length and bin 0; run-reviewed (Swift `f082a55`, Python `180b595`, web `7fef7a6`) |
| 6 | B — `peaks` (synthetic cases and averaging) | `peaks` | done — identical in all three; the web's averaging, auto-selection, guitar type and saves are Swift's; run-reviewed (Swift `7855a3d`, Python `8837a28`, web `8f31b91`) |
| 7 | B — `mode-colors` | `mode-colors` | done — with Issue #2 (theme) step 4: each mode's colour role is a case in `theme.json` (`modeRoles`), run in all three (Swift `382cfeb`, Python `450e1ce`, web `329a10e`); closed 2026-10-07 |
| 8 | B — `mic-selection` (the web has no pure `inputDeviceToUse` — needs your decision) | `mic-selection` | done — `mic-selection.json`, MS1–MS5: Swift and Python run all five against their function; the web runs MS1–MS3 through its engine and a fake browser; MS4 and MS5 are marked Swift and Python only, because the browser always resolves a default input itself. *Decision (owner, 2026-10-14):* option 1 — not giving the web Swift's mechanism, which would open the default microphone first (a Bluetooth headset audibly switching to call mode). Swift `3a8022b`, Python `3c513c1`, web `ee74021` |
| 9 | B — `measurement-codable` | `measurement-codable` | done — the whole slug moves to shared definitions, in two parts (owner, 2026-10-14: same inputs, same guitar type, same organisation; Swift's inputs win). **9a** done — run-reviewed by the owner in all three, 2026-10-14; Swift `f02b9f7`, Python `5db7f73`, web `4e41e8c`: `measurement-codable.json` — tap-tone ratio TR1–TR9 (TR4–TR7 and TR9 also checked against the live analyzer), the label each peak is written with and displayed with ML1–ML4, the selection heal on decode SH1–SH5 — classical, Swift's values, identical in all three. Found and fixed with it, the same way in all three (owner's decisions, 2026-10-14): (1) a saved measurement's modes and labels come from one model function (`autoModes` / `peakModeLabels`), classified among ALL its peaks with its own guitar type, else Generic — the writer, the Details pane, the ratio, the selection heal and every saved-measurement export (report table, chart image) read it; the Details panes and the saved exports had classified only the shown peaks, and Swift used the app's guitar type; (2) the multi-tap comparison entries are built once, on the measurement model (`multiTapComparisonEntries`) — the on-screen overlay, the live report and the saved report all build from a measurement (`makeMeasurement`), where each edition had three builders; (3) Select None round-trips: an empty selection is written as `[]` and read as nothing selected (Swift and Python wrote nothing and the read healed it to the auto-selection; Python and the web read `[]` as all peaks); (4) the web's measurement logic moved from `fromLive.ts` to the model (`types.ts`), its heals to the reader (`decode.ts`), its comparison building and restore into the analyzer, and its saved exports read the measurement directly, as Swift's renderers do — `fromLive.ts` is gone; Python's measurement list uses the measurement's own ratio. (5) found in the owner's run-review, 2026-10-14: the web classified a loaded measurement's peaks under the app's current guitar type before applying the measurement's own (Air shown as Unknown after the app was set to Acoustic) — it now applies the measurement's type first, as Swift and Python do (test PR46 in all three); (6) found in the run-review: Python's averaged Air read 88.3 Hz where Swift and the web read 88.4 — at launch Python applied the calibration at each bin's frequency rounded down to a whole hertz (`rate // fft_size` in the chart view), up to 1.06 dB off near 11 Hz and ~0.002 dB at 88 Hz. Python's calibration is now owned by its engine, as Swift's and the web's are: the engine takes the device's calibration when it selects the device (launch included), computes the per-bin corrections from its own exact bin frequencies and recomputes them when the sample rate changes; the analyzer keeps no copy. The web engine's cached corrections did not follow a sample-rate change; now they do. New shared `test/calibration` (CAL1, CAL2) on all three engines; (7) found in the run-review: Swift and Python did not save a live multi-tap session recording. Not a defect — a logging run showed each sequence had started with Dump Capture Audio off and the setting was turned on before tapping; since the owner's 2026-10-07 decision (F58 item 8) all three read the setting only when a sequence starts. A sequence starts at launch, on New Tap, on Cancel (which starts a fresh sequence exactly as New Tap does), on a measurement-type change that needs one, and on Play File — the setting is read at each of these, not only at launch and New Tap. Decision (owner, 2026-10-14): turning the setting on before the sequence's first tap saves that sequence, as a user would expect; turned on after the first tap it takes effect when the next sequence starts; turned off at any point, the sequence is not saved. The bounded 2 s pre-roll is now kept with the setting off too (owner chose this over recording from the moment the setting is turned on), so a sequence saved this way has the same recording as one started with the setting on; with the setting off it is dropped at the first tap, so the 2026-10-07 bound on memory still holds. The same way in all three: the analyzer applies a change of the setting (`applyDumpCaptureAudioSetting` / `apply_dump_capture_audio_setting`; Swift and Python from Settings and both "Turn Off Saving" buttons, the web from `setSettings`); `maintainSessionRecording` drops the pre-roll at the first tap when the sequence is not saved; resume after a pause keeps the pre-roll; the capture probe's records (the diagnostic `…-capture-probe.json` beside the WAV) follow the recording — found in the owner's run-review, where a sequence saved this way had its WAV but no probe file (a probe-only test in all three, run while the probe is switched on). New shared cases `session-pre-roll.json` SR1–SR11 in `test/session-pre-roll` (a mutation restoring "nothing kept with the setting off" fails SR1, SR2, SR5, SR6 and SR11 in all three); the 1.0.3 release-note line updated in all three **9b** done — Swift `9cd3c38`, Python `3310195`, web `84196de`: the file format in `measurement-codable.json`, Swift's values, identical in all three — `snapshotBytes` SB1–SB2 (the spectrum's base64 float32 text, exact), `decode` DC1–DC10 (legacy `tapLocation` / `peakThreshold`, a missing sample rate, the legacy plain-array snapshot, overrides in the legacy object and current flat forms, an `auto` override dropped, no pitch, no visibility), `write` WR1–WR4 (no legacy key written, unset optionals omitted, Float fields as their shortest float32 text from float64 input, overrides as assigned entries), and `fixtures` — the 18 real files every edition carries, each read to its facts, its overrides naming peaks it contains, written with no legacy key and its spectrum bytes unchanged, and read back the same (three files saved before the `findPeaks` duplicate fix read one peak fewer, by design). All three passed with no writer change. Mutations, each caught: Swift writing the plain arrays too (SB1, SB2), Python skipping the float32 step (WR3 — which first passed it, because its inputs were already short; now float64 expansions), the web dropping the `peakThreshold` fallback (DC2). The code tests these replace are gone in all three (Swift 14, Python 10, web 7); model-only facts and the Contreras fixture's own checks stay as matched code. Python's comparison-entry codec tests moved to `test/comparison` (`test_comparison_mode.py`), where Swift and the web keep theirs (owner, 2026-10-14). |
| 10 | B — F18's three | `import-persistence`, `peak-selection-persistence`, `material-measurement-inputs` | **done** 2026-10-15 — owner, 2026-10-14: one shared case file per slug (the union of the editions' cases, as step scripts, Swift's values); a case about something only one edition has is marked for that edition; the code tests the cases replace are removed. **`peak-selection-persistence`** done — Swift `6407014`, Python `8c2914e`, web `5c720fc`: `peak-selection-persistence.json` — PSP1–PSP3, a measurement saved automatic, manual or with no flag is loaded, and whether it loads as manual (which enables the Reset to automatic selection wand), whether the saved selection is kept, and that the wand makes it automatic over all its peaks; PSP4–PSP6, the flag written and read back (omitted when unset). Found doing it: the old tests — and their comments — pinned "an automatic selection re-runs auto-selection when Peak Min changes", the rule from before Peak Min became display-only; they passed only by calling `recalculateFrozenPeaksIfNeeded` directly on a loaded measurement, a path no app reaches (its one caller, Re-analyze, drops the loaded peaks first), and the web's copy of that branch skipped the selection step Swift's ran. Decision (owner, 2026-10-14): the cases test what the app does (the wand), and the loaded-measurement branch of `recalculateFrozenPeaksIfNeeded` is removed in all three. In `test/frozen-peak-recalc` with it: PR03, PR04, PR07, PR08, PR09 now set Peak Min on the measurement's peaks (the app's path) instead of calling the recalculation; PR06 and PR31 (the branch itself) removed; PR11 and PR16 on the live path; Swift's PR20, PR23, PR26, PR28 and Python's PR28 moved to the live path (a re-detection), where the web and Python already tested them; PR21 and PR24 (a hidden peak keeps its label and its name across a re-detection) rewritten on the live path and added to Python and the web (mutation: snapshotting against the displayed peaks fails PR21, PR24 and PR19). **Found next, and fixed before the rest of step 10 (owner, 2026-10-14): loading a measurement is not done the same way.** Swift's `loadMeasurement` does nearly the whole load in the model; Python's view does a second round after it, and the web's `App` finishes it by copying the model's values into its settings store and pushing them back. The three load paths were traced, model against view, step by step:<br>1. Saved peaks into the durable set — Swift: model. Python: the model stores `loaded_measurement_peaks`, the VIEW sets `all_peaks` from them (`_emit_loaded_peaks_at_threshold`, twice when there is no spectrum). Web: model (via `restoreSnapshot`); `App` holds an unused copy, and the property is read by nothing after the load.<br>2. The analyzer's own measurement type — Swift: model. Python: settings written by the model, but `analyzer._measurement_type` set only by the VIEW (`_apply_measurement_type_to_ui` → canvas). Web: model, then `App` pushes settings back into the analyzer.<br>3. Restored settings and their saved values (Peak Min, threshold, guitar type, annotation mode, Show Unknown Modes) — Swift: model, except Show Unknown Modes, restored only by the VIEW, which also repeats three of the model's writes. Python: model; the view's slider updates write the same values back. Web: the model publishes `loadedSettings`; `App` copies them into the settings store (and so localStorage) and pushes Peak Min, threshold and annotation mode back into the analyzer.<br>4. Plate/brace phase spectra — Swift, web: model. Python: model, then the VIEW rebuilds and sets them again, with a different plate/brace gate.<br>5. Plate/brace frozen spectrum — Swift, web: model clears it. Python: the VIEW refills it (crosshair).<br>6. Peak list selection and mode labels — Swift, web: the view reads the model. Python: the VIEW recomputes them from the file and forces "manual" on its list model.<br>7. One-shot `loaded*` values — Swift: the VIEW clears them 0.1 s later. Python, web: none.<br>8. A saved comparison record — Swift, Python: model; neither stops detection or the session recording; Python's view load handler then runs anyway. Web: model, and it does stop both.<br>9. A new comparison from a multi-select — Swift: model. Python: the canvas clears the curves, then the model. Web: `App` sequences clear-peaks, clear-result, load.<br>10. Chart axis range — model publishes it, the view holds it, in all three (the same pattern; it stays).<br>Defects seen in the trace (read, not run): Python — a saved comparison loaded after a guitar measurement puts the previous peaks back into the durable set (row 8); web — a plate/brace load's banner shows the current threshold as the loaded one (the material load restores only the type and FLC); web — a new comparison keeps the previous measurement's microphone in the results line; all three — a file with no microphone id leaves an earlier microphone warning showing; all three — the peaks are projected and the ring-out quality labelled under the previous type and Peak Min before the new ones are restored; Swift — a file with no saved label positions keeps the previous measurement's, and two view handlers for material peak ids are dead. The target: `loadMeasurement` / `loadComparison` do the whole load in the model in all three — peaks, type, every restored setting and its saved value, phase and frozen spectra, selection, stopping detection — and the views only display it (keeping the chart range as now); the loaded-peaks property goes in all three; the defects are fixed in the same pass. Effect on the shared cases until then: a case that loads a measurement calls the model's `loadMeasurement`, which in Python and the web is only part of the load — so a load case can pass in all three while the apps differ (Python's test helpers already set `analyzer._measurement_type` by hand, as its view does). Pure-logic cases are unaffected. **Load path — done: Swift `fb5b0e6`, Python `9ecaf7b`, web `6aba00a`; run-review passed (steps under "Load path run-review" below) (owner decisions 2026-10-15):** (1) the web gets a settings store outside React (`settingsStore.ts`, the same localStorage key and JSON layout — no migration), which the analyzer reads and a load writes, as Swift's analyzer and load use TapDisplaySettings; (2) Swift keeps `loadedAxisRange` as the view's signal (applied on each new load, not replayed when the view subscribes) and the view never writes the model; (3) loading a saved comparison stops detection and the session recording in all three; (4) shared cases in a new slug, `test/measurement-load` (`measurement-load.json`, LD1–LD8; LD7 and LD8 from the run-review); and, the web's Settings type change done Swift's way — Settings' Done calls the model (`changeMeasurementType`), a load never does. Done: Swift — the load applies and saves Show Unknown Modes itself, applies the type and Peak Min before the peaks, clears earlier label positions and microphone warning, and the view's `loaded*` handlers (bar the axis range), `loadedMeasurementPeaks`, four other `loaded*` values and dead peak-id handlers are gone. Python — `load_measurement` does the whole load (it now restores Show Unknown Modes, which it had only logged), ends by announcing the peaks to show, and restores Peak Min and the tap threshold exactly (it rounded them to whole dB); the analyzer's measurement type IS the saved setting (one store, as Swift; the view no longer keeps a second in step); the view's load handler only updates widgets; the crosshair snaps to plate/brace curves as Swift's does; `loaded_measurement_peaks` gone; Re-analyze no longer disables itself after one press (found here). Web — the store above; the analyzer applies the settings itself; a load writes the measurement's settings (a plate/brace its threshold too, fixing the banner; settings a file lacks are no longer reset to defaults, as Swift); a new comparison is one model call that clears the previous result and microphone line; `loadedPeaks`, `loadedSettings` and App's copying effects gone. LD1–LD8 pass in all three; mutations caught: Swift label positions LD2 and comparison microphone LD7, Python saved-comparison detection LD6, web microphone warning LD3 and load highlight LD8. **`material-measurement-inputs`** done (2026-10-15) — Swift `aca3fc6`, Python `3174bbd`, web `2b25826`: `material-measurement-inputs.json` — M1–M5, a measurement's own dimensions (Store B) taken from the Settings defaults when it completes (plate; none for a guitar; none during a load; the completion transition only, not a repeated assignment; a brace's own defaults); M6–M7, a plate or brace load takes the file's dimensions and leaves the Settings defaults untouched; M8, a save writes the measurement's own dimensions; M9–M12, notes on load (kept; empty, spaces-only and surrounding spaces normalized); M13, a plate file without body size, stiffness preset or custom stiffness takes them from Settings. Before, the editions shared 6 tests by count with almost none in common: M4, M5 and M8 ran only in the web, and the web ran M5, M6 and M8 on helpers rather than the analyzer, and none of M9–M12 (owner, 2026-10-15: M4, M5, M8 shared, run in all three). Found doing it, decided (owner, 2026-10-15) and fixed: a load's notes and name were normalized three ways — Swift dropped only empty text, Python also spaces-only text but kept surrounding spaces, the web neither — while each edition's own `normalizedNotes` / `normalizedName` (used by Save and Edit) trims and drops blank; the load now uses them in all three (name cases LD9–LD11 in `measurement-load.json`). And the web filled a file's missing body size, stiffness preset and custom stiffness with 0 and Steel String Top, where Swift and Python (load and saved-measurement PDF) use the Settings values; the web now does too, on load and in its saved-measurement image and report (M13). Mutations caught: Swift notes M11–M12, Python save ignoring Store B M8 and loaded name LD11, web completion-transition guard M4 and missing-field fallback M13. **`import-persistence`** done (2026-10-15) — Swift `1f7f986`, Python `8e6bfc3`, web `fcc9741`: `import-persistence.json` — IP1–IP3, an import (through the app's `importAndLoadMeasurements`) adds its measurements to the library and to storage, in order, keeping the file's id, and a re-import appends a second entry sharing it; IP4–IP5, editing an entry changes only that entry, in its place, with a new id, and editing one of two duplicates leaves the other its shared id; IP6, a save appends; IP9, Delete All empties the library and its saved copy; IP7 (natives only — they address entries by position, the web by row key, deferred to the sort work) an edit of a missing entry changes nothing; IP8 (web only) the row key never reaches an exported file; IM1–IM3, the import message. Before, the editions shared 3 cases by number with different content: the natives' IP1 and IP3 tested `importMeasurements(json:)` / `import_measurements(json_str)`, which no app path calls; decision (owner, 2026-10-15): test through the app's import, and those two functions are removed. Found running the full Swift suite, decided (owner, 2026-10-15) and fixed: Swift wrote the library on a concurrent queue, so two quick changes (an import, then an edit) could land out of order and leave the older library on disk — it now writes on one serial queue, in order, as Python (synchronous) and the web (IndexedDB transactions) already do; and the Swift test shared the per-process library file with two other suites that save in parallel — an analyzer now has a `libraryFileURL` (the usual file by default), and each case uses its own. Mutations caught: Swift edit not persisted IP4–IP5, Python import replacing the library IP2/IP5/IP6, web a save minting a new row key IP4–IP5. Also found, decided (owner, 2026-10-15) and fixed: the web's Measurements panel did the library's edit, delete and Delete All itself (amend, then store calls), where Swift's and Python's are the analyzer's — the web analyzer now has `updateMeasurement`, `deleteMeasurement` and `deleteAllMeasurements`, which the panel calls; and Swift's Delete All was the view clearing `savedMeasurements` without saving, so the measurements came back at the next launch unless another change was saved first — Swift's analyzer now has `deleteAllMeasurements()` (clear and save, as Python's `delete_all_measurements`), which the view calls; IP9 (a mutation dropping its save fails it). |
| 11 | C — scenario slugs: they stay as code, so what makes their tests the same in all three is **not yet decided** | `scenario-trace`, `tap-decisions`, `state-invariants`, `start-tap-race`, `session-pre-roll`, `tap-count-change`, `tap-progress`, `status-message`, `annotation-state`, `audio-clock-timers`, `comparison`, `frozen-peak-recalc`, `notification`, `measurement-complete`, `effective-peak-id`, and `display-range`'s scenario tests and `decay-tracking`'s DK9 | done — batches A, B and C (C1–C7) — see **Step 11 — scenario slugs** below |
| 12 | Cannot be shared — per-machine baselines, random draws, the filesystem | `self-regression`, `uuid-case`, `wav-dump-folder` | nothing to do |
| 13 | Parity links — every test slug linked to the code it tests, every model file in a group | all | done (Swift 3543ac7, Python bb752af, web 0296fd0) — see **Step 13 — parity links** below |
| 14 | Close Stage 2 and #17 | — | to do — the open items below first |

**Open before closing (2026-10-16).** Raised along the way, not yet decided or done:

| # | item | status |
|---|---|---|
| O1 | Id case on decode: Swift's ids are `UUID`s, so it reads an id in any case and writes it uppercase; Python and the web keep the string as the file holds it and compare ids as strings. A file whose ids differ only in case — `selectedPeakIDs` lowercase against uppercase peak ids, say — matches in Swift and not in the others (recorded in Python's `test_uuid_case.py` docstring, tracked nowhere). Surveyed and decided (2026-10-16): UUIDs are UUIDs in all three, one rule — plan O1.1–O1.10 below | done — run-reviewed in all three (2026-10-17); Swift 050217d, Python f85eeff, web 08e35bc |
| O2 | The web names the armed prompt `restingPrompt()`; Swift and Python `armedPrompt()` / `_armed_prompt()` (C7). Widened (owner, 2026-10-17): the status-derivation functions the same in structure, not only behaviour, and how the web analyzer reads its settings — section **O2** below | done — run-reviewed in all three (2026-10-17); Swift e59469e, Python 02d1227, web 379faa2 |
| O3 | Two slugs break the area naming: `dead-input` (no area; its group holds test files) and `models/capture-probe` (`models/` for `model/`) — renames in all three (step 13). Decided (owner, 2026-10-17: "1 as proposed 2 (b)"): `dead-input` split into `audio/dead-input tests=test/dead-input-threshold` (DeadInput.swift, dead_input.py, deadInput.ts) and `test/dead-input-threshold` (the three test files; the web and Python "— paired with …" notes moved off the tag line); `models/capture-probe` is `util/capture-probe` — a diagnostic in the app, like `util/test-sandbox`, in an area not expected to have tests (as `model/capture-probe` it would have been a coverage gap whose only evidence, the probe-only `session-pre-roll` test, is skipped while the probe is off). Tag lines only; `--check` current, 143 groups; `audio/dead-input` reads tests; the dead-input tests pass (Python 16, web 16) | done (2026-10-17); Swift 626f023, Python 0e311c7, web 8c0dd71 |
| O4 | `audio/buffer-watchdog` has no test (the map's one coverage gap, as step 13 left it; the `--check` runs piped through `tail` hid the warning). The decision is tested — `watchdogDecision` / `watchdog_decision` in the shared `dead-input-threshold` tests, under the `dead-input` group, not linked to this one — but not the tick around it: the guards (not running, a file playing, already recovering, the 4 s start-up grace), the attempt count and 0.5 / 1 / 2 / 4 s backoff, giving up but still watching, a healthy tick clearing the warning, the count and the given-up latch, the dead-input warning's edges, and a restart not counting as signal seen. Testable: the tick reads the system clock directly and runs on a real 1 s timer, and its recovery restarts the audio — a test would give it the analyzer's `WallClock` (C6), call the tick and stand in for the restart. Python already calls the tick directly (SR3, SR6 in `stream-restart-coordination`). Seen, not checked: Swift's tick also handles a wrong-device decision (`wrongDevice`, `wrongDeviceExhausted`) and clears an earlier permission-denied determination on a healthy tick; Python's and the web's do neither | open |

**O1 survey (2026-10-16).** Where lowercase ids come from: Python minted `str(uuid.uuid4())` — lowercase — until
`8a1f2eb` (2026-09-20), so files and libraries saved by the shipped Python 1.0.0–1.0.2 hold lowercase ids; Swift and the
web have always written uppercase. How each edition reads them:

- **Swift**: every id is a `UUID`. Decoding accepts either case, and the ids compare as values, so case never matters;
  it writes them back uppercase. (An id that is not a UUID at all fails the decode — the ports accept any string.)
- **Python**: ids stay strings as the file has them, except that label-offset keys are uppercased at decode
  (`from_dict`), and the plate/brace peak ids are matched uppercased at load; selections, mode names and tap entries
  compare exactly. So inside Python a 1.0.x measurement has lowercase peak ids and uppercase offset keys. Read, not
  run: an export straight from a saved measurement (`exportable_spectrum_chart`, `annotation_positions.get(peak_id)`)
  finds no offsets for those peaks, so dragged labels go back to their default positions; re-saving such a measurement
  without loading it writes the mixed case into the file; and the duplicate-peak heal does not drop a removed peak's
  offset (its key is uppercased, the removed id is not).
- **Web**: ids stay strings as the file has them and compare exactly. A consistently lowercase file works; a mixed-case
  one — such as Python's re-save above — loses whichever selections, names and label positions differ in case.

Options: (A) every id uppercased when read, in Python and the web, as Swift's `UUID` does in effect — the scattered
uppercasing in Python goes — with shared `measurement-codable` cases: a lowercase file and a mixed-case file read with
their selection, names and label positions intact, and written back uppercase. (B) Compare ids without regard to case
wherever they are compared — many places, easy to miss one. Recommended: (A). Not proposed: refusing a non-UUID id as
Swift does.

**The standard.** A UUID is a 128-bit number; its string is hexadecimal, and RFC 4122 §3 (kept by RFC 9562) says the
digits a–f "are output as lower case characters and are case insensitive on input". So `3f2a…` and `3F2A…` are the same
id, and a reader must accept both. Swift, comparing `UUID` values, follows it; Python and the web, comparing strings,
do not. (Swift writes uppercase — Apple's `uuidString` — against the RFC's lowercase recommendation for output; the
ports copied it. Allowed for any reader that reads UUIDs as UUIDs.)

**Swift and an id that is not a UUID — three behaviours today.** The measurement `id`, a peak `id`, `selectedPeakIDs`,
the plate/brace peak ids and the tap-entry ids: the decode throws, and the whole file fails (opening a `.guitartap`
reports an error). `peakModeOverrides`: the legacy reader drops just the bad entries, silently. `peakAnnotationOffsets`:
every label position of that measurement is dropped, silently (`try?`). The last two are lenient by accident — code
written to tolerate older formats that also swallows bad ids. And if the library (`saved_measurements.json`) fails to
decode, Swift logs it and starts with an empty library, which the next save writes over the file — read, not run.

**Decided (owner, 2026-10-16): one rule in all three, and UUIDs are UUIDs in all three — not strings.** Plan, for the
owner's approval before the build:

| # | item | status |
|---|---|---|
| O1.1 | Scan this Mac: the Swift and Python libraries, the web library (exported to Downloads by the owner), every `.guitartap` — does anything fail the rule (an id that is not a strict UUID)? | done — none fails (below) |
| O1.2 | History: did any version of any edition ever write an id that is not a UUID (empty, missing, a placeholder)? If none did, no customer's file fails the rule unless edited by hand | done — none did (below) |
| O1.3 | The library rule, all three, first (owner, 2026-10-16: yes): a library that fails to load is never overwritten, and the user is told. Swift and Python (one file): rename it `saved_measurements-unreadable-<date>.json` beside it, start empty, tell the user once where it was kept and that fixing it and renaming it back restores it. The web (one IndexedDB record per measurement): skip the unreadable records and leave them in storage, tell the user how many, offer Delete them — a browser user cannot edit them. Committed on its own after its own run-review; O1.4–O1.9 together after | built (2026-10-17, uncommitted) — below |
| O1.4 | Python: every id a `uuid.UUID` — peaks, measurements, tap and comparison entries, selections, mode-name and label-position keys, plate/brace peak ids, calibration ids (~25 source files; Qt signals carry the object). Read parses, either case; written uppercase; `new_uuid()` returns a UUID; the scattered `.upper()` go | built (2026-10-17, uncommitted) — below; calibration ids too (Open 1) |
| O1.5 | Web: a branded `Uuid` — a canonical uppercase string at run time (a UUID object would break `Map`/`Set` keys, which compare objects by identity, and React keys), made only by `parseUuid()` (validates, uppercases) or `newId()`; the compiler finds every raw string used as an id (~18 source files); the IndexedDB library parsed on load | built (2026-10-17, uncommitted) — below; calibration ids too (Open 1) |
| O1.6 | The strict form in Python and the web, as Swift's `UUID(uuidString:)`: 36 characters, hyphenated 8-4-4-4-12, either case. Python's `uuid.UUID()` alone also takes braces, `urn:uuid:` and unhyphenated hex — too lenient | built (2026-10-17, uncommitted) — below |
| O1.7 | Swift: the mode-name and label-position readers stop swallowing bad ids — one rule for every field; otherwise unchanged | built (2026-10-17, uncommitted) — below |
| O1.8 | Tests: the ~80 made-up ids (`"air"`, `"top"`, `"p1"` …) in 7 Python and web test files and the 36 in one shared case file become UUIDs; new shared `measurement-codable` cases — a lowercase file, a mixed-case file, an invalid id in each id field (rejected); `uuid-case` adjusted | built (2026-10-17, uncommitted) — below |
| O1.9 | Docs: App. B states the rule — ids are RFC 9562 UUIDs, read in either case, written uppercase, an invalid one rejects the file (reaches shipped users through the online manual) | written (2026-10-17, uncommitted) — below |
| O1.10 | Run-review: load, save, export, comparison and the library in all three; a Python 1.0.x file, a mixed-case file, a file with a bad id | done — all three, steps 1–9 with step 9 as rewritten (owner, 2026-10-17) |

**O1.1 scan (2026-10-16, read-only).** Every id in every measurement — the measurement `id`, peak ids, `selectedPeakIDs`,
the plate/brace peak ids, the mode-name and label-position keys, tap-entry ids, peaks and selections, comparison-entry
ids and `sourceMeasurementID` — against the strict form. Swift's library: 101 measurements, all ids valid and uppercase.
Python's library: 67 measurements, all valid; lowercase ids from before 2026-09-20; two measurements ("Test of UUID",
2026-09-21) have an uppercase measurement id over lowercase peak ids — every reference to a peak in the same case as the
peak, so nothing breaks. The web library (exported by the owner): 31 measurements, all valid and uppercase. Every
`.guitartap` Spotlight or a search of the home folder finds — 443 files, 524 measurements: none unreadable, none with an
invalid id, none mixing case within a reference; 31 hold lowercase ids (old Python).

**O1.2 history (2026-10-16).** Swift: every stored id has always been a `UUID` (the other `id: String` in its history are
enum and test-sandbox ids, never written to a file). Python: minted `str(uuid.uuid4())` from the start — valid, lowercase
— until `8a1f2eb` (2026-09-20) made it uppercase; the empty-string ids in its history are view-widget defaults, never
written. The web: minted with `crypto.randomUUID()` from the start, uppercased since `fbd2231` (2026-09-21). So no
edition ever wrote an id that is not a UUID; a customer's file fails the rule only if edited by hand or written by other
software. Found on the way, covered by the rule: a MISSING id is handled three ways today — Swift fails the decode,
Python mints a new id, and the web reads it as `''` and would write that back — under the rule it is invalid in all
three.

**Progress (overnight 2026-10-16/17, uncommitted — for the owner's review).**

- **O1.3 the library rule.** Swift `setAsideUnreadableLibrary(at:)` / Python `_set_aside_unreadable_library`: a library
  that fails to load is renamed `<name>-unreadable-<yyyyMMdd-HHmmss>.json` beside itself, the library starts empty,
  and `libraryLoadFailure` / `library_load_failure` carries the message, shown once ("Saved Measurements Unreadable",
  after the window is up — Swift an `.alert`, Python beside the engine-error report); if the rename fails, the file
  stays and `isLibraryWriteBlocked` / `is_library_write_blocked` stops every library write for the session. The web
  (`readLibrary()` in store.ts): each stored record has its ids checked as on reading a file (`canonicalIds`); one
  that fails is skipped and left in storage, the app says so at launch with Keep / Delete (`deleteUnreadable`).
  Tests: Swift and Python — a library cut short mid-write, or whole but holding a bad id, is kept aside byte for byte, a later import writes a new
  library beside it; a read-only folder blocks every write. Web — a stored record with a bad id is skipped, kept
  through another save, and gone only after Delete. Mutations (no setting aside / no record check) fail them.
  Noted, not changed: the web reads its library in the Measurements panel and App, not in the analyzer as Swift does.
- **O1.6 strict reading, Python and the web.** One parser beside the minting helper — Python `parse_uuid` in
  `utilities/new_uuid.py`, the web `parseUuid` in `newId.ts` (both `util/new-id`) — accepting exactly Swift's form
  (hyphenated 8-4-4-4-12, either case) and returning it uppercase; `InvalidIdError` otherwise. Every id is parsed
  when a measurement is read (Python `_canonical_ids` on the file's dict before decoding; the web `canonicalIds` on
  the decoded model, plus every key in the map readers so a key whose value is a dropped legacy form is still
  checked). A missing id is invalid (Python no longer mints one; the web no longer reads it as `''`). Python's
  scattered `.upper()` calls are gone.
- **O1.7 Swift.** `checkUUIDKeys` checks every key of the mode-name and label-position maps, in the flat or the object
  form, before their tolerant readers run; a key that is not a UUID fails the decode.
- **O1.8 shared cases.** `measurement-codable.json` group `ids`, ID1–ID23: all-lowercase and mixed-case files read
  with selection, mode name and label position on their peak and are written back with no lowercase id; a missing or
  invalid id in each id field (measurement, peaks, selection, plate/brace ids, both map forms, a key with a legacy
  value, tap entries, comparison entries, source, mode peak ids) is rejected; braces, no hyphens and `urn:uuid:` are
  rejected; two controls read. And `import-persistence` IP10–IP11, all three: an import of a file with a bad id fails and
  leaves the library and its file as they were, and a file with a good and a bad measurement adds neither. Mutations: Swift without the key check fails ID8–ID11; Python without the check
  fails all but the controls, with a lenient `uuid.UUID` parser ID21–ID23; the web without `canonicalIds` 17 cases,
  without the map-reader check ID11. Test ids made up as strings became UUIDs (Python minting through `new_uuid()`;
  the web's `testId(n)` helper in `test/testIds.ts`).
- **O1.5 the web, ids as a type.** `Uuid` (newId.ts) — a string at run time, branded so only `parseUuid()` and
  `newId()` make one — on every id field of the measurement types, the analyzer's id-keyed state (selection, mode
  names, label positions, modes, highlight, material ids), `classifyAll`, the chart's markers and hit-tests and their
  handlers; `idEntries()` gives an id-keyed map's entries with their keys as ids. The decoder keeps the file's raw
  ids typed as unchecked until `canonicalIds()` checks them — the one check. The compiler found every other place
  (61 errors, all fixed). Tests use `testId(n)` for readable fixed UUIDs.
- **O1.4 Python, ids as a type.** Every id is a `uuid.UUID`: `new_uuid()` mints one, `parse_uuid()` reads one
  (strict form, either case), `uuid_text()` writes one (uppercase) — the writers (`to_dict` of the measurement, peaks,
  tap and comparison entries, the map keys) write text, the readers parse. The three peak-table signals that carry an
  id (`annotationUpdate`, `selectionToggled`, `modeOverrideChanged`) are `object`. Found and fixed on the way: the
  mode-name and label-position readers tested `isinstance(k, str)` and would have dropped every entry. Tests compare
  ids as UUIDs; `uuid-case` now pins that ids are UUIDs written uppercase (and still that nothing mints outside the
  helper).
- **O1.9 App. B.** "Ids": every id is a UUID written uppercase, read in either case, and a file with one missing or
  in another form cannot be opened. "The saved-measurements library": kept, renamed, and how to restore it; the
  browser edition's unreadable records. (App. B is in Swift's manual — the online manual every edition links to.)
- **Suites (2026-10-17):** Swift passed (2 skipped, as before); Python 1379 passed, 1 skipped; the web 1295 passed,
  1 skipped; `--check` current, 142 groups.
- **Open — for the owner:**
  1. *Calibration ids:* decided (owner, 2026-10-17: "make the UUID handling consistent. It seems safe enough") and
     done, uncommitted. Python and the web hold calibration ids as UUIDs (Python `uuid.UUID`, the web `Uuid`),
     written uppercase, read strictly; a stored active or device-mapped id that is not a UUID counts as none, as
     Swift's `UUID(uuidString:)` gives nil. Found on the way: the wipe risk was in all three — Swift's `loadAll()` and
     the web's `listCalibrations()` also gave `[]` on a list they could not read, and the next save wrote over it.
     Now one rule: a stored calibration list that cannot be read is moved to `<key>-unreadable-<yyyyMMdd-HHmmss>`
     (UserDefaults / QSettings / localStorage), logged, and the list starts empty — no alert, a calibration can be
     imported again. Tests, each edition: a damaged list is kept byte for byte and a later save leaves it alone;
     the web also reads a lowercase id as the same id. Mutations (no setting aside) fail them. Also found: Qt's
     `findData()` matches a Python object only by identity — an equal UUID read back separately is not found; the
     app compares `itemData(i) == id` and never uses it for ids (a test did, now by equality). Suites: Swift
     passed, Python 1384, the web 1300.
  2. *Release notes:* decided (owner, 2026-10-17: yes) and written, uncommitted — Swift and Python "Saved Measurements
     and Files" under Improvements (an unreadable library kept, not written over; ids read in either case, a file
     with a missing or malformed id refused); Python also two Bug Fixes (Play File could freeze the app — C6; exports
     of 1.0.x measurements lost their dragged label positions); the web the same as an Improvements item, its
     unreadable records left out of the list and kept, with Delete offered.
  3. *Where the web reads its library:* decided (owner, 2026-10-17: "We are striving for architectural alignment so
     move it") and done, uncommitted — the analyzer holds `savedMeasurements` and `unreadableMeasurements` and loads
     them at construction (`loadPersistedMeasurements`, as Swift's init), again after every save, edit, delete,
     Delete All and import; the Measurements panel shows the analyzer's list (`measurements` prop from the
     snapshot) instead of reading the store, and App's alert reads the analyzer (`keepUnreadableMeasurements` /
     `deleteUnreadableMeasurements`). Test: the analyzer holds the library and the unreadable record; Keep keeps it,
     Delete removes it. Fast suite 1277 passed.

- **The failed-import message (owner, 2026-10-17: "they should all have the same text message … Including the illegal
  id (as in python) is desirable … also make the alert consistent").** One message in all three, from one model-level
  function — Swift `TapToneAnalyzer.importErrorMessage(for:fileName:)`, Python `import_error_message`, the web
  `TapToneAnalyzer.importErrorMessage`: `Could not import "<file>": the file is not a valid GuitarTap measurement
  ("<value>" in <field> is not a UUID).` for an id (`<field> is missing` when there is none), the same without the
  bracket for any other content, Swift's and Python's "Could not read … the system denied access" for a permission
  failure, otherwise what went wrong. Shown in an "Import Error" alert with OK in all three — the web's red line in
  the Measurements panel is gone (it had been left when the success message became an alert, `04c66b9`). Swift names
  the id from its decoder's own failure (`InvalidIDError.from`: the field from the coding path, the value read from
  the file), its two import paths share the function; Python no longer wraps the named-id error in a generic one.
  Shared: `import-persistence` IP10 (a bad measurement id) and IP12 (no id) pin the exact text; all three pass.
- **Export failures (owner, 2026-10-17: yes, Swift's way in all three).** Every export failure is an "Export Failed"
  alert with OK: the chart could not be drawn — Swift's sentence, already the same in all three — or `Could not save
  "<file>": <reason>.` for a file that could not be written (Python `export_failure_message`, the web
  `exportFailureMessage`; Swift writes through the system's save panel and reports none). Python's measurement list
  and main window drop "Export Error" and the raw text; the web's Measurements panel drops its red line (the last
  one) and its main window "Error" becomes "Export Failed" — keeping, for the PDF only, the web's own reload hint
  when a stale cached app could not load the report code. Tests (Python, web): the two messages.
- **A measurement with no spectrum (owner, 2026-10-17: (A)).** Export Spectrum is not offered for it — disabled in
  the row menu of all three (Swift `.disabled`, Python `setEnabled`, the web `disabled`, with the chart menu's
  disabled look) — by one property, `hasExportableSpectrum` / `has_exportable_spectrum`: a comparison's entries, or
  the guitar spectrum or a plate/brace's longitudinal one, as Swift's renderer reads them. Before: Swift offered it and
  did nothing; Python said "no spectrum snapshot"; the web failed inside its image code. Shared: `measurement-codable`
  DC11–DC13. Then (owner, 2026-10-17: "if there is no spectrum there is no PDF to export, there is no spectrum
  image to export, and there is no measurement to export. A comparison does have a spectrum … so be careful"): the
  property, renamed `hasSpectrum` / `has_spectrum` (a comparison's, in its entries), greys out Export Measurement,
  Export Spectrum and Export PDF — and Swift's Save Measurement to Disk — in all three. No measurement on this Mac
  lacks one (700 checked, every library and file): only a hand-written file or other software's can.

- **No spectrum is not a measurement (owner, 2026-10-17: "loading a measurement with no spectrum fails as an illegal
  measurement (since there is no way for the application to create one)" — "Go").** Replaces the greying above. All
  three refuse, on reading a file or a library record, a measurement with no guitar spectrum and no plate/brace
  longitudinal one, or a comparison of fewer than two entries — Swift `NoSpectrumError` at the end of its decoder,
  Python `NoSpectrumError` in `from_dict`, the web `checkMeasurement` (ids, then spectrum; also used for the stored
  records) — and Import says `… not a valid GuitarTap measurement (no spectrum).` `hasSpectrum`, the greyed export
  items and their CSS are gone. Data: every shared case and edition test that left out a spectrum or used a
  one-entry comparison only for brevity now has a valid one (measurement-codable DC1–DC10, WR1–WR4, ID1–ID23 with a
  second entry for ID16–ID20, CR2–CR5; comparison CM20 compares two; the web's PR38 runner; Python's and Swift's
  round-trip tests through `_create` / `aSpectrum()`). New: DC11 (no spectrum, refused), DC14 (one-entry comparison,
  refused); DC12–DC13 read a guitar and a plate. Before this landed the owner deleted the step-9 measurement from
  Swift's library (it would have made the library unreadable).
- **Next, decided (owner, 2026-10-17: "Yes"):** (1) retire CM3, CM8 (comparison), DR2 (display-range), PR37
  (frozen-peak-recalc) — each about a loaded measurement with no spectrum, which no longer exists; (2) then survey,
  and bring to the owner as a list before deleting anything, the code that exists only for such a measurement (some
  checks also serve other states — Re-analyze is unavailable with nothing loaded too). (3) Swift warnings reported by
  the owner: `normalizedName` / `normalizedNotes` called from a nonisolated context in
  `TapToneAnalyzer+MeasurementManagement.swift` (lines ~592, 593, 627, 631). Then the full suites, once, and the
  owner finishes the run-review (left: web steps 6 and 8, and step 9 as rewritten).
- **Done (2026-10-17, uncommitted):** CM3, CM8, DR2, PR37 retired, with the stored entries only they used (comparison
  `With`, `Without`, `Without2`; display-range `no-spectrum`); the three slugs pass in all three. Swift warnings fixed:
  `.flatMap(TapToneMeasurement.normalizedName)` passed a main-actor function as a nonisolated value — now
  `.flatMap { TapToneMeasurement.normalizedName($0) }` (four places); the rebuild shows no warnings.
- **Survey of code for a measurement with no spectrum (2026-10-17) — for the owner.** Most checks of the guitar
  spectrum are not about a missing spectrum but about guitar against plate/brace (a plate has no guitar spectrum):
  which measurements Compare accepts (Swift `comparableMeasurements` / `isComparable`, the comparison's
  `withSnapshots`; Python's list view and `with_snapshots`; the web's `isComparable`, `withSnapshots` and App's
  count), the row's spectrum icon, the Details pane's choice of snapshot, the renderer's `primarySnapshot`. These stay.
  The one branch that exists only for a loaded measurement with neither spectrum: Swift `loadMeasurement`'s last
  `else { setFrozenSpectrum(frequencies: [], magnitudes: []) }` (after the plate/brace and guitar branches), and its
  counterparts in Python and the web — to remove, with the owner's go. Re-analyze's check stays (it is also what
  makes Re-analyze unavailable with nothing loaded).
  The web's counterpart is `measurementToLive`'s no-`snap` handling, whose comment calls it "a measurement saved before
  spectra were stored … Mirrors Swift loadMeasurement's old-format branch". Checked against the history: Swift stored
  the spectrum from `87a7410` (2026-02-08), before its first release (Beta 1.0, 2026-02-20); Python 0.9 and 0.10
  (2023) saved no measurements; Python 1.0 (2026-06-17) saved the guitar spectrum on every guitar save (its
  `spectrum_snapshot=None` is the plate/brace save, which stores the longitudinal one); the web always has. So the
  "old format" is development files from before February 2026 — no shipped edition wrote one, and none of the 700
  measurements on the owner's Mac lacks a spectrum. Refusing them is safe.
- **Done (owner, 2026-10-17: "Remove"), uncommitted:** the no-spectrum branch is gone in all three — Swift
  `loadMeasurement`'s last `else`, Python's matching `else`, the web `measurementToLive`'s no-`snap` handling (the
  type, range and view now come from the measurement's spectrum). Python keeps `if snap is not None` around setting
  the spectrum, as Swift's `if let`: tests that build a measurement in memory, not from a file, reach it without one.
- **An empty spectrum is no spectrum (owner, 2026-10-17: "An empty spectrum means there is no spectrum … yes to all
  3"; DC16–DC18 kept).** The spectrum check in all three (Swift's decoder, Python `from_dict`, the web
  `checkMeasurement`) counts a spectrum as present only if it has points and as many magnitudes as frequencies — for
  the guitar spectrum, a plate/brace's longitudinal one, and each comparison entry's. The optional cross and FLC
  spectra are not checked. Shared cases: `measurement-codable` DC15 (no points), DC16 (frequencies and magnitudes
  differ in number), DC17 (a plate/brace longitudinal spectrum with no points), DC18 (a comparison entry with no
  points), all refused; `import-persistence` IP13 (no spectrum) and IP14 (no points) — the import fails with the exact
  "(no spectrum)." message and the library and its file are as they were (new stored measurements `no-spectrum`,
  `empty-spectrum`). Library: Swift's and Python's unreadable-library tests run four kinds — cut short, bad id, no
  spectrum, empty spectrum; the web's unreadable-record test three (bad id, no spectrum, empty spectrum). Test data:
  the ML/SH case builder in all three had an empty spectrum, now two points; the web's SB2 reads its snapshot back
  on its own (`decodeSnapshot`), as Swift's, instead of inside a measurement. Suites (run before the owner's go — not
  asked for): Swift 278 tests passed, Python 1396 passed, 1 skipped, the web 1310 passed, 1 skipped.
- **Run-review (owner, 2026-10-17): complete in all three**, steps 1–9 below, step 9 as rewritten.

**O1.10 run-review (for the owner).** Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, then clear the service worker after the build (F30's run-review steps). Same list
per edition, Swift first; (N) natives only, (W) the web only.

1. Launch. → The saved measurements are all there, as before, with no alert.
2. Load a saved guitar measurement with named peaks and dragged labels. → Selection, names and label positions as saved.
3. Export it as a `.guitartap`, Export Spectrum and Export PDF. → All three as before; the PDF's labels where dragged.
4. Open a `.guitartap` saved by Python 1.0.x (lowercase ids — e.g. `dws-2024-umik-1-python-mac-1784225140.guitartap`
   from the test fixtures). → It opens with its selection and names; saving it again works.
5. Compare two saved measurements, save the comparison, open it again. → The comparison as saved.
6. Open `step6-bad-peak-id.guitartap` (in Downloads › "GuitarTap O1 run-review": the Contreras fixture with its first
   peak id changed to `not-a-uuid`). → An "Import Error" alert with OK, reading: Could not import
   "step6-bad-peak-id.guitartap": the file is not a valid GuitarTap measurement ("not-a-uuid" in peaks[].id is not a
   UUID).
7. (N) Quit. Rename the library — Swift
   `~/Library/Containers/com.dolcesfogato.GuitarTap/Data/Documents/saved_measurements.json`, Python
   `~/Library/Application Support/guitar-tap/saved_measurements.json` — to `saved_measurements-original.json`; copy
   `step7-saved_measurements-cut-short.json` (same folder in Downloads) there as `saved_measurements.json`; launch.
   → "Saved Measurements Unreadable", naming the file it was kept as; no new `saved_measurements.json` (one is
   written only when something is saved). Quit, delete the `saved_measurements-unreadable-…json`, and rename
   `saved_measurements-original.json` back.
8. In Settings, check the imported calibrations, then quit and relaunch. → The same calibrations listed, and the
   one chosen for the microphone still applied.
9. Import `step9-no-spectrum.guitartap` (same folder in Downloads: the Contreras fixture with its spectrum removed).
   → An "Import Error" alert reading: Could not import "step9-no-spectrum.guitartap": the file is not a valid
   GuitarTap measurement (no spectrum). Nothing is added.

What the tests already pin, so these two steps are only what is seen: an import that fails leaves the library and its
file as they were, and a file is imported whole or not at all (`import-persistence` IP10–IP11, all three); a library
cut short or holding a bad id is kept aside byte for byte, the library starts empty, a later save writes a new one
beside it, and one that cannot be moved is never written (Swift and Python library tests, both damaged libraries);
the web's unreadable stored record — not reachable by hand, a browser user cannot edit one — is skipped, kept and
removed only on Delete (the store test). A measurement with no spectrum, or one with no points: an import fails with
"(no spectrum)." (IP13–IP14, all three), and a library holding one is unreadable (the library tests, all three).

- Found on the way: the Swift filter `-only-testing:GuitarTapTests/MeasurementCodableTests` names no suite (the file's
  suites are `MeasurementCodecTests`, `MeasurementLogicTests` …) and runs nothing — use the suite names.

What users would see: Python 1.0.x files and libraries (lowercase ids) behave the same in all three, Python exports keep
their dragged label positions, files are written back uppercase on their next save; a file with an id that is not a
UUID is refused with an error in all three — only a hand-edited or third-party file can have one.

**O2 — the armed prompt, and how the web analyzer reads its settings (owner, 2026-10-17: "Start O2"; asked
whether the change made it the same as Swift architecturally, not just functionally — it did not; then "Why
not fix item 5 as part of O2 since it is directly related?" — "Yes").** Two parts: the status-derivation
functions, and — directly related, since they read the measurement type — how the web analyzer gets its
settings.

| # | item | status |
|---|---|---|
| O2.1 | The status-derivation functions as Swift's (`TapToneAnalyzer.swift`, section "Status derivation"): `tapPrompt`, `pausedStatus`, `armedPrompt`, `materialArmPrompt`, `statusAfterSettle`, `restoredStatus`, `guitarLoopStatus`, in that order, in the analyzer's main file | done — run-reviewed (2026-10-17), uncommitted |
| O2.2 | The web analyzer reads its settings as Swift's reads `TapDisplaySettings` — survey done, plan and decisions below | done — items 1–4, D3, E1–E4; run-reviewed in all three (2026-10-17), uncommitted |

**O2.1 done (uncommitted).** The web: `restingPrompt()` is `armedPrompt()`, and its guitar branch calls
`guitarLoopStatus(false)` (it held a copy of that function's body); the seven are together in Swift's order under
one heading, with Swift's comments — the `statusAfterSettle` comment that sat above `restoredStatus` and an
orphan comment for a method that no longer exists are gone; `materialArmPrompt` asks "plate?" as Swift's does
(it asked "brace?" — the same result with two material types); they are no longer private, as Swift's are
internal, so the `notification` test calls `armedPrompt()` directly. Python: the seven moved from
`tap_tone_analyzer_control.py` to `tap_tone_analyzer.py`, in Swift's order, after `number_of_taps` as Swift has
them after `numberOfTaps`; otherwise unchanged. Swift: no change. Tests: the web 77 (`state-notification`,
`status-message`, `tap-count-change`, `tap-progress`, `scenario-trace`), Python 92; `--check` current.
*Seen, for the owner:* (a) Swift's own section has `guitarLoopStatus`'s doc comment above `pausedStatus`, stacked
on that constant's comment, and none on `guitarLoopStatus`; (b) Python keeps the other status constants
(`ROUTE_CHANGE_STATUS`, `CLIPPING_WARNING_STATUS`, `DEAD_INPUT_STATUS`) and `_resolved_status` (Swift
`applyStatusOverrides`) in the control mixin, where Swift has them in `TapToneAnalyzer.swift`; (c) the web's
`PAUSED_STATUS` is a module constant, Swift's a static on the analyzer, Python's a class attribute.

**O2.2 survey (2026-10-17, read-only).** Swift's analyzer reads `TapDisplaySettings` where it needs a setting, in
every analyzer file; Python's reads `TapDisplaySettings` (`_tds`) the same way. The web's keeps copies, refreshed
by `applyStoreSettings` on every change of the settings store (`attachSettingsStore`, from App):

| setting | Swift (Python the same) | the web |
|---|---|---|
| measurement type | read where used — 29 places across the analyzer files | a copy, `this.measurementType`; also set by `setMeasurementTypeAndNotify` |
| Measure FLC | read where used (5) | a copy, `this.measureFlc`, by `setMeasureFlc` |
| guitar type | read where used: the measurement type's guitar type, else the guitar type last stored | derived from the copied measurement type, else Generic — a plate or brace is saved with guitar type Generic where Swift writes the last guitar type (read, not run) |
| Show Unknown Modes, Dump Capture Audio, the display range, the plate/brace and body defaults | read where used | read from a copy of the whole settings, `this.settings`, replaced by `setSettings` on every change |
| tap threshold, Peak Min, annotation mode | analyzer state (`@Published`), set from the settings at construction and on reset (`TapToneAnalyzer.swift:1551–1556`); the control sets the analyzer, and the analyzer writes the setting (`didSet`) | analyzer fields overwritten from the store on every change; the control writes the STORE (App `updateSettings({ tapDetectionThreshold })`, `({ peakMinThreshold })`; the annotation cycle sets the analyzer, then App writes the store) — the direction is reversed |
| the analysis range (30–2000 Hz) | a fixed constant in `TapDisplaySettings` | a fixed constant in `settings.ts` — the same |

Without a store (a unit test) the web analyzer keeps the settings it was given: 12 web test files set the copies
through `setSettings`, `setMeasureFlc` or `setMeasurementTypeAndNotify`. Swift's tests write `TapDisplaySettings`
in a sandbox (`TestSandbox`), Python's write `_tds` in one (`settings_scope`). The comments that say "the web has
no analyzer-visible global, so App mirrors it" date from before step 10 gave the web its store.

**O2.2 plan (for the owner's approval; nothing changed yet).**
1. The analyzer reads the settings store where it uses a setting, everywhere Swift reads `TapDisplaySettings`.
   The copies `settings`, `measurementType` and `measureFlc` go, with `setSettings`, `setMeasureFlc`,
   `setMeasurementTypeAndNotify` and the re-seeding in `applyStoreSettings`. What the analyzer must DO on a change
   stays an explicit model call, as in Swift (a type change is `changeMeasurementType`, as now).
2. The tap threshold, Peak Min and annotation mode are analyzer state as in Swift: set from the store at
   construction and on reset; the controls set the analyzer, and the analyzer writes the store. App stops writing
   them to the store itself.
3. Tests set settings in the store, sandboxed per test, as Swift's and Python's; the 12 files move off the setters.
4. The guitar type follows Swift's rule.

*Decisions (owner, 2026-10-17: "D1 (a). D2 Follow Swift D3 Yes"):* the plan approved; D1 (a), D2 Swift's rule, D3 all three fixed in O2.
- **D1 — which store the analyzer reads.** (a) The app's one store, the `settingsStore` module instance, read
  directly as Swift reads the global `TapDisplaySettings`, with tests resetting it per test as Swift's sandbox does;
  or (b) a store given to the analyzer at construction, tests passing their own. (a) is Swift's shape —
  recommended.
- **D2 — the guitar type of a plate or brace.** Swift's rule needs the web to keep the last guitar type when the
  type changes to plate or brace (a new stored setting, as Swift's `guitarTypeKey`). Recommended: Swift's rule.
- **D3 — the three items seen in O2.1** (Swift's misplaced comment; Python's other status constants and
  `_resolved_status` in the control mixin; the web's `PAUSED_STATUS` as a module constant): fix in O2, or leave.
  Recommended: fix all three in O2 — Swift's comment moved to `guitarLoopStatus`, Python's constants and
  `_resolved_status` moved to `tap_tone_analyzer.py` where Swift has them, the web's constant a static on the
  analyzer.

**O2 progress (2026-10-17, uncommitted).**
- **D3(a), D3(c) done.** Swift: `guitarLoopStatus`'s comment moved onto it from above `pausedStatus` (comment only).
  The web: the paused status is `TapToneAnalyzer.pausedStatus`, a static, with Swift's comment.
- **O2.2 items 1–3 done (the web).** The analyzer reads `settingsStore` — the app's one store, D1 (a) — where it
  uses a setting, as Swift reads `TapDisplaySettings`; the copies `settings`, `measurementType` and `measureFlc`,
  and `setSettings`, `setMeasureFlc`, `setMeasurementTypeAndNotify`, `attachSettingsStore` and
  `applyStoreSettings`, are gone. The tap threshold, Peak Min and annotation mode are analyzer state as in Swift:
  set from the store at construction, saved to it on every change (the threshold and Peak Min setters, as Swift's
  didSets; `cycleAnnotationVisibility`, as Swift's); App's Threshold and Peak Min controls set the analyzer
  (`setTapDetectionThreshold`, new, and `setPeakMinThreshold`), its annotation button no longer writes the store,
  and Settings' Done sets the analyzer's Peak Min, as Swift's Settings sets `peakMinThreshold`. A load writes the
  measurement's settings to the store and sets those three on the analyzer, as Swift's load sets the properties.
  Tests: the step runner as Swift's (`makeStepsAnalyzer()` returns the analyzer; `runAnalyzerStep(step, a)`; the
  settings step writes the store, the Threshold and Peak Min steps set the analyzer, the visibility step sets the
  analyzer's mode, as Swift's `AnalyzerSteps.swift` and `AnnotationStateTests`); every test sets settings in
  `settingsStore`; `test/setup.ts` puts the store back to the defaults before each test (each test file has its
  own instance, saving nothing — Swift's tests have their own settings per process). Web: typecheck and lint
  clean; fast suite 1289 passed, 1 skipped; `--check` current after regenerating (`test/setup.ts` listed, web only).
- **Kept, for the owner (E1 below):** `watchSettings()` — the analyzer subscribes to the store only to re-derive
  the displayed peaks and tell the view when a setting changes (App calls it, as it called `attachSettingsStore`).
- **Seen, not checked:** Swift's Settings Done starts a new sequence when Measure FLC changes
  (`measurementChanged` includes it, `TapSettingsView+Actions.swift`); the web's `applySettings` acts only on a
  type change.

*Questions for the owner:*
- **E1 — telling the web view of a settings change.** The web view shows a snapshot the analyzer caches (the
  visible peaks, the tap total, whether it is a guitar), rebuilt only when the analyzer notifies. Swift's views
  re-read the analyzer's computed values whenever they redraw — closing Settings redraws them — so Swift needs
  nothing like it. Keeping the store subscription for this alone (re-derive and notify, no copying) is the web's
  form of that redraw. The alternative is App calling the analyzer after each settings change, as Swift's Settings
  calls `onApply`. Recommended: keep `watchSettings()`.
- **E2 — D2 described wrongly.** Swift's guitar type for a plate or brace is not "the last guitar type used":
  `TapDisplaySettings.guitarType` is the measurement type's guitar type, else a stored guitar type that only
  loading a guitar measurement writes (`loadMeasurement`, `TapDisplaySettings.guitarType = …`; Settings writes
  only the measurement type) — else Generic. So a plate saved after loading a Classical measurement records
  Classical, and one saved on a fresh install records Generic. Python is the same. Following Swift means the web
  stores that guitar type on a guitar load and reads it for a plate or brace. Still follow Swift?
- **E3 — D3(b) is larger than described.** Python's status override is one unit — `_set_status_message`, the three
  status constants, `_set_clipping`, `_set_input_appears_dead`, `_apply_status_overrides`, `_resolved_status` —
  all in the control mixin, all in `TapToneAnalyzer.swift` in Swift. Moving only the constants and
  `_resolved_status` would split it. Move the whole unit? Swift's route-change handling
  (`handleRouteChangeRestart`) is in the same file too, Python's in the control mixin — include it?

**O2, second round (owner, 2026-10-17: "E2 - Yes. E3 Yes - web and python should follow swift on the change of
Measure FLC"; E1 asked how Python does it and why React cannot work as Swift does).**
- **E2 done (the web).** A stored guitar type apart from the measurement type (`Settings.guitarType`, default
  Generic), written by every load whose spectrum names one (`loadedSettingsPatch`, as Swift's load writes
  `TapDisplaySettings.guitarType`), read through `guitarTypeSetting()` — the measurement type when it is a guitar,
  else the stored one, as Swift's getter — by the analyzer's classification, its saves (guitar and material) and
  the per-tap snapshots, and App's guitar type. New shared cases, `material-measurement-inputs` M14 (a plate saved
  with no guitar measurement loaded records Generic) and M15 (a plate saved after loading a Classical guitar
  measurement records Classical); the Swift and Python runners read the saved `guitarType`. All three pass; the
  web with its old rule fails M15.
- **E3 done (Python).** The status-override unit (`_set_status_message`, the three status constants,
  `_set_clipping`, `_set_input_appears_dead`, `_apply_status_overrides`, `_resolved_status`) and the route-change
  handling (`handle_route_change_restart`, `_restore_detection_after_route_change`) moved from
  `tap_tone_analyzer_control.py` to `tap_tone_analyzer.py`, after the status derivation, unchanged; the map now
  lists `state/route-change-settle` in `tap_tone_analyzer.py`, beside Swift's `TapToneAnalyzer.swift`. Python's
  status, settle and device tests 151 passed.
- **Measure FLC — not done; it is part of a larger difference, for the owner (E4).** Swift's Settings Done:
  `measurementChanged` = a type change other than guitar to guitar, or a Measure FLC change → `requestStartTapSequence()`;
  else a guitar-to-guitar change → `reclassifyForGuitarTypeChange()`; no check of whether the engine runs. Python:
  restarts only across the guitar/material boundary (and only while running), or — through a separate
  cancel-then-`start_plate_analysis` path — on a type or FLC change while the old type is material and running;
  an FLC change under a guitar type, or while stopped, does nothing. The web (`changeMeasurementType`, the
  owner's 2026-10-15 decision that Settings' Done calls the model): a guitar-to-guitar change reclassifies, any
  other type change clears the result and starts a sequence if the engine runs; an FLC change does nothing.
- Web fast suite, Python and Swift targeted suites pass; `--check` current after regenerating.

**O2, third round (owner, 2026-10-17: "E1 Yes, make the change. E4 match swift").**
- **E1 done (the web).** `watchSettings()` is gone, with App's call: nothing subscribes the analyzer to the
  settings. Its snapshot records the settings object it was built under and is rebuilt at the next read when
  `settingsStore.get()` is another (the store makes a new one on every change) — App redraws on every settings
  change, so the view re-reads what depends on a setting, as Swift's views re-read the analyzer's computed
  values. What the analyzer stores is refreshed by explicit model calls, as in Swift. Test (web only, in
  `settings-store.test.ts`): a settings change shows in the next snapshot with no notify; without the rebuild it
  fails.
- **E4 done (the web and Python).** Settings' Done decides as Swift's: `measurementChanged` = a type change other
  than guitar to guitar, or a Measure FLC change → a new tap sequence (`requestStartTapSequence` /
  `restart_tap_sequence`), with no check of whether the engine runs; else a guitar-to-guitar change →
  `reclassifyForGuitarTypeChange`. The web: `changeMeasurementType` is gone (it replaced the 2026-10-15 shape, as
  the owner chose), App's `applySettings` computes the two flags as Swift's `applySettings`; the annotation
  test's guitar-type step is Swift's (the setting, then the re-derivation). Python: the cancel-before-saving and
  `start_plate_analysis` paths are gone; `_on_measurement_type_changed` takes Swift's `measurement_changed`
  (it took `crosses_boundary`, the guitar/material boundary only) and no longer checks `_is_running` (set once,
  when the engine first starts, never cleared). No edition has a test of Settings' Done (Swift's is view code) —
  the run-review below covers it.
- Web fast suite 1292 passed, 1 skipped; Python fast suite 1376 passed, 1 skipped; Swift targeted suites passed;
  `--check` current.

**O2 run-review — passed in all three (owner, 2026-10-17).** Same list per edition, Swift first; (W) the web only.
1. Launch. → The status reads as before ("Tap the guitar..." once warmed up).
2. Set Taps to 3 before tapping. → "Tap the guitar 3 times..."; tap once → "Tap 1/3 captured. Tap again...".
3. Change the type to Material (Plate), Measure FLC off, Taps 2; Done. → A new sequence: "Ready for fL tap (×2 each for L, C)".
4. Open Settings, turn Measure FLC on; Done. → A new sequence: "Ready for fL tap (×2 each for L, C, FLC)" (before, the web and Python kept the old sequence).
5. With the type still Plate, turn Measure FLC off while the engine is running mid-sequence (one fL tap taken); Done. → The sequence restarts at fL.
6. Change the type to Classical Guitar; Done; then to Flamenco Guitar; Done. → The first starts a new sequence; the second keeps the measurement and re-labels its peaks.
7. Move the Threshold and Peak Min sliders; quit and relaunch. → Both as left.
8. Cycle the annotation button; quit and relaunch. → The mode as left.
9. (W) With a guitar measurement shown, turn Show Unknown Modes off and on in Settings. → The unknown peaks' labels go and come back at once on Done.
10. Load a saved Classical guitar measurement; change the type to Material (Plate); measure and save a plate; export it as a `.guitartap` and open the file in a text editor. → Its `longitudinalSnapshot` has `"guitarType" : "Classical"` (as Swift and Python already did; the web wrote "Generic").

### Stage 2 progress

What is done, slug by slug, with its commits. What is left is the plan above. Details are in the survey, the
pilot and the batch entries below. *done* = the cases are in `tooling/parity/cases/<slug>.json`, run in all three editions, and pass.

| group | slug | status | commits (Swift / Python / web) |
|---|---|---|---|
| pilot | `classify` | done — Python's label resolver and empty-override rule fixed; duplicate claiming algorithm, legacy modes and `normalized` removed | `8fdd350` / `7c20911` / `9b49fc2` |
| A, batch 1 | `field-precision` | done — identical | `3d6eeba` / `2cbca0e` / `2446bdf` |
| A, batch 1 | `frequency-format` | done — identical | same |
| A, batch 1 | `analysis-quality` | done — identical | same |
| A, batch 1 | `quality-colors` | done — identical | same |
| A, batch 1 | `measurement-name` | done — identical | same |
| A, batch 1 | `export-filename` | done — Python and web stem functions now keep whole seconds, as Swift | same |
| A, batch 2 | `display-range` (the widening rule and range moves) | done — identical in all three | `2e8a208` / `e693b46` / `937b172` |
| A, batch 2 | `button-enablement` (B1–B16) | done — identical in all three, defaults included | same |
| A, batch 2 | `measurement-type-name` | done — Python and web fixed to Swift's type resolution (word, flag, save path) | same |
| A, batch 2 | `measurement-amend` (`isAmended`) | done — identical in all three | same |
| A, batch 2 | `settings-store` (validation, entered value, defaults) | done — identical in all three | same |
| A, batch 2 | `decay-tracking` (DK1–5, DK8–10) | done — identical in all three. Replaced 2026-10-14 by #3 item 8: the ring-out is measured from the tap's window, and the cases are DK1–DK8 on generated audio, identical in all three | same; item 8: Swift `777a951`, Python `3a83e99`, web `760dacb` |
| A, batch 3 | `material-selection` | done — identical in all three | Swift `d414025`, Python `5994aa0`, web `828c8f4` |
| A, batch 3 | `peak-heal` | done — identical in all three; the web's measurement type now declares `wasHealed`, as Swift and Python | same |
| A, batch 3 | `pdf-report` | done — fixture list and baseline tolerance in `pdf-report.json` | same |
| A, batch 3 | `spectrum-export` | done — cases in `spectrum-export.json` | same |
| A, batch 3 | `peaks` (fixtures) | done — the fixture list is `peak-baseline-expected.json`'s keys (already shared) | same |
| oracle | `gated-fft` | done — the tone cases are one test over the oracle's own case list (GFFT1–3, 5) | same |
| oracle | `file-playback` | done — `file-playback.json` names what each REG case checks; one runner per kind of check in each edition; the playing file's name tested in all three | same |
| B | `pitch` | done — `pitch.json`, 56 cases, identical in all three; Swift floors below C0; Python and the web round the half-step count as Swift; `formatCents` in all three | Swift `5a22fda`, Python `3f03523`, web `d39196d` |
| B | `plate`, `brace` (together: one model) | done — identical in all three; the web has Swift's model types; Python's wrappers and dialogs gone; when properties are shown follows Swift; Python's G_LC rule as Swift | Swift `da367e5`, Python `308d0e3`, web `288d003` |
| B | `dsp` | done — identical in all three; the web's peak analysis and the live FFT (web and Python) are analyzer methods, as Swift's; one live-spectrum length (32768) with a correct bin 0; run-reviewed | Swift `f082a55`, Python `180b595`, web `7fef7a6` |
| B | `peaks` | done — identical in all three; the web's averaging, auto-selection, guitar type and every save on the analyzer, as Swift's; run-reviewed | Swift `7855a3d`, Python `8837a28`, web `8f31b91` |
| B | `mode-colors` | done — the cases are `theme.json`'s `modeRoles` (Issue #2 step 4), identical in all three | Swift `382cfeb`, Python `450e1ce`, web `329a10e` |
| B | `mic-selection` (MS1–MS5) | done — `mic-selection.json`; MS4 and MS5 Swift and Python only (the browser resolves its own default) | Swift `3a8022b`, Python `3c513c1`, web `ee74021` |
| B | `measurement-codable` (TR, ML, SH; SB, DC, WR, fixtures) | done — `measurement-codable.json`, identical in all three; with it `calibration.json` (CAL1–CAL2) and `session-pre-roll.json` (SR1–SR11) | 9a: Swift `f02b9f7`, Python `5db7f73`, web `4e41e8c`; 9b: Swift `9cd3c38`, Python `3310195`, web `84196de` |

### Stage 2 survey — what is still not the same (2026-10-02)

**What Stage 1 did and did not establish.** Stage 1 asked, slug by slug: does each edition's test reach production,
does it test something that still exists, and do the productions agree as far as the tests show. It did **not**
require the three editions to test the same cases — F18 deferred that here on purpose. Reading all 48 `test/*`
slugs again (three readers, one per third, each reading all three editions' test files) shows how much that leaves:
many slugs test the same rule with different inputs, tolerances or checks, so no one has shown the productions agree
on the cases one edition tests and another does not. Some differences are weaker tests that Stage 1 should have
caught (below).

**The slugs by shape** (counts are cases Swift / Python / web):

| group | slugs | what it means |
|---|---|---|
| A — the same cases in all three, input → expected output | `field-precision` (16/16/16), `frequency-format` (7/7/7), `analysis-quality` (8/8/8), `button-enablement` B1–B16, `measurement-name`, `measurement-type-name` (six-type table), `measurement-amend` (`isAmended`), `settings-store` (validation, entered value, defaults), `quality-colors` (5 grades), `decay-tracking` DK1–5 and DK8–10, `display-range` (`DisplayRangeExpansion`, 19/19/19), `export-filename` (the 9 shared rows), `material-selection`, `peak-heal`, `pdf-report`, `spectrum-export`, `peaks` (the 3 fixtures and `peak-baseline-expected.json`) | can move as they are |
| B — the same rule, different cases per edition | `pitch` (32/32/26; tolerances, inputs and A4 differ), `plate` (39/41/34; free functions on the web, properties in the natives), `brace` (web lacks "higher fL gives equal-or-better quality"), `classify` (below), `dsp` (F1–F5, F9: web's F9 checks only not-NaN where the natives check bandwidth 990 and Q 0.505; Swift F6 1024 bins against 2048), `peaks` synthetic F10–F16 and averaging (widths, thresholds, tolerances and frequencies differ in each), `mode-colors` (the web's values differ by design), `mic-selection` MS1–5 (the web has no pure `inputDeviceToUse`), `measurement-codable` (ratio and heal inputs differ: Swift classical 95/210, Python generic 100/150, web classical 90/200), and F18's carried-in slugs | need one agreed case set first |
| C — scenarios (sequences of calls on the analyzer, timers, signals, storage) | `scenario-trace`, `tap-decisions`, `state-invariants`, `start-tap-race`, `session-pre-roll`, `tap-count-change`, `tap-progress`, `status-message`, `annotation-state`, `audio-clock-timers`, `comparison`, `frozen-peak-recalc`, `notification`, `measurement-complete`, `material-measurement-inputs`, `import-persistence`, `peak-selection-persistence`, `effective-peak-id`, `display-range` (`LoadedRange`, `MaterialPeakAnnouncement`) | stay as code; `scenario-trace` and `tap-decisions` could take a shared step list, but each edition would still need its own interpreter and its own waiting |
| already shared data | `gated-fft`, `file-playback` — expected values in `parity-oracle.json` | only the case list in code becomes a loop |
| cannot be shared | `self-regression` (per-machine baselines), `uuid-case` (random draws, a source scan), `wav-dump-folder` (filesystem) | stay per edition |

**Raised by the survey, not changed:** web `measurement-type-name.test.ts` says the Swift counterpart is deferred —
it exists; Swift `PitchTests`' header counts are stale; `gated-fft` checks at 0 in Swift and 0.001 in the others (by
design — Swift's baseline is the oracle); the web's `7108913.txt` has CRLF line endings again (Swift and Python LF;
`check-fixtures.py` reports it, with the per-machine self-baselines).

**The method (proposed 2026-10-02; the owner: pilot it on `classify`).** Reading cannot settle whether the
productions agree on cases only one edition tests; running them can. For each slug: gather the **union** of every
edition's cases into one data file (Swift's spellings), take the expected values from **Swift's production** (run
Swift — it is canonical), and run all three editions against the file. Each case then either passes (identical —
it stays on the shared list), fails (a production difference — a finding, fixed to Swift), or cannot be run by an
edition (a missing or different API — a mechanism difference, the owner's decision). The shared-data runner is
therefore the tool that produces the remaining list, verified by execution; Stage 2's move is its by-product. The
data files: one JSON file per slug, canonical in the hub (`tooling/parity/cases/`), copied into each edition's
fixture folder and kept identical by `check-fixtures.py`; Swift's spellings, mapped by each runner; NaN and
±infinity as `"NaN"`, `"Infinity"`, `"-Infinity"`, as the oracle writes them.

**`classify` — which function** (owner: "Make sure it is classify or classify all since there use to be two
different ones"). Checked in the code:

| | per-frequency band lookup | whole-set claiming (the app's) | other |
|---|---|---|---|
| Swift | `classify(frequency:guitarType:)` — **private** | `classifyAll(_:guitarType:)` — every app caller | — |
| Python | `GuitarMode.classify(freq, type)` — public; `classify_peak(freq, type)` — public, exported, no app caller | `GuitarMode.classify_all(peaks, type)` — every analyzer caller | `GuitarMode._classify_all_tuples` — a **second copy of the claiming algorithm** over (freq, mag) tuples, used by the results table's model (`views/shared/peaks_model.py`) |
| web | `classifySingle(freq, type)` — exported, called only inside `classifyAll` and by tests | `classifyAll(peaks, type)` — every app caller | `resolvedModePeaks` (strongest peak per mode, from `classifyAll`) |

The app classifies only through the whole-set claiming in all three. Swift tests it only through `classifyAll` (28
calls; single-peak sets stand in for the band lookup); Python calls `classify` directly 14 times and `classify_all`
9; the web calls `classifySingle` in 4 places and `classifyAll` in 9. Two Swift doc comments
(`UserAssignedMode.swift`, `TapToneAnalyzer+PeakAnalysis.swift`) and two Python ones (`user_assigned_mode.py`) still
say labels are re-evaluated "by `classify(frequency:)`" — the code calls `classifyAll`.

*Recommendation (the pilot):* the shared cases test `classifyAll` only, as Swift — each band-lookup case becomes a
one-peak set; then (after the run, and after the owner has seen its results) the per-frequency lookup becomes
private in Python and the web as in Swift, Python's results table calls `classify_all` and `_classify_all_tuples`
and the unused `classify_peak` go, and the four comments are corrected. *Decision (owner, 2026-10-02):* "I think
so. Let's see how it works."

**Pilot run — `classify` (2026-10-02).** `tooling/parity/cases/classify.json` (copied into Swift
`GuitarTapTests/`, Python `tests/`, web `test/fixtures/`) holds the union of the three editions' cases, 95 in all:
45 `classifyAll` sets (each band-lookup case as a one-peak set), 3 `resolvedModePeaks` (the strongest peak per mode,
which is where the equal-magnitude tie shows — Swift's and Python's tie tests recomputed the maximum inside the test,
so they could not fail), the four types' bands, the override labels, `effectiveMode`, display names and
normalisation; each case notes which editions' tests it came from. Runners: `ClassifyCasesTests.swift`,
`test_classify_cases.py`, `classify-cases.test.ts`. Swift passes all 95 — the expected values are Swift's answers.

| | Swift | Python | web |
|---|---|---|---|
| `classifyAll`, 45 sets — every band, overlap, claiming, tie and empty case | pass | pass | pass |
| `resolvedModePeaks`, 3 (incl. the tie: the first peak wins) | pass | pass | pass |
| bands, all four types | pass | pass | pass |
| override labels → mode, 15 | pass | **2 fail** | pass |
| `effectiveMode`, 5 | pass | **1 fails** | pass |
| display names and normalisation, 22 | pass | pass | **8 cannot run** |

- **The classifier is identical in all three** on every case any edition tested — the question the pilot was for.
- **Python, labels:** `from_mode_string("Helmholtz T(1,1)_1")` gives the legacy `HELMHOLTZ`, not `AIR` (the old test
  compared after normalising, so it passed); and an unresolvable label ("Wolf note") gives `UNKNOWN` where Swift's
  `fromDisplayName` gives nil — Python cannot tell an unknown label from the label "Unknown".
- **Python, `effectiveMode`:** an empty override `""` keeps the auto mode (`if override:`); Swift and the web treat it
  as a label that resolves to nothing — `unknown`.
- **Legacy modes** (`helmholtz`, `crossGrain`, `longGrain`, `monopole`): the web has none. In Swift nothing creates or
  reads them — no saved model has a `GuitarMode` field, the file's `modeLabel` is ignored on decode, and no file in
  the hub's `Tests/` holds a legacy name; only Python's label resolver produces one (above).
- *Recommendation:* (1) Python's resolver as Swift's — the academic labels give the current modes, an unresolvable
  label `None`, its callers checked; (2) Python's `effective_mode` resolves any override present, `""` included, as
  Swift; (3) the legacy modes removed from Swift and Python, unused, as the web never had them; (4) the pilot's
  clean-up — the per-frequency lookup private in Python and the web, Python's `_classify_all_tuples` and
  `classify_peak` gone, the stale comments fixed (and Python's "falling back to Classical", which falls back to
  Generic); (5) each edition's old `classify` cases deleted, the shared file holding them, the old files keeping only
  what the data cannot express. *Decision (owner, 2026-10-02):* "Yes to all."
- *Raised while doing it:* with the legacy modes gone, `normalized` (legacy → current) does nothing — every mode is
  its own normal form; about 20 call sites in each native, none on the web. And Python's one remaining old test pinned
  the UNKNOWN mode's range (0–20,000 Hz), which no caller reads — the natives' range function must return something
  for every case, the web models "unknown" as no band. The legacy modes (`helmholtz` "Helmholtz (Air)", `crossGrain`
  "Cross-Grain", `longGrain` "Long-Grain", `monopole` "Monopole" — old names for Air, Air, Top, Back) are not the
  override picker's academic labels: the picker stores a label, resolved by `fromDisplayName` to a current mode; the
  only link was Python's resolver turning "Helmholtz T(1,1)_1" into `helmholtz`. *Recommendation:* remove
  `normalized` with the legacy modes, and the unknown-range test. *Decision (owner, 2026-10-02):* "Yes".
- *Done (2026-10-02; Swift `8fdd350`, Python `7c20911`, web `9b49fc2`):* `classify.json` — 45 `classifyAll` sets, 3 `resolvedModePeaks`, the four types'
  bands, 15 override labels and the seven academic labels' order, 5 `effectiveMode`, 7 display names, 7
  abbreviations (all three have the same; added) — passes in all three. Python: `GuitarMode.from_display_name`
  (Swift's `fromDisplayName`: `None` for a label it cannot resolve; the academic labels give current modes) replaces
  `from_mode_string`, its callers checking for `None` where they compared with `UNKNOWN` and "Unknown"; `effective_mode`
  resolves any override present; the per-frequency lookup is `_classify`; `_classify_all_tuples` and `classify_peak`
  removed, the results table's model calls `classify_all`. Web: `classifySingle` no longer exported. Swift and
  Python: the four legacy modes and `normalized` removed (about 20 call sites each; the switches over the mode now
  exhaustive without a fallback); the legacy-colour tests removed from `test/mode-colors`. Comments: Swift
  `UserAssignedMode.swift`, `TapToneAnalyzer+PeakAnalysis.swift`; Python `user_assigned_mode.py`, the analyzer's
  "falling back to Classical" (it falls back to Generic) and two that named `classify_peak`. The move: Swift
  `GuitarModeTests.swift` and Python `test_guitar_mode.py` deleted (every case is in the shared file); the web's
  `classify.test.ts` keeps one test the data cannot express (the band list is a fresh copy). Parity map: `test/classify`
  is the three runners plus that web file; 116 groups, `--check` clean; `check-fixtures.py` keeps the three copies of
  `classify.json` identical. Suites: Swift 717 (its classification tests are now 6 parameterised), Python 935, web
  826; Swift macOS and iOS Simulator build.

**Group A, batch 1 (2026-10-02; Swift `3d6eeba`, Python `2cbca0e`, web `2446bdf`)** — `field-precision`, `frequency-format`, `analysis-quality`, `quality-colors`,
`measurement-name`, `export-filename`. Each slug's cases moved into `tooling/parity/cases/<slug>.json` (copied into
the three editions' fixtures) and run by one file per edition, in the old test file's place; what the data cannot
express stays beside it (Swift: the quality colour is built from the pinned hex, not a system colour; web: the dark
quality colours, which only the web has). Two rewrites on the way: the "each type at its thresholds" decay cases and
the name/notes agreement checks read their inputs from the code under test — they are literal rows now.

| slug | cases | Swift | Python | web |
|---|---|---|---|---|
| `field-precision` | 59 | pass | pass | pass |
| `frequency-format` | 12 | pass | pass | pass |
| `analysis-quality` | 53 | pass | pass | pass |
| `quality-colors` | 5 grades | pass | pass | pass |
| `measurement-name` | 35 | pass | pass | pass |
| `export-filename` | 11 stems, 3 measurements | pass | pass — failed 1 until fixed (below) | pass — failed 1 until fixed (below) |

- **`export-filename`:** Swift's `ExportFilename.stem` takes the time and keeps whole seconds itself
  (`Int(timestamp.timeIntervalSince1970)`); Python's `export_stem` and the web's `exportStem` take seconds and print
  them as given — a fractional time gives `x-1784060789.123456`. Every caller in Python and the web passes whole
  seconds today (each truncates first), so no filename is wrong; the rule lives in the callers rather than the
  function. *Recommendation:* the two functions keep whole seconds themselves (truncating, as Swift's `Int()` does),
  so the rule is where Swift has it.
  *Decision (owner, 2026-10-02):* "Yes please". *Done:* `export_stem` writes `int(epoch_seconds)`, `exportStem`
  `Math.trunc(epochSeconds)`; the fractional case passes in all three.
- **The fixture check's four "drifts"** (raised in the survey): `7108913.txt` was CRLF only in this machine's web
  working copy — the repository holds it LF, as Swift's and Python's; the copy predates the web's `.gitattributes`
  and had never been rewritten. The three `self-baseline-*.json` are each edition's own per-machine baselines
  (`test/self-regression`), different by design but compared by name. *Decision (owner, 2026-10-02):* "Yes" —
  the working copy refreshed from git (nothing to commit), and `check-fixtures.py` ignores `self-baseline-*` as it
  ignores `parity-oracle.json`. It now reports no drift: 53 shared fixtures, all byte-identical.
- Suites: Swift 690 (its batch-1 tests now parameterised over the shared files), Python 1072, web 958; Swift macOS
  and iOS Simulator build; parity map 116 groups, `--check` clean.

**Group A, batch 2 (2026-10-02; Swift `2e8a208`, Python `e693b46`, web `937b172`)** — the slugs where part of the file is a table. Each table moves into its
shared file; the rest of the file (scenarios, signals) stays as code.

| slug | cases | Swift | Python | web |
|---|---|---|---|---|
| `display-range` — `DisplayRangeExpansion` (widening; Settings Done; a new measurement; widening while showing a load) | 24 | pass | pass | pass |
| `button-enablement` — B1–B16, each giving only the fields it sets, so the editions' defaults are checked too (the Save / export scenario stays as code) | 16 | pass | pass | pass |
| `measurement-type-name` — the Details pane's type word and the material flag (in-memory measurements) | 19 | pass | pass — MT08 failed until fixed (below) | pass — MT08 failed until fixed (below) |
| `measurement-amend` — `isAmended`, the gate on Save (the amend itself, which mints an id, stays as code) | 8 | pass | pass | pass |
| `settings-store` — per-type default ranges, a range field's entered value, validation of an entered range (the store's read and write stay as code) | 21 | pass | pass | pass |
| `decay-tracking` — `measureDecayTime` on given histories, DK1–DK5 and DK8–DK10, and the default threshold (one tolerance, 1e-6, for all three; the web used 5e-7); the tracker driven chunk by chunk stays as code | 9 | pass | pass | pass |

- **`measurement-type-name`:** Swift resolves a measurement's type field by field —
  `spectrumSnapshot?.measurementType ?? longitudinalSnapshot?.measurementType` (`resolvedMeasurementType`) — and its
  Details word (`measurementTypeShortName`) and material flag both read that. Python's `_type_name` and the web's
  `measurementTypeName` take the first snapshot that exists and read its type, so a spectrum snapshot with no type
  hides the longitudinal snapshot's: MT08 (spectrum snapshot untyped, longitudinal "Material (Brace)") is "Brace" in
  Swift and "—" in both. Each port also has a second resolution that disagrees with its first: the web's
  `resolvedMeasurementType` is Swift's chain (its `isMaterialMeasurement` uses it), and Python's model
  `resolved_measurement_type` takes the first snapshot and then falls back to the top-level type, which Swift has no
  field for. And the word lives on the model in Swift (`measurementTypeShortName`), in a view helper over stand-in
  objects in Python, and in `fromLive.ts` on the web. MT09–MT11 (an unrecognised type, a loaded file's top-level
  type) run only in Python and the web — Swift's enum cannot hold an unknown type and its model has no top-level type.
  *Recommendation:* one resolution, Swift's, for the word and the flag in every edition — the web's
  `measurementTypeName` reads `resolvedMeasurementType`; Python's model `resolved_measurement_type` follows Swift's
  chain, a model property `measurement_type_short_name` (Swift's `measurementTypeShortName`) gives the word, and the
  Details view calls it. Open: Python's fallback to the top-level type. *Owner (2026-10-02):* "Check all the
  measurements in the hub and in the editions - does it have the problem case? If not then make it the same as
  swift." Checked: 157 `.guitartap` files in the hub's `Tests/` and the three editions' test folders, 176
  measurements (9 comparisons); every other one has exactly one snapshot, typed — 99 a spectrum snapshot, 68 a
  longitudinal one. None has an untyped snapshot beside a typed one, none relies on the top-level type, and none has
  a top-level type that differs from its snapshot's. So: the same as Swift, the fallback dropped.
  The guitar type, which the save path resolves the same way, checked too: every measurement's snapshot carries it.
  *Done:* Python — `resolved_measurement_type` is Swift's chain (no top-level fallback); a new
  `measurement_type_short_name` (Swift's `measurementTypeShortName`) gives the word and the Details view shows it
  (`_type_name`, the view's own resolver, removed); `to_dict` writes the top-level `measurementType` and `guitarType`
  by the same chain. Web — `measurementTypeName`, the save path's top-level copies and the mode-label builder all
  read `resolvedMeasurementType` (the save path's guitar type by the same chain). Python's runner now tests the
  model property on real `TapToneMeasurement`s, not stand-ins. All 19 cases pass in all three.
- Suites after batch 2: Swift 631 (more tests parameterised over the shared files), Python 1094, web 975; Swift macOS
  and iOS Simulator build; parity map 116 groups, `--check` clean; `check-fixtures.py` 59 shared fixtures, no drift.

**Group A, batch 3 (2026-10-02; Swift `d414025`, Python `5994aa0`, web `828c8f4`)** — the fixture-list slugs and the oracle's. The fixtures and expected
values move into shared files; the checks stay in each runner.

| slug | cases | Swift | Python | web |
|---|---|---|---|---|
| `material-selection` — the iPad plate whose saved selection was clobbered resolves all three peaks | 1 | pass | pass | pass |
| `peak-heal` — the fixture with a twin peak decodes healed, keeps the selected twin, leaves nothing dangling, reports the heal and never saves it | 1 fixture, 5 checks | pass | pass | pass |
| `pdf-report` — the fixture list and the 1 pt baseline tolerance (`pdf-report.json`) | 18 | pass | pass | pass |
| `spectrum-export` — pixels and pixels per inch (`spectrum-export.json`) | 3 | pass | pass | pass |
| `peaks` (fixture regression) — the fixture list is `peak-baseline-expected.json`'s keys | 3 | pass | pass | pass |
| `gated-fft` — one test over the oracle's tone cases | 4 | pass | pass | pass |
| `file-playback` — what each REG case checks (`file-playback.json`); the expected values stay the oracle's | 8 cases, 8 kinds of check | pass | pass | pass |

- On the way: the three `peak-heal` files probed the heal flag indirectly, with comments saying it "does not exist
  yet" — it does; Swift and Python now read it directly, and the web's measurement type declares `wasHealed` (decode
  set it untyped). The web's store does not read the flag: its library holds decoded objects in IndexedDB, so it runs
  the heal itself on read — forced by the storage, and documented there. The headers' project history ("authored
  against the unfixed code", "step 8") is gone. `material-selection`'s Swift test now decodes through
  `TapToneAnalyzer.decodeMeasurements`, the production path, as the others do.
- `file-playback`: first recommended to stay as code, since its expected values are already the oracle's. The owner
  (2026-10-02): "Since the goal is to have identical tests across the editions how does just having the values
  acheive that?" It does not — shared values fix the answers, not what each edition checks. The three run the same
  18 cases by name (levelled in F52 / F53), plus Python's main-thread check (a Qt rule) and two web tests of the
  playing file's name; whether same-named tests assert the same things is unverified. *Recommendation (revised):*
  the shared file names what each REG case checks (averaged peaks by role, per-tap peaks, ring-out, phases captured
  with a relative noise floor), one runner per kind of check in each edition; the playback rules (cancel, a type
  change, the session recording, provenance, calibration) stay as code; the web's file-name tests checked against
  Swift and Python. *Decision (owner, 2026-10-02):* "Proceed on file-playback proposal."
  *Done:* `file-playback.json` lists the 8 cases (REG-B1, B2, G1, the REG-G ring-out, G2, P1, P2, OUT-4) and, for
  each, its checks: `materialPhaseComplete`, `measurementComplete`, `capturedTaps` / `tapEntries` (count), `peaks`
  (roles and fields against the oracle's `peaks` or `averagedPeaks`), `perTapPeaks`, `ringOut`, `phasesCaptured`,
  `noiseFloorBetween`. Each edition plays the oracle entry's fixture, calibration and settings through its
  file-playback path and runs one branch per kind; an unknown kind fails. Swift asserts at `selfTolerances` (zero),
  Python and the web at `tolerances`. The 8 hand-written REG tests in each edition are gone; the expected-value
  constants Python kept for them are gone too (the rule tests keep the fixtures and settings they play).
  The playing file's name: the behaviour is the same in all three (set when a playback starts, kept when the file
  ends, cleared by a stop or a new sequence). Swift and Python checked "cancel clears it" inside their cancel test,
  the web in a separate test; the web's check moved into its cancel test, Swift's shape. "Named while it plays,
  kept at the end, cleared by a new sequence" was web-only; Swift and Python now have it.
- Suites after batch 3 and `file-playback`: Swift 622 (Swift Testing counts a parameterised test once: the 8 REG
  tests became 1, plus the file-name test), Python 1095, web 974 (the separate cancel file-name test folded into the
  cancel test); Swift macOS and iOS Simulator build; parity map 116 groups, `--check` clean; `check-fixtures.py` 64
  shared fixtures, no drift.

**Group B — `pitch` (2026-10-02; Swift `5a22fda`, Python `3f03523`, web `d39196d`).** `pitch.json` is the union of the three editions' inputs (Swift 32,
Python 32 and web 26 tests, with different frequencies, tolerances and checks), plus new cases for the two findings
below. Each frequency row checks every function at once: `hasPitch`, `pitch` (note index and octave), `note`,
`cents`, `freq0`, `pitchRange`, `formattedNote` and `isInTune`. Other rows check a threshold, the inclusive
comparison (in tune at exactly its own offset, not a hair under), `freq(note, octave)` and `formatCents`. The
expected values were minted by compiling Swift's `Pitch.swift` with a driver; the tolerance is 1e-9.

| | cases | Swift | Python | web |
|---|---|---|---|---|
| frequencies (440 and 432, sharp/flat branches, octave crossings, below C0, no pitch) | 44 | pass | pass (failed 1 before item 2) | pass (failed 2 before item 2) |
| `isInTune` at a threshold | 5 | pass | pass | pass |
| `isInTune` at its own offset (inclusive) | 1 | pass | pass | pass |
| `freq(note, octave)` | 5 | pass | pass | pass |
| `formatCents`, 12 values including the half ties | 1 | pass | pass | pass |

1. **Swift traps below C0.** `pitch(frequency:)` split the half-step count with `/` and `%`, which truncate. Below
   about 15.9 Hz the count is negative, the note index goes negative and `noteNames[note]` traps. The analysis range
   reaches 1 Hz (`DisplayRange.frequencyBounds`), and every found peak gets a note, so the app can reach it. Python
   and the web floor: 12 Hz is G-1, 10 Hz D#-1. *Recommendation:* Swift floors as they do (the alternative: below
   C0 is "no pitch", as 0 Hz is). *Decision (owner, 2026-10-02):* "Item 1 I agree with your suggestion."
   *Done:* Swift floors the octave and the note.
2. **The half-step count's rounding differs at an exact half.** Swift rounds a half away from zero, Python to even,
   the web up (`Math.round`). At 427.47 Hz (50 cents below A4, exactly 56.5 half-steps) Swift and the web give
   "A4 (−50 cents)", Python "G#4 (+50 cents)". Below C0 the web's `Math.round` gives the integer −0 (16 Hz:
   octave −0), which Swift's `Int` cannot be; it prints as 0, but it is a different value. *Recommendation:*
   Python and the web round as Swift does. *Decision (owner, 2026-10-02):* "Your recommendation on item 2 as
   well." *Done:* Python `_round_half_away_from_zero`, web `roundHalfAwayFromZero` (a plain integer, never −0).
- Suites after `pitch`: Swift 598 (Swift Testing counts each parameterised test once), Python 1119, web 1006; Swift
  macOS and iOS Simulator build; parity map 116 groups, `--check` clean; `check-fixtures.py` 65 shared fixtures, no
  drift.

**Group B — `plate` and `brace` (2026-10-02; Swift `da367e5`, Python `308d0e3`, web `288d003`).** The survey: 39/41/34 and the brace equivalent; the same
formulas, different shapes. Done together, because the first finding is one model for both.

1. **The web had no plate or brace model.** Swift computes every value as a property of `PlateProperties` /
   `BraceProperties` (E, c, specific modulus, radiation ratio, the anisotropy ratios, the grades, the Gore moduli and
   shear, `goreTargetThickness(...)` as a method); Python has the same model. The web had only free functions
   (`plateYoungsLongPa`, `speedOfSound`, `specificModulus`, …), and each caller assembled the values itself — the
   Results panel and the measurement image, which the PDF also reads — as did its tests, so they did not test what
   the app shows. *Recommendation:* the web gets Swift's `MaterialDimensions`, `PlateProperties`,
   `BraceProperties` and `WoodQuality` (`evaluate`, `numericScore`), the callers use them, the free functions become
   internals. *Decision (owner, 2026-10-02):* "Yes".
2. **Python's Gore target thickness was a free function** (`calculate_gore_target_thickness(props, …)`), a method in
   Swift; Python also had `calculate_plate_properties` / `calculate_brace_properties` wrappers Swift does not.
   *Recommendation:* a method on `PlateProperties`; callers construct the model directly. *Decision (owner,
   2026-10-02):* "Yes".
3. **When the properties are shown differs** (found while doing 2). Python's wrappers raise `ValueError` when a
   dimension or frequency is not positive; at the end of a live measurement the main view shows a "Calculation
   Error" dialog, elsewhere the callers show no properties. Swift has no such check: its zero guards give 0s.

   | | Results panel | export image / PDF |
   |---|---|---|
   | Swift | needs the fL and fC peaks and the measurement's dimensions | needs fL and fC, and length > 0 and mass > 0 |
   | Python | all four dimensions and the frequencies positive, else the dialog (live) or nothing (loaded) | all four dimensions positive |
   | web | needs fL and fC | a missing fL or fC computed as 0 Hz |

   *Recommendation:* follow Swift — Python's wrappers and the dialog go, and Python's and the web's conditions become
   Swift's. *Alternative:* the Gore method only, the rest recorded for later. *Decision (owner, 2026-10-02):* "Your
   recommendation - full fix/not partial fix."
4. **Comparing the values:** Swift computes in 32-bit `Float`, Python and the web in doubles; they agree to about one
   part in a million. The shared file holds Swift's values, compared at a relative tolerance of 1e-5.
5. **Python's G_LC is `None` for an fLC of 0**, where Swift computes it (0) and returns `nil` only when there was no
   FLC tap (`if self.f_flc is None or self.f_flc <= 0`). No caller passes 0 — a missing tap is `None` — so no
   output differs; found by reading. The web matches Swift. *Recommendation:* Python tests only for `None`, as
   Swift. *Decision (owner, 2026-10-02):* "Yes". *Done:* Python tests only for `None`; `plate.json` gains "real
   plate, an fLC of 0 Hz" (G_LC 0), which all three pass.

*Done (1–3; 5 above):*
- **Web:** `src/dsp/material.ts` holds `MaterialDimensions`, `PlateProperties`, `BraceProperties` and `WoodQuality`
  (`evaluate`, `numericScore`; wood types spruce, cedar, maple, rosewood, as Swift); the beam formula is private.
  The Results panel, the Settings density read-out and the report data use them. The report builds the material
  section only from fL (and fC for a plate) and a sample with length and mass, as Swift; otherwise it has none
  (it used to compute a missing frequency as 0 Hz).
- **Python:** `PlateProperties.gore_target_thickness(...)`; `calculate_plate_properties`,
  `calculate_brace_properties`, `calculate_gore_target_thickness` and `MaterialDimensions.is_valid` are gone. The
  Results panel is filled from `_calculated_plate_properties` / `_calculated_brace_properties` — Swift's
  `calculatedPlateProperties` / `calculatedBraceProperties`: the identified peaks and the measurement's own
  dimensions (Store B), no other check — in all four places it was filled (a measurement's end, a dimension edit, a
  load, a settings change). The "Missing Dimensions" and "Calculation Error" dialogs at a measurement's end are
  gone. The two report builders build properties when the peaks are there and length > 0 and mass > 0, as Swift.
- **Case files:** `plate.json` (16 plates, each with every property and its Gore target thicknesses; 41 grade
  rows over all four wood types — cedar, maple and rosewood new; the five scores) and `brace.json` (7 braces), the
  union of the three editions' samples. The identities the old tests checked (E ∝ f², E ∝ L⁴, c = √(E/ρ), the
  reciprocal ratios, the brace's 22.37332) are pinned by each row's values. Expected values minted by compiling
  Swift's `MaterialProperties.swift` with a driver.

| | cases | Swift | Python | web |
|---|---|---|---|---|
| plates — every property, the Gore target thicknesses | 16 | pass | pass | pass |
| grades (`WoodQuality.evaluate`), all four wood types | 41 rows | pass | pass | pass |
| numeric scores | 5 rows | pass | pass | pass |
| braces — every property | 7 | pass | pass | pass |

- Suites after `plate` and `brace`: Swift 539 (the per-property tests became two parameterised ones), Python 1078,
  web 973; Swift macOS and iOS Simulator build; parity map 116 groups, `--check` clean; `check-fixtures.py` 67
  shared fixtures, no drift.
3. **The cents rounding was testable only in the web.** `formattedNote` rounds the cents offset half to even
   (C's `%.0f` in Swift, `:.0f` in Python); the web hand-wrote that rounding (`roundTiesToEven`, since `toFixed`
   rounds a half away from zero) and tested it at exact halves, which no frequency can reach. *Options:* (a) each
   edition gets a cents formatter and the half-tie rows go in the shared file; (b) drop the web's test.
   *Decision (owner, 2026-10-02):* "I like (a)." *Done:* `Pitch.formatCents(_:)` (Swift), `Pitch.format_cents`
   (Python), `Pitch.formatCents` (web, replacing `roundTiesToEven`); `formattedNote` uses it in all three.

**Group B — `dsp` (2026-10-02 – 10-04; Swift `f082a55`, Python `180b595`, web `7fef7a6`).**

1. **The cases differ, and every check is loose.** F1–F5 are the same arrays in all three; F6 uses a 1024-bin
   spectrum in Swift and 2048 in the others; F9 pins bandwidth 990 and Q 0.505 in Swift and Python, while the web
   checks only "not NaN" under a comment saying Q "falls back to 0". No F-case pins a value ("shifted left",
   "sharp Q > broad Q", "0 < Q < 15"). The silence and level tests: Swift 4 (the gated path only), Python 8, web 7.
   *Proposal:* one `dsp.json`, values minted from Swift — `parabolicInterpolate` (F1–F5, the synthetic peak at 1024
   and 2048 bins), `calculateQFactor` (sharp, broad, both flat spectra), and the union of the silence and level
   cases (gated FFT, live FFT, live peak, a chunk's detection and readout levels) as signal → result.
2. **Swift's header says its live path cannot be called without starting the engine.** Out of date: `init` builds
   the rectangular window, so `computeFFT` runs on a test analyzer. Swift gains the live-path cases.
3. **The web's peak analysis is free functions; Swift's and Python's are analyzer methods.** Swift has
   `parabolicInterpolate`, `calculateQFactor`, `findPeaks` and the rest on `TapToneAnalyzer`
   (`TapToneAnalyzer+PeakAnalysis.swift`), as does Python; the web has them in `src/dsp/peaks.ts`. One
   implementation each — a difference in where the code lives. *Recommendation:* leave it and record it.
   *Decision (owner, 2026-10-02):* "Please remove the divergence in the web code." — the web's peak analysis moves
   onto its `TapToneAnalyzer`, as Swift's.
4. **The FFT code has the same divergence** (found doing 3). Swift's live FFT (`computeFFT(on:)`) and live peak
   (computed in `performFFT`, published as `peakFrequency` / `peakMagnitude`) are `RealtimeFFTAnalyzer` methods;
   Python's are module functions (`dft_anal`, `perform_fft(analyzer, …)`); the web's are free functions
   (`dftAnalRect`, `spectrumPeak` in `dsp/guitarFFT.ts`). The gated FFT is a method in all three. *Options:* (a)
   the same treatment now — methods on the engine in Python and the web; (b) finish `dsp` on the code as it is
   and record the difference. *Recommendation:* (a). *Decision (owner, 2026-10-02):* "(a) please".

*Done (1–4):*
- **Web — peak analysis on the analyzer (3):** `TapToneAnalyzer.findPeaks`, `removeDuplicatePeaks`,
  `parabolicInterpolate`, `calculateQFactor` (Swift's name; was `calculateQ`), a private `makePeak`, the static
  `peakProximityHz` and `peakDetectionFloor`, and the analysis range as `minFrequency` / `maxFrequency`.
  `findPeaks` takes its defaults from the analyzer, as Swift's — the range, `peakMinThreshold`, `pitchCalculator`.
  `src/dsp/peaks.ts` is gone; the analysis-range constants moved to `settings.ts` (Swift `TapDisplaySettings`);
  `dsp/find-peaks` is tagged on `ResonantPeak`, as the natives. The `peaks` tests call the analyzer (their own
  rework is step 6).
- **Web — the live FFT on the engine (4):** `RealtimeFFTAnalyzer.computeFFT` (Swift `computeFFT(on:)`),
  `performFFT` (calibration and the live peak, `peakFrequency` / `peakMagnitude`), `frequencies`, and
  `processRawSamples` (Swift's per-chunk entry; was a private `processChunk` whose callers computed the RMS),
  with `inputLevelDB` / `readoutLevelDB`. `dftAnalRect` and `spectrumPeak` are gone. The guitar capture calls
  the engine's `computeFFT`, as Swift's calls `fftAnalyzer.computeFFT`.
- **Python — the live FFT on the analyzer (4):** `RealtimeFFTAnalyzerFFTProcessingMixin` with `compute_fft`
  (returns the dB spectrum, as Swift) and `perform_fft`, beside the EngineControl and DeviceManagement mixins;
  `dft_anal`, the module `perform_fft(analyzer, …)` and the unused `hps_peak_freq` are gone. The frame signal no
  longer carries a linear spectrum (stored, never read; Swift has none). `input_level_db` added (Swift
  `inputLevelDB`).
- **Swift (2):** the stale header is gone with the old tests; Swift runs the live-path cases.
- **`dsp.json` (1):** values minted by running Swift's production code in a temporary test. The tones are
  generated in double precision and rounded to Float per sample in every edition — Float's `sin` loses phase at
  the large arguments a 65536-sample tone reaches, which moved Swift's live peak by 0.0005 dB.

| | cases | Swift | Python | web |
|---|---|---|---|---|
| `parabolicInterpolate` — F1–F5, the synthetic peak at 1024 and 2048 bins | 8 | pass | pass | pass |
| `calculateQFactor` — sharp, broad, both flat spectra | 4 | pass | pass | pass |
| signals — gated FFT, live FFT, live peak, a chunk's levels, each for silence and a tone; the live FFT of DC, Nyquist and both | 11 | pass | pass | pass |

5. **The live spectrum differs in length and bin 0** (found doing 4, measured). Swift's live FFT has 32768 bins;
   vDSP's real DFT packs DC and Nyquist into bin 0 and Swift does not unpack them, so its bin 0 is DC doubled (+6 dB)
   mixed with Nyquist, and it has no Nyquist bin (constant 0.5: Swift 0.0 dB, Python and web −6.02 dB; alternating
   ±0.5: Swift 0.0 dB in bin 0, Python and web −6.02 dB in a 32769th bin). Only 0 Hz and 24 kHz are affected —
   peak analysis is 30–2000 Hz and the display 1–5000 Hz — but saved guitar spectra are 32768 values from Swift
   and 32769 from Python and the web, and with a DC offset Swift's idle Peak readout reads 0 Hz 6 dB high.
   *Options:* (a) Python and the web copy Swift's packed bin 0; (b) Swift unpacks, adding a Nyquist bin (32769);
   (c) all three 32768 bins with a correct bin 0 — Swift's bin 0 is DC alone, Python and the web drop the Nyquist
   bin. *Recommendation:* (c). The owner asked for the practical effect, then for verification that files of
   different lengths cause no problem. *Verified:* all 157 measurement files (hub and editions), 99 guitar
   measurements (69 of 32768 values, 30 of 32769): in every edition each decodes, loads and re-analyzes with peaks,
   and a comparison of a 32768 and a 32769 measurement overlays both; every length check in the code compares
   arrays of one capture or a snapshot's own frequencies — nothing combines two measurements by bin index. Not
   run: the PDF / image export of a loaded 32769 measurement (read only). *Decision (owner, 2026-10-02):* "It
   looks like (c) is safe and is my preference. Go".
   *Done:* Swift's bin 0 is DC alone — `abs(realp[0]) · 0.5` after vDSP's scaling, the packed Nyquist dropped;
   Python's `compute_fft` and the web's `computeFFT` stop at the last bin below Nyquist (32768 bins), and their
   live frequency axes and live calibration follow (Python `freq`, the canvas's initial calibration, the capture's
   fallback axis; the web engine's `frequencies` and calibration cache). `dsp.json` gains three live-FFT cases —
   a constant 0.5 (DC), an alternating ±0.5 (Nyquist), both — each pinning the bin count, bin 0 and the last bin,
   and the two existing live-FFT cases pin the bin count. All 23 cases pass in all three.
- Suites after `dsp`: Swift 528, Python 1084, web 979; Swift macOS and iOS Simulator build; parity map 116
  groups, `--check` clean; `check-fixtures.py` 68 shared fixtures, no drift.

**`dsp` run-review (done — owner, 2026-10-04: "all 3 editions have been verified").** The live audio path changed in all three editions
(the web's peak analysis and live FFT moved onto its analyzer and engine; Python's live FFT onto its analyzer;
one live-spectrum length and bin 0 everywhere), so it is run-reviewed before the commit. Launch: Xcode scheme
`guitar_tap` · `.venv/bin/python -m guitar_tap` · web `npm run build && npm run preview`, then clear the service
worker after the build (the procedure in F30's run-review steps — a web result without it is not a result). Same list per
edition, Swift first.

1. Start the app with the UMIK-1 in a quiet room. → The live spectrum draws as before; the Peak readout shows a
   level and a frequency.
2. Switch the input to the BlackHole virtual device, which delivers digital silence. → The Peak readout shows
   −∞ dB. (Muting or unplugging the UMIK-1 cannot do this: a muted mic still carries noise, and unplugging
   switches devices.)
3. Take a guitar measurement of 1 tap, then one of 3 taps. → Peaks, modes and Q look as before.
4. Take a plate measurement. → fL, fC, fLC and the material results look as before.
5. Load a saved guitar measurement from each edition (Swift, Python, web), then compare two of them. → Each loads;
   both overlays draw.
6. Re-analyze a loaded guitar measurement. → The peaks come back.

| step | Swift | Python | web |
|---|---|---|---|
| 1–6 | ✅ (2026-10-04) | ✅ (2026-10-04) | ✅ (2026-10-04) |

- **Step 4, Swift (owner, 2026-10-03).** First tried by playing the first tap of
  `Tests/AllPlatforms/plate-umik-1-swift-mac-1785359486.wav` through the speaker into the UMIK-1 (threshold −53):
  fL 29.3 Hz, fC 117.4 Hz, fLC 36.3 Hz — looked wrong. Not the code: the session WAV (what the mic heard) shows
  the speaker path lost the low modes — 67 Hz arrived at −79…−82 dB, 16 dB *below* 117 Hz, where the recording has
  it 6 dB *above* (−42.3 against −48.2 dB) — so the pickers took noise at ~30 and ~36 Hz. Replaying that session
  WAV through the plate pipeline gives the same (fL 30.0, fC 117.6, fLC 33.1 Hz). Then run through a lossless
  loopback (the recording played to BlackHole, BlackHole as the input): fL 67.0 Hz each time. A speaker cannot
  test plate capture; real taps or a loopback can.

**Group B — `peaks` (2026-10-04; Swift `7855a3d`, Python `8837a28`, web `8f31b91`).** Synthetic peak finding (F10–F17, the duplicate regression
D1–D4), spectrum averaging (A1–A5) and the full-set save; the fixture cases moved in batch 3.

1. **Spectrum averaging is a free function in the web** (`averageSpectra()` in `src/dsp/spectrumAverage.ts`);
   Swift's `averageSpectra(from:)` and Python's `average_spectra` are analyzer methods. With no taps Swift and
   Python return an empty spectrum; the web throws. *Recommendation:* a method on the web's analyzer, empty for no
   taps. *Decision (owner, 2026-10-04):* yes.
2. **Saving in the web differs from Swift in three ways** (the web's analyzer already owns the guitar and material
   save): (a) no `guitarFullSavePeaks()` — `buildMeasurement` passes `this.peaks` itself; (b) a comparison is saved
   by `App.tsx` building the record (`buildComparisonMeasurement`) and storing it, where Swift calls
   `analyzer.saveComparison(measurementName:notes:)`; (c) the record builders are exported free functions in
   `fromLive.ts` (`buildGuitarMeasurement`, `buildMaterialMeasurement`, `buildComparisonMeasurement`) that about
   eight test files call with hand-made arguments, where Swift builds inside `saveMeasurement` / `saveComparison`.
   First recommended deferring (c) to the `measurement-codable` step; the owner: "Since the change in the web is
   code and not testing there is no reason to wait … Fix it now so it is correct." *Recommendation:* (a)
   `guitarFullSavePeaks()` on the analyzer, used by the save; (b) `saveComparison(name, notes)` on the analyzer,
   building from its comparison state, and the app's save and export call the analyzer; (c) the builders private to
   the analyzer, their tests driving an analyzer. *Decision (owner, 2026-10-04):* "yes do 1, 2 (a, b and c) and 3."
3. **Guitar auto-selection is a different function in the web.** Swift's `guitarModeSelectedPeakIDs(from:)` —
   `classifyAll`, the six named modes, the strongest per mode (the first on a tie), defaulting to `allPeaks`, the
   guitar type from the settings — and Python's `guitar_mode_selected_peak_ids` are the same loop; the web's
   `guitarModeSelectedPeakIds(peaks, guitarType)` returns `resolvedModePeaks`'s winners, the same result today by a
   different route, with the peaks and guitar type supplied by the caller. *Recommendation:* the web's becomes
   Swift's loop, defaulting to the durable set and reading the guitar type from the analyzer's settings; the shared
   cases pin the result. *Decision (owner, 2026-10-04):* yes.
4. **The cases differ, and most checks are loose** (F10's width 20 against 15 Hz; F12's flat spectrum at 0 against
   −20 dB; "within 2 bins", "≥ 3 peaks"; only the web pins one exact Q; A5 Python-only; "a loaded measurement is
   not upgraded" missing in the web). *Plan:* `peaks.json`, minted from Swift — `findPeaks` (every edition's
   spectra and settings → the full peak list), `removeDuplicatePeaks`, `averageSpectra` (none, one, mismatched
   lengths), auto-selection on the overlap spectrum, and the full-set save on the real swift-mac fixture.
5. **The web passes the guitar type into four methods** — `reclassifyPeaks`, `resetToAutoSelection`,
   `reclassifyForGuitarTypeChange`, `applyFrozenPeakState` — where Swift's read it from the settings
   (`TapDisplaySettings.guitarType`). Found doing 3; wider than 3, so not folded in: the web's auto-selection takes
   Swift's defaults (the durable set, the analyzer's guitar type) but still accepts a type from those callers.
   *Recommendation:* the web reads the type from the analyzer's settings, as Swift, and callers stop passing it.
   *Decision (owner, 2026-10-04):* "I agree with your recommendation on 5. Do it before the run review."


*Done (1–5):*
- **Web, the guitar type (5):** `reclassifyPeaks()`, `resetToAutoSelection()`, `reclassifyForGuitarTypeChange()`,
  `applyFrozenPeakState(old, new)` and `guitarModeSelectedPeakIds(peaks?)` read the analyzer's own guitar type, as
  Swift's read the settings; `App.tsx` no longer passes one. Safe because the app syncs the type into the analyzer
  in a layout effect declared before the one that reclassifies; the recalculation already read the analyzer's
  type. Web suite 993 after it.
- **Web, averaging (1):** `TapToneAnalyzer.averageSpectra(taps)` — empty for no taps, a single tap unchanged, the
  first tap on different lengths, as Swift; `src/dsp/spectrumAverage.ts` is gone.
- **Web, saving (2):** (a) `guitarFullSavePeaks()` returns the durable set, and the guitar save uses it; (b)
  `buildComparisonMeasurement(name, notes)` and `saveComparison(name, notes)` on the analyzer, building from its
  comparison state — `App.tsx`'s save and PDF paths call the analyzer, never a builder; (c) the three record
  builders moved from `fromLive.ts` into the analyzer's module, unexported (`makeGuitarMeasurement`,
  `makeMaterialMeasurement`, `makeComparisonMeasurement`). The eight test files that called them now set an
  analyzer's state and save through it (`test/saveFromAnalyzer.ts`); all 113 of their tests pass.
- **Web, auto-selection (3):** `guitarModeSelectedPeakIds(peaks = the durable set, guitarType = the analyzer's)` is
  Swift's loop — `classifyAll`, the six named modes, the strongest per mode, the first on a tie.
- **`peaks.json` (4):** minted by running Swift's production code in a temporary test. 16 `findPeaks` cases (every
  edition's spectra and settings, each with its full peak list — frequency, magnitude, Q, bandwidth, pitch — plus
  the overlap at the −100 dB floor), 6 `removeDuplicatePeaks`, 11 `averageSpectra` (none, one, mismatched
  lengths), auto-selection on the overlap spectrum (modes Top, Back, Back; the first two selected), and the full-set
  save on the real swift-mac capture (the Air peak displayed no, saved yes; every saved peak its own id; a loaded
  set saved as it is). The web's `peak-fullset-save.test.ts` is folded in.

| | cases | Swift | Python | web |
|---|---|---|---|---|
| `findPeaks` | 16 | pass | pass | pass |
| `removeDuplicatePeaks` | 6 | pass | pass | pass |
| `averageSpectra` | 11 | pass | pass | pass |
| auto-selection | 1 | pass | pass | pass |
| full-set save | 1 | pass | pass | pass |

- Suites after `peaks`: Swift 514 (each parameterised test counts once), Python 1100, web 993; Swift macOS and iOS
  Simulator build; parity map 116 groups, `--check` clean; `check-fixtures.py` clean.

**`peaks` run-review (done — owner, 2026-10-04).** Only the web's production code changed — its averaging, auto-selection, guitar
type and every save path — so the run-review is the web's. Launch: `npm run build && npm run preview`, then clear
the service worker (F30's run-review steps).

1. Take a 3-tap guitar measurement and save it. → It appears in Measurements; reloading it shows the same peaks
   and selection.
2. Change the guitar type (e.g. Generic → Classical) with that result showing. → The peaks are relabelled for the
   new type and the selection resets to auto.
3. Press the wand after deselecting a peak. → The auto-selection comes back.
4. Save a plate measurement. → It reloads with fL, fC, fLC and the dimensions.
5. Compare two guitar measurements and save the comparison. → It appears in Measurements and reloads as the
   comparison.
6. Export a PDF of a guitar measurement and of a comparison. → Both export as before.

| step | web |
|---|---|
| 1–6 | ✅ (2026-10-04) |

- **A loopback plate capture (owner, 2026-10-04)** — `Tests/AllPlatforms/plate-umik-1-swift-mac-1785359486.wav`
  played through Audacity into BlackHole, captured live by the web (−48 dB, no calibration): fL 67.037 Hz −51.52 dB,
  fC 117.333 Hz −56.12 dB, fLC 35.867 Hz −60.24 dB — identical to replaying that WAV through the plate pipeline at
  −48 dB, so the web's live path reproduces file playback exactly. Against the original July capture
  (`…1785359486.guitartap`, UMIK-1 with calibration `7108913`, −56.47 dB) fC and fLC differ by exactly the
  calibration's correction (+0.69, +1.29 dB; frequencies within 0.006 Hz); fL differs by the correction (+0.98 dB)
  plus 0.95 dB and 0.09 Hz — the July live capture's window placement and build, not the editions (today's
  analysis gives 67.037 Hz at either threshold).

**Group B — `mode-colors` (2026-10-04; done with Issue #2 step 4 — Swift `382cfeb`, Python `450e1ce`, web `329a10e`; closed 2026-10-07).** The mode colours differ because the chart
backgrounds differ: Swift follows the OS (light or dark), Python is always white, the web always dark; Swift and
Python share one table, the web brightened five of seven for its dark chart. Swift's colour sits on the
`GuitarMode` model (its own source calls that a layer violation to shed with the theme work); the web's in its
presentation layer. Options were: (a) the web takes Swift's table now; (b) do Issue #2 (Theme — Light / Dark /
System) so all three have the same light and dark tables and the same background rule; (c) pin Swift's table for
the natives only. The owner (2026-10-04): "Once color schemes are available they will both respond to the current
color scheme and have the same numbers for the same scheme … My preference is to go ahead and do #2 since it keeps
coming up everytime we hit a color difference. Can you please spec it out?" — with three questions for the spec:
can the user choose the scheme or only follow the system; are all colours in all three editions inventoried and
assigned to what changes with the scheme; which schemes. The spec (`docs/completed/THEME-SPEC.md`, written 2026-08) is
being rewritten on a full colour inventory of the three editions; `mode-colors` resumes when #2 lands.

**Load path run-review (step 10 — complete).** Loading a measurement changed in all three editions — the whole load
moved into the model, and the views only display it — and the views are not covered by the tests, so it is
run-reviewed before the commit. Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, then clear the service worker after the build (F30's run-review steps). Same list
per edition, Swift first; (P) / (W) marks a step that is chiefly about Python or the web.

1. Set Peak Min to −40, then load a guitar measurement saved with a lower Peak Min (e.g. the annotation-override
   file). → The Peak Min slider and value show the measurement's own Peak Min, and the chart and peak list show its
   peaks under that value; Settings shows its type and Show Unknown Modes.
2. Load a measurement with dragged label positions, then one saved without any. → None of the first measurement's
   dragged labels remain.
3. Load a measurement whose microphone isn't connected. → The microphone warning appears; dismiss it.
4. Load a plate measurement. → The banner says "Settings from loaded measurement" with the plate's own threshold;
   the L/C/FLC spectra and peaks show, with no extra guitar line under them (P); the crosshair snaps to the phase
   curves (P).
5. Load a brace measurement. → Its L spectrum and its one peak show, with its own threshold.
6. Press New Tap so it is listening, then load a saved comparison. → The comparison is shown; the status stops
   listening, and a tap captures nothing.
7. Load a guitar measurement, then compare two or more measurements from the list. → The comparison shows; the
   results' microphone line is empty — a comparison has no microphone of its own.
8. With a guitar measurement loaded, change the type in Settings from Generic to Classical and press Done. → The
   measurement stays, reclassified as Classical. Then change it to Plate and press Done. → The result clears and a
   plate sequence starts.
9. Load a measurement, then press Re-analyze twice. → The button stays available after the first press (P).
10. In Measurements, import `Tests/AllPlatforms/dws-2024-umik-1-3-tap-swift-iphone-1785357764.guitartap` (saved with
    an automatic selection; a single import loads it). → The wand button is disabled. Import
    `Tests/AllPlatforms/dws-2024-umik-1-3-tap-swift-mac-1785359425.guitartap` (saved with a manual selection). → The
    wand is enabled; pressing it reselects automatically, and the wand is then disabled. (A measurement saved before
    the selection flag existed loads as manual — wand enabled — as the 29 July Swift saves in the library do.)
11. Change a setting, then reload the page (W) or relaunch the app. → The setting is kept, including the settings the
    last load restored.
12. Load a guitar measurement. Click a peak's dot. → Its card is highlighted and the dot is marked. Click another peak's
    card. → The highlight moves to it, on the chart and in the list. Click that card again. → Nothing is highlighted.
    Highlight a peak, then load another measurement. → Nothing is highlighted, on the chart or in the list.
13. Load a guitar measurement. → The Peak Min field (label, slider, value and, in Swift and Python, the reset button)
    is available; its value is green and the Threshold value blue; the Taps, Threshold and Peak Min labels are grey
    (secondary text). Load a plate measurement. → The whole Peak Min
    field is still shown, faded and unavailable. Compare two measurements. → The same.

| step | Swift | Python | web |
|---|---|---|---|
| 1–13 | ✅ (2026-10-15) | ✅ (2026-10-15) | ✅ (2026-10-15) |

**Run-review progress.** Swift passed steps 1–11 (owner, 2026-10-15), on a fresh build after the step 7 fix. Swift, step 7 (owner, 2026-10-15): after loading a guitar measurement, a comparison's
microphone line still named the loaded measurement's UMIK-1 (not connected) — Swift's and Python's `loadComparison`
kept the loaded result's recorded microphone, and with none the line would name the current input, wrong for a
comparison too. Decision (owner): a comparison shows no microphone. Fixed in all three — both comparison paths clear
the recorded microphone, and the results line shows none while a comparison is shown; the comparison PDF and the
spectrum image already show none in all three. New shared case LD7 (a mutation dropping Swift's clear fails it).
Step 7 to be re-run in all three. Swift, step 10 (owner, 2026-10-15): the wand was enabled for a library
measurement whose selection looked automatic — expected: that save (29 July) predates the selection flag, which loads
as manual; the step now names shared files saved automatic and manual, since each edition's library differs.
Python, step 10 (owner, 2026-10-15): after an import the chart's Peak Min line stayed at the previous −77 dB while the
slider, model and peak list had the file's −55, and a red star — the previous measurement's selected-peak marker —
stayed on the chart. Cause: the load handler sets the sliders without their signals (so the view does not write the
model), and Python's Peak Min slider signal was also what moved the chart's line and cleared the marker. Fixed: the
canvas's `show_peak_min` shows a Peak Min (line, label, marker cleared) and writes nothing; `set_threshold` writes the
model and uses it; the load handler calls only `show_peak_min`. Compared with Swift and the web (owner): the line is
right — Python's chart is told the model's Peak Min, as Swift's and the web's redraw from it. The marker was not:
Swift and the web keep ONE highlight, the model's `highlightedPeakID` / `highlightedPeakId`, keyed by peak id, which the
chart and the list draw from; Python's `highlighted_peak_id` was dead, and its highlight was passed between views by
frequency — the canvas's star, `analyzer.selected_peak` (written by the canvas) and the list's `selected_freq`.
Decision (owner): Python takes Swift's model — `highlighted_peak_id` is the store (`set_highlighted_peak`,
`toggle_highlighted_peak`, `highlightedPeakChanged`); a dot or card click toggles it; the star and the highlighted card
draw from it; `selected_peak`, the frequency-passing signals and the view's select/deselect handlers are gone; and a
load clears the highlight in all three (Swift and the web's guitar load did not). New shared case LD8 (a mutation
dropping the web's clear fails it), and run-review step 12. With the analyzer reading the saved measurement type,
four Python tests that relied on a type left by earlier tests now pin Generic, as Swift's do. Python steps to be re-run
from 1; step 12 in all three. Python (owner, 2026-10-15): after a plate load the Peak Min label and value were not
faded, as Swift's are — Swift disables its whole Peak Min row and draws it at 0.4 for plate/brace and in a comparison.
Python disabled only the slider, value and reset button; its label was never disabled, and the value's own colour hid
Qt's disabled look. The web hid the field for plate/brace instead of disabling it, and did not disable it in a
comparison. Both values were also drawn in the primary text colour, where Swift draws the Threshold value in the accent
text colour and Peak Min's in the Peak Min green, at medium weight. Decision (owner): Python and the web match Swift —
the whole field shown, disabled and faded to 0.4 for plate/brace and in a comparison, and the values in Swift's
colours. Fixed in both. Python's Taps, Threshold and Peak Min labels were in the default text colour, where Swift's
(and the web's) are secondary text: fixed (owner, 2026-10-15). Why the theme work missed these: its inventories listed
each edition's colour literals, and an item drawn in the default colour has none, so it never appeared. The web's
sliders still have no reset buttons (Swift and Python do): noted, not changed. New step 13, in all three. A sweep
for more such misses (owner, 2026-10-15) found 39 across the three editions: filed as #32
([`THEME-MISSED-COLOURS.md`](THEME-MISSED-COLOURS.md)), to be fixed after this run-review. **All three editions passed steps 1–13 (owner, 2026-10-15). Run-review complete.**

### Step 11 — scenario slugs

The scenario slugs: their tests become shared step scripts, run by a small runner per edition. This section is step
11's record — the status table first, then each item's decision and what was done, in the order of the table. The
run-reviews are the sections after it.

| # | item | batch | status | commits (Swift · Python · web) |
|---|---|---|---|---|
| A | DK9 | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| A | measurement-complete | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| A | tap-count-change | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| A | scenario-trace | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| A | state-invariants | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| A | tap-progress | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| A | annotation-state | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| A | session-pre-roll | A | done | `acce5cb` · `3b28c56` · `34eda6b` |
| B | status-message | B | done | `d7389de` · `8527a21` · `eeaf68e` |
| B | effective-peak-id | B | done | `d7389de` · `8527a21` · `eeaf68e` |
| B | display-range scenarios | B | done | `d7389de` · `8527a21` · `eeaf68e` |
| B | audio-clock-timers (bar the timeout) | B | done | `d7389de` · `8527a21` · `eeaf68e` |
| B | comparison (and its format, into measurement-codable) | B | done | `d7389de` · `8527a21` · `eeaf68e` |
| C1 | tap-decisions | C | done | `8b1989a` · `1e42d3e` · `63b33b5` |
| C2 | start-tap-race retired; scenario-trace S2 and S5 | C | done | `8b1989a` · `1e42d3e` · `63b33b5` |
| C3 | the status settle (two writes) | C | done | `8b1989a` · `1e42d3e` · `63b33b5` |
| C4 | frozen-peak-recalc | C | done | `8b1989a` · `1e42d3e` · `63b33b5` |
| C5 | web engine and auto-start; Python start() — architectural | C | done — run-review passed (owner, 2026-10-16) | `2c4f638` · `f1d29c1` · `37df25c` |
| C6 | no-audio safety timeout on an injectable clock | C | done — run-review passed (owner, 2026-10-16) | `414a88a` · `d730a58` · `545ca56` |
| C7 | device-change settle on the audio clock | C | done — run-review passed (owner, 2026-10-16) | `e4d9951` · `f16c877` · `0feffbb` |
| — | run-review find: Python's table names (Re-analyze) | C | done | — · `ca4b7fb` · — |
| — | run-review find: the web's Safari microphone after a dialog | C | done | — · — · `60571e6` |
| — | run-review find: the web's New Tap left the loaded peaks (PR51) | C | done | — · — · `37df25c` |
| — | run-review find: Python hung at Play File (stream-stop deadlock) | C | done | — · `d730a58` · — |

#### Background

in progress — the owner (2026-10-02): "I agree that the comment on C is not acceptable. Staying as code means
divergence".

**Survey (2026-10-15, three readers, every edition's tests for each slug):** the reason for "stay as code" no longer
holds — step 10 shared four of this group's slugs as step scripts with a small runner per edition, and nearly every
case here is synchronous or runs on the audio clock the tests already feed (`audio-clock-feed`, the same in all
three). Three obstacles are production mechanisms, not tests: (1) Swift published its frequency bins with
`DispatchQueue.main.async`, so its tests slept 50 ms before a guitar tap; (2) the no-audio safety timeout
(`afterAudioStall`) runs on wall-clock timers in all three, with no clock a test can set; (3) the settle timer after a
device change lives in the analyzer in Swift (unreachable from a test) and Python (a test swaps the timer function),
and in a React hook (a view) on the web. Same-named cases test different things: frozen-peak-recalc PR10, 12, 15, 16,
18, 19, 27, 32 (and four spectrum generators); status-message redo (L vs C) and no-resonance (suffix vs string);
annotation-state D11, D15; audio-clock-timers T2/T3 (state set by hand vs real taps). Defects seen (read): Python
comparison range rounded to whole Hz and `comparison_snapshots` never cleared by `load_comparison`; the web's
`loadComparison` / `clearComparison` do more than Swift's; Swift N10 omits the write it describes; the web's 220 Hz
overlap case asks about an id that does not exist; Swift PR34 duplicates PR33 and PR10 may depend on an earlier test's
Peak Min; start-tap-race R1 guards a deferred path no edition has; the web lacks `effective…PeakID`, the label /
manual-override / auto-mode lookups and LoadedRange tests; MC11–MC12 are the web's alone; stale comments in each
edition.

**Plan (owner, 2026-10-15):** batch A, ready now — DK9, measurement-complete, tap-count-change, scenario-trace,
state-invariants, tap-progress, annotation-state, session-pre-roll's remaining five; batch B after the same-name
decisions — status-message, audio-clock-timers (bar the timeout), comparison, display-range's scenarios,
effective-peak-id; batch C after the timing decisions — notification, the timeout cases, frozen-peak-recalc; each
slug's defects fixed as it is reached. Decision (owner, 2026-10-15): Swift publishes the frequency bins at once when
on the main thread (engine start, file playback, tests), queued only from another thread — the 50 ms waits go as each
slug is reached.

#### Batch A

**DK9.** done: `decay-tracking.json` gains an 'analyzer' case list (DK9 as steps), run in all three; the hand-written DK9s
removed.

**measurement-complete.** done (2026-10-15): `measurement-complete.json` MC1–MC18 through each edition's real paths (process the captured taps,
New Tap, Cancel, load, change Taps or the threshold); the web's load cases go through `loadMeasurement` (they called
`restoreSnapshot`); MC11–MC12, the web's alone, shared; Python's signal and setter cases stay in its file as Python's
own. Found by MC10 and decided (owner, 2026-10-15): when changing Taps or the threshold ends the loaded-settings
warning differed — Swift clears it when the new value differs from the loaded one (`loadedNumberOfTaps` /
`loadedTapDetectionThreshold`, each set only when the file carries it); Python only when a loaded value existed, and
it recorded the current values at the end of every load; the web on any change, with no loaded values. Python and the
web now follow Swift (Python drops the extra check and records each value where it restores it, and `set_tap_num`'s
duplicate of the rule goes; the web keeps the loaded values on the analyzer, its threshold setter applies the rule on
an actual change, and App's `noteLoadedSettingsDeviation` call goes). Also fixed: the web's load set Taps to 1 when a
file carried no count, where Swift leaves it (MC18). New MC13–MC18. Mutations caught: web any-change rule MC14, web
Taps-to-1 MC18, Python's extra check MC10.

**tap-count-change.** done (2026-10-15): `tap-count-change.json` TC1–TC10, each case reaching its state through the app's paths in all three
(decided, owner, 2026-10-15) — New Tap, real captured taps (a guitar or material capture finish on a synthetic tap),
Accept, Redo, audio fed through a rest — where the natives had written the detection state, tap count, captured taps
and prompt by hand; one starting point where the editions differed (Generic; the lower case from 4). TC7, the guard
that keeps a later phase's instruction, first passed with the guard removed: listening for fC, the prompt the hook
would write is the one already shown; it now reaches the fC redo, whose "— tap again" the hook would overwrite
(mutation: the guard removed fails it in Swift and the web). Also decided (owner, 2026-10-15) and done: the web's
`startTapSequence({arm: false})`, a parameter for tests only, is removed — its 36 test calls use `startTapSequence()`
as the natives do, and the full web suite passes. New shared test helper `tooling/synthetic-tap` (the decaying-sine
tap, written out in several test files per edition), used here; the other slugs move to it as they are reached. Also
decided (owner, 2026-10-15) and done: the web's `acceptMaterial` / `redoMaterial` renamed `acceptCurrentPhase` /
`redoCurrentPhase`, the names Swift and Python use. New shared test helper `tooling/analyzer-steps`: the steps the
scenario case files share (settings, Taps, New Tap, Pause, Resume, Cancel, a guitar or material capture on a synthetic
tap, Accept, Redo, audio through a rest), each through the app's path, run by one function per edition, so the runners
keep only their own set-up and expectations.

**scenario-trace.** done (2026-10-15): `scenario-trace.json` S1–S4, the trace as recorded states; the set-up made one (Generic, threshold
−40 — the web had used Classical, Python a 256-point frequency axis and a stand-in microphone, and the natives set
warm-up fields by hand, none needed), and Swift's 50 ms waits gone with the bins fix. S2 keeps its simulated stray
detection; whether it, and start-tap-race R1, still guard anything is for that slug. Mutations caught: Python Resume
doing nothing S3, web Cancel not restarting S4.

**state-invariants.** done (2026-10-15): `state-invariants.json` V1–V13; the I1–I6 checker stays test code in each edition, its rules
written out in the case file; the V cases reach their states through real steps (V3 now completes through a real
capture and the capture window, where it had set the detection state, taps and count by hand), and the checker's own
cases (V7, V9–V13) set a forbidden state with a `write` step named as such. Python's unused real-time `_pump_events`
(its docstring still said the rest was a QTimer) went with the rewrite. `tooling/analyzer-steps` gains `setThreshold`.
Mutations caught: Swift checker without I2 V9, web checker without I5 V12, Python Taps step doing nothing V4.

**tap-progress.** done (2026-10-15): `tap-progress.json` TP1–TP15 — the taps expected, the bar over guitar taps, the cumulative material
count across Accepts and through the FLC wait, Redo's rebase, Cancel during the FLC wait, a load tearing down a
part-captured sequence, and the bar kept after a later Taps change; the web's own load-over-a-plate case (fixture
`plate-umik-1-3-tap-swift-mac-1785359465`, carried by all three) is shared as TP15. Mutations caught: Python Accept
resetting the count TP6/TP8/TP9/TP12, web and Swift Redo resetting it TP8/TP9.

**annotation-state.** done (2026-10-15): `annotation-state.json` AS1–AS41 — label positions, selection and the user's mark, which peaks are
annotated (with Show Unknown Modes off, shared from the web's own case), labels and the auto-detected mode, Reset to
Auto, the definitive Air/Top/Back and the ratio, the guitar-type clean slate and a new sequence, a load replacing
labels and positions, and a brace capture's unclassified peak. Decided (owner, 2026-10-15) and done: every case loads
its peaks as the app loads a file and the analyzer classifies them — the editions had seeded different internal lists
(Swift `allPeaks`, Python `peaks_above_peak_min`, the web `peaksAbovePeakMin` and `modeByPeak` by hand, skipping
classification); where inputs differed, Swift's (D11's two auto Tops, D15's freeform label); the web's 220 Hz case,
which asked about an id that did not exist, now asks about a peak the analyzer does not know, as Swift's does, and the
real case — a material peak — is AS41. Also decided and done: the web's peak cards took their label, auto mode and
override flag from App (`labelFor`, `overrides.has`, `modeByPeak`) — the web analyzer now has `effectiveModeLabel`,
`autoDetectedMode` and `hasManualOverride`, as Swift's and Python's do, and the cards read them; and Python cleared a
label through `set_mode_override(None)` (which also ran the uniqueness rule Swift's reset does not), accepting "auto"
too — its view now calls `reset_mode_override`, as Swift's calls `resetModeOverride`, and `set_mode_override` only
sets a label. The web's `peak-state-store.test.ts` (the same store cases) is replaced by the shared ones; the web
keeps three cases of its own for its chart-marker and report helpers, and Swift two for its visibility enum's cycle
and icons. Mutations caught: web label ignoring the user's AS19/AS20, Python Reset to Auto doing nothing AS21–AS23,
Swift uniqueness rule off AS26/AS28.

**session-pre-roll.** done (2026-10-15): its four hand-written cases join `session-pre-roll.json` as SR12–SR14 (idle bounded, the first tap
freezing the latch, completely live after it — through a new `release` step and a `preRoll` field; each case's
expectations now optional) and a `preRollSeconds` value each edition's constant is checked against; the capture
probe's case stays code (it runs only with the probe on). Raised, not changed: the natives' Settings call
`applyDumpCaptureAudioSetting` after writing the setting; the web's analyzer applies it itself when its stored setting
changes. Mutation caught: web latch never freezing SR6/SR8/SR13/SR14.

**Batch A complete** — Swift `acce5cb`, Python `3b28c56`, web `34eda6b`. Run-review (owner, 2026-10-15), all three
editions passed: (1) load a saved measurement, change Taps away from its value and back → the loaded-settings banner
goes at the change and stays gone (the threshold likewise on the web); (2) a peak given a name of its own, then Reset
to Auto from its label menu → the auto mode's name returns (Python: a selected Top stays selected). A step for a file
saved without a tap count was dropped — no saved file lacks one; MC18 pins it. The wand (Reset to automatic selection)
resets the selection and keeps the labels, by design (AS10).

#### Batch B

**Decisions** — decided (owner, 2026-10-15): (1) the web's comparison follows Swift — `loadComparison` and the
saved-comparison load no longer clear the previous result, the microphone warning or the ring-out (the
saved-comparison load clears the highlight, as Swift's), the chart range is set only when something was compared, and
`clearComparison` no longer touches the multi-tap flag; Python's comparison range keeps its fractions (it truncated to
whole Hz) and `load_comparison` starts a fresh `comparison_snapshots` (it grew); (2) the web gains
`effectiveLongitudinalPeakID` / `effectiveCrossPeakID` / `effectiveFlcPeakID` (its material record builder keeps
reading the ids off the same three peaks); (3) Swift's clipping and dead-input overrides apply at once — no main-queue
hop; found doing it: a @Published sink runs before the property changes, and `statusMessage.didSet` re-applies the
overrides, so the hop had been hiding a stale read — the analyzer now keeps its own `isClipping` / `inputAppearsDead`,
set by the sinks before applying, as Python and the web do (Swift's notification tests keep the analyzer's
subscriptions, which they had removed); (4) material peak announcements are observed per edition, with no production
change; (5) the web applies Dump Capture Audio from Settings' Apply, as the natives do, and `setSettings` no longer
applies it.

**status-message.** done: `status-message.json` SM1–SM23, every string reached through the app's own path — the armed prompts past a real
warm-up (the natives had set warm-up fields), clipping through the input level, the device change, Pause/Resume,
completion held through a Peak Min change, the loaded prompt, plate and brace completion, the material prompts through
a warm-up chunk, the guitar loop's capturing / processing strings from real detection (Swift and Python had called
`guitarLoopStatus` directly), Redo on fL and on fC (each edition had one), material progress and review (SM20's exact
'fL: 60.0 Hz …' — all three find the same peak), no resonance from a silent tap, and the file-playback auto-advance.
`tooling/analyzer-steps` gains `setPeakMin`. The 'two writes settle' quiet-period case stays code in each edition
(real time, batch C); the device change's restore is batch C; the web keeps its guard against strings it alone once
produced. Swift's status cases no longer wait 50 ms. Mutations caught: Swift clipping ignored SM4, web paused prompt
changed SM6.

**effective-peak-id.** done: `effective-peak-id.json` EP1–EP4 through real plate taps, in all three (the web had none; Python's file renamed
from `test_wi2_…`). Mutations caught: web fC getter null EP3/EP4, Python fC getter returning fL EP2–EP4.

**display-range scenarios.** done: `display-range.json` gains 'files' and 'scenarios' DR1–DR7 — the range a load publishes (a snapshot's exactly;
the saved range without one), the analysis range a load leaves, the material peaks' announcements (a load's, and
Redo's single clear) and the from-a-load mark; DR7, the web's sequence-start count, is the web's alone. Swift's
LoadedRangeTests and MaterialPeakAnnouncementTests, Python's test_loaded_range and test_material_peak_announcement and
the web's material-peak-announcement test become one runner each (the web had no LoadedRange cases). Found by DR2 and
decided (owner, 2026-10-15): the web's load returned at once for a measurement with no spectrum (a file from before
spectra were stored), where Swift and Python load it — the saved range, its own settings and peaks; the web now does
too (`measurementToLive` takes the settings and handles no snapshot).

**audio-clock-timers.** (bar the timeout) done: `audio-clock-timers.json` AT1–AT6 — the rest between material taps, the FLC hold and its
warm-up anchor, the file's end releasing the capture window but not a rest, a tap detected from audio turning
detection off, and file playback's auto-advance — each case reaching its state through real detection and captures
(the natives had called `handleTapDetection` and set the phase and spectra by hand for T2/T3, as the web did not).
`tooling/analyzer-steps` gains audio at a level (`advance` with 'level' / 'extra', `audioChunks`). The two
safety-timeout cases stay code in each edition until batch C; the web keeps its own file-playback pacing case.
Mutation caught: web rests halved AT1/AT2.

**comparison.** done: `comparison.json` CM1–CM24 — entries, labels (numbered duplicates, shared from the web), the range, the mode,
detection standing down or left alone, a load ending a comparison, the per-tap overlay giving way and turning off,
each entry's Air/Top/Back from its source's selection and labels, saving a comparison (Python's save cases, shared —
Swift had none) and loading it back, New Tap ending a comparison (guitar and plate, shared from the web). CM15 found a
gap in the web's change above — `loadComparison` had emptied the per-tap taps only through `clearResult` — now done as
Swift does. The comparison-format cases (an entry written and read back, a field left out, a legacy entry healed, the
stored map read back, a plain record not a comparison) moved into `measurement-codable.json` as its `comparison`
group, CR1–CR5, replacing Swift's ComparisonModePersistence suite, Python's TestComparisonEntryCodable,
TestComparisonDefinitiveModes and TestResolvedModePeaks, and the web's format describes; what those held that the
shared cases lacked was added — an entry's guitar type after loading (CM17 `entryGuitarType`) and no peaks giving no
modes (classify RM04). Python's own `comparisonChanged` signal cases stay in its comparison file. CR1 found (owner,
2026-10-16: fix it): a saved comparison has no peaks and no `selectedPeakIDs`, and Swift's and the web's read-time
selection heal established an empty selection for it and flagged it healed — every comparison read as healed, so a
library holding one was saved again at each launch, and an opened comparison read as changed; Python's heal already
ran only with peaks. Now the heal runs only with peaks in all three (SH6: no peaks and no selection, not healed);
mutation: the guard removed fails CR1 and SH6 in each edition. Batch B full suites green (2026-10-16); run-review
passed in all three (owner, 2026-10-16; steps under "Step 11 batch B run-review" below). Found and decided (owner,
2026-10-15: an architectural divergence, resolved): the Taps toggle was two view calls in Swift and Python (set
`showingMultiTapComparison`, then `applyMultiTapComparisonOverlays`) and one model call on the web
(`setMultiTapComparison`) — now one model call in all three, under Swift's name: `applyMultiTapComparisonOverlays`
sets the flag itself, the toggles call only it, Python's view no longer writes the flag on entering a saved comparison
(the model already has), and the web's method is renamed (mutation: Python's method not setting the flag fails CM15,
CM23, CM24). Then found and decided (owner, 2026-10-15): where the per-tap overlay is kept differed — Swift's and
Python's `applyMultiTapComparisonOverlays(true)` builds the taps and the average into the comparison the chart draws
(`comparisonSpectra` / `_comparison_data`), the web's only set the mode and App asked the analyzer for the per-tap
entries on every redraw; now the web's builds them into `comparisonEntries` (at the saved range, as Swift's
`makeMeasurement()`; nothing when there are no taps, as Swift's guard), the chart draws `comparisonEntries` for either
kind, App's `comparison` is the saved-measurement comparison (`isSavedMeasurementComparison`) and its separate per-tap
path is gone. New shared case CM25 (the overlay holds each tap and the average), which the old web fails. Mutations
caught: Swift comparison not standing detection down CM9, Python Clear not returning to live CM6, web per-tap taps
kept CM15.

**Batch B complete** — Swift `d7389de`, Python `8527a21`, web `eeaf68e`.

#### Batch C

Survey and decisions (owner, 2026-10-16). Survey (three readers, every edition): The items below are in the order they
are built; each item's survey finding and decision come first, then what was done.

##### C1 — tap-decisions

**Survey and decision.** tap-decisions was in no batch: the same cases in all three, on the audio clock; Swift's noise-floor seed sets the
level by hand where the others feed audio; Swift's 50 ms wait for the frequency bins waits for nothing since the bins
decision. Decided: shared in batch C; the 50 ms wait removed; Python's pipeline-delivery class (Qt signal connections,
a risk the others' single-assignment callbacks do not have) stays Python's own, so noted in the case file.

**Done.** done (batch C item 1, 2026-10-16): `tap-decisions.json` T1–T14 (T1e and T6 each split into the two analyzers they
compared; the settle, seed, confirmation and resume cases numbered T9–T14) and the onset alignment O1–O3, through the
shared steps in all three; `confirmChunks` checked against each edition's constant. `tooling/analyzer-steps` gains
`newTapSkippingWarmUp`, and `audioChunks` feeds exactly n chunks (it had gone through the seconds, where rounding
could add one). Found and decided (owner, 2026-10-16: (A)): Swift seeded a new sequence's noise floor, and re-anchored
the latch on Accept, Redo and the phase restarts, from the level meter's value (`fftAnalyzer.level.inputLevelDB`, set
a buffer at a time on the main thread), where Python and the web use the level of the chunk the analyzer last received
— Swift now reads its own `lastChunkLevelDB`, as its resume and re-arm already did, so a fed chunk seeds it as in the
others. Swift's 50 ms wait for the frequency bins is gone with its runner. T7's value is the EMA's (−55.38; Swift's
old comment said ≈ −57.4, its check only > −58). Python's pipeline-delivery class stays its own, so noted in the case
file. Mutations caught: Swift seeding from the meter T11; Python with no hysteresis margin T1f, T5; web confirming on
one chunk T12, T13 and the constant.

##### C2 — start-tap-race retired; S2 and S5

**Survey and decision.** start-tap-race R1 guards the deferred start Swift removed in `df17a48` (Python and the web never had one) and tests
nothing; R2–R4 repeat S1–S3; R5 (pause, then Cancel) is its own. S2's hand-set idle is reachable by no real path.
Decided: start-tap-race retired, R5 moved into scenario-trace; S2 reaches its state through a real detection (warm-up,
audio above the threshold), as AT1/AT5; the stale comments on the deferred start fixed.

**Done.** (batch C item 2, 2026-10-16): the three start-tap-race files are gone (R1 guarded the deferred start removed in
`df17a48`; R2–R4 repeated S1–S3) and the web's tag no longer names the slug. `scenario-trace.json` S2 now reaches its
state through a real detection — warm-up, two loud chunks — and records it (postWarmUp, postDetect), where it had set
the detection state idle by hand; the `strayDetection` step is gone from the three runners. S5 is R5: Cancel from a
paused sequence starts a fresh one listening — reached through a real tap and re-arm, where R5 had set the tap count
by hand. The comments that still described a deferred start (Swift's and Python's same-value guard on the detection
state, Python's per-sequence clear) now describe what the code does. Mutations caught: a detection not standing
detection down S2 (Swift, Python); web Cancel leaving a paused sequence paused S5. Found by the full suite after this:
Python's self-regression playback (`tests/parity_runner.py`) left the measurement type it set, which the
start-tap-race file's set-up had been resetting before the state-notification cases ran; it now puts the type back
with Measure FLC.

##### C3 — The status settle (two writes)

**Survey and decision.** "Two writes settle" has no timer in any edition — the writes are synchronous; the case pins that, once the main queue
drains, no further status writes come (the bouncing-sink regression). Decided: a shared drain-the-main-queue step and
a status-writes check; Swift's status runner becomes async; no production change.

**Done.** (batch C item 3, 2026-10-16): `status-message.json` SM24 — arming straight after the analyzer is made, the status
settles on the prompt and stays — through two status-runner steps, `drainMainQueue` (ten passes, each waiting for
everything queued on the main thread before it: Swift a main-queue continuation, Python `processEvents`, the web a
zero timeout — no time passes) and `countStatusWrites`, and the field 'statusWrites' (Swift's status publisher,
Python's `statusMessageChanged`, the web's change notifications, its one signal); Swift's status runner is async; the
three hand-written cases and their 50 ms waits are gone. No production change. Mutations: a status that keeps
re-queuing itself — Swift a sink writing it back through the main queue, Python and the web a status alternating
between two values — fails SM24 in each; a single queued write does not (the first drain absorbs it: the case is about
settling, and a write that settles is not the regression).

##### C4 — frozen-peak-recalc

**Survey and decision.** frozen-peak-recalc: PR12, 15, 16, 18, 19, 27, 28, 29, 32 mean different things across the editions, four spectrum
generators, state set by hand; the web's recalc re-classifies every peak where Swift carries each peak's mode forward
(±5 Hz), and has no non-guitar branch. Decided: the web's recalc aligned with Swift; one `frozen-peak-recalc.json`
under Swift's ids and meanings, spectra from the shared `gaussians`/`flat` spec of `peaks.json`, through real entry
points; the editions' own checks that test something real kept as new ids.

**Done.** (batch C item 4, 2026-10-16): `frozen-peak-recalc.json` — 44 cases under Swift's ids and meanings plus PR38 (a tap
entry's modes, a function case) — through the app's paths only: each frozen measurement is a .guitartap document the
runner writes from a spectrum spec (the `gaussians`/`flat` spec of `peaks.json`; the web's builder moved to
`test/spectrumSpec.ts`) and its saved peaks, selection, names, label positions and per-tap entries, read with the
edition's own reader and loaded; then Re-analyze, Peak Min, select, name, drag, a live frame, captures, Save, load and
Redo. Peaks are named by frequency. Guitar cases sit inside the default 75–350 Hz analysis range (400 Hz became 330,
PR12's 1000 Hz became 250). New ids for the editions' own real checks: PR47 (a live frame selects every peak, the
web's), PR49 (New Tap on material clears its label positions, the web's); the web's per-tap floor case was not carried
over. Found and decided (owner, 2026-10-16: (A), twice): the recalc's only caller is Re-analyze, which first clears
the hand-modified flag, the selected-frequency cache and the modes, and is never offered for material — so its
carry-forward of a hand-made selection, its carry-forward of modes and its material branch could not run; and its
loading guard and complete/spectrum guard could not fire (a load never reaches Re-analyze; Re-analyze checks the same
condition first). All removed in all three — Re-analyze classifies afresh, auto-selects and carries label positions
and names ±5 Hz — and PR05, PR10, PR11, PR26, PR27 retired; the web's recalc had re-classified where Swift carried
modes (the difference is gone with the branch). The comments describing the old carry-forward now say what the code
does. Raised and decided (owner, 2026-10-16): the file's `selectedPeakFrequencies` is no longer read by GuitarTap, and
stays — it is written for programs a user might write that read a .guitartap file without the selection algorithm; now
documented as such in Appendix B of the manual and at each edition's field (Appendix B's `userModifiedSelection` row
also corrected: it decides whether Reset to automatic selection is offered). Swift's live-frame analysis acts only
while its engine reports running, Python's and the web's had no such check — now all three check (Python
`mic.is_stopped`, the web its device's `running`); no app path delivers a frame without a running engine, so no case
pins it. Mutations caught: Swift not carrying label positions PR12, PR19, PR20, PR21; Python keeping a stale selection
on Re-analyze PR28; web not carrying names PR19, PR23, PR24.

**Batch C items 1–4 complete** (run-review passed, owner, 2026-10-16; steps under "Step 11 batch C (items 1–4)
run-review" below) — Swift `8b1989a`, Python `1e42d3e`, web `63b33b5`; found in the run-review and fixed separately:
Python's table reading names from the analyzer `ca4b7fb`, the web's Safari microphone fix `60571e6`.

##### C5 — web engine and auto-start; Python start()

**Survey and decision.** Found: the web's auto-start at engine start has no guard, where Swift starts only when idle (not detecting, not
complete, not paused, no taps). Decided: check whether it can discard a completed or loaded measurement, then align
with Swift.

**Found and decided (owner, 2026-10-16).** The web's auto-start at engine start is unguarded: the hook starts a sequence the moment the engine's start resolves —
at launch and on Retry microphone — so a measurement loaded while the mic had failed, or while the browser's
permission prompt was up, is replaced by a new sequence. Swift's and Python's analyzer start it one pass later, only
when not detecting, not complete, not paused and with no taps. Decided: make the web architecturally the same as Swift
and Python, all three layers: (1) start — an analyzer start() that starts the engine, anchors the warm-up and, one
pass later, makes the guarded auto-start; the hook calls it and keeps the alerts and Retry; (2) wiring — the analyzer
subscribes to its engine (chunks, frames, dead input, device changes, with the device-change timer moved into the
analyzer as it is), the engine's single callbacks object becoming subscriptions, and the hook subscribes only to what
it displays (live spectrum, metrics, device list, the could-not-open alert); (3) engine lifetime — one engine created
with the analyzer and kept for its life, Retry restarting the same engine, and the remount race handled in the engine
(a start while one is in flight joins it; a stop records that it should not be running). The guarded auto-start
becomes its own model method in all three (Swift's closure split out of start(); Python already has
_auto_start_tap_sequence; the web's new), and the shared cases call it — the engine's hardware start stays untested in
all three alike (a test that only the web's headless engine could run would itself be a divergence). Python's
start(parent_widget), which does view wiring and loads the saved measurements where Swift's starts the engine, is
brought to Swift's shape (owner). Proposed, to confirm: the engine's own config (tapDetectionThreshold, numberOfTaps),
written by App's setConfig and never read, removed.

**Design (for review, 2026-10-16).** Swift's shape, which the other two take: `init(fftAnalyzer:)` keeps the
engine for the analyzer's life, loads the saved measurements and sets up the subscriptions to the engine; the view
calls `start()`, which starts the engine, anchors the warm-up and, one main-queue pass later, makes the guarded
auto-start; the view keeps the start's error alerts and the retry.

1. **The guarded auto-start, one method in all three.** Swift: the closure in `start()` becomes
   `autoStartTapSequence()` (only when not detecting, not complete, not paused and no taps → `requestStartTapSequence()`),
   which `start()` calls one main-queue pass later. Python: `_auto_start_tap_sequence` renamed
   `auto_start_tap_sequence`. Web: a new `autoStartTapSequence()` with the same guard.
2. **Shared cases** in `scenario-trace.json`, through a new step `{"engineStarted": true}` that calls that method —
   what the engine coming up does, without hardware in any edition: S6 nothing on screen → a sequence starts; S7 a
   loaded measurement → it stays; S8 a paused sequence → it stays paused; S9 a sequence with a tap taken → it carries
   on. The web fails S7 today.
3. **Web, layer 1 — start.** An async `analyzer.start()`: start the engine, anchor the warm-up, then one pass later
   (`setTimeout(0)`, as Python's main-loop pass) the guarded auto-start; a failure is thrown to the hook, which shows
   the permission or engine alert as now. `armForCurrentType` and `onStarted` go.
4. **Web, layer 2 — wiring.** The engine's callbacks object becomes subscriptions (`engine.onAudioFrame(fn)` and the
   like, each returning an unsubscribe, the pattern `level.onClipping` already uses). The analyzer subscribes when it
   is given its engine: each chunk → `processAudioFrame`, each frame → `onFftFrame`, dead input →
   `setInputAppearsDead`, an input change → `handleDeviceChange`, its 3 s timer moved from the hook into the analyzer
   as it is (C7 then moves it onto the audio clock in all three). The hook subscribes only to what it displays: the
   live spectrum, the metrics, the device list, the could-not-open alert. The tests that pass callbacks to the engine
   (file-playback, audio-clock-timers) subscribe instead.
5. **Web, layer 3 — one engine.** `useTapToneAnalyzer` creates the analyzer with its engine, once; `engineRef` goes
   (App reads the analyzer's engine where it needs one). Retry calls `analyzer.start()` again on the same engine. The
   engine's `start()` joins a start already in flight, and its `stop()` during a start records that it should not be
   running, which the start checks after each step — so React's remount (mount, unmount, remount) leaves one engine
   running, by the engine's own rule, and the hook's orphaned-engine check goes.
6. **Python, start() in Swift's shape.** `start()` starts the engine — the stream (`mic.start()`, now in FftCanvas's
   constructor) and the processing thread (`proc_thread.start()`, now in FftCanvas `start_analyzer`) — anchors the
   warm-up and schedules the guarded auto-start; a start failure is raised to the canvas, which reports it as now.
   The saved measurements are loaded when the analyzer is made, as Swift's `init` does. The Qt parenting and the
   hot-plug wiring, which need the parent widget and which Swift has no counterpart of, stay a Python-only step the
   canvas calls first, named for what it does (`attach_to_view(parent_widget)`). FftCanvas's restart of a thread
   that has died, and its start of the thread for a file playback, go through `analyzer.start()`.
7. The web engine's own config (`tapDetectionThreshold`, `numberOfTaps`), written by App's `setConfig` and never
   read, removed with its two calls.

Approved (owner, 2026-10-16): the design; item 6's Python-only `attach_to_view` step ("if we have to have a parent
then we have to have a parent"); item 7 ("dead code should be removed").

Tests: each layer's own suites, the new S6–S9 with mutations, then the full suites; run-review of launch, Retry
microphone after a load, a remount (web dev build), file playback, and a device change, in all three.

**Done, steps 1–2 (2026-10-16; Swift 2c4f638, Python f1d29c1, web 37df25c).** The guarded auto-start is one method in all three: Swift's closure in start() split out as autoStartTapSequence(),
called one main-queue pass later as before; Python's renamed auto_start_tap_sequence(); the web's
autoStartTapSequence() new (the hook still calls requestStartTapSequence() until step 3). tooling/analyzer-steps gains
engineStarted (that method) and loadFixture, moved from the frozen-peak runners, which now reach it through the shared
steps. scenario-trace.json S6–S9: nothing under way → a sequence starts; a loaded measurement (the Contreras fixture —
a load leaves no taps counted, so only the complete check protects it) → it stays; paused before any tap → it stays
paused; a tap taken → it carries on. Mutations: Swift without the complete check S7; Python without the paused check
S8; the web without the taps check S9 — each guard condition pinned by its own case (the first S7/S8, a finished
measurement and a pause after a tap, were also held by the taps check, and were changed when the Swift and Python
mutants passed).

**Done, steps 3–5 — the web (2026-10-16; web 37df25c).** The engine's callbacks object is gone: each event is a subscription (onAudioFrame, onSpectrum, onMetrics,
onDeviceStateChanged, onInputChanged, onInputOpenFailed, onInputAppearsDead), returning its removal. The analyzer is
created with its engine (useTapToneAnalyzer: new TapToneAnalyzer(new RealtimeFFTAnalyzer()); tests attach a headless
one with setDevice) and, when given it, subscribes to each chunk, each frame, a dead input, clipping and an input
change; the 3 s device-change settle moved from the hook into the analyzer as it was. analyzer.start() starts the
engine, anchors the warm-up and, one pass later, makes the guarded auto-start; analyzer.stop() stops it. The hook
shows what the engine reports — the level, live spectrum, metrics, devices, the could-not-open alert — starts the
analyzer when the app comes up and stops it when it goes, and reports a failed start; Retry starts the same engine
again. App's engineRef, armForCurrentType, onStarted and tapThresholdRef are gone. The engine's start joins a start in
flight, and a stop during a start ends it at its next step (each await in the start checks), so React's remount leaves
one input — the hook's orphaned-engine check is gone. The engine's dead config (tapDetectionThreshold, numberOfTaps)
and App's two setConfig calls are removed. Tests: the engines the tests built with callbacks now subscribe or are
attached; status-message's fake engine (stubs of methods the engine no longer has) is a real headless one; new
web-only engine-start.test.ts (a second start joins; a stop during a start leaves no input; start-stop-start leaves
one) — mutations: no join fails the join and remount cases, a stop that tears down at once fails the remount case.
Full web suite 1262 + 3 new pass; typecheck and lint clean.

**Done, step 6 — Python (2026-10-16; Python f1d29c1).** start(parent_widget) is split as Swift's shape asks: attach_to_view(parent_widget) — the Qt parenting, the hot-plug
wiring and the calibration's device name, which need the widget and have no Swift counterpart (owner: if we have to
have a parent, we have to have a parent) — called by FftCanvas after construction; load_persisted_measurements(),
called from __init__ as Swift's init calls loadPersistedMeasurements() (the healed-library save with it); and start(),
which starts the engine — the processing thread, then the input stream, each only if not running, so a file can still
play when no input opens — anchors the warm-up and schedules the guarded auto-start, raising a stream failure as
Swift's start() throws. FftCanvas no longer opens the stream in its constructor; its start_analyzer() — at startup,
for a file's first playback, and for a thread that has died — calls analyzer.start() and records a failure in
engine_start_error, which the window reports as before. The test engine's stream start does nothing (a test instance
has no stream, as its restart, close and watchdog already say): without it, the pipeline test that calls
start_analyzer opened the real microphone, and one such run crashed in PortAudio's callback at exit. Full Python suite
1348 passed, 1 skipped.

##### C6 — no-audio safety timeout

**Survey and decision.** The no-audio safety timeout is the same in all three, on the wall clock by design, its tests sleeping. Decided: the
analyzer takes a clock it reads now from and schedules on (the real one in the app, a manual one in tests); a shared
step stalls it.

**Design (owner, 2026-10-16: "At construction").** A `WallClock` — `now()` in seconds and `after(seconds, action)` on
the main thread — in a file of its own in each edition (`WallClock.swift`, `wall_clock.py`, `wallClock.ts`; group
`model/wall-clock`). The analyzer takes it at construction, as it takes its engine, defaulting to the system's
(`SystemWallClock`: Swift `systemUptime` + `DispatchQueue.main.asyncAfter`; Python `time.monotonic` + `QTimer.singleShot`
on the main thread, from any thread; the web `performance.now()` + `setTimeout`), so the app is unchanged.
`lastChunkWallTime` and `afterAudioStall` read and schedule on it; the web's `afterAudioStall` now takes seconds, as
Swift's and Python's do, its callers dividing their millisecond values as Swift's guitar timeout does. Tests: a
`ManualWallClock` beside the audio-clock feed — time stands still until `advance`, which runs each action as its time
comes, in time order, including one scheduled within the advance; the steps analyzer always has one, so a stray 2 s
timer from an earlier step can never fire mid-case. Shared step `{"stall": seconds}`: wall time with no audio.
Python's `test_capture_opens_no_window` keeps the system clock (it drives the real window through Play File).

**Done (2026-10-16; Swift 414a88a, Python d730a58, web 545ca56).** AT7 (a capture the audio stops filling closes after a 2.1 s stall; detection then
rests and re-arms) and AT8 (one quiet chunk every 0.4 s for 2.8 s: the capture stays open) in
`audio-clock-timers.json`; the six per-edition sleeping tests (2.3 s and 2.8 s each) are gone, so the slug is wholly
shared. Mutations, each edition: firing at the first check (silence measured from the capture's start) fails AT8;
never firing fails AT7. Full suites: Swift passed, Python 1349, the web 1266 (the same counts — two tests became two
cases). `--check`: 141 groups, no problems.

**Run-review.** The clock is only wired in the app (the system clock behaves as before), so the check is that captures
still complete and are not closed early. Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, then clear the service worker after the build (F30's run-review steps). Same list
per edition, Swift first.

1. Set the type to Plate. Tap for L, press Accept, tap for C. → Each tap is analysed and its peak shown; neither
   capture ends with "No signal detected".
2. Set the type to a guitar, then tap. → The tap is analysed and its peaks shown.
3. Play File with a recorded plate tap. → The tap is analysed, as before.
4. (P) Python only: with the microphone live, Play File, let it finish, and repeat ten times. → It never hangs.

**Run-review progress.** Python, step 3 (owner, 2026-10-16): the app hung at Play File (spinning cursor, no input,
no microphone), and Swift's Settings stalled for minutes while it did. The stack dump (`kill -USR1`) put the main
thread in `stream.stop()` in `start_from_file`, and a native sample showed the audio thread inside PortAudio's
callback stopping the audio unit too, each waiting on a CoreAudio lock the other held. Cause: the stop sets
`is_stopped` and then stops the stream, and the callback, seeing `is_stopped`, raised `CallbackStop`, which makes
PortAudio stop the unit from the audio thread at the same moment — a deadlock whenever the timing meets. In Python
since April, not from C6; every stop path had it (Play File, `stop()`'s abort, a device change's abort). Swift has no
equivalent (AVAudioEngine stops itself). Fixed (owner, 2026-10-16: (A)): the callback drops a stopping stream's
chunks instead of raising `CallbackStop`, so only the stopping thread stops the stream; PortAudio's stop waits for a
running callback, so no chunk is processed after it. Timing-dependent, so not unit-tested; step 4. Swift's stall is
read as the system audio service waiting on Python's half-stopped microphone — not reproduced on its own.
Python, before the hang (owner): a tap's result showed peaks with none identified as Air or Top; not seen again after the
fix, and taken to be related to the hang.

| step | Swift | Python | web |
|---|---|---|---|
| 1–3 | ✅ (2026-10-16) | ✅ (2026-10-16, after the fix) | ✅ (2026-10-16) |
| 4 | n/a | ✅ (2026-10-16) | n/a |

All three editions passed (owner, 2026-10-16). **Run-review complete.**

##### C7 — device-change settle

**Survey and decision.** the settle after a device change differs — the timer is in the analyzer in Swift and Python and in a React hook on the
web; Swift and Python stand the detector down on a change and re-arm it after the settle, the web never touches the
detection state; Swift waits 3 s and then for the next FFT frame, Python restores after 3 s; the web merges repeated
changes into one restore, the natives schedule one per change. Decided: the web stands the detector down and re-arms
as Swift; the timer moves into the analyzer in all three and the settle runs on the audio clock (3 s of audio, then
the next frame), driven in tests by `advance`; raised, to be looked at: whether one restore per change can cut a later
change's settle short.

**One restore per change — answered (2026-10-16).** It can: with changes 2 s apart, the first change's restore re-armed
1 s into the second device's settle, and the second's ran again at 5 s. Decided (owner, 2026-10-16: (A)): each change
supersedes any pending restore (a change count the restore checks), so the settle always ends 3 s of audio after the
LAST change — as the web's coalesced timer did; the status before the settle, and whether its end re-arms listening,
are captured by the change that begins it and cleared when it ends (a later change finds the detector already stood
down, so it cannot be the one to decide).

**Design.** One mechanism in all three, Swift's `handleRouteChangeRestart()`: stand the detector down if it was
listening, re-anchor the warm-up, hold the level latch up, blank a live chart, capture the status, show the transient;
then `afterAudio(3.0)` and `afterNextFrame` — a new hook in each analyzer's frame entry (`onFftFrame` / `on_fft_frame`),
run before the frame's peak analysis, as `afterAudio` is from the chunk entry — on which the latch is re-anchored from
that frame's peak, the chart unblanked, readiness and listening restored and the status put back. Swift's Combine
one-shot on `$magnitudes` and its wall-clock `asyncAfter` are replaced; Python gains the wait for the next frame (it
restored straight after its timer); the web's two-edge `handleDeviceChange(true/false)` and its 3 s `setTimeout` give
way to `handleRouteChangeRestart()`, so the web now stands the detector down and re-arms as Swift does. If the new
device delivers no audio the settle does not end; nothing could be detected anyway, and the dead-input watchdog says
so. New group `state/route-change-settle`, `tests=test/notification`.

**Done (2026-10-16; Swift e4d9951, Python f16c877, web 0feffbb).** `notification` shared: `notification.json`, N1–N18 — N1–N13 as they were, now
through the app's paths (a real completed measurement, a real material phase, the clipping and dead-input setters)
instead of state set by hand and `restoredStatus` called directly, and N14–N18 new: the settle restarts on a second
change (N14), ends only on a frame after 3 s (N15), re-anchors the latch from that frame either way (N16–N17), and a
paused sequence stays paused (N18). Shared steps `{"routeChange": true}` and `{"spectrumFrame": spectrum}` (Python's
frames carry no frequencies, so its step puts the analyzer on the spectrum's axis). The status-message runners' device
change goes through `handleRouteChangeRestart()`; Python's SR7 runs the whole settle with the microphone released.
Mutations, each edition: no supersede (B) fails N13–N14; the second change re-capturing listening fails N13–N14; no
wait for a frame fails N15–N16; no audio delay fails N3 and N14. Full suites: Swift passed, Python 1354, the web 1271.
`--check`: 142 groups, no problems (the platform-specific count fell to 29: Python's old notification docstring
mentioned "`@parity none`", which the generator read as a tag). Raised, not changed: the web calls the armed prompt
`restingPrompt()`, Swift and Python `armedPrompt()` / `_armed_prompt()`.

**Run-review.** The settle's timing and the web's detector changed, and no test sees a real device change. Launch:
Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web `npm run build && npm run preview`, then clear the
service worker after the build (F30's run-review steps). Same list per edition, Swift first.

1. With a guitar prompt waiting for a tap, plug in or unplug a microphone. → "Audio device changed - reinitializing…",
   New Tap greyed and the chart blank; about 3 s later the prompt returns and a tap is detected.
2. During that settle, tap the guitar. → No tap is detected.
3. Unplug and plug back in within a second or two. → The prompt returns about 3 s after the second change, not
   sooner; a tap is detected.
4. With a completed measurement on screen, plug in or unplug a microphone. → The result, its peaks and its status stay.
5. Press Pause, then plug in or unplug a microphone. → After the settle the sequence is still paused; Resume works.

**Run-review progress.** Python, step 3 (owner, 2026-10-16): plugging the Umik-1 in and unplugging it at once gave
"Could not open the microphone 'Umik-1 Gain: 18dB'. The previous input is still in use — please check the microphone."
(PortAudio logged "Unspecified Audio Hardware Error"); after OK the settle ended as written and a tap was detected. Not
reproduced in about five more tries. Not from C7: it is the failed-open alert all three show when a device switched to
cannot be opened (`mic-selection` MS23–MS25), here because the device was removed while its stream was opening — a race
any edition can meet. Decided (owner, 2026-10-16: (B)): left as it is — rare, and the message is true. ((A) would have
dropped the alert when the device that failed is no longer listed.)
Web, step 1 (owner): macOS asked "Allow accessory to connect?" for the Umik-1 — its USB accessory check, before the
browser sees the device; after Allow the step ran as written.

| step | Swift | Python | web |
|---|---|---|---|
| 1–5 | ✅ (2026-10-16) | ✅ (2026-10-16) | ✅ (2026-10-16) |

All three editions passed (owner, 2026-10-16). **Run-review complete.**

### Step 13 — parity links

**Finding (owner, 2026-10-16: "We are doing a slug sweep to clean up problems in the slugs and testing and we make it
worse").** A test slug is linked to the code it tests only by that code's `@parity <group> tests=…` annotation, and
the generator's check ("every testable impl group has test evidence") never asked the reverse. Counted 2026-10-16:

- **16 shared test slugs listed by no production group** — nine created in steps 10–11 (`audio-clock-timers`,
  `comparison`, `display-range`, `effective-peak-id`, `import-persistence`, `measurement-load`,
  `peak-selection-persistence`, `session-pre-roll`, `tap-count-change`) and seven older (`field-precision`,
  `measurement-codable`, `measurement-type-name`, `mic-selection`, `peak-heal`, `self-regression`, `uuid-case`).
- **46 model files in no group** — Swift 18 of 43, Python 17 of 44, the web 11 of 30 — among them the whole load,
  save and comparison code (`+MeasurementManagement`, `tap_tone_analyzer_measurement_management`, `decode.ts`,
  `encode.ts`).

Decided (owner, 2026-10-16), in order:

| # | item | status |
|---|---|---|
| 13.1 | `gen_parity_map.py` fails (and CI with it) when a test slug is listed by no production group, or a model / state / audio / measurement file is in no group and not marked `@parity none` with a reason | done (2026-10-16) — below |
| 13.2 | A table for the owner's approval: each of the 16 slugs → the groups whose code it is about (what it tests, not everything it calls); each of the 46 files → its group, a new group (e.g. `model/measurement-management`), or `@parity none` with a reason. Then the annotations, and the generator passing | done (2026-10-16) — approved as proposed (owner, "Go") |
| 13.3 | Working rule: a new or moved shared test slug gets its `tests=` link on the code it tests in the same change | done (memory) |

**13.1 done (2026-10-16; hub).** `--check` gains two problems, and fails on either:
`UNLINKED` — a `test/*` group that no code group names in its `tests=`; `UNGROUPED` — a file in an edition's code
directories with no `@parity` tag at all. The code directories are declared per edition in `platforms.py`
(`code_dirs`): Swift `GuitarTap/Models`; Python `src/guitar_tap/models`; the web `src/state`, `src/audio`,
`src/measurement`, `src/dsp` (`__init__.py` and `.d.ts` files excepted). The check is per file: a file with one
tagged section passes even if the rest of it is in no group (Python's `realtime_fft_analyzer_engine_control.py`,
tagged only `dsp/wav`, is one). It now reports 16 unlinked slugs and 44 ungrouped files: Swift 18, Python 16, the web 10
(the earlier count of 46 included Python's `__init__.py`). The check fails until 13.2 lands, so the two are committed together.

**13.2 proposal (2026-10-16) — for the owner's approval.** Rule applied: a file joins the group of the code it
belongs to where one exists, so it inherits that group's tests; a new group only where the code is a block of
its own. A new group's web member is the section of the file where the web keeps that code, tagged in place.

*New groups*

| # | new group | Swift | Python | web | tests= |
|---|---|---|---|---|---|
| N1 | `model/measurement-management` | `TapToneAnalyzer+MeasurementManagement` | `tap_tone_analyzer_measurement_management` | `tapToneAnalyzer.ts` (load, save, comparison); `store.ts` | measurement-load, import-persistence, comparison |
| N2 | `model/measurement-codable` | `TapToneMeasurement` (Codable); `SpectrumSnapshot` | `tap_tone_measurement` (to/from dict); `spectrum_snapshot` | `decode.ts`, `encode.ts`, `floatJson.ts`, `base64.ts` | measurement-codable, peak-heal, peak-selection-persistence |
| N3 | `model/measurement-type` | `MeasurementType`; `TapToneMeasurement` (type short name) | `measurement_type`; `tap_tone_measurement` (same) | `types.ts` (MeasurementType) | measurement-type-name |
| N4 | `state/mode-overrides` | `TapToneAnalyzer+ModeOverrideManagement`; `UserAssignedMode` | `…_mode_override_management`; `user_assigned_mode` | `tapToneAnalyzer.ts` (setModeOverride) | frozen-peak-recalc, annotation-state |
| N5 | `state/annotation-management` | `TapToneAnalyzer+AnnotationManagement` | `…_annotation_management` | `tapToneAnalyzer.ts` (label offsets) | annotation-state, frozen-peak-recalc |
| N6 | `state/mode-lookup` | `TapToneAnalyzer+AnalysisHelpers` | `…_analysis_helpers` | `tapToneAnalyzer.ts` (peak mode, tap-tone ratio) | measurement-codable, frozen-peak-recalc |
| N7 | `audio/engine-control` | `RealtimeFFTAnalyzer+EngineControl` | `realtime_fft_analyzer_engine_control` (start/stop, file playback) | `realtimeFFTAnalyzer.ts` (start/stop) | file-playback |
| N8 | `audio/buffer-watchdog` | `RealtimeFFTAnalyzer+Watchdog` | `realtime_fft_analyzer_engine_control` (watchdog) | `realtimeFFTAnalyzer.ts` (watchdog) | none shared — a coverage gap, reported as one |
| N9 | `audio/device-management` | `RealtimeFFTAnalyzer+DeviceManagement`; `AVAudioDevice` | `realtime_fft_analyzer_device_management`; `audio_device` | `realtimeFFTAnalyzer.ts` (input devices) | mic-selection |
| N10 | `dsp/session-recording` | `TapToneAnalyzer+SpectrumCapture` (session recording) | `tap_tone_analyzer_spectrum_capture` (same) | `tapToneAnalyzer.ts` (same); `sampleBuffer.ts` | session-pre-roll |
| N11 | `util/test-sandbox` | `TestSandbox` | `settings_scope` | — (a browser has no shared settings) | — (`util/` is not a tested area) |
| N12 | `util/new-id` | — (Swift mints with `UUID()`, no helper) | `utilities/new_uuid` | `newId.ts` | uuid-case |

*Files joining an existing group*

| file(s) | group |
|---|---|
| `DetectionState` · `detection_state`; `MaterialTapPhase` · `material_tap_phase` | `state/tap-tone-analyzer` |
| `AnnotationVisibilityMode` · `annotation_visibility_mode` | `state/visible-peaks` |
| `AnalysisDisplayMode` · `analysis_display_mode` | `state/button-enablement` |
| `PlateStiffnessPreset` · `plate_stiffness_preset` | `model/material-measurement-inputs` |
| `GuitarType` · `guitar_type` | `dsp/guitar-modes` |
| web `calibrationStore.ts` (Swift's CalibrationStorage is in `MicrophoneCalibration`) | `dsp/calibration` |
| web `guitarFFT.ts` | `dsp/guitar-fft` |
| web `measurement/index.ts` | `@parity none` — re-exports only |

*Slugs linked to existing groups* (the rest are linked by N1–N12 above)

| slug | group(s) |
|---|---|
| audio-clock-timers | `state/tap-detection`, `state/tap-tone-analyzer` |
| display-range | `presentation/display-range` (which has no tests= today) |
| effective-peak-id | `audio/tap-analyzer` (the effective…PeakID properties are in `TapToneAnalyzer`) |
| field-precision | `util/field-precision` (which has no tests= today) |
| peak-selection-persistence | also `dsp/peak-analysis` (Reset to automatic selection) |
| tap-count-change | `audio/tap-analyzer` (`numberOfTaps`) |
| self-regression | the groups `test/file-playback` names: `audio/realtime-analyzer`, `dsp/calibration`, `dsp/fft`, `dsp/gated-capture`, `dsp/guitar-fft`, `dsp/wav` |

**13.2 done (2026-10-16; Swift 3543ac7, Python bb752af, web 0296fd0).** Approved as proposed (owner). The tags are in all three editions — tag lines
only, nothing else changed — and `--check` passes: 140 groups, 30 platform-specific, no problems; the one
coverage gap is `audio/buffer-watchdog`, as proposed. A group's `tests=` is the union over its tags, so existing
groups gained theirs on the tags that already carried a list.

*Seen, not in this step:* two existing slugs break the area naming, `dead-input` (no area, and its group holds
test files) and `models/capture-probe` (`models/` for `model/`). Both are renames touching all three editions.

**Step 11 batch B run-review.** The clipping warning, Dump Capture Audio, the per-tap overlay and reading a saved
comparison changed in the models, and the views that show them are not covered by the tests, so batch B is
run-reviewed before the commit. Launch: Xcode scheme `guitar_tap` · `.venv/bin/python -m guitar_tap` · web
`npm run build && npm run preview`, then clear the service worker after the build (F30's run-review steps). Same list
per edition, Swift first; (S) / (W) marks a step for Swift or the web only. The comparison changes (a comparison
leaving the earlier result, microphone warning and ring-out alone) have nothing to see at the app — the comparison
replaces what is shown, and the microphone warning is an alert dismissed before comparing — so the shared cases
cover them.

1. (W) Turn Dump Capture Audio on in Settings, then press New Tap and tap. → The sequence's recording is saved.
2. (S) Tap hard enough to clip the input. → The clipping warning appears at once, not after a delay.
3. Set Taps to 3 and tap a guitar measurement. Turn the per-tap overlay on. → Each tap and the average are drawn,
   labelled Tap 1, Tap 2, Tap 3 and Averaged.
4. Turn the per-tap overlay off. → The averaged spectrum alone is drawn, with its peaks.
5. Open a saved comparison from Measurements. → Each entry's spectrum and its Air/Top/Back show as before.

| step | Swift | Python | web |
|---|---|---|---|
| 1–5 | ✅ (2026-10-16) | ✅ (2026-10-16) | ✅ (2026-10-16) |

**Run-review progress.** All three editions passed steps 1–5 (owner, 2026-10-16). **Run-review complete.**

**Step 11 batch C (items 1–4) run-review.** Re-analyze, Peak Min and the detector's level changed in the models,
and the views that show them are not covered by the tests. Launch: Xcode scheme `guitar_tap` ·
`.venv/bin/python -m guitar_tap` · web `npm run build && npm run preview`, then clear the service worker after the
build (F30's run-review steps). Same list per edition, Swift first.

1. Load a guitar measurement. Name a peak and drag its label to a new position. Raise Peak Min above that peak,
   press Re-analyze, then lower Peak Min again. Re-analyze resets the selection, so set Annotations to All. → The
   peak shows its name, with its label where it was dragged.
2. Select a different peak by hand, then press Re-analyze. → Automatic selection returns: the loudest peak in each
   mode is selected.
3. Set the type to Plate. Tap for L and press Accept while it still rings, then tap for C; press Redo and tap C
   again. → Each tap is detected with one strike, and the ring-out at Accept or Redo is not taken as a tap.
4. Press New Tap and tap. → One tap per strike, and no tap during the warm-up.
5. Web, in Safari: name a peak with Custom…. → An in-page "Custom Mode Label" dialog (Cancel / Assign), in the
   theme's colours; after Assign, New Tap and a tap are detected.
6. Web, in Safari: delete one measurement, then Delete All. → In-page "Delete Measurement?" and "Delete All
   Measurements?" alerts; afterwards a tap is detected.
7. Web, in Safari: switch the Mac's sound output to another device mid-session (or the hearing aids). → Taps are
   still detected; the console shows the context's state changes and ends on `running`.

| step | Swift | Python | web |
|---|---|---|---|
| 1–4 | ✅ (2026-10-16) | ✅ (2026-10-16) | ✅ (2026-10-16) |
| 5–7 | n/a | n/a | ✅ (2026-10-16; Delete All not exercised — deleting one was) |

All three editions passed (owner, 2026-10-16), Python's step 1 on the re-run after the table fix. **Run-review complete.**

**Run-review progress.** Python, step 1 (owner, 2026-10-16): a peak named "Fred" on a freshly loaded measurement
showed as Unknown after Re-analyze, with its label still where it was dragged; done again without restarting, it
kept its name. Swift passed. Cause: Python's peak table kept its own copy of the names (`PeaksModel.modes`), keyed
by frequency, and showed it before asking the analyzer — the file's 32-bit frequency (568.99994) is not the
re-detected one (568.99996), so the copy missed; the analyzer had kept the name. Decided (owner, 2026-10-16: (A),
as Swift): Python's table and cards read a peak's label and whether it is the user's from the analyzer by peak id
(`effective_mode_label`, `has_manual_override`), as Swift's rows read `effectiveModeLabel` / `hasManualOverride`;
the copy, and the load, rename and guitar-type writes of it, are gone. New shared case PR50 (a fixture's peak named,
hidden, re-analyzed and shown: still its label — the field the three tables show), with a `loadFixture` step and a
`labels` field; Python keeps its own table test of the same steps. Mutations: Python's table ignoring the
analyzer's label fails its table test; the analyzer's label ignoring the name fails PR50. Step 1 to be re-run on
Python. Web (owner, 2026-10-16): after naming a peak the microphone went dead — in Safari only, and in the
released web app (build 213) too; Chrome unaffected. A logged context state (added to find it) showed the audio
context suspended the moment the name was given: the web asked for the name with the browser's `window.prompt`,
during which Safari suspends the page's audio, and nothing resumed it — the engine resumed only at start, and its
watchdogs stand down while the context is not running, so nothing was logged. Deleting a measurement
(`window.confirm`) did the same (owner). Decided (owner, 2026-10-16: both): (A) the engine resumes its context
whenever it stops while in use — at once where the browser allows, else on the next click or key — and logs each
change; (B) the three browser dialogs are in-page: the custom label (`CustomLabelDialog`, Swift's
CustomModeLabelPopover), Delete Measurement? and Delete All Measurements? (`AlertModal`, Swift's titles and
messages), in the theme's colours. Not unit-tested (no AudioContext in the test environment); steps 5–7.

**Step 11 C5 run-review.** The engine's start changed in all three (the web's and Python's start-up rebuilt, Swift's
auto-start split into a method), and the views that start it are not covered by the tests. Launch: Xcode scheme
`guitar_tap` · `.venv/bin/python -m guitar_tap` · web `npm run build && npm run preview`, then clear the service
worker after the build (F30's run-review steps). Same list per edition, Swift first; (P) / (W) marks a step for
Python or the web only.

1. Launch. → The guitar prompt appears, the level meter moves, and a tap is detected.
2. Load a saved measurement, then press New Tap and tap. → The loaded measurement shows until New Tap; the tap is
   detected.
3. (W) With the microphone blocked for the site, reload; then allow it and press Retry microphone. → The alert,
   then a working microphone after Retry, with no reload.
4. (W) Load a measurement while the microphone alert is showing, then press Retry microphone. → The loaded
   measurement stays on screen. **n/a (owner, 2026-10-16):** not reachable by hand — the alert covers the page,
   a click outside it dismisses it, and Retry is only on the alert; a measurement on screen when the engine's start
   completes is pinned by the shared case S7 in all three.
5. (P) Play File before tapping anything, then press New Tap and tap. → The file plays and analyses; afterwards
   the microphone works.
6. Plug in or unplug a microphone. → "Audio device changed - reinitializing…", then the prompt; a tap is detected.
7. (W) In the dev build (`npm run dev`). → The console shows one `🎤 Starting` (passed, owner, 2026-10-16).

**Run-review progress.** Web, step 2 (owner, 2026-10-16): after Load then New Tap, the loaded measurement's peak dots stayed until the first
live frame. The web's New Tap (startTapSequence → clearResult) cleared the frozen spectrum, selection, names and label
positions but not the peaks and their modes, where Swift's and Python's startTapSequence clear them at once (allPeaks
= [], identifiedModes = []) — not from C5; the first run-review to load then press New Tap. Fixed (owner): the web's
startTapSequence clears the peaks and modes and refreshes the display at the same point. New shared case PR51 (a
loaded fixture, New Tap → no peaks); mutation: the web without the clear fails it. The tap-tone-analyzer group's tests
now name frozen-peak-recalc. Step 2 to be re-run on the web.

| step | Swift | Python | web |
|---|---|---|---|
| 1–2, 6 | ✅ (2026-10-16) | ✅ (2026-10-16) | ✅ (2026-10-16; step 2 after the New Tap fix) |
| 3, 7 | n/a | n/a | ✅ (2026-10-16) |
| 4 | n/a | n/a | n/a — not reachable by hand (above) |
| 5 | n/a | ✅ (2026-10-16) | n/a |

All three editions passed (owner, 2026-10-16). **Run-review complete.** Also checked (owner): choosing a
microphone in the app's own Settings still changes the microphone, in all three. Whether it restarts an engine whose
start failed — the recovery the "Audio Engine Error" message names — is not verified: there is no known way to make
the start fail by hand in Swift or Python. The web alone also has Retry on its alerts (a page cannot open the
browser's settings, where Swift's permission alert opens System Settings).

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
