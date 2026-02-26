from __future__ import annotations

import time
import uuid

from pydantic import BaseModel, Field, field_validator


def _hex12() -> str:
    return uuid.uuid4().hex[:12]


def _ts() -> int:
    return int(time.time())


DEVICE_MEMORY_VALUES = (0.25, 0.5, 1, 2, 4, 8)

WEBRTC_POLICIES = (
    "default",
    "default_public_and_private_interfaces",
    "default_public_interface_only",
    "disable_non_proxied_udp",
)

FONT_PACKS = ("windows", "linux", "macos")

_UA_OS_PART = {
    "Win32": "Windows NT 10.0; Win64; x64",
    "MacIntel": "Macintosh; Intel Mac OS X 10_15_7",
    "Linux x86_64": "X11; Linux x86_64",
}

PLATFORMS: dict[str, dict] = {
    "windows": {
        "identity": {
            "platform": "Win32",
            "ua_platform": "Windows",
            "ua_platform_version": "15.0.0",
            "ua_arch": "x86",
        },
        "webgl": {
            "vendor": "Google Inc. (NVIDIA)",
            "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        },
        "fonts": {"font_pack": "windows"},
    },
    "macos": {
        "identity": {
            "platform": "MacIntel",
            "ua_platform": "macOS",
            "ua_platform_version": "14.5.0",
            "ua_arch": "arm",
        },
        "webgl": {
            "vendor": "Google Inc. (Apple)",
            "renderer": "ANGLE (Apple, Apple M1, OpenGL 4.1)",
        },
        "fonts": {"font_pack": "macos"},
    },
    "linux": {
        "identity": {
            "platform": "Linux x86_64",
            "ua_platform": "Linux",
            "ua_platform_version": "",
            "ua_arch": "x86",
        },
        "webgl": {
            "vendor": "Google Inc. (Mesa)",
            "renderer": "ANGLE (Mesa, llvmpipe, OpenGL 4.5)",
        },
        "fonts": {"font_pack": "linux"},
    },
}


class Identity(BaseModel):
    chrome_version: int = 145
    platform: str = "Win32"
    ua_platform: str = "Windows"
    ua_platform_version: str = "15.0.0"
    ua_arch: str = "x86"
    user_agent: str = ""

    def model_post_init(self, __context):
        if not self.user_agent:
            os_part = _UA_OS_PART.get(self.platform, "Windows NT 10.0; Win64; x64")
            self.user_agent = (
                f"Mozilla/5.0 ({os_part}) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{self.chrome_version}.0.0.0 Safari/537.36"
            )


class Hardware(BaseModel):
    cores: int = 8
    memory_gb: float = 8.0
    screen_width: int = 1920
    screen_height: int = 1080
    avail_width: int = 1920
    avail_height: int = 1040
    device_pixel_ratio: float = 1.0
    color_depth: int = 24

    @field_validator("memory_gb")
    @classmethod
    def check_memory(cls, v):
        if v not in DEVICE_MEMORY_VALUES:
            raise ValueError(
                f"memory_gb must be one of {DEVICE_MEMORY_VALUES}, got {v}"
            )
        return v


class WebGL(BaseModel):
    vendor: str = "Google Inc. (NVIDIA)"
    renderer: str = (
        "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 "
        "Direct3D11 vs_5_0 ps_5_0, D3D11)"
    )


class Noise(BaseModel):
    canvas_seed: str = Field(default_factory=_hex12)
    audio_seed: str = Field(default_factory=_hex12)
    clientrects_seed: str = Field(default_factory=_hex12)
    webgl_seed: str = Field(default_factory=_hex12)


class Network(BaseModel):
    proxy: str = ""
    proxy_username: str = ""
    proxy_password: str = ""
    webrtc_policy: str = "disable_non_proxied_udp"
    timezone: str = "America/New_York"
    locale: str = "en-US"
    languages: list[str] = Field(default_factory=lambda: ["en-US", "en"])

    @field_validator("webrtc_policy")
    @classmethod
    def check_webrtc_policy(cls, v):
        if v not in WEBRTC_POLICIES:
            raise ValueError(
                f"webrtc_policy must be one of {WEBRTC_POLICIES}, got {v}"
            )
        return v


class Fonts(BaseModel):
    font_pack: str = "windows"

    @field_validator("font_pack")
    @classmethod
    def check_font_pack(cls, v):
        if v not in FONT_PACKS:
            raise ValueError(f"font_pack must be one of {FONT_PACKS}, got {v}")
        return v


class Profile(BaseModel):
    id: str = Field(default_factory=_hex12)
    name: str = "default"
    created_at: int = Field(default_factory=_ts)
    updated_at: int = Field(default_factory=_ts)
    notes: str = ""
    identity: Identity = Field(default_factory=Identity)
    hardware: Hardware = Field(default_factory=Hardware)
    webgl: WebGL = Field(default_factory=WebGL)
    noise: Noise = Field(default_factory=Noise)
    network: Network = Field(default_factory=Network)
    fonts: Fonts = Field(default_factory=Fonts)
