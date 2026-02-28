# Configuration

## Config class

```python
from dechromium import Config

config = Config(
    data_dir="/path/to/data",
    browser_bin="/path/to/chrome",
    fonts_dir="/path/to/fonts",
    api_host="127.0.0.1",
    api_port=3789,
    debug_port_start=9200,
    debug_port_end=9999,
)
```

## Fields

| Field | Type | Default | Env var | Description |
|-------|------|---------|---------|-------------|
| `data_dir` | `Path` | `~/.dechromium` | `DECHROMIUM_DATA_DIR` | Base directory for profiles and browsers |
| `browser_bin` | `Path` | auto-detect | `DECHROMIUM_BROWSER_BIN` | Chromium binary path |
| `fonts_dir` | `Path` | `~/.dechromium/fonts` | `DECHROMIUM_FONTS_DIR` | Font packs directory |
| `api_host` | `str` | `127.0.0.1` | — | REST API bind address |
| `api_port` | `int` | `3789` | — | REST API port |
| `debug_port_start` | `int` | `9200` | — | CDP port range start |
| `debug_port_end` | `int` | `9999` | — | CDP port range end |

## Browser binary resolution

If `DECHROMIUM_BROWSER_BIN` is not set and `browser_bin` is not passed explicitly, the library resolves it automatically:

1. Scan `~/.dechromium/browsers/*/chrome`
2. Sort by version number (e.g. `146.0.8000.50` > `145.0.7632.116`)
3. Return the latest

If no browser is installed, falls back to `~/.dechromium/browser/chrome` (legacy path).

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `profiles_dir` | `Path` | `data_dir / "profiles"` |

## Environment variables

Environment variables are checked at `Config()` instantiation time. Explicit constructor arguments take priority.

```bash
export DECHROMIUM_DATA_DIR=/var/lib/dechromium
export DECHROMIUM_BROWSER_BIN=/usr/local/bin/chrome
export DECHROMIUM_FONTS_DIR=/usr/share/dechromium/fonts
```

```python
# These env vars are now the defaults
dc = Dechromium()
```
