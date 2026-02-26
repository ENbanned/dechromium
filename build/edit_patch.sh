#!/bin/bash
set -e

CHROMIUM_SRC="${CHROMIUM_SRC:?Set CHROMIUM_SRC to your chromium/src directory}"
BASE_TAG="${1:-145.0.7632.116}"

cd "$CHROMIUM_SRC"

current=$(git branch --show-current)
if [ "$current" != "aspect" ]; then
    echo "ERROR: not on aspect branch (current: $current)"
    exit 1
fi

echo "Opening interactive rebase from $BASE_TAG..."
echo "Mark the commit you want to edit as 'edit', save and close."
echo ""
git rebase -i "$BASE_TAG"
