from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from eln.models.citation import Citation
from eln.models.run_manifest import RunManifest

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class ELNRenderer:
    """Renders a RunManifest + citations to a structured ELN.md via Jinja2."""

    def __init__(self, templates_dir: Path = _TEMPLATES_DIR):
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(disabled_extensions=("md",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, manifest: RunManifest, citations: list[Citation] | None = None) -> str:
        template = self._env.get_template("eln.md.j2")
        return template.render(
            manifest=manifest,
            citations=citations or [],
            citation_map={c.citation_id: c for c in (citations or [])},
        )

    def render_to_file(
        self,
        manifest: RunManifest,
        output_path: Path,
        citations: list[Citation] | None = None,
    ) -> Path:
        content = self.render(manifest, citations)
        output_path.write_text(content, encoding="utf-8")
        return output_path
