"""
TemplateStore: filesystem-based persistence for DocumentTemplate objects.

Layout:
  <templates_root>/<doc_type>/<template_id>.json
"""

import json
from pathlib import Path

from eln.models.template import DocumentTemplate, DocumentType


class TemplateStore:
    def __init__(self, templates_root: Path) -> None:
        self.root = templates_root
        # Ensure all doc-type subdirs exist
        for doc_type in DocumentType:
            (self.root / doc_type.value).mkdir(parents=True, exist_ok=True)

    def save(self, template: DocumentTemplate) -> Path:
        """Persist a template to disk. Returns the path written."""
        dest = self.root / template.document_type.value / f"{template.template_id}.json"
        dest.write_text(template.model_dump_json(indent=2))
        return dest

    def load(self, doc_type: DocumentType, template_id: str) -> DocumentTemplate:
        path = self.root / doc_type.value / f"{template_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {template_id}")
        return DocumentTemplate.model_validate_json(path.read_text())

    def list(self, doc_type: DocumentType | None = None) -> list[DocumentTemplate]:
        """Return all templates, optionally filtered by document type."""
        templates: list[DocumentTemplate] = []
        types = [doc_type] if doc_type else list(DocumentType)
        for dt in types:
            subdir = self.root / dt.value
            if not subdir.exists():
                continue
            for path in sorted(subdir.glob("*.json")):
                try:
                    templates.append(DocumentTemplate.model_validate_json(path.read_text()))
                except Exception:
                    pass  # Skip corrupt files silently
        return templates

    def delete(self, doc_type: DocumentType, template_id: str) -> None:
        path = self.root / doc_type.value / f"{template_id}.json"
        path.unlink(missing_ok=True)
