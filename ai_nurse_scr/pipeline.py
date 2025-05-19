import json
from pathlib import Path
from . import extraction, metrics


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

    chunk_size = int(config.get("chunk_size", 200))
    all_chunks: list[list[str]] = []
    results = []
    for pdf in pdfs:
        text = extract_text(pdf)
        tokens = metrics.simple_tokenize(text)
        chunks = metrics.make_chunks(tokens, chunk_size)
        all_chunks.extend(chunks)
        data = extract_data(text)
        data["pdf_path"] = str(pdf)
        results.append(data)

    out_dir = Path(config.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{config.get('run_id', 'run')}_metadata.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    stats = metrics.chunk_statistics(all_chunks)
    metrics.write_metrics(
        config.get("run_id", "run"),
        "tokenization",
        stats,
        config.get("metrics_dir", "outputs/metrics"),
    )

    if config.get("retrieval_predictions") and config.get("retrieval_references"):
        with open(config["retrieval_predictions"], "r", encoding="utf-8") as f:
            retrieved = json.load(f)
        with open(config["retrieval_references"], "r", encoding="utf-8") as f:
            references = json.load(f)
        ret_metrics = metrics.compute_retrieval_metrics(retrieved, references)
        metrics.write_metrics(
            config.get("run_id", "run"),
            "retrieval",
            ret_metrics,
            config.get("metrics_dir", "outputs/metrics"),
        )

    if config.get("answer_predictions") and config.get("answer_references"):
        with open(config["answer_predictions"], "r", encoding="utf-8") as f:
            preds = json.load(f)
        with open(config["answer_references"], "r", encoding="utf-8") as f:
            refs = json.load(f)
        ans_metrics = metrics.compute_answer_metrics(preds, refs)
        metrics.write_metrics(
            config.get("run_id", "run"),
            "answer",
            ans_metrics,
            config.get("metrics_dir", "outputs/metrics"),
        )

    print("[INFO] Pipeline completed")
