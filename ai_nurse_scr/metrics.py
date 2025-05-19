"""Utility functions for computing pipeline metrics."""

from __future__ import annotations

from typing import Iterable, Tuple, List, Dict, Sequence
from pathlib import Path
import json, csv

def _confusion(true: Iterable[bool], pred: Iterable[bool]) -> Tuple[int, int, int, int]:
    """Return (tp, tn, fp, fn) counts for boolean lists."""
    tp = tn = fp = fn = 0
    for t, p in zip(true, pred):
        if t and p:
            tp += 1
        elif not t and not p:
            tn += 1
        elif not t and p:
            fp += 1
        else:
            fn += 1
    return tp, tn, fp, fn


def precision(tp: int, fp: int) -> float:
    return tp / (tp + fp) if tp + fp else 0.0


def recall(tp: int, fn: int) -> float:
    return tp / (tp + fn) if tp + fn else 0.0


def f1_score(tp: int, fp: int, fn: int) -> float:
    p = precision(tp, fp)
    r = recall(tp, fn)
    return 2 * p * r / (p + r) if p + r else 0.0


def accuracy(tp: int, tn: int, fp: int, fn: int) -> float:
    total = tp + tn + fp + fn
    return (tp + tn) / total if total else 0.0


def classification_metrics(true: Iterable[bool], pred: Iterable[bool]) -> Dict[str, float]:
    """Compute precision, recall, f1, and accuracy for boolean predictions."""
    tp, tn, fp, fn = _confusion(list(true), list(pred))
    return {
        "precision": precision(tp, fp),
        "recall": recall(tp, fn),
        "f1": f1_score(tp, fp, fn),
        "accuracy": accuracy(tp, tn, fp, fn),
    }

def simple_tokenize(text: str) -> list[str]:
    """Tokenize text using whitespace splitting."""
    return text.split()


def make_chunks(tokens: Sequence[str], chunk_size: int = 200) -> list[list[str]]:
    """Split token sequence into chunks of ``chunk_size`` tokens."""
    return [list(tokens[i : i + chunk_size]) for i in range(0, len(tokens), chunk_size)]


def chunk_statistics(chunks: Sequence[Sequence[str]]) -> dict:
    """Return basic statistics for a list of token chunks."""
    counts = [len(c) for c in chunks]
    if not counts:
        return {"num_chunks": 0, "avg_tokens": 0.0, "min_tokens": 0, "max_tokens": 0}
    return {
        "num_chunks": len(counts),
        "avg_tokens": sum(counts) / len(counts),
        "min_tokens": min(counts),
        "max_tokens": max(counts),
    }


def compute_retrieval_metrics(
    retrieved: Sequence[Sequence[str]], references: Sequence[Sequence[str]]
) -> dict:
    """Compute precision, recall and MRR over multiple queries."""
    precisions: list[float] = []
    recalls: list[float] = []
    rrs: list[float] = []
    for ret, ref in zip(retrieved, references):
        ref_set = set(ref)
        tp = sum(1 for doc in ret if doc in ref_set)
        precisions.append(tp / len(ret) if ret else 0.0)
        recalls.append(tp / len(ref_set) if ref_set else 0.0)
        rr = 0.0
        for rank, doc in enumerate(ret, 1):
            if doc in ref_set:
                rr = 1.0 / rank
                break
        rrs.append(rr)
    if not retrieved:
        return {"precision": 0.0, "recall": 0.0, "mrr": 0.0}
    return {
        "precision": sum(precisions) / len(precisions),
        "recall": sum(recalls) / len(recalls),
        "mrr": sum(rrs) / len(rrs),
    }


def _lcs_len(a: Sequence[str], b: Sequence[str]) -> int:
    """Return the length of the longest common subsequence."""
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, ta in enumerate(a, 1):
        for j, tb in enumerate(b, 1):
            if ta == tb:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]


def compute_answer_metrics(predictions: Sequence[str], references: Sequence[str]) -> dict:
    """Compute Exact Match, F1 and ROUGE-L scores."""
    ems: list[float] = []
    f1s: list[float] = []
    rouges: list[float] = []
    for pred, ref in zip(predictions, references):
        pred_tokens = simple_tokenize(pred.lower())
        ref_tokens = simple_tokenize(ref.lower())
        ems.append(1.0 if pred.strip().lower() == ref.strip().lower() else 0.0)
        common = len(set(pred_tokens) & set(ref_tokens))
        if pred_tokens or ref_tokens:
            f1 = 2 * common / (len(pred_tokens) + len(ref_tokens))
        else:
            f1 = 0.0
        f1s.append(f1)
        lcs = _lcs_len(pred_tokens, ref_tokens)
        if lcs:
            prec = lcs / len(pred_tokens) if pred_tokens else 0.0
            rec = lcs / len(ref_tokens) if ref_tokens else 0.0
            rouge = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        else:
            rouge = 0.0
        rouges.append(rouge)
    if not predictions:
        return {"exact_match": 0.0, "f1": 0.0, "rouge_l": 0.0}
    return {
        "exact_match": sum(ems) / len(ems),
        "f1": sum(f1s) / len(f1s),
        "rouge_l": sum(rouges) / len(rouges),
    }


def write_metrics(run_id: str, stage: str, metrics: dict, metrics_dir: str = "outputs/metrics") -> None:
    """Write metrics to a JSON file and append a row to ``summary.csv``."""
    out_dir = Path(metrics_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{run_id}_{stage}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    summary_path = out_dir / "summary.csv"
    file_exists = summary_path.exists()
    with open(summary_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["run_id", "stage", "metric", "value"])
        for k, v in metrics.items():
            writer.writerow([run_id, stage, k, v])
