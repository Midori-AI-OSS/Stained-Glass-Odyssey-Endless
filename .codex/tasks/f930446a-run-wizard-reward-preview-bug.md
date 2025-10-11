# Task: Fix Run Wizard Reward Preview Showing Identical EXP/RDR Values

## Background
Players configuring modifiers in the Run Wizard rely on the reward preview card to understand how stacks change EXP and Rare Drop Rate (RDR). The backend defines dramatically different per-stack bonuses for foe-focused modifiers (EXP +0.50 vs RDR +0.01) in `backend/services/run_configuration.py`, and the frontend utility `frontend/src/lib/utils/rewardPreview.js` is supposed to sum these separately.

## Problem Statement
On the live Run Wizard (Configure Modifiers step), the reward preview card displays the same percentage for "EXP Bonus" and "RDR Bonus". The user confirmed the issue against the backend at `http://192.168.10.27:59002`. This contradicts the intended balance (RDR should be much lower than EXP) and misleads players when they pick modifiers.

## Reproduction Steps
1. Open the Run Wizard in the WebUI, proceed to **Configure Modifiers**.
2. Add stacks to any foe modifier that grants rewards (e.g., Foe Speed / Foe HP).
3. Observe the Reward Preview card: the EXP and RDR rows show the same formatted value even though they should differ.

## Investigation Notes
- Backend metadata (`_MODIFIER_DEFINITIONS` in `backend/services/run_configuration.py`) sets `exp_bonus_per_stack` to `0.50` and `rdr_bonus_per_stack` to `0.01` for foe modifiers.
- Frontend aggregation occurs in `frontend/src/lib/utils/rewardPreview.js` and is rendered through `RewardPreviewCard.svelte`.
- Need to verify whether `/run/config` is returning incorrect `rdr_bonus_per_stack`, or if the frontend is overwriting/misreading RDR bonuses when building the preview (e.g., fallback logic that prefers EXP values).

## Requested Work
- Capture the actual `/run/config` payload from the running backend to confirm what values the UI receives.
- Trace the data flow through `RunChooser.svelte` and `rewardPreview.js` to identify where RDR is being duplicated or replaced with EXP.
- Implement the fix (backend and/or frontend) so the preview shows accurate, distinct EXP vs RDR totals.
- Add a regression test (frontend unit or integration) that asserts differing per-stack values produce distinct EXP/RDR preview numbers.
- Update any relevant docs in `.codex/implementation/` if the data contract changes.

## Acceptance Criteria
- Reward Preview card displays the correct RDR bonus when modifiers grant both EXP and RDR, matching backend math (e.g., EXP ≫ RDR for foe modifiers).
- Automated coverage exists to prevent the EXP/RDR values from unintentionally matching again.
- Documentation stays in sync with any code/API adjustments.

## References
- Backend definitions: `backend/services/run_configuration.py:200`
- Frontend preview logic: `frontend/src/lib/utils/rewardPreview.js`
- Run Wizard view: `frontend/src/lib/components/RunChooser.svelte`
