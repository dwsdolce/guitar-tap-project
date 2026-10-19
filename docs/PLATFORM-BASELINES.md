# Platform baselines — Windows and Linux checked on real machines, iPad and iPhone minted, the tolerance set

**Issue:** [#16](https://github.com/dwsdolce/guitar-tap-project/issues/16)

Status: **OPEN — items 1–3 to run; items 4–5 planned after item 3.** Detail doc written 2026-10-19 (the Issue
was opened before detail docs were the rule).

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
| 1 | Windows and Linux: the full suites run on the real Windows machine and the Linux VM, against the CI-minted baselines | open — the Windows and Linux sessions |
| 2 | macOS: the full suites of Swift, Python and the web | open — on the owner's go |
| 3 | iPad and iPhone simulators: Swift's full suite; record what differs from the macOS oracle | open — on the owner's go |
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

*Windows:* not yet run.
*Linux:* not yet run.
