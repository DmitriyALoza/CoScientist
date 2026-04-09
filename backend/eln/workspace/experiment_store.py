"""Persistent store for experiments and experiment loops."""
from pathlib import Path

from eln.models.experiment import Experiment, ExperimentLoop


class ExperimentStore:
    """CRUD store for experiments and loops under experiments/ and experiments/loops/."""

    def __init__(self, experiments_path: Path):
        self._path = experiments_path
        self._loops_path = experiments_path / "loops"
        self._path.mkdir(parents=True, exist_ok=True)
        self._loops_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Experiments
    # ------------------------------------------------------------------

    def save_experiment(self, exp: Experiment) -> None:
        dest = self._path / f"{exp.experiment_id}.json"
        with open(dest, "w") as f:
            f.write(exp.model_dump_json(indent=2))

    def load_experiment(self, experiment_id: str) -> Experiment | None:
        for p in self._path.glob("*.json"):
            if p.stem.startswith(experiment_id):
                with open(p) as f:
                    return Experiment.model_validate_json(f.read())
        return None

    def list_experiments(self, hypothesis_id: str | None = None) -> list[Experiment]:
        exps = []
        for p in sorted(self._path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(p) as f:
                    exp = Experiment.model_validate_json(f.read())
                if hypothesis_id is None or exp.hypothesis_id == hypothesis_id:
                    exps.append(exp)
            except Exception:
                continue
        return exps

    # ------------------------------------------------------------------
    # Loops
    # ------------------------------------------------------------------

    def save_loop(self, loop: ExperimentLoop) -> None:
        dest = self._loops_path / f"{loop.loop_id}.json"
        with open(dest, "w") as f:
            f.write(loop.model_dump_json(indent=2))

    def load_loop(self, loop_id: str) -> ExperimentLoop | None:
        for p in self._loops_path.glob("*.json"):
            if p.stem.startswith(loop_id):
                with open(p) as f:
                    return ExperimentLoop.model_validate_json(f.read())
        return None

    def get_loop_for_hypothesis(self, hypothesis_id: str) -> ExperimentLoop | None:
        """Find the active loop for a hypothesis."""
        for p in self._loops_path.glob("*.json"):
            try:
                with open(p) as f:
                    loop = ExperimentLoop.model_validate_json(f.read())
                if loop.hypothesis_id == hypothesis_id:
                    return loop
            except Exception:
                continue
        return None

    def list_loops(self) -> list[ExperimentLoop]:
        loops = []
        for p in sorted(
            self._loops_path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True
        ):
            try:
                with open(p) as f:
                    loops.append(ExperimentLoop.model_validate_json(f.read()))
            except Exception:
                continue
        return loops
