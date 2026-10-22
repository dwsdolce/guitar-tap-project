#!/usr/bin/env python3
"""The editions this project keeps at parity — declared once, used by every parity tool.

Before this file existed the platform list was written out separately in `gen_parity_map.py`,
`parity_lookup.py`, `doc_coverage.py` and `guitartap_matrix.py`, so adding an edition meant
finding four hard-coded triples (plus a literal `len(pres) == 3`). Everything now reads this
table.

**Active vs declared.** An edition is *declared* here as soon as its repo is planned, but it is
only *active* once its repo exists on disk AND some file in it carries an `@parity` tag. Tools
render columns for active editions only, so declaring a new one changes no output until its first
tagged file lands — which is why adding Android here leaves the generated map byte-identical
today. `is_active()` is the test.

Repo roots are overridable with the environment variables named below, for a checkout that does
not sit beside the hub.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parents[2]   # …/tooling/parity/ -> …/guitar-tap-project
SRC = HUB_ROOT.parent                            # …/src — the code repos are siblings of the hub


@dataclass(frozen=True)
class Platform:
    """One edition: where its code lives, what it is written in, how it documents itself."""
    key: str                       # column key in PARITY-MAP.md / parity-index.json
    label: str                     # column heading
    repo: str                      # sibling directory name
    env: str                       # environment variable overriding the repo root
    exts: frozenset[str]           # source extensions scanned for @parity tags
    doc_style: str                 # doc_coverage.py analyzer: docc | docstring | tsdoc | kdoc
    matrix_token: str              # platform token in Tests/AllPlatforms capture filenames
    canonical: bool = False        # Swift is the reference the others mirror
    doc_root: str = ""             # subdirectory doc_coverage.py scans, "" = repo root
    fixtures: str = ""             # where this edition keeps the shared test fixtures
    code_dirs: tuple[str, ...] = ()  # source directories whose every file is in a group or `@parity none`
    test_dirs: tuple[str, ...] = ()  # test directories whose every file is in a group or `@parity none`

    @property
    def root(self) -> Path:
        return Path(os.environ.get(self.env, SRC / self.repo))

    def is_active(self) -> bool:
        """Present on disk and carrying at least one @parity tag (see module docstring)."""
        root = self.root
        if not root.is_dir():
            return False
        return _has_parity_tag(root, self.exts)


PLATFORMS: tuple[Platform, ...] = (
    Platform("swift", "Swift", "GuitarTap", "PARITY_SWIFT", frozenset({".swift", ".py"}),
             "docc", "swift", canonical=True, fixtures="GuitarTapTests",
             code_dirs=("GuitarTap",), test_dirs=("GuitarTapTests", "GuitarTapUITests")),
    Platform("python", "Python", "guitar_tap", "PARITY_PYTHON", frozenset({".py"}),
             "docstring", "python", fixtures="tests",
             code_dirs=("src/guitar_tap",), test_dirs=("tests",)),
    Platform("web", "Web", "GuitarTapWeb", "PARITY_WEB",
             frozenset({".ts", ".tsx", ".js", ".css"}), "tsdoc", "web", doc_root="src",
             fixtures="test/fixtures",
             code_dirs=("src",), test_dirs=("test", "e2e")),
    # Declared ahead of its first tagged file — see "Active vs declared" above.
    Platform("android", "Android", "GuitarTapAndroid", "PARITY_ANDROID",
             frozenset({".kt", ".kts"}), "kdoc", "android",
             fixtures="core/src/test/resources"),
)

KEYS: tuple[str, ...] = tuple(p.key for p in PLATFORMS)
BY_KEY: dict[str, Platform] = {p.key: p for p in PLATFORMS}

# Directories never scanned, in any edition.
SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".build", "DerivedData",
    "__pycache__", "Pods", ".venv", "venv", "coverage", ".vite", ".idea",
    ".gradle", ".kotlin",              # Gradle/Kotlin build state (Android)
    # The parity tooling itself carries example `@parity` tags in its docstrings. Skip any
    # `parity` tooling dir in every scanned repo (not just this hub copy) so a still-present
    # copy in a code repo can't pollute the map.
    "parity",
}

ALL_EXTS: frozenset[str] = frozenset().union(*(p.exts for p in PLATFORMS))

_TAG = "@parity"
_active_cache: dict[str, bool] = {}


def _has_parity_tag(root: Path, exts: frozenset[str]) -> bool:
    key = str(root)
    if key in _active_cache:
        return _active_cache[key]
    found = False
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if Path(name).suffix not in exts:
                continue
            try:
                if _TAG in Path(dirpath, name).read_text(encoding="utf-8", errors="ignore"):
                    found = True
                    break
            except OSError:
                continue
        if found:
            break
    _active_cache[key] = found
    return found


def active() -> tuple[Platform, ...]:
    """Editions with a repo on disk and at least one @parity tag."""
    return tuple(p for p in PLATFORMS if p.is_active())


def active_keys() -> tuple[str, ...]:
    return tuple(p.key for p in active())


def describe() -> str:
    """One line per edition, for tool banners and --platforms output."""
    out = []
    for p in PLATFORMS:
        state = "active" if p.is_active() else ("no @parity tags yet" if p.root.is_dir() else "repo not present")
        out.append(f"  {p.key:<8} {p.label:<8} {p.repo:<18} {state}")
    return "\n".join(out)


if __name__ == "__main__":
    print("editions declared in tooling/parity/platforms.py:\n" + describe())
