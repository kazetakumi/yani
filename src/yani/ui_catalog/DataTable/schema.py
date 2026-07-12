"""DataTable — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class DataTableProps(BaseModel):
    headers: list[str]
    rows: list[list[str]] = Field(description="each row has one cell per header; inline markdown and TeX \\( .. \\) allowed in cells")


class DataTableComponent(BaseModel):
    id: str
    component: Literal["DataTable"]
    props: DataTableProps
