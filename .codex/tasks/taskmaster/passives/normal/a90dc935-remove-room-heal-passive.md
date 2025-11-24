# Remove room_heal Passive from All Tiers

## Task ID
`a90dc935-remove-room-heal-passive`

## Priority
High

## Status
AUDITED - Ready for Task Master Sign-Off

## Audit Notes (2024-11-24)
**Auditor Review:** Comprehensive audit completed. All acceptance criteria met.

✅ **Code Changes Verified:**
- All 4 room_heal.py files deleted (normal, boss, prime, glitched tiers)
- 0 references to room_heal found in backend code
- Tests passing (test_passives.py: 3 passed)

✅ **Testing Verified:**
- No import errors or undefined references
- All passive-related tests pass
- No test failures related to room_heal removal

✅ **Documentation Verified:**
- No references to room_heal in .codex/implementation/
- No references in character or foe definitions

✅ **Quality Checks:**
- Existing linting issues (E402 in test files) are unrelated to this task
- Git changes show only expected deletions

**Recommendation:** APPROVE - Task completed successfully. Ready for Task Master final sign-off.

## Description
Remove the `room_heal` passive from all tier folders (normal, boss, prime, glitched). This passive currently heals 1 HP after each battle. The passive is being removed as part of a gameplay balance/redesign decision.

## Context
The `room_heal` passive exists in 4 tier variants:
- `backend/plugins/passives/normal/room_heal.py`
- `backend/plugins/passives/boss/room_heal.py`
- `backend/plugins/passives/prime/room_heal.py`
- `backend/plugins/passives/glitched/room_heal.py`

Each tier variant extends the normal version with slight modifications (typically just different IDs). The passive triggers on `battle_end` and heals the character for a small amount.

## Rationale for Removal
(To be filled in based on project direction - possibilities include):
- Too simple/passive gameplay mechanic
- Healing should be more strategic/active
- Replacing with different healing mechanics
- Balance concerns

## Current Implementation

### Normal Tier (`backend/plugins/passives/normal/room_heal.py`)
```python
@dataclass
class RoomHeal:
    plugin_type = "passive"
    id = "room_heal"
    name = "Room Heal"
    trigger = "battle_end"
    amount = 1
    stack_display = "pips"
```

### Other Tiers
Boss, Prime, and Glitched tiers each have similar classes that extend or reference the normal version with modified IDs (`room_heal_boss`, `room_heal_prime`, `room_heal_glitched`).

## Files to Delete
```
backend/plugins/passives/normal/room_heal.py
backend/plugins/passives/boss/room_heal.py
backend/plugins/passives/prime/room_heal.py
backend/plugins/passives/glitched/room_heal.py
```

## Files to Update

### Test Files
The following test files reference `room_heal`:

1. **`backend/tests/test_passives.py`**:
   - `test_room_heal_trigger()` - Delete entire test function
   - `test_room_heal_event_and_enrage()` - Delete entire test function

2. **`backend/tests/test_passive_demos.py`** (check for any room_heal references):
   - Search for "room_heal" and remove/update as needed

3. **`backend/tests/test_advanced_passive_behaviors.py`** (check for references):
   - Search for "room_heal" and remove/update as needed

4. **`backend/tests/test_effect_serialization.py`** (check for references):
   - Search for "room_heal" and remove/update as needed

### Character/Foe Definitions
Search for any character or foe definitions that include "room_heal" in their passive list:
```bash
grep -r "room_heal" backend/plugins/characters/
grep -r "room_heal" backend/autofighter/rooms/foes/
```

For any found:
- Remove "room_heal" from the passives list
- Consider adding a different passive or leaving empty if appropriate

### Documentation
Update if room_heal is mentioned:
- `.codex/implementation/tier-passive-system.md`
- `.codex/implementation/player-foe-reference.md`

## Implementation Steps

### Step 1: Verify Current Usage
```bash
# Find all references to room_heal in the codebase
grep -r "room_heal" backend/ --include="*.py"
```

### Step 2: Delete Passive Files
```bash
rm backend/plugins/passives/normal/room_heal.py
rm backend/plugins/passives/boss/room_heal.py
rm backend/plugins/passives/prime/room_heal.py
rm backend/plugins/passives/glitched/room_heal.py
```

### Step 3: Update Tests
1. Open `backend/tests/test_passives.py`
2. Delete `test_room_heal_trigger()` function (around line 23)
3. Delete `test_room_heal_event_and_enrage()` function (around line 26)
4. Search for any other "room_heal" references and remove

### Step 4: Update Character/Foe Definitions
For each character or foe with room_heal in their passives:
1. Open the file
2. Remove "room_heal" from the passives list
3. Optionally replace with a different passive

### Step 5: Update Documentation
1. Check `.codex/implementation/tier-passive-system.md`
   - Remove room_heal from examples/lists
2. Check `.codex/implementation/player-foe-reference.md`
   - Remove room_heal from character/foe descriptions

### Step 6: Run Tests
```bash
cd backend
uv run pytest tests/ -v
```

Ensure:
- No import errors for room_heal
- All remaining tests pass
- No references to room_heal remain

### Step 7: Run Linting
```bash
uv tool run ruff check backend --fix
```

## Acceptance Criteria
- [ ] All 4 room_heal.py files deleted (normal, boss, prime, glitched)
- [ ] Test functions for room_heal deleted from test_passives.py
- [ ] All other test files updated (no room_heal references)
- [ ] Character/foe definitions updated (no room_heal in passive lists)
- [ ] Documentation updated (no room_heal references)
- [ ] All tests pass after removal
- [ ] No import errors or undefined references
- [ ] Linting passes
- [ ] Git shows only expected file deletions and updates

## Testing Requirements

### Verification Tests
After deletion:
```bash
# Should return nothing
grep -r "room_heal" backend/plugins/
grep -r "room_heal" backend/tests/
grep -r "room_heal" backend/autofighter/
```

### Regression Tests
- Run full test suite to ensure no broken imports
- Test battle end event still works correctly
- Test that passives system still functions with room_heal removed

## Dependencies
None - this is a straightforward deletion task

## References
- `backend/plugins/passives/normal/room_heal.py` - Main implementation
- `backend/tests/test_passives.py` - Test cases to remove
- `.codex/implementation/tier-passive-system.md` - Passive system documentation

## Notes for Coder
- This is a deletion task - make sure to find all references
- Be thorough in searching for "room_heal" across the codebase
- If you find characters/foes heavily relying on room_heal, consider consulting with the task master about replacements
- After deletion, commit with message: `[FEAT] Remove room_heal passive from all tiers`
- Some characters might have room_heal as their only passive - that's okay, they can have an empty passive list
- Make sure to check both `room_heal` and variations like `room_heal_boss`, `room_heal_prime`, `room_heal_glitched`
