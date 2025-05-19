import hashlib
import os
import json
import re
try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None


def sha256_file(path):
    """Return SHA-256 hex digest of a file or None on error."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def pdf_hash_id(pdf_path, length=8):
    """Return a short hash identifier for a PDF path."""
    h = hashlib.sha1(str(pdf_path).encode("utf-8")).hexdigest()[:length]
    return f"paper_ID_{h}"


def normalize_doi(x):
    """Normalize DOI strings into a canonical form."""
    if not x or not isinstance(x, str):
        return ""
    x = x.strip().lower().replace(" ", "")
    x = re.sub(r"^(https?://(dx\.)?doi\.org/)", "", x)
    x = re.sub(r"\s", "", x)
    return x


def check_grobid_healthy(url="http://localhost:8070/api/isalive", timeout=8):
    """Check if the GROBID service is responding."""
    if requests is None:
        return False
    try:
        r = requests.get(url, timeout=timeout)
        return (r.status_code == 200) and ("grobid" in r.text.lower() or "true" in r.text.lower())
    except Exception:
        return False


def write_audit_log(data, path="audit/block1_env_fingerprint.jsonl"):
    """Append JSON data to an audit log."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
