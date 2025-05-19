# AI Nurse Scoping Review Pipeline

The **AI Nurse Scoping Review (ScR) Pipeline** automates metadata extraction and summarisation of nursing literature. The project started as a set of large notebooks but has been refactored into a small Python package with a command line interface (CLI) so that each run is reproducible.

## Pipeline Overview
1. **Configure paths and environment** – paths and settings are loaded from a YAML/JSON configuration file.
2. **Collect PDFs** – place all documents to analyse in the chosen PDF folder.
3. **Parse metadata and text** – the pipeline extracts text from each PDF and enriches it with metadata from external sources.
4. **Write summary files** – results are saved as JSONL and CSV files for further analysis.

## Installation
Clone the repository and install the required packages. If running locally you also need to export your OpenAI API key so the extraction functions can call the API.

```bash
git clone https://github.com/Nurse-David/AI-Nurse_ScR_v6.git
cd AI-Nurse_ScR_v6
pip install -r requirements.txt
export OPENAI_API_KEY=<your-api-key>  # only for local environments
```

## Running in Google Colab
The repository ships with a helper module to simplify the Colab setup. The steps below walk through a full extraction run.

### 1. Start a new notebook and clone the repo
```python
!git clone https://github.com/Nurse-David/AI-Nurse_ScR_v6.git
%cd AI-Nurse_ScR_v6
```

### 2. Install Python dependencies
```python
!pip install -r requirements.txt
```
See `config_example.yaml` for the minimal keys (`pdf_dir`, `run_id`) your configuration file must define. JSON files follow the same schema.

Running this command executes the full extraction pipeline and writes a
JSONL file of metadata to the configured output directory. Each run also
creates a `config_snapshot.json` in the same directory capturing the loaded
configuration along with the current package version and git commit hash.



### 3. Add your OpenAI key as a user secret
1. Open **Settings → Manage user secrets** in the Colab menu.
2. Add a secret named `OPENAI_API_KEY` containing your key.

### 4. Mount Drive and create folders
Use `colab_setup.setup()` to mount Google Drive (if running in Colab) and create a timestamped project directory. The `PDFs` folder is now placed directly under the `Pilot` directory. The function also loads the secret `OPENAI_API_KEY` into the environment for you.

```python
import colab_setup
project_root, pdf_dir = colab_setup.setup()
```
Upload your PDF files to `pdf_dir` using the file browser or `google.colab.drive` utilities.

### 5. Create a configuration file
The minimal configuration requires a PDF directory and a run identifier.

```python
%%writefile config.yaml
pdf_dir: "${pdf_dir}"
run_id: my_first_run
output_dir: output
```

### 6. Run the extraction pipeline
Invoke the CLI with the configuration file and PDF directory.

```python
!python -m ai_nurse_scr.cli extract --config config.yaml --pdf-dir "$pdf_dir"
```
This command writes a JSONL file of metadata and a `config_snapshot.yaml` into the specified `output_dir`.

### 7. Optional: run sequential QA rounds
The pipeline also supports multi-stage question answering over PDFs.

```python
!python -m ai_nurse_scr.cli qa --config config.yaml --pdf-dir "$pdf_dir"
```
Two files (`*_round1.jsonl` and `*_round2.jsonl`) will be created in the output folder containing model answers.

### 8. Review the results
All output files reside in the folder specified by `output_dir`. Download them from Drive or continue analysing them within Colab.

## Running the CLI Locally
Outside Colab the commands are the same. Ensure your `OPENAI_API_KEY` environment variable is set and pass the path to your configuration file and PDF directory.

```bash
python -m ai_nurse_scr.cli extract --config config.yaml --pdf-dir path/to/PDFs
```

## Demo Notebook
The notebook `legacy_versions/Nurse_AI_ScR_v6_3.ipynb` demonstrates the pipeline step by step. It mirrors the CLI behaviour and can be executed locally or in Colab.

## Running Tests
Execute the unit test suite before committing changes:

```bash
python -m unittest discover tests -v
```

## License
This project is licensed under the [MIT License](LICENSE).

