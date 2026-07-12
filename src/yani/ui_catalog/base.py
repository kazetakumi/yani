"""Shared building blocks every component schema imports.

(Named base.py, not types.py, because the barrel also needs stdlib
`types` for UnionType — a same-named sibling would read ambiguously.)
"""
from typing import Literal

from pydantic import BaseModel


class PathBinding(BaseModel):
    """A reference into the surface's data model: {"path": "/surface/field"}."""
    path: str


# Dynamic props: a literal now, or a binding filled later via update_data.
DynStr = str | PathBinding
DynNum = float | PathBinding
DynBool = bool | PathBinding


WEIGHT_DESC = "relative weight within a Row/Column, like CSS flex-grow; null for natural sizing"


JUSTIFY = Literal["start", "center", "end", "spaceBetween", "spaceAround", "spaceEvenly", "stretch"]
ALIGN = Literal["start", "center", "end", "stretch"]
