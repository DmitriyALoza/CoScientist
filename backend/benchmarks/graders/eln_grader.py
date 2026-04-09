"""
ELN completeness grader.

Parses an ELN.md document and scores it against a weighted checklist:

  Section presence         (40 pts total)
  Reagents table fields    (20 pts)
  Controls checklist       (15 pts)
  Deviations quality       (10 pts)
  Citation density         (15 pts)

Total: 100 pts
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ELNGradeResult:
    score: float          # 0 – 100
    section_score: float
    reagents_score: float
    controls_score: float
    deviations_score: float
    citation_score: float
    missing_sections: list[str] = field(default_factory=list)
    missing_reagent_fields: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# Required sections (case-insensitive heading match)
_REQUIRED_SECTIONS = [
    "objective",
    "hypothesis",
    "samples",
    "reagents",
    "parameters",
    "controls",
    "deviations",
    "results",
    "citations",
]

# Reagents table must have these column headers
_REAGENT_FIELDS = ["vendor", "catalog", "lot", "concentration"]

# Controls checklist markers
_CONTROL_CHECKED = re.compile(r"\[x\]", re.IGNORECASE)
_CONTROL_MISSING = re.compile(r"⚠️\s*\*\*MISSING", re.IGNORECASE)
_CONTROL_ITEM = re.compile(r"^\s*-\s*\[", re.MULTILINE)

# Deviation impact assessment
_DEVIATION_IMPACT = re.compile(r"impact", re.IGNORECASE)

# Inline citations
_INLINE_CITE = re.compile(r"\[citation_id:", re.IGNORECASE)

# Rough factual claim heuristic: sentences containing numbers, percentages, or
# quantitative terms count as "factual claims" requiring a citation.
_FACTUAL_CLAIM = re.compile(r"\d+[\s%µ]|p\s*[<=>]\s*0\.\d|fold[- ]change|statistically", re.IGNORECASE)


def _find_section(text: str, name: str) -> str | None:
    """Return the text block under a given heading, or None if absent."""
    pattern = re.compile(
        r"#+\s+" + re.escape(name) + r"\s*\n(.*?)(?=\n#+\s|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def grade(eln_md: str) -> ELNGradeResult:
    """Score an ELN.md string on a 100-point scale."""

    # ── Section presence (40 pts, ~4.4 per section) ─────────────────────
    section_pts_each = 40.0 / len(_REQUIRED_SECTIONS)
    missing_sections: list[str] = []
    for sec in _REQUIRED_SECTIONS:
        block = _find_section(eln_md, sec)
        if block is None or len(block.strip()) < 10:
            missing_sections.append(sec)
    section_score = (len(_REQUIRED_SECTIONS) - len(missing_sections)) * section_pts_each

    # ── Reagents table fields (20 pts) ───────────────────────────────────
    reagents_block = _find_section(eln_md, "reagents") or ""
    missing_reagent_fields: list[str] = []
    for col in _REAGENT_FIELDS:
        if col.lower() not in reagents_block.lower():
            missing_reagent_fields.append(col)
    reagents_score = (len(_REAGENT_FIELDS) - len(missing_reagent_fields)) / len(_REAGENT_FIELDS) * 20

    # ── Controls checklist (15 pts) ──────────────────────────────────────
    controls_block = _find_section(eln_md, "controls") or ""
    total_control_items = len(_CONTROL_ITEM.findall(controls_block))
    missing_critical = len(_CONTROL_MISSING.findall(controls_block))
    if total_control_items == 0:
        controls_score = 0.0
    else:
        penalty = missing_critical * 3  # each missing critical = -3 pts
        controls_score = max(0, 15 - penalty) * (total_control_items > 0)

    # ── Deviations quality (10 pts) ──────────────────────────────────────
    deviations_block = _find_section(eln_md, "deviations") or ""
    if not deviations_block.strip() or deviations_block.strip().lower() in ("none", "n/a"):
        deviations_score = 10.0  # No deviations is fine
    elif _DEVIATION_IMPACT.search(deviations_block):
        deviations_score = 10.0
    else:
        deviations_score = 5.0  # Deviations present but no impact assessment

    # ── Citation density (15 pts) ────────────────────────────────────────
    results_block = _find_section(eln_md, "results") or ""
    factual_claims = len(_FACTUAL_CLAIM.findall(results_block))
    inline_cites = len(_INLINE_CITE.findall(eln_md))
    if factual_claims == 0:
        citation_score = 15.0 if inline_cites > 0 else 7.5
    else:
        density = inline_cites / factual_claims
        if density >= 0.33:
            citation_score = 15.0
        elif density >= 0.15:
            citation_score = 10.0
        elif density > 0:
            citation_score = 5.0
        else:
            citation_score = 0.0

    total = section_score + reagents_score + controls_score + deviations_score + citation_score

    notes: list[str] = []
    if missing_sections:
        notes.append(f"Missing sections: {', '.join(missing_sections)}")
    if missing_reagent_fields:
        notes.append(f"Reagents table missing columns: {', '.join(missing_reagent_fields)}")
    if missing_critical > 0:
        notes.append(f"{missing_critical} critical control(s) flagged as MISSING")

    return ELNGradeResult(
        score=round(total, 2),
        section_score=round(section_score, 2),
        reagents_score=round(reagents_score, 2),
        controls_score=round(controls_score, 2),
        deviations_score=round(deviations_score, 2),
        citation_score=round(citation_score, 2),
        missing_sections=missing_sections,
        missing_reagent_fields=missing_reagent_fields,
        notes=notes,
    )
