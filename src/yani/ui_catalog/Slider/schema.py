"""Slider — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, PathBinding, WEIGHT_DESC


class SliderProps(BaseModel):
    value: PathBinding = Field(description="ALWAYS a path binding — where the numeric value lives")
    label: DynStr | None = Field(None, description="the slider's label")
    min: float | None = Field(None, description="minimum value")
    max: float | None = Field(None, description="maximum value")
    steps: int | None = Field(None, description="discrete divisions; null for continuous")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class SliderComponent(BaseModel):
    id: str
    component: Literal["Slider"]
    props: SliderProps
