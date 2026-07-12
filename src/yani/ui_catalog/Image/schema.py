"""Image — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, WEIGHT_DESC


class ImageProps(BaseModel):
    url: DynStr = Field(description="image URL (http/https only)")
    description: DynStr | None = Field(None, description="accessibility text")
    fit: Literal["contain", "cover", "fill", "none", "scaleDown"] | None = Field(None, description="resize behavior")
    variant: Literal["icon", "avatar", "smallFeature", "mediumFeature", "largeFeature", "header"] | None = \
        Field(None, description="size/style hint")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class ImageComponent(BaseModel):
    id: str
    component: Literal["Image"]
    props: ImageProps
