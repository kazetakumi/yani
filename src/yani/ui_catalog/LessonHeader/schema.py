"""LessonHeader — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class LessonHeaderProps(BaseModel):
    eyebrow: str = Field(description='e.g. "Lesson 0003"')
    title: str = Field(description="the lesson title")
    subtitle: str = Field(description="one-line promise of the lesson")
    loop_plan: str | None = Field(None, description="teacher-side shorthand line; null on the learner-facing Overview (spec 0002: letter codes are never shown to the learner)")


class LessonHeaderComponent(BaseModel):
    id: str
    component: Literal["LessonHeader"]
    props: LessonHeaderProps
