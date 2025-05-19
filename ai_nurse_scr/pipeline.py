import json
from pathlib import Path
from typing import List

from . import extraction, config


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


def ask_llm(text: str, question: str, temperature: float = 0.0, model: str = "gpt-4") -> str:
    """Query an LLM with the provided question and context text.

    Parameters
    ----------
    text:
        Context text to provide the model.
    question:
        Prompt or question for the model.
    temperature:
        Sampling temperature for the LLM.
    model:
        Chat model to use.

    Returns
    -------
    str
        The model response as plain text. On error an empty string is returned.
    """
    try:  # pragma: no cover - network calls are mocked in tests
        import openai

        resp = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question + "\n" + text}],
            temperature=temperature,
            max_tokens=256,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""


def _chunk_text(text: str, size: int) -> List[str]:
    """Split text into roughly ``size`` character chunks."""
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


def run_rounds(config_path: str, pdf_dir: str) -> None:
    """Run sequential QA rounds over the provided PDFs.

    The configuration file must define a ``rounds`` section with at least a
    ``question`` value. ``round1`` and ``round2`` subsections control the number
    of chunks aggregated and sampling temperature respectively.
    """
    cfg = config.load_config(config_path)
    rounds_cfg = cfg.extra.get("rounds", {})
    question = rounds_cfg.get("question", "")
    chunk_size = int(rounds_cfg.get("chunk_size", 2000))
    r1 = rounds_cfg.get("round1", {})
    r2 = rounds_cfg.get("round2", {})

    pdfs = find_pdfs(pdf_dir)
    out_dir = Path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out1 = out_dir / f"{cfg.run_id}_round1.jsonl"
    out2 = out_dir / f"{cfg.run_id}_round2.jsonl"

    with open(out1, "w", encoding="utf-8") as f1, open(out2, "w", encoding="utf-8") as f2:
        for pdf in pdfs:
            text = extract_text(pdf)
            chunks = _chunk_text(text, chunk_size)

            # round 1 - aggregate larger context
            top_n = int(r1.get("top_n", len(chunks)))
            ctx = " ".join(chunks[:top_n])
            ans1 = ask_llm(ctx, question, float(r1.get("temperature", 0.0)))
            f1.write(json.dumps({"pdf_path": str(pdf), "answer": ans1}) + "\n")

            # round 2 - individual chunks
            temp2 = float(r2.get("temperature", 0.0))
            for idx, chunk in enumerate(chunks):
                ans2 = ask_llm(chunk, question, temp2)
                rec = {"pdf_path": str(pdf), "chunk_index": idx, "answer": ans2}
                f2.write(json.dumps(rec) + "\n")

    print("[INFO] QA rounds completed")
