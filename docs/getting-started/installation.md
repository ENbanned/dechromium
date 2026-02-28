# Installation

## 1. Python library

```bash
pip install dechromium
```

With REST API server:
```bash
pip install dechromium[server]
```

Verify:
```bash
dechromium version
```

## 2. Browser binary

The library requires a patched Chromium binary.

### Download (recommended)

```bash
dechromium install
```

This downloads the latest patched Chromium from [GitHub Releases](https://github.com/ENbanned/dechromium/releases) and installs it to `~/.dechromium/browsers/<version>/`.

Install a specific version:
```bash
dechromium install 145.0.7632.116
```

### Build from source

See [Build Guide](../patches/building.md). First build takes 2-4 hours; incremental builds after patch changes take 2-5 minutes.

## 3. Font packs

Font packs are included in the repository under `fonts/`. Copy them to the default location:
```bash
cp -r fonts/ ~/.dechromium/fonts/
```

Or point to a custom directory:
```python
from dechromium import Dechromium, Config

dc = Dechromium(Config(fonts_dir="/path/to/fonts"))
```

## Directory structure

```
~/.dechromium/
├── browsers/
│   └── 145.0.7632.116/
│       ├── chrome                # patched Chromium binary
│       └── .manifest.json        # version metadata
├── fonts/
│   ├── windows/                  # .ttf files for Windows profiles
│   ├── linux/                    # .ttf files for Linux profiles
│   └── macos/                    # .ttf files for macOS profiles
└── profiles/                     # created automatically
    └── {profile_id}/
        ├── profile.json
        ├── chrome_data/
        ├── fonts/
        └── fonts.conf
```

## Configuration

All paths can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DECHROMIUM_DATA_DIR` | `~/.dechromium` | Base directory |
| `DECHROMIUM_BROWSER_BIN` | auto-detect | Override Chromium binary path |
| `DECHROMIUM_FONTS_DIR` | `~/.dechromium/fonts` | Font packs |

If `DECHROMIUM_BROWSER_BIN` is not set, the library scans `~/.dechromium/browsers/` and selects the latest installed version.

Or via `Config`:
```python
from dechromium import Dechromium, Config

dc = Dechromium(Config(
    browser_bin="/opt/dechromium/chrome",
    data_dir="/var/lib/dechromium",
))
```
