#!/usr/bin/env python3
"""How far apart the editions actually are — the measurement behind the parity tolerance.

    ./tooling/parity-report.py            # summary
    ./tooling/parity-report.py --verbose  # every value's delta, worst first

The cross-edition tolerance in parity-oracle.json (1 dB / 1 Hz / q 1 / ringOut 0.03) was never
measured. It is a safe round number, and a bar that loose stops being a check: the Swift goldens
drifted by up to 0.0028 dB for an unknown length of time and nothing noticed, because the bar sat
four orders of magnitude above the drift.

This replaces the guess with data. It needs no instrumented assertions and no measurement flag —
once each configuration has committed the absolute values it computes, the distance between any
two of them is subtraction over committed files.

Two decompositions matter, because a single "distance from the oracle" conflates them:

  * EDITION effect   — same OS and arch, different edition. How much the implementations differ.
  * PLATFORM effect  — same edition, different OS or arch. How much the machines differ.

If the spread is mostly platform, tightening the cross-edition bar is safe and the real bar is
elsewhere. If it is mostly edition, tightening it is what starts catching real divergence.

The oracle is the canonical configuration — swift-darwin-arm64 — doing double duty as the parity
origin, so "distance from the oracle" means distance from that one configuration, not from
"Swift" in the abstract.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINES = os.path.join(HUB, "tooling", "parity", "baselines")
ORACLE_PATH = os.path.join(HUB, "tooling", "parity", "parity-oracle.json")

# Which tolerance governs a value, by the leaf its path ends in.
TOLERANCE_KEYS = {
    "frequency": "freqHz",
    "magnitude": "magDb",
    "q": "q",
    "ringOutSec": "ringOutSec",
    "db": "gatedFftDb",
    "deltaDb": "gatedFftDb",
}

# Editions and the OSs each is expected to reach, so a gap is reported rather than assumed absent.
EXPECTED = {
    "swift": ["darwin", "ios", "ios-simulator"],
    "python": ["darwin", "windows", "linux"],
    "web": ["darwin", "windows", "linux"],
    "kotlin": ["linux", "windows", "darwin"],
}


def flatten(values: dict[str, Any]) -> dict[str, float]:
    """Nested case values → one flat {path: number} map. Mirrors each edition's own flatten()."""
    flat: dict[str, float] = {}

    def label(item: Any) -> str | None:
        if not isinstance(item, dict):
            return None
        if "role" in item:
            return str(item["role"])
        if "tap" in item:
            return f"tap{item['tap']}"
        if "hz" in item:
            return f"{item['hz']}Hz"
        return None

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("role", "tap", "hz") or key.startswith("_"):
                    continue
                walk(value, f"{path}/{key}")
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}/{label(item) or index}")
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            flat[path] = float(node)

    for block in ("filePlayback", "gatedFft"):
        for name, body in values.get(block, {}).items():
            walk(body, name)
    return flat


def tolerance_class(path: str) -> str | None:
    return TOLERANCE_KEYS.get(path.rsplit("/", 1)[-1])


def load_configurations() -> dict[str, dict[str, Any]]:
    """Every collected baseline, plus the oracle standing in for the canonical configuration."""
    with open(ORACLE_PATH, encoding="utf-8") as fh:
        oracle = decode_nonfinite(json.load(fh))
    # The oracle is the canonical configuration's own baseline as well as the cross-edition
    # contract. Newer mints name the configuration that produced them; older ones predate the
    # field, and the only configuration that has ever minted is this one.
    config = oracle.get("configuration") or {"edition": "swift", "os": "darwin", "arch": "arm64"}
    origin = f"{config['edition']}-{config['os']}-{config['arch']}"
    configs: dict[str, dict[str, Any]] = {
        origin: {
            "values": flatten(oracle),
            "provenance": {"oracleVersion": oracle.get("oracleVersion", "?"),
                           "mintedAt": oracle.get("generatedAt", "?")},
            "isOracle": True,
        }
    }
    if os.path.isdir(BASELINES):
        for name in sorted(os.listdir(BASELINES)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(BASELINES, name), encoding="utf-8") as fh:
                document = decode_nonfinite(json.load(fh))
            configs[name[:-5]] = {
                "values": flatten(document["values"]),
                "provenance": document.get("provenance", {}),
                "isOracle": False,
            }
    return configs


def decode_nonfinite(node: Any) -> Any:
    """JSON has no infinity: every oracle and baseline stores a non-finite number as the STRING
    "-Infinity" / "Infinity" / "NaN" (GFFT4's silence is -inf). Turn them back into floats."""
    if isinstance(node, dict):
        return {k: decode_nonfinite(v) for k, v in node.items()}
    if isinstance(node, list):
        return [decode_nonfinite(v) for v in node]
    if isinstance(node, str) and node in ("-Infinity", "Infinity", "NaN"):
        return float(node.replace("Infinity", "inf").replace("NaN", "nan"))
    return node


def deltas(reference: dict[str, float], other: dict[str, float]) -> dict[str, float]:
    # Equal values differ by exactly 0 — including two equal infinities, whose subtraction is NaN.
    return {p: (0.0 if other[p] == reference[p] else other[p] - reference[p])
            for p in reference if p in other}


def worst_by_class(delta_map: dict[str, float]) -> dict[str, tuple[float, str]]:
    worst: dict[str, tuple[float, str]] = {}
    for path, value in delta_map.items():
        kind = tolerance_class(path)
        if kind is None:
            continue
        if kind not in worst or abs(value) > abs(worst[kind][0]):
            worst[kind] = (value, path)
    return worst


def pairwise(configs: dict[str, dict[str, Any]]) -> list[tuple[str, str, str, dict[str, tuple[float, str]]]]:
    """Every comparable pair, labelled by which single thing differs between them.

    A pair sharing OS and arch isolates the edition; a pair sharing the edition isolates the
    platform. Pairs differing in both are skipped — they measure the sum and explain neither.
    """
    out = []
    names = sorted(configs)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            l_edition, l_os, l_arch = left.split("-", 2)
            r_edition, r_os, r_arch = right.split("-", 2)
            if (l_os, l_arch) == (r_os, r_arch) and l_edition != r_edition:
                label = "EDITION"
            elif l_edition == r_edition and (l_os, l_arch) != (r_os, r_arch):
                label = "PLATFORM"
            else:
                continue
            worst = worst_by_class(deltas(configs[left]["values"], configs[right]["values"]))
            if worst:
                out.append((label, left, right, worst))
    return out


def coverage(configs: dict[str, dict[str, Any]]) -> list[str]:
    have = set(configs)
    missing = []
    for edition, systems in EXPECTED.items():
        for system in systems:
            if not any(k.startswith(f"{edition}-{system}-") for k in have):
                missing.append(f"{edition}-{system}")
    return missing


def main() -> int:
    # Status lines use non-ASCII markers. A Windows console is cp1252 by default and raises
    # UnicodeEncodeError on them, which killed this script at its first status line - on the
    # very platforms it exists to characterise. Same fix as tooling/parity/doc_coverage.py.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbose", action="store_true", help="every value's delta, worst first")
    args = parser.parse_args()

    configs = load_configurations()
    with open(ORACLE_PATH, encoding="utf-8") as fh:
        tolerances = json.load(fh)["tolerances"]
    origin = next(k for k, v in configs.items() if v["isOracle"])
    oracle_values = configs[origin]["values"]

    print("Configurations with a committed baseline")
    print("-" * 78)
    for name, body in configs.items():
        note = "  (the oracle itself)" if body["isOracle"] else ""
        prov = body["provenance"]
        print(f"  {name:<28} {len(body['values']):>4} values  "
              f"minted {prov.get('mintedAt', '?')}{note}")

    missing = coverage(configs)
    if missing:
        print(f"\n⚠️  {len(missing)} configuration(s) have never been minted: {', '.join(missing)}")
        print("   Their regression bar is not in force, and they are absent from every number")
        print("   below — the tolerance this report suggests is only as good as its coverage.")

    print(f"\n\nDistance from the oracle ({origin})")
    print("-" * 78)
    overall: dict[str, tuple[float, str, str]] = {}
    for name, body in configs.items():
        if body["isOracle"]:
            continue
        worst = worst_by_class(deltas(oracle_values, body["values"]))
        if not worst:
            continue
        print(f"\n  {name}")
        for kind in sorted(worst):
            value, path = worst[kind]
            bar = float(tolerances.get(kind, 0))
            share = f"{abs(value) / bar * 100:5.1f}% of bar" if bar else "     no bar"
            print(f"    {kind:<12} worst |Δ| {abs(value):>12.6g}   {share}   {path}")
            if kind not in overall or abs(value) > abs(overall[kind][0]):
                overall[kind] = (value, path, name)

    if not overall:
        print("\n  Nothing to compare yet — collect at least one edition's baseline.")
        return 0

    print("\n\nCandidate tolerance")
    print("-" * 78)
    print("  The bar can be no tighter than the worst delta across every configuration that")
    print("  must pass. These are the measured worsts, with the tolerance in force today.")
    print()
    print(f"  {'class':<12} {'measured worst':>16} {'in force':>12} {'headroom':>12}")
    for kind in sorted(overall):
        value, path, who = overall[kind]
        bar = float(tolerances.get(kind, 0))
        headroom = f"{bar / abs(value):.0f}x" if value else "—"
        print(f"  {kind:<12} {abs(value):>16.6g} {bar:>12g} {headroom:>12}   ({who})")

    print("\n\nEdition effect vs platform effect")
    print("-" * 78)
    print("  Distance from the oracle conflates two things. These separate them: configurations")
    print("  that share an OS and arch differ only by EDITION; those that share an edition differ")
    print("  only by PLATFORM. Whichever dominates is the one that sets the floor under the bar.")
    pairs = pairwise(configs)
    if not pairs:
        print("\n  Not enough configurations yet — needs two that share an OS/arch or an edition.")
    for kind_of_pair, left, right, worst in pairs:
        print(f"\n  {kind_of_pair}: {left} vs {right}")
        for kind in sorted(worst):
            value, path = worst[kind]
            print(f"    {kind:<12} worst |Δ| {abs(value):>14.6g}   {path}")

    print("\n  Headroom is how many times looser the bar is than anything yet observed. A large")
    print("  number is not automatically an invitation to tighten: the bar must still cover")
    print("  configurations nobody has minted, and every one of those is missing from this table.")

    if args.verbose:
        print("\n\nEvery value, worst first")
        print("-" * 78)
        for name, body in configs.items():
            if body["isOracle"]:
                continue
            print(f"\n  {name}")
            rows = sorted(deltas(oracle_values, body["values"]).items(),
                          key=lambda kv: -abs(kv[1]))
            for path, value in rows:
                print(f"    {abs(value):>14.6g}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
