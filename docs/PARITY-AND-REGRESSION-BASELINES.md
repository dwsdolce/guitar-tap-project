# Per-configuration baselines: regression and parity

**Status:** ⏳ BUILT, NOT RUN-REVIEWED — Python and web minted on macOS/arm64; Windows and
Linux unminted. **Issue:** #10 (follow-on). **Depends on:** the oracle cutover, done 2026-09-18.

## Two metrics, not one

| | **Regression** | **Parity** |
|---|---|---|
| Question | Did *this* edition on *this* machine change? | How far apart are the editions? |
| Compared against | That configuration's own committed baseline | The oracle |
| Healthy value | **Exactly zero.** Any movement is a defect. | Never zero. The question is how big is allowed. |
| Bar today | zero — live in Swift only | 1 dB / 1 Hz / q 1 / ringOut 0.03 — live everywhere |
| Status | live in all three (Python/web added 2026-09-18) | live, unchanged by this work |

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


## As built

| Piece | Python | Web | Swift |
|---|---|---|---|
| Runs every case, shared by mint and check | `tests/parity_runner.py` | `test/parityRunner.ts` | the generator |
| Configuration key + baseline load + flatten | `tests/self_baseline.py` | `test/selfBaseline.ts` | — |
| Zero-tolerance check | `tests/test_self_regression.py` | `test/self-regression.test.ts` | already live (`selfTolerances`) |
| Mint | `Tooling/mint-baseline.py` | `tooling/mint-baseline.sh` → gated test | `Tooling/mint-oracle.sh` |
| Committed baseline | `tests/self-baseline-<os>-<arch>.json` | `test/fixtures/self-baseline-<os>-<arch>.json` | the oracle |

Hub: `tooling/collect-baselines.py` pulls each repo's baseline into
`tooling/parity/baselines/`; `tooling/parity-report.py` does the arithmetic.

The runner is shared with the parity suite in both editions — web's
`file-playback.test.ts` imports `playGuitar`/`playMaterial` from it rather than keeping
its own copy — so the numbers in the baseline are the numbers the parity assertions see.
That was the point of instrumenting nothing: there is one implementation, not two.

## Staleness: the vendored copy vs canonical (#10 step 4)

Every repo commits its own oracle so the suite runs offline, and that convenience is also
the failure mode — a copy can sit in a repo for months, quietly stale, while canonical
moves on. Nothing notices, because every test passes against the stale copy.

`sync-oracle.sh --check` was the answer and had to be remembered. It is now a test
(`tests/test_oracle_sync.py`, `test/oracle-sync.test.ts`) that runs it: exit 0 passes,
exit 1 fails with the diff, and an unreachable canonical **skips loudly** rather than
failing. That last part is forced by the hub being private — the published URL 404s, so
canonical is only reachable through `ORACLE_SRC` pointing at a local hub checkout, which
most machines do not have. Failing everywhere for a condition nobody can fix locally
would just train people to ignore it. When the hub goes public (#11) the URL resolves and
this begins checking everywhere with no change to the tests.

Swift is the exception: its test host is sandboxed and `Process` is macOS-only, so it
cannot shell out to the script. There it stays a manual step in the release checklist.

## What the first measurement says

Python and web, both on macOS/arm64, against the oracle:

| class | worst \|Δ\| | bar in force | headroom |
|---|---|---|---|
| freqHz | 0.0076 Hz | 1 Hz | 132× |
| magDb | 0.0030 dB | 1 dB | 339× |
| gatedFftDb | 0.00017 dB | 1 dB | 5761× |
| q | 6.7e-07 | 1 | 1.5e+06× |
| ringOutSec | 3.3e-09 s | 0.03 s | 9e+06× |

Swift's side of that comparison is solid: the same numbers come back bit-identical from
macOS/arm64, an M5 iPad and an A19 Pro iPhone, so the deltas below are edition
differences and not platform noise on the reference.

The decomposition is the interesting part. **Python and web agree with each other to
~1e-14** — the last bits of double precision — while both sit ~0.0076 Hz and ~0.003 dB
from the oracle. The entire measured edition effect is therefore *Swift versus the other
two*, and the two tracking editions are numerically indistinguishable from each other.

That is one platform. The bar must also cover Windows, Linux and eventually Kotlin, and
none of those have been minted — so this is not yet an argument for tightening anything.

### What it is not (measured, not assumed)

The editions do not compute at the same precision: Swift's `computeGatedFFT` is `[Float]`
end to end (`vDSP_DFT_zrop`, `vDSP_hann_window` are single-precision), Python pads into a
`float64` array and runs a float64 FFT, and JavaScript has only doubles. That asymmetry
is real and nobody chose it — each edition took its platform's idiomatic path.

It is *not*, however, the explanation for the numbers above. Re-running the gated cases
with the Python chain forced to single precision does not move them, and the gated-FFT
delta is a near-constant ~1.7e-4 dB on every tone rather than the scattered, magnitude-
dependent error precision loss would produce. A constant relative offset of ~2e-5 points
instead at the window: Swift uses the *periodic* Hann `0.5(1 − cos(2πn/N))` and
numpy/web the *symmetric* `0.5(1 − cos(2πn/(N−1)))`, a difference already documented in
`RealtimeFFTAnalyzer+FFTProcessing.swift`.

The 0.0076 Hz frequency delta comes through a different path (guitar FFT plus peak
interpolation) and has **not** been attributed to anything yet. Both questions — whether
the canonical edition should be the least precise one, and what actually produces that
frequency delta — are open, and they are exactly what this measurement exists to surface.

## Known gaps

* **Windows and Linux are unminted** for both editions, and Kotlin does not exist yet.
  Seven configurations are reported missing by the hub script.
* ~~**Swift's zero bar holds only on the minting machine.**~~ **Measured, and it does
  not.** The full Swift suite was run on real hardware against the macOS-minted oracle at
  zero tolerance: iPad Pro 13-inch (M5) and iPhone 17 Pro Max (A19 Pro), both iOS 26.6.2,
  **491 passed / 0 failed** each, all five REG cases plus ring-out and the gated-FFT
  parity cases included. Swift is bit-identical across three chip generations and two
  operating systems, so iOS needs no separate baseline — the oracle already serves as its
  self-baseline, now by measurement rather than assumption. (Intel is moot: there are no
  Intel Macs left here.) The toolchain remains the live variable, and a different Xcode
  that moves the numbers will fail at zero — which is exactly what is wanted.
* **The web baseline is a Node measurement.** The suite runs under V8 in Node, so it
  characterises the web DSP on this OS and arch — not Safari, which is a separate
  question a browser harness would have to answer.
* **Cost:** the zero-tolerance check re-runs every fixture, adding ~100 s to the Python
  suite and ~95 s to the web suite.
