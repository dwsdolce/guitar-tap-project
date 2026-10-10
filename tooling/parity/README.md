# Parity tooling

Cross-platform parity map for **GuitarTap** (Swift, canonical) ↔ **guitar_tap**
(Python) ↔ **GuitarTapWeb** (Web), generated from co-located `@parity <slug>` tags.

## The tag

Every mirrored source file carries one comment naming its **group key** (a stable,
area-namespaced kebab slug). The slug is the join key — the tools discover the paths
by grouping files that share a slug, so paths are never restated and can't disagree.

```swift
// @parity dsp/gated-fft      // Swift / TypeScript
```
```python
# @parity dsp/gated-fft       # Python
```

A file with no counterpart by design uses the reserved slug `@parity none`.

An impl tag may link its behavioural test group with an optional attribute:

```swift
// @parity dsp/gated-fft tests=test/gated-fft
// @parity dsp/material-properties tests=test/brace,test/plate
```

The generator uses that link to fill the map's **Equivalence** column — the honest
answer to "are the contents *actually* equivalent, or just co-located?" A linked
`test/*` group makes the impl group **oracle**-backed (it has a `g#-…` web oracle
test) and/or **tests**-backed (paired Swift+Python tests); unlinked groups read
**review only**. The map asserts *location*; equivalence is proven by the oracle +
paired tests, and this column shows which rows actually have that proof.

## Commands

```
.venv/bin/python tooling/parity/gen_parity_map.py            # regenerate PARITY-MAP.md + parity-index.json + TEST-COVERAGE.md's coverage block
.venv/bin/python tooling/parity/gen_parity_map.py --check    # CI: verify all three are current + no orphan/malformed slugs
.venv/bin/python tooling/parity/gen_parity_map.py --coverage # print the functional-block coverage report (read-only)
.venv/bin/python tooling/parity/gen_parity_map.py --gaps     # report testable impl groups with NO test evidence
.venv/bin/python tooling/parity/parity_lookup.py classify    # show a group's counterparts (any column)
.venv/bin/python tooling/parity/parity_lookup.py . --sort=web    # browse everything, sorted by web path
```

`--coverage` prints the **functional-block coverage report** — of the testable blocks, how many are
covered by a test group, how many are *proven on all three platforms* (≥1 linked `test/*` group that
exists in every repo), and which are gaps — plus a per-area breakdown. The same numbers are written
into `../../TEST-COVERAGE.md`'s "Current coverage state" block by `generate`, and `--check` fails if
that block drifts. `--coverage` is read-only; it never writes.

`--gaps` (also printed by `generate`/`--check`) lists **testable** impl groups
(`dsp/` `audio/` `state/` `model/` — `view/*` is UI, review-only by design) whose
equivalence is "review only", i.e. no `tests=` link to any `test/*` group. Each is a
candidate for a test back-fill or a documented, justified gap. Two "missing-coverage"
checks together: `--check` = *missing on some* platforms (orphan slugs); `--gaps` =
*missing on all* (no test evidence).

## Outputs (committed here, in the hub)

- `PARITY-MAP.md` — single self-contained table; Ctrl-F any path to find its counterparts.
- `parity-index.json` — the database the lookup utility reads.

Repo roots default to the three code repos (`GuitarTap`, `guitar_tap`, `GuitarTapWeb`)
as siblings of this hub; override with `PARITY_SWIFT` / `PARITY_PYTHON` / `PARITY_WEB`.

## Workflow

Change/add/move a mirrored file → add or adjust its `@parity` tag in the same diff →
run the generator → commit the updated `PARITY-MAP.md` + `parity-index.json`. `--check`
fails if the committed map drifts or a slug lands in only one repo (a typo, or something
that should be `@parity none`). Design rationale: `../../docs/completed/PHASE6-PARITY.md` § 6-MAP.

The living **coverage reference** (the `@parity` system, equivalence levels, the
change-all-three rule, the gates, current gaps/reverse-gaps, and the full layout of where
every coverage artifact lives) is **`../TEST-COVERAGE.md`** (in the hub's `tooling/`).
## Operating rules for the oracle and the self-baselines

Extracted from the #10 build-out (2026-09) so the rules live beside the commands rather than in an
archived record. The measurements and the reasoning behind the numbers are in
[`../../docs/completed/PARITY-AND-REGRESSION-BASELINES.md`](../../docs/completed/PARITY-AND-REGRESSION-BASELINES.md).

### Two bars, and machines enter neither

| | compares | against | bar |
|---|---|---|---|
| **regression** | one configuration | **its own** prior baseline | `selfTolerances` in `parity-oracle.json`: 1e-12 |
| **parity** | one edition | the oracle | `tolerances` in `parity-oracle.json` |

The regression bar is 1e-12, not zero, only because one configuration runs on different CPUs —
GitHub's runners, different people's machines — whose vectorised maths can differ in the last bit
(7e-15 between Linux runners, 2026-10-10); 1e-12 is still a million times below the smallest real
change. Every edition reads it from the oracle and maps a value to its class by the leaf its path
ends in (the table in `parity-report.py`).

A tracking edition cannot be checked at the regression bar against the oracle — the oracle holds Swift's numbers,
and the distance to them is what the parity bar measures. So every configuration
(**edition × OS × arch**) mints its own absolute self-baseline and is checked against itself.

The configuration key deliberately excludes library, runtime and compiler versions. A NumPy, V8 or
Xcode upgrade that moves the numbers is precisely the event the regression bar exists to catch; keying on
the version would let the baseline follow the upgrade and report nothing.

### A suite never writes its own expectations

Minting is always an explicit command (`mint-oracle.sh`, `mint-baseline.py`,
`mint-baseline.sh`), never a side effect of a test run. If a missing baseline caused a run to create
one, the check could never fail: delete the file, run the tests, and whatever the machine produces
today becomes the answer it is checked against.

- **First mint** on a new configuration has no prior, so the values must clear
  `bootstrapTolerances` — a deliberately separate, looser bar. Failing *parity* is a finding to
  investigate; failing *this* means the numbers are garbage and must not be frozen. Sharing one
  number would mean a port still being built loses its regression check exactly when it most
  needs one.
- **Re-mint** of an existing configuration prints the diff and requires confirmation. That diff is
  the review artifact: adopt it only if a deliberate change explains every line.
- **No baseline** → the configuration skips its regression tests loudly; it is still covered at the
  parity bar. The gap must stay countable (`parity-report.py` names every unminted configuration),
  because an invisible skip is how a check dies.

### Which direction each file flows

The oracle flows **hub → repos** (`sync-oracle.sh`, `--check` proves the copies identical; no test
opens the hub copy). Self-baselines flow the other way: minted and read by one configuration, they
live beside that repo's tests and are published **up** to `parity/baselines/` where
`parity-report.py` can see them all. Swift-on-macOS's baseline *is* the oracle — it minted it.

**Publish before you sync.** Minting into the Swift repo and then running `sync-oracle.sh` elsewhere
pulls the hub's *older* copy back down and silently undoes the mint.

### Changing the tolerances

`tolerances` measures today's state, defects included — see `_toleranceProvenanceNote` in the oracle
itself, which is what someone changing the numbers will actually open. `freqHz` is **not**
independent of `magDb`: peak frequency comes from a parabola through three dB bins, and on broad
modes that fit reaches ~2.5 bins/dB, so a magnitude difference becomes a frequency difference.
Tighten the two together or not at all.
