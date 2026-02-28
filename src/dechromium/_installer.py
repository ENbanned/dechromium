"""Download and manage patched Chromium browser installations."""

from __future__ import annotations

import contextlib
import hashlib
import json
import platform
import shutil
import sys
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from dechromium._config import _default_data_dir
from dechromium._exceptions import DechromiumError

GITHUB_REPO = "ENbanned/dechromium"

_CHROME_BIN = "chrome.exe" if sys.platform == "win32" else "chrome"


class InstallError(DechromiumError):
    """Raised when Chromium installation fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        arch = "x64" if machine in ("x86_64", "amd64") else machine
        return f"linux-{arch}"
    if system == "darwin":
        arch = "arm64" if machine == "arm64" else "x64"
        return f"macos-{arch}"
    if system == "windows":
        arch = "x64" if machine in ("amd64", "x86_64") else machine
        return f"win-{arch}"

    return f"{system}-{machine}"


def _asset_name(version: str, plat: str) -> str:
    return f"dechromium-chromium-{version}-{plat}.tar.gz"


def _fetch_json(url: str) -> dict | list:
    req = Request(url, headers={"Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _download(url: str, dest: Path, *, progress: bool = True) -> None:
    req = Request(url, headers={"Accept": "application/octet-stream"})
    with urlopen(req, timeout=300) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            while chunk := resp.read(1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if progress and total:
                    pct = downloaded * 100 // total
                    print(f"\r  Downloading... {pct}%", end="", flush=True)
        if progress and total:
            print()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def _version_key(v: str) -> tuple[int, ...]:
    parts = []
    for x in v.split("."):
        try:
            parts.append(int(x))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _find_asset(release: dict, name: str) -> dict | None:
    for a in release.get("assets", []):
        if a["name"] == name:
            return a
    return None


def _check_compat(manifest: dict) -> None:
    """Warn if this Chromium version needs a newer library. May raise."""
    min_lib = manifest.get("min_library")
    if not min_lib:
        return
    from dechromium import __version__

    if _version_key(__version__) < _version_key(min_lib):
        print(
            f"  Warning: requires dechromium >= {min_lib} "
            f"(you have {__version__}). Run: pip install --upgrade dechromium"
        )


# ---------------------------------------------------------------------------
# BrowserManager
# ---------------------------------------------------------------------------


class BrowserManager:
    """Manage patched Chromium browser installations."""

    def __init__(self, data_dir: Path | None = None):
        self._data_dir = data_dir or _default_data_dir()
        self._browsers_dir = self._data_dir / "browsers"

    # -- queries -----------------------------------------------------------

    @staticmethod
    def available() -> list[str]:
        """List Chromium versions available on GitHub."""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        try:
            releases = _fetch_json(url)
        except (HTTPError, OSError):
            return []
        versions = []
        for rel in releases:
            tag = rel.get("tag_name", "")
            if tag.startswith("chromium-"):
                versions.append(tag.removeprefix("chromium-"))
        return versions

    def installed(self) -> list[dict]:
        """List locally installed browser versions.

        Returns list of dicts: ``{"version": str, "manifest": dict | None}``.
        Sorted newest-first.
        """
        if not self._browsers_dir.is_dir():
            return []
        results = []
        for d in self._browsers_dir.iterdir():
            if d.is_dir() and (d / _CHROME_BIN).exists():
                manifest = self._read_manifest(d.name)
                results.append({"version": d.name, "manifest": manifest})
        results.sort(key=lambda e: _version_key(e["version"]), reverse=True)
        return results

    def resolve_latest_remote(self) -> str:
        """Query GitHub for the latest chromium-* release version."""
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        releases = _fetch_json(url)
        for rel in releases:
            tag = rel.get("tag_name", "")
            if tag.startswith("chromium-"):
                return tag.removeprefix("chromium-")
        raise InstallError(
            f"No Chromium releases found at https://github.com/{GITHUB_REPO}/releases"
        )

    def resolve_latest_local(self) -> Path | None:
        """Return path to the latest installed chrome binary, or None."""
        entries = self.installed()
        if entries:
            return self._browsers_dir / entries[0]["version"] / _CHROME_BIN
        return None

    # -- install -----------------------------------------------------------

    def install(
        self,
        version: str | None = None,
        *,
        force: bool = False,
        progress: bool = True,
    ) -> Path:
        """Download and install patched Chromium.

        Args:
            version: Chromium version. If None, installs the latest from GitHub.
            force: Re-download even if already installed and up-to-date.
            progress: Show progress output.

        Returns:
            Path to the installed chrome binary.
        """
        if version is None:
            if progress:
                print("Checking for latest Chromium release...")
            version = self.resolve_latest_remote()

        dest = self._browsers_dir / version
        plat = _detect_platform()
        asset_name_str = _asset_name(version, plat)

        if progress:
            print(f"Installing Chromium {version} ({plat})...")

        # Fetch release from GitHub
        try:
            release = self._get_release(version)
        except HTTPError as exc:
            raise InstallError(
                f"Chromium {version} not found on GitHub. "
                f"Check https://github.com/{GITHUB_REPO}/releases"
            ) from exc
        except OSError as exc:
            raise InstallError(f"Failed to reach GitHub API: {exc}") from exc

        # Find binary asset
        binary_asset = _find_asset(release, asset_name_str)
        if not binary_asset:
            available = [a["name"] for a in release.get("assets", [])]
            raise InstallError(f"No binary for platform '{plat}'. Available: {available}")

        # Fetch remote manifest.json (optional, for compat check + sha256)
        remote_manifest: dict = {}
        manifest_asset = _find_asset(release, "manifest.json")
        if manifest_asset:
            with contextlib.suppress(Exception):
                req = Request(manifest_asset["browser_download_url"])
                with urlopen(req, timeout=10) as resp:
                    remote_manifest = json.loads(resp.read())

        # Compatibility warning (best-effort, doesn't block)
        with contextlib.suppress(Exception):
            _check_compat(remote_manifest)

        # Already up-to-date?
        asset_updated = binary_asset.get("updated_at", "")
        if not force:
            local = self._read_manifest(version)
            if local and local.get("asset_updated_at") == asset_updated:
                if progress:
                    print(f"  Chromium {version} is already up to date.")
                return dest / _CHROME_BIN

        # Download
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / asset_name_str
            try:
                _download(binary_asset["browser_download_url"], archive, progress=progress)
            except OSError as exc:
                raise InstallError(f"Download failed: {exc}") from exc

            # Verify sha256 if manifest provides it (supports both flat and per-platform)
            expected_sha = remote_manifest.get("sha256")
            if not expected_sha:
                assets = remote_manifest.get("assets", {})
                plat_info = assets.get(plat, {})
                expected_sha = plat_info.get("sha256")
            if expected_sha:
                actual_sha = _sha256(archive)
                if actual_sha != expected_sha:
                    raise InstallError(
                        f"SHA-256 mismatch: expected {expected_sha}, got {actual_sha}"
                    )
                if progress:
                    print(f"  SHA-256 verified: {actual_sha[:16]}...")

            # Extract
            if progress:
                print("  Extracting...")

            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True, exist_ok=True)

            with tarfile.open(archive, "r:gz") as tar:
                tar.extractall(dest, filter="data")

        # Write local manifest
        local_manifest = {
            **remote_manifest,
            "chromium_version": version,
            "asset_updated_at": asset_updated,
            "installed_at": datetime.now(UTC).isoformat(),
        }
        self._write_manifest(version, local_manifest)

        # Make chrome executable (not needed on Windows)
        chrome_bin = dest / _CHROME_BIN
        if chrome_bin.exists() and sys.platform != "win32":
            chrome_bin.chmod(0o755)

        if progress:
            print(f"  Installed to {dest}")

        return chrome_bin

    # -- update ------------------------------------------------------------

    def update(self, *, progress: bool = True) -> list[str]:
        """Check for updates to installed browsers.

        Returns list of versions that were updated.
        """
        entries = self.installed()
        if not entries:
            if progress:
                print("No browsers installed.")
            return []

        updated = []
        for entry in entries:
            version = entry["version"]
            local_manifest = entry["manifest"]

            if progress:
                print(f"Checking {version}...")

            try:
                release = self._get_release(version)
            except (HTTPError, OSError):
                if progress:
                    print("  Could not check (network error or release not found).")
                continue

            plat = _detect_platform()
            binary_asset = _find_asset(release, _asset_name(version, plat))
            if not binary_asset:
                continue

            remote_updated = binary_asset.get("updated_at", "")
            local_updated = (local_manifest or {}).get("asset_updated_at", "")

            if remote_updated != local_updated:
                if progress:
                    print(f"  Update available for {version}, downloading...")
                self.install(version, force=True, progress=progress)
                updated.append(version)
            elif progress:
                print("  Up to date.")

        return updated

    # -- uninstall ---------------------------------------------------------

    def uninstall(self, version: str) -> bool:
        """Remove an installed Chromium version."""
        dest = self._browsers_dir / version
        if not dest.exists():
            return False
        shutil.rmtree(dest)
        return True

    # -- internal ----------------------------------------------------------

    @staticmethod
    def _get_release(version: str) -> dict:
        tag = f"chromium-{version}"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}"
        return _fetch_json(url)

    def _read_manifest(self, version: str) -> dict | None:
        path = self._browsers_dir / version / ".manifest.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def _write_manifest(self, version: str, data: dict) -> None:
        path = self._browsers_dir / version / ".manifest.json"
        path.write_text(json.dumps(data, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def install_chromium(
    version: str | None = None,
    *,
    force: bool = False,
    progress: bool = True,
) -> Path:
    """Download and install patched Chromium. Convenience wrapper."""
    return BrowserManager().install(version, force=force, progress=progress)


def list_available() -> list[str]:
    """List Chromium versions available on GitHub."""
    return BrowserManager.available()


def list_installed() -> list[dict]:
    """List locally installed browser versions."""
    return BrowserManager().installed()
