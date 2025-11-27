# Optimize Relic Stack Loop Performance

## Task ID
`62d6b944-relic-stack-loop-performance`

## Priority
High

## Status
WIP

## Description
Turns can last a while due to looping over each stack of a relic. When a relic has multiple stacks, the current implementation iterates through each stack individually, causing noticeable delays during battle turns. This needs to be optimized to batch process relic stacks.

## Context
Currently in `backend/autofighter/relics.py`, the `apply_relics()` function iterates over all relic IDs in `party.relics`. When a relic has multiple stacks (e.g., collecting the same relic multiple times), the loop processes each occurrence individually. Additionally, in `backend/plugins/relics/_base.py`, the `apply()` method has a nested loop:
1. Outer loop over party members
2. Inner calculation using `party.relics.count(self.id)` to determine stacks

This means the relic count is recalculated for every member, and effects are applied redundantly.

## Current Implementation

### File: `backend/autofighter/relics.py` (lines 54-59)
```python
async def apply_relics(party: Party) -> None:
    registry = _registry()
    for rid in party.relics:
        relic_cls = registry.get(rid)
        if relic_cls:
            await relic_cls().apply(party)
```

### File: `backend/plugins/relics/_base.py` (lines 46-79)
```python
async def apply(self, party: Party) -> None:
    # ...
    stacks = party.relics.count(self.id)
    for member in party.members:
        # Apply stack multiplier: each additional copy multiplies the effect
        changes = {f"{attr}_mult": (1 + pct) ** stacks for attr, pct in self.effects.items()}
        # ...
```

## Problem Analysis
1. **Redundant instantiation**: Each relic instance is created fresh (`relic_cls()`) for every stack
2. **Repeated counting**: `party.relics.count(self.id)` is called per-member
3. **Duplicate applications**: If a relic appears 3 times in the party, `apply()` is called 3 times, but each call correctly handles stacks - meaning effects are applied 3 times
4. **Unnecessary event emissions**: BUS events are emitted for each stack × each member

## Objectives
1. Deduplicate relic processing to call `apply()` only once per unique relic ID
2. Pre-calculate stack counts before iterating
3. Cache relic instances to avoid repeated instantiation
4. Batch event emissions where possible

## Implementation Steps

### Step 1: Modify `apply_relics()` in `backend/autofighter/relics.py`
```python
async def apply_relics(party: Party) -> None:
    """Apply relic effects to party, processing each unique relic once."""
    registry = _registry()
    
    # Pre-calculate stacks for each unique relic
    unique_relics = set(party.relics)
    relic_stacks = {rid: party.relics.count(rid) for rid in unique_relics}
    
    for rid in unique_relics:
        relic_cls = registry.get(rid)
        if relic_cls:
            relic = relic_cls()
            await relic.apply(party, stacks=relic_stacks[rid])
```

### Step 2: Update `apply()` signature in `backend/plugins/relics/_base.py`
```python
async def apply(self, party: Party, *, stacks: int | None = None) -> None:
    """Apply relic effects to party members.
    
    Args:
        party: The party to apply effects to
        stacks: Pre-calculated stack count (if None, will be calculated)
    """
    self._reset_subscriptions(party)
    log.info("Applying relic %s to party", self.id)
    mods = []
    if stacks is None:
        stacks = party.relics.count(self.id)
    # ... rest of implementation
```

### Step 3: Consider Batching Effect Applications
For relics that emit events, consider batching the emissions:
```python
# Instead of emitting per-member:
events = []
for member in party.members:
    # ... calculate changes
    events.append((self.id, member, effect_type, value, metadata))

# Batch emit after all calculations
for event_args in events:
    await BUS.emit_async("relic_effect", *event_args)
```

## Files to Modify
- `backend/autofighter/relics.py` - Update `apply_relics()` to deduplicate
- `backend/plugins/relics/_base.py` - Update `apply()` signature to accept pre-calculated stacks

## Acceptance Criteria
- [ ] Each unique relic ID is processed only once, not once per stack
- [ ] Stack counts are pre-calculated before the apply loop
- [ ] Relic instances are created once per unique relic, not per stack
- [ ] All existing relic tests pass
- [ ] Battle turn timing improves noticeably when party has multiple stacks
- [ ] Linting passes (`uv tool run ruff check backend --fix`)
- [ ] No change to relic effect values (same cumulative effect as before)

## Testing Requirements

### Manual Verification
1. Create a party with 3+ stacks of the same relic
2. Time battle turns before and after the fix
3. Verify relic effects are correctly applied with same cumulative values

### Unit Tests
- Test that unique relics are processed once
- Test that stack calculations are correct
- Test that effect values match expected values for multiple stacks

## Notes for Coder
- The fix should be backward compatible - existing relic subclasses should work without modification
- Focus on correctness first, then optimize
- Consider adding timing logs to verify improvement
- Be careful with relics that have side effects in `apply()` - they should only run once
