from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


def _env_path(key: str, default: str) -> Path:
    return Path(os.environ.get(key, default))


def _default_data_dir() -> Path:
    return _env_path("DECHROMIUM_DATA_DIR", str(Path.home() / ".dechromium"))


def _default_browser_bin() -> Path:
    env = os.environ.get("DECHROMIUM_BROWSER_BIN")
    if env:
        return Path(env)

    data_dir = _default_data_dir()

    # Multi-version layout: pick latest installed
    browsers_dir = data_dir / "browsers"
    if browsers_dir.is_dir():
        versions = [
            d.name for d in browsers_dir.iterdir() if d.is_dir() and (d / "chrome").exists()
        ]
        if versions:
            versions.sort(key=_version_key, reverse=True)
            return browsers_dir / versions[0] / "chrome"

    # Legacy layout (pre-multi-version)
    return data_dir / "browser" / "chrome"


def _version_key(v: str) -> tuple[int, ...]:
    parts = []
    for x in v.split("."):
        try:
            parts.append(int(x))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _default_fonts_dir() -> Path:
    return _env_path("DECHROMIUM_FONTS_DIR", str(Path.home() / ".dechromium" / "fonts"))


class Config(BaseModel):
    data_dir: Path = Field(default_factory=_default_data_dir)
    browser_bin: Path = Field(default_factory=_default_browser_bin)
    fonts_dir: Path = Field(default_factory=_default_fonts_dir)
    api_host: str = "127.0.0.1"
    api_port: int = 3789
    debug_port_start: int = 9200
    debug_port_end: int = 9999

    @property
    def profiles_dir(self) -> Path:
        return self.data_dir / "profiles"
