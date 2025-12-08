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

## Agent System Integration

**Important:** AutoFighter uses the [Midori AI Agent Framework](https://github.com/Midori-AI-OSS/agents-packages) for LRM/LLM management.

### Working with Agents

When working on agent-related code:

1. **Clone or import the framework** to review documentation:
   ```bash
   # Option 1: Clone for reference
   git clone https://github.com/Midori-AI-OSS/agents-packages /tmp/agents-packages
   
   # Option 2: Import and read embedded docs
   uv add "git+https://github.com/Midori-AI-OSS/agents-packages.git#subdirectory=midori-ai-agents-all"
   ```

2. **Report issues** to the framework, not this repo:
   - Agent framework issues: `.codex/agents-packages/issues` (in framework repo)
   - AutoFighter integration issues: Standard issue tracker

3. **Primary backend**: Midori AI OpenAI agents system
   - For users with OpenAI API or compatible servers (Ollama, LocalAI, etc.)
   
4. **Fallback backend**: Midori AI HuggingFace agents system
   - For local inference without external dependencies

5. **Logger**: Use the logger from the agents packages for all logging (replace `print` statements)
   ```python
   from midori_ai_logger import get_logger
   log = get_logger(__name__)
   ```

### Breaking Changes Policy

**We intentionally break backward compatibility** during the agent migration to identify and fix issues faster. Do not add compatibility layers or fallbacks to old code.

## Coordination Notes
- Major adjustments to data models, migrations, or background workers must be
  coordinated with the Lead Developer before merging.
- When updating documentation or operational playbooks, keep the relevant files
  in `.codex/implementation/` synchronized with the code changes.
