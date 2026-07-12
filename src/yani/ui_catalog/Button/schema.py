"""Button — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import PathBinding, WEIGHT_DESC


class ContextEntry(BaseModel):
    key: str
    value: str | float | bool | PathBinding = Field(
        description="a literal, or a {\"path\"} binding resolved from the data model when the user clicks")


class ActionEvent(BaseModel):
    name: str = Field(description="the action name dispatched to the server")
    context: list[ContextEntry] = Field(
        description="how user input travels back: bind entries to the input paths this click should carry")


class ActionSpec(BaseModel):
    event: ActionEvent


class ButtonProps(BaseModel):
    child: str = Field(description="id of the label component — use a Text")
    action: ActionSpec = Field(description="dispatched to the server as a [UI action] turn on click")
    variant: Literal["default", "primary", "borderless"] | None = Field(None, description="style hint; at most one primary per surface")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class ButtonComponent(BaseModel):
    id: str
    component: Literal["Button"]
    props: ButtonProps
