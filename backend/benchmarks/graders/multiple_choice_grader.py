"""
Multiple-choice grader for LAB-Bench and BioProBench MCQ items.

Extracts the answer letter from a free-text response and compares it
against the gold answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class MCQResult:
    correct: bool
    extracted_answer: str | None
    gold_answer: str
    raw_response: str


# Patterns to extract a letter answer from free text, in order of preference:
# 1. Explicit format: "Answer: B" / "The answer is (C)"
# 2. Standalone letter on its own line
# 3. Last single capital letter A-D anywhere in the text
_EXPLICIT = re.compile(
    r"""
    (?:answer\s*(?:is|:)?\s*)   # "Answer is", "Answer:", etc.
    \(?                          # optional open paren
    ([A-Da-d])                   # the letter
    \)?                          # optional close paren
    """,
    re.IGNORECASE | re.VERBOSE,
)
_STANDALONE = re.compile(r"^\s*\(?([A-Da-d])\)?\s*$", re.MULTILINE)
_FALLBACK = re.compile(r"\b([A-Da-d])\b")


def _extract_letter(text: str) -> str | None:
    m = _EXPLICIT.search(text)
    if m:
        return m.group(1).upper()
    m = _STANDALONE.search(text)
    if m:
        return m.group(1).upper()
    matches = _FALLBACK.findall(text)
    if matches:
        return matches[-1].upper()
    return None


def grade(response: str, gold_answer: str) -> MCQResult:
    """Grade a free-text response against a gold answer.

    Args:
        response: Model's free-text response.
        gold_answer: Correct answer (single letter A-D, or the full text of
                     the correct choice).  If full text, we normalise both
                     the extracted letter and the gold text label.
    """
    gold_norm = gold_answer.strip().upper()

    # If gold is a full-text choice label (not a single letter), try to match
    # the first letter only.
    if len(gold_norm) > 1:
        gold_letter = gold_norm[0] if gold_norm[0] in "ABCD" else None
    else:
        gold_letter = gold_norm if gold_norm in "ABCD" else None

    extracted = _extract_letter(response)

    if gold_letter and extracted:
        correct = extracted == gold_letter
    else:
        # Fall back to substring match if we couldn't extract a letter
        correct = gold_norm in response.upper()

    return MCQResult(
        correct=correct,
        extracted_answer=extracted,
        gold_answer=gold_answer,
        raw_response=response[:500],
    )


def score_batch(results: list[MCQResult]) -> dict:
    """Aggregate accuracy over a list of MCQ results."""
    total = len(results)
    if total == 0:
        return {"accuracy": 0.0, "correct": 0, "total": 0}
    correct = sum(1 for r in results if r.correct)
    return {
        "accuracy": correct / total,
        "correct": correct,
        "total": total,
    }
