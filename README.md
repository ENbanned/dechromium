# dechromium

Anti-detect browser built on Chromium. Manages unique browser profiles with isolated fingerprints — canvas, WebGL, audio, fonts, screen, navigator, timezone, and network.

Each profile gets its own identity, noise seeds, font environment, and Chrome user data directory. Browsers are launched with per-profile command-line switches that control spoofing at the C++ level — no JavaScript injection, no CDP overrides.

## Install

```
pip install dechromium
```

## Quick start

```python
from dechromium import Dechromium

dc = Dechromium()

profile = dc.create("my-profile", platform="windows")
browser = dc.start(profile.id, headless=False)

# Connect with Playwright, Puppeteer, or any CDP client
# playwright: browser = pw.chromium.connect_over_cdp(browser.cdp_url)
print(browser.ws_endpoint)

dc.stop(profile.id)
```

## Profiles

```python
# Create with platform preset — sets identity, WebGL, fonts automatically
profile = dc.create("work",
    platform="windows",
    proxy="socks5://user:pass@host:1080",
    timezone="America/New_York",
    locale="en-US",
    languages=["en-US", "en"],
)

# Full control over individual sections
profile = dc.create("custom",
    identity={"chrome_version": 145, "ua_platform_version": "15.0.0"},
    hardware={"cores": 4, "memory_gb": 4, "screen_width": 1366, "screen_height": 768},
    webgl={"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, ...)"},
)

# List, update, delete
profiles = dc.list()
dc.update(profile.id, name="renamed", hardware={"cores": 8})
dc.delete(profile.id)
```

## Browser lifecycle

```python
browser = dc.start(profile.id, headless=False)

# BrowserInfo fields:
# browser.pid          - OS process ID
# browser.debug_port   - CDP port
# browser.ws_endpoint  - WebSocket URL for CDP
# browser.cdp_url      - HTTP URL for CDP

dc.stop(profile.id)
dc.stop_all()
```

## REST API

```
pip install dechromium[server]
dechromium serve --host=127.0.0.1 --port=3789
```

```
POST   /profiles              — create profile
GET    /profiles              — list profiles
GET    /profiles/{id}         — get profile
PUT    /profiles/{id}         — update profile
DELETE /profiles/{id}         — delete profile
POST   /profiles/{id}/start   — start browser
POST   /profiles/{id}/stop    — stop browser
GET    /profiles/{id}/status  — browser status
GET    /running               — all running browsers
POST   /stop-all              — stop all browsers
GET    /health                — service health
```

## Configuration

Paths default to `~/.dechromium/`. Override with environment variables or constructor arguments:

| Env var | Default | Description |
|---|---|---|
| `DECHROMIUM_DATA_DIR` | `~/.dechromium` | Base directory for profiles and data |
| `DECHROMIUM_BROWSER_BIN` | `~/.dechromium/browser/chrome` | Path to patched Chromium binary |
| `DECHROMIUM_FONTS_DIR` | `~/.dechromium/fonts` | Font packs directory |

```python
from dechromium import Dechromium, Config

dc = Dechromium(Config(
    browser_bin="/path/to/chrome",
    fonts_dir="/path/to/fonts",
))
```

## Building from source

See [docs/building.md](docs/building.md) for instructions on building the patched Chromium browser from the patches in this repository.

## What the patches do

See [docs/patches.md](docs/patches.md) for a description of each patch.

## License

MIT
