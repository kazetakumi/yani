"""Multi-user workspaces (wayfinder map: multi-user-workspaces, ticket 01):
which learner's learner home the current HTTP request is reading/writing.

.yani/
    workspace/               the users root: one learner home per subfolder
        <user-slug>/         the learner home (this map's new partition)
            about.md          personal facts about the human as a person —
                               distinct from concepts/<slug>/about.md
            state.json        this learner's chat transcript (state.py)
            surfaces.json     this learner's UI surface store (surface_store.py)
            workspace/        CONTEXT.md's existing "Workspace" term, unchanged:
                               MISSION.md, index.md, concepts/, learning-records/,
                               evidence-log.jsonl, NOTES.md

Identity is resolved per request, not once per server process (decided
2026-07-12 — see docs/adr/0001-per-request-cookie-identity.md): the current
user lives in a contextvar, populated at the top of every request from the
learner's identity cookie (server.py's middleware), not in a file shared by
the whole process. Starlette gives each request its own asyncio Task, and a
contextvar set inside one Task is invisible to sibling Tasks, so concurrent
requests from different learners never see each other's identity. Every
other module (workspace.py, state.py, surface_store.py) resolves its paths
through learner_home() below rather than hardcoding a workspace root, so
setting the current user for a request redirects all of them at once.
"""

import contextlib
import contextvars
import re
from pathlib import Path

from filelock import FileLock

WORKSPACE_ROOT = Path(".yani") / "workspace"
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

_current_user_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_user", default=None
)


def is_valid_slug(value: str) -> bool:
    """True iff `value` could only ever have come from slugify() — no '..',
    no '/', nothing that could escape WORKSPACE_ROOT when joined into a
    Path. The identity cookie is client-supplied and unvalidated by the
    browser, so callers that set the current user from a cookie (server.py's
    middleware) must check this before trusting it; /login's own slugs
    always pass since slugify()'s output is exactly this pattern."""
    return bool(_SLUG_RE.fullmatch(value))


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"can't derive a slug from {name!r}")
    return slug


def list_users() -> list[str]:
    if not WORKSPACE_ROOT.exists():
        return []
    return sorted(p.name for p in WORKSPACE_ROOT.iterdir() if p.is_dir())


def resolve_user_slug(name: str) -> str:
    """Slugify `name` and fuzzy-match it against existing learner homes (same
    dash-stripped convention as workspace.py's concept resolver) so a
    re-typed name reliably lands on the same learner home even if punctuation
    slugifies slightly differently. Returns the fresh slug, unmatched, if
    this is a brand-new name — the caller decides whether that means
    "create a new learner home"."""
    candidate = slugify(name)
    existing = list_users()
    if candidate in existing:
        return candidate
    norm = candidate.replace("-", "")
    for slug in existing:
        slug_norm = slug.replace("-", "")
        if norm == slug_norm or norm in slug_norm or slug_norm in norm:
            return slug
    return candidate


def current_user() -> str | None:
    return _current_user_var.get()


def set_current_user(slug: str | None):
    _current_user_var.set(slug)


def learner_home() -> Path:
    """The current user's learner home directory. Raises if no user is set
    yet: every caller sits behind the login gate (map tickets 02/03), so a
    missing current user here is a bug in the caller, not a state to
    tolerate — there is deliberately no "default workspace" fallback."""
    slug = current_user()
    if slug is None:
        raise RuntimeError("no current user set — call set_current_user first")
    return WORKSPACE_ROOT / slug


def ensure_learner_home(slug: str) -> Path:
    """Scaffold a brand-new learner home's directories (idempotent). Does not
    touch about.md content — that's ticket 02 (starter file) and ticket 04
    (the model-facing update tool)."""
    home = WORKSPACE_ROOT / slug
    (home / "workspace").mkdir(parents=True, exist_ok=True)
    return home


@contextlib.contextmanager
def learner_lock():
    """Exclusive lock scoped to the current learner, held for one whole turn
    (harness.py's loop()) or one /history read (docs/adr/0002-per-learner-
    file-locking.md). state.py, surface_store.py, lesson_store.py, and
    workspace.py all do unlocked read-modify-write against this learner's
    files — safe only because, until now, exactly one request touched one
    learner's files at a time. Concurrent multi-user identity (ADR 0001)
    plus multi-process workers both break that assumption: two tabs of the
    same learner, or two worker processes handling that learner's requests,
    have no shared memory to coordinate through, only these files. A plain
    OS advisory lock (flock) is enough — it's released automatically even
    if the holding process dies, and different learners never contend since
    each lock file lives inside that learner's own home directory."""
    home = learner_home()
    home.mkdir(parents=True, exist_ok=True)
    with FileLock(home / ".lock"):
        yield
