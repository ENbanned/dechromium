#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHROMIUM_SRC="${CHROMIUM_SRC:?Set CHROMIUM_SRC to your chromium/src directory}"
BASE_TAG="${1:-145.0.7632.116}"
PATCHES_DIR="$REPO_DIR/patches/$BASE_TAG"

cd "$CHROMIUM_SRC"

current=$(git branch --show-current)
if [ "$current" != "aspect" ]; then
    echo "ERROR: not on aspect branch (current: $current)"
    exit 1
fi

mkdir -p "$PATCHES_DIR"
rm -f "$PATCHES_DIR"/*.patch
git format-patch "$BASE_TAG"..aspect -o "$PATCHES_DIR"

cd "$PATCHES_DIR"
for f in *.patch; do
    [ -f "$f" ] || continue
    new=$(echo "$f" | sed 's/^[0-9]*-//')
    mv "$f" "$new"
done

echo "Exported patches to $PATCHES_DIR:"
ls -1 "$PATCHES_DIR"/*.patch
