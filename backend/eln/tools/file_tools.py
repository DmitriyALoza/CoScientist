"""
File-related tools exposed to subagents.

Primarily used by eln_scribe to write the final ELN.md to the run folder.
"""

import hashlib
from pathlib import Path

from langchain_core.tools import tool

# Module-level run path — set by the supervisor builder before graph invocation
_run_path: Path | None = None


def set_run_path(path: Path) -> None:
    global _run_path
    _run_path = path


def get_run_path() -> Path:
    if _run_path is None:
        raise RuntimeError("Run path not set. Call set_run_path() first.")
    return _run_path


@tool
def write_eln(content: str) -> str:
    """Write ELN.md content to the current run folder.

    Args:
        content: The complete Markdown content for the ELN entry.

    Returns:
        Confirmation message with the file path.
    """
    run_path = get_run_path()
    eln_path = run_path / "ELN.md"
    eln_path.write_text(content, encoding="utf-8")
    return f"ELN.md written to {eln_path}"


@tool
def write_report(content: str, filename: str = "troubleshooting_report.md") -> str:
    """Write a report (e.g., troubleshooting) to the run's reports folder.

    Args:
        content: The Markdown content for the report.
        filename: Filename (default: troubleshooting_report.md).

    Returns:
        Confirmation message with the file path.
    """
    run_path = get_run_path()
    report_path = run_path / "reports" / filename
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")
    return f"Report written to {report_path}"


@tool
def read_artifact(filename: str) -> str:
    """Read a text artifact from the current run's artifacts folder.

    Args:
        filename: Name of the file in the artifacts/ folder.

    Returns:
        The file contents (first 5000 chars).
    """
    run_path = get_run_path()
    artifact_path = run_path / "artifacts" / filename
    if not artifact_path.exists():
        return f"Artifact not found: {filename}"
    text = artifact_path.read_text(encoding="utf-8", errors="replace")
    if len(text) > 5000:
        return text[:5000] + f"\n\n... [truncated, {len(text)} total chars]"
    return text


@tool
def save_csv_artifact(csv_content: str, filename: str) -> str:
    """Save CSV text as a run artifact (for chart data extracted by image_analyst).

    Args:
        csv_content: The CSV text content to save.
        filename: Filename for the artifact (e.g., 'chart_data.csv').

    Returns:
        Confirmation with artifact path, or error message.
    """
    run_path = get_run_path()
    artifacts_dir = run_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifacts_dir / filename
    artifact_path.write_text(csv_content, encoding="utf-8")
    return f"CSV artifact saved: {artifact_path}"


@tool
def save_plot_artifact(filename: str) -> str:
    """Save the current matplotlib figure as a PNG artifact.

    Call this after generating a plot with matplotlib. The current figure
    (plt.gcf()) will be saved to artifacts/{filename}.

    Args:
        filename: Filename for the plot artifact (e.g., 'comparison_plot.png').

    Returns:
        Confirmation with artifact path, or error message.
    """
    run_path = get_run_path()
    artifacts_dir = run_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifacts_dir / filename
    try:
        import matplotlib.pyplot as plt

        plt.savefig(str(artifact_path), bbox_inches="tight", dpi=150)
        plt.close()
        return f"Plot saved: {artifact_path}"
    except Exception as e:
        return f"Error saving plot: {e}"


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
