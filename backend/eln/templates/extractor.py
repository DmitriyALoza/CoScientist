"""
Template extractor: single structured LLM call to extract document structure.

Uses LangChain's with_structured_output for native JSON mode — no manual parsing.
"""

from eln.models.template import DocumentTemplate, DocumentType

_EXTRACTION_PROMPT = """\
You are a document structure analyst. Analyze the document text below and extract
its structural template as JSON — section names, field types, table schemas, required
status. Do NOT extract content — only structure.

Document type: {doc_type}

Rules:
- Identify all top-level sections and subsections
- For any table, list its column names and types
- Mark required vs optional sections
- Identify metadata fields (title, author, date, version, etc.)
- The "name" field of the DocumentTemplate should be a short descriptive label
  (e.g. "Standard ELN Template", "Manufacturer SOP Template")
- The "document_type" field must be one of: eln, sop, report, patent
- Output valid JSON matching the DocumentTemplate schema exactly

Document text (truncated to first 6000 chars for structure analysis):
{text}
"""


def extract_template(
    full_text: str,
    doc_type: DocumentType,
    llm,
    source_filename: str | None = None,
    name: str | None = None,
) -> DocumentTemplate:
    """Extract a DocumentTemplate from document full text.

    Args:
        full_text: Complete document text (non-chunked).
        doc_type: The document category to guide extraction.
        llm: A LangChain BaseChatModel with structured output support.
        source_filename: Original filename for provenance.
        name: Override the template name; if None the LLM picks one.

    Returns:
        A DocumentTemplate populated from the LLM's structured output.
    """
    prompt = _EXTRACTION_PROMPT.format(doc_type=doc_type.value, text=full_text[:6000])
    structured_llm = llm.with_structured_output(DocumentTemplate)
    result: DocumentTemplate = structured_llm.invoke(prompt)
    result.source_filename = source_filename
    if name:
        result.name = name
    return result
