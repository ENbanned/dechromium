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

# Rename: git format-patch outputs 0001-name.patch, 0002-name.patch, etc.
# Commits are named like "001-aspect-infrastructure", so format-patch produces
# "0001-001-aspect-infrastructure.patch". Strip only the format-patch prefix.
cd "$PATCHES_DIR"
for f in *.patch; do
    [ -f "$f" ] || continue
    # Remove the 4-digit format-patch prefix (e.g. "0001-" → keep "001-name.patch")
    new=$(echo "$f" | sed 's/^[0-9]\{4\}-//')
    mv "$f" "$new"
done

echo "Exported patches to $PATCHES_DIR:"
ls -1 "$PATCHES_DIR"/*.patch
