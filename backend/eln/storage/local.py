import shutil
from pathlib import Path

from eln.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Stores objects on the local filesystem under kb_root.

    Key convention: kb/<user_id>/<collection>/<sha256>.<ext>
    The kb_root already points to workspaces/<user>/kb/, so we strip
    the leading 'kb/<user_id>/' prefix.
    """

    def __init__(self, kb_root: Path) -> None:
        self.kb_root = kb_root

    def _dest(self, key: str) -> Path:
        # key = "kb/<user_id>/<collection>/<filename>"
        # Strip first two segments (kb/<user_id>) since kb_root already contains them
        parts = key.split("/")
        relative = "/".join(parts[2:]) if len(parts) > 2 else key
        return self.kb_root / relative

    def put_object(self, key: str, source_path: Path) -> str:
        dest = self._dest(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, dest)
        return key

    def get_object(self, key: str, dest_path: Path) -> None:
        src = self._dest(key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest_path)

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        return self._dest(key).resolve().as_uri()

    def exists(self, key: str) -> bool:
        return self._dest(key).exists()

    def delete(self, key: str) -> None:
        dest = self._dest(key)
        if dest.exists():
            dest.unlink()
