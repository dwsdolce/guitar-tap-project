#!/usr/bin/env python3
"""Check that the test fixtures shared between editions are byte-identical.

Each edition keeps its own copy of the shared fixtures — the WAV recordings the playback
regression tests replay, the UMIK-1 `.cal` file, the `.guitartap` files decoded by the codec
tests. Nothing kept them in step: they were copied by hand, and `test/peaks` asserts in three
repos that the files are identical without ever checking it. They did drift — `7108913.txt` was
CRLF in Swift and Python and LF in the web repo until 2026-09-15, so the three copies had
different bytes while every suite passed.

This compares every fixture that appears in more than one edition by SHA-256 and reports any
that disagree. It is read-only by default; `--adopt <edition>` copies that edition's copy of a
named fixture over the others, which is the only way a fixture should ever be "synced".

    python3 tooling/check-fixtures.py                  # report drift (exit 1 if any)
    python3 tooling/check-fixtures.py --list           # list every shared fixture and its editions
    python3 tooling/check-fixtures.py --adopt swift 7108913.txt

Fixture directories are declared per edition in tooling/parity/platforms.py.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "parity"))
import platforms  # noqa: E402

# Only these are shared contracts. Source files, snapshots and per-edition scratch are not.
FIXTURE_EXT = {".wav", ".guitartap", ".txt", ".cal", ".json"}
# Generated or edition-local files that legitimately differ / are not shared fixtures.
IGNORE_NAMES = {"parity-oracle.json", "package.json", "tsconfig.json"}
# Each edition's own regression baselines (test/self-regression): one per edition per machine, each minted
# from that edition's output, so the same name in two editions is two different files by design.
IGNORE_PREFIXES = ("self-baseline-",)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect() -> dict[str, dict[str, Path]]:
    """basename -> {edition key: path}, for every fixture-looking file in a declared dir."""
    found: dict[str, dict[str, Path]] = defaultdict(dict)
    for plat in platforms.PLATFORMS:
        if not plat.fixtures:
            continue
        root = plat.root / plat.fixtures
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in FIXTURE_EXT:
                continue
            if path.name in IGNORE_NAMES or path.name.startswith(IGNORE_PREFIXES):
                continue
            found[path.name][plat.key] = path
    return found


def main() -> int:
    args = sys.argv[1:]
    found = collect()
    shared = {name: locs for name, locs in found.items() if len(locs) > 1}

    if "--list" in args:
        print(f"{len(shared)} fixture(s) shared by more than one edition:")
        for name in sorted(shared):
            print(f"  {name:<50} {', '.join(sorted(shared[name]))}")
        return 0

    if "--adopt" in args:
        i = args.index("--adopt")
        try:
            source, name = args[i + 1], args[i + 2]
        except IndexError:
            sys.exit("usage: --adopt <edition> <fixture-name>")
        locs = shared.get(name) or found.get(name) or {}
        if source not in locs:
            sys.exit(f"{name} not found in edition '{source}' (have: {', '.join(sorted(locs)) or 'none'})")
        src = locs[source]
        for key, dest in sorted(locs.items()):
            if key == source:
                continue
            shutil.copyfile(src, dest)
            print(f"  {key}: overwritten from {source}  ({dest})")
        print(f"adopted {source}'s {name} — review and commit in each repo")
        return 0

    drift = []
    for name, locs in sorted(shared.items()):
        digests = {key: sha(path) for key, path in locs.items()}
        if len(set(digests.values())) > 1:
            drift.append((name, locs, digests))

    print(f"shared fixtures: {len(shared)} (of {len(found)} fixture files across "
          f"{sum(1 for p in platforms.PLATFORMS if p.fixtures and (p.root / p.fixtures).is_dir())} editions)")
    if not drift:
        print("all shared fixtures are byte-identical across the editions that hold them.")
        return 0

    print(f"\nDRIFT: {len(drift)} fixture(s) differ between editions:", file=sys.stderr)
    for name, locs, digests in drift:
        print(f"  {name}", file=sys.stderr)
        for key in sorted(locs):
            size = locs[key].stat().st_size
            print(f"    {key:<8} {digests[key][:16]}  {size:>9} bytes  {locs[key]}", file=sys.stderr)
        print(f"    fix with: python3 tooling/check-fixtures.py --adopt <edition> {name}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
