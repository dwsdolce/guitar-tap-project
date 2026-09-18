# Per-configuration baselines: regression and parity

**Status:** ⏳ BUILT, PARTLY MEASURED — Python and web minted on macOS/arm64 and
Windows/x86_64; Linux unminted, Kotlin does not exist. **Issue:** #10 (follow-on). **Depends on:** the oracle cutover, done 2026-09-18.

## Two metrics, not one

| | **Regression** | **Parity** |
|---|---|---|
| Question | Did *this* edition on *this* machine change? | How far apart are the editions? |
| Compared against | That configuration's own committed baseline | The oracle |
| Healthy value | **Exactly zero.** Any movement is a defect. | Never zero. The question is how big is allowed. |
| Bar today | **zero** — live in all editions | **0.02 Hz / 0.01 dB** — tightened 2026-09-18 on six configurations' evidence |
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

### The platform effect, measured (Windows, 2026-09-18)

Both tracking editions are now minted on Windows 11 / x86_64 (Intel i7-12700H), and the
answer to *“is an edition stable across operating systems?”* is **very nearly yes**:

| edition | values | differing macOS/arm64 vs Windows/x86_64 | worst \|Δ\| |
|---|---|---|---|
| Python (NumPy 2.5.1) | 91 | **0** | exactly 0 |
| web (Node 24.20, V8 13.6) | 105 | **1** | 1.78e-15 dB |

Python is **bit-identical** across a different OS *and* a different architecture. The web's
single exception is `GFFT1/expected/100Hz/db`: `-15.722160814127067` on macOS against
`-15.722160814127065` on Windows — bit patterns `…41c9` and `…41c8`, a difference of exactly
**1.000 ULP**. What is distinctive about that case is amplitude: GFFT1 is the only tone
driven at 0.5, roughly 34 dB hotter than GFFT2/3/5 at 0.01–0.1. It is not bin-centring —
GFFT2's tones are off-bin like GFFT1's and match exactly.

A single last-bit difference with 104 values identical is not an algorithmic difference; it
is one rounding landing differently, most plausibly JIT codegen (arm64 contracting a
multiply-add into an FMA where x64 does not) or a different `log10` in V8's libm per
architecture. **Linux will discriminate between those two:** it is x86_64 like Windows but a
different OS, so if linux-x64 matches windows-x64 exactly and both differ from darwin-arm64
here, the cause is architecture rather than operating system.

Consequence for the scheme: the per-OS baseline files are **not** redundant, but they are
close to it. The measured platform effect is zero for Python and one ULP for web — against
an edition effect of 0.0076 Hz, which is **twelve orders of magnitude larger**. Whatever the
bar becomes, it is being set by the edition difference alone; the machine contributes
nothing measurable.

Still unminted: Linux for both editions, and Kotlin everywhere. Kotlin in particular is a
different runtime and could behave unlike either, so no bar set now should be treated as
final for it.

### Where the edition difference comes from (traced 2026-09-18)

**The guitar capture window is onset-aligned in Swift and not in Python or web.**

| | material capture | guitar capture |
|---|---|---|
| Swift | aligns | **aligns** |
| Python | aligns | **`samples[:fft_size]`** |
| web | aligns | **no alignment** |

Swift's comment at that call site states the purpose: *align to the sample-level tap
onset so that chunk-boundary differences don't shift the FFT input.* Two editions skip it
on the guitar path, so they are not handed the same samples. That explains the shape of
every measurement here — Python and web agree with each other to ~1e-14 (both lack it)
and both differ from Swift on the **guitar** path by 0.0004–0.003 dB, while the material
path, where all three align, differs only by ~0.0002–0.00035 dB, matching the separately
identified periodic-vs-symmetric Hann window difference.

Patching Python to align shrinks the per-tap back-peak deltas by 6–52% but does not close
them, so at least one more difference remains in what reaches the aligner. This is the
same family as issues #7 (replay ≠ live capture), #3 (Swift's 4800-frame buffer) and #5.

**Why it surfaces as frequency rather than dB.** Peak frequency comes from a parabola
through three dB bins, `shift = 0.5(l−r)/(l−2v+r)`. Guitar back modes are broad, so that
denominator is small and the fit is ill-conditioned:

| | curvature | sensitivity |
|---|---|---|
| back peaks | −0.39 to −0.61 dB | up to **−2.455 bins/dB** |
| air peaks | −4.41 dB | −0.099 bins/dB |

A 0.0042 dB difference in one neighbouring bin moves the peak 0.0076 Hz. All eight largest
frequency deltas are back peaks; air and top are ~20× smaller. So **freqHz is not an
independent measurement**: 0.01 dB × 2.455 bins/dB × 0.7324 Hz/bin = 0.018 Hz, which is
the bar. Tighten the two together or not at all.

Ruled out by measurement, not argument: float32 at the output stage moves the frequency by
at most 3.2e-6 Hz (2392× too small), and the Hann window form cannot apply to the guitar
path, which uses a rectangular window.

**These bars therefore measure today's state, defects included.** When the alignment gap
closes the editions should converge and the bars will become loose. A sudden jump in the
headroom `parity-report.py` prints is the expected consequence and the signal to
re-measure — not an anomaly. The same warning is carried in the oracle itself
(`_toleranceProvenanceNote`), which is what a future session will actually open.

## The tolerance decision (settled 2026-09-18)

Two bars, and machines enter neither:

* **Same machine, same edition: zero.** Nothing legitimately moves it.
* **Different editions: 0.02 Hz / 0.01 dB** (plus gatedFftDb 0.001, q 1e-05, ringOutSec 1e-07).

Evidence: six configurations across three operating systems and two architectures, worst
measured 0.0076 Hz / 0.0030 dB, **identical to six significant figures on every one of
them**. That last point is what justifies tightening — the edition difference is a
property of the algorithms, not of the machines, so it does not wander. Checked against
all six baselines before adopting: **0 values exceed the new bars**, margins 2.6× to 30×.

Two consequences had to be handled in the same change or the tightening would have been
quietly wrong:

**`REG-P2`'s `magDb: 0.5` override is deleted.** It was written as a *tighter* bar than
the old 1.0 global — the thing that catches a regression to reading the last tap instead
of the averaged spectrum. Against a 0.01 global it inverts to **50× looser**, making the
one case that exists to catch that regression the least protected in the suite. It is
also unnecessary: REG-P2's real deltas are 0.000347 dB (29× inside the new global) and the
regression it guards produces 0.81–2.62 dB, which the global catches with 81–262× margin.

**The first mint gets its own bar** (`bootstrapTolerances`, holding the old 1 dB / 1 Hz).
A new configuration has no prior, so the mint asks the only question available — are these
numbers plausible against the oracle? That had been borrowing the parity number. At 0.01 dB
it would block a port still being built from minting any baseline, leaving it with no
zero-tolerance regression check at exactly the moment it most needs one. Failing parity is
a finding to investigate; failing the first-mint bar means the numbers are garbage.

The generator's tolerance handling changed with it: it rounded these blocks to five decimal
places, which would have silently written `ringOutSec: 0`.

### Not adopted: a cross-platform bit-identity gate

Proposed in the Linux handoff, and the measurement behind it stands — within an edition,
across machines, only five values have ever differed, all dB, all 1–2 ULP, worst 1.42e-14.
It is not being added as a gate. Zero is not achievable there (NumPy's Linux wheel and its
MSVC build carry different `log10` implementations, legitimately 1 ULP apart) and the spread
is 2×10¹¹ times smaller than the edition difference it would share a budget with. The
`PLATFORM:` lines in `parity-report.py` already surface it if it ever moves.

## Known gaps

* ~~**Windows and Linux are unminted**~~ — **Windows is minted** for both editions
  (2026-09-18, results above). **Linux remains unminted** for both, and Kotlin does not
  exist yet: five configurations are reported missing by the hub script.
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
