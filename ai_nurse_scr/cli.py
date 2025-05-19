import argparse
from pathlib import Path

from . import pipeline, setup
from .evaluation import spotcheck_files


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="AI Nurse Scoping Review Pipeline CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser(
        "extract", help="Run the data extraction pipeline"
    )
    extract.add_argument(
        "--config", help="Path to a JSON configuration file", required=True
    )
    extract.add_argument(
        "--pdf-dir", help="Directory containing PDF files", required=True
    )

    spot = subparsers.add_parser(
        "spotcheck", help="LLM-based semantic spot check between two CSV files"
    )
    spot.add_argument("--file1", required=True, help="First CSV file")
    spot.add_argument("--file2", required=True, help="Second CSV file")
    spot.add_argument(
        "--context-col", default="text", help="Column containing context"
    )
    spot.add_argument(
        "--answer-col", default="llm_answer", help="Answer column name"
    )
    spot.add_argument("--out", help="Output CSV path")
    spot.add_argument("--n-check", type=int, default=10, help="Rows to check")
    spot.add_argument("--api-key", help="OpenAI API key")
    spot.add_argument("--model", default="gpt-4.1", help="LLM model name")

    args = parser.parse_args(argv)

    if args.command == "extract":
        setup.install_dependencies()
        setup.prepare_environment()
        pipeline.run(args.config, args.pdf_dir)
    elif args.command == "spotcheck":
        spotcheck_files(
            Path(args.file1),
            Path(args.file2),
            context_col=args.context_col,
            ans_col=args.answer_col,
            out_path=Path(args.out) if args.out else None,
            n_check=args.n_check,
            openai_api_key=args.api_key,
            model=args.model,
        )


if __name__ == "__main__":
    main()
