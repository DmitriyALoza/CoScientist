from enum import StrEnum

from pydantic import BaseModel, Field


class SourceType(StrEnum):
    PAPER = "paper"
    SOP_INTERNAL = "sop_internal"
    SOP_MANUFACTURER = "sop_manufacturer"
    REPORT = "report"
    ELN_ENTRY = "eln_entry"
    REFERENCE_DOC = "reference_doc"


class Citation(BaseModel):
    citation_id: str
    source_type: SourceType
    source_id: str  # DOI, URL, or file hash
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    excerpt: str  # short snippet (<= ~500 chars)
    location: str | None = None  # "page 3", "section 2.1", "slide 4"
    excerpt_hash: str  # sha256 of excerpt
