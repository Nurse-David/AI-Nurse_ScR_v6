import json
from pathlib import Path
import tempfile
from . import extraction


def load_config(path: str) -> dict:
    """Load JSON configuration from path."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_pdfs(directory: str):
    """Yield PDF files within the directory."""
    return sorted(Path(directory).glob('*.pdf'))


def extract_text(pdf_path: Path) -> str:
    """Return all text from a PDF using ``pdfplumber``."""
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
    """Extract structured metadata from paper text."""
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
    """Run the pipeline sequentially using the given configuration and PDF directory."""
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


def run_multiple(config_path: str, pdf_dir: str, rounds: int) -> list[Path]:
    """Run the pipeline multiple times returning output file paths."""
    base_cfg = load_config(config_path)
    outputs: list[Path] = []
    for i in range(1, rounds + 1):
        run_id = f"{base_cfg.get('run_id', 'run')}_round{i}"
        cfg = {
            "pdf_dir": base_cfg.get("pdf_dir"),
            "run_id": run_id,
            **{k: v for k, v in base_cfg.items() if k not in {"pdf_dir", "run_id"}},
        }
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            json.dump(cfg, tmp)
            tmp.flush()
            run(tmp.name, pdf_dir)
        out_dir = Path(cfg.get("output_dir", "output"))
        outputs.append(out_dir / f"{run_id}_metadata.jsonl")
    return outputs
