#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CHROMIUM_SRC="${CHROMIUM_SRC:?Set CHROMIUM_SRC to your chromium/src directory}"
BASE_TAG="${1:-145.0.7632.116}"
PATCHES_DIR="$REPO_DIR/patches/$BASE_TAG"

if [ ! -d "$PATCHES_DIR" ]; then
    echo "ERROR: patches not found: $PATCHES_DIR"
    exit 1
fi

cd "$CHROMIUM_SRC"

echo "Resetting to $BASE_TAG..."
git checkout -B aspect "$BASE_TAG"

echo "Applying patches..."
git am "$PATCHES_DIR"/*.patch

echo ""
echo "Applied commits:"
git log --oneline "$BASE_TAG"..aspect
