# Implement themed daily login buffs tied to streak progress

## Problem
The daily login rewards system currently exposes a single "Run Drop Rate" (RDR) bonus that scales with extra rooms cleared on a reward day. Design wants each reward day of the week to apply a themed bonus that still scales off Rooms Cleared × Daily Streak with diminishing returns while keeping the existing RDR bonus intact. Sunday should continue to reward EXP gain for characters, Saturday should still boost all core stats, and Monday–Friday must revolve around elemental damage types (Fire, Ice, dual Light/Dark, Wind, and Lightning). For those weekdays we also need to grant extra drops aligned with the themed damage type and simultaneously increase the party's outgoing damage while reducing incoming damage of the matching type. None of the backend, party hydration, or frontend paths understand these new mixed stat/damage-type bonuses today. The modernized Login Rewards menu layout has already landed, so we must keep the updated structure while fixing the now-broken component tests that still assume the previous markup.

## Why this matters
* Themed buffs give players a reason to keep logging in on specific days and to continue clearing rooms after the automatic bundle unlocks.
* Without backend support, we cannot expose the buff values to the UI nor apply them during party hydration or combat damage checks, so the feature would be invisible and ineffective.
* Keeping documentation and automated tests in sync is necessary to prevent future regressions around streak math, timezone resets, reward previews, and damage-type reward logic.

## Requirements
* **Backend – login reward service (`backend/services/login_reward_service.py`):**
  * Introduce a per-day configuration that maps the PT reward day (`_reward_day(now).weekday()`) to a themed buff definition. Convert the provided percentages to decimal multipliers/additive bonuses:
    * Sunday → EXP multiplier, 0.001% ⇒ `0.00001` base per extra room × streak.
    * Monday → Fire theme, 5% ⇒ `0.05` base per extra room × streak applied to Fire damage dealt, Fire damage taken reduction, and bonus Fire upgrade item drop weight.
    * Tuesday → Ice theme, 5% ⇒ `0.05` base per extra room × streak applied to Ice damage dealt, Ice damage taken reduction, and bonus Ice upgrade item drop weight.
    * Wednesday → Dual Light/Dark theme, 5% ⇒ `0.05` base per extra room × streak that simultaneously covers Light and Dark damage dealt/taken and both Light and Dark drop weights.
    * Thursday → Wind theme, 5% ⇒ `0.05` base per extra room × streak applied to Wind damage dealt/taken and Wind drop weight.
    * Friday → Lightning theme, 5% ⇒ `0.05` base per extra room × streak applied to Lightning damage dealt/taken and Lightning drop weight.
    * Saturday → All stats theme, 0.0001% ⇒ `0.000001` base per extra room × streak applied multiplicatively to HP/ATK/DEF and additively to crit stats (retain the original behavior), plus a small universal damage-type drop weight bump so the day is still enticing.
  * Reuse the diminishing returns logic already implemented for RDR. Extract `_calculate_daily_rdr_bonus` so it accepts a base rate and returns a capped scalar, then call it for the RDR bonus (with the existing `0.0001`) and each themed buff. Each weekday entry should resolve to a structure that includes:
    * the stat buffs (e.g., `exp_multiplier`, `all_stat_multiplier`),
    * the damage-type payload (`damage_type`, `damage_bonus`, `damage_reduction`, and `drop_weight_bonus`), allowing Wednesday to list two damage types in one structure,
    * and any frontend display hints (friendly label, formatted percentages, themed icon keys).
  * Persist the themed buff map in `LoginRewardState.extra` (e.g., `daily_theme_bonuses`) alongside `DAILY_RDR_BONUS_KEY`, and ensure `_refresh_state` + `_update_daily_rdr_bonus` (or a renamed helper) recompute and store both the drop-rate and themed buff outputs whenever rooms or streak change.
  * Extend the serialized status payload returned by `get_login_reward_status` with the active weekday metadata, the themed buff identifier (e.g., `"fire_theme"`), computed values after diminishing returns, and the damage-type drop bonuses so the frontend can present everything.
  * Provide an async accessor (and matching `*_sync` helper) to retrieve the themed buff map for both party hydration and loot reward code, similar to `get_daily_rdr_bonus`/`get_daily_rdr_bonus_sync`.
  * Update `record_room_completion` and `claim_login_reward` flows to recompute/save themed bonuses alongside the existing RDR bonus so they stay in sync across auto-claim and manual claim paths.

* **Backend – party hydration and combat application (`backend/runs/party_manager.py`, `backend/autofighter/stats.py`, and related helpers):**
  * Load the themed bonus map via the new accessor during party creation. Apply the active buff exactly once per party load in the same section that currently applies `run_user_level` and `login_rdr_bonus` adjustments.
  * Map each buff to concrete stat adjustments:
    * EXP → multiply each member’s `exp_multiplier` by `(1 + bonus)`.
    * All stats → multiply `_base_max_hp`, `_base_atk`, and `_base_defense`, and recompute derived values; add to `_base_crit_rate`/`_base_crit_damage`.
    * Damage-type themes → for each affected damage type, multiply outgoing damage modifiers (e.g., hooks in `Stats` or damage-type plugins) by `(1 + damage_bonus)` and apply an incoming reduction (e.g., scale resistances or damage mitigation hooks) by `(1 - damage_reduction)`.
  * Surface the applied bonuses on the hydrated `Party` object (e.g., attributes like `login_theme_buffs`) so downstream systems/tests can introspect them.
  * Ensure combat calculations respect the stored bonuses. If necessary, extend `Stats` or damage-type plugin helpers so they consult the login theme metadata when calculating damage dealt or taken for the relevant element.
  * Extend `backend/tests/test_login_rewards.py` (or add a new suite) to cover the party integration: load a party on each weekday with mocked streak/room counts and assert stat deltas, damage-type multipliers, and drop-weight metadata align with the computed values (use `pytest.approx` for floats).

* **Backend – loot and reward services (`backend/services/run_service.py`, `backend/autofighter/rooms/rewards.py`, or whichever module handles damage-type upgrade item rolls):**
  * Thread the active themed drop bonuses into the reward calculation path so that Fire/Ice/etc. upgrade item odds receive the advertised weighting on the correct weekdays. Document whether this stacks multiplicatively or additively with existing RDR effects.
  * Add unit coverage verifying that the damage-type drop weights change when the login theme bonuses are present and revert when the bonus expires.

* **Frontend – Login Rewards panel (`frontend/src/lib/components/LoginRewardsPanel.svelte`):**
  * Preserve the recently merged menu layout/styling improvements; treat the new structure as the baseline while addressing regressions.
  * Update the Vitest/Playwright suites under `frontend/tests/` so selectors, snapshots, and mocked payloads reflect the current DOM and copy, covering both the RDR bonus and the themed buff display (exercise at least one single-element weekday and Wednesday’s dual Light/Dark scenario).
  * Add or refresh assertions that verify the descriptive labels/tooltips introduced with the redesign so the improved UX remains covered by automated checks.
  * Re-validate ARIA attributes and screen-reader text in the tests to confirm accessibility stays aligned with the new markup.

* **Documentation and planning sync:**
  * Update `.codex/implementation/login-reward-system.md` with a new section describing themed buffs, including the weekday mapping, scaling math, and persistence details, and now highlighting the damage-type bonuses/drop weighting.
  * Refresh `.codex/docs/login-rewards-panel.md` (and associated SVG annotations if needed) to reflect the expanded UI and the new damage-type visuals.
  * If planning files or roadmaps reference the login reward system, append notes about the damage-type themed buffs so future tasks stay aligned.

* **Quality checks:**
  * Run the relevant backend test module (`uv run pytest backend/tests/test_login_rewards.py`) and any new/updated loot or reward tests, plus the frontend specs (`bun x vitest run <pattern>` / Playwright suites).
  * Capture before/after screenshots for the Login Rewards panel if the UI layout changes significantly (attach via the existing screenshot workflow).

## Definition of done
* Backend state tracking returns both RDR and themed buff outputs, persists them across reward days, and exposes helpers so other systems can consume the data.
* Party hydration applies the correct stat bonuses for the active reward day, exposes metadata for verification, and combat hooks respect the outgoing/incoming damage modifiers.
* Loot generation increases the drop weight for the specified damage-type upgrade items on the correct weekdays.
* The Login Rewards panel retains the refreshed layout while surfacing the active themed buff alongside the RDR bonus with updated copy/tooltips, and the adjusted automated tests pass.
* Documentation in `.codex/implementation` and `.codex/docs` is synchronized with the new feature.
* Automated tests covering the new logic pass locally.
* Updated `frontend/tests/login-rewards-panel.vitest.js` assertions so the redesigned panel layout passes Vitest again.

ready for review
