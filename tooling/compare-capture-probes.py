#!/usr/bin/env python3
"""Compare two editions' capture-window fingerprints, and say what the difference means.

    ./tooling/compare-capture-probes.py capture-probe-swift.json capture-probe-python.json

Produced by Swift's CaptureProbeTests, guitar_tap's Tooling/capture-probe.py and GuitarTapWeb's
tooling/capture-probe.sh; any two compare. Each fingerprints the buffer on either side of the
onset-alignment step for every tap of REG-G2, so the comparison localises a cross-edition
difference rather than just confirming it:

    buffer differs               -> the editions are not capturing the same samples;
                                    the divergence is upstream, in detection or buffering
    buffer same, window differs  -> the same samples are being windowed differently;
                                    the alignment step is the divergence
    both identical               -> the input is identical and the arithmetic differs;
                                    look at the FFT, not the capture

All three editions align the guitar capture window to the tap onset. The probes run on file
replay, which feeds 1024-sample chunks in every edition; they do not see the size of the buffers
a live microphone delivers.
"""

from __future__ import annotations

import json
import sys


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    a, b = (load(p) for p in argv)
    label_a = f"{a['edition']}-{a['os']}-{a['arch']}"
    label_b = f"{b['edition']}-{b['os']}-{b['arch']}"
    print(f"{label_a}  vs  {label_b}   (case {a.get('caseName')})\n")

    ra, rb = a["records"], b["records"]
    if len(ra) != len(rb):
        print(f"❌ different number of captures: {len(ra)} vs {len(rb)} — the editions are not")
        print("   even detecting the same taps. Nothing below is comparable.")
        return 1

    buffers_differ = windows_differ = counts_differ = 0
    print(f"{'tap':<5}{'buffer':>10}{'window':>10}   verdict")
    for index, (x, y) in enumerate(zip(ra, rb), start=1):
        same_buffer = x["bufferHash"] == y["bufferHash"]
        same_window = x["windowHash"] == y["windowHash"]
        if x["bufferCount"] != y["bufferCount"] or x["windowCount"] != y["windowCount"]:
            counts_differ += 1
            verdict = (f"LENGTH differs — buffer {x['bufferCount']}/{y['bufferCount']}, "
                       f"window {x['windowCount']}/{y['windowCount']}")
        elif not same_buffer:
            buffers_differ += 1
            verdict = "buffer differs — divergence is UPSTREAM of the capture"
        elif not same_window:
            windows_differ += 1
            verdict = "same buffer, different window — the ALIGNMENT diverges"
        else:
            verdict = "identical — input matches; any spectrum difference is ARITHMETIC"
        print(f"{index:<5}{'same' if same_buffer else 'DIFF':>10}"
              f"{'same' if same_window else 'DIFF':>10}   {verdict}")

    print()
    if counts_differ:
        print(f"{counts_differ} tap(s) captured a different NUMBER of samples. Buffer sizing")
        print("differs between the editions — that alone shifts every spectrum.")
    if buffers_differ:
        print(f"{buffers_differ} tap(s) differ before alignment. The editions are not capturing")
        print("the same samples, so fixing the alignment step cannot close the gap on its own.")
    if windows_differ and not buffers_differ:
        print(f"{windows_differ} tap(s) share a buffer but not a window. The alignment step is")
        print("the whole difference.")
    if not (counts_differ or buffers_differ or windows_differ):
        print("Every capture is bit-identical. The editions feed the FFT the same samples, so")
        print("the measured spectrum difference is arithmetic — look at the transform, not the")
        print("capture. That would rule out the whole alignment family for this case.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
