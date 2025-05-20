from __future__ import annotations

import sys
import time
from pathlib import Path

_PROJECT_ROOT = None


def default_project_root() -> Path:
    if "google.colab" in sys.modules:
        return Path("/content/drive")
    return Path.cwd()


def set_project_root(path: Path) -> None:
    global _PROJECT_ROOT
    _PROJECT_ROOT = path


def get_project_root() -> Path:
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        _PROJECT_ROOT = default_project_root()
    return _PROJECT_ROOT


def get_path(*parts: str | Path) -> Path:
    return get_project_root().joinpath(*parts)


def timestamped_filename(stage: str, round_tag: int | None = None, ext: str = "jsonl") -> str:
    ts = time.strftime("%Y%m%d_%H%M")
    if round_tag is not None:
        return f"{stage}_round{round_tag}_{ts}.{ext}"
    return f"{stage}_{ts}.{ext}"
