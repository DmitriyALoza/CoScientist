"""Pydantic models for Cross-Species Target Intelligence."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResolvedTarget(BaseModel):
    gene_symbol: str
    protein_name: str
    uniprot_id: str
    organism: str
    synonyms: list[str] = Field(default_factory=list)


class Ortholog(BaseModel):
    species: str
    uniprot_id: str
    gene_symbol: str
    percent_identity: float  # 0–100, computed via pairwise alignment
    sequence_length: int
    mapping_confidence: str  # "high" | "moderate" | "low"


class PTMSite(BaseModel):
    residue: str         # e.g. "S15"
    ptm_type: str        # e.g. "Phosphoserine"
    position: int        # 1-based position in reference (human) protein
    species_status: dict[str, str] = Field(default_factory=dict)
    # e.g. {"rat": "conserved", "mouse": "shifted", "dog": "no_evidence"}
    evidence_source: str = "UniProt"


class AntibodyRecord(BaseModel):
    ab_id: str
    clone_name: str | None = None
    vendor: str
    catalog_number: str | None = None
    host_species: str | None = None
    reactivity_species: list[str] = Field(default_factory=list)
    applications: list[str] = Field(default_factory=list)
    epitope_info: str | None = None
    validation_source: str | None = None


class ConservationSummary(BaseModel):
    ortholog_conservation: str   # "High" | "Moderate" | "Low"
    ptm_conservation: str        # "High" | "Moderate" | "Unclear"
    antibody_coverage: str       # "Strong" | "Partial" | "Limited"
    translational_risk: str      # "Low" | "Moderate" | "High" | "Unclear"


class TargetAnalysisRun(BaseModel):
    analysis_id: str
    user_id: str
    target_input: str
    comparison_species: list[str]
    ptm_filter: list[str] = Field(default_factory=list)
    tissue_filter: str | None = None
    status: str = "pending"  # "pending" | "running" | "complete" | "error"
    resolved_target: ResolvedTarget | None = None
    orthologs: list[Ortholog] = Field(default_factory=list)
    ptm_sites: list[PTMSite] = Field(default_factory=list)
    antibodies: list[AntibodyRecord] = Field(default_factory=list)
    conservation_summary: ConservationSummary | None = None
    ai_interpretation: str | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: str
    completed_at: str | None = None
