# Sweep every `@parity` slug

**Issue:** [#17](https://github.com/dwsdolce/guitar-tap-project/issues/17) · **Status:** ⏳ NOT STARTED

## The problem

`gen_parity_map.py --check` answers one question: does this slug have a test in each edition? It
cannot tell whether those tests assert the same thing, whether they reach production code at all, or
whether the behaviour still exists. And it only sees files that carry a `@parity` tag — eleven do not.

So a slug can report healthy while its three tests measure three different things, or nothing.

## Why we believe that is happening

Issue #8 read **one slug out of 44** closely — `test/frozen-peak-recalc`. It found:

- eight tests that measured nothing (they exercised a helper in the test file, not the app)
- two rows pairing tests that asserted genuinely different behaviours
- a missing test in the canonical edition
- two architectural defects in the web app
- **a data bug that wrote 111 peaks into every saved measurement as 217**
- a classifier returning a guitar mode for peaks it could not classify, including material peaks
- a chart behaviour that existed in Swift and in neither port

That slug was not picked because it looked suspicious. By test-count spread it looked *healthier*
than `test/pitch`, `test/brace`, `test/plate` or `test/classify`. It was simply the one somebody read.

The remaining 43 slugs have had no equivalent reading.

## The two rules to apply

Set by the owner, 2026-09-20:

1. **Every test file carries a `@parity` tag.** `none` is a valid value when justified; absent is not.
2. **No behaviour is tested in only one edition when it exists in more.** A method name that differs
   between editions is not a missing test — look for what the code *does*.

## Stage 1 — sweep and triage

Go slug by slug. For each, answer: is every edition testing the same behaviour, against production
code, for something that still exists?

Four defect shapes to look for. All four occurred in #8 and none is visible to `--check`:

| shape | what it looked like in #8 |
|---|---|
| a test-local helper reimplementing the behaviour under test | `_remap_by_freq` — six tests asserting against a copy of the logic |
| a fixture encoding a contract the app no longer sends | `peak-fullset-save` fed a filtered peak set; the app sends the full one |
| tests pinning a removed feature or an unreachable state | PS1–PS6, green for five months against deleted UI |
| an assertion that holds by construction | asserting a peak is in a list the branch just set to `[thatPeak]` |

[`process/PARITY-TEST-METHOD.md`](../process/PARITY-TEST-METHOD.md) is the method — eight rules,
including how to verify a test is worth keeping (mutate it) and how to avoid the false greens that
caught us three times.

### Starting picture, measured 2026-09-20

**Eleven test files carry no `@parity` tag**, so `--check` has never seen them:

| edition | files |
|---|---|
| Python | `test_wi1_settings_persistence`, `test_wi6_tap_display_settings`, `test_comparison_annotation_guard` |
| web | `calibration-store`, `g0-wav`, `g3a-calibration`, `g6-measurement-bridge`, `g7-measurement-4c`, `g8-material-load`, `g9-multitap` |

**Eight tagged slugs are missing an edition entirely**, and around ten more differ by 2× or worse in
test count. The widest:

| slug | Swift | Python | web |
|---|---|---|---|
| `test/brace` | 20 | 20 | 1 |
| `test/plate` | 28 | 28 | 3 |
| `test/classify` | 37 | 37 | 8 |
| `test/dsp` | 10 | 10 | 0 |
| `test/comparison` | 20 | 32 | 7 |
| `test/measurement-codable` | 53 | 64 | 23 |

⚠️ **Re-measure these before acting on them.** The counts above came from `grep`, which undercounts
table-driven files: one `it(` can expand to six tests at runtime. `test/pitch` looked like 22/22/1
and is really 22/22/6. Use the test runner's own count.

A wide spread is a hint, not a verdict — `test/frozen-peak-recalc` was nearly balanced and was full
of defects.

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
