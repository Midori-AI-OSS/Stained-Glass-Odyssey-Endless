# Frontend Contributor Instructions

> **Lead Notice:** Before authoring or reviewing any frontend change, re-read your assigned mode documentation in `.codex/modes/` and confirm you are working under the correct role guidance. Managers, Coders, Reviewers, and other roles must verify current expectations **every time** so process updates are not missed.

## Workflow Expectations
- Keep this directory's guidance in sync with the repository root `AGENTS.md` and the documentation stored in `.codex/`. Surface gaps to the Lead Developer and Task Master when you spot them.
- Review `frontend/README.md` prior to significant UI work; it documents the runtime behavior, assets, and integration flows that components depend on.
- Use Bun for all Node tooling:
  - `bun install` to sync dependencies.
  - `bun dev` for the SvelteKit dev server (default port `59001`).
  - `bun run build` only when generating static output or verifying Docker/Tauri behavior—ensure `svelte-kit sync` has been executed (handled automatically by the `prepare` script).
- Prefer incremental commits that isolate UI, logic, and asset updates so reviewers can trace changes cleanly.

## Svelte Conventions
- Follow idiomatic Svelte 5 patterns: leverage reactive statements (`$:`), stores, and component props instead of manual DOM mutation.
- Co-locate component-specific helpers under `src/lib` and keep files under ~300 lines; split complex widgets into focused child components.
- Honor accessibility defaults (aria labels, keyboard navigation) and Reduced Motion settings documented in `frontend/README.md`.
- Keep styling inside `<style>` blocks scoped to the component when possible. Promote shared styles to global layers only when they are reused broadly.

## Testing Standards
- Run targeted tests with Bun's test runner or Vitest before submitting changes:
  - `bun test` for the full suite when changes are broad.
  - `bun test tests/<file>.test.ts` (or similar path/pattern) for focused runs during iteration.
  - For Vitest-specific options, use `bun x vitest run <pattern>` to reproduce CI behavior.
- Capture and address console warnings during test runs; unresolved warnings block approval.

## Review Checklist
- Confirm updated components respect the data contracts described in `frontend/README.md` and associated `.codex/implementation/` notes (e.g., snapshot polling, reward overlays, asset loading).
- Verify new dependencies are Bun-compatible and pinned in `bun.lock` via `bun add`.
- Document any process or instruction gaps encountered so Manager mode can update this file or supporting docs.
