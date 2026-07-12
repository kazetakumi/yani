"""DateTimeInput — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, PathBinding, WEIGHT_DESC


class DateTimeInputProps(BaseModel):
    value: PathBinding = Field(description="ALWAYS a path binding — where the ISO 8601 value lives")
    label: DynStr | None = Field(None, description="the input's label")
    enableDate: bool | None = Field(None, description="allow picking a date (default true)")
    enableTime: bool | None = Field(None, description="allow picking a time (default false)")
    min: str | None = Field(None, description="earliest allowed, ISO 8601")
    max: str | None = Field(None, description="latest allowed, ISO 8601")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class DateTimeInputComponent(BaseModel):
    id: str
    component: Literal["DateTimeInput"]
    props: DateTimeInputProps
