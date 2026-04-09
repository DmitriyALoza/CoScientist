"""
Controls grader — precision/recall of controls checklist against a gold standard.

Gold standard is loaded from benchmarks/datasets/internal/controls/*.json.
Each gold file has:
  {
    "id": "ctrl_001",
    "domain": "flow_cytometry",
    "required_controls": ["Unstained", "Isotype", ...],
    "optional_controls": ["FMO", ...]
  }
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ControlsGradeResult:
    precision: float    # fraction of controls mentioned that are legitimate
    recall: float       # fraction of gold required controls that are present
    f1: float
    required_found: list[str] = field(default_factory=list)
    required_missing: list[str] = field(default_factory=list)
    spurious: list[str] = field(default_factory=list)


def _normalise(name: str) -> str:
    """Lowercase and strip punctuation for fuzzy matching."""
    return re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()


def _is_present(control_name: str, response: str) -> bool:
    norm = _normalise(control_name)
    # Accept if any 3+ consecutive words from the norm appear in the response
    words = norm.split()
    if len(words) <= 2:
        return norm in _normalise(response)
    # sliding window of 2 words
    response_norm = _normalise(response)
    for i in range(len(words) - 1):
        phrase = " ".join(words[i : i + 2])
        if phrase in response_norm:
            return True
    return False


def grade(response: str, gold: dict) -> ControlsGradeResult:
    """Grade a controls checklist response against a gold standard dict.

    Args:
        response: Model's free-text checklist response.
        gold: Gold dict with keys 'required_controls' and 'optional_controls'.
    """
    required: list[str] = gold.get("required_controls", [])
    optional: list[str] = gold.get("optional_controls", [])
    all_legitimate = set(_normalise(c) for c in required + optional)

    # Recall: which required controls are mentioned?
    found = [c for c in required if _is_present(c, response)]
    missing = [c for c in required if not _is_present(c, response)]
    recall = len(found) / len(required) if required else 1.0

    # Precision: extract checklist items from the response and check legitimacy
    # Heuristic: lines that start with "- [ ]", "- [x]", "* ", or numbered list
    item_pattern = re.compile(r"^[-*]\s*(?:\[.?\]\s+)?(.+)$", re.MULTILINE)
    response_items = [m.group(1).strip() for m in item_pattern.finditer(response)]

    spurious: list[str] = []
    legitimate_count = 0
    for item in response_items:
        item_norm = _normalise(item)
        if any(item_norm in leg or leg in item_norm for leg in all_legitimate):
            legitimate_count += 1
        else:
            spurious.append(item)

    precision = legitimate_count / len(response_items) if response_items else (1.0 if not required else 0.0)

    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return ControlsGradeResult(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        required_found=found,
        required_missing=missing,
        spurious=spurious[:10],  # cap for readability
    )


def load_gold(gold_path: Path) -> dict:
    with open(gold_path) as f:
        return json.load(f)
