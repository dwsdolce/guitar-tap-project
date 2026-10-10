#!/usr/bin/env python3
"""Regenerate the colour-role tables in the three palette modules from the shared theme.json.

The role table (docs/THEME-SPEC.md §5) lives in tooling/parity/cases/theme.json; each edition holds the same
roles in its palette module, checked by its theme test. This rewrites the generated blocks so a role added to
theme.json reaches all three editions identically:

  Swift  GuitarTap/Views/Utilities/Palette.swift   — `enum Role` cases and the `pairs` table
  Python src/guitar_tap/views/utilities/palette.py — `class Role` members and the `PAIRS` table
  web    src/presentation/palette.ts               — the `ROLES` table

    .venv/bin/python tooling/parity/gen_palette_tables.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import platforms  # noqa: E402

THEME = Path(__file__).resolve().parent / "cases" / "theme.json"


def swift_name(role: str) -> str:
    segments = role.split(".")
    return segments[0] + "".join(s[0].upper() + s[1:] for s in segments[1:])


def python_name(role: str) -> str:
    return "_".join(re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", s).upper() for s in role.split("."))


def replace_block(text: str, pattern: str, body: str, path: Path) -> str:
    new, n = re.subn(pattern, lambda m: m.group(1) + body + m.group(3), text, count=1, flags=re.S)
    if n != 1:
        sys.exit(f"{path}: generated block not found ({pattern[:40]}…)")
    return new


def main() -> int:
    roles = json.loads(THEME.read_text())["roles"]
    roots = {p.key: p.root for p in platforms.PLATFORMS}

    swift = roots["swift"] / "GuitarTap/Views/Utilities/Palette.swift"
    s = swift.read_text()
    s = replace_block(s, r"(    enum Role: String, CaseIterable \{\n)(.*?)(\n    \}\n)",
                      "\n".join(f'        case {swift_name(n)} = "{n}"' for n, _, _ in roles), swift)
    s = replace_block(s, r"(    static let pairs: \[Role: Pair\] = \[\n)(.*?)(\n    \]\n)",
                      "\n".join(f'        .{swift_name(n)}: Pair(light: "{l}", dark: "{d}"),'
                                for n, l, d in roles).rstrip(","), swift)
    swift.write_text(s)

    python = roots["python"] / "src/guitar_tap/views/utilities/palette.py"
    s = python.read_text()
    s = replace_block(s, r'(class Role\(Enum\):\n    """[^"]*"""\n\n)(.*?)(\n\n\nclass Opacity)',
                      "\n".join(f'    {python_name(n)} = "{n}"' for n, _, _ in roles), python)
    s = replace_block(s, r"(PAIRS: dict\[Role, ColorPair\] = \{\n)(.*?)(\n\}\n)",
                      "\n".join(f'    Role.{python_name(n)}: ColorPair("{l}", "{d}"),' for n, l, d in roles),
                      python)
    python.write_text(s)

    web = roots["web"] / "src/presentation/palette.ts"
    s = web.read_text()
    s = replace_block(s, r"(export const ROLES = \{\n)(.*?)(\n\} as const satisfies Record<string, ColorPair>)",
                      "\n".join(f"  '{n}': {{ light: '{l}', dark: '{d}' }}," for n, l, d in roles), web)
    web.write_text(s)

    print(f"wrote {len(roles)} roles to the Swift, Python and web palettes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
