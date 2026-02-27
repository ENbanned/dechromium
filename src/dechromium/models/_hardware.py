from __future__ import annotations

from pydantic import BaseModel, Field

from ._enums import ColorDepth, DeviceMemory


class Hardware(BaseModel):
    cores: int = Field(8, ge=1, le=32)
    memory: DeviceMemory = DeviceMemory.GB_8
    screen_width: int = Field(1920, ge=800, le=3840)
    screen_height: int = Field(1080, ge=600, le=2160)
    avail_width: int | None = None
    avail_height: int | None = None
    color_depth: ColorDepth = ColorDepth.BIT_24
    pixel_ratio: float = Field(1.0, ge=1.0, le=3.0)

    def model_post_init(self, __context):
        if self.avail_width is None:
            self.avail_width = self.screen_width
        if self.avail_height is None:
            self.avail_height = self.screen_height - 40
