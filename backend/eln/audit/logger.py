import hashlib
import json
import time
from pathlib import Path

from opentelemetry import trace


class AuditLogger:
    """
    Append-only JSONL audit trail.

    Each line is a JSON object: {ts, event_type, session_id, payload}
    The log is NEVER overwritten — only appended to.
    Prompts are stored as SHA-256 hashes, not raw text, for privacy.
    """

    def __init__(self, audit_dir: Path, session_id: str):
        self.audit_dir = audit_dir
        self.session_id = session_id
        audit_dir.mkdir(parents=True, exist_ok=True)
        # One file per calendar day
        date_str = time.strftime("%Y-%m-%d")
        self.log_path = audit_dir / f"{date_str}.jsonl"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _write(self, event_type: str, payload: dict) -> None:
        entry = {
            "ts": time.time(),
            "event_type": event_type,
            "session_id": self.session_id,
            "payload": payload,
        }

        # Correlate with OTel trace if active
        span_ctx = trace.get_current_span().get_span_context()
        if span_ctx.trace_id:
            entry["trace_id"] = format(span_ctx.trace_id, "032x")
            entry["span_id"] = format(span_ctx.span_id, "016x")

        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    @staticmethod
    def _hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Public event methods
    # ------------------------------------------------------------------

    def log_user_action(self, action: str, details: dict | None = None) -> None:
        self._write("user_action", {"action": action, "details": details or {}})

    def log_llm_call(
        self,
        provider: str,
        model: str,
        prompt: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float | None = None,
        subagent: str | None = None,
    ) -> None:
        self._write(
            "llm_call",
            {
                "provider": provider,
                "model": model,
                "prompt_hash": self._hash(prompt),
                "prompt_tokens": len(prompt.split()),  # rough token estimate for non-API contexts
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
                "subagent": subagent,
            },
        )

    def log_tool_call(
        self,
        tool_name: str,
        args: dict,
        result_summary: str,
        artifacts_written: list[str] | None = None,
    ) -> None:
        self._write(
            "tool_call",
            {
                "tool_name": tool_name,
                "args": args,
                "result_summary": result_summary,
                "artifacts_written": artifacts_written or [],
            },
        )

    def log_retrieval(
        self,
        query: str,
        source_types: list[str],
        doc_ids: list[str],
        excerpt_hashes: list[str],
    ) -> None:
        self._write(
            "retrieval",
            {
                "query_hash": self._hash(query),
                "source_types": source_types,
                "doc_ids": doc_ids,
                "excerpt_hashes": excerpt_hashes,
            },
        )

    def log_eln_write(
        self,
        run_id: str,
        output_path: str,
        citation_count: int,
        citation_coverage: float | None = None,
    ) -> None:
        self._write(
            "eln_write",
            {
                "run_id": run_id,
                "output_path": output_path,
                "citation_count": citation_count,
                "citation_coverage": citation_coverage,
            },
        )

    def log_error(self, error_type: str, message: str, context: dict | None = None) -> None:
        self._write(
            "error",
            {"error_type": error_type, "message": message, "context": context or {}},
        )
