# Testing and Iteration

1. Unit tests for menus, stat screen, map navigation, gacha logic, and data wiring.
2. Run `uv run pytest` after each major change.
3. Review and update build scripts for Windows, Linux, and Android:
   - Audit `builder/` scripts per OS.
   - Verify web UI and dependency bundling.
   - Perform smoke builds for cross-platform checks.
4. Add a **Give Feedback** menu button that opens a pre-filled GitHub issue.
5. Update `.codex/planning` with follow-up tasks as features stabilize.
6. Code structure:
   - Configure pytest fixtures for backend endpoints; frontend tests are handled separately.
   - Add CI workflow steps to run tests and lint on pushes and pull requests.
