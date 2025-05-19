from pathlib import Path

from .utils import sha256_file, normalize_doi
from .extract.grobid import extract_grobid
from .extract.pdfmeta import extract_pdfmeta
from .extract.crossref import extract_crossref
from .extract.openalex import extract_openalex
from .extract.llm import extract_llm


def run_pipeline(pdf_path: str | Path) -> dict:
    """Run the full extraction pipeline on a PDF."""
    pdf_path = Path(pdf_path)
    result = {
        "sha256": sha256_file(pdf_path),
    }
    result.update(extract_pdfmeta(pdf_path))
    if "doi" in result:
        result["doi"] = normalize_doi(result["doi"])
        result.update(extract_crossref(result["doi"]))
        result.update(extract_openalex(result["doi"]))
    result.update(extract_grobid(pdf_path))
    result.update(extract_llm(result))
    return result
