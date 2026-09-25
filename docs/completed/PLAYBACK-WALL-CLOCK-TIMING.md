# File-playback results depend on machine speed

**Issue:** [#19](https://github.com/dwsdolce/guitar-tap-project/issues/19)

**Status:** ✅ COMPLETE — issue closed 2026-09-25. Committed: Swift `58796ac`, Python `820fabd` (with F49's baseline
re-mint), web `c4fb2f3`. Implemented in all three editions and verified repeatable; owner's run-review
PASSED in all three; the Chrome hidden-tab check PASSED on the current bundle. The web's "Tap 8/8" status
was a stale cached bundle, not #19 (below). No open questions remain. Found 2026-09-23 during #17 (S6, finding F44).

## The symptom

Python's `tests/test_self_regression.py` (zero tolerance against this machine's own baseline) fails
under pytest, but the same pipeline run as a standalone script passes against the same baseline, on
the same machine and tree. The number of moved values is **not stable**: pytest reported 19 of 94,
then 21 of 94, on the same code.

What moves (21-of-94 run, GFFT4 aside — that one is F44's deliberate −∞):

- REG-G2 **taps 7 and 8 only** — the last two of eight. Taps 1–6 are bit-identical to the baseline.
  Largest: tap 7 air +0.041 Hz / −0.457 dB; tap 8 air +0.033 Hz / −0.350 dB.
- REG-G2 averaged peaks — only because taps 7 and 8 feed the average.
- REG-P2 `flc/frequency` +0.051 Hz — FLC is the **last** phase of the plate sequence. One further
  value was past pytest's display limit and was not seen.

A DSP change would move every tap. This moves the end of a sequence, by a varying amount: a timing
signature.

## The mechanism

Two clocks run during file playback, and the tap lifecycle straddles them.

1. **Audio advances at "real time + processing time."** Playback processes a chunk and then sleeps one
   chunk's duration:
   - Python `process_file_data` —
     [`realtime_fft_analyzer_engine_control.py`](../../../guitar_tap/src/guitar_tap/models/realtime_fft_analyzer_engine_control.py)
     (`process_raw_samples(chunk)` then `time.sleep(chunk_duration)` then pump the Qt loop).
   - Swift `processFileData` —
     [`RealtimeFFTAnalyzer+EngineControl.swift`](../../../GuitarTap/GuitarTap/Models/RealtimeFFTAnalyzer+EngineControl.swift)
     (`processRawSamples(chunk)` then `Thread.sleep(forTimeInterval: chunkDuration)` on a background
     queue).
2. **The tap lifecycle is timed on the wall clock.** Cooldown / re-enable, capture window, safety
   timeout and the FLC cooldown are scheduled as delays:
   - Python `_main_async_after` → `QTimer.singleShot` (`tap_tone_analyzer_spectrum_capture.py`,
     `tap_tone_analyzer_tap_detection.py`, `tap_tone_analyzer_control.py`).
   - Swift `DispatchQueue.main.asyncAfter`.

So when a timer fires, how much audio has passed depends on how long each chunk took to process. A
timer landing one chunk earlier or later moves where detection re-arms and which samples a capture
takes in. The error accumulates along the sequence, which is why the last taps move first.

**Web** is partly different: detection and warm-up are timed on `audioTime`, and the parity runner
plays **unpaced** (`pace: false`) yet reproduces its baseline, so the paths the oracle exercises are
audio-clocked. It still has one wall-clock timer — the FLC cooldown `setTimeout` in
[`tapToneAnalyzer.ts`](../../../GuitarTapWeb/src/state/tapToneAnalyzer.ts). The rest is not audited.

## The evidence

REG-G2 alone, fresh settings sandbox, artificial work added after each chunk in a scratch wrapper (no
edition code touched), compared to the baseline:

| added work per chunk | REG-G2 values moved |
|---|---|
| 0 ms | 0 / 54 |
| 5 ms | 0 / 54 |
| 15 ms | **54 / 54 — all 8 taps** |

The pytest run took 385 s against ≈ 4 min standalone; it sat just past the threshold, so only the
tail moved.

## Explanations ruled out — do not re-investigate

| hypothesis | how it was killed |
|---|---|
| F44's epsilon-clamp removal | A/B of none / live / gated / both clamps gives identical REG-G2 peaks; with the clamp removed only GFFT4 moves, in both environments |
| Machine load (as distinct from speed) | failed on an idle machine; the variable is processing time per chunk, which load is one cause of |
| The user's real settings vs the test sandbox | every settings read during REG-G2 logged and diffed; each differing key seeded into a sandbox one at a time and all together — 0 moved |
| Ordering leak between cases (in memory or on disk) | full `compute_all()` — all six cases in sequence — in a fresh sandbox outside pytest moves only GFFT4 |
| pytest configuration | no plugins beyond `pytest-cov`, no `addopts`, no warning filters |

A side lesson: a scratch script named `bisect.py` in `/tmp` shadowed the standard library module and
invalidated one round of results. Scratch scripts go in the session scratchpad with prefixed names.

## History — why it never failed before

| date | event |
|---|---|
| 2026-04-15 / 05-04 | Python wall-clock capture-window timer (`be0a456`, `69ed447`) |
| 2026-04-23 | Python real-time pacing sleep (`1709ce6`, `5252220`) |
| 2026-05-06 / 05-11 | Swift `Thread.sleep(chunkDuration)` pacing (`434315b`, `a17da56`) |
| 2026-06-17 → 07-31 | released in 1.0, 1.0.1, 1.0.2 |
| 2026-09-18 | parity bar tightened from **1 Hz / 1 dB** to 0.02 Hz / 0.01 dB (hub `60be927`); zero-tolerance self-baseline introduced (Python `73dee74`), both #10 |

Every observed move is far inside 1 Hz / 1 dB, so the old bar could not see it. The tightening exposed
an old defect; it did not introduce one. The tightened **parity** bar (0.01 dB) is also far below these
moves: Python's parity tests have passed only because they ran at a speed where the timers lined up.

## Open questions

None. Questions 1–5 were answered by the fix, and 6 by checking how tests are isolated (below).

### 6. Tests define their full context — answered, no action (owner, 2026-09-25)

Asked 2026-09-23: every test must set its measurement type itself — including which of the four guitar
types — never inherit it from a settings file or the environment. Python's runner passes the type by
writing the global settings store, which production then reads back. The owner's core question: **how is
one test's environment, including that store, isolated from another's?** Checked in all three:

- **Between test runs (processes): isolated in all three.**
  - Swift: under XCTest, `TapDisplaySettings` uses a per-process UserDefaults suite,
    `com.guitartap.tests.<pid>`, wiped on first access; stale suites of dead runs are reaped
    (`TestSandbox.swift`).
  - Python: `conftest.py` sets `GT_TEST_SANDBOX=<pid>` before anything reads settings; QSettings then
    uses `Dolcesfogato.tests.<pid>`, cleared at session start, dead runs' files reaped
    (`settings_scope.py`) — the fix for the 2026-09-20 cross-run wipe.
  - Web: no persistent store under test. The analyzer's settings are an object on the instance
    (`settings = DEFAULT_SETTINGS`), and tests pass settings objects in. The node test environment has
    no `localStorage`; the one test that needs it installs an in-memory mock. Vitest also gives each test
    file fresh modules.
  - Parallel execution would not break this: Xcode's parallel clones and pytest-xdist workers are
    separate processes, so each gets its own store. Today both natives run serially (Swift's
    `guitar_tap.xctestplan`: `parallelizable: false`; Python: no xdist).
- **Between tests within one run:** Swift and Python share the process's store, serially, with no reset
  between tests — isolation rests on each test setting the context it reads, which is the rule itself;
  `play_file_for_testing` sets the measurement type on every call. The web is isolated by construction
  (each test builds its own analyzer with its own settings).
- **Remaining gaps, already listed under "Noticed while doing #19" and due in S7's slugs:** Python's
  minter run standalone (outside pytest, without `GT_TEST_SANDBOX`) uses the real settings; and timers
  from one playback case fire during the next (not the settings store; no result changed).

### Answered by the fix (2026-09-25)

Questions 1–5, as first asked (2026-09-23), and what settled each:

1. **Magnitude** — how large the moves get on a slower machine. **Superseded, not measured:** the fix
   removed the dependence on machine speed, so there is no longer a move to size. Python with 15 ms of
   added work per chunk now gives the same 146 values as a normal-speed run (0 differ; before the fix,
   65 did) — see "Reliability check … REPEATABLE" below.
2. **A reliable test case.** **Answered:** repeatability is shown by that comparison (two normal-speed
   runs: 0 of 146 differ; normal vs +15 ms/chunk: 0), and the audio clock is pinned in all three by
   `test/audio-clock-timers` — each case advances only audio, so a delay moved back to the wall clock
   would not fire and the case fails.
3. **Swift** — same structure, not shown to move. **Settled by the fix, not measured before it:** Swift
   received the same audio-clock timers and the same playback hold (App Nap), and its
   `AudioClockTimerTests` pin them.
4. **The live app** — the same wall-clock timers ran live. **Answered:** the timers are the same code
   live and in playback, so live capture now runs on the audio clock too. The one wall-clock timer left,
   T6, measures silence: it fires only when no audio arrives, which is its purpose.
5. **Fix direction.** **Done as proposed:** the tap-lifecycle timers run on audio time in all three
   editions, Swift first — see "Design (approved by the owner, 2026-09-24)" and "Implementation".

## Inventory — every tap-lifecycle timer, all three editions (read 2026-09-24)

Only timers that decide **which audio** a tap sequence detects or captures, or when it completes.
Excluded: device-change settle (3 s), engine start/watchdog, file pacing itself, and timestamps
(`captureTime: Date()`) that are recorded but decide nothing.

| # | what it does | Swift | Python | web |
|---|---|---|---|---|
| T1 | guitar: rest after a tap, then re-arm (`tapCooldown` 0.5 s) | `scheduleGuitarReEnable` — `asyncAfter` (SpectrumCapture:617) | `_do_reenable_guitar` — `_main_async_after` (spectrum_capture:778, 907) | `scheduleGuitarReEnable` — `setTimeout(TAP_COOLDOWN_MS)` (tapToneAnalyzer:1960) |
| T2 | plate/brace: rest between taps of one phase, then re-arm (0.5 s) | `reEnableDetectionForNextPlateTap` — `asyncAfter` (TapDetection:424); does **not** restart warm-up | `_do_reenable_detection` — `_main_async_after` (tap_detection:485) | **no rest**: `armMaterialDetection` at once, which restarts the **warm-up** (0.5 s of **audio** time) |
| T3 | FLC: hold after C is accepted, then arm FLC (0.5 s) | `asyncAfter` (Control:379) | `_do_start_flc` — `_main_async_after` (control:999) | `flcCooldownTimer` — `setTimeout` (tapToneAnalyzer:1251) |
| T4 | detection's own cooldown gate: ignore a crossing within 0.5 s of the last tap | `lastTapTime = Date()` (TapDetection:142) | `last_tap_time` on `time.monotonic` (tap_detection:185) | **none** |
| T5 | guitar: "All taps captured. Processing..." for `captureWindow` (0.2 s), then average | `asyncAfter` (SpectrumCapture:747) | `_main_async_after` (spectrum_capture:911) | `setTimeout(CAPTURE_WINDOW_MS)` (tapToneAnalyzer:1954) |
| T6 | gated capture safety timeout: close a capture the audio never filled (material 2.0 s; guitar window + 0.5 s) | `asyncAfter` ×4 (SpectrumCapture:448, 498, 556, 593) | `_main_async_after` ×2 (spectrum_capture:663, 772) | **none** |
| T7 | ring-out tracking stops 3 s after the tap | `Timer.scheduledTimer(3.0)` (DecayTracking:67) — wall | `QTimer` (decay_tracking:105) — wall | `TRACK_SECONDS` on the **audio** clock (dsp/decay.ts) |

What this shows:

- **T1–T4 decide which audio is detected next** — the #19 defect. When one fires a chunk early or late
  against the audio, the next capture shifts. The error builds along a sequence, which is why the last
  taps move.
- **T5 changes no value** (the taps are already captured), only when "complete" is reached against the
  audio.
- **T6 must not move to audio time alone.** It exists for the case where audio STOPS (file ends, user
  stops, device drops) — then audio time stops too, and an audio-timed timeout would never fire.
- **T7 decides a value** (the ring-out) when the decay is slow, and the web already runs it on audio
  time — the natives do not.
- **The web differs in mechanism in four places** (T2, T4, T6, T7). T2 is likely why the web is immune on
  material: it re-arms at once and its warm-up runs on audio time. Its guitar path (T1, T5) is
  wall-clock like the natives since #17 F45, yet REG-G2 has not moved in any web run; why is not
  examined.

### Why the web lacks T4 and T6 (checked 2026-09-24)

Neither was ever ported. The web's first commit (2026-06-22) had no cooldown and no timeout; the
alignment work since (#17 F42, F45) added T1, T3 and T5 but not these two. Nothing records a decision.

- **T4 appears to be dead in the natives.** Swift's `detectTap` runs only while detection is listening
  (`onRmsLevelChanged`, TapDetection.swift:109), and `handleTapDetection` sets it idle the moment a tap
  is detected (TapDetection.swift:320). Detection returns only after the capture completes plus a 0.5 s
  rest (T1/T2), or after Accept (T3); a capture lasts at least 0.5 s (1.37 s for guitar), so on every
  path found the 0.5 s since the last tap has always passed. **Probed 2026-09-24:** with the gate's
  reject path made to crash, then to log, across the full Swift suite (every file-playback fixture
  included), it was reached exactly once — by `TapDetectionTests.duringCooldown_suppressesDetection`,
  which sets `lastTapTime` to 0.1 s ago by hand, forces detection to listening and calls `detectTap`
  directly. No production path reached it. Removing it therefore removes that test too (owner approved),
  in Swift and in Python's mirror.
- **But Python reaches T4 in real playback (probed 2026-09-24, on the committed code in a scratch
  worktree).** Besides its hand-set test, the gate rejected crossings in REG-P1 (7 times), REG-P2 (6),
  OUT-4 (4) and the self-regression's run of every case (14) — all PLATE sessions played from a file.
  The path the reasoning above missed: in file playback a plate phase auto-advances (L → C → FLC) and
  arms the next phase at once, with no rest, so detection is listening again within 0.5 s of the last
  tap and the wall-clock gate can fire. Whether it does depends on how fast the capture completed in
  wall time — Swift's run did not reach it, Python's did — which makes T4 itself a #19 timer, not dead
  code. The removal decision rested on "unreachable", so it is back with the owner.
- **Why Python reaches it and Swift does not — measured in REG-P1 (committed code, scratch worktrees).**
  Both fire the L tap at audio 2.880 s and fill the 0.5 s capture at ≈3.18 s; the finish runs at audio
  3.20 s in both. The difference is WALL time:

  | | Swift | Python |
  |---|---|---|
  | next phase armed, wall time after the tap | 1.27–1.33 s | 0.39 s |
  | the chunks at audio 3.20–3.29 s reach detection at | ≈1.3 s wall | ≈0.39 s wall |
  | T4 (0.5 s wall) open when they arrive? | no | yes — 5 chunks rejected |

  In Swift the audio thread keeps playing while the main thread does the finish and auto-advance
  (≈0.9 s of work here); the levels it produced meanwhile queue up and reach detection, carrying their
  audio times, after the re-arm. Python's test harness processes audio inline on the main thread, so
  the same chunks reach detection sooner in wall time. The SAME audio (0.32–0.41 s after the tap) is
  therefore rejected in Python and accepted in Swift — T4 measured in wall time is exactly the #19
  defect. In audio time the gate would reject those chunks in both editions; removed, in neither.
  What it rejects is the tail of the tap's ring-out, and the auto-advance already sets
  `isAboveThreshold = true` so a ring-out must fall before anything counts.
- **Decision (owner, 2026-09-24): T4 is removed from all three** (option (ii), over putting it on the
  audio clock). It duplicates the auto-advance's own ring-out guard, is never reached live, and Swift —
  canonical — already behaves as though it were absent; removing it moves Python onto Swift's behaviour.
  Python's plate playback values may shift slightly (the chunks it rejected now reach detection); the
  re-mint after #19 shows it.
- **T6 is a real behaviour difference.** The natives close a capture the audio never filled, live or
  file: after 2 s (material) or window + 0.5 s (guitar) they analyse the partial capture, or with no
  samples say "No signal detected — tap again" and re-arm. The web has no timeout; live, a capture the
  audio stops filling stays open.
- **The file-end flush is a separate mechanism, and the web's copy is incomplete.** *Correction: this
  entry first called the web's flush a stand-in for T6. It is not.* Swift has its own file-end flush:
  after the last chunk, `processFileData` calls `preMicRestartHandler`, which the analyzer set to
  `flushGatedCaptureOnFileEnd()` (SpectrumCapture.swift) — take the partial capture, zero-pad it to the
  window, and finish it as guitar OR material (Python `_flush_gated_capture_on_file_end`). The web's
  counterpart, `flushPartialGuitarCapture()`, handles guitar only (a partial material capture is dropped)
  and is called from the view (`App.tsx`, and the test runners) rather than by the engine at file end.

### Decisions (owner, 2026-09-24)

- **When #19 is done, all three editions do the same thing THE SAME WAY** — architectural consistency,
  not just matching behaviour: the same timers, the same clock, the same mechanism, in the same place.
  Where the web is incomplete, it is completed: it gets T6 in the natives' shape, its file-end flush becomes the natives'
  (guitar and material, called by the engine at file end), and T2 and T7 take the shared design.
- **Changing Swift is fine where the code does nothing.** T4 is removed from Swift and Python once it is
  proved unreachable — by a test/mutation showing that no path reaches it — rather than added to the web.

## Design (approved by the owner, 2026-09-24)

**Scope.** T1, T2, T3 and T5 run on the **audio clock**; T7 stops on the audio clock (the web's existing
mechanism, adopted by the natives); T6 stays on the **wall clock**, because it exists for when the
audio stops and an audio-timed version would then never fire. T4 is removed from Swift and Python once
proved unreachable. Every edition does this the same way, in the same place.

**Mechanism — the same in all three.**

1. **The analyzer's audio clock is the chunk time detection already receives.** Every chunk's level
   reaches the analyzer on the main thread with that chunk's audio time, in order (Swift
   `onRmsLevelChanged(_:audioTime:)`, Python `_on_rms_level_changed(level_db, audio_time)`, web the
   engine's per-chunk level call). The analyzer records it as `lastAudioTime` on every chunk, before any
   guard. The timers' actions use it, never the engine's running clock (`fftAnalyzer.audioElapsed`) read
   on the main thread — the audio thread races ahead of that. *Not changed:* the warm-up anchors set by
   user actions (Start, Accept, Redo, route change) still read the engine's clock at the moment of the
   action. They are not timers and are outside this design; recorded here so the difference is known.
2. **An audio-time scheduler replaces the wall-clock delays.** `afterAudio(delay, action)` records
   `(dueAudioTime = lastAudioTime + delay, action)`. On each chunk, before detection's guards, the
   analyzer runs every action whose due time has been reached, in order. The actions are the existing
   closures with their existing guards — the same timers, on a different clock.
3. **Re-arming re-anchors from THAT chunk's level**, the one whose audio time made the action due —
   not from the published meter level, which lags by a chunk on the main thread. Detection then resumes
   from the next chunk.
4. **Anchors are audio times.** A capture's completion is the audio time the analyzer has seen when it
   finishes the capture (on the main thread that is exactly the end of the chunk before the completing
   one — the completing chunk's level is queued behind the capture's finish). Accept (T3) anchors at the
   audio time seen when the user accepts.
5. **End of audio (owner's decision (b)).** File end already exists as a lifecycle event in all three —
   the file-end flush. It also releases a pending T5 at once, so a measurement whose last capture ends
   with the file still completes. T1–T3 are not released: with no audio there is nothing to detect.
6. **T7:** ring-out tracking stops when the chunk's audio time is 3 s past the tap's, checked in the
   per-chunk decay feed — as the web does now.
7. **T6** is unchanged in the natives (wall clock) and added to the web in the same shape.
8. **The web is completed to the same structure:** T2 becomes the 0.5 s rest (it currently restarts the
   warm-up), T6 is added, and its file-end flush becomes the natives' — guitar AND material, called by the
   engine at file end rather than by the view.

**Python's detection thread (owner, 2026-09-24: "C is all that makes sense").** Swift's per-chunk level
callback is called on the audio queue and hops to the main thread before detection
(`DispatchQueue.main.async`, TapToneAnalyzer.swift). Python's has run detection directly on the
processing thread since #17 F44 (`87e7ad7`), which ended a double delivery (a direct callback plus a
queued Qt signal) by keeping the direct one — so a capture's finish (queued to the main thread) and
detection ran on different threads, and "the audio time seen at finish" depended on thread timing.
Python now hops to the main thread with a single queued delivery, as Swift does: detection, the timer
actions and the capture finish all run on the main thread, in chunk order, in both editions.

**Found while porting to the web (2026-09-24): its material re-arm is one mechanism where the natives
have three.** The web re-arms every material phase through `armMaterialDetection`, which restarts the
0.5 s warm-up AND resets the noise-floor estimate to its initial value. The natives distinguish:

| material re-arm | Swift / Python | web |
|---|---|---|
| between taps of a phase (T2), and after a rejected tap (EG-1, "No resonance detected") | 0.5 s rest, then the latch from the current chunk; warm-up and noise floor untouched | warm-up restart + noise-floor reset |
| file-playback auto-advance to the next phase (L→C, C→FLC) | latch ABOVE (`isAboveThreshold = true`), listening at once; warm-up and noise floor untouched | warm-up restart + noise-floor reset |
| Accept L → arm C; the FLC hold ends → arm FLC | latch from the current level + warm-up restart; noise floor untouched | warm-up restart + noise-floor reset |

T2 was already in the design. The other two rows are the same family but not timers; they decide which
audio the next phase detects on, and bringing the web onto the natives' structure moves its material
playback values. **Decision (owner, 2026-09-24): all three rows now, in #19's web port — "do not do
later what you can do now".**

**And one more, underneath the rows above: whether detection runs DURING a capture.** In Swift and
Python a detected tap goes through `handleTapDetection`, whose first act is `detectionState = .idle`
(Swift TapDetection.swift:320, Python `_handle_tap_detection`); detection stays off through the capture
and the rest, and the latch and the noise-floor EMA are not updated meanwhile. The web's `detectTap`
fires straight into `beginCapture` and leaves detection LISTENING through the capture (guitar and
material); its comment says this is "as it does in Swift", which holds only for Swift's audio-queue
level-crossing path — the main-thread detection that follows sets it idle. So on the web the latch and
the EMA keep tracking through every capture, and the rest (T2) would begin from different state.
Why the values agree anyway: the web's re-arm threw that state away after every capture (the guitar rest
re-anchors the latch; the material re-arm restarts the warm-up and resets the floor), so the two
divergences cancelled. Fixing the re-arm alone would have CREATED a difference. **Decision (owner,
2026-09-24): align them — a detected tap turns detection off first on the web, as `handleTapDetection`
does in Swift and Python.**

**Tests.** Tests that wait on the wall clock for a re-arm or completion (the S6 traces, state invariants,
start-tap race, status re-arm, FLC cooldown) instead feed chunks with advancing audio time — the
production path the audio takes. Mutation checks: each timer back on the wall clock must fail a test;
T4's removal is justified by instrumenting it (fail if it ever rejects a crossing) and running every
suite, plus the reasoning above.

**Order.** Swift, then Python, then web; then one re-mint: Swift's oracle if its playback numbers move,
and every self-baseline (including Python's, pending since #17 F49).

## Implementation (2026-09-24; committed 2026-09-25: Swift `58796ac`, Python `820fabd`, web `c4fb2f3`)

**Swift.** `afterAudio(_:releasedAtFileEnd:_:)`, `runDueAudioActions()`, `releaseAudioActionsAtFileEnd()`
and `reArmFromCurrentChunk()` on the analyzer; `lastAudioTime` / `lastChunkLevelDB` set per chunk in
`onRmsLevelChanged`, before its guards. T1 (`scheduleGuitarReEnable`), T2
(`reEnableDetectionForNextPlateTap`), T3 (the FLC hold in `acceptCurrentPhase`, anchored on the due
chunk's level and audio time) and T5 (released at file end, by a `defer` in `flushGatedCaptureOnFileEnd`)
use it. T7: `trackDecayFast` stops at `decayTrackingDuration` (3 s) of audio; the wall `Timer` is gone.
T4 and its hand-set test removed.

**Python.** The same, plus (C): the per-chunk level reaches detection through a QUEUED signal
(`_rmsLevelOnMain`), as Swift's hops to the main thread. The file-end release is queued behind the
flush's own queued finish. `_do_start_flc` now restarts the warm-up, as Swift's FLC arm always has (its
docstring cited the plate rest's rule instead). The ring-out's `QTimer` and its four tests
(`test_wi10_qtimer_slots.py`) removed — rule 5.

**Web.** The same scheduler on the analyzer, hooked in `processAudioFrame` after the capture is fed (so a
finish sees the previous chunk's audio time, as in Swift). `tapCooldown` / `captureWindow` are analyzer
fields in seconds. The three material re-arm shapes (`armMaterialDetection` for the start,
`armMaterialPhase` for Accept/Redo/FLC, `autoAdvanceMaterialPhase`, and the rest
`reEnableDetectionForNextPlateTap`); detection off at tap fire; T6 added (`scheduleCaptureSafetyTimeout`,
wall clock); the file-end flush is `flushGatedCaptureOnFileEnd`, called by the engine's
`preMicRestartHandler` (guitar and material), and `App.tsx` / the runners no longer call a flush. The
FLC timer and its cancel are gone (the phase guard is the protection, as in the natives).

**Tests, all three.** A shared feed helper (`tooling/audio-clock-feed`) advances audio through the
production entry point; every test that slept through a timer feeds audio instead. A new slug,
`test/audio-clock-timers`, pins what nothing did: the plate rest, the FLC hold, the file-end release (and
that a rest is not released), a detected tap turning detection off, the wall-clock safety timeout, the
auto-advance arming at once latched above, and (natives) the ring-out stop — the web's is in
`decay-tracking` with its engine-side tracker. Python also pins detection running on the main thread.

**Mutation checks — every rule fails a test when broken, in every edition that has it.** Timers back on
the wall clock (T1, T2, T3, T5), T5 not released at file end (also caught by the real REG-G1 fixture),
T7 removed (Python: also REG-G2 and REG-P1), detection left on at tap fire (Swift sets it in two places;
both removed), T6 removed, the auto-advance reverted, the engine not flushing at file end (web: REG-G1
and both session recordings), and Python's detection back on the processing thread (also REG-G2 and
REG-P2).

**Suites (superseded by "Suites and the re-mint" below).** Swift 615, web 652 — all pass, with no playback value moved in either (Swift's zero-tolerance
oracle checks and the web's self-regression both pass). Python: all pass except `test_self_regression`,
expected until the re-mint.

## Suites and the re-mint (2026-09-24)

Run all three at once (a load test in itself): **Swift 616, Python 727, web 654 — all pass** except
Python's `test_self_regression` before its re-mint; `tsc` clean; parity map **107 groups**, no problems
(new: `test/audio-clock-timers`, `tooling/audio-clock-feed`, `util/timing-activity`).

- **Swift:** its zero-tolerance playback checks pass — no Swift value moved, so **the oracle does not
  change**.
- **Web:** its self-regression passes — no web value moved with #19, so **its baseline does not change**.
- **Python:** re-minted (owner approved). Exactly the 24 values #17 F49's window moved — every GFFT and
  plate/brace value, −0.0002 to −0.0004 dB and a few µHz — with no REG-G2 value, and nothing from T4's
  removal or detection's move to the main thread. `test_self_regression` then passes. Collected into
  the hub. Python and the web now agree on every value to 13–14 significant digits (48 of 146 differ
  only in the last digits — floating-point order, not a result); the parity report puts
  python-darwin-arm64 at 0.1–6.7% of each tolerance against the oracle.
- Windows/Linux baselines stay as they are until #17's sweep ends (#16).

## Reliability check, after the stall timeout and the playback hold (2026-09-24) — REPEATABLE

Python's `compute_all()`, the same scratch runs as below, rerun with T6 measuring silence and the
latency-critical activity held during playback:

| comparison | before | after |
|---|---|---|
| two normal-speed runs | 14 of 146 differ | **0** |
| normal vs +15 ms of work per chunk | 65 of 146 differ | **0** |
| one full run | 392–433 s | **111 s** |

The slowed run took 187 s and produced identical values: speed no longer changes a result. The 3.5–4×
speed-up is the throttling hold — playback now runs at about real time throughout.

## Reliability check (2026-09-24) — NOT yet repeatable

Python's `compute_all()` (every oracle case), run as a scratch script in a test settings sandbox:

| comparison | values that differ (of 146) |
|---|---|
| two normal-speed runs | **14** — REG-G2 tap 8 and the average it feeds |
| normal vs +15 ms of work per chunk | **65** — every REG-G2 tap and the average, REG-P1 (5), REG-P2 (6) |

**Cause 1, found: the safety timeout (T6) fires during SLOW playback, not only when audio stops.** The
guitar safety timeout is 1.865 s of WALL time after a capture starts; a guitar capture needs 1.37 s of
AUDIO. Run alone, REG-G2 is repeatable (3/3 identical) and every capture fills. Run after REG-B1/B2 in the
same process, Python's paced playback runs ~26% slower than real time, and taps 7–8 were closed by the
safety timeout with 32 128 / 29 056 of 65 536 samples (30 080 / 28 032 in another run). T6 was kept on
the wall clock because it must fire when audio STOPS — but it also fires when audio is merely slow,
which is #19 again. The design choice for T6 is back with the owner.

**Cause 2, not yet found:** under +15 ms/chunk REG-P1 and REG-P2 move. A plate capture needs 0.5 s of
audio against a 2 s safety timeout, so T6 does not explain it; something else in Python's plate path
still depends on speed.

**Why only Python, why only in sequence, why "slower after the brace cases" — measured (2026-09-24).**
Profiling REG-G2 in the sequence: 39.9 s of its 41.9 s were `time.sleep` — 851 sleeps averaging 47 ms
where each asks for one chunk (21.3 ms). The Python code did no extra work; its sleeps overran. A bare
process doing nothing but one-chunk sleeps for 60 s:

| process | 0–30 s | 30–60 s |
|---|---|---|
| plain Python, no Qt | 25 ms | 25 ms, steady |
| a `QApplication` | 22 ms | 56–98 ms |
| `QApplication` + "user-initiated" activity assertion | 22 ms | 56–73 ms |
| `QApplication` + **latency-critical** activity assertion | 22 ms | 22 ms, steady |

So it is **macOS App Nap / timer throttling**, applied to a windowless Cocoa app — which the Python test
process is, because it creates a `QApplication` — after about 30–35 s of process life, and lifted only
by the latency-critical activity. That answers the three questions: Python because its test process is
a Qt app (the web's tests run in Node, a plain command-line process; Swift's test host has not been
checked); in sequence but not alone because REG-G2 alone ends before the throttling starts; and "after
the brace cases" is simply elapsed process time. Throttled paced playback runs 2–4× slower than real
time, and the one lifecycle timer still on the wall clock (T6) then closes captures early. Probably
cause 2 as well: REG-P1/P2 run later still, where the throttling is heaviest, and at ~4× a 0.5 s plate
capture needs more than T6's 2 s — to be confirmed.

**This also reaches the real Python app:** a user who plays a file with the app in the background gets
the same throttling, and T6 would cut captures there too.

**Decisions (owner, 2026-09-24):**
1. **T6 becomes a STALL timeout** in all three editions: it fires only after its interval with NO audio
   arriving, measured on the wall clock since the last chunk — not since the capture started. Throttled
   or slow playback still delivers chunks, so it never fires there; audio that truly stops still
   triggers it.
2. **Time-critical operations hold off the OS's throttling** — "any place that has time critical
   operations (which is playback and capture)": the Python test harness, and the apps while playing a
   file or capturing, ask the OS not to throttle their timers (macOS: a latency-critical activity).
   Where an edition's platform offers no such control, that is recorded rather than worked around.
4. **One safety-timeout site per capture kind, in all three (owner, 2026-09-24, option (b)).** Swift had
   a separate copy of each timeout closure in each start path (fast-start and normal — four in all);
   Python reached one per kind from both paths; the web has one in `beginCapture`. Swift is restructured
   to Python's shape — "layout is an important part of architecture". The web differs only in having no
   audio-side fast-start path.
3. **Check Swift's test host** for the same throttling. **Checked:** a paced one-chunk sleep on a
   background queue inside Swift's test host held at 25.0 ms, steady for 60 s — not throttled (XCTest
   keeps its host active). So of the three test suites only Python's was affected. The real Swift app
   in the background was not measured; decision 2 covers it regardless.

**Implemented (2026-09-24; committed with #19):**
- **Stall timeout, all three:** `afterAudioStall` (Swift) / `after_audio_stall` (Python) / `afterAudioStall`
  (web) fires only once no chunk has arrived for the interval, measured from `lastChunkWallTime`, which
  the per-chunk entry sets; it stops checking once its capture has finished or been superseded. Each
  edition has ONE safety timeout per capture kind — Swift's four closures became two (decision 4). New
  test in all three: the timeout does not fire while audio keeps arriving slowly (one chunk every 0.4 s
  for 2.8 s); timing it from the capture's start again fails that test in every edition.
- **Throttling hold during file playback, natives:** `holdTimingActivity` / `releaseTimingActivity`
  (Swift `Utilities/TimingActivity.swift`, Python `utilities/timing_activity.py`), a latency-critical
  activity held for the whole playback pump (`processFileData` / `process_file_data`). Python is a no-op
  off macOS. **Web: no equivalent** — a browser offers no way to exempt a page from background-tab
  timer throttling; its file playback is paced by `setTimeout`, so a background tab plays slower. With
  every lifecycle timer on the audio clock and T6 measuring silence, that changes speed, not results —
  except under a browser's heaviest throttling (Chrome's once-a-minute timers in a tab hidden for 5
  minutes), where chunks would arrive further apart than T6's interval. **Decision (owner, 2026-09-24):
  pace the web's file playback from the AUDIO clock — the worklet's rendered frames — instead of
  `setTimeout`**, which Chrome's heaviest throttling cannot slow. **Verified (owner, 2026-09-25), on
  the current bundle `index-CVNPXn6d.js`:** the re-run with Taps = 8 completed with correct values and
  waveforms. (A first pass is void — the page was running a stale cached bundle; see "Resolved: … stale
  bundle" below.) The first pass, as recorded: a
  348 s file — 330 s of noise matched to `Recording.wav`'s lead-in (−72 dBFS), then `Recording.wav` —
  played with Generic, Taps = 8, first with the tab visible, then with the tab hidden for more than 5
  minutes (Memory Saver off). Both runs completed with the correct waveform and peaks, matching the
  saved reference. (The owner brought the check forward from after the sweep.)
- **Capture — raised with the owner:** once T6 measures silence, throttling cannot change a capture's
  result: the capture fills by the audio, every lifecycle delay runs on the audio clock, and a late
  wall-clock check only delays a stall timeout. **Decision (owner, 2026-09-24): during file playback
  only** ("Your argument works. Just during playback.").

**Also seen:** wall-clock timers scheduled in one case fire during the next (the queued file-end release
and the safety timeouts of REG-B1/B2/G1). They act on the previous case's analyzer and did not differ
between runs, so they are not the cause here — but a test run leaks work across cases.

## The web's audio-clock playback pacing (2026-09-24; web `c4fb2f3`)

`RealtimeFFTAnalyzer.playFile` no longer sleeps with `setTimeout` when an `AudioContext` is running.
While a file plays the mic's samples are ignored, but each 1024-frame chunk the worklet posts is still a
tick of the audio clock: `onChunk` adds its duration (at the context's rate) to `renderedSeconds`, and
the playback loop feeds the next file chunk once the device has rendered as much audio as the file has
played (`untilRendered`) — so the file stays at real time even when the device rate differs from the
file's. If no chunk arrives for 250 ms (the input stopped) a waiter gives up, so playback cannot hang —
slower, same results. Headless (tests, no `AudioContext`) keeps `setTimeout` pacing. Tagged
`util/timing-activity`, the natives' counterpart. Test: a stand-in context and hand-delivered worklet
chunks — one rendered chunk lets exactly one more file chunk through; pacing by the timer again fails it.

## Run-review for the owner (2026-09-24) — what changed that can be seen

All three editions:
1. Guitar, Taps = 3, live: after each tap "Tap N/3 captured", detection back about 0.5 s later; a second
   strike inside that 0.5 s is not counted; after the third, "All taps captured. Processing..." briefly,
   then the result.
2. Plate, Taps = 2, live: tap twice for fL — the second counts once ~0.5 s has passed; same for fC.
   (Web: used to re-arm with a warm-up — should now feel like the natives.)
3. Plate with FLC, live: Accept fC → the reposition prompt ~0.5 s → fLC arms and takes a tap.
4. File playback of a multi-tap guitar session and a full plate session (REG-G2, REG-P1 recordings):
   results as each edition gave before. (Web: plate phases still auto-advance L → C → FLC.)
5. File playback of a short single-tap file whose tap is near the end (REG-G1): still completes. (Web:
   now through the engine, not the view; a plate file whose last capture the file cuts off is analysed,
   no longer dropped.)

Python only:
6. Play a long file and switch to another app for the whole playback: identical result to a foreground
   run, and not noticeably longer than the file.
7. Live mic taps: still immediate (detection now runs on the main thread).

Web only:
8. Play a file with the tab visible: real time (paced by the audio device now). Then the Chrome
   hidden-tab check: `Tests/O'Brien/Recording-with-5m30s-noise-lead-in.wav`, tab hidden for the lead-in.

## Resolved: the web's "Tap 8/8 captured. Tap again..." at file start was a stale bundle (2026-09-25)

**Seen by the owner in Chrome, during the hidden-tab check:** after a completed 8-tap run, pressing Play
File showed "Tap 8/8 captured. Tap again..." at once, and kept it until the file's taps began; from then on
the messages and the result were correct.

**Cause: the page was not running the current code.** The PWA service worker served a cached bundle
(`index-CgNU_BYb.js`) left over from an earlier build; the clean build of 2026-09-25 11:43 is
`index-CVNPXn6d.js`. That old bundle no longer exists, so which code it held is unknown. After the service
worker was unregistered and site data cleared, the current bundle shows "Tap the guitar 8 times..." at
file start on the same file. **Not a #19 defect.** (Safari runs were not affected; Chrome was used only
for the hidden-tab check.)

- How it was found: a temporary diagnostic in `setStatusMessage` traced every "…captured. Tap again..."
  status with its call path. On the stale page it printed nothing, even for taps 1–7, which exposed the
  stale bundle; on the current bundle it traced each tap from `finishGuitarGatedCapture`, as expected.
  The diagnostic has been removed (tsc clean).
- Ruled out along the way: `startTapSequence` itself (headless, the app's exact Play File sequence after
  a completed run gives "Tap the guitar 8 times..." with the count at 0); a stale snapshot (`notify()`
  rebuilds it); the app's settings and Taps effects.
- **Consequence: the earlier Chrome hidden-tab pass was void** — it ran on the same unknown bundle. The
  re-run on `index-CVNPXn6d.js` (Taps 8) PASSED: correct values and waveforms.
- Before any web run-review, check in DevTools → Sources that the page's `assets/index-*.js` matches the
  one in `dist/assets/`. If not: Application → Service workers → Unregister (tick "Update on reload"),
  Application → Storage → Clear site data, reload.
- The hidden-tab test file, `Tests/O'Brien/Recording-with-5m30s-noise-lead-in.wav`, is the only file
  with a lead-in long enough to exercise Chrome's heaviest timer throttling (the other files' taps come
  too soon). **Not committed (owner, 2026-09-25): 66.8 MB, and easy to recreate:** read
  `Tests/O'Brien/Recording.wav` as int16 (48 kHz, stereo); take the RMS of its quiet lead-in (the chunks
  before the first 1024-sample chunk above −60 dBFS, mono mix: −72.2 dBFS); generate 330 s of Gaussian
  noise at that RMS (`numpy.random.default_rng(19)`), rounded to int16 and duplicated to both channels;
  append Recording.wav's samples unchanged; write 16-bit PCM. Result: 348.2 s.

## Noticed while doing #19 — not acted on, for the owner

- **Python's baseline minter sets up no settings sandbox.** `Tooling/mint-baseline.py` sandboxes only
  under pytest or with `GT_TEST_SANDBOX` set, so a standalone mint reads and writes the user's REAL
  Python settings (the runner restores what it changes). #19's own mints were run with
  `GT_TEST_SANDBOX` set; five earlier `--check` runs that day were not.
- **Test runs leak work across cases.** Wall-clock timers scheduled in one playback case (the queued
  file-end release, the safety timeouts) fire during the next, against the previous case's analyzer,
  which is never freed. They did not change a result, but each case does not start clean.
- **Swift turns detection off in two places for a plate tap** (`handleTapDetection` and
  `handlePlateTapDetection`); Python and the web in one. Layout — for the `tap-decisions` slug.
- **The web tracks the ring-out in the engine** (`DecayTracker`), the natives on the analyzer — so its
  T7 is pinned in `decay-tracking.test.ts`, not beside the natives'. For the `decay-tracking` slug.

## Interim

Until this is fixed, Python's `test_self_regression` can fail under pytest for this reason alone. A
failure listing only late-sequence REG-G2 / REG-P2 values is this issue; anything else is not.

**2026-09-24 — now blocking a re-mint, and the reason to do this next.** #17 F49 changed Python's gated
window, which moves 24 GFFT and plate/brace values in its self-baseline. The re-mint could not be done
cleanly: four standalone mint runs in a row each also moved REG-G2 taps 7–8 (tap 6 too in one run), by a
different amount each time (tap 7 air −0.31, −0.40, −0.59 dB in the runs inspected). Standalone runs were
therefore **not** reliably clean on this machine that day, contrary to the note above. Python's baseline
was left as committed, so `test_self_regression` fails until this is fixed; since the fix moves values in
all three editions anyway, every baseline (and the oracle, if Swift's playback numbers move) is
re-minted once, afterwards. The web's runner did not move REG-G2 in any run — why Python is the more
sensitive edition has not been examined.
