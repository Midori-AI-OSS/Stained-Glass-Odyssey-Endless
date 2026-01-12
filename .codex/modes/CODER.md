
# Coder Mode

> **Note:** Prefer the codebase and docstrings as the source of truth. Keep notes minimal and task-scoped; avoid creating long-lived documentation artifacts unless explicitly requested.


## Purpose
For contributors actively writing, refactoring, or reviewing code. Coder Mode emphasizes high-quality, maintainable contributions that are easy for others to understand and build upon.


## Guidelines
- Follow all repository coding standards, style guides, and best practices.
- **Recommended**: Run linting before every commit. For backend Python code: `ruff check . --fix` and address any remaining issues manually.
- **Task Status**: Tasks are organized by status in `.codex/tasks/`. Pick up tasks from `.codex/tasks/wip/` and move them to `.codex/tasks/review/` when complete. If more work is needed after review, tasks will be moved back to `.codex/tasks/wip/` with feedback.
- Regularly review the `.codex/tasks/wip/` folder for new or assigned tasks, and pick up work from there as requested by the Task Master or project leads.
- Write clear, maintainable, well-commented, and well-documented code with meaningful variable and function names.
- Add or update tests for all changes; ensure high test coverage and passing tests.
- Re-run only the tests affected by your change. Use the commands in `run-tests.sh` as your baseline and scope them to the impacted area—e.g., backend checks with `uv run pytest tests/test_battle.py -k scenario_name` or node IDs like `uv run pytest tests/test_battle.py::TestBattle::test_scenario_name`, and frontend checks with `bun test tests/ui-navigation.test.js` or focused runs such as `bun x vitest run ui-navigation --run`. When the repository's `run-tests.sh` filters are available, pass them to skip untouched services; otherwise rely on the targeted commands above so you iterate quickly without skipping required coverage.
- Use the recommended tools (`uv` for Python, `bun` for Node/React) for consistency and reproducibility.
- When working on frontend features, review the Svelte documentation and existing components in `frontend/src/`. The application uses a web-based architecture with a Svelte frontend and Quart backend.
- Verification-first: confirm current behavior before changing code; reproduce/confirm the issue (or missing behavior); verify the fix with clear checks.
- Keep docstrings accurate; avoid creating long-lived documentation artifacts unless explicitly requested. For relics, cards, and passives, treat the plugin modules as the canonical source.
- Break down large changes into smaller, reviewable commits or pull requests.
- Review your own code before submitting for review, checking for errors, clarity, and completeness.
- **Never edit audit or planning files (see Prohibited Actions below).**
- Ignore time limits—finish the task even if it takes a long time.

## Typical Actions
- Review the `.codex/tasks/wip/` folder for new or assigned tasks
- **Run linting checks** (`ruff check . --fix`) before starting work and before each commit
- Implement new features or enhancements
- Fix bugs or technical debt
- Refactor modules for clarity, performance, or maintainability
- Keep docstrings accurate and aligned with behavior.
- Review code from others and provide constructive feedback
- Write or update tests
- Move completed tasks from `.codex/tasks/wip/` to `.codex/tasks/review/`
- **Ensure all linting issues are resolved** before submitting pull requests

## Prohibited Actions
**Do NOT edit audit or planning files.**
- Never modify files in `.feedback/`, `.codex/audit/`, `.codex/planning`, or `.codex/review` (or any other audit/planning directories). 
    - These are managed by Task Masters, Auditors, and Reviewers only.
- These files are read-only for coders. Editing them disrupts project planning and audit processes, and is grounds for removal from the repository.
- If you believe a planning or audit file needs to be updated, notify the Task Master instead of editing it yourself.
    - Ways to notify Task Master
        - update the task file with comments (Recommended)
        - tell the reviewer that sent you the request
        - add it to your pr message (Not recommended)
        - add comments in the code (Best way)

## Communication
- Announce start, progress, and completion of tasks directly in the relevant task file or pull request so reviewers and Task Masters can track status without a separate channel.
- When completing a task, move it from `.codex/tasks/wip/` to `.codex/tasks/review/` to signal it's ready for auditor review.
- Clearly describe the purpose and context of your changes in commit messages and pull requests.
- Reference related issues, documentation, or discussions when relevant.
- Prefer referencing code/docstrings and the relevant task file; keep notes minimal and task-scoped.
