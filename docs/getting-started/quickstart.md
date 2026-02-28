# Quick Start

Prerequisite: install the library and browser binary.
```bash
pip install dechromium
dechromium install
```

## Create a profile
```python
from dechromium import Dechromium, Platform

with Dechromium() as dc:
    # Platform preset sets identity, WebGL, and fonts automatically
    profile = dc.create("my-profile", platform=Platform.WINDOWS)
```

This creates a profile with:

- Windows user agent and navigator properties
- NVIDIA WebGL renderer (matches Windows)
- Windows font pack (Arial, Times New Roman, etc.)
- Unique canvas, audio, WebGL, and client rects noise seeds
- Default timezone (America/New_York) and locale (en-US)

## Customize everything
```python
from dechromium import Dechromium, Platform, DeviceMemory

with Dechromium() as dc:
    profile = dc.create("custom",
        platform=Platform.WINDOWS,
        proxy="socks5://user:pass@host:1080",
        timezone="Europe/London",
        locale="en-GB",
        languages=["en-GB", "en"],
        cores=4,
        memory=DeviceMemory.GB_4,
        screen=(1366, 768),
    )
```

Or override individual sections:
```python
with Dechromium() as dc:
    profile = dc.create("manual",
        identity={"chrome_version": 145, "platform": "Win32", "ua_arch": "x86"},
        hardware={"cores": 8, "memory": 8},
        webgl={"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, ...)"},
        network={"timezone": "Asia/Tokyo", "locale": "ja-JP"},
    )
```

## Launch a browser
```python
with Dechromium() as dc:
    profile = dc.create("my-profile", platform=Platform.WINDOWS)

    # Headless (default) — for automation
    browser = dc.start(profile.id, headless=True)

    # browser contains everything you need to connect:
    browser.pid           # OS process ID
    browser.debug_port    # CDP port number
    browser.ws_endpoint   # ws://127.0.0.1:9200/devtools/browser/...
    browser.cdp_url       # http://127.0.0.1:9200
# all browsers stopped automatically on exit
```

## Connect with automation tools

=== "Playwright"
```python
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(browser.cdp_url)
        page = browser.contexts[0].pages[0]
        page.goto("https://example.com")
```

=== "Puppeteer"
```javascript
    const browser = await puppeteer.connect({
        browserWSEndpoint: wsEndpoint,
    });
    const [page] = await browser.pages();
    await page.goto("https://example.com");
```

=== "Selenium"
```python
    from selenium import webdriver

    options = webdriver.ChromeOptions()
    options.debugger_address = f"127.0.0.1:{browser.debug_port}"
    driver = webdriver.Chrome(options=options)
```

## Stop and cleanup
```python
with Dechromium() as dc:
    profile = dc.create("temp", platform=Platform.WINDOWS)
    browser = dc.start(profile.id)
    # ... do work ...
# all browsers stopped automatically on exit
```

## Alternative: manual lifecycle

If you prefer explicit control over browser shutdown:
```python
from dechromium import Dechromium, Platform

dc = Dechromium()
profile = dc.create("my-profile", platform=Platform.WINDOWS)
browser = dc.start(profile.id)
# ... do work ...
dc.stop(profile.id)    # stop one browser
dc.stop_all()           # stop all browsers
dc.delete(profile.id)   # delete profile and all data
```
