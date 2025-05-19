from pathlib import Path

from ... import extraction


def extract_pdfmeta(pdf_path: str | Path) -> dict:
    """Extract initial metadata from the first page of a PDF.

    Parameters
    ----------
    pdf_path:
        Path to the PDF file.

    Returns
    -------
    dict
        Metadata returned by the LLM along with ``raw_first_page`` text.
    """
    pdf_path = Path(pdf_path)
    try:
        import pdfplumber
    except Exception:
        pdfplumber = None
    if pdfplumber is not None:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first = pdf.pages[0].extract_text() if pdf.pages else ""
        except Exception:
            first = ""
    else:
        first = ""
    meta = extraction.extract_ai_llm_full(first)
    meta["raw_first_page"] = first
    return meta

