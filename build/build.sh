#!/bin/bash
set -e

CHROMIUM_SRC="${CHROMIUM_SRC:?Set CHROMIUM_SRC to your chromium/src directory}"

cd "$CHROMIUM_SRC"

current=$(git branch --show-current)
if [ "$current" != "aspect" ]; then
    echo "ERROR: not on aspect branch (current: $current)"
    exit 1
fi

echo "Building chrome..."
autoninja -C out/Release chrome -j$(nproc)
echo "Build complete: out/Release/chrome"
