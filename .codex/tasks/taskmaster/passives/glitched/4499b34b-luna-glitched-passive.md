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

---

## Audit Report (2025-11-16)

**Auditor:** GitHub Copilot Agent  
**Status:** ⚠️ CONDITIONALLY APPROVED - Depends on character file fix

### Implementation Review

✅ **Passive File (`backend/plugins/passives/glitched/luna_lunar_reservoir.py`)**
- File exists with correct structure (47 lines)
- Properly inherits from `LunaLunarReservoir` base class (line 11)
- Correct plugin metadata:
  - `id = "luna_lunar_reservoir_glitched"` (line 19)
  - `name = "Glitched Lunar Reservoir"` (line 20)
- `_charge_multiplier()` returns 2 (line 28) - ✅ 2x multiplier as specified
- `_sword_charge_amount()` returns 8 (line 35) - ✅ Doubled from base 4
- Module docstring describes glitched behavior (lines 11-17)
- `get_description()` properly describes doubled mechanics (lines 38-45)

✅ **Test Coverage**
- `test_tier_passives.py::test_resolve_passives_for_rank_glitched` - PASSED
- `test_tier_passives.py::test_apply_rank_passives_glitched` - PASSED
- `test_tier_passive_stacking.py::test_luna_glitched_charge_multiplier` - PASSED
- Passive correctly registered in PassiveRegistry

❌ **Integration Test Failure**
- `test_luna_swords.py::test_glitched_luna_sword_hits_double_charge` - **FAILED**
  - Expected: 8 charge gain (2x multiplier, 4 base)
  - Actual: 4 charge gain (only base multiplier applied)
  - **Root Cause:** `luna.py::_LunaSwordCoordinator._handle_hit()` calls `_get_luna_passive()` which always returns the **normal** base class, not the glitched variant
  - The character file bypasses the passive resolution system that would select the correct tier variant

✅ **Documentation**
- Referenced in `.codex/implementation/player-foe-reference.md`
- Task file properly updated with background and requirements

### Code Quality Notes

**Good Practices:**
- Clean inheritance pattern - extends base without duplicating logic
- Override only the methods that need tier-specific behavior
- Maintains compatibility with sword registration and event handling
- Properly typed with TYPE_CHECKING guards

**Design Concerns:**
- The glitched passive implementation is correct, but it cannot function properly until `luna.py` is refactored to use the passive resolution system instead of hard-coding the base passive class

### Recommendation

**APPROVE with dependency on character file fix:**

The glitched passive implementation is architecturally sound and correctly implements the 2x multiplier. The integration test failure is NOT due to a problem with this passive—it's due to the character file (`luna.py`) bypassing the tier resolution system.

**Dependency Chain:**
1. Normal passive task (d7d772d6) - APPROVED conditionally
2. **This task (4499b34b)** - APPROVED conditionally (depends on luna.py fix)
3. Character file refactor (NEW TASK) - REQUIRED for functional integration
4. Prime passive task (91661353) - Can be approved after same fix
5. Boss passive task (2cd60c9a) - Can be approved after same fix

**Specific Finding for Follow-up:**
When the character file is fixed, verify that:
- Glitched Luna (rank="glitched") gains 8 charge per sword hit
- Glitched Boss Luna (rank="glitched boss") gains 8 charge per sword hit  
- Normal Luna (rank="normal") gains 4 charge per sword hit

**Task Disposition:** Move to taskmaster with annotation that character file fix must complete before this passive is functional in-game.
