# Optimize AOE Pacing for Simultaneous Hits

## Task ID
`df55b9e9-aoe-simultaneous-hit-pacing`

## Priority
High

## Status
WIP

## Related Tasks
**IMPORTANT**: This task may overlap with the Action Plugin System tasks. Review:
- `.codex/tasks/wip/GOAL-action-plugin-system.md` - Main action system goal
- `.codex/tasks/wip/chars/fac8f16b-migrate-character-special-abilities.md` - Ability migration
- The action plugin system is designed to handle ALL actions - including AOE attacks

Consider whether this task should be:
1. Part of the action plugin migration (attacks become action plugins with batched pacing)
2. A separate pacing layer that works with action plugins
3. Deferred until action plugins are fully implemented

## Description
Turns can last a while due to pacing in AOE attacks. Currently, AOE abilities (like Wind's multi-target spread) apply damage to each target sequentially with a pause between each hit. This creates a "machine gun" effect where hits land one-by-one. Instead, AOE attacks should send a pulse that hits all foes at the same time, then pause once before moving to the next action.

## Context
The issue is particularly noticeable with:
- Wind damage type's normal attack spread (`_handle_wind_spread`)
- Wind ultimate (`WindUltimate`)
- Fire ultimate (AOE with burn)
- Other multi-target abilities

Currently, the code in `backend/autofighter/rooms/battle/turn_loop/player_turn.py` and ultimate action plugins applies damage in a loop with `pace_per_target(actor)` or `pace_sleep()` after EACH hit. This means hitting 5 targets results in 5 pauses.

## Current Implementation

### Wind Spread (`player_turn.py`)
```python
# In _handle_wind_spread:
for mgr, extra_target in additional_targets:
    # ... apply damage
    await pace_per_target(actor)  # Pause after each target
```

### Wind Ultimate (`plugins/actions/ultimate/wind_ultimate.py`)
```python
for _ in range(total_chunks):
    # ... select target
    dealt = await target.apply_damage(...)
    await pace_per_target(actor)  # Pause after each hit
```

## Problem Analysis
1. **Sequential pacing**: Each target hit triggers a separate pause
2. **Visual disconnect**: Players expect AOE to hit all targets "at once"
3. **Longer turns**: 5 targets × 0.5s pacing = 2.5s per AOE instead of ~0.5s
4. **Inconsistent UX**: Single-target attacks take similar time to multi-target

## Objectives
1. Batch all AOE hits to occur without individual pauses
2. Apply a single consolidated pause after all hits in an AOE
3. Preserve per-hit damage logging and events
4. Maintain animation system compatibility

## Implementation Strategy

### Option A: Batch Hit Pattern (Recommended)
Apply all damage first, then pause once:
```python
# Collect all hits without pausing
hits = []
for target in targets:
    damage = await target.apply_damage(...)
    hits.append((target, damage))

# Single pause for the entire AOE
await pace_aoe_batch(actor, len(hits))

# Emit hit events after all damage applied
for target, damage in hits:
    await BUS.emit_async("hit_landed", actor, target, damage, ...)
```

### Option B: Parallel Hit Pattern (Advanced)
Use asyncio.gather for truly simultaneous damage:
```python
async def apply_batch_damage(targets, attacker, damage_value):
    tasks = [t.apply_damage(damage_value, attacker=attacker) for t in targets]
    results = await asyncio.gather(*tasks)
    return results

# Single pause after all hits
await pace_sleep()
```

## Implementation Steps

### Step 1: Add AOE Batch Pacing Helper
Create new function in `backend/autofighter/rooms/battle/pacing.py`:
```python
async def pace_aoe_batch(actor: Any, hit_count: int) -> None:
    """Consolidated pause for a batch of AOE hits.
    
    Instead of pausing after each hit, this provides a single
    pause that represents the entire AOE attack landing.
    
    Args:
        actor: The attacking entity
        hit_count: Number of targets hit (for potential scaling)
    """
    # Single pause regardless of hit count
    await pace_sleep()
    # Optional: slight extra time for very large AOEs
    if hit_count > 10:
        await asyncio.sleep(YIELD_DELAY * 2)
```

### Step 2: Update Wind Spread
Modify `_handle_wind_spread` in `player_turn.py`:
```python
async def _handle_wind_spread(context, member, target_index, ...):
    hits = []
    
    # Apply all damage without pausing
    for mgr, extra_target in additional_targets:
        if getattr(extra_target, "hp", 0) <= 0:
            continue
        prepare_additional_hit_metadata(member)
        damage = await extra_target.apply_damage(...)
        hits.append((extra_target, damage, mgr))
    
    # Single consolidated pause
    if hits:
        await pace_aoe_batch(member, len(hits))
    
    # Post-hit processing (DOTs, events)
    for extra_target, damage, mgr in hits:
        await BUS.emit_async("hit_landed", member, extra_target, damage, ...)
        if mgr:
            await mgr.maybe_inflict_dot(member, damage)
    
    return sum(d for _, d, _ in hits)
```

### Step 3: Update Wind Ultimate
Modify `WindUltimate.execute()` in `plugins/actions/ultimate/wind_ultimate.py`:
```python
async def execute(self, actor, targets, context):
    # ... setup code ...
    
    hits = []
    
    # Batch all hits without individual pauses
    for _ in range(total_chunks):
        try:
            _, target = select_aggro_target(enemies)
        except ValueError:
            break
        if getattr(target, "hp", 0) <= 0:
            continue
        
        damage_value = max(1, int(per + extra))
        dealt = await target.apply_damage(damage_value, ...)
        hits.append((target, dealt))
    
    # Single pause for the entire ultimate
    await pace_aoe_batch(actor, len(hits))
    
    # Post-hit event emissions
    for target, dealt in hits:
        await BUS.emit_async("hit_landed", actor, target, dealt, ...)
        # Handle DOT application
        # ...
```

### Step 4: Update Other AOE Abilities
Apply the same pattern to:
- Fire Ultimate (`fire_ultimate.py`)
- Ice Ultimate (`ice_ultimate.py`)
- Lightning Ultimate (`lightning_ultimate.py`)
- Any other multi-target abilities

### Step 5: Consider Animation Timing
Update animation timing calculations to account for batch hits:
```python
def compute_aoe_animation_time(hit_count: int) -> float:
    """Calculate animation time for a batched AOE attack."""
    # Base time for the attack animation
    base = TURN_PACING * 0.5
    # Small scaling for visual feedback on large AOEs
    scale = min(1.0 + (hit_count - 1) * 0.05, 2.0)
    return base * scale
```

## Files to Modify
- `backend/autofighter/rooms/battle/pacing.py` - Add `pace_aoe_batch()`
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py` - Update `_handle_wind_spread()`
- `backend/plugins/actions/ultimate/wind_ultimate.py` - Batch hits
- `backend/plugins/actions/ultimate/fire_ultimate.py` - Batch hits
- `backend/plugins/actions/ultimate/ice_ultimate.py` - Batch hits
- `backend/plugins/actions/ultimate/lightning_ultimate.py` - Batch hits

## Acceptance Criteria
- [ ] AOE attacks hit all targets before any pause occurs
- [ ] A single consolidated pause follows multi-target attacks
- [ ] Per-target damage is still correctly calculated and logged
- [ ] Hit events (`hit_landed`) still emit for each target
- [ ] DOT application still works correctly per-target
- [ ] Turn duration is noticeably shorter for multi-target attacks
- [ ] Wind spread, Wind ultimate, and other AOEs use batched pacing
- [ ] All existing tests pass
- [ ] Linting passes (`uv tool run ruff check backend --fix`)

## Testing Requirements

### Manual Verification
1. Trigger Wind ultimate against 5+ enemies
2. Verify all hits appear to land simultaneously
3. Verify single pause after all hits
4. Time the turn and compare to before (should be ~80% shorter)

### Unit Tests
- Test `pace_aoe_batch` function behavior
- Test batched damage application
- Test event emission order

### Integration Tests
- Test Wind spread with 3+ targets
- Test ultimate abilities with multiple targets
- Verify damage totals match expected values

## Notes for Coder
- The key insight is separating damage application from pacing
- Events should still emit per-target for proper passive/effect triggers
- Be careful with order-dependent effects (some passives may rely on hit order)
- Consider adding a feature flag to toggle between old/new behavior for testing
- Animation callbacks may need updates to reflect the new timing model
