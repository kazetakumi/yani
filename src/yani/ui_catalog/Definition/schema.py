"""Definition — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class DefinitionProps(BaseModel):
    label: str = Field(description='the callout label, e.g. "Definition - reducer" or "Mental model v1"')
    text: str = Field(description="the one-or-two-sentence content")
    variant: Literal["plain", "model", "break"] = Field(description="plain=new term (tan), model=mental model (sage), break=where the analogy breaks (red dashed)")


class DefinitionComponent(BaseModel):
    id: str
    component: Literal["Definition"]
    props: DefinitionProps
