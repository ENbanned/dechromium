from dechromium._client import Dechromium
from dechromium._config import Config
from dechromium._exceptions import (
    BrowserError,
    BrowserNotRunningError,
    BrowserTimeoutError,
    DechromiumError,
    DisplayError,
    ProfileExistsError,
    ProfileNotFoundError,
)
from dechromium.browser import BrowserInfo
from dechromium.models import (
    ColorDepth,
    DeviceMemory,
    FontPack,
    Fonts,
    Hardware,
    Identity,
    Network,
    Noise,
    Platform,
    Profile,
    WebGL,
    WebRTCPolicy,
)

__version__ = "0.2.0"

__all__ = [
    "BrowserError",
    "BrowserInfo",
    "BrowserNotRunningError",
    "BrowserTimeoutError",
    "ColorDepth",
    "Config",
    "Dechromium",
    "DechromiumError",
    "DeviceMemory",
    "DisplayError",
    "FontPack",
    "Fonts",
    "Hardware",
    "Identity",
    "Network",
    "Noise",
    "Platform",
    "Profile",
    "ProfileExistsError",
    "ProfileNotFoundError",
    "WebGL",
    "WebRTCPolicy",
]
