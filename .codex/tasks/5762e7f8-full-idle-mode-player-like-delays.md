# Rework Full Idle Mode to mimic player pacing and enforce battle review skipping

## Problem
Full Idle Mode currently fires reward actions as soon as the overlay exposes them, producing instantaneous loot acknowledgements, card selections, and relic confirmations. That bursty behaviour looks robotic, skips natural pauses between phases, and leaves the Battle Review toggle independent of automation. Luna requested that automation feel like an actual player: wait for UI affordances to settle, choose rewards after short delays, then advance with an additional beat. Full Idle Mode should also ensure Skip Battle Review remains on so automation can immediately continue to the next room.

## Why this matters
* QA and telemetry expect human-like pacing so timing-based detectors or analytics can treat automated runs as closer to real players.
* Current automation can conflict with countdown messaging in `RewardOverlay.svelte` because it advances phases before the UI finishes animating staged choices.
* Leaving Skip Battle Review optional causes Full Idle Mode to stall on the intermediate summary screen, defeating the goal of unattended runs.

## Requirements
* Audit the reward automation helpers used by Full Idle Mode:
  * Update `frontend/src/routes/+page.svelte` so `maybeAutoHandle` no longer issues immediate `handleRewardAdvance`, `chooseCard`, `chooseRelic`, or `handleLootAcknowledge` calls. Introduce a lightweight scheduler that queues a single automation action at a time and inserts realistic pauses (e.g., ~600–900 ms after loot appears, ~750–1200 ms before selecting a card or relic, and an additional ~500 ms before confirming/advancing). The exact timings can live in a small helper but should be easy to tweak and respect Reduced Motion if necessary.
  * Ensure the scheduler still respects the existing `rewardAdvanceInFlight`, `autoHandling`, and `lootAckBlocked` guards so manual inputs and reconnects cannot interleave conflicting commands.
  * Guarantee that when a phase still has staged entries (cards or relics), automation waits for the backend confirmation before scheduling the advance delay.
* Update `frontend/src/lib/utils/rewardAutomation.js` (and any other helper touched by the scheduler) as needed so automation still picks deterministic choices but exposes metadata (e.g., desired delay kind) if it helps the new pacing logic. Keep test coverage in sync with the new return signature if it changes.
* Enforce Skip Battle Review when Full Idle Mode is on:
  * When the user enables Full Idle Mode via `GameplaySettings`/`SettingsMenu`, automatically set `skipBattleReview` to `true` and persist that change through `settingsStorage`.
  * While Full Idle Mode remains active, keep Skip Battle Review locked on (disable the toggle or show it checked + read-only) so automation cannot get stranded on the review overlay.
  * Allow Skip Battle Review to return to the user’s previous setting when Full Idle Mode is turned off.
* Update automated coverage:
  * Extend or add Vitest tests (e.g., in `frontend/tests/reward-automation.vitest.js` or a new spec) that mock timers to verify the scheduler waits the expected durations before invoking handlers and that enabling Full Idle Mode flips Skip Battle Review in persisted settings.
  * Adjust `frontend/tests/skip-battle-review-setting.test.js`, `frontend/tests/actionqueue.test.js`, and any other impacted snapshots to reflect the locked toggle state and new automation metadata.
* Documentation and UX notes:
  * Update `.codex/instructions/options-menu.md` to describe the Skip Battle Review coupling and the human-paced automation behaviour.
  * Append implementation details to `.codex/implementation/reward-overlay.md` (and `post-fight-loot-screen.md` if needed) noting the queued delays and how automation now mirrors player cadence.
  * Call out any new telemetry or logging needed so QA can confirm the pacing in manual tests.

## Definition of done
* Full Idle Mode issues exactly one automated action at a time, each preceded by the configured delay, and still completes the Drops → Cards → Relics → Battle Review loop without hanging.
* Skip Battle Review toggles on automatically whenever Full Idle Mode is active, cannot be disabled during automation, and restores the prior user preference after disabling Full Idle Mode.
* Vitest coverage confirms the queued delays and skip-battle coupling, and all existing automation tests remain green with the new behaviour.
* Documentation under `.codex/` reflects the updated automation pacing and settings contract so future contributors understand the intent.
