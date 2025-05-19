import hashlib
import re
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Compute the sha256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def normalize_doi(doi: str) -> str:
    """Normalize a DOI string by removing URL prefixes and whitespace."""
    doi = doi.strip()
    doi = doi.lower()
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi)
    return doi
