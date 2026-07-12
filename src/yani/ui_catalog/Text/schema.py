"""Text — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, WEIGHT_DESC


class TextProps(BaseModel):
    text: DynStr = Field(description="the text to display (rendered as plain text)")
    variant: Literal["body", "caption"] | None = Field(None, description="\"caption\" is smaller and muted")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class TextComponent(BaseModel):
    id: str
    component: Literal["Text"]
    props: TextProps
