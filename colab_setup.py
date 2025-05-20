"""Utilities for running this repository in Google Colab."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def in_colab() -> bool:
    """Return ``True`` when executed inside Google Colab."""
    return "google.colab" in sys.modules


def mount_drive() -> Path:
    """Mount the user's Google Drive and return the mount path.

    If the drive is already mounted the existing path is returned.
    """
    from google.colab import drive  # type: ignore

    mount_path = Path("/content/drive")
    if mount_path.exists() and any(mount_path.iterdir()):
        return mount_path

    drive.mount(str(mount_path))
    return mount_path


def auto_mount_drive() -> Path | None:
    """Mount Google Drive when running in Colab and not already mounted."""
    if not in_colab():
        return None
    mount_path = Path("/content/drive")
    if mount_path.exists() and any(mount_path.iterdir()):
        return mount_path
    from google.colab import drive  # type: ignore
    drive.mount(str(mount_path))
    return mount_path


def setup(base_dir: str = "My Drive/Pilot", project_prefix: str = "ScR_GitHub_v1") -> tuple[Path, Path]:
    """Mount Drive and create project directories under ``base_dir``.

    Parameters
    ----------
    base_dir:
        Directory inside ``My Drive`` used to store project files.
    project_prefix:
        Prefix for the timestamped project folder.

    Returns
    -------
    tuple
        The created ``(project_root, pdf_dir)`` paths.
    """
    if not in_colab():
        print("[INFO] Not running inside Google Colab; skipping Drive setup.")
        cwd = Path.cwd()
        pdf_dir = cwd / "PDFs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        return cwd, pdf_dir

    mount_path = mount_drive()
    timestamp = time.strftime("%y%m%d_%H%M")
    project_root = mount_path / base_dir / f"{project_prefix}_{timestamp}"
    project_root.mkdir(parents=True, exist_ok=True)
    os.chdir(project_root)

    pdf_dir = mount_path / base_dir / "PDFs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    try:
        from google.colab import userdata  # type: ignore

        api_key = userdata.get("OPENAI_API_KEY")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    except Exception:
        pass

    print(f"[INFO] Project root: {project_root}")
    print(f"[INFO] PDF directory: {pdf_dir}")
    return project_root, pdf_dir
