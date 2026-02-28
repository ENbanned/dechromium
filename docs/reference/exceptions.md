# Exceptions

All exceptions inherit from `DechromiumError`.

```
DechromiumError
├── ProfileNotFoundError
├── ProfileExistsError
├── InstallError
├── BrowserError
│   ├── BrowserNotRunningError
│   └── BrowserTimeoutError
└── DisplayError
```

## DechromiumError

Base exception for all dechromium errors.

```python
from dechromium import DechromiumError

try:
    dc.start("nonexistent")
except DechromiumError as e:
    print(f"dechromium error: {e}")
```

## ProfileNotFoundError

Raised when a profile does not exist on disk.

```python
from dechromium import ProfileNotFoundError

try:
    profile = dc.get("nonexistent")
except ProfileNotFoundError:
    print("Profile not found")
```

**Raised by:** `Dechromium.get()`, `Dechromium.update()`, `Dechromium.start()`

## ProfileExistsError

Raised when attempting to create a profile that already exists.

## InstallError

Raised when browser installation fails — release not found, network error, SHA-256 mismatch, or missing platform binary.

```python
from dechromium import InstallError

try:
    dc.install_browser("999.0.0.0")
except InstallError as e:
    print(f"Install failed: {e}")
```

**Raised by:** `Dechromium.install_browser()`, `install_chromium()`, `BrowserManager.install()`

## BrowserError

Base exception for browser-related errors. Raised when the browser process exits unexpectedly or ports are exhausted.

```python
from dechromium import BrowserError

try:
    browser = dc.start(profile.id)
except BrowserError as e:
    print(f"Browser failed: {e}")
```

## BrowserNotRunningError

Raised when an operation requires a running browser but none is found.

## BrowserTimeoutError

Raised when the browser fails to become ready (CDP endpoint) within the timeout period.

```python
from dechromium import BrowserTimeoutError

try:
    browser = dc.start(profile.id, timeout=5.0)
except BrowserTimeoutError:
    print("Browser took too long to start")
```

## DisplayError

Raised when the virtual display (Xvfb) fails to start. Typically occurs when running headed mode on a server without Xvfb installed.
