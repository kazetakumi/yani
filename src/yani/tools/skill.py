from .. import skill_registry


def load_skill(skill_name: str):
    """Load a skill's full instructions. The system prompt's Skills menu lists each skill's name and description; call this with the name before doing that skill's job, then follow the returned workflow exactly."""
    return {
        "skill": skill_name,
        "instructions": skill_registry.skill_body(skill_name),
    }
