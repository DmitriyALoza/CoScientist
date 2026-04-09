"""
Export tools: zip a run folder into a bundle.
"""

import shutil
from pathlib import Path

from langchain_core.tools import tool

from eln.tools.file_tools import get_run_path


@tool
def export_run_bundle() -> str:
    """Export the current run folder as a zip archive.

    Returns:
        Path to the created zip file.
    """
    run_path = get_run_path()
    return create_zip_bundle(run_path)


def create_zip_bundle(run_path: Path) -> str:
    """Create a zip archive of a run folder. Returns the zip file path."""
    if not run_path.exists():
        return f"Run path does not exist: {run_path}"

    # Place the zip next to the run folder
    zip_base = run_path.parent / f"{run_path.name}_bundle"
    zip_path = shutil.make_archive(
        str(zip_base), "zip",
        root_dir=str(run_path.parent),
        base_dir=run_path.name,
    )
    return zip_path
