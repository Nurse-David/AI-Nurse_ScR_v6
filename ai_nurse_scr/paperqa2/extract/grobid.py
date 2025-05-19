from pathlib import Path

from ...utils import check_grobid_healthy


def extract_grobid(pdf_path: str | Path) -> dict:
    """Call a local GROBID service to extract header information."""
    if not check_grobid_healthy():
        return {}
    try:
        import requests
    except Exception:
        return {}
    try:
        with open(pdf_path, "rb") as f:
            resp = requests.post(
                "http://localhost:8070/api/processHeaderDocument",
                files={"input": f},
            )
        resp.raise_for_status()
        return {"grobid_xml": resp.text}
    except Exception:
        return {}

