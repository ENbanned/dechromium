#!/usr/bin/env python3
"""Package built Chromium into release archives.

Usage:
    python build/package.py --version 145.0.7632.116
    python build/package.py --version 145.0.7632.116 --platform linux
    python build/package.py --version 145.0.7632.116 --platform win
    python build/package.py --version 145.0.7632.116 --platform all
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

PLATFORMS = {
    "linux": {
        "out_dir": "out/Release",
        "binary": "chrome",
        "asset_platform": "linux-x64",
        "files": [
            "chrome",
            "chrome_100_percent.pak",
            "chrome_200_percent.pak",
            "chrome_crashpad_handler",
            "headless_lib_data.pak",
            "headless_lib_strings.pak",
            "icudtl.dat",
            "libEGL.so",
            "libGLESv2.so",
            "libvk_swiftshader.so",
            "libvulkan.so.1",
            "resources.pak",
            "v8_context_snapshot.bin",
            "vk_swiftshader_icd.json",
        ],
        "globs": ["locales/*.pak", "MEIPreload/*"],
    },
    "win": {
        "out_dir": "out/ReleaseWin",
        "binary": "chrome.exe",
        "asset_platform": "win-x64",
        "files": [
            # Core — chrome.exe is a thin launcher, chrome.dll is the browser
            "chrome.exe",
            "chrome.dll",
            "chrome_elf.dll",
            # No chrome_crashpad_handler.exe on Windows — crash handling is
            # built into chrome.exe via --type=crashpad-handler
            "chrome_proxy.exe",
            "chrome_pwa_launcher.exe",
            "chrome_wer.dll",
            "notification_helper.exe",
            "eventlog_provider.dll",
            # Resources
            "chrome_100_percent.pak",
            "chrome_200_percent.pak",
            "headless_lib_data.pak",
            "headless_lib_strings.pak",
            "headless_command_resources.pak",
            "icudtl.dat",
            "resources.pak",
            # V8 — cross-compiled builds use snapshot_blob.bin, not v8_context_snapshot.bin
            "snapshot_blob.bin",
            # Graphics — ANGLE + SwiftShader + DXC (dawn_use_built_dxc=true for win-x64)
            "libEGL.dll",
            "libGLESv2.dll",
            "d3dcompiler_47.dll",
            "dxcompiler.dll",
            "dxil.dll",
            "vk_swiftshader.dll",
            "vulkan-1.dll",
            "vk_swiftshader_icd.json",
            # First-run suppression — without this Chrome shows import wizard
            "First Run",
            # VC++ runtime — required on machines without Redistributable
            "vcruntime140.dll",
            "vcruntime140_1.dll",
            "msvcp140.dll",
        ],
        "globs": [
            "locales/*.pak",
            "MEIPreload/*",
            "PrivacySandboxAttestationsPreloaded/*",
            "IwaKeyDistribution/*",
            # {version}.manifest — SxS assembly manifest required by chrome.exe
            "*.manifest",
        ],
    },
}

# Patches directory relative to repo root
REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def collect_files(out_path: Path, platform: str) -> list[Path]:
    """Collect all files to include in the archive."""
    info = PLATFORMS[platform]
    files: list[Path] = []

    for name in info["files"]:
        p = out_path / name
        if p.exists():
            files.append(p)
        else:
            print(f"  Warning: {name} not found in {out_path}", file=sys.stderr)

    for pattern in info["globs"]:
        files.extend(sorted(out_path.glob(pattern)))

    return files


def package_platform(
    version: str, platform: str, chromium_src: str, dist_dir: Path
) -> dict | None:
    """Create a tar.gz archive for one platform. Returns asset info dict."""
    info = PLATFORMS[platform]
    out_path = Path(chromium_src) / info["out_dir"]

    binary = out_path / info["binary"]
    if not binary.exists():
        print(f"Skipping {platform}: {binary} not found", file=sys.stderr)
        return None

    asset_plat = info["asset_platform"]
    archive_name = f"dechromium-chromium-{version}-{asset_plat}.tar.gz"
    archive_path = dist_dir / archive_name

    print(f"Packaging {platform} ({asset_plat})...")
    files = collect_files(out_path, platform)

    with tarfile.open(archive_path, "w:gz") as tar:
        for f in files:
            arcname = f.relative_to(out_path)
            tar.add(f, arcname=str(arcname))
            print(f"  + {arcname}")

    sha = sha256_file(archive_path)
    size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"  -> {archive_name} ({size_mb:.1f} MB, sha256:{sha[:16]}...)")

    return {
        "platform": asset_plat,
        "archive": archive_name,
        "sha256": sha,
        "size": archive_path.stat().st_size,
    }


def get_patch_list(version: str) -> list[str]:
    """List patch names for a version."""
    patches_dir = REPO_ROOT / "patches" / version
    if not patches_dir.is_dir():
        return []
    patches = sorted(p.stem for p in patches_dir.glob("*.patch"))
    return patches


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Chromium for release")
    parser.add_argument("--version", required=True, help="Chromium version (e.g. 145.0.7632.116)")
    parser.add_argument(
        "--platform",
        choices=["linux", "win", "all"],
        default="all",
        help="Platform to package (default: all)",
    )
    args = parser.parse_args()

    chromium_src = os.environ.get("CHROMIUM_SRC")
    if not chromium_src:
        print("ERROR: Set CHROMIUM_SRC to your chromium/src directory", file=sys.stderr)
        sys.exit(1)

    dist_dir = REPO_ROOT / "build" / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    platforms = list(PLATFORMS.keys()) if args.platform == "all" else [args.platform]
    assets = []
    for plat in platforms:
        result = package_platform(args.version, plat, chromium_src, dist_dir)
        if result:
            assets.append(result)

    if not assets:
        print("ERROR: No platforms were packaged successfully", file=sys.stderr)
        sys.exit(1)

    # Build manifest
    from dechromium import __version__ as lib_version

    manifest = {
        "chromium_version": args.version,
        "min_library": lib_version,
        "patches": get_patch_list(args.version),
        "assets": {
            a["platform"]: {"sha256": a["sha256"], "archive": a["archive"]} for a in assets
        },
    }

    manifest_path = dist_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nManifest written to {manifest_path}")
    print(f"Archives in {dist_dir}:")
    for a in assets:
        print(f"  {a['archive']}")


if __name__ == "__main__":
    main()
