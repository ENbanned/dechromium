#!/usr/bin/env python3
"""Build patched Chromium for one or more platforms.

Usage:
    python build/build_chromium.py --platform linux
    python build/build_chromium.py --platform win
    python build/build_chromium.py --platform all --jobs 24
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

PLATFORMS = {
    "linux": {"out_dir": "out/Release", "target": "chrome"},
    "win": {"out_dir": "out/ReleaseWin", "target": "chrome"},
}


def get_chromium_src() -> str:
    src = os.environ.get("CHROMIUM_SRC")
    if not src:
        print("ERROR: Set CHROMIUM_SRC to your chromium/src directory", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(src):
        print(f"ERROR: CHROMIUM_SRC={src} is not a directory", file=sys.stderr)
        sys.exit(1)
    return src


def check_branch(src: str) -> None:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=src,
        capture_output=True,
        text=True,
    )
    branch = result.stdout.strip()
    if branch != "aspect":
        print(f"ERROR: not on aspect branch (current: {branch})", file=sys.stderr)
        sys.exit(1)


def build_platform(src: str, platform: str, jobs: int) -> None:
    info = PLATFORMS[platform]
    out_dir = info["out_dir"]
    target = info["target"]

    print(f"Building {target} for {platform} in {out_dir}...")
    cmd = ["autoninja", "-C", out_dir, target, f"-j{jobs}"]
    result = subprocess.run(cmd, cwd=src)
    if result.returncode != 0:
        print(f"ERROR: {platform} build failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"Build complete: {out_dir}/{target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build patched Chromium")
    parser.add_argument(
        "--platform",
        choices=["linux", "win", "all"],
        default="linux",
        help="Target platform (default: linux)",
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=os.cpu_count() or 8,
        help="Parallel build jobs (default: CPU count)",
    )
    args = parser.parse_args()

    src = get_chromium_src()
    check_branch(src)

    platforms = list(PLATFORMS.keys()) if args.platform == "all" else [args.platform]
    for plat in platforms:
        build_platform(src, plat, args.jobs)


if __name__ == "__main__":
    main()
