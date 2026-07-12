"""Tabs — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import WEIGHT_DESC


class TabItem(BaseModel):
    title: str = Field(description="the tab title")
    child: str = Field(description="id of the component shown when this tab is active")


class TabsProps(BaseModel):
    tabs: list[TabItem] = Field(description="one entry per tab")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class TabsComponent(BaseModel):
    id: str
    component: Literal["Tabs"]
    props: TabsProps
