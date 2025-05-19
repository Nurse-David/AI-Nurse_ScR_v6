# @title [Block 1] Install & Verify All Pipeline Libraries (+Deprecation-safe, Audit Logging, Timezone)

# Version 6.2.5

# v6.0: Added tiktoken and improved environment/version printouts.

# v6.1: Suppresses noisy pdfminer/pdfplumber warnings, writes requirements.txt, more clear reviewer messages.

# v6.2: Audit log, fail-closed preflight, critical package enforcement, more robust error/warning audit output.

# v6.2.3: NZDT/UTC timestamp for chain-of-custody, audit-logging enhanced.

# v6.2.4: Fully removes pkg_resources, uses importlib.metadata for requirements/version print.

# v6.2.5: [BUGFIX] Corrects `required_packages` unpacking (now always 3-element tuples).

#

# Block Summary

#

# - Installs/verifies all dependencies, fails closed if any are missing.

# - Suppresses pdfminer/pdfplumber UserWarnings.

# - Prints all required package versions, Python/platform/locale.

# - Records UTC and NZDT timestamps for fixity audit.

# - Writes requirements.txt and audit/block1_env_fingerprint.jsonl.

# - Uses importlib.metadata (not pkg_resources) everywhere.



import sys, platform, subprocess, os, locale, hashlib, json

from datetime import datetime

from pathlib import Path
from src.utils import sha256_file, write_audit_log, check_grobid_healthy, pdf_hash_id, normalize_doi



# ---- Timezone handling ----

try:

    import zoneinfo

    TZ_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")

    now_nzdt = datetime.now(TZ_NZ)

except Exception:

    TZ_NZ = None

    now_nzdt = None

now_utc = datetime.utcnow()

now_utc_iso = now_utc.isoformat() + "Z"

now_nzdt_iso = (now_nzdt.isoformat() if now_nzdt else "Unavailable")



# --------- Audit log helper ----------







# --------- Suppress noisy PDF warnings ----------

import logging, warnings

logging.getLogger("pdfminer").setLevel(logging.ERROR)

logging.getLogger("pdfminer.pdfpage").setLevel(logging.ERROR)

warnings.filterwarnings("ignore", category=UserWarning)



# --------- REQUIRED/IMPORT names and install names (pip_name, import_name, dist_name) ----------

required_packages = [

    ("PyMuPDF", "fitz", "pymupdf"),

    ("pdfplumber", "pdfplumber", "pdfplumber"),

    ("pandas", "pandas", "pandas"),

    ("tqdm", "tqdm", "tqdm"),

    ("tiktoken", "tiktoken", "tiktoken"),

    ("openai", "openai", "openai"),

    ("requests", "requests", "requests"),

    ("pyyaml", "yaml", "pyyaml"),

]



# --------- Audit log object ----------

block1_audit = {

    "step": "block1_install_and_env",

    "timestamp_utc": now_utc_iso,

    "timestamp_nzdt": now_nzdt_iso,

    "python_version": sys.version,

    "platform": platform.platform(),

    "cwd": str(Path.cwd()),

    "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),

    "locale": "",

    "requirements_txt_hash": None,

    "errors": [],

    "warnings": [],

}



try:

    block1_audit["locale"] = locale.setlocale(locale.LC_ALL, '')

except Exception:

    block1_audit["warnings"].append("Could not detect locale.")



# --------- Preflight: install/verify packages, fail-closed if not present ----------

def pip_install_package(pip_name, import_name):

    try:

        __import__(import_name)

        return True

    except ImportError:

        try:

            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])

            __import__(import_name)

            return True

        except Exception as e:

            return str(e)



failed_pkgs = []

for pip_name, import_name, dist_name in required_packages:

    result = pip_install_package(pip_name, import_name)

    if result is not True:

        failed_pkgs.append((pip_name, result))

if failed_pkgs:

    print("\n[CRITICAL ERROR] Could not install required dependencies:")

    for pip_name, err in failed_pkgs:

        print(f" - {pip_name}: {err}")

        block1_audit["errors"].append(f"{pip_name}: {err}")

    write_audit_log(block1_audit)

    print("Reviewer Action:\n - Please verify internet access and pip availability.\n - Rerun this block when resolved.\n - Error log is saved to audit/block1_env_fingerprint.jsonl.")

    raise SystemExit("Block 1 failed closed due to missing required libraries.")



# --------- Write requirements.txt and hash it for audit trail ----------

try:

    try:

        import importlib.metadata as importlib_metadata

    except ImportError:

        import importlib_metadata # type: ignore

    dists = sorted(importlib_metadata.distributions(), key=lambda d: (d.metadata["Name"] if "Name" in d.metadata else d._path.name).lower())

    with open("requirements.txt", "w", encoding="utf-8") as f:

        for dist in dists:

            name = dist.metadata["Name"] if "Name" in dist.metadata else dist._path.name

            version = dist.version

            f.write(f"{name}=={version}\n")

    req_hash = sha256_file("requirements.txt")

    block1_audit["requirements_txt_hash"] = req_hash

except Exception as e:

    msg = f"Could not write requirements.txt: {e}"

    block1_audit["warnings"].append(msg)

    print("[WARN]", msg)



# --------- Print python/environment/time details ----------

print("--- PYTHON ENVIRONMENT FINGERPRINT ---")

print(f"Python version: {sys.version}")

print(f"Platform      : {platform.platform()}")

print(f"CWD           : {Path.cwd()}")

try:

    print(f"Locale        : {locale.setlocale(locale.LC_ALL, '')}")

except:

    print("Locale        : [Could not detect locale]")

print(f"Datetime UTC  : {now_utc_iso}")

print(f"Datetime NZDT : {now_nzdt_iso if now_nzdt else '[Zoneinfo not installed]'}")

print("- Required Pip Package Versions -")

for pip_name, import_name, dist_name in required_packages:

    try:

        version = importlib_metadata.version(dist_name)

        print(f"{pip_name}: {version}")

    except Exception as e:

        print(f"{pip_name}: NOT INSTALLED or version not found ({e})")

        block1_audit["warnings"].append(f"{pip_name}: not found ({e})")

print("--- End Block 1 ---")

write_audit_log(block1_audit)
# @title [Block 2] Define Project Paths, Mount Drive, NZDT Run Folder, Print PDF Corpus Summary, Interactive Config Confirmation, Save pipeline_env.json (v6.2.5)

#

# ----------- [Version 6.2.5] -----------

# v6.0: Sets up all pipeline dirs and run/output/audit folders.

# v6.1: Reviewer-friendly summary and robust error checks.

# v6.2: Audit logging, fail-closed config, explicit directory setup, next-step guidance.

# v6.2.3: NZDT time/fixity, prints cd/CONFIG_PATH helper, logs NZDT+UTC.

# v6.2.5: On completion, writes all global pipeline folder/ID variables to pipeline_env.json for use in all future blocks (NO search or input needed).

#

# ----------- [Block Summary] -----------

# - Sets up and prints all pipeline directories and run/output/audit folders with NZDT/UTC timestamp for fixity.

# - Creates/validates config.yaml (if missing, prints code-grouped YAML, reviewer Y/N pause option).

# - Writes all project/run path/globals to pipeline_env.json so all next blocks just reload this—NO searching, prompt, or ambiguity.

# - Reviewer guidance, printout, and summary for PI/repro.

# - Audit log written with full NZDT/UTC provenance.

#

# ----------- [Start of Code] -----------

import os

from pathlib import Path

import json

import yaml

from datetime import datetime



# --- Timezone safe run creation ---

try:

    import zoneinfo

    TZ_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")

    now_nzdt = datetime.now(TZ_NZ)

    NOW_STR = now_nzdt.strftime('%y%m%d_%H%M')

    now_utc = datetime.utcnow()

    NZDT_LABEL = now_nzdt.isoformat()

    UTC_LABEL = now_utc.isoformat() + "Z"

except Exception:

    TZ_NZ = None

    now_nzdt = None

    NOW_STR = datetime.utcnow().strftime('%y%m%d_%H%M')

    now_utc = datetime.utcnow()

    NZDT_LABEL = "Unavailable"

    UTC_LABEL = now_utc.isoformat() + "Z"



try:

    import google.colab

    IN_COLAB = True

except ImportError:

    IN_COLAB = False

if IN_COLAB:

    from google.colab import drive

    drive.mount('/content/drive')



PROJECT_ROOT = Path('/content/drive/My Drive/Pilot') if IN_COLAB else Path.cwd() / "Pilot"

PDF_DIR = PROJECT_ROOT / 'PDFs'

RUN_ID = f"Nurse-AI_ScR_{NOW_STR}"

RUN_DIR = PROJECT_ROOT / RUN_ID

OPERATIONAL_DIR      = RUN_DIR / 'operational'

AI_ARTIFACTS_DIR     = RUN_DIR / 'ai_artifacts'

REVIEWER_CONTENT_DIR = RUN_DIR / 'reviewer_content'

METRICS_DIR          = RUN_DIR / 'metrics'

AUDIT_DIR            = RUN_DIR / 'audit'

ISSUES_DIR           = RUN_DIR / 'issues'

TESTS_DIR            = RUN_DIR / 'tests'

for d in [RUN_DIR, OPERATIONAL_DIR, AI_ARTIFACTS_DIR, REVIEWER_CONTENT_DIR, METRICS_DIR, AUDIT_DIR, ISSUES_DIR, TESTS_DIR]:

    d.mkdir(parents=True, exist_ok=True)



pdfs_list = sorted(PDF_DIR.glob('*.pdf')) if PDF_DIR.exists() else []

n_pdfs = len(pdfs_list)



CONFIG_PATH = OPERATIONAL_DIR / "config.yaml"

MANIFEST_PATH = OPERATIONAL_DIR / "manifest.csv"

CONFIG_PARAMETERS = {

    'llm_model': 'gpt-4.1-2025-04-14',

    'openai_key_envvar': 'OPENAI_API_KEY',

    'embedding_model': 'text-embedding-3-large',

    'chunk_sizes': [500, 5000],

    'chunk_overlaps': {500: 100, 5000: 500},

    'tiktoken_encoding': 'cl100k_base',

    'num_pdfs': n_pdfs,

    'temperature_schedule': [0.0, 0.0, 0.0, 0.1, 0.2],

    'max_context_tokens': 1000000,

    'max_synthesis_tokens': 1000000,

    'run_timestamp': NZDT_LABEL,

    'run_id': RUN_ID,

    'use_grobid': True,

    'grobid_url': "http://localhost:8070/api/processHeaderDocument",

    'use_crossref': True,

    'use_openalex': True,

    'allow_internet': False,

    'allow_dynamic_expansion': False,

}

CONFIG_PATHS = {

    'pdf_dir': str(PDF_DIR),

    'run_dir': str(RUN_DIR),

    'project_root': str(PROJECT_ROOT),

    'manifest_path': str(MANIFEST_PATH),

    'operational_dir': str(OPERATIONAL_DIR),

    'ai_artifacts_dir': str(AI_ARTIFACTS_DIR),

    'reviewer_content_dir': str(REVIEWER_CONTENT_DIR),

    'metrics_dir': str(METRICS_DIR),

    'audit_dir': str(AUDIT_DIR),

    'issues_dir': str(ISSUES_DIR),

    'tests_dir': str(TESTS_DIR),

}

DEFAULT_CONFIG = {**CONFIG_PARAMETERS, **CONFIG_PATHS}

config_yaml_content = "# --- Pipeline Parameters and Tools ---\n"

config_yaml_content += yaml.dump(CONFIG_PARAMETERS, sort_keys=False, default_flow_style=False)

config_yaml_content += "\n# --- Directories, Paths, and Filenames ---\n"

config_yaml_content += yaml.dump(CONFIG_PATHS, sort_keys=False, default_flow_style=False)



missing_config = False

user_choice = None

if not CONFIG_PATH.exists():

    missing_config = True

    with open(CONFIG_PATH, "w") as f:

        f.write(config_yaml_content)

    print(f"\n[NOTICE] config.yaml was NOT found and a full template was created at:\n  {CONFIG_PATH}")

    print("------ config.yaml TEMPLATE CONTENT ------")

    print(config_yaml_content)

    print("-----------------------------------------")

    try:

        user_choice = input("Would you like to edit config.yaml before continuing? [Y/N]: ").strip().lower()

    except Exception:

        user_choice = "n"

    if user_choice == "y":

        print(f"Pause here and edit config.yaml at:\n  {CONFIG_PATH}\nThen run this block again when finished.")

        block2_audit = {

            "step": "block2_dir_and_config_preflight",

            "timestamp_nzdt": NZDT_LABEL,

            "timestamp_utc": UTC_LABEL,

            "user_decision": "pause_to_edit_config",

            "config_path": str(CONFIG_PATH),

        }

        audit_log_path = AUDIT_DIR / "block2_dirsetup_preflight.jsonl"

        with open(audit_log_path, "a", encoding="utf-8") as f:

            f.write(json.dumps(block2_audit, ensure_ascii=False) + "\n")

        raise RuntimeError("[BLOCK 2 PAUSED] Edit config.yaml and rerun this cell.")

    else:

        print("Continuing with the generated config.yaml as shown above.")

else:

    print(f"[OK] config.yaml found: {CONFIG_PATH}")



print(f"\n--- BLOCK 2: PDF Corpus & Directory Setup ---")

print(f"Python working directory now (os.getcwd()): {os.getcwd()}")

print(f"Time in NZDT: {NZDT_LABEL} | UTC: {UTC_LABEL}")

print(f"PROJECT_ROOT    : {PROJECT_ROOT}")

print(f"PDF_DIR         : {PDF_DIR}")

print(f"SAMPLE RUN_DIR  : {RUN_DIR}")



if not PDF_DIR.exists():

    print(f" [ERROR] PDF corpus directory does not exist: {PDF_DIR}")

    corpus_ok = False

elif not n_pdfs:

    print(f" [WARNING] PDF corpus exists, but contains NO PDF files.")

    corpus_ok = False

else:

    corpus_ok = True

    print(f" [OK] Found {n_pdfs} PDF file(s) in '{PDF_DIR}':")

    shown_files = [f.name for f in pdfs_list[:5]]

    for i, fname in enumerate(shown_files, 1):

        print(f" [{i}] {fname}")

    if n_pdfs > 5:

        print(f" ... ({n_pdfs - 5} more not shown)")

    missing_ext = [f for f in pdfs_list if not f.name.lower().endswith('.pdf')]

    if missing_ext:

        print(f" [WARNING] {len(missing_ext)} files missing .pdf extension! Files: {[f.name for f in missing_ext]}")

print(f"\nPlanned run directory for this session: {RUN_DIR}")



# ------ [Write pipeline_env.json for ALL further blocks] ------

pipeline_env = dict(

    PROJECT_ROOT   = str(PROJECT_ROOT),

    RUN_ID         = RUN_ID,

    RUN_DIR        = str(RUN_DIR),

    OPERATIONAL_DIR= str(OPERATIONAL_DIR),

    AI_ARTIFACTS_DIR=str(AI_ARTIFACTS_DIR),

    REVIEWER_CONTENT_DIR=str(REVIEWER_CONTENT_DIR),

    METRICS_DIR    = str(METRICS_DIR),

    AUDIT_DIR      = str(AUDIT_DIR),

    ISSUES_DIR     = str(ISSUES_DIR),

    TESTS_DIR      = str(TESTS_DIR)

)

with open("pipeline_env.json", "w") as f:

    json.dump(pipeline_env, f, indent=2)



# ------ [AUDIT LOG: directory/config/corpus state] ------

block2_audit = {

    "step": "block2_dir_and_config_preflight",

    "timestamp_nzdt": NZDT_LABEL,

    "timestamp_utc": UTC_LABEL,

    "env": "colab" if IN_COLAB else "local",

    "project_root": str(PROJECT_ROOT),

    "run_id": RUN_ID,

    "run_dir": str(RUN_DIR),

    "pdf_dir": str(PDF_DIR),

    "n_pdfs": n_pdfs,

    "config_yaml_exists": True,

    "config_yaml_path": str(CONFIG_PATH),

    "corpus_ok": corpus_ok,

    "user_decision": user_choice,

    "warnings": [],

    "errors": []

}

if missing_config and user_choice == "y":

    block2_audit["warnings"].append("User paused to edit just-created config.yaml; rerun required.")

if not corpus_ok:

    block2_audit["errors"].append("PDF directory/corpus unsatisfactory")

audit_log_path = AUDIT_DIR / "block2_dirsetup_preflight.jsonl"

with open(audit_log_path, "a", encoding="utf-8") as f:

    f.write(json.dumps(block2_audit, ensure_ascii=False) + "\n")



if not corpus_ok:

    print("\n[BLOCK 2 TERMINATED: Correct the PDF corpus directory and rerun this block.]\n- No further code will execute in this run.")

    raise SystemExit("Block 2 failed closed: PDF corpus missing/empty.")



print(f"\n[INFO] pipeline_env.json has been written for deterministic use by all future blocks (no search, no prompts).")

print("--- End Block 2 ---")
# @title [Block 2.5] Install & Launch Grobid Server (Colab/Local, NZDT Audit, Progress Bar, v6.2.3)

#

# ----------- [Version 6.2.3] -----------

# v6.1: Colab/local Grobid install/launch/progress, healthcheck

# v6.2: Audit logging, config support, progress bar, reviewer guidance

# v6.2.3: Timestamp/zoneinfo in NZDT + UTC, audit file in correct run dir, provenance-logged status/report.

#

# ----------- [Block Summary] -----------

# - Installs Java/Grobid, builds & launches Grobid server (Colab/local)

# - NZDT and UTC audit log; audit file in correct run folder's audit dir.

# - Progress bar for launch polling. Clear reviewer instructions and provenance trace.

# - Sets envs GROBID_RUNNING, GROBID_URL for all downstream blocks; never fails-closed.

#

# ----------- [Start of Code] -----------

import os, requests, subprocess, time, json

from pathlib import Path

from tqdm import tqdm

import yaml

from datetime import datetime



# --- Timezone for audit-fixity ---

try:

    import zoneinfo

    TZ_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")

    now_nzdt = datetime.now(TZ_NZ)

    NZDT_LABEL = now_nzdt.isoformat()

    UTC_LABEL = datetime.utcnow().isoformat() + "Z"

except Exception:

    TZ_NZ = None

    NZDT_LABEL = "Unavailable"

    UTC_LABEL = datetime.utcnow().isoformat() + "Z"



# -- Load config to get correct audit directory and Grobid URL --

CONFIG_PATH = None

for candidate in [

    Path.cwd() / "operational" / "config.yaml",

    Path.cwd() / "config.yaml",

    Path.cwd().parent / "operational" / "config.yaml"]:

    if candidate.exists():

        CONFIG_PATH = candidate

        break

AUDIT_DIR = Path.cwd() / "audit"

GROBID_URL = "http://localhost:8070/api/processHeaderDocument"

if CONFIG_PATH:

    try:

        with open(CONFIG_PATH, "r") as f:

            config = yaml.safe_load(f)

        GROBID_URL = config.get("grobid_url", GROBID_URL)

        AUDIT_DIR = Path(config.get("audit_dir", AUDIT_DIR))

    except Exception:

        pass  # fallback below

GROBID_HOME = Path("/content/grobid")






audit_record = {

    "step": "block2.5_grobid_setup",

    "timestamp_nzdt": NZDT_LABEL,

    "timestamp_utc": UTC_LABEL,

    "run_cwd": str(Path.cwd()),

    "grobid_url": GROBID_URL,

    "status": None,

    "error": None

}



try:

    print("[Grobid] Installing OpenJDK 11...")

    os.system('apt-get update')

    os.system('apt-get install -y openjdk-11-jdk')

    if not (GROBID_HOME / "gradlew").exists():

        print("[Grobid] Downloading Grobid latest release...")

        subprocess.check_call(['git', 'clone', 'https://github.com/kermitt2/grobid.git', str(GROBID_HOME)])

        subprocess.check_call(['bash', '-c', f'cd {GROBID_HOME} && ./gradlew clean install'])

    print("[Grobid] Starting Grobid server in background...")

    subprocess.Popen(["bash", "-c", f"cd {GROBID_HOME} && ./gradlew run > grobid_run.log 2>&1 &"])



    alive_url = GROBID_URL.replace("/processHeaderDocument", "/isalive")

    ready = False

    print("[Grobid] Waiting for server launch/ready (up to 120s):")

    for i in tqdm(range(12), desc="Waiting for Grobid", ncols=70, bar_format='{l_bar}{bar}| {elapsed} [{remaining}]'):

        if check_grobid_healthy(alive_url):

            print(f"\n[Grobid] Server is UP at {GROBID_URL}")

            ready = True

            break

        time.sleep(10)

    if ready:

        GROBID_RUNNING = True

        audit_record["status"] = "healthy"

        os.environ["GROBID_RUNNING"] = "1"

    else:

        print("[WARNING] Grobid server did not start in time. Extraction will use fallback methods only.")

        GROBID_RUNNING = False

        audit_record["status"] = "not_responding"

        os.environ["GROBID_RUNNING"] = "0"

except Exception as e:

    print(f"[ERROR] Grobid setup failed: {e}")

    GROBID_RUNNING = False

    audit_record["status"] = "setup_error"

    audit_record["error"] = str(e)

    os.environ["GROBID_RUNNING"] = "0"

os.environ["GROBID_URL"] = GROBID_URL



# -- Audit log --

AUDIT_DIR.mkdir(exist_ok=True, parents=True)

with open(AUDIT_DIR / "block2p5_grobid_setup.jsonl", "a", encoding="utf-8") as f:

    f.write(json.dumps(audit_record, ensure_ascii=False) + "\n")



print(f"\n[GROBID_RUNNING={os.environ['GROBID_RUNNING']}] (0 = unavailable, 1 = running)\nGROBID_URL={os.environ['GROBID_URL']}")

print("--- End Block 2.5 ---")
# @title [Block 3] Forensic Metadata Extraction - DOI, LLM, Non-LLM (v6.3.2)

# Version 6.3.2

# --------- [Version Control] ---------

# v6.0: Multi-source extraction and manifest voting in one block (fitz, pdfplumber, GROBID, CrossRef, OpenAlex, filename, LLM).

# v6.1: LLM-based metadata, review-needed flag, fuzzy matching for missing/ambiguous fields.

# v6.2: Added consensus logic, CrossRef/OpenAlex normalization, audit trail, reviewer trace.

# v6.2.4: Added extended fields (author_keywords, country, source_journal, study_type), audit-ready outputs.

# v6.3.0: Major refactor – forensic extraction only, raw outputs and audit, no voting.

# v6.3.1: Consistent IDs, match analytics, all outputs audit/stable.

# v6.3.2: [NEW] - IDs as paper_ID_xxxxx, file_name fully removed, all tables by ID only.

#       - LLM and non-LLM field results truly populated (no blanket 0s), each table is fresh wide-form (columns=fields).

#       - Direct forensics: all results, hashes, and error-trace in output.

#

# Block Summary:

# - Each PDF gets a unique, persistent deterministic ID of form paper_ID_xxxxx

# - No file_name in any table (reviewer-safe auditing).

# - Every table is indexed by ID, fields presented as separate columns per method.

# - Table 1: DOI extraction method success (summary count per method)

# - Table 2: DOI by ID/method

# - Table 3: LLM metadata extraction, rows=ID, columns=per-field

# - Table 4: Not-found counts per non-LLM method/field

# - Table 5: # of fields per non-LLM method that perfectly match LLM

# - Table 6: # of fields per non-LLM method that approximately match LLM

# - All outputs hashed, audit-logged, fully ready for downstream Block 4 aggregation.



import os, re, fitz, pdfplumber, requests, json, datetime, yaml, string, hashlib

from pathlib import Path

import pandas as pd



# === Setup

with open("pipeline_env.json", "r") as f: env = json.load(f)

OP_DIR = Path(env["OPERATIONAL_DIR"])

CONFIG_PATH = OP_DIR / "config.yaml"

with open(CONFIG_PATH, "r") as f: config = yaml.safe_load(f)

PDF_DIR = Path(config["pdf_dir"])

pdfs = sorted(PDF_DIR.glob("*.pdf"))[:5]  # FAST TEST



grobid_url = config.get("grobid_url", "http://localhost:8070/api/processHeaderDocument")

OPENAI_API_KEY = os.environ.get(config.get("openai_key_envvar", "OPENAI_API_KEY"), "")

llm_model = config.get("llm_model")

fields = [

    "title", "author", "year", "doi",

    "author_keywords", "country", "source_journal", "study_type"

]

non_llm_methods = ["grobid", "fitz", "pdfplumber", "filename", "crossref", "openalex"]

doi_methods = ["fitz", "pdfplumber", "grobid", "filename", "llm"]






try:

    import zoneinfo

    NZDT_LABEL = str(datetime.datetime.now(zoneinfo.ZoneInfo("Pacific/Auckland")))

except Exception:

    NZDT_LABEL = datetime.datetime.now().isoformat()

UTC_LABEL = datetime.datetime.utcnow().isoformat() + "Z"

print(f"========= BLOCK 3 Forensic Extraction {NZDT_LABEL} =========")




def clean_str(txt):

    return "".join(c for c in str(txt or "").lower() if c.isalnum() or c.isspace()).replace(" ","")



def approx_match(a, b, field):

    if (a is None or b is None): return False

    if field == "doi":

        return normalize_doi(a) == normalize_doi(b)

    if field in ["author_keywords"]:

        sa = sorted({x.strip() for x in str(a).replace(";"," ").replace(","," ").lower().split() if x})

        sb = sorted({x.strip() for x in str(b).replace(";"," ").replace(","," ").lower().split() if x})

        return sa == sb

    return clean_str(a) == clean_str(b)



# --- Extraction primitives (lightweight: robust, not comprehensive parsers)

def extract_first_page_text(pdf_file):

    try: doc = fitz.open(pdf_file); return doc[0].get_text()[:3000]

    except Exception: return ""



def extract_fitz_metadata(pdf_file):

    meta = {f:"" for f in fields}

    try:

        doc = fitz.open(pdf_file)

        m = doc.metadata

        meta["title"] = m.get("title", "") or m.get("Title", "")

        meta["author"] = m.get("author", "") or m.get("Author", "")

        meta["year"] = str(m.get("modDate", "")[2:6]) if m.get("modDate", "") else ""

    except Exception: pass

    meta["doi"] = ""  # Will populate via function below

    return meta



def extract_pdfplumber_metadata(pdf_file):

    meta = {f:"" for f in fields}

    try:

        with pdfplumber.open(pdf_file) as p:

            info = p.metadata or {}

            meta["title"] = info.get("Title", "")

            meta["author"] = info.get("Author", "")

            meta["year"] = info.get("ModDate", "")[2:6] if info.get("ModDate","") else ""

            meta["author_keywords"] = info.get("Keywords", "")

    except Exception: pass

    meta["doi"] = ""  # Will populate via function below

    return meta



def extract_filename_metadata(fname):

    # Example: "Author et al. - 2024 - Title.pdf"

    meta = {f:"" for f in fields}

    base = Path(fname).stem

    m = re.match(r"(.+?)\s*-\s*(\d{4})\s*-\s*(.+)", base)

    if m:

        meta["author"], meta["year"], meta["title"] = m.groups()

    return meta



def extract_fitz_pdfplumber_doi(pdf_file):

    # Try fitz, then pdfplumber for DOI in document metadata

    try:

        doc = fitz.open(pdf_file)

        for v in doc.metadata.values():

            if v and '10.' in str(v):

                doi = re.search(r"(10\.\d{4,9}/[\w\.\-\/]+)", str(v))

                if doi: return normalize_doi(doi.group(1))

    except Exception: pass

    try:

        with pdfplumber.open(pdf_file) as p:

            info = p.metadata or {}

            for v in info.values():

                if v and '10.' in str(v):

                    doi = re.search(r"(10\.\d{4,9}/[\w\.\-\/]+)", str(v))

                    if doi: return normalize_doi(doi.group(1))

    except Exception: pass

    return ""



def extract_grobid_full(pdf_file):

    # Try GROBID, return dict for all fields

    meta = {f:"" for f in fields}

    try:

        with open(pdf_file, "rb") as f:

            resp = requests.post(grobid_url, files={'input': f})

            tei = resp.text

        # Minimal TEI regexes; for robust production use XML parsing!

        title = re.search(r"<title\b[^>]*>(.*?)</title>", tei, flags=re.DOTALL)

        author = re.search(r"<persName[^>]*>.*?<forename[^>]*>(.*?)</forename>(?:.*?<forename.*?>(.*?)</forename>)?.*?<surname[^>]*>(.*?)</surname>.*?</persName>", tei, flags=re.DOTALL)

        year = re.search(r"<date\b[^>]*when=\"(\d{4})", tei)

        doi = re.search(r"<idno type=\"DOI\">(.*?)</idno>", tei)

        keywords = re.findall(r"<keyword[^>]*>(.*?)</keyword>", tei, flags=re.DOTALL)

        affiliations = re.findall(r"<affiliation.*?><orgName[^>]*?>(.*?)</orgName>.*?<country[^>]*?>(.*?)</country>", tei, flags=re.DOTALL)

        journal = re.search(r"<title level=\"j\">(.*?)</title>", tei)

        meta["title"] = title.group(1).strip() if title else ""

        meta["author"] = " ".join(x.strip() for x in author.groups() if x) if author else ""

        meta["year"] = year.group(1) if year else ""

        meta["doi"] = normalize_doi(doi.group(1)) if doi else ""

        meta["author_keywords"] = ";".join([k.strip() for k in keywords])

        meta["country"] = affiliations[0][1].strip() if affiliations else ""

        meta["source_journal"] = journal.group(1).strip() if journal else ""

    except Exception: pass

    return meta



def extract_from_filename_doi(fname):

    m = re.search(r"(10\.\d{4,9}/[\w\.\-\/]+)", fname)

    return normalize_doi(m.group(1)) if m else ""



def extract_crossref_full(doi, title=None):

    meta = {f:"" for f in fields}

    try:

        url = f"https://api.crossref.org/works/{normalize_doi(doi)}" if doi else None

        if url:

            r = requests.get(url); dat = r.json()["message"]

        elif title:

            r = requests.get(f"https://api.crossref.org/works?query.title={title}&rows=1")

            items = r.json()["message"].get("items", [])

            dat = items[0] if items else {}

        else: dat = {}

        meta["doi"] = normalize_doi(dat.get("DOI", ""))

        meta["title"] = dat.get("title", [""])[0]

        if dat.get("author"):

            meta["author"] = "; ".join("{}, {}".format(

                a.get("family","").strip(), a.get("given","").strip()

            ) for a in dat.get("author"))

            meta["country"] = "; ".join([aff.get("name","") for a in dat["author"] for aff in a.get("affiliation",[])]).strip()

        meta["year"] = str(dat.get("issued",{}).get("date-parts", [[None]])[0][0]) if dat.get("issued") else ""

        meta["author_keywords"] = ";".join(dat.get("subject", [])) if dat.get("subject") else ""

        meta["source_journal"] = dat.get("container-title", [""])[0] if dat.get("container-title") else ""

        meta["study_type"] = dat.get("type", "")

    except Exception: pass

    return meta



def extract_openalex_full(doi, title=None):

    meta = {f:"" for f in fields}

    try:

        url = f"https://api.openalex.org/works/https://doi.org/{normalize_doi(doi)}" if doi else None

        if url:

            r = requests.get(url)

            dat = r.json()

        elif title:

            url = f"https://api.openalex.org/works?title.search={title}"

            r = requests.get(url)

            dat = r.json().get("results", [{}])[0] if "results" in r.json() else r.json()

        else: dat = {}

        doi_val = dat.get("doi", "")

        if doi_val.startswith("https://doi.org/"):

            doi_val = doi_val[len("https://doi.org/") :]

        meta["doi"] = normalize_doi(doi_val)

        meta["title"] = dat.get("title", "")

        meta["author"] = "; ".join(a.get("author",{}).get("display_name","") for a in dat.get("authorships",[]))

        meta["year"] = str(dat.get("publication_year", ""))

        meta["author_keywords"] = ";".join(dat.get("keywords", [])) if dat.get("keywords") else ""

        meta["source_journal"] = dat.get("host_venue", {}).get("display_name","") if dat.get("host_venue") else ""

        meta["study_type"] = dat.get("type", "")

        # no explicit country, but can try from institutions

        meta["country"] = "; ".join(inst.get("country_code","") for auth in dat.get("authorships",[]) for inst in auth.get("institutions",[]))

    except Exception: pass

    return meta



def extract_ai_llm_doi_only(first_page, api_key=None, model=None):

    api_key = api_key or OPENAI_API_KEY

    prompt = (

        "Extract only the DOI (Digital Object Identifier) from the following text. If none is found, return an empty JSON.\n"

        f"Text:\n{first_page}"

    )

    if not api_key: return ""

    try:

        import openai

        resp = openai.chat.completions.create(

            model=model or llm_model,

            messages=[{"role":"user", "content": prompt}],

            temperature=0, max_tokens=24

        )

        txt = resp.choices[0].message.content.strip()

        if txt.startswith("```"): txt = txt.strip("` \n"); txt = txt[4:].strip() if txt.startswith("json") else txt

        result = json.loads(txt)

        return result.get('doi', '') if isinstance(result, dict) else result

    except Exception as e:

        print("LLM_DOI ERROR:", e)

        return ""



def extract_ai_llm_full(first_page, api_key=None, model=None):

    api_key = api_key or OPENAI_API_KEY

    prompt = (

        "Extract the following metadata as a JSON object from the text provided: title, author, year, doi, "

        "author_keywords, country, source_journal, study_type. "

        "If a field is missing, leave blank or use null. Text follows:\n" + first_page

    )

    if not api_key: return {k:"" for k in fields}

    try:

        import openai

        resp = openai.chat.completions.create(

            model=model or llm_model,

            messages=[{"role":"user", "content": prompt}],

            temperature=0, max_tokens=384

        )

        txt = resp.choices[0].message.content.strip()

        if txt.startswith("```"): txt = txt.strip("` \n"); txt = txt[4:].strip() if txt.startswith("json") else txt

        result = json.loads(txt)

        return {k: result.get(k, "") for k in fields}

    except Exception as e:

        print("LLM_FULL ERROR:", e)

        return {k:"" for k in fields}



# ---- Step 1: DOI Extraction All Methods ----

rows_doi = []

table_1_counts = {m: 0 for m in doi_methods}

for pdf in pdfs:

    pdf_id = pdf_hash_id(pdf)

    firstpage = extract_first_page_text(pdf)

    doi_fitz = extract_fitz_pdfplumber_doi(pdf)

    doi_pdfplumber = doi_fitz

    doi_grobid = extract_grobid_full(pdf)["doi"]

    doi_filename = extract_from_filename_doi(pdf.name)

    doi_llm = extract_ai_llm_doi_only(firstpage)

    row = [pdf_id, doi_fitz, doi_pdfplumber, doi_grobid, doi_filename, doi_llm]

    for i, val in enumerate(row[1:]):

        if val: table_1_counts[doi_methods[i]] += 1

    rows_doi.append(row)

print("\n--- Table 1: DOI Extraction Method Success Count (n_papers) ---")

for m in doi_methods:

    print(f"{m:12}: {table_1_counts[m]}")

df_doi = pd.DataFrame(rows_doi, columns=["pdf_id"] + doi_methods)

print("\n--- Table 2: DOI by PDF by Method ---")

print(df_doi.to_string(index=False, max_colwidth=36))



# ---- Step 2: LLM Metadata Extraction ----

rows_llm = []

for pdf in pdfs:

    pdf_id = pdf_hash_id(pdf)

    firstpage = extract_first_page_text(pdf)

    llm_out = extract_ai_llm_full(firstpage)

    rows_llm.append([pdf_id] + [llm_out.get(k, "") for k in fields])

df_llm = pd.DataFrame(rows_llm, columns=["pdf_id"] + fields)

print("\n--- Table 3: LLM Metadata Extraction ---")

print(df_llm.to_string(index=False, max_colwidth=42))



# ---- Step 3: Non-LLM Extraction All Fields ----

rows_nonllm = []

notfound_matrix = {meth: {field: 0 for field in fields} for meth in non_llm_methods}

for pdf in pdfs:

    pdf_id = pdf_hash_id(pdf)

    firstpage = extract_first_page_text(pdf)

    fitz_m = extract_fitz_metadata(pdf); fitz_m["doi"] = extract_fitz_pdfplumber_doi(pdf)

    pdfplumber_m = extract_pdfplumber_metadata(pdf); pdfplumber_m["doi"] = extract_fitz_pdfplumber_doi(pdf)

    filename_m = extract_filename_metadata(pdf.name); filename_m["doi"] = extract_from_filename_doi(pdf.name)

    grobid_m = extract_grobid_full(pdf)

    # Select best DOI for APIs; prefer LLM or as found in Step 1

    doi_to_use = ""

    for meth in reversed(doi_methods):

        d = df_doi[df_doi["pdf_id"]==pdf_id][meth].values[0]

        if d: doi_to_use = d; break

    # Fallback: title from LLM if needed

    title_to_use = df_llm[df_llm["pdf_id"]==pdf_id]["title"].values[0]

    crossref_m = extract_crossref_full(doi_to_use, title_to_use)

    openalex_m = extract_openalex_full(doi_to_use, title_to_use)

    method_dict = {

        "grobid"    : grobid_m,

        "fitz"      : fitz_m,

        "pdfplumber": pdfplumber_m,

        "filename"  : filename_m,

        "crossref"  : crossref_m,

        "openalex"  : openalex_m

    }

    row = [pdf_id]

    for m in non_llm_methods:

        mdata = method_dict[m]

        for f in fields:

            val = mdata.get(f, "")

            row.append(val)

            if not val:

                notfound_matrix[m][f] += 1

    rows_nonllm.append(row)

method_field_cols = [f"{meth}_{field}" for meth in non_llm_methods for field in fields]

df_nonllm = pd.DataFrame(rows_nonllm, columns=["pdf_id"] + method_field_cols)

print("\n--- Table 4: Not-Found Extraction Counts (non-LLM methods, # missings, method x field) ---")

print(pd.DataFrame(notfound_matrix).T)



# ---- Table 5/6: Matching to LLM ----

perfect_match = {meth: {f:0 for f in fields} for meth in non_llm_methods}

approx_match_count = {meth: {f:0 for f in fields} for meth in non_llm_methods}

for i, pdf in enumerate(pdfs):

    pdf_id = pdf_hash_id(pdf)

    llm_row = df_llm[df_llm["pdf_id"] == pdf_id]

    for im, meth in enumerate(non_llm_methods):

        for j, f in enumerate(fields):

            nonllm_val = df_nonllm.loc[i, f"{meth}_{f}"]

            llm_val = llm_row.iloc[0][f] if f in llm_row else ""

            if nonllm_val == llm_val and nonllm_val != "":

                perfect_match[meth][f] += 1

            elif approx_match(nonllm_val, llm_val, f) and nonllm_val != "":

                approx_match_count[meth][f] += 1

print("\n--- Table 5: # of Exact Matches to LLM (method × field) ---")

pm_df = pd.DataFrame(perfect_match).T

print(pm_df)

print("\n--- Table 6: # of Approximate Matches to LLM (method × field) ---")

am_df = pd.DataFrame(approx_match_count).T

print(am_df)






csvs = {

    "doi": OP_DIR / "block3_doi_result.csv",

    "llm": OP_DIR / "block3_llm_result.csv",

    "nonllm": OP_DIR / "block3_nonllm_result.csv",

    "pm": OP_DIR / "block3_perfect_match.csv",

    "am": OP_DIR / "block3_approx_match.csv"

}



df_doi.to_csv(csvs["doi"], index=False)

df_llm.to_csv(csvs["llm"], index=False)

df_nonllm.to_csv(csvs["nonllm"], index=False)

pm_df.to_csv(csvs["pm"])

am_df.to_csv(csvs["am"])



auditlog = {

    "step": "block3_extraction",

    "timestamp_utc": UTC_LABEL,

    "timestamp_nzdt": NZDT_LABEL,

    "output_files": {k: str(v) for k,v in csvs.items()},

    "csv_hashes": {k: sha256_file(v) for k,v in csvs.items()}

}

with open(OP_DIR / "block3_auditlog.json", "a") as f:

    f.write(json.dumps(auditlog)+"\n")



print("--- End Block 3: Forensic extraction/LLM matching complete. Outputs saved. ---")
# @title [Block 3 LLM Extraction Debug] Forensic LLM Metadata Extraction Test – Colab Userdata API

import fitz, json, hashlib

from pathlib import Path

from google.colab import userdata



with open("pipeline_env.json", "r") as f: env = json.load(f)

OP_DIR = Path(env["OPERATIONAL_DIR"])

CONFIG_PATH = OP_DIR / "config.yaml"

with open(CONFIG_PATH, "r") as f: config = yaml.safe_load(f)

PDF_DIR = Path(config["pdf_dir"])

pdfs = sorted(PDF_DIR.glob("*.pdf"))[:5]  # Adjust as needed



api_key = userdata.get('OPENAI_API_KEY')

if not api_key:

    print("ERROR: No OpenAI API key found in Colab userdata. Please set one using:\n"

          "from google.colab import userdata\n"

          "userdata.set_secret('OPENAI_API_KEY')")

llm_model = config.get("llm_model")

fields = [

    "title", "author", "year", "doi",

    "author_keywords", "country", "source_journal", "study_type"

]






def extract_first_page_text(pdf_file):

    try:

        doc = fitz.open(pdf_file)

        return doc[0].get_text()[:3000]

    except Exception as e:

        print(f"[{pdf_file.name}] ERROR extract_first_page_text:", e)

        return ""



def extract_ai_llm_full(first_page, api_key=None, model=None):

    prompt = (

        "Extract the following metadata as a JSON object from the text provided: title, author, year, doi, "

        "author_keywords, country, source_journal, study_type. "

        "If a field is missing, leave blank or use null. Text follows:\n" + first_page

    )

    if not api_key:

        print("--> NO API KEY SET IN COLAB USERDATA!")

        return {k:"" for k in fields}

    try:

        import openai

        resp = openai.chat.completions.create(

            model=model or llm_model,

            api_key=api_key,

            messages=[{"role":"user", "content": prompt}],

            temperature=0, max_tokens=384

        )

        txt = resp.choices[0].message.content.strip()

        print("[RAW LLM RETURN]:", txt[:300])

        if txt.startswith("```"):

            txt = txt.strip("` \n"); txt = txt[4:].strip() if txt.startswith("json") else txt

        result = json.loads(txt)

        return result if isinstance(result, dict) else {}

    except Exception as e:

        print("[LLM ERROR]:", e)

        return {k:"" for k in fields}



print("========== LLM Extraction Debug Block (Colab Userdata) ==========")

for pdf in pdfs:

    pdf_id = pdf_hash_id(pdf)

    print(f"\n--- PDF {pdf_id} ---")

    page1 = extract_first_page_text(pdf)

    print("[First Page Text Preview]:", repr(page1[:250]))

    llm_result = extract_ai_llm_full(page1, api_key=api_key)

    print("[LLM Structured Result]:", json.dumps(llm_result, indent=2))

    for k in fields:

        print(f"   {k:17}: {llm_result.get(k, '')}")

print("========== End of LLM Extraction Debug ==========")
# @title [Block 4] Reviewer QA, Correction, Approval of Manifest (v6.2.2)

#

# ----------- [Block Summary] -----------

# - Loads extraction_manifest.csv and ensures all *_votes columns present.

# - Prints flagged summary and requires reviewer name/custody.

# - Field-by-field correction modal, manual/choice, audit-logs output.

# - Outputs final locked manifest, reviewer log, agreement matrix.

# - All outputs are hash-logged for audit/forensic fixity.

#

# ----------- [Version Control] -----------

# v6.2.1: Robust *_votes handling, audit hashing, custody modal, reviewer workflow robust for PI/QA use.

# v6.2.2: Reviewer QA, Autofix, Correction, & Submission Approval

#

# ----------- [Block Summary] -----------

# - Loads extraction_manifest.csv, parses *_votes JSON

# - Auto-confirms a field if ≥2 non-missing sources match LLM (lenient for title/author)

# - For title/author: uses fuzzy normalization for consensus (OpenAlex/CrossRef selected if close to LLM)

# - Prompts reviewer only on non-consensus fields

# - At end, prints and requests reviewer “Ready to submit?” approval

# - All outputs hash-logged, custody and audit tracked



import json, pandas as pd, datetime, hashlib

from pathlib import Path

from collections import Counter



from difflib import SequenceMatcher






def norm_str(x):

    """ Normalize a string for lenient matching: lowercase, strip, no punct, no space """

    import re

    return re.sub(r"[\s\W_]+", "", str(x or "").lower())



def fuzzy_ratio(a, b):

    """ Return difflib ratio between two strings (0-100) """

    return int(SequenceMatcher(None, str(a or ""), str(b or "")).ratio() * 100)



with open("pipeline_env.json", "r") as f:

    env = json.load(f)

OPERATIONAL_DIR = Path(env["OPERATIONAL_DIR"])

EXTRACTION_PATH = OPERATIONAL_DIR / "extraction_manifest.csv"

REVIEW_LOG_PATH = OPERATIONAL_DIR / "review_correction_log.json"

FINAL_MANIFEST_PATH = OPERATIONAL_DIR / "final_manifest.csv"

AUDIT_PATH = OPERATIONAL_DIR / "reviewer_block4_audit.jsonl"



fields = ["title", "author", "year", "doi"]

methods = ["llm_raw", "grobid", "fitz", "crossref", "openalex", "filename"]



def robust_json_parse(val):

    if isinstance(val, dict): return val

    if pd.isna(val) or str(val).strip() in ["", "{}", "nan", "None"]:

        return {m:"" for m in methods}

    try:

        js = json.loads(val)

        if not isinstance(js, dict): return {m:"" for m in methods}

        for m in methods:

            js.setdefault(m, "")

        return js

    except Exception:

        try:

            import ast

            js = ast.literal_eval(val)

            return dict(js) if isinstance(js, dict) else {m:"" for m in methods}

        except Exception:

            return {m:"" for m in methods}



df = pd.read_csv(EXTRACTION_PATH)

for field in fields:

    col = f"{field}_votes"

    if col not in df.columns:

        df[col] = [{m:"" for m in methods} for _ in range(len(df))]

    else:

        df[col] = df[col].apply(robust_json_parse)



# -------- Consensus/Autofix Step --------------

autofix_counter = Counter()

needs_manual_idx = []

for idx, row in df.iterrows():

    auto_decided = {}

    for field in fields:

        votes = row.get(f"{field}_votes", {m:"" for m in methods}).copy()

        values = [v for v in votes.values() if v and v != "[Missing]"]

        llm_val = votes.get("llm_raw", "")

        nonblank = [m for m in methods if votes[m] and votes[m] != "[Missing]"]



        # Helper: Fuzzy or strict match

        def close_enough(a, b, field):

            if not a or not b: return False

            if field in ["title", "author"]:

                if norm_str(a) == norm_str(b): return True

                return fuzzy_ratio(a, b) >= (88 if field == "title" else 82) # tunable

            else:

                return str(a).strip().lower() == str(b).strip().lower()



        # For author/title, check if OpenAlex or CrossRef is "close" to LLM

        preferred_raw = None

        for m in ["openalex", "crossref"]:

            if close_enough(votes.get("llm_raw", ""), votes.get(m, ""), field):

                preferred_raw = votes[m]

                break



        # Consensus: ≥2 methods "close enough" to LLM and non-missing OR LLM+OpenAlex/CrossRef is close

        match_methods = [m for m in methods if close_enough(llm_val, votes[m], field)]

        n_matches = len([k for k in match_methods if votes[k]])



        # Ignore filename/fitz if only partial or non-informative (skip as consensus candidates for title/author)

        valid_compare_methods = [m for m in methods if m != "filename" and votes[m]]



        if field in ["title", "author"]:

            # More aggressive autofix for noisy fields

            if preferred_raw:

                df.loc[idx, f"{field}_final"] = preferred_raw

                df.loc[idx, f"{field}_src"] = "openalex/crossref"

                auto_decided[field] = True

                autofix_counter[field] += 1

                continue

            if n_matches >= 2 and set(match_methods).intersection(set(valid_compare_methods)):

                df.loc[idx, f"{field}_final"] = llm_val

                df.loc[idx, f"{field}_src"] = "llm_raw"

                auto_decided[field] = True

                autofix_counter[field] += 1

                continue

        else:

            if n_matches >= 2:

                df.loc[idx, f"{field}_final"] = llm_val

                df.loc[idx, f"{field}_src"] = "llm_raw"

                auto_decided[field] = True

                autofix_counter[field] += 1

                continue



        # If only one non-missing value, auto-select

        if len(nonblank) == 1:

            df.loc[idx, f"{field}_final"] = votes[nonblank[0]]

            df.loc[idx, f"{field}_src"] = nonblank[0]

            auto_decided[field] = True

            autofix_counter[field] += 1

            continue



        # Too ambiguous or no close match—needs reviewer

        if not auto_decided.get(field, False):

            needs_manual_idx.append((idx, field))



# Second pass: Flag only fields needing review

needs_review = set([idx for idx, f in needs_manual_idx])

df["needs_review"] = df.index.isin(needs_review)

df["review_reason"] = ""

for idx in range(len(df)):

    missing = [f for f in fields if (idx, f) in needs_manual_idx]

    df.loc[idx, "review_reason"] = ";".join(f"{f}_disagree_or_missing" for f in missing)



# --------- Table 2a: Reviewer Correction Summary -----------

print("\n--- Table 2a: Reviewer Correction Summary (AFTER AUTOFIX) ---")

needreview = df[df["needs_review"] == True]

reason_counter = Counter()

for _, row in needreview.iterrows():

    for reason in str(row.get("review_reason", "")).split(";"):

        if reason.strip():

            reason_counter[reason.split("_")[0]] += 1

for f in fields:

    print(f"{f:8}: {reason_counter.get(f,0)} flagged (manual review needed)")

print(f"{len(needreview)} papers to review (out of {len(df)})")

print(f"Autofixed fields breakdown: {dict(autofix_counter)}")



# ----------- Reviewer name/custody modal --------------

reviewer_name = None

while not reviewer_name or len(reviewer_name.strip()) < 2:

    reviewer_name = input("\nPlease TYPE YOUR FULL NAME for manifest lock (for audit):\n> ").strip()



result_decision = input(

    "\nDo you wish to review/correct flagged fields now? [Y/N]: "

).lower().strip()

corrections = []



if result_decision == "y" and len(needreview):

    print("\n--- Reviewer Correction: Step through flagged fields ---")

    for idx, row in needreview.iterrows():

        pdf_id = row["pdf_id"]

        for field in fields:

            if f"{field}_disagree_or_missing" not in str(row.get("review_reason", "")):

                continue

            votes = row.get(f"{field}_votes", {m:"" for m in methods})

            print(f"\n[REVIEW] pdf_id: {pdf_id} | FIELD: {field.upper()} | flagged: {row.get('review_reason','')}")

            for i, method in enumerate(methods):

                val_disp = votes.get(method, "") if votes.get(method, "") else "[Missing]"

                print(f"[{chr(65+i)}] {method:<9}: {val_disp}")

            sel = input(f"Choose value for {field} (A-{chr(65+len(methods)-1)}) or type MANUAL: ").strip()

            if sel.lower() == "manual":

                val = input(f"Manual value for {field}: ").strip()

                df.loc[idx, f"{field}_final"] = val

                df.loc[idx, f"{field}_src"] = "manual"

                corrections.append(

                    {"pdf_id": pdf_id, "field": field, "chosen": val, "src": "manual", "reviewer": reviewer_name}

                )

            elif len(sel) == 1 and chr(65) <= sel.upper() < chr(65+len(methods)):

                chosen_method = methods[ord(sel.upper()) - 65]

                val = votes.get(chosen_method, "")

                df.loc[idx, f"{field}_final"] = val

                df.loc[idx, f"{field}_src"] = chosen_method

                corrections.append(

                    {"pdf_id": pdf_id, "field": field, "chosen": val, "src": chosen_method, "reviewer": reviewer_name}

                )

    print("\n[Reviewer correction input complete.]")

else:

    print("\nNo manual review required or corrections skipped.")



# --------- Final Manifest Summary & Ready-to-Submit Step -----------

print("\n--- SUMMARY: Final Manifest Table (LOCKED after Review) ---")

finalcols = ["pdf_id"] + [f"{field}_final" for field in fields] + ["needs_review", "review_reason"]

print(df[finalcols].to_string(index=False, max_colwidth=48))

print("\nCOUNT SUMMARY by FIELD source:")

for field in fields:

    sources = Counter([str(row.get(f"{field}_src", "")) for _, row in df.iterrows()])

    print(f"{field:8}: {dict(sources)}")



final_approve = input("\n[REVIEWER FINAL CHECK] Submit this manifest as LOCKED for submission? [Y/N]: ").lower().strip()

if final_approve != "y":

    print("Lock/review decision withheld. No submission flagged. Please rerun this after changes if needed.")

else:

    print("Manifest approved by reviewer for submission. Manifest is now LOCKED in audit log.")



# ---------- Table 5: Extraction Source-Field Agreement Matrix --------

print("\n--- Table 5: Extraction Source-Field Agreement Matrix ---")

method_counts = pd.DataFrame(0, index=fields, columns=methods)

for idx, row in df.iterrows():

    for field in fields:

        src = str(row.get(f"{field}_src", "")).lower()

        if src in method_counts.columns:

            method_counts.at[field, src] += 1

print(method_counts.to_string())



# ------------- Write reviewer-locked manifest/log (hash-logged) -------------

df.to_csv(FINAL_MANIFEST_PATH, index=False)

with open(REVIEW_LOG_PATH, "w") as f:

    json.dump({

        "reviewer": reviewer_name,

        "timestamp_utc": str(datetime.datetime.utcnow()) + "Z",

        "timestamp_nzdt": str(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=12))),),

        "changes": corrections,

        "final_approved": final_approve == "y"

    }, f, indent=2)



out_hashes = {

    "final_manifest.csv.sha256": sha256_file(FINAL_MANIFEST_PATH),

    "review_correction_log.json.sha256": sha256_file(REVIEW_LOG_PATH)

}

for out, hashv in out_hashes.items():

    with open(OPERATIONAL_DIR / out, "w") as f:

        f.write(hashv or "")



# Minimal audit log

with open(AUDIT_PATH, "a") as f:

    f.write(json.dumps({

        "step": "block4_reviewer_approval",

        "timestamp_utc": str(datetime.datetime.utcnow()) + "Z",

        "timestamp_nzdt": str(datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=12))),),

        "outputs": {k: str(OPERATIONAL_DIR / k) for k in out_hashes},

        "hashes": out_hashes,

        "reviewer": reviewer_name,

        "final_approved": final_approve == "y"

    }) + "\n")



print(f"\n[Final manifest saved to {FINAL_MANIFEST_PATH}]")

print("[Review correction log saved to review_correction_log.json]")

print(f"[SHA256 hashes written for outputs. Audit log updated at: {AUDIT_PATH}]")

print("--- End Block 4 ---")
