#!/bin/bash
set -e

CHROMIUM_SRC="${CHROMIUM_SRC:?Set CHROMIUM_SRC to your chromium/src directory}"

cd "$CHROMIUM_SRC"

current=$(git branch --show-current)
if [ "$current" != "aspect" ]; then
    echo "ERROR: not on aspect branch (current: $current)"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: new_patch.sh <patch-name>"
    echo "Example: new_patch.sh 012-timezone-locale"
    exit 1
fi

git add -A
git commit -m "$1" --no-verify
echo "Created commit: $1"
echo "Run export_patches.sh to update patch files"
