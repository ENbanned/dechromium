# dechromium

Anti-detect browser built on Chromium. Manages browser profiles with isolated fingerprints — canvas, WebGL, audio, fonts, screen, navigator, timezone, and network.

Each profile gets its own identity, noise seeds, font environment, and Chrome user data directory. Browsers are launched with per-profile command-line switches that control spoofing at the C++ level — no JavaScript injection, no CDP overrides.

## How it works

A **patched Chromium binary** accepts `--aspect-*` command-line switches that override fingerprint values deep inside the browser engine. The Python library manages profiles and translates profile settings into these switches.

```
Profile JSON → Python library → CLI switches + env vars → Patched Chromium
```

Every spoofing mechanism is implemented in C++:

- `navigator.webdriver` → returns `false` (patched in navigator.cc, not a CDP override)
- Canvas noise → deterministic pixel manipulation in ImageDataBuffer
- WebGL vendor/renderer → intercepted in getParameter()
- Audio fingerprint → noise in AudioBuffer and AnalyserNode
- Fonts → per-process fontconfig isolation via `FONTCONFIG_FILE`
- Timezone → ICU reads `TZ` env var, inherited by all child processes

## Get started

```bash
pip install dechromium
dechromium install
```

```python
from dechromium import Dechromium, Platform

dc = Dechromium()

profile = dc.create("my-profile",
    platform=Platform.WINDOWS,
    proxy="socks5://user:pass@host:1080",
    timezone="America/New_York",
)

browser = dc.start(profile.id, headless=False)
# browser.ws_endpoint → connect with Playwright/Puppeteer/Selenium
dc.stop(profile.id)
```

## Repository structure

| Directory | Contents |
|-----------|----------|
| `src/dechromium/` | Python package — profile management, browser lifecycle, installer, REST API |
| `patches/` | Chromium patches organized by version (e.g. `patches/145.0.7632.116/`) |
| `fonts/` | Font packs per platform (windows, linux, macos) |
| `build/` | Shell scripts for patching and building Chromium |
| `docs/` | This documentation (mkdocs-material) |
