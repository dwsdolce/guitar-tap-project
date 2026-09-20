# Parity test method — what makes a paired test worth having

Living conventions lifted from the #8 frozen-recalc record (`docs/completed/FROZEN-RECALC-TEST-PARITY.md`)
so they outlive that archive. The record holds the evidence; this holds the rules.

`gen_parity_map.py --check` verifies **presence** — that a slug has a test per edition — and only for
files that carry a tag. Everything below is what presence does not catch.

## 1. A test must reach production code

A helper that reimplements the behaviour under test is not a fixture, it is a second implementation,
and a test against it measures nothing. Eight Python tests passed for months against `_remap_by_freq`,
a test-local copy of the carry-forward logic whose own docstring called it *"the Python equivalent of
the Swift carry-forward logic"*.

Two more shapes with the same effect:

- **Assertions that hold by construction.** The first version of a material test asserted a peak was
  in `allPeaks` — on a branch that assigns `allPeaks = [thatPeak]`. Mutation is what exposed it.
- **Fixtures encoding a contract the application no longer sends.** `peak-fullset-save.test.ts` fed a
  Peak-Min-filtered set long after `App.tsx` started sending the full durable set, and that mismatch
  hid a data bug that wrote 111 peaks as 217. **Check what the APPLICATION passes, not what the test does.**

## 2. Passing is not evidence — mutate

Break the rule the test claims and confirm that test fails, and that no *other* test fails in its place.
Every replacement written during #8 was verified this way, and it repeatedly caught tests that passed
while proving nothing.

When running a subset, **read the count, not the failure list**. `xcodebuild -only-testing` with a name
that matches nothing exits 0 with `passed=0`; so does a `-k` filter that selects nothing. This produced
false greens three times.

## 3. A name that differs between editions is not a missing test

Look for what the code *does*. Six web tests were split into their own orphan slug on the claim they had
no native counterpart; they had them all along — `clearResult` is Swift's `startTapSequence` reset,
`restoreOffsets` is `applyAnnotationOffsets`.

## 4. An "n/a" that rests on the view driving the model is a finding, not a difference

Twice in #8 a behaviour was recorded as "that edition's architecture provides no such state". Both times
that was an accurate description of a defect written down as though it were a design — a display rule
living in a view `useMemo`, and a load spread across five view-orchestrated calls. **When an edition
cannot express a behaviour its siblings test, ask whether the architecture is the reason or the finding.**

## 5. When a feature is removed, its tests are part of the feature

Tests are the last thing keeping removed code alive. PS1–PS6 passed for five months in two editions
against L/C/FLC buttons deleted in April 2026, making dead model code look maintained. The same applies
to tests pinning unreachable states — a fallback arm that no production path can enter.

## 6. Test sandboxes must be per-process

A shared, fixed-name sandbox that is *cleared at startup* is a cross-process mutex nobody declared. On a
dev machine two runs overlap, and the second wipes the first's settings mid-test. This produced an
intermittent wrong-peak failure that survived isolation, CPU load and ordering checks, because it only
reproduces when two processes overlap. Cleanup must also survive the process not exiting cleanly: reap
by dead process id, never rely on a teardown hook.

## 7. Divergence in user-visible behaviour is fixed now, not logged

An implementation difference can be tracked. A behaviour the user can see — a chart that widens onto an
identified peak in one edition and hides it in two — is fixed across all editions in the same change.
Logging it is how divergence continues.

## 8. Count with the runner, not with grep

Table-driven files expand at runtime: one `it(` can be six tests. A grep-based census understates them
and overstates divergence.
