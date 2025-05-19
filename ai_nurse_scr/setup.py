"""Setup utilities extracted from the original notebooks."""


from pathlib import Path
import importlib


def install_dependencies() -> None:
    """Verify that packages listed in ``requirements.txt`` are installed."""
    req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    missing: list[str] = []
    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            pkg = line.strip().split("==")[0]
            if not pkg:
                continue
            module = "fitz" if pkg == "pymupdf" else pkg.replace("-", "_")
            try:
                importlib.import_module(module)
            except Exception:
                missing.append(pkg)
    if missing:
        raise ImportError(
            "Missing required packages: " + ", ".join(missing) +
            ". Install them via `pip install -r requirements.txt`."
        )


def prepare_environment(output_dir: str | None = None) -> None:
    """Create output directories needed for pipeline results."""
    out = Path(output_dir or "output")
    out.mkdir(parents=True, exist_ok=True)
    print(f"[SETUP] Output directory ready at {out}")
