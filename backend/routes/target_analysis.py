"""Cross-Species Target Intelligence endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from eln.models.target_analysis import (
    AntibodyRecord,
    ConservationSummary,
    Ortholog,
    PTMSite,
    ResolvedTarget,
    TargetAnalysisRun,
)
from eln.workspace.manager import WorkspaceManager
from eln.workspace.target_analysis_store import TargetAnalysisStore

router = APIRouter(tags=["target-analysis"])

DEFAULT_SPECIES = ["rat", "mouse", "dog", "cynomolgus monkey"]


class AnalysisRequest(BaseModel):
    target: str
    reference_species: str = "human"
    comparison_species: list[str] = DEFAULT_SPECIES
    ptm_types: list[str] = []
    tissue_filter: str | None = None
    user_id: str = "default"


# ---------------------------------------------------------------------------
# POST /api/target-analysis  — run the full pipeline
# ---------------------------------------------------------------------------

@router.post("/target-analysis", status_code=201)
async def run_target_analysis(body: AnalysisRequest) -> dict:
    """Run the Cross-Species Target Intelligence pipeline synchronously."""
    from eln.tools.target_intelligence_tools import (
        align_sequences,
        get_orthologs,
        get_ptm_annotations,
        resolve_target,
        search_antibodies,
        set_target_analysis_store,
    )
    import json

    wm = WorkspaceManager(user_id=body.user_id)
    store = TargetAnalysisStore(wm.target_analyses_path())
    set_target_analysis_store(store)

    analysis_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    run = TargetAnalysisRun(
        analysis_id=analysis_id,
        user_id=body.user_id,
        target_input=body.target,
        comparison_species=body.comparison_species,
        ptm_filter=body.ptm_types,
        tissue_filter=body.tissue_filter,
        status="running",
        created_at=now,
    )
    store.save(run)

    warnings: list[str] = []

    try:
        # Step 1: resolve target
        resolved_raw = resolve_target.invoke({"gene_or_protein": body.target, "species": body.reference_species})
        resolved_data = json.loads(resolved_raw)
        if "error" in resolved_data:
            run.status = "error"
            run.warnings = [resolved_data["error"]]
            run.completed_at = datetime.now(timezone.utc).isoformat()
            store.save(run)
            return run.model_dump(mode="json")

        run.resolved_target = ResolvedTarget(**resolved_data)
        ref_uid = run.resolved_target.uniprot_id
        gene_sym = run.resolved_target.gene_symbol

        # Step 2: get orthologs
        orth_raw = get_orthologs.invoke({
            "gene_symbol": gene_sym,
            "reference_uniprot_id": ref_uid,
            "comparison_species": body.comparison_species,
        })
        orth_data = json.loads(orth_raw)
        warnings += orth_data.get("warnings", [])
        orthologs = [Ortholog(**o) for o in orth_data.get("orthologs", [])]

        # Step 3: align sequences
        all_uids = [ref_uid] + [o.uniprot_id for o in orthologs]
        align_raw = align_sequences.invoke({"uniprot_ids": all_uids})
        align_data = json.loads(align_raw)
        pct_ids: dict[str, float] = align_data.get("percent_identities", {})
        for orth in orthologs:
            orth.percent_identity = pct_ids.get(orth.uniprot_id, 0.0)
            # Update confidence based on identity
            if orth.percent_identity >= 85:
                orth.mapping_confidence = "high"
            elif orth.percent_identity >= 60:
                orth.mapping_confidence = "moderate"
            else:
                orth.mapping_confidence = "low"
        run.orthologs = orthologs

        # Step 4: PTM annotations
        uid_map = {body.reference_species: ref_uid}
        uid_map.update({o.species: o.uniprot_id for o in orthologs})
        ptm_raw = get_ptm_annotations.invoke({
            "uniprot_ids_by_species": uid_map,
            "ptm_types": body.ptm_types or None,
        })
        ptm_data = json.loads(ptm_raw)
        run.ptm_sites = [PTMSite(**p) for p in ptm_data.get("ptm_sites", [])]

        # Step 5: antibody search
        ab_raw = search_antibodies.invoke({
            "gene_symbol": gene_sym,
            "species_list": body.comparison_species,
        })
        ab_data = json.loads(ab_raw)
        warnings += ab_data.get("warnings", [])
        run.antibodies = [AntibodyRecord(**a) for a in ab_data.get("antibodies", [])]

        # Step 6: compute conservation summary
        run.conservation_summary = _compute_conservation_summary(run)
        run.warnings = warnings
        run.status = "complete"
        run.completed_at = datetime.now(timezone.utc).isoformat()
        store.save(run)

    except Exception as exc:
        run.status = "error"
        run.warnings = warnings + [str(exc)]
        run.completed_at = datetime.now(timezone.utc).isoformat()
        store.save(run)

    return run.model_dump(mode="json")


def _compute_conservation_summary(run: TargetAnalysisRun) -> ConservationSummary:
    """Derive the four conservation indicator badges from the run data."""
    # Ortholog conservation — based on mean % identity
    if run.orthologs:
        mean_id = sum(o.percent_identity for o in run.orthologs) / len(run.orthologs)
        ortholog_conservation = "High" if mean_id >= 85 else ("Moderate" if mean_id >= 60 else "Low")
    else:
        ortholog_conservation = "Unclear"

    # PTM conservation — fraction of sites "conserved" across all species
    if run.ptm_sites:
        all_statuses = [
            s for site in run.ptm_sites for s in site.species_status.values()
            if s != "conserved" or True  # count all
        ]
        conserved = sum(1 for site in run.ptm_sites
                        for s in site.species_status.values() if s == "conserved")
        total = sum(len(site.species_status) for site in run.ptm_sites)
        frac = conserved / total if total else 0
        ptm_conservation = "High" if frac >= 0.8 else ("Moderate" if frac >= 0.5 else "Unclear")
    else:
        ptm_conservation = "Unclear"

    # Antibody coverage
    n_ab = len(run.antibodies)
    antibody_coverage = "Strong" if n_ab >= 10 else ("Partial" if n_ab >= 3 else "Limited")

    # Translational risk — derived from ortholog + PTM conservation
    if ortholog_conservation == "High" and ptm_conservation in ("High", "Moderate"):
        translational_risk = "Low"
    elif ortholog_conservation == "Low" or ptm_conservation == "Unclear":
        translational_risk = "High"
    else:
        translational_risk = "Moderate"

    return ConservationSummary(
        ortholog_conservation=ortholog_conservation,
        ptm_conservation=ptm_conservation,
        antibody_coverage=antibody_coverage,
        translational_risk=translational_risk,
    )


# ---------------------------------------------------------------------------
# GET /api/target-analyses  — list
# ---------------------------------------------------------------------------

@router.get("/target-analyses")
async def list_target_analyses(user_id: str = "default", limit: int = 20) -> list[dict]:
    wm = WorkspaceManager(user_id=user_id)
    store = TargetAnalysisStore(wm.target_analyses_path())
    runs = store.list(limit=limit)
    return [r.model_dump(mode="json") for r in runs]


# ---------------------------------------------------------------------------
# GET /api/target-analyses/{id}  — get one
# ---------------------------------------------------------------------------

@router.get("/target-analyses/{analysis_id}")
async def get_target_analysis(analysis_id: str, user_id: str = "default") -> dict:
    wm = WorkspaceManager(user_id=user_id)
    store = TargetAnalysisStore(wm.target_analyses_path())
    run = store.load(analysis_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return run.model_dump(mode="json")
