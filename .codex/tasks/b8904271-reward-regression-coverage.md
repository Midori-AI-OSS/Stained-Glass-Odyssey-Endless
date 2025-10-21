# Expand reward overlay regression coverage

## Summary
Add automated tests and fixtures that exercise the new countdown advance, confirm flows, and multi-phase transitions introduced in the reward overlay overhaul.

## Requirements
- Identify the appropriate testing layers (unit, integration, end-to-end) covering the reward overlay today and extend them to cover each new phase.
- Create fixtures or mocked responses containing representative `reward_progression` data for single-phase, full four-phase, and skip-phase scenarios.
- Write tests verifying the countdown auto-advance, manual advance button, card confirm, and relic confirm behaviours fire the expected events.
- Ensure tests cover keyboard accessibility (e.g., focus order) where feasible, or document manual QA steps where automation cannot reach.
- Update CI pipelines or scripts to include the new tests so regressions block merges.

## Coordination notes
- Work with the automation task owner to share fixtures and avoid duplication.
- Coordinate with QA to review new coverage and identify any remaining gaps needing manual test cases.
ready for review
