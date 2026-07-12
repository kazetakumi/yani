"""Reader for agents/<name>/AGENT.md — the subagent system prompts.

Same folder+frontmatter template as skills, different audience: these are
never on the model's menu; tools are their only consumers."""

from pathlib import Path

AGENTS_DIR = Path(__file__).parent / "agents"


def agent_prompt(name: str) -> str:
    text = (AGENTS_DIR / name / "AGENT.md").read_text()
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text.strip()
