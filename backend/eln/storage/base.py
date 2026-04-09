from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def put_object(self, key: str, source_path: Path) -> str:
        """Copy source_path to storage under key. Returns key."""

    @abstractmethod
    def get_object(self, key: str, dest_path: Path) -> None:
        """Download object at key to dest_path."""

    @abstractmethod
    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a URL (presigned or file://) to access the object."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if the object exists."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the object at key."""
