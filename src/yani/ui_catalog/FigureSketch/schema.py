"""FigureSketch — the machine half of the contract. SKILL.md alongside carries the judgment half."""
from typing import Literal, Union
from pydantic import BaseModel, Field


class SketchLine(BaseModel):
    kind: Literal["line"]
    x1: float; y1: float; x2: float; y2: float


class SketchArrow(BaseModel):
    kind: Literal["arrow"]
    x1: float; y1: float; x2: float; y2: float


class SketchRect(BaseModel):
    kind: Literal["rect"]
    x: float; y: float; w: float; h: float


class SketchCircle(BaseModel):
    kind: Literal["circle"]
    cx: float; cy: float; r: float


class SketchLabel(BaseModel):
    kind: Literal["label"]
    x: float; y: float
    text: str


class SketchAxes(BaseModel):
    kind: Literal["axes"]
    ox: float = Field(description="origin x, e.g. 70")
    oy: float = Field(description="origin y (bottom-left of the plot area), e.g. 270")
    x_len: float = Field(description="x axis length rightward, e.g. 500")
    y_len: float = Field(description="y axis length upward, e.g. 210")
    x_label: str | None = None
    y_label: str | None = None


class SketchCurve(BaseModel):
    kind: Literal["curve"]
    points: list[list[float]] = Field(description="[[x,y], ...] waypoints; the renderer draws a smooth wobbly curve through them")


SketchElement = Union[SketchLine, SketchArrow, SketchRect, SketchCircle, SketchLabel, SketchAxes, SketchCurve]


class FigureSketchProps(BaseModel):
    figure_label: str = Field(description='e.g. "Figure 3.1"')
    caption: str = Field(description="one line naming what the eye should find")
    elements: list[SketchElement] = Field(description="drawn in order on a 640x320 canvas; y grows downward")


class FigureSketchComponent(BaseModel):
    id: str
    component: Literal["FigureSketch"]
    props: FigureSketchProps
