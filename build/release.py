#!/usr/bin/env python3
"""Upload packaged Chromium to GitHub Releases.

Usage:
    python build/release.py --version 145.0.7632.116
    python build/release.py --version 145.0.7632.116 --draft
    python build/release.py --version 145.0.7632.116 --clobber
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "build" / "dist"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def release_exists(tag: str) -> bool:
    result = run(["gh", "release", "view", tag], check=False)
    return result.returncode == 0


def get_patch_list(version: str) -> list[str]:
    patches_dir = REPO_ROOT / "patches" / version
    if not patches_dir.is_dir():
        return []
    return sorted(p.stem for p in patches_dir.glob("*.patch"))


def build_release_body(version: str, manifest: dict) -> str:
    lines = [f"## Chromium {version} (patched)\n"]

    patches = manifest.get("patches", []) or get_patch_list(version)
    if patches:
        lines.append("### Patches applied")
        for p in patches:
            lines.append(f"- `{p}`")
        lines.append("")

    assets = manifest.get("assets", {})
    if assets:
        lines.append("### Platforms")
        for plat, info in assets.items():
            lines.append(f"- **{plat}**: `{info['archive']}`")
        lines.append("")

    min_lib = manifest.get("min_library", "")
    if min_lib:
        lines.append(f"Requires `dechromium >= {min_lib}`\n")

    lines.append("```bash")
    lines.append("pip install dechromium")
    lines.append("dechromium install")
    lines.append("```")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload Chromium release to GitHub")
    parser.add_argument("--version", required=True, help="Chromium version")
    parser.add_argument("--draft", action="store_true", help="Create as draft release")
    parser.add_argument(
        "--clobber", action="store_true", help="Re-upload assets to existing release"
    )
    args = parser.parse_args()

    tag = f"chromium-{args.version}"

    # Collect assets
    manifest_path = DIST_DIR / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found. Run package.py first.", file=sys.stderr)
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text())
    upload_files: list[Path] = [manifest_path]

    for _plat, info in manifest.get("assets", {}).items():
        archive = DIST_DIR / info["archive"]
        if not archive.exists():
            print(f"ERROR: {archive} not found", file=sys.stderr)
            sys.exit(1)
        upload_files.append(archive)

    print(f"Release: {tag}")
    print(f"Assets: {[f.name for f in upload_files]}")

    exists = release_exists(tag)

    if exists and not args.clobber:
        print(f"ERROR: Release {tag} already exists. Use --clobber to re-upload.", file=sys.stderr)
        sys.exit(1)

    if exists and args.clobber:
        # Delete existing assets and re-upload
        print(f"Clobbering existing release {tag}...")
        for f in upload_files:
            run(["gh", "release", "delete-asset", tag, f.name, "--yes"], check=False)
        upload_cmd = ["gh", "release", "upload", tag]
        upload_cmd.extend(str(f) for f in upload_files)
        result = run(upload_cmd)
        if result.returncode != 0:
            print(f"ERROR: Upload failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
    else:
        # Create new release
        body = build_release_body(args.version, manifest)
        create_cmd = [
            "gh",
            "release",
            "create",
            tag,
            "--title",
            f"Chromium {args.version}",
            "--notes",
            body,
        ]
        if args.draft:
            create_cmd.append("--draft")
        create_cmd.extend(str(f) for f in upload_files)

        result = run(create_cmd)
        if result.returncode != 0:
            print(f"ERROR: Release creation failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)

    print(f"\nRelease {tag} {'updated' if exists else 'created'} successfully!")
    view = run(["gh", "release", "view", tag, "--json", "url"], check=False)
    if view.returncode == 0:
        url = json.loads(view.stdout).get("url", "")
        if url:
            print(f"  {url}")


if __name__ == "__main__":
    main()
