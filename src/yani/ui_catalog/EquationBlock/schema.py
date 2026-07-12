"""EquationBlock — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class EquationBlockProps(BaseModel):
    label: str = Field(description='e.g. "Equation 3.1"')
    tex: str = Field(description="display TeX, without surrounding \\[ \\] delimiters")
    tag: str | None = Field(None, description='equation number shown at the right, e.g. "(3.1)"')
    caption: str | None = Field(None, description='read-aloud line, e.g. "what is left is the start, times decay"')


class EquationBlockComponent(BaseModel):
    id: str
    component: Literal["EquationBlock"]
    props: EquationBlockProps
