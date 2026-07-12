"""The durable lesson store (spec 0002, ADR 0002: the harness owns the cursor).

Every planned lesson's beat list, cursor, and steering counters live in this
learner's lessons.json, a sibling of state.json/surfaces.json in their
learner home (multi-user-workspaces map, ticket 06 — missed by ticket 01's
initial sweep since this module wasn't in its explicit list). Same
read-modify-write discipline as the surface store: the file is small, exactly
one user is current per running process, and statelessness across dev-server
reloads is the point.

The mentor model never recites the plan back — it steers with
next_block(lesson_id, steering, note) and this store decides what "next"
means. A lesson can therefore never drift from the roadmap the learner
was shown on the Overview."""

import json

from . import users

_EMPTY = {"lessons": {}}

# status lifecycle: planned -> teaching -> done
STATUSES = ("planned", "teaching", "done")
MAX_REANCHORS = 2  # the original skill's cap: re-enter at B at most twice, then move on


def _store_file():
    return users.learner_home() / "lessons.json"


def _load() -> dict:
    store_file = _store_file()
    if store_file.exists():
        return json.loads(store_file.read_text())
    return json.loads(json.dumps(_EMPTY))


def _save(data: dict):
    store_file = _store_file()
    store_file.parent.mkdir(parents=True, exist_ok=True)
    store_file.write_text(json.dumps(data, indent=2))


def create(lesson_id: str, number: int, plan: dict, beats: list[dict]):
    data = _load()
    if lesson_id in data["lessons"]:
        raise ValueError(f"lesson '{lesson_id}' already exists")
    data["lessons"][lesson_id] = {
        "number": number,
        "plan": plan,
        "beats": beats,
        "cursor": 0,          # index of the next beat to stream
        "status": "planned",
        "reanchor_count": 0,
    }
    _save(data)


def get(lesson_id: str) -> dict | None:
    return _load()["lessons"].get(lesson_id)


def require(lesson_id: str) -> dict:
    lesson = get(lesson_id)
    if lesson is None:
        raise ValueError(f"unknown lesson '{lesson_id}' — call plan_lesson first")
    return lesson


def update(lesson_id: str, **fields):
    data = _load()
    if lesson_id not in data["lessons"]:
        raise ValueError(f"unknown lesson '{lesson_id}'")
    data["lessons"][lesson_id].update(fields)
    _save(data)
