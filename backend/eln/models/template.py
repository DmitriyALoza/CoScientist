"""
Pydantic models for the document template system.

Templates capture the structural schema of uploaded documents so that
output rendering can conform to the company's exact format.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    ELN = "eln"
    SOP = "sop"
    REPORT = "report"
    PATENT = "patent"


class FieldType(StrEnum):
    TEXT = "text"
    TABLE = "table"
    LIST = "list"
    DATE = "date"
    NUMBER = "number"
    BOOLEAN = "boolean"


class TableColumn(BaseModel):
    name: str
    field_type: FieldType = FieldType.TEXT
    required: bool = False
    description: str | None = None


class TemplateSection(BaseModel):
    name: str
    field_type: FieldType = FieldType.TEXT
    required: bool = True
    description: str | None = None
    columns: list[TableColumn] = []       # populated when field_type == TABLE
    subsections: list["TemplateSection"] = []


class DocumentTemplate(BaseModel):
    template_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    document_type: DocumentType
    description: str | None = None
    source_filename: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sections: list[TemplateSection]
    metadata_fields: list[str] = []      # e.g. ["title", "author", "version", "date"]
