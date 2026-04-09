"""Persistent store for debates."""
from pathlib import Path

from eln.models.debate import Debate


class DebateStore:
    """CRUD store for Debate files in debates/<debate_id>.json."""

    def __init__(self, debates_path: Path):
        self._path = debates_path
        self._path.mkdir(parents=True, exist_ok=True)

    def save(self, debate: Debate) -> None:
        dest = self._path / f"{debate.debate_id}.json"
        with open(dest, "w") as f:
            f.write(debate.model_dump_json(indent=2))

    def load(self, debate_id: str) -> Debate | None:
        for p in self._path.glob("*.json"):
            if p.stem.startswith(debate_id):
                with open(p) as f:
                    return Debate.model_validate_json(f.read())
        return None

    def list(self, limit: int = 20) -> list[Debate]:
        debates = []
        paths = sorted(self._path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in paths[:limit]:
            try:
                with open(p) as f:
                    debates.append(Debate.model_validate_json(f.read()))
            except Exception:
                continue
        return debates

    def delete(self, debate_id: str) -> bool:
        for p in self._path.glob("*.json"):
            if p.stem.startswith(debate_id):
                p.unlink()
                return True
        return False
