# AOE Batched Pacing Implementation Guide

**Created:** 2025-12-03  
**Related Task:** `.codex/tasks/wip/docs/df55b9e9-aoe-simultaneous-hit-pacing.md`  
**Status:** Implementation Guide (Code changes not yet applied)

## Overview

This document provides a comprehensive analysis and implementation plan for converting sequential AOE (Area of Effect) pacing to batched pacing. Currently, AOE attacks pause after each individual target hit, creating a "machine gun" effect. The goal is to apply all damage first, then pause once for the entire AOE attack.

## Current Pacing System Analysis

### Core Pacing Functions (`backend/autofighter/rooms/battle/pacing.py`)

1. **`pace_sleep(multiplier=1.0)`** (line 140-165)
   - Base sleep function that scales by `TURN_PACING` (default 0.5s)
   - Used throughout the codebase for timing control
   - Handles cooperative fallbacks for robustness

2. **`pace_per_target(actor, duration=None)`** (line 203-217)
   - Sleeps for one per-target interval
   - Returns the multiplier used
   - This is the function called after EACH target in AOE attacks

3. **`animation_per_target_duration(actor)`** (line 167-178)
   - Resolves the per-target pacing duration
   - Defaults to `TURN_PACING` (0.5s)
   - Can be customized per actor

### Current AOE Implementation Patterns

#### Pattern 1: Wind Spread (Sequential Loop)
Location: `backend/autofighter/rooms/battle/turn_loop/player_turn.py`

```python
# Current implementation (simplified)
for mgr, extra_target in additional_targets:
    # Apply damage
    damage = await extra_target.apply_damage(...)
    # Pause AFTER EACH hit
    await pace_per_target(actor)
```

**Problem:** 5 targets = 5 pauses = 2.5 seconds total

#### Pattern 2: Ultimate Actions (Sequential Loop)
Location: `backend/plugins/actions/ultimate/*.py`

```python
# Current implementation (simplified)
for _ in range(total_chunks):
    target = select_target(enemies)
    damage = await target.apply_damage(...)
    # Pause AFTER EACH hit
    await pace_per_target(actor)
```

**Problem:** Same sequential pacing issue

## Proposed Solution: Batched Pacing

### New Pacing Function

Add to `backend/autofighter/rooms/battle/pacing.py`:

```python
async def pace_aoe_batch(
    actor: Stats | None,
    hit_count: int,
    *,
    base_multiplier: float = 1.0
) -> None:
    """Consolidated pause for a batch of AOE hits.
    
    Instead of pausing after each hit, this provides a single
    pause that represents the entire AOE attack landing.
    
    Args:
        actor: The attacking entity
        hit_count: Number of targets hit
        base_multiplier: Base multiplier for the pause duration
    
    Notes:
        - For small AOEs (1-3 targets), uses base_multiplier directly
        - For medium AOEs (4-7 targets), adds 10% extra time
        - For large AOEs (8+ targets), adds 20% extra time
        - Maximum total wait capped at 2.0 * TURN_PACING
    """
    if hit_count <= 0:
        return
    
    # Small scaling factor for visual feedback on large AOEs
    if hit_count <= 3:
        scale = 1.0
    elif hit_count <= 7:
        scale = 1.1
    else:
        scale = 1.2
    
    # Cap total wait time
    multiplier = min(base_multiplier * scale, 2.0)
    await pace_sleep(multiplier)
```

### Implementation Pattern: Batch-Then-Pause

```python
# New pattern for AOE attacks
async def execute_aoe_attack(actor, targets):
    # Phase 1: Collect all hits without pausing
    hits = []
    for target in targets:
        if getattr(target, "hp", 0) <= 0:
            continue
        damage = await target.apply_damage(
            damage_value,
            attacker=actor,
            trigger_on_hit=False,  # Defer hit events
        )
        hits.append((target, damage))
    
    # Phase 2: Single consolidated pause
    await pace_aoe_batch(actor, len(hits))
    
    # Phase 3: Post-hit processing and events
    for target, damage in hits:
        # Emit hit events for passive triggers
        await BUS.emit_async(
            "hit_landed",
            actor,
            target,
            damage,
            metadata={...}
        )
        
        # Apply DOTs, effects, etc.
        # ...
```

## Files Requiring Modification

### 1. Core Pacing Module
**File:** `backend/autofighter/rooms/battle/pacing.py`

**Changes:**
- Add `pace_aoe_batch()` function (see above)
- Update module docstring to document batched pacing

### 2. Wind Spread Implementation
**File:** `backend/autofighter/rooms/battle/turn_loop/player_turn.py`

**Function:** `_handle_wind_spread()`

**Current Structure:**
```python
async def _handle_wind_spread(context, member, target_index, ...):
    # ... setup code ...
    for mgr, extra_target in additional_targets:
        # damage application
        await pace_per_target(member)  # ← Remove this
```

**New Structure:**
```python
async def _handle_wind_spread(context, member, target_index, ...):
    # ... setup code ...
    
    # Batch all hits
    hits = []
    for mgr, extra_target in additional_targets:
        if getattr(extra_target, "hp", 0) <= 0:
            continue
        prepare_additional_hit_metadata(member)
        damage = await extra_target.apply_damage(
            damage_value,
            attacker=member,
            action_name="Wind Spread",
            trigger_on_hit=False,
        )
        hits.append((mgr, extra_target, damage))
    
    # Single pause
    if hits:
        await pace_aoe_batch(member, len(hits))
    
    # Post-hit processing
    total_spread = 0
    for mgr, extra_target, damage in hits:
        total_spread += damage
        await BUS.emit_async("hit_landed", member, extra_target, damage, ...)
        if mgr:
            await mgr.maybe_inflict_dot(member, damage)
    
    return total_spread
```

### 3. Wind Ultimate
**File:** `backend/plugins/actions/ultimate/wind_ultimate.py`

**Class:** `WindUltimate`

**Method:** `execute()`

**Changes:**
```python
async def execute(self, actor, targets, context):
    # ... setup code ...
    
    # Batch hits
    hits = []
    for _ in range(total_chunks):
        try:
            _, target = select_aggro_target(enemies)
        except ValueError:
            break
        if getattr(target, "hp", 0) <= 0:
            continue
        
        damage_value = max(1, int(per + extra))
        dealt = await target.apply_damage(
            damage_value,
            attacker=actor,
            action_name=self.name,
            trigger_on_hit=False,
        )
        hits.append((target, dealt))
    
    # Single pause
    await pace_aoe_batch(actor, len(hits))
    
    # Post-hit events
    for target, dealt in hits:
        await BUS.emit_async("hit_landed", actor, target, dealt, ...)
        # DOT application
        # ...
```

### 4. Other Ultimate Actions

Apply the same pattern to:
- **Fire Ultimate** (`backend/plugins/actions/ultimate/fire_ultimate.py`)
- **Ice Ultimate** (`backend/plugins/actions/ultimate/ice_ultimate.py`)  
- **Lightning Ultimate** (`backend/plugins/actions/ultimate/lightning_ultimate.py`)
- **Light Ultimate** (`backend/plugins/actions/ultimate/light_ultimate.py`)
- **Dark Ultimate** (`backend/plugins/actions/ultimate/dark_ultimate.py`)

## Critical Considerations

### 1. Event Ordering
**Issue:** Some passives may depend on hit events occurring in a specific order.

**Solution:**
- Emit `hit_landed` events in the same order as damage application
- Use `trigger_on_hit=False` during damage application to defer passive triggers
- Manually emit events in Phase 3

### 2. DOT Application
**Issue:** DOTs (Damage Over Time effects) are typically applied immediately after hit.

**Solution:**
- Collect DOT applications during Phase 1
- Apply them in Phase 3 after the pause
- Maintain the same order as current implementation

### 3. Death During AOE
**Issue:** If a target dies mid-AOE, what happens to remaining hits?

**Current Behavior:** Continue hitting other targets  
**New Behavior:** Same - check HP before each damage application

### 4. Passive Triggers
**Issue:** Passives that trigger on_hit_landed may expect immediate timing.

**Solution:**
- Review all on_hit_landed passives
- Ensure they work correctly with batched events
- Test with passives that:
  - Grant shields on hit
  - Counter-attack on being hit
  - Heal on damage dealt
  - Stack charges per hit

### 5. Animation System
**Issue:** Frontend animations may expect sequential hit timing.

**Solution:**
- Update `BattleEventFloaters.svelte` to handle batched hits
- Add `is_batched_aoe` metadata to hit events
- Frontend should display all hits simultaneously

## Testing Strategy

### Unit Tests

Create `backend/tests/test_aoe_batched_pacing.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from autofighter.rooms.battle.pacing import pace_aoe_batch

@pytest.mark.asyncio
async def test_pace_aoe_batch_small():
    """Small AOE (1-3 targets) uses base multiplier."""
    actor = MagicMock()
    # Mock timing and verify single pause
    # ...

@pytest.mark.asyncio
async def test_pace_aoe_batch_medium():
    """Medium AOE (4-7 targets) adds 10% time."""
    actor = MagicMock()
    # Verify 1.1x multiplier
    # ...

@pytest.mark.asyncio
async def test_pace_aoe_batch_large():
    """Large AOE (8+ targets) adds 20% time."""
    actor = MagicMock()
    # Verify 1.2x multiplier capped at 2.0
    # ...
```

### Integration Tests

Test with actual battles:

```python
@pytest.mark.asyncio
async def test_wind_spread_batched_timing():
    """Wind spread hits all targets with single pause."""
    # Setup battle with 5 enemies
    # Trigger wind attack
    # Measure total time
    # Assert time < 1.0 second (vs 2.5s before)
```

### Manual Verification

1. Start battle with Luna (Wind type)
2. Trigger Wind ultimate against 5+ enemies
3. Observe:
   - All damage numbers appear simultaneously
   - Single pause after all hits
   - Total turn time is noticeably shorter
4. Check battle log to verify all hits recorded

## Performance Impact

### Before Batched Pacing
- 5-target AOE: 5 × 0.5s = 2.5 seconds
- 10-target AOE: 10 × 0.5s = 5.0 seconds

### After Batched Pacing
- 5-target AOE: 1 × 0.55s = 0.55 seconds (**78% faster**)
- 10-target AOE: 1 × 0.6s = 0.6 seconds (**88% faster**)

## Rollout Plan

### Phase 1: Core Implementation
1. Add `pace_aoe_batch()` to pacing.py
2. Add unit tests for the new function
3. Verify tests pass

### Phase 2: Wind Abilities
1. Update `_handle_wind_spread()`
2. Update `WindUltimate.execute()`
3. Test with Wind-type characters

### Phase 3: Other Ultimates
1. Update Fire, Ice, Lightning ultimates
2. Test each element type
3. Verify damage totals match

### Phase 4: Frontend Updates
1. Update BattleEventFloaters to handle batched hits
2. Add visual effects for simultaneous hits
3. Test animation timing

### Phase 5: Validation
1. Run full test suite
2. Manual playtesting
3. Monitor for regressions

## Known Risks

### High Risk
1. **Passive timing dependencies** - Some passives may break if hit events are batched
2. **Animation desync** - Frontend may not handle simultaneous hits well

### Medium Risk  
1. **DOT application order** - DOTs applied in different order may cause unexpected behavior
2. **Counter-attack mechanics** - May not trigger correctly with batched hits

### Low Risk
1. **Performance** - Batching should improve performance, unlikely to cause issues
2. **Battle log** - May need formatting updates for batched hits

## Rollback Strategy

If issues arise:
1. Revert `pace_aoe_batch()` changes
2. Restore `pace_per_target()` calls
3. Add feature flag: `ENABLE_BATCHED_AOE_PACING = False`
4. Allow gradual migration per ability

## Future Enhancements

1. **Parallel Damage Application**
   - Use `asyncio.gather()` for true parallel hits
   - May improve performance further

2. **Smart Scaling**
   - Scale pause time based on actual damage dealt
   - Bigger hits = slightly longer pause for visual feedback

3. **Per-Ability Configuration**
   - Allow some abilities to opt-out of batching
   - Support hybrid timing models

## References

- Task file: `.codex/tasks/wip/docs/df55b9e9-aoe-simultaneous-hit-pacing.md`
- Pacing module: `backend/autofighter/rooms/battle/pacing.py`
- Wind spread: `backend/autofighter/rooms/battle/turn_loop/player_turn.py`
- Ultimate actions: `backend/plugins/actions/ultimate/*.py`

## Conclusion

This implementation will significantly improve turn pacing for AOE attacks, reducing total battle time and creating a more satisfying "impact" feeling when AOE abilities land. The batched pacing approach maintains all existing functionality while dramatically improving perceived responsiveness.

**Estimated Implementation Time:** 8-12 hours  
**Estimated Testing Time:** 4-6 hours  
**Risk Level:** Medium (requires careful passive/animation testing)

---
**Document Status:** Ready for implementation by next developer  
**Last Updated:** 2025-12-03
