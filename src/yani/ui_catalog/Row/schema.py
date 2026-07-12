"""Row — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import ALIGN, JUSTIFY, WEIGHT_DESC


class RowProps(BaseModel):
    children: list[str] = Field(description="ids of components already in this surface's list, left to right")
    justify: JUSTIFY | None = Field(None, description="main-axis arrangement")
    align: ALIGN | None = Field(None, description="cross-axis alignment")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class RowComponent(BaseModel):
    id: str
    component: Literal["Row"]
    props: RowProps
