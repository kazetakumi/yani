"""List — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import ALIGN, WEIGHT_DESC


class ListProps(BaseModel):
    children: list[str] = Field(description="ids of components already in this surface's list")
    direction: Literal["vertical", "horizontal"] | None = Field(None, description="scroll direction, default vertical")
    align: ALIGN | None = Field(None, description="cross-axis alignment")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class ListComponent(BaseModel):
    id: str
    component: Literal["List"]
    props: ListProps
