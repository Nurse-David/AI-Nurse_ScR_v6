from ... import extraction


def extract_openalex(doi: str) -> dict:
    """Retrieve OpenAlex metadata for a DOI.

    Parameters
    ----------
    doi : str
        DOI to look up.

    Returns
    -------
    dict
        Metadata dictionary as returned by :func:`extraction.extract_openalex_full`.
        Empty values are returned on failure.
    """
    try:
        return extraction.extract_openalex_full(doi)
    except Exception:
        return {k: "" for k in extraction.fields}

