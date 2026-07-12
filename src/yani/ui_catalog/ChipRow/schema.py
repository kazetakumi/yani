"""ChipRow — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class Chip(BaseModel):
    label: str = Field(description="what the chip says, short")
    action: str = Field(description="wire action name dispatched on click, e.g. 'steer', 'start_lesson'")
    value: str | None = Field(None, description="carried in the action context as 'value' — e.g. a steering signal")
    variant: Literal["primary", "chip", "quiet"] | None = Field(None, description="primary = the main path; quiet = the visually subordinate escape (skips)")


class ChipRowProps(BaseModel):
    chips: list[Chip] = Field(description="1-4 chips; at most one primary")
    note: str | None = Field(None, description="one small muted line above the chips — a gentle nudge, never a lecture")


class ChipRowComponent(BaseModel):
    id: str
    component: Literal["ChipRow"]
    props: ChipRowProps
