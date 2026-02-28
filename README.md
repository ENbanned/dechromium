# dechromium

[![PyPI](https://img.shields.io/pypi/v/dechromium)](https://pypi.org/project/dechromium/)
[![Python](https://img.shields.io/pypi/pyversions/dechromium)](https://pypi.org/project/dechromium/)
[![License](https://img.shields.io/github/license/ENbanned/dechromium)](LICENSE)
[![CI](https://github.com/ENbanned/dechromium/actions/workflows/ci.yml/badge.svg)](https://github.com/ENbanned/dechromium/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-enbanned.github.io%2Fdechromium-blue)](https://enbanned.github.io/dechromium/)

Anti-detect browser built on Chromium. Manages browser profiles with isolated fingerprints — canvas, WebGL, audio, fonts, screen, navigator, timezone, and network. All spoofing is implemented in C++ inside the browser engine. No JavaScript injection, no CDP overrides.

## Install

```bash
pip install dechromium
dechromium install
```

The first command installs the Python library. The second downloads the patched Chromium binary from [GitHub Releases](https://github.com/ENbanned/dechromium/releases).

## Quick start

```python
from dechromium import Dechromium, Platform

dc = Dechromium()
profile = dc.create("my-profile", platform=Platform.WINDOWS)
browser = dc.start(profile.id)
print(browser.ws_endpoint)  # connect with Playwright, Puppeteer, or Selenium
dc.stop(profile.id)
```

## Features

| Feature | Details |
|---------|---------|
| **Profile management** | Create, list, update, delete profiles with full fingerprint isolation |
| **Platform presets** | `Platform.WINDOWS` / `MACOS` / `LINUX` sets identity, WebGL, and fonts in one call |
| **C++ spoofing** | Canvas noise, WebGL params, audio fingerprint, DOMRect noise — all at engine level |
| **Proxy support** | SOCKS5/HTTP with C++ auth, DNS leak protection, WebRTC leak protection |
| **Font isolation** | Per-profile fontconfig with platform-specific font packs |
| **Cookie management** | Import/export Chrome SQLite cookies |
| **REST API** | Optional FastAPI server — `pip install dechromium[server]` |
| **Typed** | PEP 561 typed, Pydantic v2 models, enum-based API with IDE autocomplete |

## Browser management

```bash
dechromium install                     # latest version
dechromium install 145.0.7632.116      # specific version
dechromium update                      # check for updates (hotfixes)
dechromium browsers                    # list available and installed
dechromium uninstall 145.0.7632.116    # remove a version
```

Multiple versions can be installed side-by-side. The library auto-selects the latest.

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `DECHROMIUM_DATA_DIR` | `~/.dechromium` | Base directory for profiles and browsers |
| `DECHROMIUM_BROWSER_BIN` | auto-detect | Override browser binary path |
| `DECHROMIUM_FONTS_DIR` | `~/.dechromium/fonts` | Font packs directory |

## Documentation

**[enbanned.github.io/dechromium](https://enbanned.github.io/dechromium/)**

## License

MIT
