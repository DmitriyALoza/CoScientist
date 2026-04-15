"""Filesystem store for Target Analysis runs."""

from __future__ import annotations

from pathlib import Path

from eln.models.target_analysis import TargetAnalysisRun


class TargetAnalysisStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.mkdir(parents=True, exist_ok=True)

    def save(self, run: TargetAnalysisRun) -> None:
        dest = self._path / f"{run.analysis_id}.json"
        dest.write_text(run.model_dump_json(indent=2))

    def load(self, analysis_id: str) -> TargetAnalysisRun | None:
        for p in self._path.glob("*.json"):
            if p.stem.startswith(analysis_id):
                try:
                    return TargetAnalysisRun.model_validate_json(p.read_text())
                except Exception:
                    continue
        return None

    def list(self, limit: int = 20) -> list[TargetAnalysisRun]:
        runs: list[TargetAnalysisRun] = []
        paths = sorted(self._path.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for p in paths[:limit]:
            try:
                runs.append(TargetAnalysisRun.model_validate_json(p.read_text()))
            except Exception:
                continue
        return runs
