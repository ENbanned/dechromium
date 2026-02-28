from __future__ import annotations

from pathlib import Path

from dechromium._fonts import ensure_fonts


def test_first_install(tmp_path: Path):
    """First call copies fonts and writes the version marker."""
    fonts_dir = tmp_path / "fonts"
    ensure_fonts(fonts_dir, "0.4.0")

    marker = fonts_dir / ".font_version"
    assert marker.read_text() == "0.4.0"
    assert (fonts_dir / "windows").is_dir()
    assert any((fonts_dir / "windows").glob("*.ttf"))
    assert (fonts_dir / "linux").is_dir()
    assert any((fonts_dir / "linux").glob("*.ttf"))


def test_skip_when_version_matches(tmp_path: Path):
    """Second call with same version is a no-op (marker mtime unchanged)."""
    fonts_dir = tmp_path / "fonts"
    ensure_fonts(fonts_dir, "0.4.0")

    marker = fonts_dir / ".font_version"
    mtime = marker.stat().st_mtime

    ensure_fonts(fonts_dir, "0.4.0")

    assert marker.stat().st_mtime == mtime


def test_resync_on_version_change(tmp_path: Path):
    """Version bump triggers a re-sync and updates the marker."""
    fonts_dir = tmp_path / "fonts"
    ensure_fonts(fonts_dir, "0.4.0")

    marker = fonts_dir / ".font_version"
    assert marker.read_text() == "0.4.0"

    ensure_fonts(fonts_dir, "0.5.0")

    assert marker.read_text() == "0.5.0"


def test_stale_fonts_removed(tmp_path: Path):
    """Fonts no longer in the bundle are cleaned up on re-sync."""
    fonts_dir = tmp_path / "fonts"
    ensure_fonts(fonts_dir, "0.4.0")

    # Plant a stale font file
    stale = fonts_dir / "windows" / "Stale_Font.ttf"
    stale.write_bytes(b"fake")

    # Re-sync with different version triggers cleanup
    ensure_fonts(fonts_dir, "0.5.0")

    assert not stale.exists()
