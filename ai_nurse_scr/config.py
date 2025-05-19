from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional
import json
import os

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover - optional dependency
    yaml = None


class ConfigError(Exception):
    """Custom error for configuration issues."""


@dataclass
class Config:
    pdf_dir: str
    run_id: str
    extra: Dict[str, Any] = field(default_factory=dict)


def _load_raw(path: str) -> Dict[str, Any]:
    """Load raw configuration data from YAML or JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file '{path}' does not exist.")

    with open(path, "r", encoding="utf-8") as f:
        if path.lower().endswith((".yaml", ".yml")):
            if yaml is None:
                raise ConfigError("PyYAML is required to load YAML files.")
            return yaml.safe_load(f) or {}
        elif path.lower().endswith(".json"):
            return json.load(f)
        else:
            raise ConfigError("Unsupported config format. Use YAML or JSON.")


def load_config(path: str, required_keys: Optional[Iterable[str]] = None) -> Config:
    """Load a configuration file and validate required keys.

    Parameters
    ----------
    path:
        Path to YAML or JSON configuration file.
    required_keys:
        Keys that must exist in the configuration. If ``None`` a default
        set of ``{"pdf_dir", "run_id"}`` is enforced.

    Returns
    -------
    Config
        Parsed configuration dataclass.
    """
    if required_keys is None:
        required_keys = ["pdf_dir", "run_id"]

    data = _load_raw(path)
    if not isinstance(data, dict):
        raise ConfigError("Configuration root must be a mapping/dictionary.")

    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ConfigError(
            "Missing required config key(s): " + ", ".join(missing)
        )

    pdf_dir = data.pop("pdf_dir")
    run_id = data.pop("run_id")
    return Config(pdf_dir=pdf_dir, run_id=run_id, extra=data)
