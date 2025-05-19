import hashlib
from pathlib import Path
from ..utils import normalize_doi


def sha256_file(path: str | Path) -> str:
    """Compute the SHA-256 hex digest of a file.

    Parameters
    ----------
    path:
        File path whose contents will be hashed.

    Returns
    -------
    str
        Hexadecimal SHA-256 digest string.
    """
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


