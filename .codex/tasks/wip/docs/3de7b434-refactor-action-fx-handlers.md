# Refactor On-Hit Effects System (Aftertaste Pattern)

## Task ID
`3de7b434-refactor-action-fx-handlers`

## Priority
Medium

## Status
WIP

## Description
There must be better ways to handle some actions/effects like Aftertaste. Aftertaste is an **on-hit effect** (a bonus hit that triggers after an attack) that currently works but displays incorrectly in the WebUI - it shows as its own separate attack instead of as an added hit. This task focuses on:
1. Understanding the on-hit effect pattern used by Aftertaste
2. Fixing the WebUI display for on-hit effects
3. Creating a proper framework for on-hit effects

## Context
**What Aftertaste Actually Is:**
- An on-hit bonus action that adds extra hits after an attack lands
- Uses a RANDOM damage type (weighted toward attacker's type)
- Triggered by relics (echoing_drum, echo_bell, rusty_buckle, plague_harp, pocket_manual)
- NOT Lightning-specific - can use Fire, Ice, Wind, Lightning, Light, or Dark
- Deals 10-150% of base potency (25) per hit

**Current Implementation** (`backend/plugins/effects/aftertaste.py`):
- Standalone effect class with `apply(attacker, target)` method
- Picks random damage type per hit (weighted 25% toward attacker's type)
- Creates temp attacker with random damage type
- Respects TURN_PACING between echo hits
- Emits `relic_effect` event with `effect_label: "aftertaste"`

**The Bug:**
- WebUI shows Aftertaste as its own attack entry
- Should show as an added hit/echo on the original attack
- No WebUI support for "on-hit FX" visualization yet

## Current Implementation

### Aftertaste Effect (`backend/plugins/effects/aftertaste.py`)
```python
@dataclass
class Aftertaste:
    plugin_type = "effect"
    id = "aftertaste"
    hits: int = 1
    base_pot: int = 25
    _damage_types = [Fire, Ice, Wind, Lightning, Light, Dark]  # Random selection
    
    async def apply(self, attacker: Stats, target: Stats) -> list[int]:
        for amount in self.rolls():
            random_damage_type = self._get_random_damage_type(attacker)
            # ... apply damage with random type
```

### Triggering Relics (examples)
- `echoing_drum.py` - Triggers Aftertaste on hit
- `echo_bell.py` - Triggers Aftertaste on hit
- `rusty_buckle.py` - Triggers Aftertaste on hit

## Problem Analysis
1. **WebUI Display Bug**: Aftertaste appears as separate attack instead of added hit
2. **No On-Hit FX Framework**: No standardized way to show on-hit effects in WebUI
3. **Action Log Confusion**: Aftertaste creates its own action log entry

## Objectives
1. Fix WebUI to display on-hit effects as added hits, not separate attacks
2. Create a standard pattern for on-hit effects visualization
3. Document how relics and effects can add on-hit bonuses
4. Ensure Aftertaste works correctly with the action plugin system

## Implementation Steps

### Step 1: Analyze WebUI Display Issue
Investigate how attacks are displayed:
- `frontend/src/lib/components/BattleEventFloaters.svelte`
- `frontend/src/lib/battle/ActionQueue.svelte`
- How `hit_landed` vs `action_used` events are rendered

### Step 2: Add On-Hit FX Metadata
Update Aftertaste to include metadata that marks it as an on-hit effect:
```python
await BUS.emit_async(
    "hit_landed",  # or appropriate event
    attacker,
    target,
    amount,
    {
        "effect_type": "on_hit",
        "parent_action": original_action_name,
        "effect_label": "aftertaste",
        "is_echo": True,  # Mark as echo/addon hit
    }
)
```

### Step 3: Update WebUI to Handle On-Hit Effects
Modify frontend to group on-hit effects with their parent attack:
```javascript
// When rendering action queue/battle log
if (hit.metadata?.is_echo) {
    // Display as sub-hit under parent attack
} else {
    // Display as main attack
}
```

### Step 4: Document On-Hit Effect Pattern
Create documentation for:
- How relics can trigger on-hit effects
- Event structure for on-hit effects
- WebUI display requirements

## Files to Review
- `backend/plugins/effects/aftertaste.py` - Current implementation (working)
- `backend/plugins/relics/echoing_drum.py` - Example triggering relic
- `frontend/src/lib/components/BattleEventFloaters.svelte` - Battle display
- `frontend/src/lib/battle/ActionQueue.svelte` - Action display

## Files to Modify
- `backend/plugins/effects/aftertaste.py` - Add on-hit metadata to events
- `frontend/src/lib/*` - Update to handle on-hit effect display
- `.codex/implementation/on-hit-effects.md` - New documentation

## Acceptance Criteria
- [ ] Aftertaste displays as added hit in WebUI, not separate attack
- [ ] On-hit effects have proper metadata (`is_echo`, `parent_action`)
- [ ] WebUI correctly renders on-hit effects under parent attack
- [ ] Documentation created for on-hit effect pattern
- [ ] All existing tests pass
- [ ] Linting passes (`uv tool run ruff check backend --fix`)

## Related Tasks
- This may relate to the action plugin system - on-hit effects might become action addons
- Consider how this interacts with AOE pacing task

## Notes for Coder
- Aftertaste is NOT Lightning-specific - it uses random damage types
- The backend logic works correctly - this is primarily a WebUI display issue
- Focus on the display/metadata first, refactoring can come later
- Coordinate with the user (@lunamidori5) who mentioned working on WebUI on-hit FX
