# Task: Build Luna's Glitched Passive Variant

## Background
With the normal `LunaLunarReservoir` passive being cleaned up, we need a dedicated glitched-tier module inside `backend/plugins/passives/glitched/`. The glitched tag is applied dynamically by `foe_factory.build_encounter`, so every foe template—including Luna Midori—must have a safe modifier that layers on top of the base passive. The old shortcut of doubling charge and sword output inside the normal file breaks the tier separation model and prevents other characters from gaining consistent glitched behaviours.

## Problem
- `backend/plugins/passives/glitched/` does not define a Luna-specific class, so glitched Luna encounters either misload or fall back to the normal passive with no distinctive flavour.
- Tier-only perks (extra sword charge, per-hit healing, higher action cadence) still live in the normal passive, making it impossible to tune or disable them when other tags (boss/prime) stack.
- Without a proper plugin, documentation and balance discussions cannot reference an actual glitched behaviour file.

## Dependencies / Order
- **Blocked by** `.codex/tasks/passives/normal/d7d772d6-luna-passive-normalization.md`. Only start this once the normal passive no longer contains tier logic.
- **Complete before** the boss-tier task so the boss variant can compose/stack against the finalized glitched behaviour.
- **Task Master note:** only change this blocking guidance during a review when the dependency state truly shifts; leave other sections untouched.

## Requested Changes
1. Create `backend/plugins/passives/glitched/luna_lunar_reservoir.py` (or equivalent naming) that:
   - Imports the normal `LunaLunarReservoir` and wraps/extends it to introduce glitched behaviour (e.g., the previous 2× charge gains, sword charge surges, unstable action cadence, or new glitch-specific penalties/bonuses that fit the lore).
   - Sets `plugin_type = "passive"` and unique metadata such as `id = "luna_lunar_reservoir_glitched"` and an appropriate `name`.
   - Registers triggers consistent with the normal version while adding any new glitch-only hooks (e.g., reacting to `hit_landed` with extra charge).
2. Move the glitched-only mechanics that were stripped from the normal passive into this file. Reuse shared helpers via a common mixin module if needed.
3. Ensure the class safely handles any foe that might inherit Luna's passive via tags (e.g., summoned echoes) by checking for missing sword helpers before mutating state.
4. Update `.codex/implementation/player-foe-reference.md` (or the relevant Luna entry) to describe the glitched variant so coders and designers know what to expect.
5. Add targeted coverage or a simulation in `backend/tests/` showing that forcing a Luna encounter to `rank = "glitched"` results in the new passive being loaded and delivering the intended effects.

## Acceptance Criteria
- A concrete Luna glitched passive file exists under `backend/plugins/passives/glitched/` with fully defined metadata and behaviour.
- Normal Luna no longer exhibits glitched-specific charge multipliers; those effects only appear when the glitch tag is present.
- Automated coverage (or a scripted repro) demonstrates a glitched Luna encounter receiving the new passive and producing the documented behaviour.
- Documentation references the new glitched passive ID and thematic description.
