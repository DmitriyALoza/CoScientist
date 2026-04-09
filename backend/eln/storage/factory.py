from pathlib import Path

from eln.storage.base import StorageBackend

_backend: StorageBackend | None = None


def get_storage_backend(user_id: str | None = None) -> StorageBackend:
    """Return the module-level singleton StorageBackend.

    First call builds the backend from settings. Subsequent calls return
    the cached instance (regardless of user_id — the key encodes user_id).
    """
    global _backend
    if _backend is None:
        from eln.config import settings

        if settings.storage_backend == "s3":
            from eln.storage.s3 import S3StorageBackend

            _backend = S3StorageBackend(
                bucket=settings.s3_bucket,
                endpoint_url=settings.s3_endpoint_url,
                access_key_id=settings.s3_access_key_id,
                secret_access_key=settings.s3_secret_access_key,
                region=settings.s3_region,
                presign_expires=settings.s3_presign_expires,
            )
        else:
            from eln.storage.local import LocalStorageBackend

            uid = user_id or settings.default_user
            kb_root = settings.workspaces_root / uid / "kb"
            _backend = LocalStorageBackend(kb_root=kb_root)

    return _backend


def reset_storage_backend() -> None:
    """Clear the singleton — for use in tests."""
    global _backend
    _backend = None
