"""
Text diff tool for SOP addenda.

Used by the sop_adapter subagent to show what changed between
the original SOP and the experiment-specific modifications.
"""

import difflib

from langchain_core.tools import tool


@tool
def text_diff(original: str, modified: str, context_lines: int = 3) -> str:
    """Generate a unified diff between two text blocks.

    Args:
        original: The original SOP or protocol text.
        modified: The modified / adapted text.
        context_lines: Number of context lines around changes (default 3).

    Returns:
        A unified diff string showing additions (+) and removals (-).
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile="original_sop",
        tofile="adapted_protocol",
        n=context_lines,
    )
    result = "".join(diff)
    return result if result else "No differences found."
