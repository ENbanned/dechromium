# dechromium

[![PyPI](https://img.shields.io/pypi/v/dechromium)](https://pypi.org/project/dechromium/)
[![Python](https://img.shields.io/pypi/pyversions/dechromium)](https://pypi.org/project/dechromium/)
[![License](https://img.shields.io/github/license/ENbanned/dechromium)](LICENSE)
[![CI](https://github.com/ENbanned/dechromium/actions/workflows/ci.yml/badge.svg)](https://github.com/ENbanned/dechromium/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-enbanned.github.io%2Fdechromium-blue)](https://enbanned.github.io/dechromium/)

Anti-detect browser built on Chromium. Manages unique browser profiles with isolated fingerprints — canvas, WebGL, audio, fonts, screen, navigator, timezone, and network. All spoofing happens at the C++ level inside the browser engine — no JavaScript injection, no CDP overrides.

## Install

```
pip install dechromium
```

## Quick start

```python
from dechromium import Dechromium, Platform

dc = Dechromium()
profile = dc.create("my-profile", platform=Platform.WINDOWS)
browser = dc.start(profile.id)
print(browser.ws_endpoint)  # connect with Playwright/Puppeteer
dc.stop(profile.id)
```

## Features

- **Profile management** — create, list, update, delete browser profiles with full fingerprint isolation
- **Platform presets** — one keyword sets identity, WebGL, and fonts for Windows, macOS, or Linux
- **Enum-based API** — `Platform`, `DeviceMemory`, `WebRTCPolicy` enums with IDE autocomplete and validation
- **Browser lifecycle** — launch headless or headed, auto-allocate CDP ports, connect via WebSocket
- **Proxy support** — SOCKS5/HTTP with auth at C++ level, DNS and WebRTC leak protection
- **Font isolation** — per-profile fontconfig with platform-specific font packs
- **Cookie management** — import/export Chrome SQLite cookies
- **REST API** — optional FastAPI server (`pip install dechromium[server]`)
- **Typed** — PEP 561 typed, Pydantic v2 models with full validation

## Configuration

| Env var | Default | Description |
|---|---|---|
| `DECHROMIUM_DATA_DIR` | `~/.dechromium` | Base directory for profiles and data |
| `DECHROMIUM_BROWSER_BIN` | `~/.dechromium/browser/chrome` | Path to patched Chromium binary |
| `DECHROMIUM_FONTS_DIR` | `~/.dechromium/fonts` | Font packs directory |

## Documentation

Full documentation at [enbanned.github.io/dechromium](https://enbanned.github.io/dechromium/).

## License

MIT
