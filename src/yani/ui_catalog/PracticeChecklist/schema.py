"""PracticeChecklist — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class PracticeChecklistProps(BaseModel):
    label: str = Field(description='e.g. "Practice"')
    steps: list[str] = Field(description="each entry is one concrete, doable step")


class PracticeChecklistComponent(BaseModel):
    id: str
    component: Literal["PracticeChecklist"]
    props: PracticeChecklistProps
