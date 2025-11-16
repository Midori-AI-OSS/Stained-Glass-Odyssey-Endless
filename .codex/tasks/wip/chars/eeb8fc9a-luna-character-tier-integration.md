# Task: Fix Luna Character Tier Passive Integration

## Background
The Luna tier passive implementation (normal, glitched, prime, boss) is complete and correct. However, `backend/plugins/characters/luna.py` bypasses the tier resolution system by directly calling methods on the base passive class. This prevents tier variants from functioning correctly and causes test failures.

The passive system includes an event-based architecture where each tier variant subscribes to `luna_sword_hit` events via their `_on_sword_hit()` class method. The character file should emit these events and let the passive variants handle charge calculation and tier-specific effects (like prime healing), but instead it duplicates this logic by calling passive methods directly.

## Problem
**File:** `backend/plugins/characters/luna.py`  
**Class:** `_LunaSwordCoordinator`  
**Method:** `_handle_hit()` (lines 110-160)

**Issues:**
1. Line 138: `passive = _get_luna_passive()` always returns the normal `LunaLunarReservoir` class, not tier variants
2. Line 139: `per_hit = passive._sword_charge_amount(owner)` calculates charge using only the base class (bypasses glitched/prime multipliers)
3. Line 141: `passive.add_charge(owner, amount=per_hit)` applies charge manually instead of letting the passive's event handler do it
4. Line 142: `healed = await passive._apply_prime_healing(owner, amount or 0)` calls a method that **doesn't exist** on the base class, causing AttributeError for all prime variants

**Test Failures:**
- `test_luna_swords.py::test_glitched_luna_sword_hits_double_charge` - Expected 8 charge, got 4 (glitched multiplier not applied)
- `test_luna_swords.py::test_prime_luna_sword_hits_gain_stacks_and_heal[prime boss-...]` - AttributeError: '_apply_prime_healing' not found
- `test_luna_swords.py::test_prime_luna_sword_hits_gain_stacks_and_heal[glitched prime boss-...]` - AttributeError
- `test_luna_swords.py::test_prime_luna_sword_hits_gain_stacks_and_heal[glitched prime champion-...]` - AttributeError

## Dependencies / Order
- **Blocked by:** None - the passive implementations are complete
- **Blocks:** Full functional testing of Luna tier variants in-game
- **Priority:** HIGH - This is the only remaining issue preventing tier passives from working

## Requested Changes

### 1. Refactor `_LunaSwordCoordinator._handle_hit()`
Remove all direct passive method calls and rely on the event system:

**Remove these lines:**
```python
passive = _get_luna_passive()
per_hit = passive._sword_charge_amount(owner)  # Line 139
_register_luna_sword(owner, attacker, label or "")  # Line 140 (keep registration)
passive.add_charge(owner, amount=per_hit)  # Line 141 - REMOVE
healed = await passive._apply_prime_healing(owner, amount or 0)  # Line 142 - REMOVE
metadata["prime_heal_handled"] = True  # Line 143 - REMOVE (passive handles this)
metadata["prime_heal_success"] = healed  # Line 144 - REMOVE
```

**⚠️ CRITICAL: Also remove this line:**
```python
metadata["charge_handled"] = True  # Line 151 - REMOVE (prevents passive from adding charge!)
```

**Keep these:**
```python
_register_luna_sword(owner, attacker, label or "")  # Sword tracking still needed
await BUS.emit_async(
    self.EVENT_NAME,  # "luna_sword_hit"
    owner,
    attacker,
    target,
    amount or 0,
    action_type or "attack",
    metadata,
)
```

**The Correct Pattern:**
The passive's `_on_sword_hit()` already:
- Calls `_sword_charge_amount()` with the correct tier-specific multiplier
- Calls `add_charge()` with the calculated amount (unless `metadata["charge_handled"]` is True)
- In prime variants, applies healing via `_apply_prime_healing()`
- Updates metadata flags internally to prevent duplicate processing

**Why `charge_handled` Must Be Removed:**
The passive checks `metadata.get("charge_handled")` and **skips adding charge if True** (line 103 in normal passive). If the character file sets this flag without actually adding charge, the passive won't add it either, resulting in zero charge being awarded. This flag was meant for the OLD pattern where the character file added charge manually. In the NEW pattern, the passive adds charge, so this flag must not be set by the character file.

By removing ALL manual charge/healing logic AND their metadata flags, the event system will route to the correct tier variant automatically.

### 2. Verify `_get_luna_passive()` Usage
Check all other usages of `_get_luna_passive()` in the file:
- Line 51: `_register_luna_sword()` - This is fine, it's just for sword tracking
- Line 171: `_handle_removal()` - This is fine, unregistration doesn't need tier logic
- Line 180: Sword cleanup - This is fine

**Only `_handle_hit()` needs changes.**

### 3. Update Tests (if needed)
After refactoring, verify all Luna sword tests pass:
```bash
pytest tests/test_luna_swords.py -v
pytest tests/test_tier_passive_stacking.py -v
```

### 4. Documentation
Update any relevant comments in `luna.py` that reference the old direct-call pattern. The docstring for `_handle_hit()` should explain that it emits events for passives to handle, not that it directly applies effects.

## Acceptance Criteria
- [ ] `_handle_hit()` no longer calls `passive._sword_charge_amount()`, `passive.add_charge()`, or `passive._apply_prime_healing()`
- [ ] `_handle_hit()` no longer sets `metadata["charge_handled"]` or `metadata["prime_heal_handled"]` (these flags prevent passive event handlers from processing the hit)
- [ ] All logic for charge calculation and healing is handled by tier-specific passive event handlers
- [ ] All 9 tests in `test_luna_swords.py` pass, including:
  - `test_glitched_luna_sword_hits_double_charge` (expects 8 charge from 2x multiplier)
  - All 3 prime healing variants (no AttributeError)
- [ ] All 36 tests in tier passive test suites continue to pass
- [ ] Sword registration and cleanup still work correctly
- [ ] No new test failures introduced

## Technical Notes

**⚠️ CRITICAL: Metadata Flag Behavior**

The passive's `_on_sword_hit()` checks `metadata.get("charge_handled")` and **skips adding charge if True**:

```python
# In LunaLunarReservoir._on_sword_hit() line 103:
handled = bool(metadata_dict.get("charge_handled"))
# ...
if not handled:  # Line 112
    cls.add_charge(actual_owner, per_hit)
```

**This means:**
- If character file sets `metadata["charge_handled"] = True` → passive skips charge → 0 charge awarded ❌
- If character file doesn't set flag → passive adds charge → correct tier-specific amount awarded ✅

The `charge_handled` flag was designed for the OLD pattern where the character file added charge manually and wanted to prevent the passive from double-adding it. In the NEW pattern, only the passive adds charge, so the character file must NOT set this flag.

**Event Flow (Correct Pattern):**
1. Luna's sword hits an enemy
2. `_LunaSwordCoordinator._handle_hit()` receives the hit event
3. Coordinator registers the sword (if needed) and enriches metadata
4. Coordinator emits `luna_sword_hit` event via BUS (WITHOUT setting charge_handled)
5. **Passive's `_on_sword_hit()` handler receives event**
6. Tier-specific passive calculates charge and applies effects
7. Passive updates owner's actions per turn

**Current Broken Flow:**
1. Luna's sword hits an enemy
2. `_LunaSwordCoordinator._handle_hit()` receives the hit event
3. Coordinator calculates charge using **base class only** (wrong tier)
4. Coordinator tries to call `_apply_prime_healing()` on base class ❌ AttributeError
5. Coordinator sets `metadata["charge_handled"] = True` to prevent double-processing
6. Coordinator emits event, but passive sees flag and ignores it (charge already "handled")

**Why the Current Code Exists:**
This appears to be legacy code from before the tier system was fully implemented. The character file was written to work with a single passive variant and never updated when the tier system was introduced.

## Related Tasks
- `.codex/tasks/taskmaster/passives/normal/d7d772d6-luna-passive-normalization.md` - Approved with this follow-up noted
- `.codex/tasks/taskmaster/passives/glitched/4499b34b-luna-glitched-passive.md` - Approved conditionally on this fix
- `.codex/tasks/taskmaster/passives/prime/91661353-luna-prime-passive.md` - Approved conditionally on this fix
- `.codex/tasks/taskmaster/passives/boss/2cd60c9a-luna-boss-passive.md` - Approved (boss works but other tiers don't)
