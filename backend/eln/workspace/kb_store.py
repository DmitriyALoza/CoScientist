import hashlib
import shutil
from datetime import datetime
from pathlib import Path


class KBStore:
    """Manages ingestion of documents into the knowledge base folders."""

    def __init__(self, kb_root: Path):
        self.kb_root = kb_root

    def add_document(self, source_path: Path, kb_type: str) -> dict:
        """
        Copy a document into the KB folder.

        Returns metadata dict with path, sha256, and timestamp.
        kb_type: 'sops_internal' | 'sops_manufacturer' | 'papers'
        """
        dest_dir = self.kb_root / kb_type
        dest_dir.mkdir(parents=True, exist_ok=True)

        sha256 = self._sha256(source_path)
        dest = dest_dir / source_path.name

        shutil.copy2(source_path, dest)

        return {
            "path": str(dest),
            "sha256": sha256,
            "kb_type": kb_type,
            "added_at": datetime.utcnow().isoformat(),
            "original_name": source_path.name,
        }

    def list_documents(self, kb_type: str) -> list[Path]:
        target = self.kb_root / kb_type
        if not target.exists():
            return []
        return [p for p in target.iterdir() if p.is_file()]

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
