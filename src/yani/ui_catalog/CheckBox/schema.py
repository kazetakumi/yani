"""CheckBox — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, PathBinding, WEIGHT_DESC


class CheckBoxProps(BaseModel):
    value: PathBinding = Field(description="ALWAYS a path binding — where the checked state lives")
    label: DynStr | None = Field(None, description="text next to the checkbox")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class CheckBoxComponent(BaseModel):
    id: str
    component: Literal["CheckBox"]
    props: CheckBoxProps
