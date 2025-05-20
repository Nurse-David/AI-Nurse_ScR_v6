"""AI Nurse Scoping Review package."""
from __future__ import annotations

import subprocess
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path

try:  # Use package metadata if available
    __version__ = _pkg_version("ai-nurse-scr")
except PackageNotFoundError:  # Fallback for editable installs
    __version__ = "0.1.0"


def _git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parent.parent,
            text=True,
        ).strip()
    except Exception:
        return "unknown"

__git_hash__ = _git_hash()

__all__ = ["pipeline", "config", "utils", "extraction", "setup", "paths"]

from . import pipeline, config, utils, extraction, setup, paths
from . import evaluation
