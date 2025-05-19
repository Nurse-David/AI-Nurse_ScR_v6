import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="AI Nurse Scoping Review Pipeline CLI (placeholder)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract = subparsers.add_parser(
        "extract", help="Run the data extraction pipeline (placeholder)."
    )
    extract.add_argument(
        "--config", help="Path to a configuration YAML file.", required=False
    )

    args = parser.parse_args(argv)

    if args.command == "extract":
        print("Running extraction pipeline...")
        print("(This is currently a placeholder implementation.)")


if __name__ == "__main__":
    main()
