from __future__ import annotations

import shutil
import sys
from pathlib import Path

from dechromium._config import Config
from dechromium.models import Profile

_FONT_GENERICS = {
    "windows": {
        "sans_serif": "Arial",
        "serif": "Times New Roman",
        "monospace": "Courier New",
    },
    "linux": {
        "sans_serif": "DejaVu Sans",
        "serif": "DejaVu Serif",
        "monospace": "DejaVu Sans Mono",
    },
    "macos": {
        "sans_serif": "Helvetica Neue",
        "serif": "Times New Roman",
        "monospace": "Courier New",
    },
}

_LINUX_FONT_BLOCKS = (
    "Liberation Sans",
    "Liberation Serif",
    "Liberation Mono",
    "DejaVu Sans",
    "DejaVu Serif",
    "DejaVu Sans Mono",
    "Ubuntu",
    "Noto Sans",
)

_MACOS_FONT_BLOCKS = (
    "Liberation Sans",
    "Liberation Serif",
    "Liberation Mono",
    "DejaVu Sans",
    "DejaVu Serif",
    "DejaVu Sans Mono",
    "Ubuntu",
)

_ALIAS_BLOCKS: dict[str, tuple[str, ...]] = {
    "windows": _LINUX_FONT_BLOCKS,
    "macos": _MACOS_FONT_BLOCKS,
    "linux": (),
}

# Map macOS proprietary font names → free substitutes bundled in fonts/macos/
_MACOS_FONT_ALIASES: dict[str, str] = {
    "Helvetica": "TeX Gyre Heros",
    "Helvetica Neue": "TeX Gyre Heros",
    "Avenir": "Nunito Sans",
    "Avenir Next": "Nunito Sans",
    "Futura": "Jost",
    "Baskerville": "Libre Baskerville",
    "Gill Sans": "Lato",
    "Palatino": "TeX Gyre Pagella",
    "Geneva": "Nimbus Sans",
    "Lucida Grande": "Inter",
    "SF Pro": "Inter",
    "SF Mono": "DejaVu Sans Mono",
    "Menlo": "DejaVu Sans Mono",
    "Monaco": "Fira Mono",
    "Optima": "Lato",
    "Symbol": "DejaVu Sans",
}

_WINDOWS_FONT_ALIASES: dict[str, str] = {
    "Calibri": "Carlito",
    "Segoe UI": "Inter",
    "Tahoma": "DejaVu Sans",
    "Consolas": "Inconsolata",
    "Cambria": "Caladea",
    "Lucida Console": "DejaVu Sans Mono",
    "Microsoft Sans Serif": "Liberation Sans",
    "Palatino Linotype": "TeX Gyre Pagella",
}

_FONTCONFIG_HEADER = """\
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>{font_dir}</dir>
  <cachedir>{cache_dir}</cachedir>

  <alias>
    <family>sans-serif</family>
    <prefer><family>{sans_serif}</family></prefer>
  </alias>
  <alias>
    <family>serif</family>
    <prefer><family>{serif}</family></prefer>
  </alias>
  <alias>
    <family>monospace</family>
    <prefer><family>{monospace}</family></prefer>
  </alias>

  <selectfont>
    <rejectfont>
      <glob>/usr/share/fonts/*</glob>
      <glob>/usr/local/share/fonts/*</glob>
      <glob>~/.fonts/*</glob>
      <glob>~/.local/share/fonts/*</glob>
    </rejectfont>
  </selectfont>
"""

_FONTCONFIG_BLOCK = """\

  <match target="pattern">
    <test name="family"><string>{family}</string></test>
    <edit name="family" mode="assign" binding="same"><string>__BLOCKED__</string></edit>
  </match>"""

_FONTCONFIG_ALIAS = """\

  <match target="pattern">
    <test name="family"><string>{family}</string></test>
    <edit name="family" mode="prepend_first" binding="strong">
      <string>{substitute}</string>
    </edit>
  </match>"""

_FONTCONFIG_FOOTER = "\n</fontconfig>\n"


def setup_profile_fonts(profile: Profile, config: Config) -> None:
    """Copy font files and write fontconfig XML for a profile."""
    pack = profile.fonts.font_pack.value
    profile_dir = config.profiles_dir / profile.id
    src_dir = config.fonts_dir / pack
    font_dir = profile_dir / "fonts"
    cache_dir = profile_dir / "fonts_cache"

    font_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    if src_dir.exists():
        for font_file in (*src_dir.glob("*.ttf"), *src_dir.glob("*.otf")):
            dst = font_dir / font_file.name
            if not dst.exists():
                shutil.copy2(font_file, dst)

    if sys.platform != "win32":
        xml = generate_fontconfig_xml(pack, font_dir, cache_dir)
        (profile_dir / "fonts.conf").write_text(xml)


def generate_fontconfig_xml(font_pack: str, font_dir: Path, cache_dir: Path) -> str:
    """Generate fontconfig XML content for a given font pack."""
    generics = _FONT_GENERICS.get(font_pack, _FONT_GENERICS["windows"])
    blocks = _ALIAS_BLOCKS.get(font_pack, ())

    conf = _FONTCONFIG_HEADER.format(
        font_dir=str(font_dir),
        cache_dir=str(cache_dir),
        sans_serif=generics["sans_serif"],
        serif=generics["serif"],
        monospace=generics["monospace"],
    )
    for family in blocks:
        conf += _FONTCONFIG_BLOCK.format(family=family)

    if font_pack == "macos":
        aliases = _MACOS_FONT_ALIASES
    elif font_pack == "windows":
        aliases = _WINDOWS_FONT_ALIASES
    else:
        aliases = {}
    for family, substitute in aliases.items():
        conf += _FONTCONFIG_ALIAS.format(family=family, substitute=substitute)

    # system-ui alias → platform-appropriate font
    system_ui_font = generics["sans_serif"]
    conf += _FONTCONFIG_ALIAS.format(family="system-ui", substitute=system_ui_font)

    conf += _FONTCONFIG_FOOTER

    return conf
