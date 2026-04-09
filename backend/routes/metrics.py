"""Dashboard metrics aggregation endpoint."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from eln.config import settings

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def get_metrics(user_id: str = "default") -> dict:
    """Aggregate workspace-level metrics for the dashboard."""
    wm_root = settings.workspaces_root / user_id
    runs_dir = wm_root / "runs"

    eln_count = 0
    citation_count = 0
    deviation_count = 0
    run_rows: list[dict] = []
    activity: list[dict] = []

    if runs_dir.exists():
        for run_dir in sorted(runs_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            manifest_path = run_dir / "run_manifest.json"
            if not manifest_path.exists():
                continue
            try:
                data = json.loads(manifest_path.read_text())
            except Exception:
                continue

            if (run_dir / "ELN.md").exists():
                eln_count += 1
                activity.append({
                    "type": "eln_generated",
                    "label": f"ELN generated: {data.get('title', run_dir.name)}",
                    "ts": data.get("timestamp", ""),
                })

            citations = data.get("citations", [])
            citation_count += len(citations)
            deviation_count += len(data.get("deviations", []))

            run_rows.append({
                "run_id": data.get("run_id", run_dir.name),
                "title": data.get("title", run_dir.name),
                "domain": data.get("domain", ""),
                "timestamp": data.get("timestamp", ""),
                "has_eln": (run_dir / "ELN.md").exists(),
            })

    # Hypothesis counts
    hypothesis_count = 0
    testing_count = 0
    hyp_dir = wm_root / "hypotheses"
    if hyp_dir.exists():
        for f in hyp_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                hyps = data.get("hypotheses", [])
                hypothesis_count += len(hyps)
                testing_count += sum(1 for h in hyps if h.get("status") == "testing")
                activity.append({
                    "type": "hypotheses_generated",
                    "label": f"{len(hyps)} hypotheses generated",
                    "ts": data.get("created_at", ""),
                })
            except Exception:
                continue

    # Experiment counts
    active_experiments = 0
    completed_experiments = 0
    exp_dir = wm_root / "experiments"
    if exp_dir.exists():
        for f in exp_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                status = data.get("status", "")
                if status == "active":
                    active_experiments += 1
                elif status in ("converged", "exhausted"):
                    completed_experiments += 1
            except Exception:
                continue

    # KB stats
    kb_stats = _get_kb_stats(wm_root / "kb")

    # Sort activity by timestamp descending, take top 10
    activity.sort(key=lambda x: x.get("ts", ""), reverse=True)

    return {
        "eln_count": eln_count,
        "citation_count": citation_count,
        "hypothesis_count": hypothesis_count,
        "testing_count": testing_count,
        "active_experiments": active_experiments,
        "completed_experiments": completed_experiments,
        "deviation_count": deviation_count,
        "recent_runs": run_rows[:5],
        "kb_stats": kb_stats,
        "activity": activity[:10],
    }


def _get_kb_stats(kb_root: Path) -> dict:
    collections = ["papers", "sops_internal", "sops_manufacturer", "reports", "eln_entries", "reference_docs"]
    stats: dict[str, int] = {}
    total = 0
    for col in collections:
        col_dir = kb_root / col
        count = len(list(col_dir.glob("*"))) if col_dir.exists() else 0
        stats[col] = count
        total += count
    return {"by_collection": stats, "total_documents": total}
