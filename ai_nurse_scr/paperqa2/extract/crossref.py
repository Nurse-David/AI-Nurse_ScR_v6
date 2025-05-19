from ... import extraction


def extract_crossref(doi: str) -> dict:
    """Retrieve Crossref metadata for a DOI.

    Parameters
    ----------
    doi : str
        DOI to look up.

    Returns
    -------
    dict
        Metadata dictionary as returned by :func:`extraction.extract_crossref_full`.
        Empty values are returned on failure.
    """
    try:
        return extraction.extract_crossref_full(doi)
    except Exception:
        return {k: "" for k in extraction.fields}

