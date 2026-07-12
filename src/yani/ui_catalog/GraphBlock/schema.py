"""GraphBlock — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field


class GraphBlockProps(BaseModel):
    title: str = Field(description='e.g. "Graph 3.1 - decay rate"')
    family: Literal["exp_decay", "exp_growth", "sine", "linear", "quadratic", "logistic"] = Field(
        description="the plotted function family; the slider's parameter k drives it")
    param_label: str = Field(description='slider label, e.g. "k"')
    param_min: float
    param_max: float
    param_default: float
    x_max: float = Field(description="plot x from 0 to this")
    caption: str = Field(description="what to notice as the parameter moves")


class GraphBlockComponent(BaseModel):
    id: str
    component: Literal["GraphBlock"]
    props: GraphBlockProps
