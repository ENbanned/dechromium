from __future__ import annotations

from pydantic import BaseModel

from ._enums import FontPack


class Fonts(BaseModel):
    font_pack: FontPack = FontPack.WINDOWS
