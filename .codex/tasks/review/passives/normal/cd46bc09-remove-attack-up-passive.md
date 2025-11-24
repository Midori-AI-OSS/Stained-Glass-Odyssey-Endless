# Remove attack_up Passive from All Tiers

## Task ID
`cd46bc09-remove-attack-up-passive`

## Priority
High

## Status
WIP

## Description
Remove the `attack_up` passive from all tier folders (normal, boss, prime, glitched). This passive currently grants +5 attack at battle start. The passive is being removed as part of a gameplay balance/redesign decision.

## Context
The `attack_up` passive exists in 4 tier variants:
- `backend/plugins/passives/normal/attack_up.py`
- `backend/plugins/passives/boss/attack_up.py`
- `backend/plugins/passives/prime/attack_up.py`
- `backend/plugins/passives/glitched/attack_up.py`

Each tier variant extends the normal version with slight modifications (typically just different IDs). The passive triggers on `battle_start` and adds a StatEffect to boost the attack stat.

## Rationale for Removal
(To be filled in based on project direction - possibilities include):
- Too simple/straightforward stat boost
- Makes early game too easy
- Replacing with more interesting combat mechanics
- Balance concerns - stat inflation

## Current Implementation

### Normal Tier (`backend/plugins/passives/normal/attack_up.py`)
```python
@dataclass
class AttackUp:
    plugin_type = "passive"
    id = "attack_up"
    name = "Attack Up"
    trigger = "battle_start"
    amount = 5
    stack_display = "pips"
    
    async def apply(self, target, **kwargs):
        stack_index = kwargs.get('stack_index', 0)
        effect = StatEffect(
            name=f"{self.id}_atk_up_{stack_index}",
            stat_modifiers={"atk": self.amount},
            source=self.id,
        )
        target.add_effect(effect)
```

### Other Tiers
Boss, Prime, and Glitched tiers each have similar classes that extend or reference the normal version with modified IDs (`attack_up_boss`, `attack_up_prime`, `attack_up_glitched`).

## Files to Delete
```
backend/plugins/passives/normal/attack_up.py
backend/plugins/passives/boss/attack_up.py
backend/plugins/passives/prime/attack_up.py
backend/plugins/passives/glitched/attack_up.py
```

## Files to Update

### Test Files
The following test files reference `attack_up`:

1. **`backend/tests/test_passives.py`**:
   - Line ~20: `assert "attack_up" in passives` - Update or remove assertion
   - Line ~22: `player.passives = ["attack_up"] * 5` - Use different passive or update test

2. **`backend/tests/test_passive_demos.py`**:
   - Multiple references to "attack_up" in passive lists
   - Lines where `multi_char.passives = ["attack_up", ...]` - Remove "attack_up" from list
   - Comments mentioning attack_up - Update or remove

3. **`backend/tests/test_advanced_passive_behaviors.py`**:
   - `simple_member.passives = ["attack_up"]` - Use different passive

4. **`backend/tests/test_effect_serialization.py`**:
   - `target.passives = ["attack_up", "luna_lunar_reservoir", ...]` - Remove "attack_up"
   - Assertions checking for attack_up effects - Remove or update

### Character/Foe Definitions
Search for any character or foe definitions that include "attack_up" in their passive list:
```bash
grep -r "attack_up" backend/plugins/characters/
grep -r "attack_up" backend/autofighter/rooms/foes/
```

For any found:
- Remove "attack_up" from the passives list
- Consider adding a different passive or leaving empty if appropriate

### Documentation
Update if attack_up is mentioned:
- `.codex/implementation/tier-passive-system.md`
- `.codex/implementation/player-foe-reference.md`
- `.codex/implementation/stats-and-effects.md`

## Implementation Steps

### Step 1: Verify Current Usage
```bash
# Find all references to attack_up in the codebase
grep -r "attack_up" backend/ --include="*.py"
```

### Step 2: Delete Passive Files
```bash
rm backend/plugins/passives/normal/attack_up.py
rm backend/plugins/passives/boss/attack_up.py
rm backend/plugins/passives/prime/attack_up.py
rm backend/plugins/passives/glitched/attack_up.py
```

### Step 3: Update Tests

#### test_passives.py
1. Update the test that checks for "attack_up" in passives registry:
   - Either remove the assertion
   - Or change to check for a different passive
2. Update tests that use `["attack_up"] * 5`:
   - Replace with a different passive for testing stacking
   - Or create a test-specific mock passive

#### test_passive_demos.py
1. Find all instances of "attack_up" in passive lists
2. Remove "attack_up" from each list
3. Update comments referencing attack_up

#### test_advanced_passive_behaviors.py
1. Replace `simple_member.passives = ["attack_up"]` with different passive

#### test_effect_serialization.py
1. Remove "attack_up" from passive lists
2. Update assertions that check for attack_up effects

### Step 4: Update Character/Foe Definitions
For each character or foe with attack_up in their passives:
1. Open the file
2. Remove "attack_up" from the passives list
3. Optionally replace with a different passive

### Step 5: Update Documentation
1. Check `.codex/implementation/tier-passive-system.md`
   - Remove attack_up from examples/lists
2. Check `.codex/implementation/player-foe-reference.md`
   - Remove attack_up from character/foe descriptions
3. Check `.codex/implementation/stats-and-effects.md`
   - Remove attack_up from examples if present

### Step 6: Run Tests
```bash
cd backend
uv run pytest tests/ -v
```

Ensure:
- No import errors for attack_up
- All remaining tests pass
- No references to attack_up remain causing failures

### Step 7: Run Linting
```bash
uv tool run ruff check backend --fix
```

## Acceptance Criteria
- [ ] All 4 attack_up.py files deleted (normal, boss, prime, glitched)
- [ ] All test files updated (no attack_up references causing failures)
- [ ] Character/foe definitions updated (no attack_up in passive lists)
- [ ] Documentation updated (no attack_up references)
- [ ] All tests pass after removal
- [ ] No import errors or undefined references
- [ ] Linting passes
- [ ] Git shows only expected file deletions and updates

## Testing Requirements

### Verification Tests
After deletion:
```bash
# Should return nothing (or only in comments)
grep -r "attack_up" backend/plugins/
grep -r '"attack_up"' backend/tests/
grep -r "'attack_up'" backend/tests/
grep -r "attack_up" backend/autofighter/
```

### Regression Tests
- Run full test suite to ensure no broken imports
- Test battle start event still works correctly
- Test that passives system still functions with attack_up removed
- Test that StatEffect system still works (attack_up was a common example)

## Known Test Updates Needed

Based on grep results, these specific test updates are required:

1. **test_passives.py**:
   - Line 20: `assert "attack_up" in passives` - Change to different passive
   - Line 22: `player.passives = ["attack_up"] * 5` - Change to different passive

2. **test_passive_demos.py**:
   - Multiple lines: `multi_char.passives = ["attack_up", ...]` - Remove "attack_up"
   - Comments: `# attack_up` - Update

3. **test_advanced_passive_behaviors.py**:
   - `simple_member.passives = ["attack_up"]` - Change to different passive

4. **test_effect_serialization.py**:
   - `target.passives = ["attack_up", ...]` - Remove "attack_up"
   - Assertions checking `p["id"] == "attack_up"` - Remove or update

## Dependencies
None - this is a straightforward deletion task

## References
- `backend/plugins/passives/normal/attack_up.py` - Main implementation
- `backend/tests/test_passives.py` - Test cases to update
- `.codex/implementation/tier-passive-system.md` - Passive system documentation
- `backend/autofighter/stat_effect.py` - StatEffect system used by attack_up

## Notes for Coder
- This is a deletion task - make sure to find all references
- Be thorough in searching for "attack_up", "attack_up_boss", "attack_up_prime", "attack_up_glitched"
- Many tests use attack_up as a simple example passive - replace with another simple passive like:
  - Any character-specific passive
  - Any other tier 1 passive
  - Or create a test-specific mock if needed
- After deletion, commit with message: `[FEAT] Remove attack_up passive from all tiers`
- Update test assertions carefully - some check for specific passive counts or effects
- If tests break after removal, it's likely because they're checking for attack_up effects in serialization - update those assertions
