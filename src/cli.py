import argparse

from . import pipeline


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the AI Nurse extraction pipeline")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the JSON configuration file"
    )
    parser.add_argument(
        "--pdf-dir",
        required=True,
        help="Directory containing PDF files to process"
    )
    args = parser.parse_args(argv)

    pipeline.run(config_path=args.config, pdf_dir=args.pdf_dir)


if __name__ == "__main__":
    main()
