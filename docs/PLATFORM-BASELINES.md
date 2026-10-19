# Platform baselines — Windows and Linux checked on real machines, iPad and iPhone minted, the tolerance set

**Issue:** [#16](https://github.com/dwsdolce/guitar-tap-project/issues/16)

Status: **OPEN — items 1–3 done (Windows and Linux confirmed on the real machines; macOS green; iOS run,
three failures, item 3); item 4 next, then item 5.** Detail doc written 2026-10-19 (the Issue was opened before
detail docs were the rule).

## What the baselines are

Each configuration (an edition on one operating system and architecture) checks two things on every full run
(`tooling/parity/README.md` has the rules):

- **Regression** — the configuration against **its own** minted baseline, at `selfTolerances` (1e-12). Nothing
  legitimately moves it; a difference is a change to the analysis.
- **Parity** — the edition against the **oracle** (Swift on macOS, `tooling/parity/parity-oracle.json`), at
  `tolerances`: 0.02 Hz / 0.01 dB.

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
| 4 | iPad and iPhone baselines: Swift mints its own configuration's baseline on iOS, its regression check reads it there, `collect-baselines.py` gathers it and `parity-report.py` reports it | to plan after item 3 |
| 5 | The tolerance re-measured with every configuration (`tooling/parity-report.py`) and decided | after item 4 |

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

