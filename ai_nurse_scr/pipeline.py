from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
import tempfile
try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None

from dataclasses import asdict
from typing import List, Callable, Dict

from . import extraction, config, metrics, __version__, __git_hash__
from . import paths


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def load_config(path: str) -> config.Config:
    """Load configuration using :func:`ai_nurse_scr.config.load_config`."""
    return config.load_config(path)


def find_pdfs(directory: str):
    """Yield PDF files within the directory."""
    return sorted(Path(directory).glob("*.pdf"))


def extract_text(pdf_path: Path) -> str:
    """Return all text from a PDF using ``pdfplumber``."""
    try:  # pragma: no cover - optional dependency
        import pdfplumber
    except Exception:  # pragma: no cover - pdfplumber missing
        return ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return ""


def extract_data(text: str, model: str = "gpt-4") -> dict:
    """Extract structured metadata from paper text."""
    first_chunk = text[:4000]
    meta = extraction.extract_ai_llm_full(first_chunk, model=model)
    doi = meta.get("doi", "")
    if doi:
        cr = extraction.extract_crossref_full(doi, meta.get("title"))
        meta.update({k: v for k, v in cr.items() if v})
        oa = extraction.extract_openalex_full(doi, meta.get("title"))
        meta.update({k: v for k, v in oa.items() if v})
    return meta



def run(config_path: str, pdf_dir: str, force: bool = False) -> Path | None:
    """Run the pipeline sequentially using the given configuration and PDF directory."""
    cfg = config.load_config(config_path)
    print(f"[INFO] Loaded config from {config_path}")

    paths.set_project_root(Path(cfg.project_root) if cfg.project_root else paths.default_project_root())
    out_dir = paths.get_path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    existing = list(out_dir.glob(f"{cfg.run_id}_metadata_*.jsonl"))
    if existing and not force:
        print("⏩ Skipping metadata (outputs present)")
        return existing[0]

    pdfs = find_pdfs(pdf_dir)
    if not pdfs:
        print(f"[WARNING] No PDF files found in {pdf_dir}")


# ---------------------------------------------------------------------------
# Pipeline stage implementations
# ---------------------------------------------------------------------------

# def run_metadata(config_path: str, pdf_dir: str) -> Path:
#     """Extract metadata from PDFs and write ``*_metadata.jsonl`` output."""
#    cfg = load_config(config_path)
#    pdfs = find_pdfs(pdf_dir)

    chunk_size = int(cfg.extra.get("chunk_size", 200))

    all_chunks: list[list[str]] = []
    results = []
    for pdf in pdfs:
        text = extract_text(pdf)
        tokens = metrics.simple_tokenize(text)
        chunks = metrics.make_chunks(tokens, chunk_size)
        all_chunks.extend(chunks)
        data = extract_data(text, model=cfg.llm_model)
        data["pdf_path"] = str(pdf)
        results.append(data)


#    snapshot = asdict(cfg)


    out_dir = Path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    snapshot = {"config": asdict(cfg), "version": __version__}

    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            text=True,
        ).strip()
    except Exception:  # pragma: no cover - git not available
        commit = "unknown"
    snapshot["commit"] = commit

    snapshot_file = out_dir / "config_snapshot.yaml"
    with open(snapshot_file, "w", encoding="utf-8") as f:
        if yaml:
            yaml.safe_dump(snapshot, f, sort_keys=False)
        else:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    run_info = {
        "run_id": cfg.run_id,
        "pipeline_version": __version__,
        "git_hash": __git_hash__,
        "timestamp": time.strftime("%Y%m%d_%H%M"),
    }
    with open(out_dir / "run_info.yaml", "w", encoding="utf-8") as f:
        if yaml:
            yaml.safe_dump(run_info, f, sort_keys=False)
        else:
            json.dump(run_info, f, ensure_ascii=False, indent=2)

        
    out_file = out_dir / paths.timestamped_filename(f"{cfg.run_id}_metadata")

    

 #   with open(out_dir / "config_snapshot.json", "w", encoding="utf-8") as f:
 #       json.dump(snapshot, f, ensure_ascii=False, indent=2)

 #   out_file = out_dir / f"{cfg.run_id}_metadata.jsonl"

    with open(out_file, "w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    stats = metrics.chunk_statistics(all_chunks)
    metrics.write_metrics(
        cfg.run_id,
        "tokenization",
        stats,
        cfg.extra.get("metrics_dir", "outputs/metrics"),
    )

    if cfg.extra.get("retrieval_predictions") and cfg.extra.get("retrieval_references"):
        with open(cfg.extra["retrieval_predictions"], "r", encoding="utf-8") as f:
            retrieved = json.load(f)
        with open(cfg.extra["retrieval_references"], "r", encoding="utf-8") as f:
            references = json.load(f)
        ret_metrics = metrics.compute_retrieval_metrics(retrieved, references)
        metrics.write_metrics(
            cfg.run_id,
            "retrieval",
            ret_metrics,
            cfg.extra.get("metrics_dir", "outputs/metrics"),
        )

    if cfg.extra.get("answer_predictions") and cfg.extra.get("answer_references"):
        with open(cfg.extra["answer_predictions"], "r", encoding="utf-8") as f:
            preds = json.load(f)
        with open(cfg.extra["answer_references"], "r", encoding="utf-8") as f:
            refs = json.load(f)
        ans_metrics = metrics.compute_answer_metrics(preds, refs)
        metrics.write_metrics(
            cfg.run_id,
            "answer",
            ans_metrics,
            cfg.extra.get("metrics_dir", "outputs/metrics"),
        )


    print("✔ Stage metadata completed")
    return out_file


def run_chunking(config_path: str, pdf_dir: str) -> Path:
    """Chunk PDF texts and write ``*_chunks.jsonl`` output."""
    cfg = load_config(config_path)
    pdfs = find_pdfs(pdf_dir)
    chunk_size = int(cfg.extra.get("chunk_size", 200))
    out_dir = Path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{cfg.run_id}_chunks.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for pdf in pdfs:
            text = extract_text(pdf)
            tokens = metrics.simple_tokenize(text)
            for idx, chunk in enumerate(metrics.make_chunks(tokens, chunk_size)):
                rec = {"pdf_path": str(pdf), "chunk_index": idx, "tokens": chunk}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print("✔ Stage chunking completed")
    return out_file


def ask_llm(text: str, question: str, temperature: float = 0.0, model: str = "gpt-4") -> str:
    """Query an LLM with the provided question and context text."""
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



def run_rounds(config_path: str, pdf_dir: str, force: bool = False) -> tuple[Path, Path] | None:
    """Run sequential QA rounds over the provided PDFs.

    The configuration file must define a ``rounds`` section with at least a
    ``question`` value. ``round1`` and ``round2`` subsections control the number
    of chunks aggregated and sampling temperature respectively.
    """
    cfg = config.load_config(config_path)

# def run_round1(config_path: str, pdf_dir: str) -> Path:
#    """Run QA round 1 over the PDFs."""
#    cfg = load_config(config_path)

    rounds_cfg = cfg.extra.get("rounds", {})
    question = rounds_cfg.get("question", "")
    chunk_size = int(rounds_cfg.get("chunk_size", 2000))
    r1 = rounds_cfg.get("round1", {})

    model = cfg.llm_model
    paths.set_project_root(Path(cfg.project_root) if cfg.project_root else paths.default_project_root())
    pdfs = find_pdfs(pdf_dir)
    out_dir = paths.get_path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    exist1 = list(out_dir.glob(f"{cfg.run_id}_round1_*.jsonl"))
    exist2 = list(out_dir.glob(f"{cfg.run_id}_round2_*.jsonl"))
    if exist1 and exist2 and not force:
        print("⏩ Skipping QA rounds (outputs present)")
        return exist1[0], exist2[0]
    out1 = out_dir / paths.timestamped_filename(f"{cfg.run_id}_round1")
    out2 = out_dir / paths.timestamped_filename(f"{cfg.run_id}_round2")


    with open(out_file, "w", encoding="utf-8") as f1:
        for pdf in pdfs:
            text = extract_text(pdf)
            chunks = _chunk_text(text, chunk_size)
            top_n = int(r1.get("top_n", len(chunks)))
            ctx = " ".join(chunks[:top_n])
            ans1 = ask_llm(ctx, question, float(r1.get("temperature", 0.0)), model=model)
            f1.write(json.dumps({"pdf_path": str(pdf), "answer": ans1}) + "\n")

    print("✔ Stage round1 completed")
    return out_file


def run_round2(config_path: str, pdf_dir: str) -> Path:
    """Run QA round 2 on individual chunks."""
    cfg = load_config(config_path)
    rounds_cfg = cfg.extra.get("rounds", {})
    question = rounds_cfg.get("question", "")
    chunk_size = int(rounds_cfg.get("chunk_size", 2000))
    r2 = rounds_cfg.get("round2", {})

    model = cfg.llm_model
    pdfs = find_pdfs(pdf_dir)
    out_dir = Path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{cfg.run_id}_round2.jsonl"

    with open(out_file, "w", encoding="utf-8") as f2:
        for pdf in pdfs:
            text = extract_text(pdf)
            chunks = _chunk_text(text, chunk_size)
            temp2 = float(r2.get("temperature", 0.0))
            for idx, chunk in enumerate(chunks):
                ans2 = ask_llm(chunk, question, temp2, model=model)
                rec = {"pdf_path": str(pdf), "chunk_index": idx, "answer": ans2}
                f2.write(json.dumps(rec) + "\n")

    print("✔ Stage round2 completed")
    return out_file


def run_round3(config_path: str, pdf_dir: str) -> Path:
    """Placeholder for QA round 3 synthesis."""
    cfg = load_config(config_path)
    out_dir = Path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{cfg.run_id}_round3.jsonl"
    out_file.write_text("")
    print("✔ Stage round3 completed")
    return out_file


def run_synthesis(config_path: str, pdf_dir: str) -> Path:
    """Placeholder for final synthesis stage."""
    cfg = load_config(config_path)
    out_dir = Path(cfg.extra.get("output_dir", "output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{cfg.run_id}_synthesis.jsonl"
    out_file.write_text("")
    print("✔ Stage synthesis completed")
    return out_file


# ---------------------------------------------------------------------------
# Orchestration helpers
# ---------------------------------------------------------------------------

STAGES: Dict[str, Callable[[str, str], Path]] = {
    "metadata": run_metadata,
    "chunking": run_chunking,
    "round1": run_round1,
    "round2": run_round2,
    "round3": run_round3,
    "synthesis": run_synthesis,
}


def run(
    config_path: str,
    pdf_dir: str,
    *,
    start: str = "metadata",
    stop: str = "synthesis",
    force: bool = False,
) -> None:
    """Run pipeline stages from ``start`` to ``stop`` inclusive."""

    stage_names = list(STAGES.keys())
    if start not in STAGES or stop not in STAGES:
        raise ValueError("Unknown stage name")
    start_idx = stage_names.index(start)
    stop_idx = stage_names.index(stop)
    if start_idx > stop_idx:
        raise ValueError("start must be before stop")

    for name in stage_names[start_idx : stop_idx + 1]:
        STAGES[name](config_path, pdf_dir)

    print("[INFO] Pipeline completed")


def run_multiple(config_path: str, pdf_dir: str, rounds: int) -> list[Path]:
    """Run the pipeline multiple times returning output file paths."""
    base_cfg = load_config(config_path)
    outputs: list[Path] = []
    for i in range(1, rounds + 1):
        run_id = f"{base_cfg.run_id}_round{i}"
        cfg = {
            "pdf_dir": base_cfg.pdf_dir,
            "run_id": run_id,
            **base_cfg.extra,
        }
        with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as tmp:
            json.dump(cfg, tmp)
            tmp.flush()
            run(tmp.name, pdf_dir)
        out_dir = Path(cfg.get("output_dir", "output"))
        outputs.append(out_dir / f"{run_id}_metadata.jsonl")
    return outputs


def run_rounds(config_path: str, pdf_dir: str) -> None:
    """Compat wrapper that executes round 1 and round 2."""
    run_round1(config_path, pdf_dir)
    run_round2(config_path, pdf_dir)
    print("[INFO] QA rounds completed")
    return out1, out2
