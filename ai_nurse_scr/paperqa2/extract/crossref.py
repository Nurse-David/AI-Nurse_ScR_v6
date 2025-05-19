from ... import extraction


def extract_crossref(doi: str) -> dict:
    """Retrieve Crossref metadata for a DOI.

    Parameters
    ----------
    doi:
        DOI to query in the Crossref API.

    Returns
    -------
    dict
        Mapping of metadata fields returned by Crossref.
    """
    try:
        return extraction.extract_crossref_full(doi)
    except Exception:
        return {k: "" for k in extraction.fields}

