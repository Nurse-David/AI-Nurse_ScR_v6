"""AI Nurse Scoping Review package."""


from importlib.metadata import version as _pkg_version, PackageNotFoundError

try:  # Use package metadata if available
    __version__ = _pkg_version("ai-nurse-scr")
except PackageNotFoundError:  # Fallback for editable installs
    __version__ = "0.1.0"

__all__ = ["pipeline", "config", "utils", "extraction", "setup"]

from . import pipeline, config, utils, extraction, setup
from . import evaluation

