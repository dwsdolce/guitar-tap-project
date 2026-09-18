#!/usr/bin/env python3
"""Collect each edition's self-baseline into the hub, where the parity arithmetic can see them.

    ./tooling/collect-baselines.py ~/src/guitar_tap ~/src/GuitarTapWeb ~/src/GuitarTap

A self-baseline is minted by one configuration and read by that same configuration, so it
lives beside that repo's tests and the suite needs no hub checkout to run. This is the other
direction: the hub is a *collection point*, downstream of the repos, and the only place that
sees every configuration at once. The oracle flows the opposite way — hub to repos — which is
why this is a separate script rather than a mode of sync-oracle.sh.

Nothing here needs to know how any repo is laid out: each baseline file declares its own
configuration, so the destination name comes from the file's contents, not from its path.
"""

from __future__ import annotations

import json
import os
import shutil
import sys

HUB = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(HUB, "tooling", "parity", "baselines")

# The canonical Swift edition's baseline IS the oracle — it minted it — so it is collected
# from there rather than from a separate file that would only ever be a copy.
ORACLE = os.path.join(HUB, "tooling", "parity", "parity-oracle.json")


def find_baselines(root: str) -> list[str]:
    found = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", ".venv", "build")]
        for name in filenames:
            if name.startswith("self-baseline-") and name.endswith(".json"):
                found.append(os.path.join(directory, name))
    return sorted(found)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    os.makedirs(DEST, exist_ok=True)
    collected = 0
    for root in argv:
        root = os.path.expanduser(root)
        if not os.path.isdir(root):
            print(f"⚠️  not a directory, skipped: {root}")
            continue
        for path in find_baselines(root):
            with open(path, encoding="utf-8") as fh:
                document = json.load(fh)
            config = document.get("configuration")
            if not config:
                print(f"⚠️  no configuration block, skipped: {path}")
                continue
            name = f"{config['edition']}-{config['os']}-{config['arch']}.json"
            shutil.copyfile(path, os.path.join(DEST, name))
            minted = document.get("provenance", {}).get("mintedAt", "?")
            print(f"✅ {name:<34} ← {path}   (minted {minted})")
            collected += 1
    print(f"\n{collected} baseline(s) collected into {DEST}")
    print("Commit them, then run ./tooling/parity-report.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
