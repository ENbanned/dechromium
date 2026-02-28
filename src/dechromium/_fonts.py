from __future__ import annotations

import shutil
from pathlib import Path

_BUNDLED_DIR = Path(__file__).parent / "fonts"


def ensure_fonts(fonts_dir: Path, version: str) -> None:
    """Copy bundled font packs to *fonts_dir* if needed.

    Uses a ``.font_version`` marker file to skip when the installed version
    already matches *version*.  Stale ``.ttf`` files that are no longer in
    the bundle are removed.
    """
    marker = fonts_dir / ".font_version"

    # Fast path — already synced for this version.
    if marker.exists() and marker.read_text().strip() == version:
        return

    for pack_dir in _BUNDLED_DIR.iterdir():
        if not pack_dir.is_dir():
            continue

        dest = fonts_dir / pack_dir.name
        dest.mkdir(parents=True, exist_ok=True)

        bundled = {f.name for f in pack_dir.iterdir() if f.suffix == ".ttf"}

        # Copy new / updated fonts.
        for name in bundled:
            shutil.copy2(pack_dir / name, dest / name)

        # Remove stale fonts no longer in bundle.
        for existing in dest.iterdir():
            if existing.suffix == ".ttf" and existing.name not in bundled:
                existing.unlink()

    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(version)
