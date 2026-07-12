"""The component catalog — the contract side of every UI element.

One folder per component: SKILL.md (prose — when to pick it) + schema.py
(types — what props it takes, with binding rules as types). The composer
subagent's output is decoded directly against these models, so a prop shape
these types don't allow is UNREPRESENTABLE — an input component's `value` is
`PathBinding`, full stop (Option B, adopted 2026-07-11 after three strikes
against generic props). The composer's prompt specs are generated from the
same models via `component_spec` — one source of truth, nothing to drift.

This file is the explicit barrel, the server twin of static/catalog.js:
adding a component means adding its folder AND registering it in the three
lists below, on purpose. The union feeds constrained decoding — a missing
entry must fail loudly at import time, never silently shrink the menu.
"""
from pathlib import Path
from types import UnionType
from typing import Literal, Union, get_args, get_origin

from pydantic import BaseModel

from .base import PathBinding
from .Text.schema import TextComponent, TextProps
from .Image.schema import ImageComponent, ImageProps
from .Icon.schema import IconComponent, IconProps
from .Video.schema import VideoComponent, VideoProps
from .AudioPlayer.schema import AudioPlayerComponent, AudioPlayerProps
from .Row.schema import RowComponent, RowProps
from .Column.schema import ColumnComponent, ColumnProps
from .List.schema import ListComponent, ListProps
from .Card.schema import CardComponent, CardProps
from .Tabs.schema import TabsComponent, TabsProps
from .Modal.schema import ModalComponent, ModalProps
from .Divider.schema import DividerComponent, DividerProps
from .Button.schema import ButtonComponent, ButtonProps
from .TextField.schema import TextFieldComponent, TextFieldProps
from .CheckBox.schema import CheckBoxComponent, CheckBoxProps
from .ChoicePicker.schema import ChoicePickerComponent, ChoicePickerProps
from .Slider.schema import SliderComponent, SliderProps
from .DateTimeInput.schema import DateTimeInputComponent, DateTimeInputProps

# Lesson block components (spec 0001 — the mentor port)
from .LessonHeader.schema import LessonHeaderComponent, LessonHeaderProps
from .Heading.schema import HeadingComponent, HeadingProps
from .Prose.schema import ProseComponent, ProseProps
from .Definition.schema import DefinitionComponent, DefinitionProps
from .EquationBlock.schema import EquationBlockComponent, EquationBlockProps
from .FigureSketch.schema import FigureSketchComponent, FigureSketchProps
from .GraphBlock.schema import GraphBlockComponent, GraphBlockProps
from .CodeBlock.schema import CodeBlockComponent, CodeBlockProps
from .DataTable.schema import DataTableComponent, DataTableProps
from .ExplainBack.schema import ExplainBackComponent, ExplainBackProps
from .PracticeChecklist.schema import PracticeChecklistComponent, PracticeChecklistProps
from .QuizBlock.schema import QuizBlockComponent, QuizBlockProps
from .SummaryBlock.schema import SummaryBlockComponent, SummaryBlockProps
from .TreeLocator.schema import TreeLocatorComponent, TreeLocatorProps

# Checkpoint components (spec 0002 — the lesson dialogue)
from .ChipRow.schema import ChipRowComponent, ChipRowProps
from .PromptInput.schema import PromptInputComponent, PromptInputProps

# A plain (non-discriminated) union on purpose: Pydantic renders a
# discriminated union as JSON-Schema `oneOf`, which OpenAI's strict mode
# rejects — a plain union renders as the permitted `anyOf`, and each
# member's Literal `component` field disambiguates parsing regardless.
AnyComponent = Union[
    TextComponent, ImageComponent, IconComponent, VideoComponent, AudioPlayerComponent,
    RowComponent, ColumnComponent, ListComponent, CardComponent, TabsComponent,
    ModalComponent, DividerComponent, ButtonComponent, TextFieldComponent, CheckBoxComponent,
    ChoicePickerComponent, SliderComponent, DateTimeInputComponent,
    LessonHeaderComponent, HeadingComponent, ProseComponent, DefinitionComponent,
    EquationBlockComponent, FigureSketchComponent, GraphBlockComponent, CodeBlockComponent,
    DataTableComponent, ExplainBackComponent, PracticeChecklistComponent, QuizBlockComponent,
    SummaryBlockComponent, TreeLocatorComponent,
    ChipRowComponent, PromptInputComponent,
]


class ComposedSurface(BaseModel):
    components: list[AnyComponent]


PROPS_MODELS: dict[str, type[BaseModel]] = {
    "Text": TextProps,
    "Image": ImageProps,
    "Icon": IconProps,
    "Video": VideoProps,
    "AudioPlayer": AudioPlayerProps,
    "Row": RowProps,
    "Column": ColumnProps,
    "List": ListProps,
    "Card": CardProps,
    "Tabs": TabsProps,
    "Modal": ModalProps,
    "Divider": DividerProps,
    "Button": ButtonProps,
    "TextField": TextFieldProps,
    "CheckBox": CheckBoxProps,
    "ChoicePicker": ChoicePickerProps,
    "Slider": SliderProps,
    "DateTimeInput": DateTimeInputProps,
    "LessonHeader": LessonHeaderProps,
    "Heading": HeadingProps,
    "Prose": ProseProps,
    "Definition": DefinitionProps,
    "EquationBlock": EquationBlockProps,
    "FigureSketch": FigureSketchProps,
    "GraphBlock": GraphBlockProps,
    "CodeBlock": CodeBlockProps,
    "DataTable": DataTableProps,
    "ExplainBack": ExplainBackProps,
    "PracticeChecklist": PracticeChecklistProps,
    "QuizBlock": QuizBlockProps,
    "SummaryBlock": SummaryBlockProps,
    "TreeLocator": TreeLocatorProps,
    "ChipRow": ChipRowProps,
    "PromptInput": PromptInputProps,
}


def known_components() -> list[str]:
    return sorted(PROPS_MODELS)


_CATALOG_DIR = Path(__file__).parent


def component_doc(name: str) -> str:
    """The component's SKILL.md prose, frontmatter stripped — the judgment
    half of the contract; `component_spec` below carries the machine half."""
    text = (_CATALOG_DIR / name / "SKILL.md").read_text()
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:]
    return text.strip()


# --- prompt-spec generation (replaces schema.json) ---

def _type_str(annotation) -> str:
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        parts = [a for a in get_args(annotation) if a is not type(None)]
        return " or ".join(_type_str(p) for p in parts)
    if origin is Literal:
        return "one of: " + ", ".join(str(a) for a in get_args(annotation))
    if origin is list:
        return f"list of {_type_str(get_args(annotation)[0])}"
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        if annotation is PathBinding:
            return '{"path": ...} binding'
        return "{" + ", ".join(annotation.model_fields) + "} object"
    return {str: "string", float: "number", int: "integer", bool: "boolean"}.get(annotation, str(annotation))


def component_spec(name: str) -> str:
    """A compact prop spec for the composer prompt, generated from the same
    models the decoder enforces — one source of truth, nothing to drift."""
    lines = ["Props:"]
    for pname, field in PROPS_MODELS[name].model_fields.items():
        req = "required" if field.is_required() else "optional, null if unused"
        desc = f" — {field.description}" if field.description else ""
        lines.append(f"- {pname} ({_type_str(field.annotation)}; {req}){desc}")
    return "\n".join(lines)
