from datetime import datetime
from pathlib import Path

from eln.config import settings
from eln.models.workspace import RunIndex, WorkspaceSettings


class WorkspaceManager:
    """Manages the filesystem-based workspace for a single user."""

    def __init__(self, user_id: str | None = None, root: Path | None = None):
        self.user_id = user_id or settings.default_user
        self.root = (root or settings.workspaces_root) / self.user_id
        self._settings_path = self.root / "settings.json"
        self._ensure_root()

    # ------------------------------------------------------------------
    # Workspace lifecycle
    # ------------------------------------------------------------------

    def _ensure_root(self) -> None:
        dirs = [
            self.root,
            self.root / "kb" / "papers",
            self.root / "kb" / "sops_internal",
            self.root / "kb" / "sops_manufacturer",
            self.root / "kb" / "reports",
            self.root / "kb" / "eln_entries",
            self.root / "kb" / "reference_docs",
            self.root / "indexes",
            self.root / "audit",
            self.root / "memory",
            self.root / "hypotheses",
            self.root / "debates",
            self.root / "experiments",
            self.root / "experiments" / "loops",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        for doc_type in ("eln", "sop", "report", "patent"):
            (self.root / "templates" / doc_type).mkdir(parents=True, exist_ok=True)

        if not self._settings_path.exists():
            ws = WorkspaceSettings(workspace_id=self.user_id, owner=self.user_id)
            self._save_settings(ws)

    def load_settings(self) -> WorkspaceSettings:
        with open(self._settings_path) as f:
            return WorkspaceSettings.model_validate_json(f.read())

    def _save_settings(self, ws: WorkspaceSettings) -> None:
        with open(self._settings_path, "w") as f:
            f.write(ws.model_dump_json(indent=2))

    # ------------------------------------------------------------------
    # Run management
    # ------------------------------------------------------------------

    def create_run(self, run_id: str, title: str, domain: str) -> Path:
        """Scaffold the run folder structure and register the run."""
        run_path = self.root / "runs" / run_id
        for sub in ["artifacts", "protocols", "analysis", "reports"]:
            (run_path / sub).mkdir(parents=True, exist_ok=True)

        ws = self.load_settings()
        entry = RunIndex(
            run_id=run_id,
            title=title,
            domain=domain,
            owner=self.user_id,
            timestamp=datetime.utcnow(),
            path=str(run_path.resolve()),
        )
        ws.runs.append(entry)
        self._save_settings(ws)

        return run_path

    def get_run_path(self, run_id: str) -> Path:
        return self.root / "runs" / run_id

    def list_runs(self) -> list[RunIndex]:
        return self.load_settings().runs

    def set_last_run(self, run_id: str) -> None:
        ws = self.load_settings()
        ws.last_run_id = run_id
        self._save_settings(ws)

    def audit_path(self) -> Path:
        return self.root / "audit"

    def kb_path(self, kb_type: str) -> Path:
        """kb_type: 'sops_internal' | 'sops_manufacturer' | 'papers'"""
        return self.root / "kb" / kb_type

    def indexes_path(self) -> Path:
        return self.root / "indexes"

    def templates_path(self) -> Path:
        return self.root / "templates"

    def memory_path(self) -> Path:
        return self.root / "memory"

    def hypotheses_path(self) -> Path:
        return self.root / "hypotheses"

    def debates_path(self) -> Path:
        return self.root / "debates"

    def experiments_path(self) -> Path:
        return self.root / "experiments"
