# Repository Contributor Guide

This document summarizes common development practices for all services in this repository.

---


## Where to Look for Guidance (Per-Service Layout)
- **`.feedback/`**: Task lists and priorities. *Read only*—never edit directly. The old `feedback.md` file has been removed in favor of this directory.
- **`.codex/`** (inside each service directory, e.g., `WebUI/.codex/`, `Rest-Servers/.codex/`):
  - Use it for contributor coordination (tasks, modes, notes). Prefer reading code and docstrings as the source of truth; keep notes minimal and task-scoped.
- **Never edit files in `.codex/audit/` unless you are in Auditor mode.**
- **`.github/`**: Workflow guidelines and UX standards.
- When entering any folder, check for a `AGENTS.md` file in that folder and read it before starting any work there.

---

## Development Basics
- Use [`uv`](https://github.com/astral-sh/uv) for Python environments and running code. Avoid `python` or `pip` directly.
- Use [`bun`](https://bun.sh/) for Node/React tooling instead of `npm` or `yarn`.
- Verification-first: confirm current behavior in the codebase before changing code; reproduce/confirm the issue (or missing behavior); verify the fix with clear checks.
- No broad fallbacks: do not add “fallback behavior everywhere”; only add a narrow fallback when the task explicitly requires it, and justify it.
- No backward compatibility shims by default: do not preserve old code paths “just in case”; only add compatibility layers when the task explicitly requires it.
- Minimal documentation, minimal logging: prefer reading code and docstrings; do not add docs/logs unless required to diagnose a specific issue or prevent a crash.
- Do not update `README.md`.
- Split large modules into smaller ones when practical.
- If a build retry occurs, the workflow may produce a commit titled `"Applying previous commit."` when reapplying a patch.
  This is normal and does not replace the need for your own clear `[TYPE]` commit messages.
- If coding in Python, ensure code is asynchronous-friendly: avoid blocking the event loop, use async/await for I/O and long-running tasks, and keep work off the main loop (e.g., use background tasks or thread/executor for CPU-bound work).
- Any test running longer than 15 seconds is automatically aborted (or force them please...) in local development (using `run-tests.sh`). GitHub Actions CI has no timeout limits.
- For Python style:
   - Place each import on its own line.
   - Sort imports within each group (standard library, third-party, project modules) from shortest to longest.
   - Insert a blank line between each import grouping (standard library, third-party, project modules).
   - Avoid inline imports.
   - For `from ... import ...` statements, group them after all `import ...` statements, and format each on its own line, sorted shortest to longest, with a blank line before the group. Example:

     ```python
     import os
     import time
     import logging
     import threading

     from datetime import datetime
     from rich.console import Console
     from langchain_text_splitters import RecursiveCharacterTextSplitter
     ```

## File Size and Readability (Repository-wide Rule)
- Aim for ~300 lines or fewer per file.
- Split monolithic modules into smaller units when they grow beyond this threshold.
- Keep code well commented and organized for readability.

---

## Commit and Pull Request Workflow
Follow this checklist whenever you are ready to publish work:

1. Stage and review your changes locally (`git status`, `git diff`) before committing.
2. Create a descriptive commit that begins with the appropriate `[TYPE]` prefix.
3. Verify the working tree is clean after committing—`git status` must show **no pending changes**.
4. Immediately call the `make_pr` tool to draft the pull request summary and title once the commit is created.
5. Never call `make_pr` before your changes are committed, and never finish a task without creating a pull request for committed work.
6. If you did not modify the repository, do **not** commit or call `make_pr`.

These steps apply to **all** contributor modes. Managers should remind their teams of this workflow whenever new instructions are published.

---

## Contributor Modes
The repository supports several contributor modes to clarify expectations and best practices for different types of contributions:

> **MANDATORY: All contributors must read their mode's documentation in `.codex/modes/` before starting any work. Failure to do so may result in removal from the repository.**
>
> Recent incidents (e.g., a coder updating audit files 3 times without following mode guidelines) have shown that skipping these docs leads to wasted effort and rework. This is not optional—review your mode doc every time you contribute.

**Mode selection rule:** When a request begins with the name of a mode (e.g., "Manager", "Coder", "Reviewer"), treat that as the required mode for the task unless explicitly told otherwise. Switch to that mode's instructions before continuing.

**All contributors should regularly review and keep their mode cheat sheet in `.codex/notes/` up to date.**
Refer to your mode's cheat sheet for quick reminders and update it as needed.

- **Task Master Mode** (`.codex/modes/TASKMASTER.md`)
- **Manager Mode** (`.codex/modes/MANAGER.md`)
- **Swarm Manager Mode** (`.codex/modes/SWARMMANAGER.md`)
- **Coder Mode** (`.codex/modes/CODER.md`)
- **Reviewer Mode** (`.codex/modes/REVIEWER.md`)
- **Auditor Mode** (`.codex/modes/AUDITOR.md`)
- **Storyteller Mode** (`.codex/modes/STORYTELLER.md`)
- **Unknown Mode** (no file)

You must refer to the relevant mode guide in `.codex/modes/` before starting work. For service-specific details, read the service's own `AGENTS.md` and follow existing in-repo guidance.

### Documentation sync
Prefer code and docstrings as the canonical source; keep notes minimal and task-scoped.
