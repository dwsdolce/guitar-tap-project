#!/usr/bin/env python3
"""Play one recording at every position of the audio chunk boundary, and say what changes.

    .venv/bin/python tooling/chunk-boundary-sweep.py RECORDING.wav [options]

    --threshold DB     tap detection threshold in dBFS (default -40)
    --kind KIND        guitar (default) or material (plate / brace)
    --positions N      how many boundary positions to try, spread over one chunk (default 1024: all)
    --probe FILE ...   capture-probe files recorded from this same audio: check the model against them

WHY. The editions process audio in 1024-sample chunks, and a tap is detected from the loudness of
whole chunks. Where the chunk boundaries fall relative to a tap is an accident — of when the stream
started, of the edition, of the run — so anything that depends on it makes the same tap come out
differently from one edition, or one run, to the next. A live comparison of three editions shows
three of those accidents. This shows all 1024: the recording is "played" with its first k samples
dropped, for every k, which moves every boundary k samples against the audio and changes nothing
else.

WHAT IT REPORTS.
  * Per tap: at how many boundary positions it is detected, and how many different onset samples and
    different FFT windows the capture comes to. One window means the tap's result does not depend on
    the boundary.
  * Per recording: how many taps are detected at each position. More than one count means a tap is
    caught or missed by the accident of the boundary.
  * The same for a SAMPLE-BASED trigger (a prototype; no edition has one): a running loudness over
    the last 1024 samples, firing once it has stayed above the threshold for 1024 samples. It has no
    boundary, so it gives one answer.

IT IS A MODEL, NOT THE APP. The detection, capture and alignment below are written out again here in
Python, from the editions' rules; they must be kept in step with them (the constants are at the
top). --probe is the check that they are: given the capture-probe files an edition wrote for this
audio (the `LIVE_PROBE` developer switch, with Dump Capture Audio on), the model is run on that
edition's own boundary position and must reproduce where its capture started and the window it
handed to the transform, bit for bit.

Two things are simpler here than in the editions:
  * The rest after a capture is modelled as a fixed dead time, then a fresh rising edge.
  * Plate and brace are detected here as guitar is, against the threshold itself; the editions use a
    noise floor that moves. Their captures and alignment are modelled; which of their taps is
    detected is only indicative.

The recording should be one the app saved (Dump Capture Audio): mono 32-bit float, with about two
seconds before the first tap. Any WAV is read (channels are averaged), but one with less quiet
before its first tap than the pre-roll plus a chunk cannot be shifted across a whole chunk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from collections import Counter

import numpy as np

# --- The editions' rules, restated. Keep in step with them. -------------------------------------

CHUNK = 1024                    # samples per processed chunk
CONFIRM_CHUNKS = 2              # consecutive chunks above the threshold that confirm a tap
FFT_SIZE = 65536                # the guitar capture and its FFT window
PRE_ROLL_SECONDS = 0.2          # audio kept before the trigger
PRE_ONSET_SECONDS = 0.1         # silence kept before the onset in the aligned window
ONSET_NOISE_SAMPLES = 2048      # stretch of noise the onset threshold is measured over
ONSET_THRESHOLD_MULTIPLIER = 10.0
ONSET_MIN_THRESHOLD = 0.001
ONSET_BACKUP_SAMPLES = 32
ONSET_NOISE_GUARD_SAMPLES = 256  # between the re-measured noise and the tap
ONSET_REFINEMENT_PASSES = 4
REST_SECONDS = 0.5              # the rest after a capture before detection re-arms
MATERIAL_CAPTURE_SECONDS = 0.5  # plate / brace capture
MATERIAL_WINDOW_SECONDS = 0.4   # plate / brace FFT window


class Geometry:
    """The capture's sizes at a sample rate, for guitar or material."""

    def __init__(self, sample_rate: int, kind: str) -> None:
        self.kind = kind
        self.pre_roll = int(sample_rate * PRE_ROLL_SECONDS)
        self.pre_onset = int(sample_rate * PRE_ONSET_SECONDS)
        if kind == "guitar":
            self.capture = FFT_SIZE
            self.window = FFT_SIZE
            # The window's audio ends a fixed margin short of its end; zeros follow.
            self.window_audio = FFT_SIZE - max(0, self.pre_roll - self.pre_onset)
        else:
            self.capture = int(sample_rate * MATERIAL_CAPTURE_SECONDS)
            self.window = int(sample_rate * MATERIAL_WINDOW_SECONDS)
            self.window_audio = self.window
        # From one trigger to the earliest next: the rest of the capture, then the rest.
        self.dead_time = self.capture - self.pre_roll + int(sample_rate * REST_SECONDS)


def read_wav(path: str) -> tuple[np.ndarray, int]:
    """The recording as mono float32 samples and its sample rate. PCM 16/24/32-bit and 32-bit float."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise SystemExit(f"{path}: not a WAV file")
    at, fmt, body = 12, None, None
    while at + 8 <= len(data):
        tag, size = data[at:at + 4], struct.unpack("<I", data[at + 4:at + 8])[0]
        if tag == b"fmt ":
            fmt = struct.unpack("<HHIIHH", data[at + 8:at + 24])
        elif tag == b"data":
            body = data[at + 8:at + 8 + size]
        at += 8 + size + (size & 1)
    if fmt is None or body is None:
        raise SystemExit(f"{path}: no fmt or data chunk")
    code, channels, rate, _, _, bits = fmt
    if code == 3 and bits == 32:
        samples = np.frombuffer(body, dtype="<f4").astype(np.float32)
    elif code in (1, 0xFFFE) and bits == 16:
        samples = (np.frombuffer(body, dtype="<i2").astype(np.float32)) / np.float32(32768)
    elif code in (1, 0xFFFE) and bits == 32:
        samples = (np.frombuffer(body, dtype="<i4").astype(np.float64) / 2147483648.0).astype(np.float32)
    elif code in (1, 0xFFFE) and bits == 24:
        raw = np.frombuffer(body, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        value = raw[:, 0] | (raw[:, 1] << 8) | (raw[:, 2] << 16)
        value = np.where(value >= 1 << 23, value - (1 << 24), value)
        samples = (value.astype(np.float64) / 8388608.0).astype(np.float32)
    else:
        raise SystemExit(f"{path}: unsupported WAV format (code {code}, {bits} bits)")
    if channels > 1:
        samples = samples[: len(samples) // channels * channels].reshape(-1, channels).mean(axis=1).astype(np.float32)
    return samples, rate


# --- Detection -----------------------------------------------------------------------------------

def chunk_levels(x: np.ndarray, k: int) -> np.ndarray:
    """Each chunk's RMS level in dBFS (-100 for digital silence), with the boundaries k samples in."""
    n = (len(x) - k) // CHUNK
    chunks = x[k:k + n * CHUNK].astype(np.float64).reshape(n, CHUNK)
    rms = np.sqrt((chunks * chunks).mean(axis=1))
    return np.where(rms > 0, 20 * np.log10(np.maximum(rms, 1e-30)), -100.0)


def chunk_triggers(x: np.ndarray, k: int, threshold_db: float, dead_time: int, start: int = 0,
                   only_first: bool = False) -> list[int]:
    """Where the chunk-based detector fires, as the stream index just past the confirming chunk:
    a fresh rising edge, then CONFIRM_CHUNKS consecutive chunks above the threshold; after each,
    nothing until the dead time has passed."""
    levels = chunk_levels(x, k)
    above = levels > threshold_db
    out: list[int] = []
    i = max(1, (start - k) // CHUNK + 1)
    run = 0
    while i < len(above):
        if above[i]:
            if run > 0:
                run += 1
            elif not above[i - 1]:
                run = 1
            if run >= CONFIRM_CHUNKS:
                trigger = k + (i + 1) * CHUNK
                out.append(trigger)
                if only_first:
                    break
                # Detection re-arms on the chunk in which the dead time ends, and that chunk can
                # itself begin the next tap's run.
                i = max(i + 1, (trigger + dead_time - k) // CHUNK)
                run = 0
                continue
        else:
            run = 0
        i += 1
    return out


def sample_triggers(x: np.ndarray, threshold_db: float, dead_time: int, window: int = CHUNK,
                    hold: int = CHUNK) -> list[int]:
    """PROTOTYPE. Where a sample-based detector would fire: the running level over the last `window`
    samples, from below the threshold, stays above it for `hold` samples."""
    x64 = x.astype(np.float64)
    total = np.concatenate([[0.0], np.cumsum(x64 * x64)])
    above = (total[window:] - total[:-window]) / window > 10 ** (threshold_db / 10)
    edges = np.diff(np.concatenate([[1], above.astype(np.int8)]))
    rises, falls = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    out: list[int] = []
    earliest = 0
    for rise in rises:
        later = falls[falls > rise]
        end = later[0] if len(later) else len(above)
        trigger = int(rise) + window + hold
        if end - rise >= hold and trigger >= earliest:
            out.append(trigger)
            earliest = trigger + dead_time
    return out


# --- Capture and alignment -----------------------------------------------------------------------

def find_onset(buffer: np.ndarray, refine: bool = True) -> int | None:
    """The tap's onset in a capture: the first sample above 10× the noise at the buffer's start, then —
    `refine` — above 10× the noise re-measured just before that sample, until it stops moving; less
    the backup. None when nothing exceeds the threshold."""
    if len(buffer) < ONSET_NOISE_SAMPLES:
        return None
    magnitude = np.abs(buffer)

    def threshold(start: int) -> float:
        region = buffer[start:start + ONSET_NOISE_SAMPLES].astype(np.float64)
        return max(float(np.sqrt(np.mean(region * region))) * ONSET_THRESHOLD_MULTIPLIER, ONSET_MIN_THRESHOLD)

    def first_above(level: float) -> int | None:
        hits = np.flatnonzero(magnitude > level)
        return int(hits[0]) if len(hits) else None

    crossing = first_above(threshold(0))
    if crossing is None:
        return None
    if refine:
        for _ in range(ONSET_REFINEMENT_PASSES):
            noise_start = crossing - ONSET_NOISE_GUARD_SAMPLES - ONSET_NOISE_SAMPLES
            if noise_start < 0:
                break
            refined = first_above(threshold(noise_start))
            if refined is None or refined == crossing:
                break
            crossing = refined
    return max(0, crossing - ONSET_BACKUP_SAMPLES)


def aligned_window(buffer: np.ndarray, onset: int | None, g: Geometry) -> np.ndarray:
    """The window handed to the transform: `g.window` samples with the onset at the pre-onset mark,
    zero-filled where the capture does not reach, its audio ending at `g.window_audio`."""
    window = np.zeros(g.window, dtype=np.float32)
    if onset is None:
        count = min(len(buffer), g.window)
        window[:count] = buffer[:count]
    else:
        start = onset - g.pre_onset
        if start >= 0:
            piece = buffer[start:start + g.window]
            window[:len(piece)] = piece
        else:
            piece = buffer[:g.window + start]
            window[-start:-start + len(piece)] = piece
    window[g.window_audio:] = 0
    return window


def capture_at(x: np.ndarray, trigger: int, g: Geometry) -> tuple[int, np.ndarray]:
    """The capture a trigger starts: from the pre-roll before it, `g.capture` samples."""
    start = max(0, trigger - g.pre_roll)
    return start, x[start:start + g.capture]


def fingerprint(samples: np.ndarray) -> str:
    """FNV-1a over the samples' float32 bit patterns — the capture probes' function."""
    h = 0xCBF29CE484222325
    for byte in np.asarray(samples, dtype="<f4").tobytes():
        h = ((h ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


# --- The sweep ------------------------------------------------------------------------------------

def sweep(x: np.ndarray, rate: int, threshold_db: float, kind: str, positions: int) -> None:
    g = Geometry(rate, kind)
    ks = sorted({round(i * CHUNK / positions) % CHUNK for i in range(positions)})
    reference = chunk_triggers(x, 0, threshold_db, g.dead_time)
    if not reference:
        print("No tap is detected at this threshold.")
        return
    print(f"{len(reference)} tap(s) detected with the boundaries as recorded; "
          f"{len(ks)} boundary positions tried.\n")

    counts: Counter[int] = Counter()
    for k in ks:
        counts[len(chunk_triggers(x, k, threshold_db, g.dead_time))] += 1
    sample = sample_triggers(x, threshold_db, g.dead_time)
    print("Taps detected over the whole recording")
    for count, positions_with in sorted(counts.items()):
        print(f"  chunk-based : {count} tap(s) at {positions_with} of {len(ks)} positions")
    print(f"  sample-based: {len(sample)} tap(s), at every position (prototype)\n")

    print("Each tap on its own (detection armed shortly before it)")
    print(f"  {'tap':>3} {'at (s)':>8} {'detected':>12} {'onsets':>7} {'span':>5} {'windows':>8}   "
          f"{'old rule: onsets':>16} {'span':>5}")
    for number, tap in enumerate(reference, 1):
        armed = max(0, tap - 8 * CHUNK)
        onsets, old_onsets, windows, detected = set(), set(), set(), 0
        for k in ks:
            fired = chunk_triggers(x, k, threshold_db, g.dead_time, start=armed, only_first=True)
            if not fired:
                continue
            detected += 1
            start, buffer = capture_at(x, fired[0], g)
            onset = find_onset(buffer)
            old = find_onset(buffer, refine=False)
            onsets.add(None if onset is None else start + onset)
            old_onsets.add(None if old is None else start + old)
            windows.add(hashlib.blake2b(aligned_window(buffer, onset, g).tobytes(), digest_size=8).digest())

        def span(values: set) -> str:
            real = sorted(v for v in values if v is not None)
            return str(real[-1] - real[0]) if real else "-"

        print(f"  {number:>3} {tap / rate:>8.2f} {f'{detected}/{len(ks)}':>12} {len(onsets):>7} {span(onsets):>5} "
              f"{len(windows):>8}   {len(old_onsets):>16} {span(old_onsets):>5}")
    print("\n  onsets / windows: how many different ones over the positions — 1 is boundary-independent.")
    print("  old rule: the onset from the noise at the start of the capture alone, for comparison.")


def check_probes(x: np.ndarray, rate: int, threshold_db: float, kind: str, paths: list[str]) -> bool:
    """Run the model on each probe record's own boundary position; it must reproduce the record."""
    g = Geometry(rate, kind)
    ok = True
    print("Model against the capture probes")
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            document = json.load(fh)
        for index, record in enumerate(document["records"], 1):
            head = np.array([int(h, 16) for h in record["bufferHead"]], dtype=np.uint32).view(np.float32)
            lead = int(np.argmax(head != 0))
            candidates = np.flatnonzero(x[lead:len(x) - len(head) + lead + 1] == head[lead])
            found = [int(c) for c in candidates if np.array_equal(x[c:c + len(head)], head)]
            label = f"  {document.get('edition', '?'):7s} capture {index}"
            if not found:
                print(f"{label}: its audio is not in this recording")
                ok = False
                continue
            start = found[0]
            k = (start + g.pre_roll) % CHUNK
            fired = chunk_triggers(x, k, threshold_db, g.dead_time, start=max(0, start - 2 * CHUNK), only_first=True)
            if not fired or capture_at(x, fired[0], g)[0] != start:
                got = None if not fired else capture_at(x, fired[0], g)[0]
                print(f"{label}: capture starts at {start}; the model says {got}  ✗")
                ok = False
                continue
            buffer = x[start:start + record["bufferCount"]]
            window = aligned_window(buffer, find_onset(buffer), g)
            same_buffer = fingerprint(buffer) == record["bufferHash"]
            same_window = fingerprint(window) == record["windowHash"]
            ok = ok and same_buffer and same_window
            print(f"{label}: start {start} ✓   buffer {'✓' if same_buffer else '✗'}   window {'✓' if same_window else '✗'}")
    # The whole recording at each probe file's boundary position: the model must find the taps the
    # edition captured, no more and no fewer.
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            document = json.load(fh)
        starts = []
        for record in document["records"]:
            head = np.array([int(h, 16) for h in record["bufferHead"]], dtype=np.uint32).view(np.float32)
            lead = int(np.argmax(head != 0))
            candidates = np.flatnonzero(x[lead:len(x) - len(head) + lead + 1] == head[lead])
            starts += [int(c) for c in candidates if np.array_equal(x[c:c + len(head)], head)][:1]
        if len(starts) < 2 or len({(s + g.pre_roll) % CHUNK for s in starts}) != 1:
            continue  # one tap, or captures from separate sessions: no sequence to check
        k = (starts[0] + g.pre_roll) % CHUNK
        modelled = [capture_at(x, t, g)[0] for t in chunk_triggers(x, k, threshold_db, g.dead_time)]
        same = modelled == starts
        ok = ok and same
        print(f"  {document.get('edition', '?'):7s} sequence: {len(starts)} captures; the model finds {len(modelled)} "
              f"{'✓' if same else '✗ ' + str(modelled)}")
    print("  The model reproduces every probe record.\n" if ok else
          "  ✗ The model does NOT match the editions here — its rules are out of step, or the\n"
          "    threshold / kind given is not the one the recording was made with.\n")
    return ok


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("recording")
    parser.add_argument("--threshold", type=float, default=-40.0)
    parser.add_argument("--kind", choices=("guitar", "material"), default="guitar")
    parser.add_argument("--positions", type=int, default=CHUNK)
    parser.add_argument("--probe", nargs="+", default=[])
    args = parser.parse_args(argv)

    x, rate = read_wav(args.recording)
    print(f"{args.recording}: {len(x)} samples at {rate} Hz ({len(x) / rate:.2f} s), {args.kind}, "
          f"threshold {args.threshold} dBFS\n")
    ok = check_probes(x, rate, args.threshold, args.kind, args.probe) if args.probe else True
    sweep(x, rate, args.threshold, args.kind, max(1, min(args.positions, CHUNK)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
