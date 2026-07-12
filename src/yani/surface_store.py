"""The durable surface store (spec 0001: lessons survive reloads).

Every surface's final structure and data live in this learner's
surfaces.json, a sibling of state.json in their learner home (multi-user-
workspaces map, ticket 01). Read-modify-write per operation, deliberately:
the file is small, exactly one user is current per running process, and
statelessness across server reloads is the whole point — the reload=True
dev server wipes module memory freely.

/history replays surfaces from here, positioned by the conversation's
function_call entries (state.json stays a pure LLM transcript)."""

import json

from . import users

_EMPTY = {"lesson_seq": 0, "surfaces": {}}


def _store_file():
    return users.learner_home() / "surfaces.json"


def _load() -> dict:
    store_file = _store_file()
    if store_file.exists():
        return json.loads(store_file.read_text())
    return json.loads(json.dumps(_EMPTY))


def _save(data: dict):
    store_file = _store_file()
    store_file.parent.mkdir(parents=True, exist_ok=True)
    store_file.write_text(json.dumps(data, indent=2))


def create(surface_id: str):
    data = _load()
    if surface_id in data["surfaces"]:
        raise ValueError(f"surface '{surface_id}' already exists — pick a new id")
    data["surfaces"][surface_id] = {"components": None, "data": {}}
    _save(data)


def exists(surface_id: str) -> bool:
    return surface_id in _load()["surfaces"]


def get(surface_id: str) -> dict | None:
    return _load()["surfaces"].get(surface_id)


def set_components(surface_id: str, components: list):
    data = _load()
    if surface_id not in data["surfaces"]:
        raise ValueError(f"unknown surface '{surface_id}' — call create_surface first")
    data["surfaces"][surface_id]["components"] = components
    _save(data)


def update_data(surface_id: str, values: dict):
    data = _load()
    if surface_id not in data["surfaces"]:
        raise ValueError(f"unknown surface '{surface_id}' — call create_surface first")
    data["surfaces"][surface_id]["data"].update(values)
    _save(data)


def next_lesson_number() -> int:
    data = _load()
    data["lesson_seq"] += 1
    _save(data)
    return data["lesson_seq"]


def replay_events(surface_id: str) -> list[dict]:
    """The wire events that rebuild one surface, for /history."""
    surface = get(surface_id)
    if surface is None:
        return []
    events = [{"type": "ui.createSurface", "surface_id": surface_id}]
    if surface["components"] is not None:
        events.append({"type": "ui.updateComponents", "surface_id": surface_id,
                       "components": surface["components"]})
    if surface["data"]:
        events.append({"type": "ui.updateDataModel", "surface_id": surface_id,
                       "values": surface["data"]})
    return events
