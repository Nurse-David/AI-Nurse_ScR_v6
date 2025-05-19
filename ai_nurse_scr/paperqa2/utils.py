import hashlib
from pathlib import Path
from ..utils import normalize_doi


def sha256_file(path: str | Path) -> str:
    """Compute the sha256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


