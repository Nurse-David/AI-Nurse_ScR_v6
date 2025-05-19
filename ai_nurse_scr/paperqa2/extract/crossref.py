from ... import extraction


def extract_crossref(doi: str) -> dict:
    """Retrieve Crossref metadata for a DOI."""
    try:
        return extraction.extract_crossref_full(doi)
    except Exception:
        return {k: "" for k in extraction.fields}

