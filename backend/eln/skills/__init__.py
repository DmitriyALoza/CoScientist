from pathlib import Path

_SKILLS_DIR = Path(__file__).parent

# Cache loaded skills in memory (loaded once at graph build time)
_cache: dict[str, str] = {}


def load_skill(name: str) -> str:
    """
    Load a SKILL.md file by subagent name.

    Cached after first load so there's no file I/O on the hot path.
    """
    if name not in _cache:
        skill_path = _SKILLS_DIR / name / "SKILL.md"
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_path}")
        _cache[name] = skill_path.read_text(encoding="utf-8")
    return _cache[name]
