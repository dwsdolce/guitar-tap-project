#!/usr/bin/env bash
# Copy the export checker into each edition, or check that each edition's copy is identical.
#
#   tooling/export-check/sync.sh           copy the hub's checker into the three editions
#   tooling/export-check/sync.sh --check   exit non-zero if any edition's copy differs
#
# The hub holds the source of truth; each edition runs its own copy, without the hub. The editions are
# found beside the hub (override with GT_SRC): GuitarTap, guitar_tap, GuitarTapWeb.

set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
src="${GT_SRC:-$(cd "$here/../../.." && pwd)}"
files=(check_exports.py expected.json tolerances.json requirements.txt README.md)
dests=("$src/GuitarTap/Tooling/export-check" "$src/guitar_tap/Tooling/export-check" "$src/GuitarTapWeb/tooling/export-check")

status=0
for dest in "${dests[@]}"; do
    for f in "${files[@]}"; do
        if [[ "${1:-}" == "--check" ]]; then
            if ! cmp -s "$here/$f" "$dest/$f"; then
                echo "differs: $dest/$f"
                status=1
            fi
        else
            mkdir -p "$dest"
            cp "$here/$f" "$dest/$f"
        fi
    done
done
[[ "${1:-}" == "--check" && $status -eq 0 ]] && echo "export checker: all three copies match the hub"
[[ "${1:-}" != "--check" ]] && echo "export checker copied into ${#dests[@]} editions"
exit $status
