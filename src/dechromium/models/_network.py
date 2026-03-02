from __future__ import annotations

from pydantic import BaseModel

from ._enums import WebRTCPolicy


class Network(BaseModel):
    proxy: str = ""
    proxy_username: str = ""
    proxy_password: str = ""
    webrtc_policy: WebRTCPolicy = WebRTCPolicy.DISABLE_NON_PROXIED_UDP
    timezone: str | None = None
    locale: str | None = None
    languages: list[str] | None = None
    latitude: float | None = None
    longitude: float | None = None
