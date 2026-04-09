"""
Global audit logger singleton.

Same accessor pattern as set_retriever() in eln/tools/retrieval_tools.py.
Call set_audit_logger() once at startup; providers and retrieval use
get_audit_logger() without needing to pass the instance around.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from eln.audit.logger import AuditLogger

_audit_logger: "AuditLogger | None" = None


def set_audit_logger(logger: "AuditLogger") -> None:
    global _audit_logger
    _audit_logger = logger


def get_audit_logger() -> "AuditLogger | None":
    return _audit_logger
