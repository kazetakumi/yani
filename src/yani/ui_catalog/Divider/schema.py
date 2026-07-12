"""Divider — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import WEIGHT_DESC


class DividerProps(BaseModel):
    axis: Literal["horizontal", "vertical"] | None = Field(None, description="orientation, default horizontal")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class DividerComponent(BaseModel):
    id: str
    component: Literal["Divider"]
    props: DividerProps
