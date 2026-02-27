from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


def _hex12() -> str:
    return uuid.uuid4().hex[:12]


class Noise(BaseModel):
    canvas_seed: str = Field(default_factory=_hex12)
    audio_seed: str = Field(default_factory=_hex12)
    clientrects_seed: str = Field(default_factory=_hex12)
    webgl_seed: str = Field(default_factory=_hex12)
