"""CodeBlock — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class CodeBlockProps(BaseModel):
    title: str = Field(description='listing title, e.g. "Listing 3.1 - teacher builds"')
    language: str = Field(description='shown in the header, e.g. "python"')
    code: str = Field(description="the code, plain text; ____ (4+ underscores) marks a fill-in blank")
    blank_hint: str | None = Field(None, description="what belongs in the blank, shown inside it")


class CodeBlockComponent(BaseModel):
    id: str
    component: Literal["CodeBlock"]
    props: CodeBlockProps
