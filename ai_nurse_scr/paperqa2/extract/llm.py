from ... import extraction


def extract_llm(data: dict) -> dict:
    """Use an LLM to fill missing metadata fields from the first page.

    Parameters
    ----------
    data : dict
        Dictionary containing at least the key ``"raw_first_page"``.

    Returns
    -------
    dict
        Metadata dictionary as returned by :func:`extraction.extract_ai_llm_full`.
        Empty values are returned on failure.
    """
    text = data.get("raw_first_page", "")
    try:
        return extraction.extract_ai_llm_full(text)
    except Exception:
        return {k: "" for k in extraction.fields}

