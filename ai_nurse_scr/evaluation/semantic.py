"""Semantic comparison helpers using LLMs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict
import csv

try:  # optional pandas for convenience
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - optional dep
    pd = None


def llm_semantic_compare(
    chunk: str,
    ans1: str,
    ans2: str,
    openai_api_key: str,
    model: str = "gpt-4.1",
) -> str:
    """Compare two answers for semantic equivalence via an LLM.

    Parameters
    ----------
    chunk : str
        Context snippet to provide to the model.
    ans1 : str
        First answer text.
    ans2 : str
        Second answer text.
    openai_api_key : str
        API key used to call OpenAI.
    model : str, optional
        Comparison model name, by default ``"gpt-4.1"``.

    Returns
    -------
    str
        Model verdict of ``"Yes"``, ``"No"`` or ``"Not Enough Info"``. If the
        API call fails the returned string begins with ``"API_ERROR:"``.
    """
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key)
    prompt = (
        "Are these two answers factually the same? Reply Yes/No/Not Enough Info.\n"
        f"Context excerpt: {chunk[:200]}...\nA1: {ans1}\nA2: {ans2}"
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=8,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:  # pragma: no cover - network failure
        print("LLM call failed:", exc)
        return f"API_ERROR: {exc}"


def _spotcheck_rows(
    rows: List[Dict[str, str]],
    context_col: str,
    ans1_col: str,
    ans2_col: str,
    out_path: Optional[Path],
    n_check: int,
    openai_api_key: str,
    model: str,
) -> Path:
    """Internal helper to run spot checks on a list of row dictionaries."""
    if n_check > len(rows):
        n_check = len(rows)

    audit_rows: List[Dict[str, str]] = []
    for idx, row in enumerate(rows[:n_check]):
        context = str(row.get(context_col, ""))[:400]
        ans1 = row.get(ans1_col, "")
        ans2 = row.get(ans2_col, "")
        verdict = llm_semantic_compare(
            context,
            ans1,
            ans2,
            openai_api_key=openai_api_key,
            model=model,
        )
        audit_rows.append(
            {
                "row_idx": idx,
                "file_name": row.get("file_name", ""),
                "chunk_id": row.get("chunk_id", ""),
                "A1": ans1,
                "A2": ans2,
                "verdict": verdict,
                "context_excerpt": context[:200],
            }
        )
        print(f"SpotCheck idx={idx}, verdict={verdict}")

    if out_path is None:
        out_path = Path("spotcheck_results.csv")

    if pd:
        pd.DataFrame(audit_rows).to_csv(out_path, index=False)
    else:
        if not audit_rows:
            headers: List[str] = []
        else:
            headers = list(audit_rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(audit_rows)

    n_disagree = sum(
        1 for r in audit_rows if str(r["verdict"]).lower().startswith("no")
    )
    if n_disagree > 0:
        print(
            f"\u26a0\ufe0f Reviewer: {n_disagree} semantic disagreements flagged (see {out_path})."
        )
    return Path(out_path)


def _read_csv(path: Path) -> List[Dict[str, str]]:
    if pd:
        return pd.read_csv(path).to_dict(orient="records")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def batch_semantic_spotcheck(
    csv_path: Path,
    context_col: str = "text",
    ans1_col: str = "llm_answer_1",
    ans2_col: str = "llm_answer_2",
    out_path: Optional[Path] = None,
    n_check: int = 10,
    openai_api_key: Optional[str] = None,
    model: str = "gpt-4.1",
) -> Path:
    """Run semantic comparison on answers stored in a CSV file."""
    rows = _read_csv(csv_path)
    return _spotcheck_rows(rows, context_col, ans1_col, ans2_col, out_path, n_check, openai_api_key, model)


def spotcheck_files(
    file1: Path,
    file2: Path,
    context_col: str = "text",
    ans_col: str = "llm_answer",
    out_path: Optional[Path] = None,
    n_check: int = 10,
    openai_api_key: Optional[str] = None,
    model: str = "gpt-4.1",
) -> Path:
    """Spot check two CSV files containing answers.

    Parameters
    ----------
    file1, file2 : Path
        CSV files with the same number/order of rows.
    context_col : str, optional
        Column containing the context snippet.
    ans_col : str, optional
        Column name of the answer in each file.
    out_path : Path, optional
        Where to write the CSV results. Defaults to ``file1`` name with
        ``_spotcheck.csv`` suffix.
    n_check : int, optional
        Number of rows to check.
    openai_api_key : str, optional
        API key for the comparison LLM.
    model : str, optional
        LLM model name.
    """
    rows1 = _read_csv(file1)
    rows2 = _read_csv(file2)
    if len(rows1) != len(rows2):
        raise ValueError("CSV files must have the same number of rows")

    merged = []
    for r1, r2 in zip(rows1, rows2):
        merged.append(
            {
                context_col: r1.get(context_col, r2.get(context_col, "")),
                "llm_answer_1": r1.get(ans_col, ""),
                "llm_answer_2": r2.get(ans_col, ""),
                "file_name": r1.get("file_name", r2.get("file_name", "")),
                "chunk_id": r1.get("chunk_id", r2.get("chunk_id", "")),
            }
        )

    if out_path is None:
        out_path = Path(file1).with_suffix("").name + "_spotcheck.csv"

    return _spotcheck_rows(
        merged,
        context_col,
        "llm_answer_1",
        "llm_answer_2",
        Path(out_path),
        n_check,
        openai_api_key,
        model,
    )

