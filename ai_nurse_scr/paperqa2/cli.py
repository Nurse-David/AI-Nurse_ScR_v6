import argparse
import json
from pathlib import Path

from .pipeline import run_pipeline


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run paperqa2 pipeline")
    parser.add_argument("pdf", type=Path, help="Path to PDF file")
    parser.add_argument("--output", type=Path, help="Output JSON file")
    args = parser.parse_args(argv)

    result = run_pipeline(args.pdf)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
