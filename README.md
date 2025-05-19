# AI Nurse Scoping Review Pipeline

This repository contains an automated extraction pipeline used for the AI Nurse
scoping review (ScR). The goal of the project is to reproducibly gather
literature, extract metadata, and produce summary tables for further analysis.
The first iterations of this work lived entirely in very large notebooks. Those
notebooks have been refactored into smaller modules and a command line interface
(CLI) so that the code base is easier to maintain and test. The original
notebooks remain in this repository for reference.

## Extraction Pipeline Overview
1. Configure project paths and environment variables. The pipeline creates a
   `pipeline_env.json` file so subsequent steps can reload all paths without
   manual input.
2. Collect PDF documents and other source data.
3. Parse metadata and extract text from each file.
4. Generate CSV summaries of the corpus for downstream analysis.

The CLI orchestrates these steps to provide a deterministic, repeatable run.

## Installation
Clone the repository and install the required Python packages:

```bash
git clone <repo-url>
cd AI-Nurse_ScR_v6
pip install -r requirements.txt
```

## Running the CLI
The extraction pipeline exposes a CLI entry point. Run `--help` to see
available commands:

```bash
python -m ai_nurse_scr.cli --help
```

A typical extraction run might look like:

```bash
python -m ai_nurse_scr.cli extract --config config.yaml
```

The current implementation is a placeholder and will print a message. It can be
extended with real pipeline logic as needed.

## Demo Notebook
For an interactive walkthrough open `Nurse_AI_ScR_v6_3.ipynb` in Jupyter or
VS Code. The notebook demonstrates each stage of the pipeline and mirrors the
CLI functionality.

## History
Earlier versions of the project were maintained as single, very large notebooks.
These have been split into smaller modules and wrapped with a CLI to improve
maintainability. The original notebooks are provided for reference only.

## Running Tests
Execute the unit test suite using ``unittest``:

```bash
python -m unittest discover tests -v
```

