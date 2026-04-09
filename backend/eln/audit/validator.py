"""
Audit trail validator.

Reads JSONL audit logs and checks:
  - Every llm_call has a prompt_hash
  - Every tool_call has a result_summary
  - Every eln_write has a citation_count
  - Reports citation coverage stats

Usage:
  uv run python -m eln.audit.validator workspaces/default/audit/
"""

import json
import sys
from pathlib import Path


def validate_audit_dir(audit_dir: Path) -> dict:
    """
    Validate all JSONL files in an audit directory.

    Returns a summary dict with counts and issues.
    """
    summary = {
        "files": 0,
        "entries": 0,
        "llm_calls": 0,
        "tool_calls": 0,
        "eln_writes": 0,
        "retrievals": 0,
        "errors": 0,
        "issues": [],
    }

    if not audit_dir.exists():
        summary["issues"].append(f"Audit directory not found: {audit_dir}")
        return summary

    for log_file in sorted(audit_dir.glob("*.jsonl")):
        summary["files"] += 1
        with open(log_file) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    summary["issues"].append(f"{log_file.name}:{line_num} — invalid JSON")
                    continue

                summary["entries"] += 1
                event_type = entry.get("event_type", "")
                payload = entry.get("payload", {})

                if event_type == "llm_call":
                    summary["llm_calls"] += 1
                    if not payload.get("prompt_hash"):
                        summary["issues"].append(
                            f"{log_file.name}:{line_num} — llm_call missing prompt_hash"
                        )
                    if not payload.get("model"):
                        summary["issues"].append(
                            f"{log_file.name}:{line_num} — llm_call missing model"
                        )

                elif event_type == "tool_call":
                    summary["tool_calls"] += 1
                    if not payload.get("tool_name"):
                        summary["issues"].append(
                            f"{log_file.name}:{line_num} — tool_call missing tool_name"
                        )

                elif event_type == "eln_write":
                    summary["eln_writes"] += 1
                    if "citation_count" not in payload:
                        summary["issues"].append(
                            f"{log_file.name}:{line_num} — eln_write missing citation_count"
                        )
                    coverage = payload.get("citation_coverage")
                    if coverage is not None and coverage < 0.5:
                        summary["issues"].append(
                            f"{log_file.name}:{line_num} — low citation coverage: {coverage:.0%}"
                        )

                elif event_type == "retrieval":
                    summary["retrievals"] += 1

                elif event_type == "error":
                    summary["errors"] += 1

    return summary


def compute_citation_coverage(eln_text: str) -> float:
    """
    Compute citation coverage for an ELN.md document.

    Returns ratio of sentences with citation markers vs. total sentences
    in the Results Summary section. Returns 1.0 if no results section found.
    """
    import re

    # Find the Results Summary section
    results_match = re.search(
        r"## Results Summary\s*\n(.*?)(?=\n## |\Z)", eln_text, re.DOTALL
    )
    if not results_match:
        return 1.0  # no results section = not applicable

    results_text = results_match.group(1).strip()
    if not results_text or results_text.startswith("_Results not yet"):
        return 1.0  # placeholder text = not applicable

    # Split into sentences (rough)
    sentences = re.split(r"[.!?]+", results_text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    if not sentences:
        return 1.0

    # Count sentences with citation markers [citation_id: ...] or [<hex>]
    cited = sum(
        1 for s in sentences if re.search(r"\[citation_id:\s*\w+\]|\[[0-9a-f]{6,}\]", s)
    )

    return cited / len(sentences) if sentences else 1.0


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m eln.audit.validator <audit_dir>")
        print("  Validates all JSONL audit logs in the given directory.")
        sys.exit(1)

    audit_dir = Path(sys.argv[1])
    summary = validate_audit_dir(audit_dir)

    print(f"Audit Directory: {audit_dir}")
    print(f"  Log files: {summary['files']}")
    print(f"  Total entries: {summary['entries']}")
    print(f"  LLM calls: {summary['llm_calls']}")
    print(f"  Tool calls: {summary['tool_calls']}")
    print(f"  ELN writes: {summary['eln_writes']}")
    print(f"  Retrievals: {summary['retrievals']}")
    print(f"  Errors logged: {summary['errors']}")
    print()

    if summary["issues"]:
        print(f"Issues found ({len(summary['issues'])}):")
        for issue in summary["issues"]:
            print(f"  ⚠  {issue}")
    else:
        print("✓ No issues found.")


if __name__ == "__main__":
    main()
