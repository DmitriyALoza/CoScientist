"""
External literature search tools: PubMed (NCBI E-utilities) and Semantic Scholar.

These are @tool-decorated functions injected into the literature_scout subagent.
They perform live HTTP searches and return formatted results.
"""

import hashlib
import xml.etree.ElementTree as ET

import httpx
from langchain_core.tools import tool

from eln.config import settings

_PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

_TIMEOUT = 15.0


@tool
def search_pubmed(query: str, max_results: int = 5) -> str:
    """Search PubMed for biomedical papers matching a query.

    Args:
        query: Scientific search query (e.g., "CD3 T-cell activation flow cytometry").
        max_results: Maximum number of results (default 5, max 10).

    Returns:
        Formatted list of papers with titles, authors, year, PMID, and abstracts.
    """
    max_results = min(max_results, 10)

    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json",
        "sort": "relevance",
    }
    if settings.ncbi_email:
        params["email"] = settings.ncbi_email

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            # Step 1: search for PMIDs
            resp = client.get(_PUBMED_SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            id_list = data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return f"No PubMed results found for: {query}"

            # Step 2: fetch summaries
            fetch_resp = client.get(
                _PUBMED_FETCH_URL,
                params={
                    "db": "pubmed",
                    "id": ",".join(id_list),
                    "rettype": "abstract",
                    "retmode": "xml",
                },
            )
            fetch_resp.raise_for_status()

            return _parse_pubmed_xml(fetch_resp.text)

    except httpx.HTTPError as e:
        return f"PubMed search error: {e}"


def _parse_pubmed_xml(xml_text: str) -> str:
    """Parse PubMed efetch XML into formatted results."""
    root = ET.fromstring(xml_text)
    results = []

    for article in root.findall(".//PubmedArticle"):
        medline = article.find(".//MedlineCitation")
        if medline is None:
            continue

        pmid_el = medline.find("PMID")
        pmid = pmid_el.text if pmid_el is not None else "N/A"

        art = medline.find(".//Article")
        if art is None:
            continue

        title_el = art.find("ArticleTitle")
        title = title_el.text if title_el is not None else "Untitled"

        # Authors
        authors = []
        for author in art.findall(".//Author"):
            last = author.find("LastName")
            initials = author.find("Initials")
            if last is not None:
                name = last.text
                if initials is not None:
                    name += f" {initials.text}"
                authors.append(name)

        # Year
        year = "N/A"
        pub_date = art.find(".//PubDate")
        if pub_date is not None:
            y_el = pub_date.find("Year")
            if y_el is not None:
                year = y_el.text

        # Abstract
        abstract_parts = []
        for abs_text in art.findall(".//AbstractText"):
            label = abs_text.get("Label", "")
            text = abs_text.text or ""
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts)[:400] if abstract_parts else "No abstract available."

        citation_id = hashlib.sha256(f"pmid:{pmid}".encode()).hexdigest()[:12]
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."

        results.append(
            f"[{citation_id}] PMID:{pmid}\n"
            f"  Title: {title}\n"
            f"  Authors: {author_str}\n"
            f"  Year: {year}\n"
            f"  Abstract: {abstract}...\n"
        )

    return "\n".join(results) if results else "No results parsed from PubMed."


@tool
def search_semantic_scholar(query: str, max_results: int = 5) -> str:
    """Search Semantic Scholar for academic papers matching a query.

    Args:
        query: Scientific search query.
        max_results: Maximum number of results (default 5, max 10).

    Returns:
        Formatted list of papers with titles, authors, year, DOI, and abstracts.
    """
    max_results = min(max_results, 10)

    params = {
        "query": query,
        "limit": str(max_results),
        "fields": "title,authors,year,abstract,externalIds,citationCount",
    }
    headers = {}
    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key

    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.get(_S2_SEARCH_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        papers = data.get("data", [])
        if not papers:
            return f"No Semantic Scholar results found for: {query}"

        results = []
        for paper in papers:
            title = paper.get("title", "Untitled")
            year = paper.get("year", "N/A")
            citations = paper.get("citationCount", 0)
            abstract = (paper.get("abstract") or "No abstract.")[:400]

            authors = [a.get("name", "") for a in paper.get("authors", [])[:3]]
            author_str = ", ".join(authors)
            if len(paper.get("authors", [])) > 3:
                author_str += " et al."

            ext_ids = paper.get("externalIds", {})
            doi = ext_ids.get("DOI", "")
            s2_id = paper.get("paperId", "")
            source_id = doi or s2_id

            citation_id = hashlib.sha256(f"s2:{source_id}".encode()).hexdigest()[:12]

            results.append(
                f"[{citation_id}] {f'DOI:{doi}' if doi else f'S2:{s2_id}'}\n"
                f"  Title: {title}\n"
                f"  Authors: {author_str}\n"
                f"  Year: {year} (cited {citations}x)\n"
                f"  Abstract: {abstract}...\n"
            )

        return "\n".join(results)

    except httpx.HTTPError as e:
        return f"Semantic Scholar search error: {e}"
