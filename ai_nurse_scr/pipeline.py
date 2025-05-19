import json
from pathlib import Path
from . import extraction


def load_config(path: str) -> dict:
    """Load a pipeline configuration file.

    Parameters
    ----------
    path:
        Path to a JSON file containing configuration options.

    Returns
    -------
    dict
        Dictionary with the parsed configuration values.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_pdfs(directory: str):
    """Return a list of PDFs under ``directory``.

    Parameters
    ----------
    directory:
        Directory to search for ``.pdf`` files.

    Returns
    -------
    list[Path]
        Sorted list of PDF paths found.
    """
    return sorted(Path(directory).glob("*.pdf"))


def extract_text(pdf_path: Path) -> str:
    """Extract raw text from a PDF file.

    Parameters
    ----------
    pdf_path:
        Path to the PDF document.

    Returns
    -------
    str
        Concatenated text of all pages or an empty string on error.
    """
    try:
        import pdfplumber
    except Exception:
        return ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return ""


def extract_data(text: str) -> dict:
    """Extract structured metadata from paper text.

    Parameters
    ----------
    text:
        Plain text extracted from the PDF.

    Returns
    -------
    dict
        Metadata dictionary containing keys from ``extraction.fields``.
    """
    first_chunk = text[:4000]
    meta = extraction.extract_ai_llm_full(first_chunk)
    doi = meta.get("doi", "")
    if doi:
        cr = extraction.extract_crossref_full(doi, meta.get("title"))
        meta.update({k: v for k, v in cr.items() if v})
        oa = extraction.extract_openalex_full(doi, meta.get("title"))
        meta.update({k: v for k, v in oa.items() if v})
    return meta


def run(config_path: str, pdf_dir: str) -> None:
    """Execute the CLI pipeline.

    Parameters
    ----------
    config_path:
        Path to a JSON configuration file.
    pdf_dir:
        Directory containing PDF files to process.

    Returns
    -------
    None
    """
    config = load_config(config_path)
    print(f"[INFO] Loaded config from {config_path}")

    pdfs = find_pdfs(pdf_dir)
    if not pdfs:
        print(f"[WARNING] No PDF files found in {pdf_dir}")

    results = []
    for pdf in pdfs:
        text = extract_text(pdf)
        data = extract_data(text)
        data["pdf_path"] = str(pdf)
        results.append(data)

    out_dir = Path(config.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{config.get('run_id', 'run')}_metadata.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("[INFO] Pipeline completed")
