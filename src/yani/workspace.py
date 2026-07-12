"""Yani's teaching workspace (spec 0001 + the parallel-concept-workspace map):
durable, human-readable memory.

.yani/workspace/<user-slug>/workspace/
    MISSION.md             durable, cross-concept learner profile + constraints
    index.md                concept roster + last-active pointer, regenerated on every write
    concepts/<slug>/
        about.md             name, one-line description, details — what this concept covers
        progress.md          milestone checklist toward this concept, same checkbox convention as before
    NOTES.md               teaching preferences and observations
    learning-records/      LR-NNNN-*.md — judged evidence, each with next-review
    evidence-log.jsonl     raw quiz/explain-back submissions, harness-appended

This is CONTEXT.md's "Workspace" term — one learner's teaching memory, nested
one level under their learner home (see users.py: WORKSPACE_ROOT is the users
root, learner_home() is the per-user partition). Which user's workspace this
module reads/writes is resolved fresh on every call via users.learner_home(),
never cached — so a login (multi-user-workspaces map, ticket 02) redirects
every function below without this module needing to know a login happened.

Concepts are independent and freely parallel — no dependency graph (initially).
The student can be mid-way through several at once; index.md's "last active"
pointer plus session_ritual() below is how the harness resumes the right one
without the model having to remember across turns.

Two kinds of writer, deliberately separate (grilling decision 10):
- the typed tool functions below — Yani's judgment, format enforced here;
- append_evidence() — deterministic capture the server calls on every UI
  action, before any model sees it. Nothing the learner does is ever lost.

session_ritual() is the deterministic, zero-model-call session decision
(grilling decision 9): the harness reads this directory and injects the
verdict into the system prompt; the model executes it, never chooses it.
"""

import json
import re
import time
from datetime import date, timedelta
from pathlib import Path

from . import users

RECORDS_DIRNAME = "learning-records"
CONCEPTS_DIRNAME = "concepts"
INDEX_FILENAME = "index.md"
FIRST_REVIEW_DAYS = 3


def _workspace_dir() -> Path:
    return users.learner_home() / "workspace"


def _dir() -> Path:
    d = _workspace_dir()
    (d / RECORDS_DIRNAME).mkdir(parents=True, exist_ok=True)
    return d


def _read(name: str) -> str | None:
    path = _workspace_dir() / name
    return path.read_text().strip() if path.exists() else None


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"can't derive a slug from {name!r}")
    return slug


def _concepts_dir() -> Path:
    d = _workspace_dir() / CONCEPTS_DIRNAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def _concept_dir(slug: str) -> Path:
    return _concepts_dir() / slug


# ── typed tools (Yani's judgment) ────────────────────────────────

def read_workspace():
    """Read the whole teaching workspace: mission, the concept index, and learning records with their review dates."""
    return {
        "mission": _read("MISSION.md") or "(no mission yet)",
        "concepts": list_concepts(),
        "active_concept": _read_last_active(),
        "notes": _read("NOTES.md") or "(no notes yet)",
        "learning_records": list_records(),
    }


def update_mission(profile: str, constraints: str):
    """Write the learner's durable, cross-concept profile after the intro interview. profile = who they are and why they're here in general (age/level, overall motivation); constraints = durable rules that apply to every concept (session length, no code, etc.). Concept-specific goals belong in each concept's about.md, not here."""
    content = (
        f"# Mission\n\n## Profile\n{profile}\n\n"
        f"## Constraints\n{constraints}\n\n*Updated {date.today().isoformat()}*\n"
    )
    (_dir() / "MISSION.md").write_text(content)
    return {"written": "MISSION.md"}


def _milestone_text(entry) -> str:
    # normalize model creativity: a dict entry means the schema vacuum got
    # filled with invented structure — take the milestone text, drop the rest
    if isinstance(entry, dict):
        for key in ("item", "milestone", "title", "text"):
            if key in entry:
                return str(entry[key])
    return str(entry)


def _parse_about(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    name = lines[0].lstrip("#").strip() if lines else ""
    description = ""
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            break
        description = stripped
        break
    return name, description


def _progress_counts(progress_text: str) -> tuple[int, int]:
    done = sum(1 for line in progress_text.splitlines() if line.strip().startswith("- [x]"))
    open_ = sum(1 for line in progress_text.splitlines() if line.strip().startswith("- [ ]"))
    return done, done + open_


def _resolve_concept_slug(concept: str) -> str:
    candidate = _slugify(concept)
    if (_concepts_dir() / candidate).exists():
        return candidate
    # fuzzy fallback: a model's guessed slug/phrase rarely matches the exact
    # slugification (apostrophes, punctuation) — compare with dashes/spaces
    # stripped so "newtons-laws-of-motion" still finds "newton-s-laws-of-motion"
    norm = candidate.replace("-", "")
    needle = concept.strip().lower()
    for c in list_concepts():
        slug_norm = c["slug"].replace("-", "")
        name_norm = c["name"].lower()
        if norm == slug_norm or norm in slug_norm or slug_norm in norm:
            return c["slug"]
        if needle in name_norm or name_norm in needle:
            return c["slug"]
    available = ", ".join(c["slug"] for c in list_concepts()) or "(none yet)"
    raise ValueError(f"no concept matches {concept!r} — available: {available}")


def create_concept(name: str, description: str, details: str, milestones: list[str]):
    """Start a new independent concept workspace — its own about.md and progress.md, no dependency on any other concept. name/description/details describe what it is; milestones (4-7 plain-text items) become its progress checklist. Becomes the active concept."""
    if not name.strip():
        raise ValueError("concept needs a name")
    if not milestones:
        raise ValueError("concept needs at least one progress milestone")
    slug = _slugify(name)
    concept_dir = _concept_dir(slug)
    if concept_dir.exists():
        raise ValueError(f"concept {slug!r} already exists — use update_concept_about or tick_concept_progress instead")
    concept_dir.mkdir(parents=True)
    about = f"# {name.strip()}\n\n{description.strip()}\n\n## Details\n\n{details.strip()}\n"
    (concept_dir / "about.md").write_text(about)
    lines = "\n".join(f"- [ ] {_milestone_text(m).strip()}" for m in milestones)
    (concept_dir / "progress.md").write_text(f"# Progress\n\n{lines}\n")
    _write_index(slug)
    return {"created": slug, "milestones": len(milestones)}


def update_concept_about(concept: str, description: str, details: str):
    """Update an existing concept's about.md description and details (its name stays fixed)."""
    slug = _resolve_concept_slug(concept)
    path = _concept_dir(slug) / "about.md"
    name = _parse_about(path.read_text())[0]
    path.write_text(f"# {name}\n\n{description.strip()}\n\n## Details\n\n{details.strip()}\n")
    _write_index(_read_last_active())
    return {"updated": slug}


def tick_concept_progress(concept: str, item: str, status: str, note: str):
    """Mark a milestone in one concept's progress.md. status must be 'taught' (covered, no evidence yet) or 'demonstrated' (real evidence exists). note says what happened. Sets that concept as active."""
    if status not in ("taught", "demonstrated"):
        raise ValueError("status must be 'taught' or 'demonstrated'")
    slug = _resolve_concept_slug(concept)
    path = _concept_dir(slug) / "progress.md"
    lines = path.read_text().splitlines()
    needle = item.strip().lower()
    for i, line in enumerate(lines):
        if needle in line.lower() and line.lstrip().startswith("- ["):
            text = re.sub(r"^(\s*)- \[.\]", r"\1- [x]", line)
            text = re.sub(r"\s*—\s*(taught|demonstrated).*$", "", text)
            lines[i] = f"{text} — {status} {date.today().isoformat()}: {note}"
            path.write_text("\n".join(lines) + "\n")
            _write_index(slug)
            return {"ticked": lines[i].strip(), "concept": slug, "status": status}
    raise ValueError(f"no progress item in {slug!r} matches {item!r} — read_concept to see the list")


def set_active_concept(concept: str):
    """Switch which concept is active/being resumed — use when the learner explicitly asks to work on a different concept than last time."""
    slug = _resolve_concept_slug(concept)
    _write_index(slug)
    return {"active_concept": slug}


def read_concept(concept: str):
    """Read one concept's full about.md and progress.md — use to zoom in before switching to it or reviewing its state."""
    slug = _resolve_concept_slug(concept)
    d = _concept_dir(slug)
    return {
        "slug": slug,
        "about": (d / "about.md").read_text().strip(),
        "progress": (d / "progress.md").read_text().strip(),
    }


def list_concepts() -> list[dict]:
    concepts = []
    concepts_dir = _workspace_dir() / CONCEPTS_DIRNAME
    if not concepts_dir.exists():
        return concepts
    for d in sorted(p for p in concepts_dir.iterdir() if p.is_dir()):
        about_path = d / "about.md"
        if not about_path.exists():
            continue
        name, description = _parse_about(about_path.read_text())
        progress_path = d / "progress.md"
        done, total = _progress_counts(progress_path.read_text()) if progress_path.exists() else (0, 0)
        concepts.append({
            "slug": d.name, "name": name or d.name, "description": description,
            "done": done, "total": total,
        })
    return concepts


def active_concept() -> str | None:
    """The slug of the currently active concept, or None if no concepts exist yet."""
    return _read_last_active()


def _read_last_active() -> str | None:
    text = _read(INDEX_FILENAME)
    if not text:
        return None
    m = re.search(r"Last active:.*\(concepts/([^/]+)/about\.md\)", text)
    return m.group(1) if m else None


def _write_index(active_slug: str | None):
    concepts = list_concepts()
    active = next((c for c in concepts if c["slug"] == active_slug), None) if active_slug else None
    lines = ["# Workspace Index", ""]
    if active:
        lines.append(f"- Last active: [{active['name']}](concepts/{active['slug']}/about.md) — {date.today().isoformat()}")
    else:
        lines.append("- Last active: (none)")
    lines += ["", "## Concepts", ""]
    if concepts:
        for c in concepts:
            lines.append(f"- [{c['name']}](concepts/{c['slug']}/about.md) — {c['description']} — {c['done']}/{c['total']} covered")
    else:
        lines.append("(no concepts yet)")
    (_dir() / INDEX_FILENAME).write_text("\n".join(lines) + "\n")


def write_learning_record(title: str, concept: str, evidence: str):
    """Record demonstrated understanding — only when real evidence exists (a correct quiz answer, a solid explain-back, a retrieval answer in chat). Never for merely covered material."""
    records = list_records()
    number = max((r["number"] for r in records), default=0) + 1
    next_review = (date.today() + timedelta(days=FIRST_REVIEW_DAYS)).isoformat()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "record"
    content = (
        f"# LR-{number:04d} — {title}\n\n"
        f"date: {date.today().isoformat()}\n"
        f"next-review: {next_review}\n\n"
        f"## Concept\n{concept}\n\n## Evidence\n{evidence}\n"
    )
    path = _dir() / RECORDS_DIRNAME / f"{number:04d}-{slug}.md"
    path.write_text(content)
    return {"written": path.name, "next_review": next_review}


def add_note(note: str):
    """Append a durable teaching observation or learner preference to NOTES.md."""
    d = _dir()
    path = d / "NOTES.md"
    existing = path.read_text() if path.exists() else "# Teaching Notes\n"
    path.write_text(existing.rstrip() + f"\n- {date.today().isoformat()}: {note.strip()}\n")
    return {"written": "NOTES.md"}


def _about_path() -> Path:
    # about.md lives at the learner-home level (a sibling of state.json,
    # surfaces.json), one level above this module's _workspace_dir() —
    # it's about the person, not the teaching (multi-user-workspaces map).
    return users.learner_home() / "about.md"


def update_about(fact: str):
    """Append a personal fact you've learned about the learner as a person — interests, communication style, life context. Not teaching strategy (see add_note/NOTES.md) and not the durable teaching profile (see update_mission/MISSION.md). Call whenever conversation reveals something personal worth remembering long-term."""
    path = _about_path()
    existing = path.read_text() if path.exists() else "# About\n"
    path.write_text(existing.rstrip() + f"\n- {date.today().isoformat()}: {fact.strip()}\n")
    return {"written": "about.md"}


def _read_about() -> str | None:
    path = _about_path()
    return path.read_text().strip() if path.exists() else None


# ── record parsing ───────────────────────────────────────────────

def list_records() -> list[dict]:
    records = []
    records_dir = _workspace_dir() / RECORDS_DIRNAME
    if not records_dir.exists():
        return records
    for path in sorted(records_dir.glob("*.md")):
        text = path.read_text()
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        m = re.search(r"^next-review:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
        num = re.match(r"(\d+)", path.stem)
        records.append({
            "file": path.name,
            "number": int(num.group(1)) if num else 0,
            "title": title,
            "next_review": m.group(1) if m else None,
        })
    return records


# ── the deterministic session ritual (zero model calls) ──────────

def session_ritual() -> dict:
    mission = _read("MISSION.md")
    if not mission:
        return {"mode": "interview"}
    today = date.today().isoformat()
    due = [r for r in list_records() if r["next_review"] and r["next_review"] <= today]
    if due:
        return {"mode": "review", "due": [r["title"] for r in due[:3]]}
    concepts = list_concepts()
    if not concepts:
        return {"mode": "new_concept"}
    active_slug = _read_last_active() or concepts[0]["slug"]
    active = next((c for c in concepts if c["slug"] == active_slug), concepts[0])
    progress_path = _concept_dir(active["slug"]) / "progress.md"
    progress_text = progress_path.read_text() if progress_path.exists() else ""
    for line in progress_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            return {
                "mode": "teach", "concept": active["name"],
                "concept_slug": active["slug"], "next_item": stripped[5:].strip(),
            }
    return {"mode": "free"}


def ritual_prompt_block() -> str:
    """The workspace summary + verdict injected into every system prompt —
    the memory index pattern: small enough to always ride along. Only the
    active concept's files are injected in full; other concepts show up
    as one roster line each in the index (ticket 05: bounded context growth
    as concepts accumulate)."""
    verdict = session_ritual()
    lines = ["# Session state", ""]
    if verdict["mode"] == "interview":
        lines.append(
            "No learner profile exists yet. THIS SESSION'S JOB: interview the learner — "
            "who they are (age/level), why they're here generally, and durable constraints "
            "(session length, no code, etc.) — then call update_mission. Then interview them "
            "about the first specific thing they want to learn and call create_concept."
        )
        return "\n".join(lines)
    if verdict["mode"] == "new_concept":
        lines.append(
            "Learner profile is set but no concepts exist yet. THIS SESSION'S JOB: interview "
            "the learner about the first specific thing they want to learn — the concrete "
            "real-world outcome, why they care, what success looks like — then call "
            "create_concept with 4-7 milestones, then teach the first lesson."
        )
    elif verdict["mode"] == "review":
        due = "; ".join(verdict["due"])
        lines.append(
            f"Reviews are due: {due}. Before teaching anything new, warm up with 2-3 "
            "retrieval questions in chat covering these, judged honestly."
        )
    elif verdict["mode"] == "teach":
        lines.append(
            f"Resuming concept '{verdict['concept']}'. Next milestone: {verdict['next_item']}. "
            "Teach it with the lesson ritual (plan_lesson first) unless the learner asks for "
            "something else, or to switch concepts (set_active_concept) or start a new one "
            "(create_concept)."
        )
    else:
        lines.append(
            "Profile set, no reviews due, active concept has no next milestone — follow the "
            "learner's lead. They may start a new concept (create_concept) or switch to an "
            "existing one (set_active_concept)."
        )
    mission = _read("MISSION.md")
    if mission:
        lines += ["", "## Mission", mission]
    about = _read_about()
    if about:
        # Personal facts about the human as a person — distinct from Mission
        # (durable teaching profile/constraints) and Teaching notes (below,
        # teaching-strategy observations). update_about is the only writer.
        lines += ["", "## About the learner", about]
    index = _read(INDEX_FILENAME)
    if index:
        lines += ["", "## Concepts", index]
    active_slug = _read_last_active()
    if active_slug:
        about_path = _concept_dir(active_slug) / "about.md"
        progress_path = _concept_dir(active_slug) / "progress.md"
        if about_path.exists():
            lines += ["", "## Active concept: about", about_path.read_text().strip()]
        if progress_path.exists():
            lines += ["", "## Active concept: progress", progress_path.read_text().strip()]
    notes = _read("NOTES.md")
    if notes:
        lines += ["", "## Teaching notes", notes]
    return "\n".join(lines)


# ── deterministic evidence capture (the harness's half) ──────────

def append_evidence(entry: dict):
    """Called by the server on every UI action, before any model call.
    Raw, judgment-free, never lost."""
    d = _dir()
    record = {"ts": time.time(), "date": date.today().isoformat(), **entry}
    with open(d / "evidence-log.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")
