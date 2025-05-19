import argparse

from . import pipeline, setup


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

    args = parser.parse_args(argv)

    if args.command == "extract":
        setup.install_dependencies()
        setup.prepare_environment()
        pipeline.run(args.config, args.pdf_dir)


if __name__ == "__main__":
    main()
