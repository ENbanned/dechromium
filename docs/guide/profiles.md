# Profiles

A profile is a complete browser identity — user agent, hardware specs, WebGL configuration, noise seeds, network settings, and fonts. Each profile gets its own Chrome user data directory, so cookies, localStorage, and history are fully isolated.

## Platform presets

The `platform` parameter is the easiest way to create a consistent profile:
```python
profile = dc.create("work", platform="windows")
```

| Platform | navigator.platform | WebGL renderer | Fonts |
|---|---|---|---|
| `windows` | `Win32` | NVIDIA RTX 3060 / D3D11 | Arial, Times New Roman, Courier New, etc. |
| `macos` | `MacIntel` | Apple M1 / OpenGL | Helvetica Neue, Times New Roman, Courier New |
| `linux` | `Linux x86_64` | Mesa / llvmpipe / OpenGL | DejaVu Sans, DejaVu Serif, DejaVu Sans Mono |

Presets set `identity`, `webgl`, and `fonts` together. You can override any individual field on top of a preset.

## Profile sections

### Identity

Controls `navigator.*` properties and HTTP Client Hints headers.
```python
dc.create("x", identity={
    "chrome_version": 145,        # Chrome/145.0.0.0 in UA
    "platform": "Win32",          # navigator.platform
    "ua_platform": "Windows",     # Sec-CH-UA-Platform header
    "ua_platform_version": "15.0.0",
    "ua_arch": "x86",             # Sec-CH-UA-Arch header
})
```

`user_agent` is auto-generated from `chrome_version` and `platform`. Override it explicitly if needed.

### Hardware
```python
dc.create("x", hardware={
    "cores": 4,                # navigator.hardwareConcurrency
    "memory_gb": 4,            # navigator.deviceMemory (0.25, 0.5, 1, 2, 4, or 8)
    "screen_width": 1920,      # screen.width
    "screen_height": 1080,     # screen.height
    "avail_width": 1920,       # screen.availWidth
    "avail_height": 1040,      # screen.availHeight
    "device_pixel_ratio": 1.0, # window.devicePixelRatio
    "color_depth": 24,         # screen.colorDepth
})
```

!!! warning
    `memory_gb` must be one of `0.25, 0.5, 1, 2, 4, 8`. Chrome only returns these values — anything else is an instant detection flag.

### WebGL
```python
dc.create("x", webgl={
    "vendor": "Google Inc. (NVIDIA)",
    "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
})
```

The vendor and renderer must match the claimed platform. A Windows profile with a Mesa renderer is an obvious flag.

### Noise

Noise seeds control deterministic fingerprint noise. Each seed produces a unique but stable fingerprint — the same seed always generates the same canvas hash.
```python
dc.create("x", noise={
    "canvas_seed": "a1b2c3d4e5f6",
    "audio_seed": "f6e5d4c3b2a1",
    "clientrects_seed": "112233445566",
    "webgl_seed": "665544332211",
})
```

Seeds are auto-generated if not specified. They're hex strings converted to uint64 for the C++ layer.

### Network
```python
dc.create("x", network={
    "proxy": "socks5://host:1080",
    "proxy_username": "user",
    "proxy_password": "pass",
    "timezone": "America/New_York",
    "locale": "en-US",
    "languages": ["en-US", "en"],
})
```

See [Proxy & Network](network.md) for details.

### Fonts
```python
dc.create("x", fonts={"font_pack": "windows"})
```

Font packs are directories of .ttf files. Each profile gets its own fontconfig configuration that only exposes fonts from the selected pack.

## CRUD operations
```python
# List all profiles
profiles = dc.list()

# Get one profile
profile = dc.get("abc123")

# Update
dc.update("abc123", name="new-name", hardware={"cores": 16})

# Delete (stops browser if running)
dc.delete("abc123")
```

## Profile storage

Profiles are stored as JSON files:
```
~/.dechromium/profiles/{id}/
├── profile.json     # profile configuration
├── chrome_data/     # Chrome user data (cookies, localStorage, etc.)
├── fonts/           # copied .ttf files for this profile
├── fonts.conf       # fontconfig configuration
└── fonts_cache/     # fontconfig cache
```
