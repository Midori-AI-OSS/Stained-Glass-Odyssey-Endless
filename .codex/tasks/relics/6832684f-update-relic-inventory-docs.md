# Task: Sync Relic Inventory Documentation with Current Implementations

## Background
The implementation guide at `.codex/implementation/relic-inventory.md` is out of sync with several relic behaviors. Notably, it still claims Killer Instinct grants extra turns on kills, Timekeeper's Hourglass grants extra turns, and Soul Prism remains a placeholder.【F:.codex/implementation/relic-inventory.md†L12-L38】 The codebase has since replaced those behaviors with specific buff logic and a fully realized revival flow.【F:backend/plugins/relics/killer_instinct.py†L11-L155】【F:backend/plugins/relics/timekeepers_hourglass.py†L11-L113】【F:backend/plugins/relics/soul_prism.py†L11-L101】 Keeping the documentation accurate is critical for player tooling and for onboarding contributors.

## Objectives
1. Update the relic entries in `.codex/implementation/relic-inventory.md` to describe the actual mechanics of Killer Instinct, Timekeeper's Hourglass, and Soul Prism, removing obsolete mentions of extra turns and placeholder text.
2. Verify the rest of the relic list for any other drift from the current implementations and refresh descriptions as needed.
3. If any additional mechanical nuances are discovered while reviewing, cross-link or update related implementation docs so the knowledge stays coherent.
4. Note any follow-on work (e.g., missing frontend tooltip updates) as separate tasks if required.

## Acceptance Criteria
- The relic inventory documentation matches the mechanics implemented in the backend relic plugins.
- All outdated claims about extra turns or placeholder status are removed or corrected.
- Any supplementary docs touched by the changes remain internally consistent.
- The update passes repository documentation checks (linting/formatting, if applicable).
ready for review
