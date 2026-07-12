"""PromptInput — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class PromptInputProps(BaseModel):
    prompt_text: str = Field(description="the question or task, addressed to the learner")
    placeholder: str = Field(description="textarea placeholder, inviting not demanding")
    submit_label: str = Field(description='e.g. "Send my guess", "Send my answer"')
    action: str = Field(description="wire action name for the submission, e.g. 'guess', 'try_one'; the text rides in context.text")
    skip_label: str | None = Field(None, description='the one-tap escape, e.g. "No idea — show me", "Skip for now"; null when the input is not skippable')
    skip_action: str | None = Field(None, description="wire action name for the escape, e.g. 'guess_skip', 'skip_checkpoint'")
    note: str | None = Field(None, description="one small muted line under the input — a gentle nudge to stay, used at most once per lesson")


class PromptInputComponent(BaseModel):
    id: str
    component: Literal["PromptInput"]
    props: PromptInputProps
