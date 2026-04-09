"""
AlphaFold and UniProt tools for the structure_analyst subagent.

Covers:
  - UniProt search (name → accession)
  - AlphaFold DB (EBI) REST API: structure download, pLDDT, PAE
  - ColabFold prediction submission (premium, gated by colabfold_enabled flag)
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from langchain_core.tools import tool

_AFDB_BASE = "https://alphafold.ebi.ac.uk/api"
_UNIPROT_BASE = "https://rest.uniprot.org/uniprotkb"
_COLABFOLD_BASE = "https://api.colabfold.com"

# Module-level run path — set by supervisor before building the graph
_structure_run_path: Path | None = None


def set_structure_run_path(path: Path | None) -> None:
    global _structure_run_path
    _structure_run_path = path


def _get_run_path() -> Path | None:
    return _structure_run_path


# ------------------------------------------------------------------
# UniProt search
# ------------------------------------------------------------------


@tool
def search_uniprot(query: str, organism: str = "human", max_results: int = 5) -> str:
    """Search UniProt to resolve a protein name to its UniProt accession.

    Use this first when the user names a protein rather than giving an accession.

    Args:
        query: Protein name, gene symbol, or description (e.g. "p53", "BRCA1", "insulin receptor").
        organism: Filter by organism common name or taxon (e.g. "human", "mouse", "9606").
        max_results: Maximum number of hits to return (default 5).

    Returns:
        Formatted list of matches: accession, entry name, protein name, organism, review status.
    """
    params: dict = {
        "query": f"({query}) AND (reviewed:true)",
        "fields": "accession,id,protein_name,organism_name,reviewed",
        "format": "json",
        "size": str(max_results),
    }
    if organism:
        organism_q = f"organism_name:{organism}" if not organism.isdigit() else f"taxonomy_id:{organism}"
        params["query"] = f"({query}) AND ({organism_q}) AND (reviewed:true)"

    try:
        resp = httpx.get(f"{_UNIPROT_BASE}/search", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPError as e:
        return f"UniProt search failed: {e}"
    except Exception as e:
        return f"Error: {e}"

    results = data.get("results", [])
    if not results:
        # Retry without reviewed filter
        params["query"] = params["query"].replace(" AND (reviewed:true)", "")
        try:
            resp = httpx.get(f"{_UNIPROT_BASE}/search", params=params, timeout=15)
            resp.raise_for_status()
            results = resp.json().get("results", [])
        except Exception:
            pass

    if not results:
        return f"No UniProt entries found for '{query}' in '{organism}'."

    lines = [f"UniProt results for '{query}' ({organism}):"]
    for r in results:
        acc = r.get("primaryAccession", "?")
        entry = r.get("uniProtkbId", "?")
        prot = r.get("proteinDescription", {})
        name = (
            prot.get("recommendedName", {}).get("fullName", {}).get("value")
            or prot.get("submissionNames", [{}])[0].get("fullName", {}).get("value", "?")
        )
        org = r.get("organism", {}).get("scientificName", "?")
        reviewed = "✓ Swiss-Prot" if r.get("entryType") == "UniProtKB reviewed (Swiss-Prot)" else "TrEMBL"
        lines.append(f"  [{acc}] {entry} — {name} ({org}) [{reviewed}]")

    lines.append("\nUse the accession (e.g. P04637) with fetch_alphafold_structure.")
    return "\n".join(lines)


# ------------------------------------------------------------------
# Fetch structure
# ------------------------------------------------------------------


@tool
def fetch_alphafold_structure(uniprot_accession: str) -> str:
    """Fetch the AlphaFold predicted structure for a protein and save it as a PDB artifact.

    Queries the EBI AlphaFold Database for a pre-computed structure.
    The PDB file is saved to the current run's artifacts folder.

    Args:
        uniprot_accession: UniProt accession (e.g. 'P04637' for human p53).

    Returns:
        Summary of the structure entry and path to the saved PDB artifact,
        or an error if no structure exists in the database.
    """
    acc = uniprot_accession.strip().upper()
    try:
        resp = httpx.get(f"{_AFDB_BASE}/prediction/{acc}", timeout=15)
        if resp.status_code == 404:
            return (
                f"No AlphaFold structure found for '{acc}'. "
                "The protein may not be in the AlphaFold DB. "
                "Try search_uniprot to confirm the accession, or use submit_colabfold_prediction "
                "for a novel sequence."
            )
        resp.raise_for_status()
        entries = resp.json()
    except httpx.HTTPError as e:
        return f"AlphaFold API error: {e}"

    if not entries:
        return f"No entries returned for '{acc}'."

    entry = entries[0]
    pdb_url = entry.get("pdbUrl")
    gene = entry.get("gene", "unknown")
    organism = entry.get("organismScientificName", "unknown")
    uniprot_start = entry.get("uniprotStart", 1)
    uniprot_end = entry.get("uniprotEnd", "?")
    model_version = entry.get("latestVersion", "?")

    if not pdb_url:
        return f"Entry found for '{acc}' but no PDB URL available."

    # Download PDB
    try:
        pdb_resp = httpx.get(pdb_url, timeout=30)
        pdb_resp.raise_for_status()
        pdb_content = pdb_resp.text
    except httpx.HTTPError as e:
        return f"Failed to download PDB file: {e}"

    # Save artifact
    run_path = _get_run_path()
    saved_path = "not saved (no active run)"
    if run_path is not None:
        artifacts_dir = run_path / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        filename = f"alphafold_{acc}.pdb"
        (artifacts_dir / filename).write_text(pdb_content, encoding="utf-8")
        saved_path = str(artifacts_dir / filename)

    return (
        f"AlphaFold Structure: {acc}\n"
        f"Gene: {gene}\n"
        f"Organism: {organism}\n"
        f"Residues: {uniprot_start}–{uniprot_end}\n"
        f"Model version: {model_version}\n"
        f"PDB source: {pdb_url}\n"
        f"Saved to: {saved_path}\n\n"
        f"Use get_alphafold_confidence to inspect per-residue pLDDT scores, "
        f"or get_alphafold_pae for domain boundary analysis."
    )


# ------------------------------------------------------------------
# Confidence scores (pLDDT)
# ------------------------------------------------------------------


@tool
def get_alphafold_confidence(uniprot_accession: str) -> str:
    """Get AlphaFold pLDDT confidence scores for a protein.

    pLDDT (predicted Local Distance Difference Test) is per-residue:
      > 90: very high confidence (well-structured)
      70–90: confident
      50–70: low confidence (may be disordered)
      < 50: very low confidence (likely intrinsically disordered)

    Args:
        uniprot_accession: UniProt accession (e.g. 'P04637').

    Returns:
        Summary statistics, disordered region map, and confidence distribution.
    """
    acc = uniprot_accession.strip().upper()
    try:
        resp = httpx.get(f"{_AFDB_BASE}/prediction/{acc}", timeout=15)
        if resp.status_code == 404:
            return f"No AlphaFold entry for '{acc}'."
        resp.raise_for_status()
        entries = resp.json()
    except httpx.HTTPError as e:
        return f"AlphaFold API error: {e}"

    if not entries:
        return f"No entries for '{acc}'."

    entry = entries[0]
    confidence_url = entry.get("confidenceUrl") or entry.get("paeDocUrl", "").replace(
        "predicted_aligned_error", "confidence"
    )

    # Confidence JSON is embedded in the pLDDT scores field or a separate endpoint
    # Try constructing the confidence URL from the alphafold ID
    af_id = entry.get("entryId", "")
    version = entry.get("latestVersion", 4)
    confidence_url = f"https://alphafold.ebi.ac.uk/files/{af_id}-confidence_v{version}.json"

    try:
        conf_resp = httpx.get(confidence_url, timeout=15)
        conf_resp.raise_for_status()
        conf_data = conf_resp.json()
    except httpx.HTTPError:
        # Fall back: parse from PDB REMARK fields if confidence endpoint unavailable
        return (
            f"Could not fetch confidence JSON for {acc} (AF ID: {af_id}). "
            "The pLDDT scores are embedded in the PDB file saved by fetch_alphafold_structure — "
            "look for REMARK B-factor column or use a structure viewer."
        )

    # conf_data is typically: {"residueNumber": [...], "confidenceScore": [...], "confidenceCategory": [...]}
    # or a flat list of scores
    try:
        if isinstance(conf_data, dict):
            scores = conf_data.get("confidenceScore") or conf_data.get("plddt") or []
        elif isinstance(conf_data, list) and conf_data and isinstance(conf_data[0], dict):
            scores = [r.get("confidenceScore", 0) for r in conf_data]
        else:
            scores = conf_data if isinstance(conf_data, list) else []

        scores = [float(s) for s in scores]
        if not scores:
            return f"Confidence data found but no scores parseable for {acc}."

        n = len(scores)
        mean_score = sum(scores) / n
        very_high = sum(1 for s in scores if s > 90)
        confident = sum(1 for s in scores if 70 < s <= 90)
        low = sum(1 for s in scores if 50 < s <= 70)
        very_low = sum(1 for s in scores if s <= 50)

        # Find disordered segments (contiguous runs with pLDDT < 50)
        disordered_regions: list[tuple[int, int]] = []
        in_disorder = False
        start = 0
        for i, s in enumerate(scores):
            if s < 50 and not in_disorder:
                in_disorder = True
                start = i + 1
            elif s >= 50 and in_disorder:
                disordered_regions.append((start, i))
                in_disorder = False
        if in_disorder:
            disordered_regions.append((start, n))

        disorder_str = (
            ", ".join(f"{a}–{b}" for a, b in disordered_regions[:10])
            if disordered_regions
            else "none detected"
        )
        if len(disordered_regions) > 10:
            disorder_str += f" ... (+{len(disordered_regions) - 10} more)"

        return (
            f"pLDDT Confidence — {acc}\n"
            f"Total residues: {n}\n"
            f"Mean pLDDT: {mean_score:.1f}\n\n"
            f"Distribution:\n"
            f"  > 90 (very high):  {very_high:4d}  ({100*very_high/n:.1f}%)\n"
            f"  70–90 (confident): {confident:4d}  ({100*confident/n:.1f}%)\n"
            f"  50–70 (low):       {low:4d}  ({100*low/n:.1f}%)\n"
            f"  ≤ 50  (disordered):{very_low:4d}  ({100*very_low/n:.1f}%)\n\n"
            f"Disordered regions (pLDDT ≤ 50): {disorder_str}"
        )
    except Exception as e:
        return f"Error parsing confidence scores: {e}"


# ------------------------------------------------------------------
# PAE (Predicted Aligned Error)
# ------------------------------------------------------------------


@tool
def get_alphafold_pae(uniprot_accession: str) -> str:
    """Get the Predicted Aligned Error (PAE) matrix for a protein from AlphaFold.

    PAE captures inter-residue positional uncertainty.
    Low PAE between two residues = high confidence in their relative positions.
    Used to identify domain boundaries and inter-domain flexibility.

    Args:
        uniprot_accession: UniProt accession (e.g. 'P04637').

    Returns:
        Summary: mean PAE, intra-domain vs inter-domain confidence, suggested domain boundaries.
    """
    acc = uniprot_accession.strip().upper()
    try:
        resp = httpx.get(f"{_AFDB_BASE}/prediction/{acc}", timeout=15)
        if resp.status_code == 404:
            return f"No AlphaFold entry for '{acc}'."
        resp.raise_for_status()
        entries = resp.json()
    except httpx.HTTPError as e:
        return f"AlphaFold API error: {e}"

    if not entries:
        return f"No entries for '{acc}'."

    entry = entries[0]
    af_id = entry.get("entryId", "")
    version = entry.get("latestVersion", 4)
    pae_url = f"https://alphafold.ebi.ac.uk/files/{af_id}-predicted_aligned_error_v{version}.json"

    try:
        pae_resp = httpx.get(pae_url, timeout=30)
        pae_resp.raise_for_status()
        pae_data = pae_resp.json()
    except httpx.HTTPError as e:
        return f"Failed to fetch PAE data for {acc}: {e}"

    try:
        # Standard format: [{"predicted_aligned_error": [[...], ...], "max_predicted_aligned_error": X}]
        if isinstance(pae_data, list) and pae_data:
            matrix_data = pae_data[0].get("predicted_aligned_error", [])
            max_pae = pae_data[0].get("max_predicted_aligned_error", 31.75)
        elif isinstance(pae_data, dict):
            matrix_data = pae_data.get("predicted_aligned_error", [])
            max_pae = pae_data.get("max_predicted_aligned_error", 31.75)
        else:
            return "Unexpected PAE data format."

        if not matrix_data:
            return f"PAE data found but matrix is empty for {acc}."

        n = len(matrix_data)
        flat = [float(v) for row in matrix_data for v in row]
        mean_pae = sum(flat) / len(flat)

        # Intra-domain PAE (on-diagonal ±30 residue window) vs off-diagonal
        window = min(30, n // 4)
        intra, inter = [], []
        for i in range(n):
            for j in range(n):
                val = float(matrix_data[i][j])
                if abs(i - j) <= window:
                    intra.append(val)
                else:
                    inter.append(val)

        mean_intra = sum(intra) / len(intra) if intra else 0.0
        mean_inter = sum(inter) / len(inter) if inter else 0.0

        # Rough domain boundary detection: find residues where mean PAE to
        # the rest of the chain spikes (high PAE row mean)
        row_means = [sum(float(v) for v in row) / n for row in matrix_data]
        threshold = mean_pae * 1.4
        boundary_candidates = [
            i + 1 for i, rm in enumerate(row_means) if rm > threshold
        ]
        # Collapse consecutive residues into ranges
        boundaries: list[str] = []
        if boundary_candidates:
            run_start = boundary_candidates[0]
            prev = boundary_candidates[0]
            for r in boundary_candidates[1:]:
                if r == prev + 1:
                    prev = r
                else:
                    boundaries.append(f"{run_start}–{prev}" if run_start != prev else str(run_start))
                    run_start = prev = r
            boundaries.append(f"{run_start}–{prev}" if run_start != prev else str(run_start))

        boundary_str = ", ".join(boundaries[:8]) if boundaries else "none detected (compact fold)"
        if len(boundaries) > 8:
            boundary_str += f" ... (+{len(boundaries)-8} more)"

        quality = (
            "excellent" if mean_pae < 5 else
            "good" if mean_pae < 10 else
            "moderate" if mean_pae < 20 else
            "poor (high inter-domain flexibility or disorder)"
        )

        return (
            f"PAE Analysis — {acc} ({n} residues)\n"
            f"Max PAE in DB: {max_pae:.1f} Å\n"
            f"Mean PAE (whole structure): {mean_pae:.2f} Å  [{quality}]\n"
            f"Mean intra-segment PAE:  {mean_intra:.2f} Å\n"
            f"Mean inter-segment PAE:  {mean_inter:.2f} Å\n\n"
            f"Suggested flexible/boundary regions: {boundary_str}\n\n"
            f"Interpretation:\n"
            f"  Low PAE (<5 Å) = confident relative positioning\n"
            f"  High inter-domain PAE = domains move independently\n"
            f"  Use domain boundaries to guide experimental design (e.g. construct boundaries for purification)"
        )
    except Exception as e:
        return f"Error analysing PAE matrix: {e}"


# ------------------------------------------------------------------
# ColabFold prediction (premium)
# ------------------------------------------------------------------


@tool
def submit_colabfold_prediction(sequence: str, job_name: str = "") -> str:
    """Submit a novel protein sequence to ColabFold for structure prediction.

    This is a premium feature (colabfold_enabled=True required).
    Submits to the public ColabFold MSA server — rate-limited, suitable for
    occasional use. For production batch predictions, install ColabFold locally.

    Args:
        sequence: Amino acid sequence in single-letter code (FASTA body only,
                  no header line needed). For multimer, separate chains with ':'.
        job_name: Optional label for this prediction job.

    Returns:
        Job ticket ID to poll with check_colabfold_job, or error.
    """
    from eln.config import settings

    if not settings.colabfold_enabled:
        return (
            "ColabFold prediction is a premium feature (colabfold_enabled=False). "
            "To enable: set COLABFOLD_ENABLED=true in your environment. "
            "For known proteins, use fetch_alphafold_structure instead (free, instant)."
        )

    seq = sequence.strip().replace(" ", "").replace("\n", "")
    if not seq:
        return "Empty sequence provided."
    if len(seq) > 2500:
        return (
            f"Sequence too long ({len(seq)} aa) for public ColabFold server (max ~2500). "
            "Use a local ColabFold installation for longer sequences."
        )

    label = job_name or f"colabfold_{seq[:8]}"
    fasta = f">{label}\n{seq}\n"

    try:
        resp = httpx.post(
            f"{_COLABFOLD_BASE}/ticket/msa",
            data={"q": fasta, "mode": "pairgreedy"},
            headers={"User-Agent": "eln-plus-plus/0.1 (ai-coscientist)"},
            timeout=30,
        )
        resp.raise_for_status()
        ticket = resp.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return (
                "ColabFold public server is rate-limited. "
                "Try again later or install ColabFold locally."
            )
        return f"ColabFold API error {e.response.status_code}: {e.response.text[:200]}"
    except httpx.HTTPError as e:
        return f"ColabFold request failed: {e}"

    job_id = ticket.get("id") or ticket.get("ticket", "")
    if not job_id:
        return f"Submission succeeded but no job ID returned: {ticket}"

    return (
        f"ColabFold job submitted\n"
        f"Job ID: {job_id}\n"
        f"Sequence: {seq[:20]}{'...' if len(seq) > 20 else ''} ({len(seq)} aa)\n"
        f"Label: {label}\n\n"
        f"Use check_colabfold_job('{job_id}') to poll status. "
        f"MSA generation typically takes 1–5 minutes."
    )


@tool
def check_colabfold_job(job_id: str) -> str:
    """Check the status of a ColabFold prediction job.

    Args:
        job_id: The ticket ID returned by submit_colabfold_prediction.

    Returns:
        Job status (PENDING / RUNNING / COMPLETE / ERROR) and download URL when ready.
    """
    from eln.config import settings

    if not settings.colabfold_enabled:
        return "ColabFold is not enabled (colabfold_enabled=False)."

    try:
        resp = httpx.get(
            f"{_COLABFOLD_BASE}/ticket/{job_id}",
            headers={"User-Agent": "eln-plus-plus/0.1 (ai-coscientist)"},
            timeout=15,
        )
        resp.raise_for_status()
        status = resp.json()
    except httpx.HTTPError as e:
        return f"Status check failed: {e}"

    state = status.get("status", "unknown").upper()
    lines = [f"ColabFold Job: {job_id}", f"Status: {state}"]

    if state == "COMPLETE":
        download_url = f"{_COLABFOLD_BASE}/result/download/{job_id}"
        lines.append(f"Results ready: {download_url}")
        lines.append("Download the .zip to retrieve PDB files and confidence scores.")

        # Save download URL as artifact note
        run_path = _get_run_path()
        if run_path is not None:
            note_path = run_path / "artifacts" / f"colabfold_{job_id}_result.txt"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(
                f"ColabFold results for job {job_id}\nDownload: {download_url}\n",
                encoding="utf-8",
            )
            lines.append(f"Download URL saved to: {note_path}")

    elif state == "ERROR":
        lines.append(f"Error details: {status.get('error', 'none provided')}")
    else:
        lines.append("Job is still running. Poll again in 1–2 minutes.")

    return "\n".join(lines)
