"""Progressive skill loading — the Claude Code SkillTool pattern, minimal.

A skill is skills/<name>/SKILL.md with YAML frontmatter:
    name, description, auto_enable (optional, default false)

Two disclosure modes, chosen per skill by the flag:
  auto_enable: true  — the full body is injected into every system prompt.
                       For small, load-bearing skills the model must never
                       miss. Costs its size in tokens on every single call.
  auto_enable: false — only name + description ride in the prompt (the menu);
                       the model fetches the body with load_skill. The body
                       arrives as a tool result and persists in state.json,
                       so one load serves the whole conversation.

Subagent prompts (agents/<name>/AGENT.md) share the same folder+frontmatter
template but are deliberately NOT skills: they are system prompts addressed
to a different model call (tools/ui.py's one-shot generators). No auto_enable
value would be safe for them — true would inject another agent's contract
into the main prompt, false would put it on the main model's menu — so they
live outside skills/ and never reach this registry.
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"

# Skill bodies served this process. tools/ui.py gates the UI tools on this so
# a small model can't compose blind having skipped the load. Process-scoped
# like ui.py's _surfaces: a server reload forgets it; the transcript doesn't.
_loaded: set = set()


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split '--- key: value ---' frontmatter from the body. Minimal on
    purpose: our frontmatter is flat single-line strings, no YAML library."""
    if not text.startswith("---"):
        return {}, text.strip()
    end = text.find("---", 3)
    if end == -1:
        return {}, text.strip()
    meta = {}
    for line in text[3:end].strip().splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, text[end + 3:].strip()


def _entry(path: Path) -> dict:
    meta, body = _parse_frontmatter(path.read_text())
    return {
        "name": meta.get("name", path.parent.name),
        "description": meta.get("description", ""),
        "auto_enable": meta.get("auto_enable", "").lower() == "true",
        "body": body,
    }


def list_skills() -> list[dict]:
    """[{name, description, auto_enable}, ...] for every skills/*/SKILL.md."""
    return [_entry(path) for path in sorted(SKILLS_DIR.glob("*/SKILL.md"))]


def skill_body(name: str) -> str:
    """Full instructions for one skill; records it as loaded this process."""
    path = SKILLS_DIR / name / "SKILL.md"
    if not path.is_file():
        available = [entry["name"] for entry in list_skills()]
        raise ValueError(f"no such skill '{name}' — available skills: {available}")
    _loaded.add(name)
    return _entry(path)["body"]


def is_loaded(name: str) -> bool:
    """True if the model has this skill's body — fetched via load_skill, or
    standing in every prompt because the skill is auto-enabled."""
    if name in _loaded:
        return True
    path = SKILLS_DIR / name / "SKILL.md"
    return path.is_file() and _entry(path)["auto_enable"]
