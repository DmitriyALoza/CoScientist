"""Episodic memory store — JSON-backed, with keyword search."""
import json
from pathlib import Path

from eln.models.memory import MemoryEntry


class EpisodicStore:
    """JSON-backed episodic memory store with simple keyword recall."""

    def __init__(self, storage_path: Path):
        self._path = storage_path / "episodes.json"
        self._episodes: list[MemoryEntry] = []
        if self._path.exists():
            self._load()

    def _load(self) -> None:
        with open(self._path) as f:
            data = json.load(f)
        self._episodes = [MemoryEntry.model_validate(e) for e in data]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(
                [e.model_dump(mode="json") for e in self._episodes],
                f,
                indent=2,
            )

    def store(self, entry: MemoryEntry) -> None:
        self._episodes.append(entry)
        self._save()

    def get_all(self) -> list[MemoryEntry]:
        return list(self._episodes)

    def search(self, query: str, k: int = 5) -> list[MemoryEntry]:
        """Keyword search — scores by word overlap, returns top-k."""
        query_words = set(query.lower().split())
        scored = []
        for e in self._episodes:
            content_words = set(e.content.lower().split())
            score = len(query_words & content_words)
            if score > 0:
                scored.append((score, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:k]]

    def get_recent(self, n: int = 10) -> list[MemoryEntry]:
        return sorted(self._episodes, key=lambda e: e.timestamp, reverse=True)[:n]
