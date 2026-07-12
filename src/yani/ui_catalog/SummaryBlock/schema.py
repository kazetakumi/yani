"""SummaryBlock — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class SummaryBlockProps(BaseModel):
    title: str = Field(description="the lesson title, restated")
    mental_model: str = Field(description="the final one-line mental model - the product of the lesson")
    points: list[str] = Field(description="numbered key points, most important first")


class SummaryBlockComponent(BaseModel):
    id: str
    component: Literal["SummaryBlock"]
    props: SummaryBlockProps
