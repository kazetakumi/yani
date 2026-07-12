"""Video — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, WEIGHT_DESC


class VideoProps(BaseModel):
    url: DynStr = Field(description="video URL (http/https only)")
    posterUrl: DynStr | None = Field(None, description="poster image shown before playback")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class VideoComponent(BaseModel):
    id: str
    component: Literal["Video"]
    props: VideoProps
