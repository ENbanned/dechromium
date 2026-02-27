from __future__ import annotations

from pydantic import BaseModel

_UA_OS_PART = {
    "Win32": "Windows NT 10.0; Win64; x64",
    "MacIntel": "Macintosh; Intel Mac OS X 10_15_7",
    "Linux x86_64": "X11; Linux x86_64",
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
