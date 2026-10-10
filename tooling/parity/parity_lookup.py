#!/usr/bin/env python3
"""Browse the parity map: given a reference in any platform, show its counterparts.

Reads `parity-index.json` (produced by gen_parity_map.py) and prints every group
whose slug or any path contains the query substring (case-insensitive). This is
the "stand on a symbol in platform x, find y and z" utility — the query doesn't
care which platform the match came from.

    .venv/bin/python tooling/parity/parity_lookup.py classify
    .venv/bin/python tooling/parity/parity_lookup.py gated-fft --sort=web
    .venv/bin/python tooling/parity/parity_lookup.py .           # list everything (sorted)

--sort picks the browse order (slug, or any edition key from platforms.py); default is slug.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import platforms

SCRIPT = Path(__file__).resolve()
SELF_DIR = SCRIPT.parent
INDEX_JSON = SELF_DIR / "parity-index.json"         # tooling/parity/parity-index.json, beside gen_parity_map.py's output
# Editions come from platforms.py; the index only carries keys for the ones that were active
# when it was generated, so read the record rather than assuming a fixed set.
PLATFORMS = platforms.KEYS


def load() -> dict:
    if not INDEX_JSON.exists():
        sys.exit(f"no parity-index.json at {INDEX_JSON} — run gen_parity_map.py first")
    return json.loads(INDEX_JSON.read_text(encoding="utf-8"))


def matches(group: dict, needle: str) -> bool:
    if needle in group["slug"].lower():
        return True
    return any(needle in p.lower() for plat in PLATFORMS for p in group.get(plat) or [])


def sort_key(group: dict, field: str):
    if field == "slug":
        return group["slug"]
    paths = group.get(field) or []
    # Groups missing the sort platform sink to the bottom, then by slug.
    return (not paths, paths[0] if paths else "", group["slug"])


def fmt(paths: list[str]) -> str:
    return ", ".join(paths) if paths else "—"


def main() -> int:
    ap = argparse.ArgumentParser(description="Look up parity counterparts by substring.")
    ap.add_argument("query", help="substring to match against slug or any path ('.' = all)")
    ap.add_argument("--sort", choices=("slug", *PLATFORMS), default="slug")
    args = ap.parse_args()

    data = load()
    needle = "" if args.query == "." else args.query.lower()
    hits = [g for g in data.get("groups", []) if not needle or matches(g, needle)]
    hits.sort(key=lambda g: sort_key(g, args.sort))

    if not hits:
        print(f"no parity group matches '{args.query}'")
        return 1

    for g in hits:
        print(g["slug"])
        for plat in PLATFORMS:
            if plat not in g:
                continue          # edition not yet active when the index was generated
            print(f"  {plat:7} {fmt(g.get(plat) or [])}")
    print(f"\n{len(hits)} group(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())