from ... import extraction


def extract_llm(data: dict) -> dict:
    """Use an LLM to fill missing metadata fields from the first page."""
    text = data.get("raw_first_page", "")
    try:
        return extraction.extract_ai_llm_full(text)
    except Exception:
        return {k: "" for k in extraction.fields}

