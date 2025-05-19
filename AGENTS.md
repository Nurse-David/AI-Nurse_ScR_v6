# Agent Guidelines

## Project Overview
- This repository contains the **AI Nurse Scoping Review** extraction pipeline, located in `ai_nurse_scr/`.
- The command line interface is invoked with `python -m ai_nurse_scr.cli`.

## Coding Conventions
- Target **Python ≥3.10**.
- Follow standard **PEP8** formatting.
- Document new functions and classes with docstrings.

## Testing Instructions
Before committing, run the unit tests:
```bash
python -m unittest discover tests -v
```
Ensure all tests pass (or explain any failures).

## Commit Guidance
- Write meaningful commit messages summarizing your changes.
- Avoid committing large binaries or secrets such as API keys.

## Pull Requests / Contributions
- Summarize the purpose of each PR in the description.
- Link relevant issues or feature requests.
- Note if new dependencies are introduced and update `requirements.txt` accordingly.

## Directory Notes
- `ai_nurse_scr/` – main package.
- `tests/` – test suite.
- `notebooks/` – example notebooks (not required for normal testing).
