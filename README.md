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
Clone the repository and install the required Python packages using the real
GitHub URL:

```bash
git clone https://github.com/Nurse-David/AI-Nurse_ScR_v6.git
cd AI-Nurse_ScR_v6
pip install -r requirements.txt
# If running locally export your OpenAI key so extraction functions can call the API
export OPENAI_API_KEY=<your-api-key>
# On Google Colab store the key as a secret named `OPENAI_API_KEY` and use the
# snippet in the next section to load it.
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
See `config_example.yaml` for the minimal keys (`pdf_dir`, `run_id`) your configuration file must define.

Running this command executes the full extraction pipeline and writes a
JSONL file of metadata to the configured output directory. Each run also
creates a `config_snapshot.yaml` in the same directory capturing the loaded
configuration along with the current package version and git commit hash.

## Running in Google Colab
When using Colab you may want project files to persist on Google Drive.
First create a user secret:

1. Open **Settings → Manage user secrets** in the Colab menu.
2. Add your OpenAI key under the name `OPENAI_API_KEY`.

The snippet below mounts Drive, creates a timestamped project folder, clones
the repository and loads the secret:

```python
from google.colab import drive, userdata
from pathlib import Path
import time

drive.mount('/content/drive')
timestamp = time.strftime('%y%m%d_%H%M')
project_root = Path('/content/drive/My Drive/Pilot') / f'ScR_GitHub_v1_{timestamp}'
project_root.mkdir(parents=True, exist_ok=True)
%cd $project_root
!git clone https://github.com/Nurse-David/AI-Nurse_ScR_v6.git
%cd AI-Nurse_ScR_v6
!pip install -r requirements.txt

# Retrieve your key from Colab secrets and expose it as an env variable
import os
os.environ["OPENAI_API_KEY"] = userdata.get('OPENAI_API_KEY')

pdf_root = Path('/content/drive/My Drive/Pilot/PDFs')
pdf_root.mkdir(parents=True, exist_ok=True)

```

Store your PDFs in `/content/drive/My Drive/Pilot/PDFs` and reference that
directory when running the CLI or notebook.

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

## License

This project is licensed under the [MIT License](LICENSE).


