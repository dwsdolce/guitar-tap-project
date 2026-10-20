# Platform baselines — Windows and Linux checked on real machines, iPad and iPhone minted, the tolerance set

**Issue:** [#16](https://github.com/dwsdolce/guitar-tap-project/issues/16)

Status: **OPEN — items 1–3 done; item 4 done (Swift `84f8845`) — iOS is two configurations, a device and the
simulator, each with its baseline; item 5 next.** Detail doc written 2026-10-19 (the Issue was opened before
detail docs were the rule).

## What the baselines are

Each configuration (an edition on one operating system and architecture) checks two things on every full run
(`tooling/parity/README.md` has the rules):

- **Regression** — the configuration against **its own** minted baseline, at `selfTolerances` (1e-12). Nothing
  legitimately moves it; a difference is a change to the analysis.
- **Parity** — the edition against the **oracle** (Swift on macOS, `tooling/parity/parity-oracle.json`), at
  `tolerances`: 2e-04 Hz / 1e-04 dB (0.02 Hz / 0.01 dB until item 5, 2026-10-19).

A baseline is minted by the configuration it belongs to, beside that repo's tests, and collected into the hub
(`tooling/collect-baselines.py` → `tooling/parity/baselines/`), the one place that sees every configuration.

## State, 2026-10-19

| Configuration | Baseline | Minted |
|---|---|---|
| Swift, macOS arm64 | the oracle (`parity-oracle.json`, oracle version `777a951`) | 2026-10-14, on the Mac |
| Python, macOS arm64 | `baselines/python-darwin-arm64.json` | 2026-10-13/14, on the Mac |
| web, macOS arm64 | `baselines/web-darwin-arm64.json` | 2026-10-13/14, on the Mac |
| Python, Linux x86_64 | `baselines/python-linux-x86_64.json` | 2026-10-13, on the CI runner (hub `1e8a5c1`) |
| web, Linux x86_64 | `baselines/web-linux-x86_64.json` | 2026-10-13, on the CI runner |
| Python, Windows x86_64 | `baselines/python-windows-x86_64.json` | 2026-10-13, on the CI runner |
| web, Windows x86_64 | `baselines/web-windows-x86_64.json` | 2026-10-13, on the CI runner |
| Swift, iPad | none — checked against the macOS oracle | never |
| Swift, iPhone | none — checked against the macOS oracle | never |

All were collected into the hub on 2026-10-14 (`96d7eb0`, #3 item 8). Nothing since was meant to move a value:
#17's changes left every reference peak unchanged in the suites that ran. CI on 2026-10-19: Linux passes for
Python and the web, Windows for the web; Python's one Windows failure was a test's setup (an unmovable folder
Windows does not enforce), fixed in Python `6a4a4e6`.

The Issue's original text (Windows and Linux "not re-minted") predates the 2026-10-13 re-mint.

**The tolerance.** `tolerances` was measured on the six Python and web configurations: 0.0076 Hz / 0.0030 dB,
identical to six significant figures across three operating systems and two architectures, set at 0.02 / 0.01
(`_selfToleranceNote` and `_toleranceProvenanceNote` in the oracle). iPad and iPhone are not in that measurement.

**iPad and iPhone.** Owner, 2026-10-08: they are regression platforms like Python and the web on each operating
system — each mints its own results and is checked against them exactly, and against Swift on macOS at the
cross-edition tolerance; one iOS baseline will do if iPad and iPhone agree. The Swift suite's first iOS run
(2026-10-08) showed last-bit differences from the macOS oracle.

## Items

| # | Item | Status |
|---|---|---|
| 1 | Windows and Linux: the full suites run on the real Windows machine and the Linux VM, against the CI-minted baselines | **done** (2026-10-19) — Linux and Windows, all four steps |
| 2 | macOS: the full suites of Swift, Python and the web | passed (2026-10-19) |
| 3 | iPad and iPhone simulators: Swift's full suite; record what differs from the macOS oracle | run (2026-10-19) — three failures, below |
| 4 | iPad and iPhone baselines: Swift mints its own configuration's baseline on iOS, its regression check reads it there, `collect-baselines.py` gathers it and `parity-report.py` reports it | done (2026-10-19, Swift `84f8845`) — two configurations: device and simulator, below |
| 5 | The tolerance re-measured with every configuration (`tooling/parity-report.py`) and decided | decided (owner, 2026-10-19) — 2e-4 Hz, 1e-4 dB, 5e-5 dB, 1e-5, 2e-8 s; verified on macOS, iOS simulators and devices; Swift `10aa335`, Python `42a010d`, web `2dcac47`; Windows and Linux to re-run |
| 6 | Swift's simulator export UI jobs on CI fail now and then — the Files picker never draws (the simulator's document service not scheduled), nothing is exported; the next run passes. Seen on iPhone (`626f023`, `fb5b0e6`, `d6b6297`, `9beff54`, `4c8d812`, `cde0605`, `0fe7630`) and iPad (`e4d9951`, `fb5b0e6`, `85a290a`, `c641dfa`). Owner, 2026-10-19: dealt with before #16 closes | open |

Owner, 2026-10-19: Windows and Linux are done only when the minted tests pass on the real machines (item 1).

### 1. Windows and Linux on the real machines

For the Windows machine (Cygwin bash; write `.venv/Scripts/python` where these say `.venv/bin/python`) and the
Linux VM:

1. Pull `main` in `guitar_tap` (at `6a4a4e6` or later) and `GuitarTapWeb` (at `ee20ac9` or later).
2. In `guitar_tap`: `.venv/bin/python -m pytest` — the full suite, the playback regression and the self-regression
   included. → Everything passes; `test_self_regression` passes, not skipped (a skip means that machine's baseline
   was never minted).
3. In `GuitarTapWeb`: `npm run test` — the full suite, `file-playback` and `self-regression` included. →
   Everything passes.
4. The export check: `Tooling/run-export-check.sh` in `guitar_tap`, `npm run test:exports` in `GuitarTapWeb`. →
   "20 exports checked, 0 failing".

Report here, under this item: the machine, the commits run, and each step's result — for a failure, the test's
name and message.

*Windows:* **all four steps pass** (2026-10-19).

Machine: the Windows machine — Dell G16 7620, `Windows-11-10.0.26300`, Intel i7-12700H; Python 3.14.8 / NumPy
2.5.4; Node 26.11.1 / V8 `14.6.202.34-node.37`; Git Bash.
Commits run: `guitar_tap` `6a4a4e6`, `GuitarTapWeb` `ee20ac9`, hub `0ba2a1e` — all three already at the required
commits and level with `origin/main`, so step 1 pulled nothing.

| Step | Result |
|---|---|
| 2. `.venv/Scripts/python -m pytest` | **1469 passed, 1 skipped** (6:50). `test_self_regression` **passed, not skipped**; `test_oracle_sync` passed, not skipped |
| 3. `npm run test` | **68 files, 1352 passed, 1 skipped** (4:09), `self-regression` and `file-playback` included |
| 4. `Tooling/run-export-check.sh` | **20 exports checked, 0 failing** |
| 4. `npm run test:exports` | **10 Playwright exports passed, then 20 exports checked, 0 failing** |

The one skip is the same as on Linux, in both editions: `the capture probe is switched off`.

**Different hardware from the minting, again:** Python's Windows baseline came from a Windows Server 2025 runner
on an AMD CPU (`AMD64 Family 26`), the web's from an **AMD EPYC 7763**, against an Intel i7-12700H on Windows 11
here — same Python / NumPy, and the same Node and V8.

**On the Node pin.** As on Linux, the web suite first ran on this machine's Node 24.20.0 (V8 13.6) and passed with
the identical counts, export check included. It was then re-run on the pinned 26.11.1 (installed with `fnm`,
followed by `npm ci` and `npx playwright install chromium`), and the result was the same again; the figures above
are from the pinned run.

*Linux:* **all four steps pass** (2026-10-19).

Machine: the Linux VM — VMware guest, `Linux-7.0.0-38-generic`, glibc 2.39, Intel i7-12700H; Python 3.14.8 /
NumPy 2.5.4; Node 26.11.1 / V8 `14.6.202.34-node.37`.
Commits run: `guitar_tap` `6a4a4e6`, `GuitarTapWeb` `ee20ac9`, hub `180c810` — all three already at or above
the required commits and level with `origin/main`, so step 1 pulled nothing.

| Step | Result |
|---|---|
| 2. `.venv/bin/python -m pytest` | **1469 passed, 1 skipped** (6:37). `test_self_regression` **passed, not skipped**; `test_oracle_sync` passed, not skipped |
| 3. `npm run test` | **68 files, 1352 passed, 1 skipped** (2:53), `self-regression` and `file-playback` included |
| 4. `Tooling/run-export-check.sh` | **20 exports checked, 0 failing** |
| 4. `npm run test:exports` | **10 Playwright exports passed, then 20 exports checked, 0 failing** |

The one skip is the same deliberate test in both editions — `the capture probe is switched off`
(`test_session_pre_roll` / `session-pre-roll.test.ts`), not a baseline skip.

**The baselines were minted on CI hardware quite unlike this machine**, which makes the pass worth more than a
formality: Python's Linux baseline came from an Azure runner (`Linux-6.17.0-1022-azure`), the web's from an
**AMD EPYC 7763**, against an Intel i7-12700H in a VM here. Same Python 3.14.8 / NumPy 2.5.4 / glibc 2.39 and
the same Node and V8. The configuration key (edition × OS × arch) therefore does hold across machines at
`selfTolerances`, which is what it claims to do.

**On the Node pin.** The web suite was first run on this machine's Node 24.18.0 (V8 13.6) and passed with the
identical count; it was then re-run on the pinned 26.11.1 (V8 `14.6.202.34-node.37`, matching the baseline's
provenance exactly) and the result was the same again. So at `selfTolerances` the web suite is insensitive to
that V8 major change — but the pinned version is what the figures above were taken on.

**Setting this machine up, for whoever runs Windows** (none of it a product problem, all of it stopped the run):

- `GuitarTapWeb` needs **its own `.venv`** for the export checker — `python3.14 -m venv .venv` then
  `.venv/bin/pip install -r requirements-dev.txt`, per that repo's README. Without it
  `run-export-check.sh` stops with "No .venv: set it up as the README's …".
- After `npm ci` under the pinned Node, **Playwright's browser build moves** and must be reinstalled:
  `npx playwright install chromium`. Until then all ten export tests fail with
  `browserType.launch: Executable doesn't exist … chromium_headless_shell-1248`. Note that
  `npm run test:exports` still **exits 0** in that state, so the failure has to be read out of the output
  rather than trusted to the exit status.

### 2. macOS, full suites (2026-10-19)

All pass: Python `6a4a4e6` — 1469 passed, 1 skipped (the capture probe, switched off); web `ee20ac9` — 1352 passed,
1 skipped; Swift `dc5620e` — 282 tests in 83 suites. CI the same day: Python passes on Windows, Linux and macOS;
the web passes; Swift's unit, Mac and iPhone jobs pass (the iPhone job's earlier red runs were the CI simulator
stalling in the Files picker — GuitarTap idle, Apple's document service not scheduled — and the same tests pass
locally).

### 3. iPad and iPhone simulators, Swift's full suite (2026-10-19, `dc5620e`)

iPad Air 11-inch (M4) and iPhone 17: 247 tests in 81 suites, the same three failures on both:

| Test | Case | Got (iOS) | Expected (macOS) | Difference | Kind |
|---|---|---|---|---|---|
| file-playback regression | REG-G2, air frequency | 87.2331 Hz | 87.23311 Hz | 7.6e-6 Hz | iOS's last bit against the macOS oracle at 1e-12 — what item 4 is for |
| gated-FFT parity | GFFT3, 117.1875 Hz and the delta | −29.507292 dB, 20.192564 dB | −29.50729 dB, 20.192566 dB | 1.9e-6 dB | the same |
| buffer watchdog | BW15 (no recovery while the microphone is not authorized) | 2 restarts, 2 attempts | 0, 0 | — | Swift's tick compiles its permission guard only on macOS (`#if os(macOS)`), though `microphoneAuthorized` already returns true elsewhere; so on iOS the case's "not authorized" never reaches the tick. Production is unaffected (iOS is always "authorized" there); Python calls the guard on every platform, its function answering per platform. **Fixed** (owner, 2026-10-19): the tick calls it on every platform, as Python's — Swift `c641dfa`; BW15 passes on the iPhone simulator and on macOS |

So item 3 leaves the two oracle differences. They are about a million times below the cross-edition bar (0.02 Hz / 0.01 dB) and match the
first iOS run of 2026-10-08. Item 4 gives iOS its own baseline, against which they are exact.

### 4. iPad and iPhone baselines — plan (2026-10-19, for the owner's review)

**How the others do it.** Python and the web each keep a self-baseline beside their tests,
`self-baseline-<os>-<arch>.json`: `configuration` (edition, os, arch), `provenance` (when, on what, against which
oracle version) and `values` — the oracle's own sections (`filePlayback`, `gatedFft`), computed by that
configuration. The suite checks itself against it at `selfTolerances` (1e-12), and separately against the oracle at
`tolerances`; a configuration never minted skips its regression check and says so. Minting is a deliberate tool,
never the suite: the first mint must clear `bootstrapTolerances` against the oracle; a re-mint prints the diff and
asks. `collect-baselines.py` gathers the files into the hub; `parity-report.py` measures across them.

**Swift today.** Swift on macOS minted the oracle, so its tests (`FilePlaybackRegressionTests`,
`GatedFFTParityTests`) check against the oracle at 1e-12. On iOS that is the wrong reference: item 3's two
failures are iOS's last bit against macOS's numbers.

**The plan.**

1. **The file.** `GuitarTapTests/self-baseline-ios-arm64.json`, in the shared format: `configuration`
   `{edition: swift, os: ios, arch: arm64}`; `provenance` (minted at, oracle version, the simulator and its iOS
   version, Xcode); `values` computed by Swift's own oracle generator (`GenerateParityOracle`), so iOS's numbers
   come from the code that makes the oracle.
2. **Minting.** `Tooling/mint-baseline.sh --simulator <name>` in Swift, as Python's `mint-baseline.py` behaves: it
   runs the generator in baseline mode on the simulator; the test hands the file out as a test attachment (as the
   export UI tests do — a simulator test cannot be relied on to write into the repo); the script extracts it, and
   then either checks a first mint against the oracle at `bootstrapTolerances` or prints the diff against the
   existing file and asks. `--check` writes nothing.
3. **The tests.** One reference for Swift's own regression checks: on macOS the oracle (it minted it), on iOS the
   iOS self-baseline, at `selfTolerances` — `FilePlaybackRegressionTests` and `GatedFFTParityTests` read it. On iOS
   the suite also checks against the oracle at `tolerances`, as Python and the web do. With no iOS baseline the
   regression check skips with a notice.
4. **One baseline for iPad and iPhone** (owner, 2026-10-08), if they agree: mint on the iPad Air simulator, then
   run the iPhone 17 against it. If they differ at 1e-12, the key gains the device (`ios-ipad`, `ios-iphone`) and
   each mints its own — to bring to the owner then.
5. **The hub.** `collect-baselines.py` gathers Swift's iOS baseline as it does the others (today it takes Swift's
   only from the oracle); `parity-report.py` then reports it — iOS against macOS is Swift's *platform* effect.
6. **Tags.** Swift's new files join `tooling/mint-baseline` and `tooling/self-baseline`, which Python and the web
   already carry.
7. **CI.** Swift's CI ran its unit tests on macOS only; the iPad and iPhone jobs ran the export UI tests. Owner,
   2026-10-19: the iPad and iPhone jobs run the unit suite too, so the iOS regression is checked on every push.
8. **The physical iPad and iPhone** (owner, 2026-10-19): the minted baseline is also checked on the owner's own
   devices — Swift's full suite run on each, connected to the Mac. If a device differs from the simulator's
   baseline at 1e-12, the configuration key separates them (simulator and device) — to bring to the owner then.

Verification: on the iPad Air and iPhone 17 simulators and on the physical iPad and iPhone, Swift's full suite
passes; on macOS unchanged; a value altered in the iOS baseline fails the iOS regression check; CI's iPad and
iPhone jobs run the unit suite and pass; `parity-report.py` lists the iOS configuration.

### 5. The cross-edition tolerance — plan (2026-10-19)

**Today's measurement** (`tooling/parity-report.py`, the seven configurations collected — iOS not yet in it):

| Value | Worst distance from the oracle | Bar in force | Headroom |
|---|---|---|---|
| frequency | 2.04e-5 Hz (REG-B2 longitudinal) | 0.02 Hz | 981× |
| magnitude | 1.16e-5 dB (REG-G2 tap 5 back) | 0.01 dB | 866× |
| gated FFT | 4.17e-6 dB (GFFT3) | 0.001 dB | 240× |
| q | 6.67e-7 (REG-P1 cross) | 1e-5 | 15× |
| ring-out | 1.51e-9 s (REG-G1) | 1e-7 s | 66× |

The oracle's note still gives the spread as 0.0076 Hz / 0.0030 dB, which set the bars at 0.02 / 0.01; since #3
aligned the guitar capture in all three editions it is about 400 times smaller, so the bars no longer catch a
divergence below them. The spread is almost all Swift against Python and the web (32-bit floats against 64-bit);
Python against the web, and one operating system against another, differ by about 1e-14 or not at all.

**The plan.**
1. With the iOS baseline minted, re-run the report on all eight configurations — iOS against macOS is Swift's own
   platform effect, not yet measured.
2. Propose new bars at a few times the worst measured — of the order of 1e-4 Hz and 1e-4 dB, 5e-5 dB for the gated
   FFT, the same margin for q and ring-out — frequency and magnitude together (the oracle's note: a magnitude
   difference becomes a frequency one through the peak fit). The numbers are the owner's decision.
3. Bring the oracle's notes (`_selfToleranceNote`, `_toleranceProvenanceNote`) up to today's measurement; record the
   decision and the numbers here.
4. Re-mint the oracle with the new bars on macOS, sync it to Python and the web, run the full suites, and hand
   Windows and Linux the item 1 check again.

#### Item 4 — done (2026-10-19, Swift `84f8845`)

**What was found.** The first iOS baseline was minted on the iPad Air simulator, and the iPhone 17 simulator
computed the same 94 values exactly. On the owner's **physical** iPad M5 (`iPad17,3`, iPadOS 27.0.1) and iPhone 17
Pro Max, the suite failed the same three values — the other way: the devices compute exactly what macOS computes
(all 94 values), and the **simulator** differs from both in REG-G2's air frequency (7.6e-6 Hz) and GFFT3 (1.9e-6
dB). The simulator's runtime, not iOS, is what differs. Owner, 2026-10-19: two configurations (plan point 8's
fallback) — a physical device mints its own baseline, as every configuration does, rather than borrow the oracle.

**What is in place** (Swift `84f8845`; bytecode untracked in `a104591`):
- `ParityOracle.configuration()` — the key `swift-ios-simulator-arm64` on a simulator, `swift-ios-arm64` on a
  device; `ParityOracle.reference` — the oracle on macOS, else that configuration's self-baseline laid over the
  oracle's cases (nil, with a notice, if never minted).
- `GenerateParityOracleTests.generateSelfBaseline` — the oracle's own computation (`computeOracle`, shared with
  `generateParityOracle`), written in the shared baseline format; on a device it reads the bundle's copy of the
  oracle (a device cannot reach the Mac's source tree).
- `Tooling/mint-baseline.py --simulator <name>` / `--device <name or UDID>` — first mint against the oracle's
  `bootstrapTolerances`, a re-mint's diff and confirmation, `--check`; a device's file copied off with
  `xcrun devicectl`.
- `FilePlaybackRegressionTests` and `GatedFFTParityTests` — against the configuration's reference at
  `selfTolerances`, and, off macOS, against the oracle at `tolerances`.
- `GuitarTapTests/self-baseline-ios-simulator-arm64.json` (minted on the iPad Air simulator) and
  `self-baseline-ios-arm64.json` (minted on the iPad M5: every value identical to the oracle).
- `Tooling/test.sh --simulator <name>`; CI's new `unit-ios` job runs the unit plan on the iPad Air and iPhone 17
  simulators. A physical device is checked by hand before a release (`process/RELEASE-CHECKLIST.md`, 1a).
- Hub: `parity-report.py` expects `swift` on `darwin`, `ios` and `ios-simulator`; `platforms.py` scans Swift's
  Python tooling (the mint tool joins `tooling/mint-baseline`); the two baselines collected into
  `tooling/parity/baselines/`.

**Verified** (2026-10-19): Swift's full unit suite passes on macOS (283), the iPad Air and iPhone 17 simulators
(248 each), and the physical iPad M5 and iPhone 17 Pro Max (248 each); the iPhone simulator, checked with
`mint-baseline.py --check`, is identical to the simulator baseline; nudging REG-G2's air frequency by 1e-4 Hz in
an iOS baseline fails the iPhone's regression test on that value.

**`parity-report.py`, nine configurations:** device iOS against macOS — 0 in every value; the simulator against
macOS or a device — 1e-5 Hz (REG-G2 air), 2e-6 dB (GFFT3); the worst cross-edition distances are unchanged
(2.04e-5 Hz, 1.16e-5 dB, Swift against Python and the web), so item 5 starts from those.

#### Item 5 — decided (owner, 2026-10-19)

Measured on all nine configurations (item 4's report): the worst distances are unchanged by iOS — 2.04e-5 Hz,
1.16e-5 dB, 4.17e-6 dB (gated FFT), 6.67e-7 (q), 1.51e-9 s (ring-out), every one Swift against Python and the web.
The bars, at about ten times the worst (owner: "they look good"):

| Value | Worst | Was | Now | Headroom |
|---|---|---|---|---|
| frequency (`freqHz`) | 2.04e-5 Hz | 0.02 | **2e-4** | 10× |
| magnitude (`magDb`) | 1.16e-5 dB | 0.01 | **1e-4** | 9× |
| gated FFT (`gatedFftDb`) | 4.17e-6 dB | 1e-3 | **5e-5** | 12× |
| q | 6.67e-7 | 1e-5 | **1e-5** (unchanged) | 15× |
| ring-out (`ringOutSec`) | 1.51e-9 s | 1e-7 | **2e-8** | 13× |

Frequency is twice magnitude because a dB difference becomes about 1.8 times as many Hz through the peak fit
(2.455 bins/dB × 0.7324 Hz/bin) — the oracle's provenance note. The first-mint bar (`bootstrapTolerances`, 1 Hz /
1 dB) is unchanged, so a new edition's first baseline is not held to these.

**Done** (Swift `10aa335`, Python `42a010d`, web `2dcac47`): the bars and the oracle's two notes (`_selfToleranceNote`, `_toleranceProvenanceNote`)
rewritten to today's measurement in Swift's oracle, published to the hub and synced to Python and the web (the
values and `oracleVersion` unchanged, so no baseline needs re-minting); the old figures in the first-mint note and
in Python's and the web's mint tools updated.

**Verified at the new bars** (2026-10-19): Python 1469 passed, 1 skipped; web 1352 passed, 1 skipped; Swift on
macOS 283, on the iPad Air and iPhone 17 simulators 248 each, on the physical iPad M5 and iPhone 17 Pro Max 248
each. `parity-report.py`: 10× headroom on frequency, 9× magnitude, 12× gated FFT, 15× q. CI's new `unit-ios` jobs
(Swift `a104591`) pass on the iPad Air and iPhone 17 simulators.

**To do:** the Windows and Linux sessions run item 1's four steps again against the new oracle — `guitar_tap` at
`42a010d` or later, `GuitarTapWeb` at `2dcac47` or later — and report here, under this item.

*Windows:* **all four steps pass at the new bars** (2026-10-19), on the same machine as item 1 (Dell G16 7620,
`Windows-11-10.0.26300`, i7-12700H; Python 3.14.8 / NumPy 2.5.4; Node 26.11.1 / V8 `14.6.202.34-node.37`).
Commits run: `guitar_tap` `42a010d`, `GuitarTapWeb` `2dcac47`, hub `c405c75` — each pulled to `origin/main`; the
web's `package-lock.json` and `.nvmrc` unchanged since item 1, so no reinstall.

| Step | Result |
|---|---|
| 2. `.venv/Scripts/python -m pytest` | **1469 passed, 1 skipped** (6:48). `test_self_regression` (both tests) and `test_oracle_sync` **passed, not skipped** |
| 3. `npm run test` | **68 files, 1352 passed, 1 skipped** (4:10); `oracle-sync`, `self-regression` and `file-playback` included |
| 4. `Tooling/run-export-check.sh` | **20 exports checked, 0 failing** |
| 4. `npm run test:exports` | **10 Playwright exports passed, then 20 exports checked, 0 failing** |

The one skip is item 1's, in both editions: `the capture probe is switched off`.

*Linux:* **all four steps pass at the new bars** (2026-10-19), on the same machine as item 1 — a VMware guest on
the Windows machine above, `Linux-7.0.0-38-generic`, glibc 2.39, i7-12700H; Python 3.14.8 / NumPy 2.5.4;
Node 26.11.1 / V8 `14.6.202.34-node.37` (the pinned `.nvmrc` version).
Commits run: `guitar_tap` `42a010d`, `GuitarTapWeb` `2dcac47`, hub `c405c75` — each at `origin/main`; the web's
`package-lock.json` unchanged since item 1 (only the oracle and the mint tool moved), so no reinstall.

All three vendored oracles — hub, Python and web — carry the new bars byte-identically (`freqHz` 2e-4, `magDb`
1e-4, `gatedFftDb` 5e-5, `q` 1e-5, `ringOutSec` 2e-8) at `oracleVersion` `777a951`, so the sync landed and, as
expected, nothing needed re-minting.

| Step | Result |
|---|---|
| 2. `.venv/bin/python -m pytest` | **1469 passed, 1 skipped** (6:29). `test_self_regression` (both tests) and `test_oracle_sync` **passed, not skipped** — re-run on their own to record them |
| 3. `npm run test` | **68 files, 1352 passed, 1 skipped** (2:53); `oracle-sync`, `self-regression` and `file-playback` included |
| 4. `Tooling/run-export-check.sh` | **20 exports checked, 0 failing** |
| 4. `npm run test:exports` | **20 exports checked, 0 failing** |

The one skip is item 1's, in both editions: `the capture probe is switched off`. Counts identical to item 1's
run at the old bars.

What this adds over item 1: that run cleared the old bar with roughly 1000× to spare, so it said little about
the bar itself. These bars sit about 10× above the worst measured distance, and both tracking editions still
pass them unchanged on a third operating system — on hardware that minted no baseline (Python's came from an
Azure-kernel runner, the web's from an AMD EPYC 7763). Worth noting the limit of that, though: this VM runs on
the very machine the Windows rows above were measured on, so the Windows and Linux results share a CPU and are
not independent hardware evidence of each other — what they isolate is the operating system and toolchain.

