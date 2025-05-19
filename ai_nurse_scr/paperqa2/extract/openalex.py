from ... import extraction


def extract_openalex(doi: str) -> dict:
    """Retrieve OpenAlex metadata for a DOI.

    Parameters
    ----------
    doi:
        DOI used to request metadata from OpenAlex.

    Returns
    -------
    dict
        Metadata dictionary populated from the API response.
    """
    try:
        return extraction.extract_openalex_full(doi)
    except Exception:
        return {k: "" for k in extraction.fields}

