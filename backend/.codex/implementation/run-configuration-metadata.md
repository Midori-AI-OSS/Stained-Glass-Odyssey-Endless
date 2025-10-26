# Run Configuration Metadata Service

## Overview

Run setup now flows through a metadata-backed configuration layer. The
`services/run_configuration.py` module defines canonical run types and modifier
definitions and exposes helpers for validation and analytics snapshots. The UI
and `/run/start` endpoint share this contract so selections are validated once
and stored with the run record.

## Metadata Endpoint

- **Route:** `GET /run/config`
- **Handler:** `routes/ui.py::run_configuration_metadata`
- **Payload:**
  - `version` (string) – metadata version identifier.
  - `generated_at` (UTC ISO timestamp) – time the payload was generated.
  - `run_types` (list) – available run type definitions with default modifier
    presets.
  - `modifiers` (list) – modifier definitions including category, minimum stack
    counts, whether stacks grant reward bonuses, and tooltip data. Stacks are no
    longer hard capped; validation only enforces the documented minimums and
    converts numeric input.
- `pressure.tooltip` – canonical tooltip text summarizing encounter sizing,
  defense floors, elite odds, and shop tax scaling for pressure stacks.

### Modifier Notes

- `foe_hp` applies a +150× additive multiplier (15,000% increase) to both max
  and current HP for each stack before diminishing returns. Preview rows show
  the raw multiplier alongside the diminished effective value so designers can
  size late-game encounters against the new scaling curve.
- `foe_mitigation` and `foe_vitality` now apply +2.50 additive bonuses per stack
  before diminishing returns. The metadata snapshot stores the full per-stack
  value alongside the diminished effective bonus so downstream systems such as
  spawn pressure and the foe factory can apply consistent scaling.
- `character_stat_down` now applies a 0.0001× overflow penalty past 500 stacks
  and publishes the `cap_threshold_stacks` and `stacks_above_cap` values in the
  snapshot. Total penalties clamp below 100% (0.999) so player stats never hit
  zero. Once penalties cross the 95% threshold (`cap_threshold_stacks`, 5,000
  stacks with the current coefficients) rare-drop bonuses stop increasing while
  experience gains trickle at 1/25th the usual pace per additional stack. Those
  excess stacks also feed a 1% per-stack foe multiplier across HP, ATK, DEF,
  SPD, and Vitality which is exposed through
  `RunModifierContext.foe_overflow_multiplier`.

Telemetry records a `Run/view_config` menu action so analytics can measure how
often the setup flow is opened.

## Validation Flow

`validate_run_configuration` accepts a run type identifier, optional modifier
payload, and the legacy `pressure` fallback. The helper:

1. Loads metadata and resolves the run type (defaulting to `standard`).
2. Merges the run type defaults with provided modifiers.
3. Applies the legacy `pressure` integer when the caller does not provide a
   pressure modifier so old clients continue to work.
4. Normalises stack counts, enforcing integer minimums and raising
   `ValueError` for unknown modifiers or invalid combinations.
5. Computes reward bonuses:
   - Foe-focused modifiers grant +1% experience and rare drop rate per stack via
     the `foe_modifier_bonus` field.
   - `character_stat_down` applies the tiered stat penalty (0.001× per stack up
     to 500 stacks, then 0.0001×) and returns the matching 0.1% + 0.12% per
     extra stack bonus in `player_modifier_bonus`. RDR stops growing once the
     penalty reaches 95% while experience continues to trickle using the
     reduced overflow rate. `player_penalty_cap_stacks`,
     `player_penalty_excess_stacks`, and `player_overflow_multiplier` capture
     the flattened reward state so telemetry can track overflow behaviour.
6. Builds a snapshot with modifier details, pressure math, and aggregate
   rewards that is stored with the run.

`RunConfigurationSelection.snapshot` is serialised directly into the
`runs.party` JSON under the `config` key and returned to the frontend as
`configuration` from `start_run`. The helper also builds a
`RunModifierContext` derived from the snapshot so downstream systems can read
foe stat multipliers (including overflow multipliers), encounter slot bonuses,
shop/tax multipliers, and player stat penalties without re-validating the
metadata payload. The context is
persisted alongside the map state and stamped onto generated nodes via a
metadata hash for analytics.

`RunModifierContext` now exposes `player_penalty_excess_stacks` and
`foe_overflow_multiplier` so map/battle generators can factor overflow pressure
into foe tuning. `derived_metrics()` mirrors these values along with the
existing foe strength aggregates, ensuring telemetry captures when players push
beyond the RDR cap.

The `apply_player_modifier_context` helper keeps player stats aligned with the
stored configuration. `start_run` uses it immediately after validation so the
new party reflects any character penalties before the first map is generated,
and `runs.party_manager.load_party` invokes the same helper when rehydrating a
run. This prevents stat penalties from disappearing on reloads and ensures
telemetry derived from reloaded parties matches the preview calculations in the
setup wizard.

Run type definitions may also include `room_overrides` metadata. The
`get_room_overrides` helper normalises these directives so `MapGenerator` can
consistently disable or duplicate optional rooms (e.g., Boss Rush removes shops
and rests while future experiments may introduce extra shops or restorative
rooms). Downstream systems should consult these overrides instead of relying on
ad-hoc party flags when deciding which room types to present.

## Reward Application

`services/run_service.start_run` integrates the validation result:

- Party members receive their `exp_multiplier` boost before the initial map is
  generated.
- The stored party snapshot records per-member experience multipliers alongside
  the RDR baseline, ensuring reloads persist the configuration bonuses.
- The new run state embeds the configuration snapshot so future services can
  read modifier details without revalidating.
- Boss Rush runs flag the party to disable shops/rests and the map generator
  now produces an all-boss floor layout (start room plus nine boss encounters)
  while Standard runs retain the mixed encounters defined in `MapGenerator`.
- Telemetry (`log_run_start`, `log_menu_action`) captures the run type,
  modifier stacks, and computed reward bonuses.

## Analytics Storage

Migration `003_run_configuration_metadata.sql` introduces the
`run_configurations` table in the tracking database. `log_run_start` writes a
row containing the run type, modifier JSON, reward bonuses, and metadata
version whenever configuration data is provided. This allows downstream tools
to analyse configuration popularity and reward trends.

