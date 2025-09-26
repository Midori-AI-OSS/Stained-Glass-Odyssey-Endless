Superseded: This epic has been decomposed into smaller actionable tasks.

Please work on the following task files instead:
- `6a8ad619-webui-run-state-store.md`
- `e0ef9019-webui-polling-orchestrator.md`
- `f152ac25-webui-overlay-gating.md`
- `05990b91-webui-root-state-transition-docs.md`

Once those tasks are complete, revisit this stub and close it out.

Progress update (2025-09-25): established a reusable `runStateStore` with unit coverage to centralize run metadata persistence.
Progress update (2025-09-26): replaced `window.af*` overlay globals with shared overlay gating stores, updated root/page consumers, and added unit coverage for the new helpers.
Progress update (2025-09-27): captured run-state, overlay gating, and polling orchestrator integration guidance plus migration/QA checklists in the frontend implementation docs.
Progress update (2025-09-28): landed a shared polling orchestrator with store-backed handlers, migrated `+page.svelte` off manual UI state timers, and covered the new controller in unit tests.
Progress update (2025-09-30): Corrected documentation to reflect that the run store and orchestrator are still partially integrated; the root page remains the active source of truth until follow-up coding work lands.
Pending additional coding follow-up before this epic is ready for review.
