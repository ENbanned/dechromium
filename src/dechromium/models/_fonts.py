from __future__ import annotations

from pydantic import BaseModel, Field

from ._enums import FontPack


class Fonts(BaseModel):
    font_pack: FontPack = FontPack.WINDOWS
    font_families: list[str] = Field(default_factory=list)
