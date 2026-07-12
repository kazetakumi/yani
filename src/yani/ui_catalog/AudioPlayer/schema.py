"""AudioPlayer — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, WEIGHT_DESC


class AudioPlayerProps(BaseModel):
    url: DynStr = Field(description="audio URL (http/https only)")
    description: DynStr | None = Field(None, description="a title or summary shown with the player")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class AudioPlayerComponent(BaseModel):
    id: str
    component: Literal["AudioPlayer"]
    props: AudioPlayerProps
