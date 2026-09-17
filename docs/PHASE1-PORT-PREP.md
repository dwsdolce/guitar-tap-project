# Phase 1 — Contract Refresh and Tooling Generalisation

The record of [ANDROID-PLAN.md](ANDROID-PLAN.md) Phase 1: what was audited, what was found, and
what changed. Phase 1 is deliberately mostly **not** Android work — it refreshes the shared
contract and removes the hard-coded "three editions" assumption, and most of it pays off for
Swift, Python and web whether or not the Android port proceeds.

> **Status:** done 2026-09-16, awaiting review. Nothing here is committed by the tooling that
> produced it; the changes sit in the working trees for evaluation across the ports.

---

## 1. INVENTORY audit — what had drifted

[INVENTORY.md](INVENTORY.md) is the spec extracted from canonical Swift in June 2026 and the
contract each port is measured against. It was audited value by value against current Swift.

**The numeric core was intact.** FFT sizes and hop, the rectangular and Hann windows, the
detection constants (−40 dBFS, 2-chunk confirmation, 3 dB hysteresis, α = 0.05, 10 dB headroom,
0.5 s warm-up and cooldown), onset alignment (2048-sample noise estimate, ×10 or 0.001, back
32 samples, window starting 100 ms early), pre-roll and capture durations, the gated FFT cap and
floors, the peak window and proximity, the analysis range, mode-band values for classical,
acoustic and generic, the pitch reference, the plate and brace formulas and Gore's coefficients,
power-domain averaging, clipping hold — all still match.

**Four real drifts, all corrected:**

| Drift | INVENTORY said | Swift does | Why it matters |
|---|---|---|---|
| **Flamenco mode bands** | Top 190–250, Back 180–240 | Top **180–220**, Back **200–250** | The old table put Back *below* Top, which `classifyAll` treats as impossible (Back is constrained above the claimed Top). A port trusting it would assign flamenco modes differently — a categorical parity failure. |
| **Peak-picking algorithm** | Two passes over the mode bands, one slot per mode | **One mode-blind sweep**; classification happens later in `classifyAll` | The old algorithm is what minted a duplicate peak on every guitar capture (`completed/PEAK-FINDING-DUPLICATE-PEAKS.md`). Documenting it invited a new port to reproduce a fixed bug. |
| **Peak Min semantics** | A detection threshold | A **display projection** over a full set detected down to −100 dB (`allPeaks` + `peaksAbovePeakMin`) | Without this, a port cannot reproduce "lower the slider on a loaded measurement and a faint Air appears", and peak identity, selection and annotations would not survive slider moves. |
| **`.guitartap` keys** | list omitted two | `sampleRate`, `userModifiedSelection` | Omitting them loses the capture-conditions warning on load, and re-selects peaks the user chose by hand. |

**Every line-number citation had rotted** — off by 60 to 300 lines, roughly 120 of them, while
the values they pointed at were still correct. They are now **file paths and symbol names only**.
A stale line number is worse than none: it sends a reader to the wrong place and undermines
trust in the document. The parity map gives the counterpart file in each edition.

**Nine behaviours existed in Swift and had never been written down** — now a section of their
own in INVENTORY: ring-out/decay tracking on the audio clock, the tap-tone ratio, material
multi-tap averaging per phase, per-field numeric precision, the two-store material dimensions
model, the dead-input watchdog, status messages derived from state with a silent warm-up, the
noise-floor EMA deliberately running *during* the warm-up, and the load-time capture-conditions
warning. Several of these have already caused bugs in at least one edition; each now points at
the hub spec that settled it.

**One thing to fix in Swift, not here:** the doc comment above the per-phase peak windows in
`TapToneAnalyzer+SpectrumCapture.swift` states 50–500 / 20–250 / 20–200 Hz, while the code uses
20–100 / 40–220 / 15–100 (brace 100–1200). The code is right and INVENTORY matches the code; the
Swift comment is stale and should be corrected in that repo.

## 2. Parity tooling — from three hard-coded editions to a list

The platform list used to be written out separately in four tools, along with a literal
`len(pres) == 3`. Adding an edition meant finding all of them.

**New: `tooling/parity/platforms.py`** — one table declaring each edition's key, label, repo
directory, environment-variable override, source extensions, documentation style, capture-matrix
token and fixture directory.

The distinction that makes this safe is **declared vs active**: an edition is declared as soon
as it is planned, but only *active* once its repo exists and at least one file in it carries an
`@parity` tag. Tools render columns for active editions only. Android is declared today and has
no tags, so **the generated map and index are byte-identical** — `--check` passes — and its
column will appear by itself the moment the first tagged Kotlin file lands.

| Tool | Change |
|---|---|
| `gen_parity_map.py` | Reads the table; per-edition extensions; dynamic columns; "proven on all editions" replaces `len(pres) == 3` |
| `parity_lookup.py` | Reads the table; skips editions absent from an older index |
| `doc_coverage.py` | Reads the table; **new KDoc analyzer** for Kotlin; dynamic columns |
| `guitartap_matrix.py` | `android` platform token; `tablet` and `phone` devices; `snowball` mic |

**Two bugs fixed while in there**, both Windows-only and both pre-existing:

- `doc_coverage.py` crashed with `UnicodeEncodeError` whenever a slug was flagged, because the
  `◄ GAP` marker is not encodable in the console's cp1252. It had therefore **never completed a
  full run on this machine**. Output is now UTF-8 with replacement.
- `guitartap_matrix.py` wrote an absolute local path into the committed matrix, and wrote CRLF.
  It now writes a hub-relative path and LF. (The committed matrix said
  `GuitarTap/Tests/AllPlatforms`, a location the corpus left when the hub was created.)

**First full doc-coverage run:** 87 slugs, 57 flagged. That is pre-existing state, not a
regression, and it is the first time the number has been visible here. Worth triaging separately
— many will be view slugs where one edition documents a helper the others leave bare.

## 3. Fixture drift — a gap that had already bitten

Each edition keeps its own copy of the shared fixtures, and nothing kept them in step. The
`test/peaks` suites assert in three repos that the files are identical **without ever checking
it**, and they had in fact diverged: `7108913.txt` was CRLF in Swift and Python and LF in the
web repo until the line-ending work of 2026-09-15.

**New: `tooling/check-fixtures.py`** — compares every fixture appearing in more than one edition
by SHA-256 and reports drift. Read-only by default; `--adopt <edition> <file>` copies one
edition's copy over the others, which is the only sanctioned way to sync one.

Current state: **14 shared fixtures, all byte-identical.** Fixture directories are declared per
edition in `platforms.py`, with Android's slot already pointing at
`core/src/test/resources`.

## 4. New document: Android UI guidelines

[ANDROID-UI-GUIDELINES.md](ANDROID-UI-GUIDELINES.md) — the counterpart of the web guidelines:
tablet-first priority, layout selection mirroring Swift's predicate order, results inline on a
tablet versus a sheet on a phone, the zone-dependent chart gestures, annotation drag and reset,
the visible ⋯ affordance, the deliberate friction on load and delete, 48 dp targets, and the
theme rules. Plus a substitution table for the platform pieces (SAF, share sheet, no menu bar)
and an explicit "not ported" list.

## 5. Still open from the Phase 1 plan

- **Process docs** — `BUG-TRACKING.md` platform labels, `DEV-DOC-STANDARD.md` KDoc rules, the
  hub `README.md` repo table: updated in this pass, worth reading in the diff.
- **A shared fixture *source*.** `check-fixtures.py` detects drift but the fixtures still live
  as per-repo copies. Making one location canonical (and having the others sync from it) is a
  bigger change, and is only worth doing if the Android port proceeds.
- **The parity rule for a partial edition.** "Proven on all active editions" is implemented,
  which is right while Android has no tags. Once Android has *some* tags, every group missing an
  Android file counts as not-proven and the number drops sharply. Decide then whether the bar is
  "all active editions" or "canonical plus N".
