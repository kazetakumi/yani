"""Prose — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class ProseProps(BaseModel):
    paragraphs: list[str] = Field(description="each entry is one paragraph; inline markdown (**bold**, *italic*, `code`) allowed")


class ProseComponent(BaseModel):
    id: str
    component: Literal["Prose"]
    props: ProseProps
