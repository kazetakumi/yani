"""QuizBlock — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class QuizOption(BaseModel):
    text: str = Field(description="the option, similar length to the others, no formatting tells")
    correct: bool
    explain: str = Field(description="why this option is right or wrong, briefly")


class QuizBlockProps(BaseModel):
    quiz_label: str = Field(description='e.g. "Quiz 3.1"')
    topic: str = Field(description="the concept this question checks, a few words")
    question: str = Field(description="a concrete question that applies the concept")
    options: list[QuizOption] = Field(description="2-4 options, exactly one with correct=true")


class QuizBlockComponent(BaseModel):
    id: str
    component: Literal["QuizBlock"]
    props: QuizBlockProps
