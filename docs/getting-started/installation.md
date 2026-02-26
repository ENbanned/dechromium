# Installation

## Python library
```bash
pip install dechromium
```

With REST API server:
```bash
pip install dechromium[server]
```

## Browser binary

The library requires a patched Chromium binary. Two options:

### Option 1: Download prebuilt (recommended)

Download from [GitHub Releases](https://github.com/aspect-browser/dechromium/releases) and extract:
```bash
mkdir -p ~/.dechromium/browser
tar xzf dechromium-browser-145.0.7632.116-linux-x64.tar.gz -C ~/.dechromium/browser/
```

### Option 2: Build from source

See [Building from Source](../patches/building.md) for full instructions. This takes 2-4 hours for a first build.

## Font packs

Font packs are included in the repository under `fonts/`. Copy them to the default location:
```bash
cp -r fonts/ ~/.dechromium/fonts/
```

Or point the library to your fonts directory:
```python
from dechromium import Dechromium, Config

dc = Dechromium(Config(fonts_dir="/path/to/fonts"))
```

## Directory structure

After installation, `~/.dechromium/` looks like:
```
~/.dechromium/
├── browser/
│   └── chrome          # patched Chromium binary
├── fonts/
│   ├── windows/        # .ttf files for Windows profiles
│   ├── linux/          # .ttf files for Linux profiles
│   └── macos/          # .ttf files for macOS profiles
└── profiles/           # created automatically
    └── {profile_id}/
        ├── profile.json
        ├── chrome_data/
        ├── fonts/
        └── fonts.conf
```

## Configuration

All paths can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `DECHROMIUM_DATA_DIR` | `~/.dechromium` | Base directory |
| `DECHROMIUM_BROWSER_BIN` | `~/.dechromium/browser/chrome` | Chromium binary |
| `DECHROMIUM_FONTS_DIR` | `~/.dechromium/fonts` | Font packs |

Or via `Config`:
```python
from dechromium import Dechromium, Config

dc = Dechromium(Config(
    browser_bin="/opt/dechromium/chrome",
    data_dir="/var/lib/dechromium",
))
```
