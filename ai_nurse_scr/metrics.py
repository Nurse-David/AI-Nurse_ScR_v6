from __future__ import annotations
from typing import Iterable, Tuple, List, Dict


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
