# Sweep every `@parity` slug — false twins, untagged files, dead tests

**Issue:** [#17](https://github.com/dwsdolce/guitar-tap-project/issues/17) · **Status:** ⏳ NOT STARTED

**Method:** [`process/PARITY-TEST-METHOD.md`](../process/PARITY-TEST-METHOD.md) — the eight rules this
work is applying, lifted from #8. Read that first; it is short and it is the whole approach.
**Evidence behind them:** [`docs/completed/FROZEN-RECALC-TEST-PARITY.md`](completed/FROZEN-RECALC-TEST-PARITY.md).

## Why this exists

#8 fixed the `test/frozen-peak-recalc` slug and, in doing so, showed the problem is not that slug.

**Everything #8 found came from reading ONE slug out of 44 — and not the suspicious one.** By
edition-to-edition test-count spread, `test/frozen-peak-recalc` looked *healthier* than `test/pitch`,
`test/brace`, `test/plate` or `test/classify`. Inside it: eight tests measuring nothing, two false-twin
rows, a missing canonical test, two web architecture defects, a duplicate-peak data bug in every saved
measurement, a wrong-guess classifier, and a user-visible chart behaviour that existed in Swift alone.

There is no reason to think that slug was unusual. It was the one anyone read closely.

`gen_parity_map.py --check` cannot see any of it: it verifies **presence**, and only for tagged files.

## The two rules being applied (owner, 2026-09-20)

1. **Every test file carries a `@parity` tag**, with `none` a deliberate and justified value.
2. **No behaviour is tested in only one edition when it exists in more.** A name that differs between
   editions is not a missing test — look for what the code *does*.

## Stage 4 first — the mechanical sweep

Deliberately **before** Stage 3. Stage 3's schema would otherwise be designed against a sample of one,
and frozen-recalc is the least representative slug there is: it needs stateful analyzer setup where most
slugs are input→output.

### Measured 2026-09-20 — the starting picture

**11 test files carry no `@parity` tag** (invisible to `--check`):

| edition | untagged |
|---|---|
| Python | `test_wi1_settings_persistence`, `test_wi6_tap_display_settings`, `test_comparison_annotation_guard` |
| web | `calibration-store`, `g0-wav`, `g3a-calibration`, `g6-measurement-bridge`, `g7-measurement-4c`, `g8-material-load`, `g9-multitap` |

*(`TestRunner.swift` and `conftest.py` are infrastructure, not tests.)*

**8 tagged slugs are missing an edition entirely**; ~10 more show a 2×+ spread. Worst first:

| slug | Swift | Python | web |
|---|---|---|---|
| `test/brace` | 20 | 20 | 1 |
| `test/plate` | 28 | 28 | 3 |
| `test/classify` | 37 | 37 | 8 |
| `test/dsp` | 10 | 10 | 0 |
| `test/comparison` | 20 | 32 | 7 |
| `test/measurement-codable` | 53 | 64 | 23 |

⚠️ **These counts came from grep and are known to be wrong for table-driven files** — one `it(` can be
six tests. `test/pitch` looked like 22/22/1 and is actually 22/22/6. **Re-measure with the runner
before acting on any row.** (Rule 8.)

### Defect shapes worth detecting automatically

All four were seen in #8, and all four are invisible to `--check`:

- test-local helpers that reimplement the behaviour under test (`_remap_by_freq`)
- fixtures encoding a contract the application no longer sends (`peak-fullset-save`)
- tests pinning removed features or unreachable states (PS1–PS6; the `?? autoSelected*PeakID` arm)
- assertions that hold by construction

## Stage 3 after — shared case data

Move case lists into shared data vendored like `parity-oracle.json`, with one runner per edition, so
divergence is **unrepresentable** rather than detectable.

The pattern is already proven in-tree and needs no prototype: web's `pitch.test.ts` is a row list plus a
loop that generates the cases. What is unknown is which *shape* of schema each family of slugs needs —
which is what Stage 4 answers.

Design it **once**, against evidence from all 44 slugs.

## Expect production defects

#8 was opened as a test-infrastructure issue and found a data-loss bug, two architecture defects and a
user-visible behaviour gap. Budget for the same here — and per rule 7, user-visible divergence found on
the way is fixed in the same change, not logged.
