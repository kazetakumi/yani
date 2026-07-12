"""Card — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import WEIGHT_DESC


class CardProps(BaseModel):
    child: str = Field(description="id of the single child — wrap multiple elements in a Column first")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class CardComponent(BaseModel):
    id: str
    component: Literal["Card"]
    props: CardProps
