"""ExplainBack — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class ExplainBackProps(BaseModel):
    prompt_text: str = Field(description="what to explain, addressed to the learner")
    placeholder: str = Field(description='textarea placeholder, e.g. "No jargon. What is it, really?"')


class ExplainBackComponent(BaseModel):
    id: str
    component: Literal["ExplainBack"]
    props: ExplainBackProps
