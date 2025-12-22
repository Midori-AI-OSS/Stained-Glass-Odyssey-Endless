# Python Idle Game — Prototype Overview

Overview
- Small PySide6-based idle-game prototype created by the developer for experimentation.
- GUI entrypoint: `idle_game/main.py` (uses `PySide6`).

Status
- Prototype / work-in-progress. May be incomplete, unstable, and can change without notice.
- Do not build production features against this code. Work here only when explicitly requested.

Quick Requirements
- Python 3.13 or newer
- `PySide6` (Qt bindings)

Quick Run (developer)
1. Create/activate a virtual environment and install dependencies (example):

```bash
python -m venv .venv
source .venv/bin/activate
pip install pyside6
```

2. Run the GUI from the repository root:

```bash
python main.py
# or using repo tooling if available: `uv run main.py`
```

Notes
- Save files and settings are stored under `idle_game/data` (e.g., `save.json`, `settings.json`).
- The project expects character data in `idle_game/data/characters.json`.
- The UI is basic and intended for experimentation: feel free to view code, but change only with explicit approval.
