# dechromium

Anti-detect browser built on Chromium. Manages unique browser profiles with isolated fingerprints — canvas, WebGL, audio, fonts, screen, navigator, timezone, and network.

Each profile gets its own identity, noise seeds, font environment, and Chrome user data directory. Browsers are launched with per-profile command-line switches that control spoofing at the C++ level — no JavaScript injection, no CDP overrides.

## How it works

**Patched Chromium binary** accepts `--aspect-*` command-line switches that override fingerprint-related values deep inside the browser engine. The Python library manages profiles and translates profile settings into these switches.
```
Profile JSON → Python library → CLI switches + env vars → Patched Chromium
```

Every spoofing mechanism is implemented in C++ inside Chromium itself:

- `navigator.webdriver` → returns `false` (not a CDP override — actually patched in navigator.cc)
- Canvas noise → deterministic pixel manipulation in ImageDataBuffer
- WebGL vendor/renderer → intercepted in getParameter()
- Fonts → per-process fontconfig isolation via `FONTCONFIG_FILE`
- Timezone → ICU reads `TZ` env var, inherited by all child processes

## Quick example
```python
from dechromium import Dechromium

dc = Dechromium()

profile = dc.create("my-profile",
    platform="windows",
    proxy="socks5://user:pass@host:1080",
    timezone="America/New_York",
)

browser = dc.start(profile.id, headless=False)
# browser.ws_endpoint → connect with Playwright/Puppeteer
dc.stop(profile.id)
```

## What's in the repo

| Directory | Contents |
|---|---|
| `dechromium/` | Python package — profile management, browser lifecycle, REST API |
| `patches/` | Chromium patches organized by version (e.g. `patches/145.0.7632.116/`) |
| `fonts/` | Font packs per platform (windows, linux, macos) |
| `build/` | Shell scripts for patching and building Chromium |
