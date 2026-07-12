"""ChoicePicker — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import DynStr, PathBinding, WEIGHT_DESC


class OptionItem(BaseModel):
    label: str = Field(description="the text shown for this option")
    value: str = Field(description="the stable value written into the selection")


class ChoicePickerProps(BaseModel):
    options: list[OptionItem] = Field(description="the choices; labels are the full text the user should read")
    value: PathBinding = Field(description="ALWAYS a path binding — where the selected values (a string array) live")
    label: DynStr | None = Field(None, description="label for the group")
    variant: Literal["multipleSelection", "mutuallyExclusive"] | None = Field(None, description="pick-many vs pick-one")
    displayStyle: Literal["checkbox", "chips"] | None = Field(None, description="visual style")
    filterable: bool | None = Field(None, description="show a filter input above the options")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class ChoicePickerComponent(BaseModel):
    id: str
    component: Literal["ChoicePicker"]
    props: ChoicePickerProps
