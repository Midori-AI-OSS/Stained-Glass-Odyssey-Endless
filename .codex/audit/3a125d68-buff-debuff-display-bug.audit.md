# Buff/Debuff Description Display Bug Audit
**Audit ID**: 3a125d68  
**Date**: 2025-11-02  
**Auditor**: AI Agent (Auditor Mode)  
**Scope**: Task `.codex/tasks/750f2ef5-fix-buff-debuff-description-display.md`, backend effect serialization, frontend StatusIcons component  
**Status**: ✅ ROOT CAUSE IDENTIFIED

## Executive Summary
The reported bug where buffs and debuffs from relics and cards are not displaying in battle has been traced to a **frontend prop mapping error** in `BattleView.svelte`. The component is incorrectly passing `member.passives` to the `active_effects` prop of StatusIcons, instead of passing `member.active_effects`. This explains why:
1. Only passive abilities show up in the buff bar
2. Buffs/debuffs from relics and cards don't appear at all
3. Passive abilities show "Unknown Effect" (because they're being rendered as effects instead of passives)

Initial audit incorrectly assumed the issue was backend serialization or missing description fields. User feedback and screenshot analysis revealed the true scope of the problem.

## Original Problem Statement
User reported that buffs and debuffs are not showing their description strings in battle screen tooltips. Task file proposed three solutions focused on adding description fields to effect classes.

## User Corrections (PR Comments)
1. **Comment on line 139**: "Or for buffs and debuffs they do not show up on the buff bar at all... (Only passives seem to show up with 'Unknown Effect'"
2. **Screenshot evidence**: Shows battle screen with character portraits, confirming passives appear but buff/debuff effects are missing
3. **Additional clarification**: "Relics and Cards that add buffs and debuffs also do not show up on the buff bar nor in the live combat review that you can click the eye icon for..."

## Root Cause Analysis

### Investigation Process
1. **Backend Serialization Verified**: 
   - `backend/autofighter/rooms/utils.py` (lines 239-249) correctly serializes `Stats._active_effects` as `active_effects` in the battle state
   - Relics like Echoing Drum correctly call `attacker.add_effect(buff_effect)` to add StatEffect objects
   - StatEffect objects ARE being added to `Stats._active_effects` and serialized properly

2. **Frontend Component Verified**:
   - `frontend/src/lib/battle/StatusIcons.svelte` correctly handles `active_effects` prop
   - Component combines `hots`, `dots`, and `active_effects` into a unified display (lines 56-67)
   - formatEffectTooltip() provides fallback description logic (lines 29-52)

3. **Integration Point - THE BUG**:
   - `frontend/src/lib/components/BattleView.svelte` uses StatusIcons component
   - **Line 2433**: `<StatusIcons ... active_effects={(foe.passives || []).slice(0, 6)} />`
   - **Line 2636**: `<StatusIcons ... active_effects={(summon.passives || []).slice(0, 6)} />`
   - **Line 2703**: `<StatusIcons ... active_effects={(member.passives || []).slice(0, 6)} />`
   
   **ALL THREE INSTANCES** pass `passives` instead of `active_effects`!

### Why This Causes the Observed Behavior

**Incorrect Prop Mapping**:
```svelte
<!-- CURRENT (WRONG) -->
<StatusIcons active_effects={(member.passives || []).slice(0, 6)} />

<!-- SHOULD BE -->
<StatusIcons active_effects={(member.active_effects || []).slice(0, 6)} />
```

**Result**:
1. `member.active_effects` (which contains buff/debuff StatEffect objects from relics/cards) is **never passed** to StatusIcons
2. `member.passives` (which contains passive ability metadata) is incorrectly passed as `active_effects`
3. StatusIcons renders passives as if they were effects
4. Passives don't have the expected effect structure, so formatEffectTooltip() returns "Unknown Effect"
5. Real buffs/debuffs never appear because they're not being passed to the component

## File References Verification

### Backend Files: ✅ ALL VERIFIED
- `backend/autofighter/effects.py` - Contains StatModifier, DamageOverTime, HealingOverTime classes
- `backend/autofighter/stat_effect.py` - Contains StatEffect dataclass
- `backend/autofighter/rooms/utils.py` - Serialization code (correct)
- `backend/plugins/relics/echoing_drum.py` - Example showing correct usage of `add_effect()`

### Frontend Files: ✅ ALL VERIFIED
- `frontend/src/lib/battle/StatusIcons.svelte` - Tooltip rendering (correct)
- `frontend/src/lib/systems/assetLoader.js` - Effect image helpers (correct)
- `frontend/src/lib/components/BattleView.svelte` - **BUG LOCATION** (lines 2433, 2636, 2703)
- `frontend/src/lib/battle/LegacyFighterPortrait.svelte` - Also uses StatusIcons but correctly passes props

**Line Number Accuracy**: Task file mentioned lines 33-46 for formatEffectTooltip(), actual is lines 29-52 (minor drift, content matches)

## Original Audit Errors

### What I Got Wrong
1. **Scope Misidentification**: Assumed the issue was backend serialization/description fields
2. **Solutions Misdirected**: Proposed adding description fields to effect classes when the real issue is frontend prop mapping
3. **Complexity Overestimation**: Estimated 8-15 hours when the fix is actually a 3-line change

### What I Got Right
1. File references were accurate
2. Technical analysis of serialization was correct
3. Description fallback logic analysis was correct
4. Testing scenarios remain valid

## Corrected Solution

### The Fix (Simple)
In `frontend/src/lib/components/BattleView.svelte`, change three lines:

**Line 2433** (Foes):
```svelte
- active_effects={(foe.passives || []).slice(0, 6)}
+ active_effects={(foe.active_effects || []).slice(0, 6)}
```

**Line 2636** (Summons):
```svelte
- active_effects={(summon.passives || []).slice(0, 6)}
+ active_effects={(summon.active_effects || []).slice(0, 6)}
```

**Line 2703** (Party Members):
```svelte
- active_effects={(member.passives || []).slice(0, 6)}
+ active_effects={(member.active_effects || []).slice(0, 6)}
```

### Secondary Issue: Description Improvements
While the main bug is the prop mapping, the original task's concern about descriptions remains valid:
- `_get_effect_description()` only handles "aftertaste" and "critical_boost"
- Other effects will rely on formatEffectTooltip() fallback logic
- This could still be improved but is NOT the primary bug

## Recommendations

### Immediate Action (Critical Fix)
1. **Fix prop mapping** in BattleView.svelte (3 lines)
2. **Test thoroughly** with relics that add buffs (e.g., Echoing Drum)
3. **Verify** effects appear in:
   - Buff bar under portraits
   - Live combat review (eye icon)
   - Both overlay and bar layouts

### Follow-up Improvements (Optional)
1. **Enhance description fallbacks** in formatEffectTooltip() to handle more effect types
2. **Add description field** to effect classes if desired for richer tooltips
3. **Coordinate with** task 00dc6da8 for concise description setting integration

### Testing Checklist
- [x] Identify root cause (frontend prop mapping)
- [ ] Fix BattleView.svelte prop mappings (coder task)
- [ ] Start battle with relic that adds buff (e.g., Echoing Drum)
- [ ] Verify buff appears in buff bar with correct icon
- [ ] Verify tooltip shows effect name and modifiers
- [ ] Check foes, summons, and party members all work
- [ ] Test with multiple simultaneous buffs
- [ ] Test with debuffs
- [ ] Test DoTs and HoTs still work correctly
- [ ] Verify passives still appear (if they should be shown separately)

## Updated Complexity Estimate

**Original Estimate**: 8-15 hours  
**Corrected Estimate**: 1-2 hours
- Frontend fix: 15 minutes
- Testing: 30-60 minutes
- Optional description improvements: 30-60 minutes

**Risk Level**: Low (simple prop name change)  
**Impact**: High (fixes major missing feature)

## Lessons Learned

### Audit Process Improvements
1. **Always verify end-to-end**: Don't assume the issue is in one layer
2. **Request visual evidence early**: Screenshot immediately revealed true scope
3. **Listen to user corrections**: User knew their system better than initial analysis
4. **Check integration points**: Bug was at component boundary, not in either component
5. **Question assumptions**: "Missing descriptions" was a red herring for "missing display"

### Communication Pattern
User provided critical feedback:
- "buffs and debuffs do not show up on the buff bar at all"
- "only passives seem to show up"
- "Relics and Cards that add buffs... do not show up"

This clearly indicated a **rendering issue**, not a **data issue**. Initial audit should have investigated component prop passing before diving into serialization.

## Conclusion

**Status**: ✅ ROOT CAUSE IDENTIFIED - Ready for implementation

**Fix Complexity**: Simple (3-line change)

**Fix Location**: `frontend/src/lib/components/BattleView.svelte` lines 2433, 2636, 2703

**Expected Outcome**: Buffs and debuffs from relics and cards will display correctly in battle screen

**Follow-up**: Task file solutions 2 and 3 (description improvements) remain valid as optional enhancements

---

_Audit revised based on user feedback and screenshot analysis. Original audit archived within this report._
