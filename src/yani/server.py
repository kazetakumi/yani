import ast
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .harness import loop
import uuid
from . import surface_store, users, workspace
from .session import session_id_store
from .state import State

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI()

# Per-request identity (docs/adr/0001-per-request-cookie-identity.md): the
# cookie value IS the learner's slug — no server-side session table. There's
# no auth here (no password), so an opaque token would buy no real security
# over the slug being readable; it would just add a lookup table that also
# needs to survive the dev server's reload=True wiping module memory.
# httponly blocks JS from reading/editing it (XSS hardening; the browser
# attaches it to fetch() automatically, JS never needs to touch it itself).
_USER_COOKIE = "yani_user"
_USER_COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # long-lived: "remember me" per browser


@app.middleware("http")
async def _resolve_user_from_cookie(request: Request, call_next):
    # Populates users.py's per-request contextvar from the cookie before any
    # handler runs, so every learner_home() call downstream (workspace.py,
    # state.py, surface_store.py) resolves to the right learner without
    # threading the request through each of them individually.
    #
    # The cookie is client-supplied and never re-validated by the browser,
    # unlike /login's slug which always comes from slugify(). A crafted
    # value like "../../etc" would otherwise reach learner_home()'s
    # WORKSPACE_ROOT / slug join and escape the workspace root — so only
    # trust it if it matches slugify()'s own output shape.
    raw = request.cookies.get(_USER_COOKIE)
    users.set_current_user(raw if raw and users.is_valid_slug(raw) else None)
    return await call_next(request)

class ChatRequest(BaseModel):
    message: str

class ActionRequest(BaseModel):
    surfaceId: str
    name: str
    context: dict = {}

class HistoryEndpointResponse(BaseModel):
    items: list[dict]

class LoginRequest(BaseModel):
    name: str

class WhoamiResponse(BaseModel):
    user: str | None

class LoginResponse(BaseModel):
    user: str
    is_new: bool

# Written once, at learner-home creation, before any lesson or interview
# happens — ticket 04's update_about tool takes over from here as the model
# actually gets to know the person during conversation.
_ABOUT_STARTER_TEMPLATE = "# {name}\n\n*(nothing learned about {name} yet.)*\n"


def _require_current_user():
    # /chat, /action, /history all bottom out in workspace.py/state.py/
    # surface_store.py, which raise a bare RuntimeError via users.learner_home()
    # if nobody's logged in yet. Turn that into a clean 401 here instead of a
    # 500 traceback, so the frontend (ticket 03) has a real signal to show
    # the name-entry modal on instead of a stale session.
    if users.current_user() is None:
        raise HTTPException(status_code=401, detail="no current user — log in first")


@app.get("/whoami")
def whoami():
    return WhoamiResponse(user=users.current_user())


@app.post("/login")
def login(req: LoginRequest):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    slug = users.resolve_user_slug(name)
    home = users.ensure_learner_home(slug)
    about_path = home / "about.md"
    is_new = not about_path.exists()
    if is_new:
        about_path.write_text(_ABOUT_STARTER_TEMPLATE.format(name=name))
    users.set_current_user(slug)
    response = JSONResponse(LoginResponse(user=slug, is_new=is_new).model_dump())
    response.set_cookie(
        _USER_COOKIE, slug, max_age=_USER_COOKIE_MAX_AGE, httponly=True, samesite="lax"
    )
    return response


@app.post("/logout")
def logout():
    users.set_current_user(None)
    response = Response(status_code=204)
    response.delete_cookie(_USER_COOKIE)
    return response

def _sse_format(event: dict) -> str:
    # SSE wire format: "data: <payload>\n\n" — one blank line ends the event.
    # loop()'s events are already small JSON-able dicts, so no envelope needed.
    return f"data: {json.dumps(event)}\n\n"

def _stream_turn(message: str) -> StreamingResponse:
    session_id = uuid.uuid4().hex[:8]
    session_id_store.set(session_id)

    def event_stream():
        for event in loop(message):
            yield _sse_format(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/chat")
def chat(req: ChatRequest):
    _require_current_user()
    return _stream_turn(req.message)

@app.post("/action")
def action(req: ActionRequest):
    _require_current_user()
    # Deterministic evidence capture (spec 0001, decision 10): every UI
    # action lands in the raw evidence log BEFORE any model call — quiz
    # results and explain-backs are never lost, regardless of what Yani
    # then does with them.
    workspace.append_evidence(
        {
            "surface_id": req.surfaceId, "action": req.name, "context": req.context,
            "concept": workspace.active_concept(),
        }
    )
    # The action return leg: a Button click re-enters the agent loop as a
    # user turn. The server owns how a click reads in the transcript —
    # the browser sends structure, never prose.
    message = (
        f"[UI action] The user clicked {req.name!r} on surface {req.surfaceId!r}. "
        f"Context: {json.dumps(req.context)}\n"
        "Respond to this interaction the way you would to a spoken message — in natural "
        "language (or with an updated UI if that serves better), never as raw JSON."
    )
    return _stream_turn(message)

@app.get("/history")
def get_history():
    """Rebuild the whole scroll — text AND surfaces, in conversation order
    (spec 0001, decision 7: lessons survive reloads). state.json stays a pure
    LLM transcript; each function_call entry tells us WHERE a surface (or a
    whole lesson) appeared, and the durable surface store says WHAT it is.

    A request-local State() (not a shared one) plus users.learner_lock():
    this used to load() into a module-level State shared by every request,
    which is a real cross-learner data leak under FastAPI's threadpool for
    sync handlers — a concurrent request for a different learner could
    overwrite self.messages mid-iteration. The lock also keeps this from
    reading state.json/surfaces.json mid-write while this learner's own
    turn (harness.py's loop(), same lock) is still saving."""
    _require_current_user()
    with users.learner_lock():
        local_state = State()
        local_state.load()
        items: list[dict] = []
        for m in local_state.messages:
            role = m.get("role")
            if role in ("user", "assistant") and m.get("content"):
                items.append({"kind": "text", "role": role, "content": m["content"]})
            elif m.get("type") == "function_call" and m.get("name") == "create_surface":
                try:
                    surface_id = json.loads(m["arguments"]).get("surface_id")
                except (json.JSONDecodeError, TypeError):
                    continue
                events = surface_store.replay_events(surface_id)
                if events:
                    items.append({"kind": "ui", "events": events})
            elif m.get("type") == "function_call_output":
                # a teach_lesson ack carries the lesson's surface ids in order.
                # Tool outputs persist as str(dict) — ast.literal_eval, not json.
                try:
                    output = ast.literal_eval(m.get("output", ""))
                except (ValueError, SyntaxError):
                    continue
                if not isinstance(output, dict):
                    continue
                if output.get("surface_ids"):
                    # spec 0002 acks (plan_lesson / start_lesson / next_block):
                    # each carries the surfaces it streamed, in order
                    events = []
                    for sid in output["surface_ids"]:
                        events.extend(surface_store.replay_events(sid))
                    if events:
                        items.append({"kind": "ui", "events": events})
                elif "lesson_id" in output and "blocks" in output:
                    # legacy teach_lesson acks (pre-0002 transcripts)
                    events = surface_store.replay_events(f"{output['lesson_id']}-header")
                    for block in output.get("blocks", []):
                        events.extend(surface_store.replay_events(block.get("surface_id", "")))
                    if events:
                        items.append({"kind": "ui", "events": events})
    return HistoryEndpointResponse(items=items)

# Mounted last and at "/" with html=True: index.html is served at "/",
# style.css and app.js resolve at their own root paths, and the API
# routes above still win for /chat and /history since they were
# registered first.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


def main():
    """Dev entrypoint — one process, reload=True."""
    import uvicorn

    # reload=True: re-import the app whenever package files change. Three
    # separate stale-runtime incidents (2026-07-10/11) came from a live
    # process outrunning the code on disk — dev servers should follow the
    # disk. Costs: in-memory surfaces reset on reload (state.json survives).
    uvicorn.run(
        "yani.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).parent)],
    )


def serve():
    """Production entrypoint — multiple worker processes, no reload.
    uvicorn.run() doesn't accept both `workers` and `reload=True`: workers
    are separate OS processes that each re-import the app fresh, which is
    incompatible with reload watching the same files live. Safe to use
    workers>1 here specifically because users.learner_lock() (docs/adr/
    0002-per-learner-file-locking.md) makes every learner's file writes
    safe across processes, not just across threads in one process — that
    lock didn't exist before this ADR, and workers must not be enabled
    without it.

    Defaults to 127.0.0.1, same as the dev server: this app has no
    authentication (docs/adr/0001), so binding 0.0.0.0 puts every learner's
    data on the network to anyone who can reach the port. Set YANI_HOST
    explicitly if you actually intend to expose it beyond localhost."""
    import os
    import uvicorn

    uvicorn.run(
        "yani.server:app",
        host=os.environ.get("YANI_HOST", "127.0.0.1"),
        port=int(os.environ.get("YANI_PORT", "8000")),
        workers=int(os.environ.get("YANI_WORKERS", "4")),
        reload=False,
    )