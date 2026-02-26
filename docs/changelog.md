# Changelog

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
