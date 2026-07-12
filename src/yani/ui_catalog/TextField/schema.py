"""TextField — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, PathBinding, WEIGHT_DESC


class TextFieldProps(BaseModel):
    value: PathBinding = Field(description="ALWAYS a path binding — the data-model slot where the user's input lives")
    label: DynStr | None = Field(None, description="the field's label")
    placeholder: DynStr | None = Field(None, description="placeholder shown when empty")
    variant: Literal["shortText", "longText", "number", "obscured"] | None = Field(None, description="input type")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class TextFieldComponent(BaseModel):
    id: str
    component: Literal["TextField"]
    props: TextFieldProps
