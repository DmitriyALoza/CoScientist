"""Persistent store for hypothesis sets."""
import json
from pathlib import Path

from eln.models.hypothesis import HypothesisSet


class HypothesisStore:
    """CRUD store for HypothesisSet files in hypotheses/<set_id>.json."""

    def __init__(self, hypotheses_path: Path):
        self._path = hypotheses_path
        self._path.mkdir(parents=True, exist_ok=True)

    def save(self, h_set: HypothesisSet) -> None:
        dest = self._path / f"{h_set.set_id}.json"
        with open(dest, "w") as f:
            f.write(h_set.model_dump_json(indent=2))

    def load(self, set_id: str) -> HypothesisSet | None:
        # Allow prefix match
        for p in self._path.glob("*.json"):
            if p.stem.startswith(set_id):
                with open(p) as f:
                    return HypothesisSet.model_validate_json(f.read())
        return None

    def list(self, limit: int = 20) -> list[HypothesisSet]:
        sets = []
        paths = sorted(self._path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in paths[:limit]:
            try:
                with open(p) as f:
                    sets.append(HypothesisSet.model_validate_json(f.read()))
            except Exception:
                continue
        return sets

    def delete(self, set_id: str) -> bool:
        for p in self._path.glob("*.json"):
            if p.stem.startswith(set_id):
                p.unlink()
                return True
        return False
