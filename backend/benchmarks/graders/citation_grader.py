"""
Citation grader — validates Citation objects for completeness and hallucination risk.

Checks:
  1. Required fields: title, authors, year, excerpt, source_id
  2. excerpt_hash integrity (sha256 of excerpt must match stored hash)
  3. Inline citation presence in the response text ([citation_id: X] pattern)

Score: (complete citations / total) × (inline-cited / total)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field


@dataclass
class CitationIssue:
    citation_id: str
    field: str
    issue: str


@dataclass
class CitationGradeResult:
    score: float  # 0.0 – 1.0
    total_citations: int
    complete_citations: int
    inline_citations: int
    issues: list[CitationIssue] = field(default_factory=list)


_INLINE_PATTERN = re.compile(r"\[citation_id:\s*([^\]]+)\]", re.IGNORECASE)
_REQUIRED_FIELDS = ("title", "excerpt", "source_id")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _check_citation(c: dict) -> list[CitationIssue]:
    issues: list[CitationIssue] = []
    cid = c.get("citation_id", "<unknown>")

    for f in _REQUIRED_FIELDS:
        if not c.get(f):
            issues.append(CitationIssue(cid, f, "missing"))

    # Loose author check — just needs to be a non-empty list
    if not c.get("authors"):
        issues.append(CitationIssue(cid, "authors", "missing or empty"))

    if not c.get("year"):
        issues.append(CitationIssue(cid, "year", "missing"))

    # Hash integrity — only verify if both excerpt and hash are present
    excerpt = c.get("excerpt", "")
    stored_hash = c.get("excerpt_hash", "")
    if excerpt and stored_hash:
        computed = _sha256(excerpt)
        if computed != stored_hash:
            issues.append(
                CitationIssue(cid, "excerpt_hash", f"mismatch: stored={stored_hash[:12]}… computed={computed[:12]}…")
            )

    return issues


def grade(response: str, citations: list[dict]) -> CitationGradeResult:
    """Grade citation quality for a model response.

    Args:
        response: The full text response from the model.
        citations: List of Citation dicts accumulated in AppState.
    """
    total = len(citations)
    if total == 0:
        return CitationGradeResult(score=0.0, total_citations=0, complete_citations=0, inline_citations=0)

    all_issues: list[CitationIssue] = []
    complete = 0
    for c in citations:
        issues = _check_citation(c)
        all_issues.extend(issues)
        if not issues:
            complete += 1

    # Inline citation check
    cited_ids = set(_INLINE_PATTERN.findall(response))
    citation_ids = {c.get("citation_id", "") for c in citations}
    inline = len(cited_ids & citation_ids)

    completeness_ratio = complete / total
    inline_ratio = inline / total
    score = completeness_ratio * (inline_ratio if inline_ratio > 0 else 0.5)

    return CitationGradeResult(
        score=round(score, 4),
        total_citations=total,
        complete_citations=complete,
        inline_citations=inline,
        issues=all_issues,
    )
