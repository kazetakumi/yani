"""TreeLocator — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class TreeLocatorProps(BaseModel):
    branches_from: str = Field(description="the concept/lesson this builds on")
    unlocks_next: str = Field(description="what this lesson makes possible next")
    primary_source: str | None = Field(None, description="one real, well-known source by NAME (book, canonical doc); never a fabricated URL or quote")


class TreeLocatorComponent(BaseModel):
    id: str
    component: Literal["TreeLocator"]
    props: TreeLocatorProps
