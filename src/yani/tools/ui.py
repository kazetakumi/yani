import json
from typing import Literal

from pydantic import BaseModel

from .. import skill_registry, surface_store
from ..agent_prompts import agent_prompt as _agent_prompt
from ..llm import LLM, get_client, DEFAULT_MODEL
from ..ui_catalog import ComposedSurface, component_doc, component_spec, known_components


class DataValue(BaseModel):
    path: str
    value: str | int | float | bool


class DataModelUpdate(BaseModel):
    values: list[DataValue]


# Generated from the barrel at import time — the designer's selection is
# constrained to real component names by decoding, the same way Option B made
# bad prop shapes unrepresentable. A new catalog folder + barrel entry grows
# this Literal automatically; nothing to keep in sync by hand.
ComponentName = Literal[tuple(known_components())]  # type: ignore[valid-type]


class SurfaceDesign(BaseModel):
    selected_components: list[ComponentName]
    layout_plan: str


def _component_to_dict(component) -> dict:
    """Typed component -> the client's wire shape. exclude_none drops the
    nulls strict decoding forces the model to emit for unused optionals;
    a Button's context converts from typed entries back to an object."""
    props = component.props.model_dump(exclude_none=True)
    action = props.get("action")
    if action and isinstance(action.get("event", {}).get("context"), list):
        action["event"]["context"] = {
            e["key"]: e["value"] for e in action["event"]["context"]
        }
    return {"id": component.id, "component": component.component, "props": props}


def _component_specs(names: list) -> str:
    return "\n\n".join(
        f"### {name}\n{component_doc(name)}\n\n{component_spec(name)}" for name in names
    )


def _bindings_of(components: list) -> list:
    paths = []
    for comp in components:
        for value in comp.get("props", {}).values():
            if isinstance(value, dict) and set(value) == {"path"}:
                paths.append(value["path"])
    return paths


def create_surface(surface_id: str):
    """Create a new UI surface. Requires the ui-builder skill to be loaded first (call load_skill). Must be called before update_components or update_data reference the same surface_id."""
    # Progressive-disclosure guard: the UI workflow rules live in the skill
    # body, not the system prompt — refuse to build until the model has
    # actually fetched them, so a small model can't compose blind.
    if not skill_registry.is_loaded("ui-builder"):
        raise ValueError(
            "the ui-builder skill is not loaded — call "
            "load_skill(skill_name='ui-builder'), follow the workflow it "
            "returns, then create the surface"
        )
    surface_store.create(surface_id)  # raises if the id already exists
    return {"surface_id": surface_id}


def _design_surface(llm: LLM, brief: str) -> SurfaceDesign:
    """Stage 1 of update_components: the ui-designer subagent turns the brief
    into a component selection + layout plan. Selection is constrained to
    real catalog names by decoding (ComponentName Literal)."""
    menu = "\n\n".join(
        f"### {name}\n{component_doc(name)}" for name in known_components()
    )
    design = llm.run_structured(
        [{"role": "system", "content": _agent_prompt("ui-designer")},
         {"role": "user", "content": f"brief: {brief}\n\nComponent menu:\n\n{menu}"}],
        SurfaceDesign,
        step="subagent.design",
    )
    # the one structural invariant the whole stack assumes — cheaper to
    # guarantee here than to fail the composer over a designer omission
    if "Column" not in design.selected_components:
        design.selected_components.append("Column")
    return design


def update_components(surface_id: str, brief: str):
    """Design and build this surface's full component tree in one call. brief describes what the surface must show and do — a UI/UX design step selects the components, so describe the experience, don't name components."""
    if not surface_store.exists(surface_id):
        raise ValueError(f"unknown surface '{surface_id}' — call create_surface first")

    llm = LLM(get_client(), DEFAULT_MODEL)

    # Stage 1 — ui-designer: brief -> component selection + layout plan.
    design = _design_surface(llm, brief)

    user = (
        f"surface_id: {surface_id}\n"
        f"brief: {brief}\n"
        f"design plan: {design.layout_plan}\n\n"
        f"Component specs:\n\n{_component_specs(design.selected_components)}"
    )

    # Stage 2 — ui-composer: one structured call decoded against the typed
    # catalog (ui_catalog/): per-component prop contracts — an input's value
    # being a PathBinding, option lists being {label, value} — are enforced
    # during decoding, not validated after. Remaining semantic slips (a
    # dangling child id) still degrade to visible error chips client-side.
    parsed = llm.run_structured(
        [{"role": "system", "content": _agent_prompt("ui-composer")},
         {"role": "user", "content": user}],
        ComposedSurface,
        step="subagent.compose",
    )

    components = [_component_to_dict(c) for c in parsed.components]
    surface_store.set_components(surface_id, components)
    return {"surface_id": surface_id, "components": components}


def update_data(surface_id: str, data_brief: str):
    """Fill in real values for this surface's path bindings, in one call. data_brief states the values in plain words (e.g. 'Paris is sunny, 70 degrees Fahrenheit')."""
    surface = surface_store.get(surface_id)
    if surface is None:
        raise ValueError(f"unknown surface '{surface_id}' — call create_surface first")
    if surface["components"] is None:
        raise ValueError(f"surface '{surface_id}' has no components yet — call update_components first")

    bindings = _bindings_of(surface["components"])
    if not bindings:
        raise ValueError(f"surface '{surface_id}' declares no path bindings — nothing to fill")

    user = (
        f"surface_id: {surface_id}\n"
        f"binding paths: {json.dumps(bindings)}\n"
        f"component tree: {json.dumps(surface['components'])}\n"
        f"data_brief: {data_brief}"
    )

    # One structured call, no path validation (Option A): an invented path
    # writes to nowhere and the bound prop stays visibly pending client-side.
    llm = LLM(get_client(), DEFAULT_MODEL)
    parsed = llm.run_structured(
        [{"role": "system", "content": _agent_prompt("ui-data-writer")},
         {"role": "user", "content": user}],
        DataModelUpdate,
        step="subagent.data",
    )

    values = {v.path: v.value for v in parsed.values}
    surface_store.update_data(surface_id, values)
    return {"surface_id": surface_id, "values": values}
