import inspect
from time import time
from typing import get_args, get_origin

from ..observability import Logger
from ..workspace import (
    add_note, create_concept, read_concept, read_workspace,
    set_active_concept, tick_concept_progress, update_about,
    update_concept_about, update_mission, write_learning_record,
)
from .weather import get_weather
from .skill import load_skill
from .lesson import next_block, plan_lesson, start_lesson
from .ui import create_surface, update_components, update_data

logger = Logger()


_PY_TYPE_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _schema_for(fn) -> dict:
    """Derive a tool's JSON schema from its type-hinted signature and docstring."""
    sig = inspect.signature(fn)
    properties = {}
    required = []

    for name, param in sig.parameters.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            raise TypeError(f"tool '{fn.__name__}' parameter '{name}' needs a type hint")
        # list[str] etc.: declare the element type, or a small model invents
        # richer structure to fill the vacuum (the 2026-07-12 set_syllabus
        # dicts-for-strings incident — a bare {"type": "array"} is a vacuum)
        if get_origin(annotation) is list:
            args = get_args(annotation)
            inner = _PY_TYPE_TO_JSON.get(args[0], "string") if args else "string"
            properties[name] = {"type": "array", "items": {"type": inner}}
            if param.default is inspect.Parameter.empty:
                required.append(name)
            continue
        json_type = _PY_TYPE_TO_JSON.get(annotation)
        if json_type is None:
            raise TypeError(
                f"tool '{fn.__name__}' parameter '{name}' has unsupported type "
                f"{annotation!r} — only {list(_PY_TYPE_TO_JSON)} and list[...] are supported"
            )
        properties[name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    doc = inspect.getdoc(fn)
    if not doc:
        raise ValueError(f"tool '{fn.__name__}' needs a docstring to use as its description")

    return {
        "type": "function",
        "name": fn.__name__,
        "description": doc.strip().splitlines()[0],
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }


class ToolExecutor:

    def __init__(self):
        self._tool_impls = {
            "get_weather": get_weather,
            "load_skill": load_skill,
            "create_surface": create_surface,
            "update_components": update_components,
            "update_data": update_data,
            "plan_lesson": plan_lesson,
            "start_lesson": start_lesson,
            "next_block": next_block,
            "read_workspace": read_workspace,
            "update_mission": update_mission,
            "create_concept": create_concept,
            "read_concept": read_concept,
            "update_concept_about": update_concept_about,
            "tick_concept_progress": tick_concept_progress,
            "set_active_concept": set_active_concept,
            "write_learning_record": write_learning_record,
            "add_note": add_note,
            "update_about": update_about,
        }

    def get_tools(self) -> list[dict]:
        return [_schema_for(fn) for fn in self._tool_impls.values()]

    def execute(self, tool_name: str, args: dict):
        if tool_name not in self._tool_impls:
            raise KeyError(f"no such tool: {tool_name}")

        fn = self._tool_impls[tool_name]
        # Streaming tools (ADR 0001): a generator tool yields UI events while
        # it runs; its return value is the transcript ack. Wrap the whole
        # iteration so a mid-stream failure still resolves to an ERROR
        # string (blocks already emitted stand) and the call still logs.
        if inspect.isgeneratorfunction(fn):
            return self._execute_streaming(tool_name, fn, args)

        try:
            s = time()
            result = fn(**args)
            e = time()
            logger.log_tool_call(tool_name, (e-s), True, args)
            return result
        except Exception as error:
            e = time()
            logger.log_tool_call(tool_name, (e-s), False, args)
            return f"ERROR: {type(error).__name__}: {error}"

    def _execute_streaming(self, tool_name: str, fn, args: dict):
        s = time()
        try:
            result = yield from fn(**args)
            logger.log_tool_call(tool_name, (time() - s), True, args)
            return result if result is not None else ""
        except Exception as error:
            logger.log_tool_call(tool_name, (time() - s), False, args)
            return f"ERROR: {type(error).__name__}: {error}"
