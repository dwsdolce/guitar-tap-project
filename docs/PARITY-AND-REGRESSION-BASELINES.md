# Per-configuration baselines: regression and parity

**Status:** 📋 DESIGN AGREED — nothing implemented.
**Issue:** #10 (follow-on). **Depends on:** the oracle cutover, done 2026-09-18.

## Two metrics, not one

| | **Regression** | **Parity** |
|---|---|---|
| Question | Did *this* edition on *this* machine change? | How far apart are the editions? |
| Compared against | That configuration's own committed baseline | The oracle |
| Healthy value | **Exactly zero.** Any movement is a defect. | Never zero. The question is how big is allowed. |
| Bar today | zero — live in Swift only | 1 dB / 1 Hz / q 1 / ringOut 0.03 — live everywhere |
| Status | missing on Python, web | live, unchanged by this work |

One number was doing both jobs, which is what let the Swift goldens drift up to
0.0028 dB unnoticed: the bar was four orders of magnitude above the drift.

Python cannot be checked at zero against the oracle. The oracle holds Swift's numbers,
and Python genuinely differs from them — that difference is what the parity metric
exists to measure. A zero bar has to compare an edition against *itself*.

## The mechanism

**Every configuration mints and commits its own absolute baseline** — the same 140
values from the same fixtures, with provenance. Its suite checks itself against its own
file at zero.

The configuration key is **edition × OS × arch**. Deliberately *not* library or
compiler version: if a NumPy or V8 upgrade changes the numbers, that is precisely the
event this is built to catch. Putting the version in the key would make the baseline
follow the upgrade silently.

### Parity falls out of it

Once every configuration has committed its absolute values, the difference between any
configuration and the oracle is subtraction over committed files. No instrumented
assertions, no measurement flag, no parallel harness that can drift from what the suite
actually compares. The candidate tolerance is the max over all of them, computed by a
script that reads nothing but committed data.

It also separates two effects that today's single parity number conflates. Python on
Windows against the oracle mixes *Python differs from Swift* with *Windows-x64 differs
from macOS-arm64*. Hold OS and arch fixed and vary the edition for the edition effect;
hold the edition fixed and vary OS/arch for the platform effect. If the spread is mostly
platform, tightening the cross-edition bar is safe and the real bar is elsewhere; if it
is mostly edition, tightening it is what starts catching real divergence.

**Rejected: storing the delta instead of the values.** It couples every configuration's
regression check to Swift's mint — the day the oracle is re-minted, every committed
delta is wrong, not because any edition changed but because the thing it was measured
from moved. Identical information, needless coupling.

## Where the files live

The oracle flows **hub → repos**: one canonical file, vendored to a path each repo
declares in `tooling/oracle-dest.txt`, `--check` proving the copies identical. No test
opens the hub copy.

Baselines flow the other way. One is minted by exactly one configuration and read by
exactly that configuration — nobody else needs it to run tests. So it lives **beside
that repo's tests** (`tests/self-baseline-<os>-<arch>.json`), readable with no hub
checkout and no network, and is **published up** to the hub, which is the collection
point where the parity arithmetic happens. The hub is upstream for the oracle and
downstream for the baselines.

Swift-macOS-arm64's baseline *is* the oracle; it needs no second file and appears in the
collection as that configuration's entry.

## Minting rules

**The suite never writes a baseline.** Only an explicit opt-in command does — the shape
Swift already has, `GENERATE_PARITY_ORACLE=1` behind `mint-oracle.sh`. If a missing
baseline caused a test run to create one, the check could never fail: delete the file,
run the tests, and whatever the machine currently produces becomes the expected answer.

**Bootstrapping a new configuration** has no prior to compare against, so the first run
is trusted. The one real check available is enforced by the mint: a new baseline may be
written only if its values **pass the parity gate against the oracle**. Within 1 dB /
1 Hz, the numbers are plausible and worth freezing. Outside it, there is no baseline to
commit — there is a finding, and committing it would freeze a bug into the thing meant
to detect bugs.

**Re-minting an existing configuration** is a different act: the script shows the diff
against the current baseline and requires confirmation. That diff is the review artifact
for a deliberate algorithm change — the role the 74-value diff played when the re-minted
Swift goldens were adopted.

**A configuration with no baseline skips its self-regression tests with a loud banner;
it does not fail.** The machine is not unprotected — the parity gate still runs at 1 dB.
Failing hard would block all work on a new platform over a condition that is expected on
a new platform. The danger is that the skip becomes invisible and permanent, so the gap
must be countable: the hub collection script reports which configurations have published
baselines and which never have.

## Costs, stated plainly

A deliberate numeric change means re-minting on **every** configuration, and it is not
finished until each one has. A Windows machine and a browser must be reachable before a
numeric change can land. That is the scheme telling the truth, not a flaw in it.

And once the parity bar is measured rather than assumed, a question arrives that 1 dB
has been suppressing: **if an edition sits 0.05 dB from the oracle, is that acceptable
parity or a bug?**
