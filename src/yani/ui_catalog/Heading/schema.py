"""Heading — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class HeadingProps(BaseModel):
    letter: str | None = Field(None, description='the block tag, e.g. "A · HOOK"; null for a plain heading')
    text: str = Field(description="the heading text (gets the highlighter swipe)")


class HeadingComponent(BaseModel):
    id: str
    component: Literal["Heading"]
    props: HeadingProps
