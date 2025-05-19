import json
from pathlib import Path


def load_config(path: str) -> dict:
    """Load JSON configuration from path."""
    with open(path, 'r') as f:
        return json.load(f)


def find_pdfs(directory: str):
    """Yield PDF files within the directory."""
    return sorted(Path(directory).glob('*.pdf'))


def extract_text(pdf_path: Path) -> str:
    """Placeholder to extract text from a PDF file."""
    print(f"[INFO] Extracting text from {pdf_path}")
    return ""


def extract_data(text: str) -> dict:
    """Placeholder to extract structured data from text."""
    print("[INFO] Extracting data from text")
    return {}


def run(config_path: str, pdf_dir: str) -> None:
    """Run the pipeline sequentially using the given configuration and PDF directory."""
    config = load_config(config_path)
    print(f"[INFO] Loaded config from {config_path}")

    pdfs = find_pdfs(pdf_dir)
    if not pdfs:
        print(f"[WARNING] No PDF files found in {pdf_dir}")

    for pdf in pdfs:
        text = extract_text(pdf)
        data = extract_data(text)
        # Insert actual processing logic here using `data` and `config`

    print("[INFO] Pipeline completed")
