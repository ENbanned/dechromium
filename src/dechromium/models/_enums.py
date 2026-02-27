from __future__ import annotations

from enum import Enum, StrEnum


class Platform(StrEnum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class FontPack(StrEnum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"


class WebRTCPolicy(StrEnum):
    DEFAULT = "default"
    DISABLE_NON_PROXIED_UDP = "disable_non_proxied_udp"
    DEFAULT_PUBLIC_INTERFACE_ONLY = "default_public_interface_only"
    DEFAULT_PUBLIC_AND_PRIVATE = "default_public_and_private_interfaces"


class DeviceMemory(float, Enum):
    """Valid deviceMemory values per W3C spec."""

    GB_0_25 = 0.25
    GB_0_5 = 0.5
    GB_1 = 1
    GB_2 = 2
    GB_4 = 4
    GB_8 = 8


class ColorDepth(int, Enum):
    BIT_24 = 24
    BIT_30 = 30
    BIT_48 = 48
