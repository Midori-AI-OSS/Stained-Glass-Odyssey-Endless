# Backend Contributor Guide

> **MANDATORY:** Before touching any file under `backend/`, open your mode
document in `.codex/modes/` and review it in full. This applies to everyone,
including reviewers performing drive-by checks. Work may be rejected if your
mode expectations are not followed.

---

## Quick Orientation
- The backend is a [Quart](https://quart.palletsprojects.com/) ASGI
  application defined in `backend/app.py` with supporting blueprints under
  `backend/routes/`. Keep new endpoints asynchronous and compatible with the
  existing background task patterns described in `backend/.codex/implementation`.
- Python tooling is standardized on [`uv`](https://github.com/astral-sh/uv).
  Use `uv sync` to install dependencies and `uv run` (or `uvx`) for commands.
  Do **not** rely on `pip`, `python -m venv`, or system interpreters.
- Read `backend/README.md` before making structural changes. It documents
  deployment expectations, telemetry flows, and services (LLM, TTS, logging,
  metrics) that new code must respect.

## Testing and Verification
- Prefer the curated helpers in `run-tests.sh` when running checks from the
  repository root. The script wires up environment variables and selects the
  right test suites for typical scenarios.
- Backend unit tests live in `backend/tests/`. Use `uv run pytest backend/tests`
  for targeted runs when you need to focus on this service. Avoid running the
  entire repo's test matrix unless your change requires it.
- If you add or modify battle logic, consult the docs in
  `backend/.codex/implementation/` to keep design notes up to date.

## Coordination Notes
- Major adjustments to data models, migrations, or background workers must be
  coordinated with the Lead Developer before merging.
- When updating documentation or operational playbooks, keep the relevant files
  in `.codex/implementation/` synchronized with the code changes.
