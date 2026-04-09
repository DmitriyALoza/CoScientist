from pathlib import Path

from eln.models.artifact import ArtifactManifest
from eln.models.run_manifest import RunManifest


class RunStore:
    """Read/write run_manifest.json and artifact_manifest.json for a single run."""

    def __init__(self, run_path: Path):
        self.run_path = run_path
        self._manifest_path = run_path / "run_manifest.json"
        self._artifact_manifest_path = run_path / "artifact_manifest.json"

    # ------------------------------------------------------------------
    # RunManifest
    # ------------------------------------------------------------------

    def save_run_manifest(self, manifest: RunManifest) -> None:
        with open(self._manifest_path, "w") as f:
            f.write(manifest.model_dump_json(indent=2))

    def load_run_manifest(self) -> RunManifest:
        with open(self._manifest_path) as f:
            return RunManifest.model_validate_json(f.read())

    def run_manifest_exists(self) -> bool:
        return self._manifest_path.exists()

    # ------------------------------------------------------------------
    # ArtifactManifest
    # ------------------------------------------------------------------

    def save_artifact_manifest(self, manifest: ArtifactManifest) -> None:
        with open(self._artifact_manifest_path, "w") as f:
            f.write(manifest.model_dump_json(indent=2))

    def load_artifact_manifest(self) -> ArtifactManifest:
        if not self._artifact_manifest_path.exists():
            # Return empty manifest rather than raising
            run = self.load_run_manifest()
            return ArtifactManifest(run_id=run.run_id)
        with open(self._artifact_manifest_path) as f:
            return ArtifactManifest.model_validate_json(f.read())

    def artifact_manifest_exists(self) -> bool:
        return self._artifact_manifest_path.exists()
