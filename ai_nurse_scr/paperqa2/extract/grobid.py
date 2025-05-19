from pathlib import Path

from ...utils import check_grobid_healthy


def extract_grobid(pdf_path: str | Path) -> dict:
    """Call a local GROBID service to extract header information.

    Parameters
    ----------
    pdf_path : str or Path
        Path to the PDF file to send to GROBID.

    Returns
    -------
    dict
        Dictionary containing the key ``"grobid_xml"`` if successful, or an
        empty dictionary if the service is unavailable or an error occurs.
    """
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

