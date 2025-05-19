"""Utility functions for extracting metadata from a variety of sources.

This module contains helper functions used throughout the project to
retrieve or infer bibliographic data for a paper.  Metadata can be
gathered from external APIs such as Crossref or OpenAlex, or inferred
from the text of the first page of a document using an LLM.  The helpers
return dictionaries keyed by a common set of fields defined in
``fields``.
"""

import os
import json
from .utils import normalize_doi
try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None

fields = [
    "title", "author", "year", "doi",
    "author_keywords", "country", "source_journal", "study_type"
]

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
llm_model = "gpt-4"


def clean_str(txt: str) -> str:
    """Return a simplified lowercase string containing only alphanumerics.

    Parameters
    ----------
    txt : str
        Input text which may contain punctuation or mixed case.

    Returns
    -------
    str
        Text normalised to lowercase with spaces and punctuation removed.
    """

    return "".join(c for c in str(txt or "").lower() if c.isalnum() or c.isspace()).replace(" ", "")


def approx_match(a: str, b: str, field: str) -> bool:
    """Loosely compare two metadata values.

    Parameters
    ----------
    a, b : str
        Values to compare.
    field : str
        Name of the metadata field being compared.  ``"doi"`` and
        ``"author_keywords"`` are treated specially.

    Returns
    -------
    bool
        ``True`` if the values are considered equivalent.
    """

    if a is None or b is None:
        return False
    if field == "doi":
        return normalize_doi(a) == normalize_doi(b)
    if field in ["author_keywords"]:
        sa = sorted({x.strip() for x in str(a).replace(";", " ").replace(",", " ").lower().split() if x})
        sb = sorted({x.strip() for x in str(b).replace(";", " ").replace(",", " ").lower().split() if x})
        return sa == sb
    return clean_str(a) == clean_str(b)


def extract_crossref_full(doi: str, title: str | None = None) -> dict:
    """Retrieve metadata from the Crossref API.

    Parameters
    ----------
    doi : str
        DOI of the paper.
    title : str, optional
        Title to query when a DOI is not supplied.

    Returns
    -------
    dict
        Dictionary populated with ``fields`` keys.
    """

    meta = {f: "" for f in fields}
    try:
        url = f"https://api.crossref.org/works/{normalize_doi(doi)}" if doi else None
        if url:
            r = requests.get(url)
            dat = r.json()["message"]
        elif title:
            r = requests.get(f"https://api.crossref.org/works?query.title={title}&rows=1")
            items = r.json()["message"].get("items", [])
            dat = items[0] if items else {}
        else:
            dat = {}
        meta["doi"] = normalize_doi(dat.get("DOI", ""))
        meta["title"] = dat.get("title", [""])[0]
        if dat.get("author"):
            meta["author"] = "; ".join(
                "{}, {}".format(a.get("family", "").strip(), a.get("given", "").strip())
                for a in dat.get("author")
            )
            meta["country"] = "; ".join(
                aff.get("name", "")
                for a in dat["author"]
                for aff in a.get("affiliation", [])
            ).strip()
        meta["year"] = str(dat.get("issued", {}).get("date-parts", [[None]])[0][0]) if dat.get("issued") else ""
        meta["author_keywords"] = ";".join(dat.get("subject", [])) if dat.get("subject") else ""
        meta["source_journal"] = dat.get("container-title", [""])[0] if dat.get("container-title") else ""
        meta["study_type"] = dat.get("type", "")
    except Exception:
        pass
    return meta


def extract_openalex_full(doi: str, title: str | None = None) -> dict:
    """Retrieve metadata from the OpenAlex API.

    Parameters
    ----------
    doi : str
        DOI of the paper.
    title : str, optional
        Title used when a DOI lookup fails.

    Returns
    -------
    dict
        Dictionary populated with ``fields`` keys.
    """

    meta = {f: "" for f in fields}
    try:
        url = (
            f"https://api.openalex.org/works/https://doi.org/{normalize_doi(doi)}"
            if doi
            else None
        )
        if url:
            r = requests.get(url)
            dat = r.json()
        elif title:
            url = f"https://api.openalex.org/works?title.search={title}"
            r = requests.get(url)
            dat = r.json().get("results", [{}])[0] if "results" in r.json() else r.json()
        else:
            dat = {}
        doi_val = dat.get("doi", "")
        if doi_val.startswith("https://doi.org/"):
            doi_val = doi_val[len("https://doi.org/") :]
        meta["doi"] = normalize_doi(doi_val)
        meta["title"] = dat.get("title", "")
        meta["author"] = "; ".join(
            a.get("author", {}).get("display_name", "") for a in dat.get("authorships", [])
        )
        meta["year"] = str(dat.get("publication_year", ""))
        meta["author_keywords"] = ";".join(dat.get("keywords", [])) if dat.get("keywords") else ""
        meta["source_journal"] = dat.get("host_venue", {}).get("display_name", "") if dat.get("host_venue") else ""
        meta["study_type"] = dat.get("type", "")
        meta["country"] = "; ".join(
            inst.get("country_code", "")
            for auth in dat.get("authorships", [])
            for inst in auth.get("institutions", [])
        )
    except Exception:
        pass
    return meta


def extract_ai_llm_doi_only(first_page: str, api_key: str | None = None, model: str | None = None) -> str:
    """Extract a DOI from the first page text using an LLM.

    Parameters
    ----------
    first_page : str
        Text from the first page of the document.
    api_key : str, optional
        OpenAI API key. Defaults to the ``OPENAI_API_KEY`` environment
        variable.
    model : str, optional
        LLM model name, default uses ``llm_model``.

    Returns
    -------
    str
        The extracted DOI, or an empty string if none is found or an
        error occurs.
    """

    api_key = api_key or OPENAI_API_KEY
    prompt = (
        "Extract only the DOI (Digital Object Identifier) from the following text. If none is found, return an empty JSON.\n"
        f"Text:\n{first_page}"
    )
    if not api_key:
        return ""
    try:
        import openai

        resp = openai.chat.completions.create(
            model=model or llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=24,
        )
        txt = resp.choices[0].message.content.strip()
        if txt.startswith("```"):
            txt = txt.strip("` \n")
            txt = txt[4:].strip() if txt.startswith("json") else txt
        result = json.loads(txt)
        return result.get("doi", "") if isinstance(result, dict) else result
    except Exception:
        return ""


def extract_ai_llm_full(first_page: str, api_key: str | None = None, model: str | None = None) -> dict:
    """Infer metadata from page text using an LLM.

    Parameters
    ----------
    first_page : str
        Text from the first page of the document.
    api_key : str, optional
        OpenAI API key. Defaults to the ``OPENAI_API_KEY`` environment
        variable.
    model : str, optional
        LLM model name, default uses ``llm_model``.

    Returns
    -------
    dict
        Dictionary of extracted metadata with ``fields`` keys.  Missing
        or failed values are returned as empty strings.
    """

    api_key = api_key or OPENAI_API_KEY
    prompt = (
        "Extract the following metadata as a JSON object from the text provided: title, author, year, doi, "
        "author_keywords, country, source_journal, study_type. "
        "If a field is missing, leave blank or use null. Text follows:\n" + first_page
    )
    if not api_key:
        return {k: "" for k in fields}
    try:
        import openai

        resp = openai.chat.completions.create(
            model=model or llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=384,
        )
        txt = resp.choices[0].message.content.strip()
        if txt.startswith("```"):
            txt = txt.strip("` \n")
            txt = txt[4:].strip() if txt.startswith("json") else txt
        result = json.loads(txt)
        return {k: result.get(k, "") for k in fields}
    except Exception:
        return {k: "" for k in fields}
