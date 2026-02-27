# Changelog

## 0.2.0

Package restructure and type safety improvements.

### Breaking changes

- **src/ layout** — package moved from `dechromium/` to `src/dechromium/` with subpackages
- **Enums replace strings** — `Platform`, `FontPack`, `WebRTCPolicy`, `DeviceMemory`, `ColorDepth` enums replace raw strings/numbers
- **Field renames** — `Hardware.memory_gb` is now `Hardware.memory` (DeviceMemory enum), `Hardware.device_pixel_ratio` is now `Hardware.pixel_ratio`
- **Custom exceptions** — `ProfileNotFoundError`, `BrowserError`, `BrowserTimeoutError` replace generic Python exceptions
- **CLI entry point** — `dechromium._cli:main` replaces `dechromium.__main__:main`

### Added

- `Platform`, `FontPack`, `WebRTCPolicy`, `DeviceMemory`, `ColorDepth` enums with IDE autocomplete and Pydantic validation
- `py.typed` marker (PEP 561)
- Custom exception hierarchy: `DechromiumError` base, `ProfileNotFoundError`, `ProfileExistsError`, `BrowserError`, `BrowserNotRunningError`, `BrowserTimeoutError`, `DisplayError`
- CI workflow (lint + test on Python 3.11, 3.12, 3.13)
- Release workflow (PyPI publish via Trusted Publishers)
- Reference docs for models, enums, exceptions, and configuration

### Changed

- Split flat package into subpackages: `models/`, `profile/`, `browser/`, `server/`
- Split `manager.py` into `profile/_manager.py`, `_launcher.py`, `_fontconfig.py`
- Split `browser.py` into `browser/_pool.py`, `_process.py`, `_display.py`
- Moved cookies to `browser/_cookies.py`
- Extracted `Dechromium` class from `__init__.py` to `_client.py`
- `Hardware.avail_width` / `avail_height` default to `None` (auto-computed from screen size)
- Updated `pyproject.toml` for hatch build with src/ layout
- Updated docs navigation with Reference section
- Fixed `repo_url` in mkdocs.yml to ENbanned/dechromium

## 0.1.0

Initial release.

### Chromium patches (145.0.7632.116)

- `navigator.webdriver` returns `false`
- `navigator.platform`, `hardwareConcurrency`, `deviceMemory` — spoofed via switches
- Screen properties — patched at WidgetBase level, covers JS API + CSS media queries
- Client Hints (Sec-CH-UA-Platform, etc.) — single patch point in `GetUserAgentMetadata()`
- Canvas fingerprint noise — deterministic per-seed
- WebGL vendor/renderer spoofing — covers WebGL 1 and 2
- Audio fingerprint noise — covers AudioBuffer and AnalyserNode
- SOCKS5/HTTP proxy auth — C++ level
- Font isolation — FONTCONFIG_FILE per-profile + strict match
- TLS/JA3 and HTTP/2 SETTINGS — verified identical to Chrome, no patch needed

### Python library

- Profile management with Pydantic v2 models
- Platform presets (windows, macos, linux)
- Browser process lifecycle with CDP readiness detection
- Font pack isolation via fontconfig
- Timezone/locale via environment variables
- Cookie import/export (Chrome SQLite format)
- Optional REST API via FastAPI
