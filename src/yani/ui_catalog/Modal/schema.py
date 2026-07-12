"""Modal — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal
from pydantic import BaseModel, Field
from ..base import WEIGHT_DESC


class ModalProps(BaseModel):
    trigger: str = Field(description="id of the component that opens the modal when clicked (e.g. a Button)")
    content: str = Field(description="id of the component shown inside the modal")
    weight: float | None = Field(None, description=WEIGHT_DESC)


class ModalComponent(BaseModel):
    id: str
    component: Literal["Modal"]
    props: ModalProps
