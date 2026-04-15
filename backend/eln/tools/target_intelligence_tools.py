"""
Deterministic tools for Cross-Species Target Intelligence.

Each tool calls a public API and returns structured JSON strings.
The LLM agent calls these in sequence, then interprets the results.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import httpx
from langchain_core.tools import tool

if TYPE_CHECKING:
    from eln.workspace.target_analysis_store import TargetAnalysisStore

# ---------------------------------------------------------------------------
# Store singleton
# ---------------------------------------------------------------------------

_store: TargetAnalysisStore | None = None


def set_target_analysis_store(store: TargetAnalysisStore) -> None:
    global _store
    _store = store


def _get_store() -> TargetAnalysisStore:
    if _store is None:
        raise RuntimeError("TargetAnalysisStore not initialised. Call set_target_analysis_store() first.")
    return _store


# ---------------------------------------------------------------------------
# Species → taxonomy mapping
# ---------------------------------------------------------------------------

_SPECIES_TAXON: dict[str, tuple[str, int]] = {
    "human":              ("Homo sapiens", 9606),
    "homo sapiens":       ("Homo sapiens", 9606),
    "rat":                ("Rattus norvegicus", 10116),
    "rattus norvegicus":  ("Rattus norvegicus", 10116),
    "mouse":              ("Mus musculus", 10090),
    "mus musculus":       ("Mus musculus", 10090),
    "dog":                ("Canis lupus familiaris", 9615),
    "canis":              ("Canis lupus familiaris", 9615),
    "cynomolgus monkey":  ("Macaca fascicularis", 9541),
    "cynomolgus":         ("Macaca fascicularis", 9541),
    "macaque":            ("Macaca fascicularis", 9541),
    "monkey":             ("Macaca fascicularis", 9541),
    "minipig":            ("Sus scrofa", 9823),
    "pig":                ("Sus scrofa", 9823),
    "rabbit":             ("Oryctolagus cuniculus", 9986),
    "zebrafish":          ("Danio rerio", 7955),
}


def _canonical_species(name: str) -> tuple[str, int] | None:
    return _SPECIES_TAXON.get(name.lower().strip())


# ---------------------------------------------------------------------------
# Tool 1: resolve_target
# ---------------------------------------------------------------------------

@tool
def resolve_target(gene_or_protein: str, species: str = "human") -> str:
    """Resolve a free-text gene or protein name to a canonical UniProt entry.

    Args:
        gene_or_protein: Gene symbol (e.g. "TP53") or protein name.
        species: Common name of the reference species (default: "human").

    Returns:
        JSON string with ResolvedTarget fields: gene_symbol, protein_name,
        uniprot_id, organism, synonyms.
    """
    spec = _canonical_species(species)
    sci_name = spec[0] if spec else "Homo sapiens"
    taxon_id = spec[1] if spec else 9606

    base = "https://rest.uniprot.org/uniprotkb/search"
    fields = "accession,gene_names,protein_name,organism_name"

    # Try reviewed (Swiss-Prot) entry first with exact gene match
    for query in [
        f'gene_exact:"{gene_or_protein}" AND taxonomy_id:{taxon_id} AND reviewed:true',
        f'gene:"{gene_or_protein}" AND taxonomy_id:{taxon_id} AND reviewed:true',
        f'"{gene_or_protein}" AND taxonomy_id:{taxon_id} AND reviewed:true',
    ]:
        try:
            r = httpx.get(base, params={"query": query, "fields": fields, "format": "json", "size": 3},
                          timeout=15)
            r.raise_for_status()
            hits = r.json().get("results", [])
            if hits:
                entry = hits[0]
                acc = entry["primaryAccession"]
                gene_names = entry.get("genes", [])
                gene_sym = (
                    gene_names[0]["geneName"]["value"]
                    if gene_names and "geneName" in gene_names[0]
                    else gene_or_protein.upper()
                )
                synonyms: list[str] = []
                for gn in gene_names:
                    synonyms += [s["value"] for s in gn.get("synonyms", [])]

                pd = entry.get("proteinDescription", {})
                rec = pd.get("recommendedName", {})
                prot_name = rec.get("fullName", {}).get("value", gene_or_protein)

                organism = entry.get("organism", {}).get("scientificName", sci_name)

                return json.dumps({
                    "gene_symbol": gene_sym,
                    "protein_name": prot_name,
                    "uniprot_id": acc,
                    "organism": organism,
                    "synonyms": synonyms[:8],
                })
        except Exception as exc:
            continue

    return json.dumps({"error": f"Could not resolve '{gene_or_protein}' in {sci_name}."})


# ---------------------------------------------------------------------------
# Tool 2: get_orthologs
# ---------------------------------------------------------------------------

@tool
def get_orthologs(gene_symbol: str, reference_uniprot_id: str, comparison_species: list[str]) -> str:
    """Find orthologs for a human protein in requested comparison species.

    Searches UniProt for the same gene symbol in each species, then returns
    basic metadata. Percent identity is computed later by align_sequences.

    Args:
        gene_symbol: Canonical gene symbol, e.g. "TP53".
        reference_uniprot_id: UniProt accession of the human protein (for context).
        comparison_species: List of common species names, e.g. ["rat", "mouse", "dog"].

    Returns:
        JSON list of Ortholog records.
    """
    base = "https://rest.uniprot.org/uniprotkb/search"
    fields = "accession,gene_names,protein_name,sequence,organism_name"
    orthologs = []
    warnings: list[str] = []

    for sp in comparison_species:
        spec = _canonical_species(sp)
        if not spec:
            warnings.append(f"Unknown species: {sp}")
            continue

        sci_name, taxon_id = spec
        for query in [
            f'gene_exact:"{gene_symbol}" AND taxonomy_id:{taxon_id} AND reviewed:true',
            f'gene:"{gene_symbol}" AND taxonomy_id:{taxon_id} AND reviewed:true',
        ]:
            try:
                r = httpx.get(base, params={"query": query, "fields": fields, "format": "json", "size": 1},
                              timeout=15)
                r.raise_for_status()
                hits = r.json().get("results", [])
                if not hits:
                    continue

                entry = hits[0]
                acc = entry["primaryAccession"]
                gene_names = entry.get("genes", [])
                gsym = (
                    gene_names[0]["geneName"]["value"]
                    if gene_names and "geneName" in gene_names[0]
                    else gene_symbol
                )
                seq_len = len(entry.get("sequence", {}).get("value", ""))

                orthologs.append({
                    "species": sp,
                    "uniprot_id": acc,
                    "gene_symbol": gsym,
                    "percent_identity": 0.0,  # filled in by align_sequences
                    "sequence_length": seq_len,
                    "mapping_confidence": "high" if "reviewed" in query else "moderate",
                })
                break
            except Exception:
                continue
        else:
            warnings.append(f"No reviewed ortholog found for {gene_symbol} in {sci_name}.")

    return json.dumps({"orthologs": orthologs, "warnings": warnings})


# ---------------------------------------------------------------------------
# Tool 3: align_sequences
# ---------------------------------------------------------------------------

@tool
def align_sequences(uniprot_ids: list[str]) -> str:
    """Fetch protein sequences and compute pairwise percent identity vs the first entry.

    Args:
        uniprot_ids: List of UniProt accessions; the first is treated as the
                     reference. Typically [human_id, rat_id, mouse_id, ...].

    Returns:
        JSON dict mapping uniprot_id → percent_identity (float, 0–100).
        Reference vs reference is always 100.0.
    """
    if not uniprot_ids:
        return json.dumps({"error": "No UniProt IDs provided."})

    # Fetch sequences
    sequences: dict[str, str] = {}
    for uid in uniprot_ids:
        try:
            r = httpx.get(f"https://rest.uniprot.org/uniprotkb/{uid}.fasta", timeout=20)
            r.raise_for_status()
            lines = r.text.strip().splitlines()
            seq = "".join(l for l in lines if not l.startswith(">"))
            if seq:
                sequences[uid] = seq
        except Exception:
            continue

    if not sequences:
        return json.dumps({"error": "Could not fetch any sequences."})

    ref_id = uniprot_ids[0]
    ref_seq = sequences.get(ref_id, "")
    result: dict[str, float] = {ref_id: 100.0}

    if ref_seq:
        try:
            from Bio import Align

            aligner = Align.PairwiseAligner()
            aligner.mode = "global"
            aligner.substitution_matrix = Align.substitution_matrices.load("BLOSUM62")
            aligner.open_gap_score = -10
            aligner.extend_gap_score = -0.5

            for uid, seq in sequences.items():
                if uid == ref_id:
                    continue
                try:
                    alignments = aligner.align(ref_seq, seq)
                    best = alignments[0]
                    aligned_ref = str(best[0])
                    aligned_seq = str(best[1])
                    matches = sum(
                        a == b for a, b in zip(aligned_ref, aligned_seq) if a != "-" and b != "-"
                    )
                    denom = max(len(ref_seq), len(seq))
                    result[uid] = round((matches / denom) * 100, 1) if denom else 0.0
                except Exception:
                    result[uid] = 0.0
        except ImportError:
            # Biopython not available — return length-based rough estimate
            for uid, seq in sequences.items():
                if uid == ref_id:
                    continue
                shorter = min(len(ref_seq), len(seq))
                longer = max(len(ref_seq), len(seq))
                result[uid] = round((shorter / longer) * 100, 1) if longer else 0.0

    return json.dumps({"percent_identities": result})


# ---------------------------------------------------------------------------
# Tool 4: get_ptm_annotations
# ---------------------------------------------------------------------------

@tool
def get_ptm_annotations(uniprot_ids_by_species: dict[str, str], ptm_types: list[str] | None = None) -> str:
    """Retrieve PTM site annotations for a set of species and compare conservation.

    Fetches UniProt feature annotations (modified residues, glycosylation,
    lipidation) for each UniProt ID, then categorises each human PTM site
    as conserved, shifted, or no_evidence in each comparison species.

    Args:
        uniprot_ids_by_species: Mapping of species name → UniProt ID.
                                The key "human" (or whichever appears first) is treated as reference.
        ptm_types: Optional list of PTM type keywords to filter, e.g. ["Phospho", "Glyco"].
                   If empty / None, all modification types are included.

    Returns:
        JSON list of PTMSite records.
    """
    _PTM_FEATURE_TYPES = {"Modified residue", "Glycosylation", "Lipidation", "Cross-link"}
    ptm_filter = [p.lower() for p in (ptm_types or [])]

    def _fetch_ptms(uid: str) -> list[dict]:
        try:
            r = httpx.get(f"https://rest.uniprot.org/uniprotkb/{uid}",
                          params={"fields": "ft_mod_res,ft_carbohyd,ft_lipid,ft_crosslnk", "format": "json"},
                          timeout=20)
            r.raise_for_status()
            features = r.json().get("features", [])
            results = []
            for feat in features:
                if feat.get("type") not in _PTM_FEATURE_TYPES:
                    continue
                desc = feat.get("description", "")
                if ptm_filter and not any(kw in desc.lower() for kw in ptm_filter):
                    continue
                pos = feat.get("location", {}).get("start", {}).get("value")
                if pos is None:
                    continue
                results.append({"position": int(pos), "description": desc, "type": feat.get("type")})
            return results
        except Exception:
            return []

    # Determine reference species (prefer "human", else first key)
    species_list = list(uniprot_ids_by_species.keys())
    ref_species = "human" if "human" in species_list else species_list[0]
    ref_uid = uniprot_ids_by_species[ref_species]

    # Fetch all PTMs
    all_ptms: dict[str, list[dict]] = {}
    for sp, uid in uniprot_ids_by_species.items():
        all_ptms[sp] = _fetch_ptms(uid)

    ref_ptms = all_ptms.get(ref_species, [])
    comparison_species = [s for s in species_list if s != ref_species]

    ptm_sites = []
    for ref_ptm in ref_ptms:
        pos = ref_ptm["position"]
        residue_letter = _residue_letter(ref_ptm["description"])
        residue_code = f"{residue_letter}{pos}"

        species_status: dict[str, str] = {ref_species: "conserved"}
        for sp in comparison_species:
            comp_ptms = all_ptms.get(sp, [])
            if not comp_ptms:
                species_status[sp] = "no_evidence"
                continue

            # Check for exact match, nearby (±5 aa), or amino-acid change
            exact = [p for p in comp_ptms if p["position"] == pos and p["description"] == ref_ptm["description"]]
            nearby = [p for p in comp_ptms if abs(p["position"] - pos) <= 5 and p["description"] == ref_ptm["description"]]
            same_type = [p for p in comp_ptms if abs(p["position"] - pos) <= 10]

            if exact:
                species_status[sp] = "conserved"
            elif nearby:
                species_status[sp] = "shifted"
            elif same_type:
                species_status[sp] = "residue_changed"
            else:
                species_status[sp] = "no_evidence"

        ptm_sites.append({
            "residue": residue_code,
            "ptm_type": ref_ptm["description"],
            "position": pos,
            "species_status": species_status,
            "evidence_source": "UniProt",
        })

    return json.dumps({"ptm_sites": ptm_sites[:40]})  # cap at 40 to keep LLM context manageable


def _residue_letter(description: str) -> str:
    """Extract single-letter amino acid code from a PTM description."""
    mapping = {
        "Ser": "S", "Thr": "T", "Tyr": "Y", "His": "H",
        "Lys": "K", "Arg": "R", "Cys": "C", "Asn": "N",
        "Gln": "Q", "Asp": "D", "Glu": "E", "Met": "M",
        "Pro": "P", "Trp": "W",
    }
    for three, one in mapping.items():
        if three.lower() in description.lower():
            return one
    return "X"


# ---------------------------------------------------------------------------
# Tool 5: search_antibodies
# ---------------------------------------------------------------------------

@tool
def search_antibodies(gene_symbol: str, species_list: list[str]) -> str:
    """Search the Antibody Registry for antibodies targeting a gene/protein.

    Args:
        gene_symbol: Gene symbol to search, e.g. "TP53".
        species_list: Species to prioritise for reactivity filtering.

    Returns:
        JSON list of AntibodyRecord objects (up to 20).
        Includes a warning if fewer than 3 results are found.
    """
    warnings: list[str] = []
    antibodies: list[dict] = []

    try:
        r = httpx.get(
            "https://antibodyregistry.org/api/antibodies",
            params={"q": gene_symbol, "limit": 30},
            timeout=20,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        data = r.json()
        raw = data if isinstance(data, list) else data.get("antibodies", data.get("results", []))

        for ab in raw[:20]:
            # Normalise the messy registry fields
            reactivity = _parse_list_field(
                ab.get("reactivityList") or ab.get("species_reactivity") or ab.get("reactivity", "")
            )
            apps = _parse_list_field(
                ab.get("applicationsList") or ab.get("applications") or ab.get("application", "")
            )
            antibodies.append({
                "ab_id": str(ab.get("abId") or ab.get("id") or ""),
                "clone_name": ab.get("cloneName") or ab.get("clone"),
                "vendor": ab.get("vendor") or ab.get("supplier") or "",
                "catalog_number": ab.get("catalogNum") or ab.get("catalog_number"),
                "host_species": ab.get("hostSpecies") or ab.get("host_species"),
                "reactivity_species": reactivity,
                "applications": apps,
                "epitope_info": ab.get("epitope") or ab.get("epitopeDescription"),
                "validation_source": ab.get("url") or ab.get("productUrl"),
            })
    except Exception as exc:
        warnings.append(f"Antibody Registry lookup failed: {exc}. Results may be incomplete.")

    if len(antibodies) < 3:
        warnings.append(
            f"Fewer than 3 antibody records found for {gene_symbol}. "
            "Commercial coverage may be limited — consider checking vendor sites directly."
        )

    return json.dumps({"antibodies": antibodies, "warnings": warnings})


def _parse_list_field(value: str | list | None) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    return [v.strip() for v in re.split(r"[,;|/]", str(value)) if v.strip()]


# ---------------------------------------------------------------------------
# Tool 6: save_target_analysis
# ---------------------------------------------------------------------------

@tool
def save_target_analysis(analysis_json: str) -> str:
    """Persist a completed TargetAnalysisRun to the workspace store.

    Args:
        analysis_json: JSON string conforming to the TargetAnalysisRun schema.

    Returns:
        JSON with {"analysis_id": "..."} on success, or {"error": "..."} on failure.
    """
    from eln.models.target_analysis import TargetAnalysisRun

    try:
        run = TargetAnalysisRun.model_validate_json(analysis_json)
        _get_store().save(run)
        return json.dumps({"analysis_id": run.analysis_id, "status": "saved"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})
