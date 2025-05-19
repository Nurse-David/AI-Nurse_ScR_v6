from pathlib import Path
from typing import Dict
def get_project_root(in_colab: bool) -> Path:
    """Return project root depending on execution environment."""
    if in_colab:
        return Path('/content/drive/My Drive/Pilot')
    return Path.cwd() / "Pilot"


def build_artifact_dir(run_dir: Path, name: str) -> Path:
    """Ensure a named artifact directory exists within run_dir."""
    path = run_dir / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_operational_dir(run_dir: Path) -> Path:
    """Ensure the operational directory exists within run_dir."""
    return build_artifact_dir(run_dir, "operational")


def build_all_dirs(run_dir: Path) -> Dict[str, Path]:
    """Create and return all standard directories for a run."""
    dirs = {
        "operational": build_operational_dir(run_dir),
        "ai_artifacts": build_artifact_dir(run_dir, "ai_artifacts"),
        "reviewer_content": build_artifact_dir(run_dir, "reviewer_content"),
        "metrics": build_artifact_dir(run_dir, "metrics"),
        "audit": build_artifact_dir(run_dir, "audit"),
        "issues": build_artifact_dir(run_dir, "issues"),
        "tests": build_artifact_dir(run_dir, "tests"),
    }
    return dirs

