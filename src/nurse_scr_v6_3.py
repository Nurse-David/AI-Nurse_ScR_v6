# --- Cell ---
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
def sha256_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def write_audit_log(data, path="audit/block1_env_fingerprint.jsonl"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

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

# --- Cell ---
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
    'allow_internet': True,
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

# --- Cell ---
# @title [Block 2.5] Install & Launch Grobid Server (Colab/Local, NZDT Audit, Progress Bar, v6.3.1)
#
# ----------- [Version Control] -----------
# v6.1: Colab/local Grobid install/launch/progress, healthcheck
# v6.2: Audit logging, config support, progress bar, reviewer guidance
# v6.2.3: Timestamp/zoneinfo in NZDT + UTC, audit file in correct run dir, provenance-logged status/report.
# Version 6.3.1 – Checks, autorestarts, clear logs, NZ English
#
# ----------- [Block Summary] -----------
# - Installs Java/Grobid, builds & launches Grobid server (Colab/local)
# - NZDT and UTC audit log; audit file in correct run folder's audit dir.
# - Progress bar for launch polling. Clear reviewer instructions and provenance trace.
# - Sets envs GROBID_RUNNING, GROBID_URL for all downstream blocks; never fails-closed.
#
# ----------- [Start of Code] -----------


import os, subprocess, time, requests, signal, json
from pathlib import Path
import yaml
from datetime import datetime
from tqdm import tqdm

# --- Audit/Config ---
try:
    import zoneinfo
    TZ_NZ = zoneinfo.ZoneInfo("Pacific/Auckland")
    now_nzdt = datetime.now(TZ_NZ).isoformat()
    now_utc = datetime.utcnow().isoformat() + "Z"
except Exception:
    now_nzdt = datetime.utcnow().isoformat()
    now_utc  = datetime.utcnow().isoformat() + "Z"

# Find config and audit directories
CONFIG_PATH = None
for candidate in [
    Path.cwd() / "operational" / "config.yaml",
    Path.cwd() / "config.yaml",
    Path.cwd().parent / "operational" / "config.yaml"]:
    if candidate.exists():
        CONFIG_PATH = candidate
        break

GROBID_HOME = Path("/content/grobid")
GROBID_URL  = "http://localhost:8070/api/processHeaderDocument"
AUDIT_DIR   = Path("audit")
if CONFIG_PATH:
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
            GROBID_URL = config.get("grobid_url", GROBID_URL)
            AUDIT_DIR = Path(config.get("audit_dir", AUDIT_DIR))
    except Exception: pass
AUDIT_DIR.mkdir(exist_ok=True, parents=True)
HEALTH_URL = GROBID_URL.replace("/processHeaderDocument", "/isalive")

def log(msg):
    print(msg)
    with open(AUDIT_DIR / "block2p5_grobid_status.txt", "a") as f:
        f.write(str(msg) + "\n")

def check_grobid_healthy(url=HEALTH_URL):
    try:
        r = requests.get(url, timeout=8)
        return (r.status_code == 200) and ("grobid" in r.text.lower() or "true" in r.text.lower())
    except Exception:
        return False

def kill_grobid(port=8070):
    # On Colab/Unix: kill process on the port if one exists
    try:
        out = subprocess.check_output(f"lsof -i:{port} -t", shell=True).decode().strip().split()
        for pid in out:
            os.kill(int(pid), signal.SIGKILL)
            log(f"[INFO] Killed previous process on port {port} (pid {pid})")
    except Exception:
        pass

status_record = {
    "step": "block2.5_grobid_setup",
    "timestamp_nzdt": now_nzdt,
    "timestamp_utc": now_utc,
    "grobid_url": GROBID_URL,
    "already_installed": False,
    "already_running": False,
    "server_start_attempted": False,
    "error": None
}

# Step 1: Check for Grobid folder and try to check/rerun the server as needed
try:
    if not (GROBID_HOME / "gradlew").exists():
        # Need to install Grobid
        log("[Grobid] Installing OpenJDK 11 and cloning Grobid...")
        os.system('apt-get update')
        os.system('apt-get install -y openjdk-11-jdk')
        subprocess.check_call(['git', 'clone', 'https://github.com/kermitt2/grobid.git', str(GROBID_HOME)])
        subprocess.check_call(['bash', '-c', f'cd {GROBID_HOME} && ./gradlew clean install'])
        status_record["already_installed"] = False
    else:
        log("[Grobid] Found existing install.")
        status_record["already_installed"] = True

    # Step 2: Health check
    if check_grobid_healthy():
        log("[Grobid] Grobid is ALREADY running and healthy.")
        status_record["already_running"] = True
        os.environ["GROBID_RUNNING"] = "1"
        os.environ["GROBID_URL"] = GROBID_URL
    else:
        status_record["already_running"] = False
        # Kill any stray process on 8070 (if recoverable)
        kill_grobid(8070)
        # Attempt relaunch
        log("[Grobid] Starting Grobid server in background...")
        subprocess.Popen(["bash", "-c", f"cd {GROBID_HOME} && ./gradlew run > grobid_run.log 2>&1 &"])
        status_record["server_start_attempted"] = True
        # Wait for server launch/healthy
        ready = False
        log("[Grobid] Waiting for server to launch (up to 120s):")
        for i in tqdm(range(12), desc="Waiting for Grobid", ncols=70, bar_format='{l_bar}{bar}| {elapsed} [{remaining}]'):
            if check_grobid_healthy():
                log(f"[Grobid] Server is UP at {GROBID_URL}")
                ready = True
                break
            time.sleep(10)
        if ready:
            os.environ["GROBID_RUNNING"] = "1"
            os.environ["GROBID_URL"] = GROBID_URL
        else:
            log("[WARNING] Grobid server did not start in time. Extraction will use fallback methods only.")
            os.environ["GROBID_RUNNING"] = "0"
            os.environ["GROBID_URL"] = GROBID_URL

except Exception as e:
    status_record["error"] = str(e)
    log(f"[ERROR] Grobid installation/setup failed: {e}")
    os.environ["GROBID_RUNNING"] = "0"
    os.environ["GROBID_URL"] = GROBID_URL

# Audit/status log
with open(AUDIT_DIR / "block2p5_grobid_setup.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(status_record, ensure_ascii=False) + "\n")

grobid_run_status = os.environ.get("GROBID_RUNNING", "0")
print(f"\n[GROBID_RUNNING={grobid_run_status}] (0 = unavailable, 1 = running)\nGROBID_URL={os.environ['GROBID_URL']}")
print("--- End Block 2.5 ---")

# --- Cell ---
# @title [Block 3.0] Extraction Pipeline Common Setup (v6.5.0)
# Current Version 6.5.0
#
# Version Control Summaries
# v6.5.0: Modularization base. Loads env/config, PDF paths, utilities, normalizers,
#         logging helpers. For import or top-of-workspace in method blocks.
#
# Block Summary
# - Loads/validates pipeline_env.json and config.yaml.
# - Loads PDF file list as Path objects.
# - Defines: normalization functions, print_and_log, hash helpers.
# - Exports: OP_DIR, PDF_DIR, pdfs, config, fields, run_id, method_names, etc.
# - All downstream extraction blocks should run after this in session.

import os, re, json, yaml, hashlib, logging
from pathlib import Path

# --- Pipeline Environment Loading ---
with open("pipeline_env.json", "r") as f: env = json.load(f)

OP_DIR = Path(env["OPERATIONAL_DIR"])
AI_ARTIFACTS_DIR = Path(env.get("AI_ARTIFACTS_DIR", "operational/ai_artifacts"))
AI_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = OP_DIR / "config.yaml"

with open(CONFIG_PATH, "r") as f: config = yaml.safe_load(f)

PDF_DIR = Path(config["pdf_dir"])
pdfs = sorted(PDF_DIR.glob("*.pdf"))  # Always a list of pathlib.Path objects

run_id = config.get("run_id", "unnamed_run")
fields = [
    "title", "author", "year", "doi",
    "author_keywords", "country", "source_journal", "study_type"
]
method_names = ["llm", "grobid", "fitz", "pdfplumber", "filename", "crossref", "openalex"]

# --- Utility: Logging ---
def print_and_log(msg, level="info"):
    print(msg)
    with open(OP_DIR / "block3_common_debug_log.txt", "a") as f:
        f.write(str(msg) + "\n")

# --- Utility: Normalize Fields ---
def normalize_doi(x):
    if not x or not isinstance(x, str): return ""
    x = x.strip().lower().replace(' ', '')
    x = re.sub(r"^(https?://(dx\.)?doi\.org/)", "", x)
    x = re.sub(r"\s", "", x)
    return x

def normalize_author(raw):
    if not raw: return ""
    if isinstance(raw, list): vals = raw
    else: vals = [raw]
    def norm_piece(x):
        if not x: return ""
        x = str(x)
        x = x.replace(",", "")
        x = re.sub(r"\s+", " ", x).strip()
        return x
    flat = []
    for v in vals:
        if isinstance(v, str):
            flat += [norm_piece(w) for w in re.split(r";|,|&| and ", v) if w.strip()]
        else:
            flat.append(norm_piece(v))
    seen, out = set(), []
    for a in flat:
        a_lc = a.lower()
        if a_lc and a_lc not in seen:
            out.append(a)
            seen.add(a_lc)
    return "; ".join(out)

def normalize_country(raw):
    ISO_MAP = {'us': 'United States', 'gb':'United Kingdom', 'uk':'United Kingdom', 'au':'Australia', 'nz':'New Zealand', 'ca':'Canada'}
    if not raw: return ""
    vals = [w.strip() for w in str(raw).split(';') if w.strip()]
    names = []
    for v in vals:
        v_lc = v.lower()
        n = ISO_MAP.get(v_lc)
        if n: names.append(n)
        else:
            c = re.sub(r'[^a-zA-Z ]+', '', v).strip()
            if c and c.lower() not in [n.lower() for n in names]:
                names.append(c)
    return "; ".join(dict.fromkeys(names))

def normalize_keywords(raw):
    if not raw: return ""
    if isinstance(raw, list): vals = raw
    else: vals = [raw]
    flat = []
    for v in vals:
        if isinstance(v, str):
            flat += [k.strip() for k in re.split(r";|,|/|\|", v) if k.strip()]
        else:
            flat.append(str(v).strip())
    uniq = []
    seen = set()
    for k in flat:
        kl = k.lower()
        if kl and kl not in seen:
            uniq.append(k)
            seen.add(kl)
    return "; ".join(sorted(uniq, key=str.lower))

# --- File Hash Helper (Useful for Version/Audit) ---
def sha256_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

# --- Export: Common Config Info ---
print(f"[Block 3.0] Loaded {len(pdfs)} PDF(s) from: {PDF_DIR}")
print(f"[Block 3.0] Available fields: {fields}")
print(f"[Block 3.0] AI_ARTIFACTS_DIR: {AI_ARTIFACTS_DIR}")
print(f"[Block 3.0] run_id: {run_id}")

# --- No main code: this block is for session setup/exports, not per-paper logic ---

# --- Cell ---
# @title [Block 3.1] LLM Metadata Extraction Only (Colab/Env Secure Input, v6.5.2)
# Version 6.5.2
#
# - Securely prompts for API key on Colab if not set (never prints or stores in code).
# - Works everywhere, no Google Colab Pro features required.

import json, hashlib, os, re
from datetime import datetime

try:
    OP_DIR
except NameError:
    raise RuntimeError("Block 3.0 (common setup) must be run first!")

def extract_first_json(text):
    text = re.sub(r"^```(?:json)?", "", text, flags=re.MULTILINE).strip('` \n')
    depth = 0
    start, end = -1, -1
    for i, c in enumerate(text):
        if c == '{':
            if depth == 0:
                start = i
            depth += 1
        elif c == '}':
            if depth > 0:
                depth -= 1
                if depth == 0:
                    end = i
                    break
    if start != -1 and end != -1:
        return text[start:end+1]
    return ""

def flatten(val): return "; ".join(str(x) for x in val) if isinstance(val, list) else str(val)

# --- Prompt user for secret if needed (always secure, never logs the secret itself) ---
def get_openai_api_key():
    keyname = config.get("openai_key_envvar", "OPENAI_API_KEY")
    # 1. Try environment variable
    val = os.environ.get(keyname, "")
    if val and val.strip():
        return val
    # 2. Try Colab userdata.get (if available)
    try:
        from google.colab import userdata
        val2 = userdata.get(keyname)
        if val2 and val2.strip():
            return val2
    except Exception:
        pass
    # 3. Prompt interactively for key (never echoed, never stored in notebook)
    try:
        import getpass
        val3 = getpass.getpass(f'Paste your OpenAI API key for {keyname}: ')
        if val3 and val3.strip():
            os.environ[keyname] = val3.strip()  # So it works for rest of pipeline
            return val3.strip()
    except Exception:
        pass
    return ""

def extract_ai_llm_full(first_page, api_key=None, model=None, debug=False):
    error = None
    # Use the get_openai_api_key logic above by default
    api_key = api_key or get_openai_api_key()
    if not api_key or not api_key.strip():
        error = (
            "[CRIT] OpenAI API key missing/blank for LLM calls!\n"
            "If in Colab, you will be prompted for your key securely.\n"
            "Else, set envvar OPENAI_API_KEY."
        )
        print_and_log(error)
        return {k:"" for k in fields}, error
    try:
        import openai
        openai.api_key = api_key
        prompt = (
            "Extract the following metadata as a JSON object from the text provided: "
            "title, author, year, doi, author_keywords, country, source_journal, study_type. "
            "If a field is missing, leave blank or use null. Text follows:\n" + first_page
        )
        resp = openai.chat.completions.create(
            model=model or config.get("llm_model"),
            messages=[{"role":"user", "content": prompt}],
            temperature=0, max_tokens=384
        )
        txt = resp.choices[0].message.content.strip()
        if debug:
            print_and_log(f"[DEBUG] LLM RAW RESPONSE:\n{txt[:400]}\n---")
        raw_json = extract_first_json(txt)
        if not raw_json:
            raise ValueError("No JSON block found in LLM output.")
        try:
            result = json.loads(raw_json)
        except Exception as e_inner:
            raw_json2 = re.sub(r',\s*([}\]])', r'\1', raw_json)
            try:
                result = json.loads(raw_json2)
            except Exception as e2:
                error = f"[ERROR] LLM JSON parsing failed: {e_inner} | {e2}"
                print_and_log(error)
                fname = OP_DIR / f"llm_raw_{hashlib.sha1(txt.encode('utf-8')).hexdigest()[:8]}.txt"
                with open(fname, "w") as f:
                    f.write(txt)
                return {k: "" for k in fields}, f"{error} | RAW SAVED to {fname}"
        output = {k: flatten(result.get(k, "")) if isinstance(result, dict) else "" for k in fields}
        return output, None
    except Exception as e:
        error = f"[ERROR] LLM extraction failed: {e}"
        print_and_log(error)
        fname = OP_DIR / f"llm_raw_fail_{hashlib.sha1(str(e).encode('utf-8')).hexdigest()[:8]}.txt"
        with open(fname, "w") as f:
            f.write(str(e))
        return {k: "" for k in fields}, error

llm_results = []
for idx, pdf in enumerate(pdfs):
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    errors = []
    try:
        import fitz
        doc = fitz.open(pdf)
        first_page = doc[0].get_text()[:3500]
    except Exception as e:
        first_page = ""
        errors.append(f"[ERROR] fitz text extraction: {e}")
    llm, err_llm = extract_ai_llm_full(first_page)
    if err_llm: errors.append(err_llm)
    normd = {
        "pdf_id": pdf_id,
        "pdf_filename": str(pdf.name),
        "llm_extraction_time_utc": datetime.utcnow().isoformat() + "Z"
    }
    for k, v in llm.items():
        if k == "doi":
            normd[k] = normalize_doi(v)
        elif k == "author":
            normd[k] = normalize_author(v)
        elif k == "country":
            normd[k] = normalize_country(v)
        elif k == "author_keywords":
            normd[k] = normalize_keywords(v)
        else:
            normd[k] = v or ""
    normd["error_log"] = errors
    llm_results.append(normd)

outfile = AI_ARTIFACTS_DIR / f"llm_results_{run_id}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(llm_results, f, indent=2, ensure_ascii=False)
print(f"[Block 3.1] Wrote LLM results to {outfile} for {len(llm_results)} papers.")

for r in llm_results[:3]:
    print(f"\n{r['pdf_filename']}\nTitle: {r['title']} | Author(s): {r['author']} | Year: {r['year']} | DOI: {r['doi']}")

print("--- End Block 3.1 (LLM Extraction Only, Colab/Env Secure Prompt) ---")

# --- Cell ---
# @title [Block 3.2] Grobid Extraction with TEI Namespace Correction (v6.5.4)
# Version 6.5.4
#
# - Correctly parses Grobid TEI XML using xmlns namespace aware XPath.
# - All major fields should now be extracted if present in the TEI.
# - TEI debug (preview/sample) retained for diagnosis.

import json, hashlib
from datetime import datetime

try:
    OP_DIR
except NameError:
    raise RuntimeError("Block 3.0 (common setup) must be run first!")

import requests
import xml.etree.ElementTree as ET

grobid_url = config.get("grobid_url", "http://localhost:8070/api/processHeaderDocument")
DEBUG_TEI_N = 3    # Save/print TEI debug for first N PDFs

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

def extract_grobid_full(pdf_file, pdf_id, tei_debug_dir=None, verbose=False):
    meta, err, tei = {f:"" for f in fields}, None, ""
    tei_path = None
    try:
        with open(pdf_file, "rb") as f:
            resp = requests.post(grobid_url, files={'input': f}, timeout=60)
        tei = resp.text
        if verbose:
            print(f"PDF {pdf_file.name}: TEI length {len(tei)}")
        if tei_debug_dir is not None and tei and '<TEI' in tei:
            tei_path = tei_debug_dir / f"{pdf_id}_tei.xml"
            with open(tei_path, "w", encoding="utf-8") as f:
                f.write(tei)
        if tei and '<TEI' in tei:
            tree = ET.fromstring(tei)
            # --- Namespace-aware field extraction ---
            title_el = tree.find('.//tei:titleStmt/tei:title', NS)
            meta["title"] = title_el.text.strip() if title_el is not None and title_el.text else ""
            authors = []
            for pers in tree.findall('.//tei:author/tei:persName', NS):
                surname = pers.find('tei:surname', NS)
                forename = pers.find('tei:forename', NS)
                a = (forename.text if forename is not None else "")
                b = (surname.text if surname is not None else "")
                val = (a + " " + b).strip()
                if val: authors.append(val)
            meta["author"] = "; ".join(authors)
            doi_el = tree.find('.//tei:idno[@type="DOI"]', NS)
            meta["doi"] = doi_el.text.strip() if doi_el is not None and doi_el.text else ""
            date_el = tree.find('.//tei:publicationStmt/tei:date', NS)
            meta["year"] = date_el.attrib['when'][:4] if date_el is not None and 'when' in date_el.attrib else ""
            j = tree.find('.//tei:monogr/tei:title', NS)
            meta["source_journal"] = j.text.strip() if j is not None and j.text else ""
            kws = [k.text.strip() for k in tree.findall('.//tei:keywords/tei:term', NS) if k.text]
            meta["author_keywords"] = "; ".join(kws)
            ptype = tree.find('.//tei:note[@type="studyType"]', NS)
            meta["study_type"] = ptype.text.strip() if ptype is not None and ptype.text else ""
            countries = []
            for aff in tree.findall('.//tei:affiliation', NS):
                country_el = aff.find('.//tei:country', NS)
                if country_el is not None and country_el.text:
                    countries.append(country_el.text.strip())
            meta["country"] = "; ".join(set(countries))
        else:
            err = f"[WARN] Malformed or empty TEI from Grobid (length={len(tei)})"
            print_and_log(err)
    except Exception as e:
        err = f"[WARN] Grobid XML: {e}"
        print_and_log(err)
    return meta, err, tei, tei_path

tei_debug_dir = AI_ARTIFACTS_DIR / "grobid_tei_debug"
tei_debug_dir.mkdir(exist_ok=True, parents=True)

grobid_results = []
for idx, pdf in enumerate(pdfs):
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    errors, tei_path = [], None
    meta, err_grobid, tei, saved_tei_path = extract_grobid_full(pdf, pdf_id, tei_debug_dir if idx < DEBUG_TEI_N else None, verbose=True)
    if err_grobid: errors.append(err_grobid)
    if saved_tei_path:
        errors.append(f"[INFO] TEI saved in {saved_tei_path}")
    normd = {
        "pdf_id": pdf_id,
        "pdf_filename": str(pdf.name),
        "grobid_extraction_time_utc": datetime.utcnow().isoformat() + "Z",
        "tei_length": len(tei),
        "tei_sample": (tei[:450] + "...") if tei else "",
    }
    for k, v in meta.items():
        if k == "doi":
            normd[k] = normalize_doi(v)
        elif k == "author":
            normd[k] = normalize_author(v)
        elif k == "country":
            normd[k] = normalize_country(v)
        elif k == "author_keywords":
            normd[k] = normalize_keywords(v)
        else:
            normd[k] = v or ""
    normd["error_log"] = errors
    grobid_results.append(normd)

outfile = AI_ARTIFACTS_DIR / f"grobid_results_{run_id}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(grobid_results, f, indent=2, ensure_ascii=False)
print(f"[Block 3.2] Wrote Grobid results to {outfile} for {len(grobid_results)} papers.")
for r in grobid_results[:3]:
    print(f"\n{r['pdf_filename']}\nTitle: {r['title']} | Author(s): {r['author']} | Year: {r['year']} | DOI: {r['doi']}\nTEI preview: {r['tei_sample'][:180]} ...")
print("\nCheck ai_artifacts/grobid_tei_debug/{pdf_id}_tei.xml for raw TEI from first few papers.")
print("--- End Block 3.2 (Grobid Extraction, Namespace-corrected) ---")

# --- Cell ---
# @title [Block 3.3] Embedded PDF Metadata Extraction (fitz + pdfplumber) (v6.5.0)
# Version 6.5.0
#
# - Extracts embedded metadata via fitz (PyMuPDF) and pdfplumber for each PDF.
# - Normalizes results, logs errors, and provides per-paper, per-method results.
# - Output: ai_artifacts/pdfmeta_results_{run_id}.json

import json, hashlib
from datetime import datetime

try:
    OP_DIR
except NameError:
    raise RuntimeError("Block 3.0 (common setup) must be run first!")

try:
    import fitz
except ImportError:
    raise ImportError("fitz (PyMuPDF) not found. Please install via pip.")

try:
    import pdfplumber
except ImportError:
    raise ImportError("pdfplumber not found. Please install via pip.")

def extract_fitz_metadata(pdf_path):
    meta, err = {f:"" for f in fields}, None
    try:
        doc = fitz.open(pdf_path)
        m = doc.metadata
        meta["title"] = m.get("title", "") or m.get("Title", "")
        meta["author"] = m.get("author", "") or m.get("Author", "")
        meta["year"] = str(m.get("modDate", "")[2:6]) if m.get("modDate", "") else ""
        meta["author_keywords"] = m.get("keywords", "") or m.get("Keywords", "")
    except Exception as e:
        err = f"[WARN] fitz metadata: {e}"
        print_and_log(err)
    return meta, err

def extract_pdfplumber_metadata(pdf_path):
    meta, err = {f:"" for f in fields}, None
    try:
        with pdfplumber.open(pdf_path) as p:
            info = p.metadata or {}
            meta["title"] = info.get("Title", "")
            meta["author"] = info.get("Author", "")
            meta["year"] = info.get("ModDate", "")[2:6] if info.get("ModDate","") else ""
            meta["author_keywords"] = info.get("Keywords", "")
    except Exception as e:
        err = f"[WARN] pdfplumber metadata: {e}"
        print_and_log(err)
    return meta, err

pdfmeta_results = []
for idx, pdf in enumerate(pdfs):
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    errors = []

    fitz_m, err_fitz = extract_fitz_metadata(pdf)
    if err_fitz: errors.append(err_fitz)

    pdfplumber_m, err_pdfplumber = extract_pdfplumber_metadata(pdf)
    if err_pdfplumber: errors.append(err_pdfplumber)

    normd = {
        "pdf_id": pdf_id,
        "pdf_filename": str(pdf.name),
        "fitz_title": normalize_author(fitz_m["title"]),
        "fitz_author": normalize_author(fitz_m["author"]),
        "fitz_year": fitz_m["year"],
        "fitz_author_keywords": normalize_keywords(fitz_m["author_keywords"]),
        "pdfplumber_title": normalize_author(pdfplumber_m["title"]),
        "pdfplumber_author": normalize_author(pdfplumber_m["author"]),
        "pdfplumber_year": pdfplumber_m["year"],
        "pdfplumber_author_keywords": normalize_keywords(pdfplumber_m["author_keywords"]),
        "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
        "error_log": errors
    }
    pdfmeta_results.append(normd)

outfile = AI_ARTIFACTS_DIR / f"pdfmeta_results_{run_id}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(pdfmeta_results, f, indent=2, ensure_ascii=False)
print(f"[Block 3.3] Wrote PDF embedded metadata results to {outfile} for {len(pdfmeta_results)} papers.")
for r in pdfmeta_results[:3]:
    print(f"\n{r['pdf_filename']}\n[fitz] Title: {r['fitz_title']} | Author(s): {r['fitz_author']} | Year: {r['fitz_year']}\n[pdfplumber] Title: {r['pdfplumber_title']} | Author(s): {r['pdfplumber_author']} | Year: {r['pdfplumber_year']}")
print("--- End Block 3.3 (PDF Embedded Metadata Extraction) ---")

# --- Cell ---
# @title [Block 3.4] Improved Filename/Regex Metadata Extraction (v6.5.1)
# Version 6.5.1
#
# - Smarter "author" extraction: Removes 'Copy of ' and other common prefixes, normalizes
# - Tolerant to spaces, underscores, multiple "Copy of" repeats, "v1 -" or "Final -"
# - Output: ai_artifacts/filename_results_{run_id}.json

import json, hashlib, re
from datetime import datetime

try:
    OP_DIR
except NameError:
    raise RuntimeError("Block 3.0 (common setup) must be run first!")

# Helper to strip common prefix junk before 'author'
def clean_author_string(author_raw):
    # Remove leading "Copy of", "Final", "v1", or multiples thereof
    author = author_raw
    author = re.sub(r"^(copy of\s*|\s*final\s*|\s*v\d+\s*|\s*-+\s*)+", "", author, flags=re.IGNORECASE)
    author = author.replace("_", " ").replace("-", " ").strip()
    # Remove trailing repeated spaces, dots or junk
    author = re.sub(r'\.+$', "", author).strip()
    # Make sure it's not just empty or a number
    return author if (len(author) > 2 and not author.strip().isdigit()) else ""

def extract_from_filename(pdf_path):
    # More robust: cleans at start, matches main academic export pattern
    base = str(pdf_path.name)
    result = {
        "author": "",
        "year": "",
        "title": "",
        "doi": "",
    }
    error = None
    m = re.match(r"(.+?)\s*-\s*(\d{4})\s*-\s*(.+)\.pdf$", base, re.IGNORECASE)
    if m:
        raw_author, result["year"], result["title"] = m.groups()
        result["author"] = clean_author_string(raw_author)
    else:
        # Try backup, less strict
        m2 = re.match(r"(.+?)\s*-\s*(\d{4})\s*-\s*(.+)", base, re.IGNORECASE)
        if m2:
            raw_author, result["year"], result["title"] = m2.groups()
            result["author"] = clean_author_string(raw_author)
        else:
            error = f"[WARN] Filename did not match expected pattern: '{base}'"
    # Try extracting DOI from base/filename (remove .pdf for search)
    base_noext = re.sub(r"\.pdf$", "", base, flags=re.IGNORECASE)
    m_doi = re.search(r"(10\.\d{4,9}/[\w\.\-\/]+)", base_noext, re.IGNORECASE)
    if m_doi:
        result["doi"] = m_doi.group(1)
    return result, error

filename_results = []
for idx, pdf in enumerate(pdfs):
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    fnres, warn = extract_from_filename(pdf)
    errors = []
    if warn:
        errors.append(warn)
    normd = {
        "pdf_id": pdf_id,
        "pdf_filename": str(pdf.name),
        "fn_author": normalize_author(fnres["author"]),
        "fn_year": fnres["year"],
        "fn_title": fnres["title"].replace("_", " ").strip(),
        "fn_doi": normalize_doi(fnres["doi"]),
        "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
        "error_log": errors
    }
    filename_results.append(normd)

outfile = AI_ARTIFACTS_DIR / f"filename_results_{run_id}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(filename_results, f, indent=2, ensure_ascii=False)
print(f"[Block 3.4] Wrote filename/regex extraction results to {outfile} for {len(filename_results)} papers.")
for r in filename_results[:3]:
    print(f"\n{r['pdf_filename']}\nAuthor(s): {r['fn_author']} | Year: {r['fn_year']} | Title: {r['fn_title']} | DOI: {r['fn_doi']} | ERROR: {r['error_log']}")
print("--- End Block 3.4 (Improved Filename/Regex Metadata Extraction) ---")

# --- Cell ---
# @title [Block 3.5] CrossRef Metadata Extraction (auto-detect missing inputs, v6.5.1)
# Version 6.5.1
#
# - Tries to load all prior method outputs but will proceed and warn even if some are missing
# - Prioritizes: Grobid > LLM > Filename for DOI/title/author query
# - Skips gracefully based on allow_internet
# - Output: ai_artifacts/crossref_results_{run_id}.json

import json, hashlib, requests
from datetime import datetime

try:
    OP_DIR
except NameError:
    raise RuntimeError("Block 3.0 (common setup) must be run first!")

def try_load(path):
    try:
        with open(path) as f:
            out = json.load(f)
        print(f"[INFO] Loaded {path.name}, {len(out)} records.")
        return {r["pdf_id"]: r for r in out}
    except Exception as e:
        print(f"[WARN] Could not load {path}: {e}")
        return {}

allow_internet = config.get("allow_internet", True)
grobid_path = AI_ARTIFACTS_DIR / f"grobid_results_{run_id}.json"
llm_path = AI_ARTIFACTS_DIR / f"llm_results_{run_id}.json"
filename_path = AI_ARTIFACTS_DIR / f"filename_results_{run_id}.json"

grobid_res = try_load(grobid_path)
llm_res = try_load(llm_path)
fn_res = try_load(filename_path)

def extract_crossref_metadata(doi, title, author):
    out, err = {f: "" for f in fields}, None
    try:
        if doi:
            url = f"https://api.crossref.org/works/{normalize_doi(doi)}"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                err = f"[WARN] CrossRef DOI {doi} query failed: HTTP {r.status_code}"
                return out, err
            dat = r.json().get("message", {})
        elif title and author:
            q = f"{title} {author}"
            url = f"https://api.crossref.org/works?query.bibliographic={requests.utils.quote(q)}&rows=1"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                err = f"[WARN] CrossRef bibliographic query ('{q}') failed: HTTP {r.status_code}"
                return out, err
            items = r.json().get("message", {}).get("items", [])
            dat = items[0] if items else {}
        else:
            err = "[WARN] No DOI or title/author, cannot query CrossRef"
            return out, err
        out["doi"] = dat.get("DOI", "")
        out["title"] = dat.get("title", [""])[0] if dat.get("title") else ""
        out["author"] = "; ".join(
            "{}, {}".format(a.get("family", "").strip(), a.get("given", "").strip())
            for a in dat.get("author", [])
        ) if dat.get("author") else ""
        out["year"] = str(dat.get("issued", {}).get("date-parts", [[None]])[0][0]) if dat.get("issued") else ""
        out["author_keywords"] = "; ".join(dat.get("subject", [])) if dat.get("subject") else ""
        out["source_journal"] = dat.get("container-title", [""])[0] if dat.get("container-title") else ""
        out["study_type"] = dat.get("type", "")
        out["country"] = ""
    except Exception as e:
        err = f"[WARN] CrossRef error: {e}"
        print_and_log(err)
    return out, err

crossref_results = []
for pdf in pdfs:
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    errors = []
    grob = grobid_res.get(pdf_id, {})
    llm = llm_res.get(pdf_id, {})
    fn = fn_res.get(pdf_id, {})
    candidates = [
        dict(doi=grob.get("doi") or "", title=grob.get("title") or "", author=grob.get("author") or ""),
        dict(doi=llm.get("doi") or "", title=llm.get("title") or "", author=llm.get("author") or ""),
        dict(doi=fn.get("fn_doi") or "", title=fn.get("fn_title") or "", author=fn.get("fn_author") or "")
    ]
    candidate = next((c for c in candidates if c["doi"] or (c["title"] and c["author"])), None)
    if not allow_internet:
        normd = {
            "pdf_id": pdf_id,
            "pdf_filename": str(pdf.name),
            "crossref_doi": "",
            "crossref_title": "",
            "crossref_author": "",
            "crossref_year": "",
            "crossref_journal": "",
            "crossref_keywords": "",
            "crossref_type": "",
            "crossref_country": "",
            "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
            "error_log": ["[INFO] Skipped: allow_internet is False"]
        }
    elif candidate:
        cr, err = extract_crossref_metadata(candidate["doi"], candidate["title"], candidate["author"])
        normd = {
            "pdf_id": pdf_id,
            "pdf_filename": str(pdf.name),
            "crossref_doi": normalize_doi(cr["doi"]),
            "crossref_title": cr["title"],
            "crossref_author": normalize_author(cr["author"]),
            "crossref_year": cr["year"],
            "crossref_journal": cr["source_journal"],
            "crossref_keywords": normalize_keywords(cr["author_keywords"]),
            "crossref_type": cr["study_type"],
            "crossref_country": normalize_country(cr["country"]),
            "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
            "error_log": [err] if err else []
        }
    else:
        normd = {
            "pdf_id": pdf_id,
            "pdf_filename": str(pdf.name),
            "crossref_doi": "",
            "crossref_title": "",
            "crossref_author": "",
            "crossref_year": "",
            "crossref_journal": "",
            "crossref_keywords": "",
            "crossref_type": "",
            "crossref_country": "",
            "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
            "error_log": ["[WARN] Could not assemble lookup info from any extractor."]
        }
    crossref_results.append(normd)

outfile = AI_ARTIFACTS_DIR / f"crossref_results_{run_id}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(crossref_results, f, indent=2, ensure_ascii=False)
print(f"[Block 3.5] Wrote CrossRef extraction results to {outfile} for {len(crossref_results)} papers.")
for r in crossref_results[:3]:
    print(f"\n{r['pdf_filename']}\nTitle: {r['crossref_title']} | Author(s): {r['crossref_author']} | Year: {r['crossref_year']} | DOI: {r['crossref_doi']}\nERROR: {r['error_log']}")
print("--- End Block 3.5 (CrossRef Metadata Extraction, resilient) ---")

# --- Cell ---
# @title [Block 3.6] OpenAlex Metadata Extraction (Bulletproof Author Join, v6.5.2)
# Version 6.5.2
#
# - Handles all OpenAlex "display_name" field variants (joins only if actual string).
# - Outputs: ai_artifacts/openalex_results_{run_id}.json

import json, hashlib, requests
from datetime import datetime

try:
    OP_DIR
except NameError:
    raise RuntimeError("Block 3.0 (common setup) must be run first!")

def try_load(path):
    try:
        with open(path) as f:
            results = json.load(f)
        print(f"[INFO] Loaded {path.name}, {len(results)} records.")
        return {r["pdf_id"]: r for r in results}
    except Exception as e:
        print(f"[WARN] Could not load {path}: {e}")
        return {}

allow_internet = config.get("allow_internet", True)
grobid_path = AI_ARTIFACTS_DIR / f"grobid_results_{run_id}.json"
llm_path = AI_ARTIFACTS_DIR / f"llm_results_{run_id}.json"
filename_path = AI_ARTIFACTS_DIR / f"filename_results_{run_id}.json"

grobid_res = try_load(grobid_path)
llm_res = try_load(llm_path)
fn_res = try_load(filename_path)

def extract_openalex_metadata(doi, title):
    out, err = {f: "" for f in fields}, None
    try:
        if doi:
            url = f"https://api.openalex.org/works/https://doi.org/{normalize_doi(doi)}"
            r = requests.get(url, timeout=20)
            if r.status_code != 200:
                err = f"[WARN] OpenAlex DOI {doi} query failed: HTTP {r.status_code}"
                return out, err
            dat = r.json()
        elif title:
            url = f"https://api.openalex.org/works?title.search={requests.utils.quote(title)}"
            r = requests.get(url, timeout=20)
            if r.status_code != 200:
                err = f"[WARN] OpenAlex title.search ('{title}') failed: HTTP {r.status_code}"
                return out, err
            dat = r.json()["results"][0] if "results" in r.json() and r.json()["results"] else {}
        else:
            err = "[WARN] No DOI or title, cannot query OpenAlex"
            return out, err
        doi_val = dat.get("doi", "")
        if doi_val and doi_val.startswith("https://doi.org/"):
            doi_val = doi_val[len("https://doi.org/") :]
        out["doi"] = doi_val
        out["title"] = dat.get("title", "")
        # Robust! Only join proper strings. Skip any non-string, non-present
        out["author"] = "; ".join([
            disp for a in dat.get("authorships", [])
            for disp in [a.get("author",{}).get("display_name")]
            if isinstance(disp, str)
        ])
        out["year"] = str(dat.get("publication_year", ""))
        out["author_keywords"] = "; ".join(dat.get("keywords", [])) if dat.get("keywords") else ""
        out["source_journal"] = dat.get("host_venue", {}).get("display_name", "") if dat.get("host_venue") else ""
        out["study_type"] = dat.get("type", "")
        ISO_MAP = {'us': 'United States', 'gb':'United Kingdom', 'uk':'United Kingdom', 'au':'Australia', 'nz':'New Zealand', 'ca':'Canada'}
        countries = []
        for a in dat.get("authorships", []):
            for inst in a.get("institutions", []):
                cc = inst.get("country_code")
                if cc:
                    countries.append(ISO_MAP.get(cc.lower(), cc.upper()))
        out["country"] = "; ".join(sorted(set(countries)))
    except Exception as e:
        err = f"[WARN] OpenAlex error: {e}"
        print_and_log(err)
    return out, err

openalex_results = []
for pdf in pdfs:
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    errors = []
    grob = grobid_res.get(pdf_id, {})
    llm = llm_res.get(pdf_id, {})
    fn = fn_res.get(pdf_id, {})
    candidates = [
        dict(doi=grob.get("doi") or "", title=grob.get("title") or ""),
        dict(doi=llm.get("doi") or "", title=llm.get("title") or ""),
        dict(doi=fn.get("fn_doi") or "", title=fn.get("fn_title") or "")
    ]
    candidate = next((c for c in candidates if c["doi"] or c["title"]), None)
    if not allow_internet:
        normd = {
            "pdf_id": pdf_id,
            "pdf_filename": str(pdf.name),
            "openalex_doi": "",
            "openalex_title": "",
            "openalex_author": "",
            "openalex_year": "",
            "openalex_journal": "",
            "openalex_keywords": "",
            "openalex_type": "",
            "openalex_country": "",
            "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
            "error_log": ["[INFO] Skipped: allow_internet is False"]
        }
    elif candidate:
        cr, err = extract_openalex_metadata(candidate["doi"], candidate["title"])
        normd = {
            "pdf_id": pdf_id,
            "pdf_filename": str(pdf.name),
            "openalex_doi": normalize_doi(cr["doi"]),
            "openalex_title": cr["title"],
            "openalex_author": normalize_author(cr["author"]),
            "openalex_year": cr["year"],
            "openalex_journal": cr["source_journal"],
            "openalex_keywords": normalize_keywords(cr["author_keywords"]),
            "openalex_type": cr["study_type"],
            "openalex_country": normalize_country(cr["country"]),
            "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
            "error_log": [err] if err else []
        }
    else:
        normd = {
            "pdf_id": pdf_id,
            "pdf_filename": str(pdf.name),
            "openalex_doi": "",
            "openalex_title": "",
            "openalex_author": "",
            "openalex_year": "",
            "openalex_journal": "",
            "openalex_keywords": "",
            "openalex_type": "",
            "openalex_country": "",
            "extraction_time_utc": datetime.utcnow().isoformat() + "Z",
            "error_log": ["[WARN] Could not assemble lookup info from any extractor."]
        }
    openalex_results.append(normd)

outfile = AI_ARTIFACTS_DIR / f"openalex_results_{run_id}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(openalex_results, f, indent=2, ensure_ascii=False)
print(f"[Block 3.6] Wrote OpenAlex extraction results to {outfile} for {len(openalex_results)} papers.")
for r in openalex_results[:3]:
    print(f"\n{r['pdf_filename']}\nTitle: {r['openalex_title']} | Author(s): {r['openalex_author']} | Year: {r['openalex_year']} | DOI: {r['openalex_doi']}\nERROR: {r['error_log']}")
print("--- End Block 3.6 (OpenAlex Metadata Extraction, bulletproof) ---")

# --- Cell ---
# @title [Block 3.7] Extraction Method Comparison/Diagnostics Table (v6.6.0)
# Version 6.6.0
#
# - Table 1: Null/blank count matrix — field (row) × method (col)
# - Table 2+: For each paper: method (row) × field (col), shows each returned value.
# - Lists per-method error logs grouped for audit.
# - Output: ai_artifacts/master_nullcount_{run_id}.csv, ai_artifacts/master_perpaper_{run_id}.json

import json, hashlib, pandas as pd
from pathlib import Path

try:
    OP_DIR
except NameError:
    raise RuntimeError("Block 3.0 (common setup) must be run first!")

# --- Method to file mapping
method_to_jsonfile = {
    "llm":         f"llm_results_{run_id}.json",
    "grobid":      f"grobid_results_{run_id}.json",
    "filename":    f"filename_results_{run_id}.json",
    "fitz":        f"pdfmeta_results_{run_id}.json",
    "pdfplumber":  f"pdfmeta_results_{run_id}.json",  # both in same file
    "crossref":    f"crossref_results_{run_id}.json",
    "openalex":    f"openalex_results_{run_id}.json"
}

def load_method_results(method, colmap=None, subkey=None):
    path = AI_ARTIFACTS_DIR / method_to_jsonfile[method]
    try:
        with open(path) as f:
            dat = json.load(f)
        results = {}
        for obj in dat:
            pdf_id = obj["pdf_id"]
            if subkey:  # for fitz/pdfplumber "pdfmeta_results"
                use = obj.get(f"{subkey}_{colmap}", "") if colmap else obj.get(f"{subkey}", "")
            else:
                use = {field: obj.get(f"{colmap}_{field}", obj.get(field, "")) for field in fields} if colmap else {field: obj.get(field, "") for field in fields}
            results[pdf_id] = obj
        return results
    except Exception as e:
        print(f"[WARN] Could not load {method}: {path}! {e}")
        return {}

fields = [
    "title", "author", "year", "doi",
    "author_keywords", "country", "source_journal", "study_type"
]
methods = ["llm", "grobid", "filename", "fitz", "pdfplumber", "crossref", "openalex"]

# --- Load data
method_results = {}
for method in methods:
    if method in ["fitz", "pdfplumber"]:
        colmap = "title"  # dummy; all handled in next block
        subkey = method
    else:
        colmap, subkey = None, None
    method_results[method] = load_method_results(method, colmap=subkey, subkey=subkey)

# --- Table 1: Null/Blank Count Table (field x method) ---
nullcount = pd.DataFrame(0, index=fields, columns=methods)
for pdf in pdfs:
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    for m in methods:
        res = method_results[m].get(pdf_id, {})
        # For fitz/pdfplumber, handle alternate field layout
        for f in fields:
            if m == "fitz":
                val = res.get("fitz_" + f, "")
            elif m == "pdfplumber":
                val = res.get("pdfplumber_" + f, "")
            else:
                val = res.get(f, "")
            if not val or str(val).strip() == "" or str(val).strip().lower() == "none":
                nullcount.loc[f, m] += 1

outfile = AI_ARTIFACTS_DIR / f"master_nullcount_{run_id}.csv"
nullcount.to_csv(outfile)
print("\n=== Table 1: Null/Blank Count Table (field x method) ===")
print(nullcount)
print(f"Table written to {outfile}")

# --- Table 2+: Per-paper method × field value map ---
perpaper_output = {}
for pdf in pdfs:
    pdf_id = f"paper_ID_{hashlib.sha1(str(pdf).encode('utf-8')).hexdigest()[:8]}"
    paper_tab = pd.DataFrame(
        columns=fields, index=methods
    )
    for m in methods:
        res = method_results[m].get(pdf_id, {})
        for f in fields:
            if m == "fitz":
                val = res.get("fitz_" + f, "")
            elif m == "pdfplumber":
                val = res.get("pdfplumber_" + f, "")
            elif m == "filename":
                # For filename, map to fn_title/fn_author/fn_year etc.
                mapfield = {"title": "fn_title", "author": "fn_author", "year": "fn_year", "doi": "fn_doi"}
                val = res.get(mapfield.get(f, "fn_" + f), "")
            elif m == "crossref":
                val = res.get("crossref_" + f, "")
            elif m == "openalex":
                val = res.get("openalex_" + f, "")
            else:
                val = res.get(f, "")
            paper_tab.loc[m, f] = val
    perpaper_output[pdf_id] = {
        "pdf_filename": pdf.name,
        "comparison_table": paper_tab.to_dict(),
    }

outfile_json = AI_ARTIFACTS_DIR / f"master_perpaper_{run_id}.json"
with open(outfile_json, "w", encoding="utf-8") as f:
    json.dump(perpaper_output, f, indent=2, ensure_ascii=False)

print("\n=== Table 2+: Per-paper Extraction Comparison ===")
for k, v in list(perpaper_output.items())[:2]:
    print(f"\nPaper: {v['pdf_filename']}")
    print(pd.DataFrame(v['comparison_table']))

# --- Per-method error logs grouped ---
print("\n=== Per-method Error Logs Grouped ===")
for m in methods:
    errlogs = []
    objs = method_results[m].values()
    for o in objs:
        errs = o.get("error_log", [])
        if errs:
            errlogs.extend(errs if isinstance(errs, list) else [errs])
    print(f"\nMethod: {m}")
    if errlogs:
        for e in errlogs:
            print("  ", e)
    else:
        print("  [no errors logged]")

print("--- End Block 3.7 (Method Comparison + Per-paper Review Tables) ---")

# --- Cell ---


# --- Cell ---
# @title [Block 3] Forensic Metadata Extraction – Normalized, Forensic Audit, Enhanced DOI (v6.4.0)
# Current Version 6.4.0
#
# Version Control Summaries
# v6.0: Multi-source extraction and manifest voting (fitz, pdfplumber, GROBID, CrossRef, OpenAlex, filename, LLM).
# v6.1: LLM-based metadata, review-needed flag, fuzzy matching for missing/ambiguous fields.
# v6.2: Added consensus logic, CrossRef/OpenAlex normalization, audit trail, reviewer trace.
# v6.2.4: Extended fields, audit-ready outputs.
# v6.3.0: Refactor - forensic extraction, no voting.
# v6.3.1: Consistent paper IDs, match analytics, outputs audit/stable.
# v6.3.2: Pure ID-table output, no filenames, exact/approx tables.
# v6.3.3: More robust error tracing, LLM key via colab.userdata, type diagnostics.
# v6.3.5: Full XML parsing for Grobid, safe LLM flattening, NZ English, method error log.
# v6.4.0: [SPRINT 1] - Normalization applied to all method outputs (DOI, authors, country, keywords).
#         - DOI regex scan on first 2 and last page (fallback).
#         - CrossRef bibliographic search if no DOI and internet enabled.
#         - All method errors captured per PDF. Raw audit JSON (all methods+errors) written per-paper.
#         - API calls conditional on allow_internet.
#         - Null summary, consensus logic preps for normalized fields. Review/PI diagnostics improved.
#
# Block Summary
# - Extracts metadata via: LLM, Grobid (XML), fitz, pdfplumber, filename, CrossRef, OpenAlex
# - Runs all field values through normalization: DOI, author, country, keywords
# - Fallback: DOI regex search (first 2 + last page); CrossRef 'bibliographic' if still missing
# - All method outputs, errors, and debug logs written to per-paper raw_meta JSON in audit/raw_meta/.
# - API/net calls POLICED BY config['allow_internet'], future-proof for caching
# - Prints method × field null-matrix, diagnostic per-paper tables; reviewer/PI clarity prioritized
# @title [Block 3] Forensic Metadata Extraction – Normalized, Path Handling Bugfix (v6.4.1)
# Current Version 6.4.1
#
# Version Control Summaries
# v6.0–v6.4.0: See previous comments.
# v6.4.1: [BUGFIX] Ensures pdfs is always a list of Path/str objects.
#         - Loop never mutates pdf variable.
#         - All extractors are called ONLY with Path/str (never dict).
#         - Assert added at start of each loop for extra safety.
#
# Block Summary
# - Restores robust method application to each PDF: no silent, systematic extraction failures.
# - All audit, normalization, error logging, API/network logic from v6.4.0 retained.

import os, re, fitz, pdfplumber, requests, json, yaml, hashlib, xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd

# ... [Normalization helpers and previous definitions—unchanged, see v6.4.0] ...

# --- Normalization Helpers ---
def normalize_doi(x):
    if not x or not isinstance(x, str): return ""
    x = x.strip().lower().replace(' ', '')
    x = re.sub(r"^(https?://(dx\.)?doi\.org/)", "", x)
    x = re.sub(r"\s", "", x)
    return x

def normalize_author(raw):
    if not raw: return ""
    if isinstance(raw, list): vals = raw
    else: vals = [raw]
    def norm_piece(x):
        if not x: return ""
        x = str(x)
        x = x.replace(",", "")
        x = re.sub(r"\s+", " ", x).strip()
        return x
    flat = []
    for v in vals:
        if isinstance(v, str):
            flat += [norm_piece(w) for w in re.split(r";|,|&| and ", v) if w.strip()]
        else:
            flat.append(norm_piece(v))
    seen, out = set(), []
    for a in flat:
        a_lc = a.lower()
        if a_lc and a_lc not in seen:
            out.append(a)
            seen.add(a_lc)
    return "; ".join(out)

def normalize_country(raw):
    ISO_MAP = {'us': 'United States', 'gb':'United Kingdom', 'uk':'United Kingdom', 'au':'Australia', 'nz':'New Zealand', 'ca':'Canada'}
    if not raw: return ""
    vals = [w.strip() for w in str(raw).split(';') if w.strip()]
    names = []
    for v in vals:
        v_lc = v.lower()
        n = ISO_MAP.get(v_lc)
        if n: names.append(n)
        else:
            c = re.sub(r'[^a-zA-Z ]+', '', v).strip()
            if c and c.lower() not in [n.lower() for n in names]:
                names.append(c)
    return "; ".join(dict.fromkeys(names))

def normalize_keywords(raw):
    if not raw: return ""
    if isinstance(raw, list): vals = raw
    else: vals = [raw]
    flat = []
    for v in vals:
        if isinstance(v, str):
            flat += [k.strip() for k in re.split(r";|,|/|\|", v) if k.strip()]
        else:
            flat.append(str(v).strip())
    uniq = []
    seen = set()
    for k in flat:
        kl = k.lower()
        if kl and kl not in seen:
            uniq.append(k)
            seen.add(kl)
    return "; ".join(sorted(uniq, key=str.lower))

with open("pipeline_env.json", "r") as f: env = json.load(f)
OP_DIR = Path(env["OPERATIONAL_DIR"])
CONFIG_PATH = OP_DIR / "config.yaml"
with open(CONFIG_PATH, "r") as f: config = yaml.safe_load(f)
PDF_DIR = Path(config["pdf_dir"])
pdfs = sorted(PDF_DIR.glob("*.pdf"))[:20]  # Always a list of Path objects!
grobid_url = config.get("grobid_url", "http://localhost:8070/api/processHeaderDocument")
allow_internet = config.get("allow_internet", True)

try:
    from google.colab import userdata
    OPENAI_API_KEY = userdata.get(config.get("openai_key_envvar", "OPENAI_API_KEY"))
except Exception:
    OPENAI_API_KEY = os.environ.get(config.get("openai_key_envvar", "OPENAI_API_KEY"), "")

llm_model = config.get("llm_model")

fields = [
    "title", "author", "year", "doi",
    "author_keywords", "country", "source_journal", "study_type"
]
method_names = ["llm", "grobid", "fitz", "pdfplumber", "filename", "crossref", "openalex"]

def pdf_hash_id(pdf_path): return f"paper_ID_{hashlib.sha1(str(pdf_path).encode('utf-8')).hexdigest()[:8]}"

def search_doi_in_text(pdf_file):
    try:
        doc = fitz.open(pdf_file)
        texts = []
        for i in [0,1,-1]:
            if 0 <= i < len(doc) or (i < 0 and len(doc) > abs(i)):
                t = doc[i].get_text()
                texts.append(t)
        s = "\n".join(texts)
        m = re.search(r'(10\.\d{4,9}/[\w\.\-;/\(\):]+)', s, flags=re.I)
        if m: return normalize_doi(m.group(1))
    except Exception: pass
    return ""

def flatten(val): return "; ".join(str(x) for x in val) if isinstance(val, list) else str(val)

def print_and_log(msg):
    print(msg)
    with open(OP_DIR / "block3_debug_log.txt", "a") as f: f.write(str(msg) + "\n")

def extract_first_page_text(pdf_file, debug=False):
    text, err = "", None
    try:
        doc = fitz.open(pdf_file)
        text = doc[0].get_text()[:3500]
        if not text.strip() and len(doc)>1:
            text2 = doc[1].get_text()[:2000]
            text += "\n" + text2
    except Exception as e:
        err = f"[ERROR] extract_first_page_text: {e}"
        print_and_log(err)
    return text, err

def extract_fitz_metadata(pdf_file):
    meta, err = {f:"" for f in fields}, None
    try:
        doc = fitz.open(pdf_file)
        m = doc.metadata
        meta["title"] = m.get("title", "") or m.get("Title", "")
        meta["author"] = m.get("author", "") or m.get("Author", "")
        meta["year"] = str(m.get("modDate", "")[2:6]) if m.get("modDate", "") else ""
    except Exception as e:
        err = f"[WARN] fitz metadata: {e}"
        print_and_log(err)
    return meta, err

def extract_pdfplumber_metadata(pdf_file):
    meta, err = {f:"" for f in fields}, None
    try:
        with pdfplumber.open(pdf_file) as p:
            info = p.metadata or {}
            meta["title"] = info.get("Title", "")
            meta["author"] = info.get("Author", "")
            meta["year"] = info.get("ModDate", "")[2:6] if info.get("ModDate","") else ""
            meta["author_keywords"] = info.get("Keywords", "")
    except Exception as e:
        err = f"[WARN] pdfplumber metadata: {e}"
        print_and_log(err)
    return meta, err

def extract_from_filename_meta(pdf_file):
    meta = {f:"" for f in fields}
    base = Path(pdf_file).stem
    m = re.match(r"(.+?)\s*-\s*(\d{4})\s*-\s*(.+)", base)
    if m:
        meta["author"], meta["year"], meta["title"] = m.groups()
    meta["doi"] = ""
    m2 = re.search(r"(10\.\d{4,9}/[\w\.\-\/]+)", base)
    if m2:
        meta["doi"] = m2.group(1)
    return meta

def extract_grobid_full(pdf_file):
    meta, err = {f:"" for f in fields}, None
    try:
        with open(pdf_file, "rb") as f:
            resp = requests.post(grobid_url, files={'input': f}, timeout=60)
        tei = resp.text
        if tei and '<TEI' in tei:
            tree = ET.fromstring(tei)
            title_el = tree.find('.//titleStmt/title')
            if title_el is not None and title_el.text:
                meta["title"] = title_el.text.strip()
            authors = []
            for pers in tree.findall('.//author/persName'):
                surname = pers.find('surname')
                forename = pers.find('forename')
                a = (forename.text if forename is not None else "")
                b = (surname.text if surname is not None else "")
                val = (a + " " + b).strip()
                if val: authors.append(val)
            meta["author"] = "; ".join(authors)
            doi_el = tree.find('.//idno[@type="DOI"]')
            meta["doi"] = doi_el.text.strip() if doi_el is not None and doi_el.text else ""
            date_el = tree.find('.//publicationStmt/date')
            meta["year"] = date_el.attrib['when'][:4] if date_el is not None and 'when' in date_el.attrib else ""
            j = tree.find('.//monogr/title')
            meta["source_journal"] = j.text.strip() if j is not None and j.text else ""
            kws = [k.text.strip() for k in tree.findall('.//keywords/term') if k.text]
            meta["author_keywords"] = "; ".join(kws)
            ptype = tree.find('.//note[@type="studyType"]')
            meta["study_type"] = ptype.text.strip() if ptype is not None and ptype.text else ""
            countries = []
            for aff in tree.findall('.//affiliation'):
                country_el = aff.find('.//country')
                if country_el is not None and country_el.text:
                    countries.append(country_el.text.strip())
            meta["country"] = "; ".join(set(countries))
        else:
            err = "[WARN] Malformed or empty TEI from Grobid"
            print_and_log(err)
    except Exception as e:
        err = f"[WARN] Grobid XML: {e}"
        print_and_log(err)
    return meta, err

def extract_ai_llm_full(first_page, api_key=None, model=None, debug=False):
    api_key = api_key or OPENAI_API_KEY
    error = None
    if not api_key or not api_key.strip():
        error = "[CRIT] OpenAI API key missing/blank for LLM calls!"
        print_and_log(error)
        return {k:"" for k in fields}, error
    try:
        import openai
        openai.api_key = api_key
        prompt = (
            "Extract the following metadata as a JSON object from the text provided: "
            "title, author, year, doi, author_keywords, country, source_journal, study_type. "
            "If a field is missing, leave blank or use null. Text follows:\n" + first_page
        )
        resp = openai.chat.completions.create(
            model=model or llm_model,
            messages=[{"role":"user", "content": prompt}],
            temperature=0, max_tokens=384
        )
        txt = resp.choices[0].message.content.strip()
        if debug:
            print_and_log(f"[DEBUG] LLM RAW RESPONSE:\n{txt}\n---")
        if txt.startswith("```"):
            txt = txt.strip("` \n")
            txt = txt[4:].strip() if txt.lower().startswith("json") else txt
        result = json.loads(txt)
        assert isinstance(result, dict)
        for k in fields:
            result[k] = flatten(result.get(k, ""))
        return {k: result.get(k, "") for k in fields}, None
    except Exception as e:
        error = f"[ERROR] LLM extraction failed: {e}"
        print_and_log(error)
        return {k: "" for k in fields}, error

def extract_crossref_full(doi, title=None, author=None, year=None):
    meta, error = {f: "" for f in fields}, None
    if not allow_internet: return meta, "[INFO] Skipped CrossRef (no internet allowed)"
    try:
        r = None
        if doi:
            url = f"https://api.crossref.org/works/{normalize_doi(doi)}"
            r = requests.get(url, timeout=20)
            dat = r.json()["message"]
        elif title and (author or year):
            qstr = f"{title} {author or ''} {year or ''}".strip()
            url = f"https://api.crossref.org/works?query.bibliographic={requests.utils.quote(qstr)}&rows=1"
            r = requests.get(url, timeout=20)
            items = r.json()["message"].get("items", [])
            dat = items[0] if items else {}
        elif title:
            url = f"https://api.crossref.org/works?query.title={requests.utils.quote(title)}&rows=1"
            r = requests.get(url, timeout=20)
            items = r.json()["message"].get("items", [])
            dat = items[0] if items else {}
        else:
            dat = {}
        meta["doi"] = dat.get("DOI", "")
        meta["title"] = dat.get("title", [""])[0] if dat.get("title") else ""
        meta["author"] = "; ".join(
            "{}, {}".format(a.get("family", "").strip(), a.get("given", "").strip())
            for a in dat.get("author", [])
        ) if dat.get("author") else ""
        meta["year"] = str(dat.get("issued", {}).get("date-parts", [[None]])[0][0]) if dat.get("issued") else ""
        meta["author_keywords"] = "; ".join(dat.get("subject", [])) if dat.get("subject") else ""
        meta["source_journal"] = dat.get("container-title", [""])[0] if dat.get("container-title") else ""
        meta["study_type"] = dat.get("type", "")
        meta["country"] = ""
    except Exception as e:
        error = f"[WARN] CrossRef: {e}"
        print_and_log(error)
    return meta, error

def extract_openalex_full(doi, title=None):
    meta, error = {f: "" for f in fields}, None
    if not allow_internet: return meta, "[INFO] Skipped OpenAlex (no internet allowed)"
    try:
        r = None
        if doi:
            url = f"https://api.openalex.org/works/https://doi.org/{normalize_doi(doi)}"
            r = requests.get(url, timeout=20)
            dat = r.json()
        elif title:
            url = f"https://api.openalex.org/works?title.search={requests.utils.quote(title)}"
            r = requests.get(url, timeout=20)
            dat = r.json().get("results", [{}])[0] if "results" in r.json() else r.json()
        else:
            dat = {}
        doi_val = dat.get("doi", "")
        if doi_val and doi_val.startswith("https://doi.org/"):
            doi_val = doi_val[len("https://doi.org/") :]
        meta["doi"]   = doi_val
        meta["title"] = dat.get("title", "")
        meta["author"] = "; ".join(a.get("author",{}).get("display_name","") for a in dat.get("authorships",[]))
        meta["year"] = str(dat.get("publication_year", ""))
        meta["author_keywords"] = "; ".join(dat.get("keywords", [])) if dat.get("keywords") else ""
        meta["source_journal"] = dat.get("host_venue", {}).get("display_name","") if dat.get("host_venue") else ""
        meta["study_type"] = dat.get("type", "")
        countries = []
        for a in dat.get("authorships", []):
            for inst in a.get("institutions", []):
                cc = inst.get("country_code")
                if cc: countries.append(cc)
        meta["country"] = "; ".join(set([c for c in countries if c]))
    except Exception as e:
        error = f"[WARN] OpenAlex: {e}"
        print_and_log(error)
    return meta, error

RAW_META_DIR = OP_DIR / "audit" / "raw_meta"
RAW_META_DIR.mkdir(parents=True, exist_ok=True)

method_null_counts = {m: {f:0 for f in fields} for m in method_names}
all_paper_tables = []

# -- MAIN Extraction Loop with Path Handling Checked
for idx, pdf in enumerate(pdfs):
    assert isinstance(pdf, (Path, str)), f"Unexpected type for pdf: {type(pdf)} -- value: {pdf}"
    pdf_id = pdf_hash_id(pdf)
    errors = []

    # Use stable local variable names for extracted outputs!
    first_page, err_f = extract_first_page_text(pdf, debug=(idx==0))
    if err_f: errors.append(err_f)
    llm, err_llm = extract_ai_llm_full(first_page, api_key=OPENAI_API_KEY, model=llm_model, debug=(idx==0))
    if err_llm: errors.append(err_llm)
    grobid, err_grobid = extract_grobid_full(pdf)
    if err_grobid: errors.append(err_grobid)
    fitz_meta, err_fitz = extract_fitz_metadata(pdf)
    if err_fitz: errors.append(err_fitz)
    pdfplumber_meta, err_pdfplumber = extract_pdfplumber_metadata(pdf)
    if err_pdfplumber: errors.append(err_pdfplumber)
    filename_meta = extract_from_filename_meta(pdf)

    doi_textscan = search_doi_in_text(pdf)
    if not any([normalize_doi(x.get("doi","")) for x in (grobid, fitz_meta, pdfplumber_meta, filename_meta)]):
        if doi_textscan:
            filename_meta["doi"] = doi_textscan

    doi_for_api = normalize_doi(grobid.get("doi","") or fitz_meta.get("doi","") or pdfplumber_meta.get("doi","") or filename_meta.get("doi","") or llm.get("doi","") or "")
    title_for_api = llm.get("title") or grobid.get("title") or fitz_meta.get("title") or filename_meta.get("title") or ""
    author_for_api = llm.get("author") or grobid.get("author") or fitz_meta.get("author") or filename_meta.get("author") or ""
    year_for_api = llm.get("year") or grobid.get("year") or fitz_meta.get("year") or filename_meta.get("year") or ""
    crossref, err_crossref = extract_crossref_full(doi_for_api, title_for_api, author_for_api, year_for_api)
    if err_crossref: errors.append(err_crossref)
    if not doi_for_api and crossref.get("doi"):
        crossref["doi"] = normalize_doi(crossref["doi"])
        doi_for_api = crossref["doi"]
    openalex, err_openalex = extract_openalex_full(doi_for_api, title_for_api)
    if err_openalex: errors.append(err_openalex)

    method_outputs = {
        "llm":      {k: v for k,v in llm.items()},
        "grobid":   {k: v for k,v in grobid.items()},
        "fitz":     {k: v for k,v in fitz_meta.items()},
        "pdfplumber":{k: v for k,v in pdfplumber_meta.items()},
        "filename": {k: v for k,v in filename_meta.items()},
        "crossref": {k: v for k,v in crossref.items()},
        "openalex": {k: v for k,v in openalex.items()},
    }
    for m in method_names:
        for f in fields:
            orig = method_outputs[m][f]
            if f == "doi":
                method_outputs[m][f] = normalize_doi(orig)
            elif f == "author":
                method_outputs[m][f] = normalize_author(orig)
            elif f == "country":
                method_outputs[m][f] = normalize_country(orig)
            elif f == "author_keywords":
                method_outputs[m][f] = normalize_keywords(orig)
            else:
                method_outputs[m][f] = str(orig).strip() if orig and orig != "null" else ""
    for m in method_names:
        for f in fields:
            val = method_outputs[m][f]
            if (not val) or val.lower() == "null":
                method_null_counts[m][f] += 1

    raw_audit = {
        "pdf_id": pdf_id, "filename": str(pdf),
        "methods": method_outputs,
        "error_log": errors
    }
    with open(RAW_META_DIR / f'{pdf_id}_raw_meta.json', "w", encoding="utf-8") as f:
        json.dump(raw_audit, f, indent=2, ensure_ascii=False)

    df_this_paper = pd.DataFrame({f: [method_outputs[m][f] for m in method_names] for f in fields}, index=method_names)
    all_paper_tables.append({"pdf_id": pdf_id, "fname": str(pdf), "table": df_this_paper})

print('\n--- Null/Blank Value Table (methods × fields, post-normalization) ---')
df_null = pd.DataFrame(method_null_counts)
print(df_null.T)

for d in all_paper_tables:
    print(f"\n\n======== PAPER: {d['pdf_id']} / {d['fname']} ========")
    print(d["table"].to_string())
print(f"\n[INFO] Raw method+error audit JSON written for each PDF in {RAW_META_DIR}")
print("--- End Block 3 v6.4.1 ---")

# --- Cell ---
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

def sha256_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

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

