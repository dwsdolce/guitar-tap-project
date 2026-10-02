# Test Coverage — cross-platform (Swift · Python · Web)

**The living reference for how test coverage is tracked and verified across the three GuitarTap codebases.**
It answers: *what is covered, on which platforms, and how do I check?*

This doc lives in the **project hub** (`guitar-tap-project`) — with the coverage database it describes
(`parity/PARITY-MAP.md`) and the tools you run to update it (`parity/`). The whole parity system sits in one
neutral place, not inside any one edition's repo.

The three code repos are siblings of the hub: **`GuitarTap`** (Swift, **canonical**) · **`guitar_tap`**
(Python) · **`GuitarTapWeb`** (Web).

---

## Layout — where everything lives & why

Anchored on **where the databases are stored and where the tools run**, not on where any project's docs live:

| Piece | Home | Why |
|---|---|---|
| `parity/gen_parity_map.py`, `parity_lookup.py`, `README.md` | **hub** `tooling/` | the cross-repo dev tools; run from the hub, which scans the three sibling code repos on disk |
| `parity/PARITY-MAP.md`, `parity/parity-index.json` | **hub** `tooling/` | the generated coverage database (the tools' output) |
| `TEST-COVERAGE.md` *(this file)* | **hub** `tooling/` | the coverage reference — co-located with the database + tools it documents |
| `parity/parity-oracle.json` | **hub** `tooling/` (canonical) | the shared numeric-golden contract — **all three suites read it** (REG-G1/G2/B1/P1/P2 peaks, the REG-G2 per-tap table, the REG-G1 ring-out, GFFT1–5). Each consumer keeps a committed local copy so tests run offline, named in its own `tooling/oracle-dest.txt`; `sync-oracle.sh` (canonical copy in hub `tooling/`) pulls this file and `--check` fails on drift. |
| project/planning docs (STATUS, phase logs) | **hub** `docs/` | the neutral home for project docs (formerly in `GuitarTapWeb/Development/`) |

---

## The rule

**Change shared behavior → change it in all three.** Swift is canonical; design the change there (or against
it), then mirror to Python, then to the web — and update the tests on every platform that has them, in the same
body of work. A behavioral change that lands on only one or two platforms is a divergence, not a feature.

The corollary for tests: a `test/<slug>` group should exist on **all** platforms that implement the behavior,
and every **testable** implementation should be linked to the test that proves it. The two tools below make both
machine-checkable.

---

## How coverage is tracked: the `@parity` system

Every mirrored source or test file carries one `@parity <slug>` comment — a stable, area-namespaced kebab slug
that is the **join key** across repos (files sharing a slug are the same logical unit). Full tag reference +
rationale: **`tooling/parity/README.md`**.

- **Impl groups** — `dsp/…`, `audio/…`, `state/…`, `model/…`, `view/…` — the implementation units.
- **Test groups** — `test/…` — a test suite. The slug is the same on each platform (e.g. `test/gated-fft` =
  Swift `GatedFFTParityTests.swift` + Python `test_gated_fft_parity.py` + web `gated-fft.test.ts`).
- **Evidence link** — an impl tag may name the test(s) that prove it:
  `// @parity dsp/find-peaks tests=test/peaks`. The generator unions `tests=` across platforms, so the link is
  normally placed on the **canonical Swift** anchor.
- **`@parity none`** — a file with no cross-platform counterpart *by design* (a platform-specific mechanism,
  e.g. SwiftUI gesture math or Qt `QTimer` slots). Acknowledged in the map's *Platform-specific* section, not
  treated as a gap.

### The map + the equivalence levels

The generated table is **`PARITY-MAP.md`** (+ `parity-index.json`, the DB the lookup tool reads). Its
**Equivalence** column is the honest answer to "are the contents *actually* equivalent, or just co-located?",
derived from each impl group's `tests=` link:

| Equivalence | Meaning |
|---|---|
| **oracle + tests** | numerically pinned by the shared oracle (a `g#` web test) **and** covered by paired Swift+Python behavioural tests |
| **oracle** / **tests** | one of the above |
| **test suite** | the row *is* a test group |
| **review only** | no `tests=` link — location asserted, equivalence rests on *change-all-three* + code review. For a **testable** area (dsp/audio/state/model) this is a **coverage gap**; for `view/*` (UI) it is expected. |

---

## Running the tools

All commands run from **the hub**; the generator auto-discovers the sibling code repos (override with
`PARITY_SWIFT` / `PARITY_PYTHON` / `PARITY_WEB`).

```
python3 tooling/parity/gen_parity_map.py            # regenerate PARITY-MAP.md + parity-index.json + this doc's coverage block
python3 tooling/parity/gen_parity_map.py --check    # gate: all three current + no orphan/malformed slugs (exit 1 on fail)
python3 tooling/parity/gen_parity_map.py --coverage # print the functional-block coverage report (read-only)
python3 tooling/parity/gen_parity_map.py --gaps     # report testable impl groups with NO test evidence
python3 tooling/parity/parity_lookup.py <slug>      # show a group's counterparts across repos
```

**The functional-block coverage report** (`--coverage`) answers "what fraction of the testable functional blocks
have a test proving them, on each platform?" — the metric that matters here (not line/statement coverage). It
counts blocks, not lines: *covered* (has any `tests=` link), *proven on all three* (≥1 linked `test/*` group
present in every repo — the strict bar), and *gaps* (no test anywhere), with a per-area breakdown. The identical
numbers are baked into the **Current coverage state** block below by `generate`; `--check` fails if they drift, so
the doc can't go stale.

**The two coverage gates** — run both before committing a change to shared behavior:

- **`--check` = *missing on some*.** Fails if `PARITY-MAP.md`/`parity-index.json` drift from source, or a slug
  lands in only one repo (an **orphan** — a typo, a test that needs back-porting, or something that should be
  `@parity none`).
- **`--gaps` = *missing on all*.** Lists testable impl groups with no `tests=` evidence — behaviour verified by
  code review alone. Each is a back-fill candidate or a documented, justified gap.

> **CI status:** no CI pipeline is wired in any repo yet. Until there is, these are **local/pre-commit** gates —
> run them by hand when you touch a mirrored file or a test. When CI is added, `--check` should be a hard gate
> (exit code) and `--gaps` a reported metric.

### The oracle (shared golden numbers)

Numeric parity (FFT magnitudes, REG-* peak freq/mag/Q) is pinned by a **shared oracle** — one canonical
file of expected values + tolerances that every suite tests against, so the goldens cannot fragment into
per-platform copies. It lives in the hub: `tooling/parity/parity-oracle.json`.

**Mint once, pull everywhere.** Swift mints it, because Swift is canonical: `GenerateParityOracle` runs the
same pipeline the regression tests assert against and writes the numbers back, so the oracle cannot disagree
with Swift. A tracking edition minting it would make the file record what the *tracking* edition does, and
the day the two disagreed there would be no way to say which was wrong. Only the minting step is macOS-bound;
vendoring, drift-checking and consuming all run anywhere.

| Step | Where | Command |
|---|---|---|
| Mint (rare — only on an intentional algorithm change) | Swift / macOS | `GENERATE_PARITY_ORACLE=1 xcodebuild test -only-testing:GuitarTapTests/GenerateParityOracle` |
| Publish to the hub | Swift repo | `ORACLE_SRC=<hub> ./tooling/sync-oracle.sh --publish`, then commit the hub |
| Vendor into a consumer | any repo, any OS | `ORACLE_SRC=<hub> ./tooling/sync-oracle.sh` (or `ORACLE_URL=` once the hub is public — #11) |
| Drift gate | any repo, any OS | `./tooling/sync-oracle.sh --check` |

`sync-oracle.sh` is one file copied verbatim into each repo; the repo's own vendored path lives beside it in
`tooling/oracle-dest.txt`, so the script carries no per-repo knowledge. The vendored copies are
`GuitarTapTests/parity-oracle.json` (Swift), `tests/parity-oracle.json` (Python) and
`test/fixtures/parity-oracle.json` (web).

The generator **recomputes values in place** rather than writing a fresh document: it reads the committed
JSON, replaces only the numeric leaves and writes it back. That preserves the prose (`_note`,
`_perTapNote`, `_ringOutNote`) — which is where the reasons behind odd-looking numbers live, such as why
REG-G2 taps 1 and 7 pin Back at 296.5 Hz — and makes the diff after a regeneration exactly the set of values
the algorithm moved.

⚠️ **Not yet exercised:** the generator has never been run, and the Swift suite's conversion to reading the
oracle has not been compiled (it was written on Windows). The Python and web suites were converted and run
green. First macOS run should be: normal suite first (proves the conversion), then the generator, then
compare its output against the committed file — the values should not move.

---

## Current coverage state

The block below is **generated from the `@parity`/`tests=` tags** — regenerate it with
`python3 tooling/parity/gen_parity_map.py` (view it on demand, without writing, via `--coverage`;
`--check` fails if it has drifted from the tags). Do not hand-edit between the markers.

<!-- COVERAGE:BEGIN — generated by tooling/parity/gen_parity_map.py; do not hand-edit -->

**Headline** — 116 parity groups · 25 platform-specific (`@parity none`) · 0 orphan slugs.

**Functional-block test coverage** — the unit is a functional block (impl group), not a line. Denominator = the **testable** blocks (`dsp` / `audio` / `state` / `model`); `view/*` is UI, review-only by design, and excluded.

| Measure | Blocks | % |
|---|---|---|
| Covered by a test group | 30 / 30 | 100% |
| Proven on all three platforms | 29 / 30 | 97% |
| Gaps (no test anywhere) | 0 / 30 | 0% |

By area: `audio` 2/2 · `dsp` 14/14 · `model` 9/9 · `state` 5/5.

**Covered, but test not yet 3-way** — passes `--check` (a 2-way slug is not a one-repo orphan) but fails the *proven-on-all-three* bar:
- `model/wav-dump-folder` — `test/wav-dump-folder` on swift, python (no web)

<!-- COVERAGE:END -->

**Notes on the two gaps** (hand-maintained context): `dsp/analysis-quality` is the decay/tap-ratio
quality-label thresholds+colours — tested only by the web's untagged `analysis-quality.test.ts`, no Swift/Python
twin (back-port candidate). `model/mode-colors` is the guitar-mode → colour mapping, untested everywhere; low-risk.

**Platform-specific (`@parity none`):** Swift `SpectrumViewGestureTests` (SwiftUI zoom/pan gesture math) ·
Python `test_wi10_qtimer_slots` (Qt `QTimer.singleShot` mechanics).

**Known reverse-gaps** (web-only tests with no Swift/Python twin, deliberately left untagged so `--check`
stays at 0 orphans; a future back-port makes them 3-way): web `g0-wav`, `g3a-calibration`, `analysis-quality`,
`calibration-store`; Python-only `test_wi1/wi2/wi6` (settings persistence + effective-peak-id). Their impl
coverage is *transitive* via `test/file-playback` (which decodes real WAVs with calibration) — except
analysis-quality, the one real gap above.

### Notable folding decisions (documented, consistent)

- `dsp/spectrum-average` folds into `test/peaks` (Swift `PeakFindingTests` tests averaging alongside find-peaks;
  the web folded its spectrum-average suite into peaks).
- Plate/brace material properties are a **2-file split** on all three (Swift `Plate`/`BracePropertiesTests`;
  Python `test_plate`/`test_brace`; web `plate`/`brace`).
- `dsp/fft` + `dsp/guitar-fft` + `dsp/wav` share one Swift anchor (`RealtimeFFTAnalyzer+FFTProcessing.swift`) —
  that file *is* the FFT/WAV layer; `computeGatedFFT` lives there too, so `test/gated-fft` is valid evidence for
  `dsp/fft`.

---

## See also

- **`tooling/parity/README.md`** — the tag format + full command reference.
- **`PARITY-MAP.md`** — the generated matrix (Ctrl-F any path to find its counterparts).
- **`../docs/completed/6-TEST-NORMALIZATION.md`** — the project *history* of how the suites were normalized
  to this state (phases 1–6). Transient — will be archived.