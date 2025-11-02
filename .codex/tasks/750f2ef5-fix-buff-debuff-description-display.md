# Fix Buff/Debuff Description Display in Battle Screen

## Objective

Fix the bug where buffs and debuffs are not displaying their `about` strings (neither the old `about` field nor the new `full_about`/`summarized_about` fields) in the battle screen tooltips and UI elements.

## Background

There is a reported bug where buff and debuff effects are not showing their description text in the battle screen. The StatusIcons component and related UI elements should display helpful tooltips with effect descriptions, but currently they are either missing or not properly utilizing the description fields from the backend.

## Task Details

### Investigation Phase

1. **Verify the bug exists:**
   - Start a battle and observe buff/debuff tooltips
   - Check if descriptions are missing or just not displaying correctly
   - Test with various effects to see if the issue is consistent

2. **Identify the data flow:**
   - Trace how effect data is passed from backend to frontend
   - Check what fields are included in the effect objects sent via API
   - Verify the backend is sending description/about fields for effects

### Backend Investigation

**Files to check:**
- `backend/autofighter/effects.py` - StatModifier and effect classes
- `backend/autofighter/stat_effect.py` - StatEffect class (if exists)
- Backend routes that serialize effects for the frontend
- Any serialization/conversion code for battle state

**Questions to answer:**
1. Do StatModifier and effect classes have `about`, `full_about`, or `summarized_about` fields?
2. Are these fields being serialized and sent to the frontend?
3. If not, should they be added or exposed?

### Frontend Investigation  

**Files to check:**
- `frontend/src/lib/battle/StatusIcons.svelte` - Main component for displaying effects
- `frontend/src/lib/systems/assetLoader.js` - Helper functions for effect data
- Any other components that display buff/debuff information

**Key areas in StatusIcons.svelte:**
- Line 33-46: `formatEffectTooltip()` function that tries to use `effect.description`
- Line 76: Tooltip display for effects in bar layout
- Line 125: Tooltip display for effects in overlay layout

**Current behavior:**
The code already attempts to use `effect.description` as a fallback, but this field may not be present in the effect data from the backend.

### Potential Solutions

1. **Add description fields to backend effect classes:**
   - Add `about`, `full_about`, and/or `summarized_about` fields to StatModifier, StatEffect, and DamageOverTime classes
   - Ensure these fields are populated with meaningful descriptions
   - Update serialization to include these fields in API responses

2. **Update frontend to better handle missing descriptions:**
   - Improve the fallback logic in `formatEffectTooltip()` to generate more useful descriptions
   - Consider using effect name and modifiers to create a readable description
   - Ensure the tooltip always shows something useful even when description is missing

3. **Coordinate with the about field migration:**
   - Ensure the solution aligns with the new `full_about`/`summarized_about` pattern
   - Consider how the "Concise Descriptions" setting should affect buff/debuff tooltips

## Implementation Guidelines

- Test thoroughly with various types of buffs and debuffs
- Ensure tooltips are readable and informative
- Follow the same description pattern used for cards and relics
- Consider performance impact if adding fields to frequently created objects
- Update any relevant type definitions or interfaces

## Acceptance Criteria

- [ ] Buffs and debuffs display meaningful descriptions in battle screen tooltips
- [ ] Descriptions are sourced from backend data when available
- [ ] Fallback descriptions are generated intelligently when backend data is missing
- [ ] All types of effects (stat buffs, DoTs, HoTs, special effects) show appropriate descriptions
- [ ] Tooltips work in both overlay and bar layouts
- [ ] Changes are tested across multiple battle scenarios
- [ ] Code follows existing style and conventions
- [ ] Solution is compatible with the ongoing `about` field migration

## Testing Scenarios

Test the following to verify the fix:
1. Basic stat buffs (ATK, DEF, SPD increases)
2. Debuffs (stat decreases)
3. DoT effects (damage over time)
4. HoT effects (healing over time)
5. Special effects (crit boost, mitigation, etc.)
6. Stacking effects
7. Multiple buffs/debuffs on the same character

## Related Issues

- Related to the broader documentation improvement work in `.codex/tasks/cards/` and `.codex/tasks/relics/`
- Should coordinate with task `00dc6da8-conscience-description-webui-setting.md` for the concise description setting

## Notes

- The term "conscience description" in the original request likely means "concise description"
- This bug may have existed before the `full_about`/`summarized_about` migration, so it may need to work with whatever fields are currently available
- Consider whether the fix should be a quick patch for existing functionality or a more comprehensive implementation that anticipates the new field structure

---

## Audit Report (2025-11-02)

### Audit Summary
✅ **TASK IS DOABLE** - The task is well-structured, technically feasible, and ready for implementation with minor clarifications.

### Verification Results

#### File References: ✅ VERIFIED
All mentioned files exist and are correctly referenced:
- `backend/autofighter/effects.py` - Contains StatModifier, DamageOverTime, HealingOverTime
- `backend/autofighter/stat_effect.py` - Contains StatEffect class
- `frontend/src/lib/battle/StatusIcons.svelte` - Contains tooltip rendering logic
- `frontend/src/lib/systems/assetLoader.js` - Contains effect image helpers

**Minor Issue**: Line numbers in StatusIcons.svelte are slightly off:
- Task says formatEffectTooltip() is at lines 33-46
- Actual location is lines 29-52
- Impact: Negligible - content matches perfectly

#### Bug Verification: ✅ CONFIRMED
The described bug is real and accurately documented:

1. **DoT/HoT Issue**: In `backend/autofighter/rooms/utils.py` (lines 204-232), DoTs and HoTs are serialized with `{id, name, damage/healing, turns, source, element, stacks}` but **NO description field**.

2. **StatModifier Issue**: In `backend/autofighter/rooms/utils.py` (lines 239-249), active_effects get descriptions via `_get_effect_description()` (lines 47-59), but this function only handles:
   - "aftertaste" → returns Aftertaste.get_description()
   - "critical_boost" → returns CriticalBoost.get_description()  
   - Everything else → returns "Unknown effect"

3. **Frontend Fallback**: StatusIcons.svelte (lines 29-52) has basic fallback logic that builds descriptions from modifiers, but it's limited and doesn't handle all cases well.

#### Technical Feasibility: ✅ ALL SOLUTIONS ARE VIABLE

**Solution 1** (Add backend description fields):
- Requires adding `about`/`full_about`/`summarized_about` fields to effect dataclasses
- Need to find all effect creation points (create_stat_buff(), create_dot() helpers)
- Update serialization in rooms/utils.py
- Impact: Medium complexity, permanent fix

**Solution 2** (Improve frontend fallbacks):
- Enhance formatEffectTooltip() logic
- Generate better descriptions from names and modifiers
- Impact: Low complexity, quick win

**Solution 3** (Coordinate with about field migration):
- Align with full_about/summarized_about pattern from cards/relics
- Consider "Concise Descriptions" UI setting
- Impact: Medium complexity, future-proof

#### Acceptance Criteria: ✅ WELL-DEFINED (1 minor issue)
All 8 criteria are clear and testable except:
- Criterion 8: "compatible with the ongoing about field migration" is vague
- Recommendation: Clarify what "compatible" means (same field names? same formatting?)

#### Testing Scenarios: ✅ COMPREHENSIVE
All 7 test scenarios are specific and cover:
- Stat buffs/debuffs, DoTs, HoTs, special effects, stacking, multiple effects
- Well aligned with acceptance criteria

### Identified Issues & Concerns

#### Minor Issues:
1. **Typo**: Task references "conscience description" (should be "concise description") - already noted in task
2. **Line number drift**: StatusIcons.svelte line numbers are slightly off
3. **Scope separation**: Task doesn't explicitly separate DoT/HoT vs StatModifier as distinct issues

#### Questions for Implementer:
1. **Plugin Discovery**: Need to audit plugin directory to find all places where effects are created
2. **Backwards Compatibility**: What happens to saved games or in-flight battles when we add new fields?
3. **Implementation Order**: Should this be done before or after task 00dc6da8 (concise description setting)?
4. **Damage Type Awareness**: Should DoT/HoT descriptions be element-specific (e.g., "Burning" vs "Freezing")?
5. **Visual Verification**: User mentioned posting photos - need to verify bug visually in running application

#### Not Blockers:
- These questions can be answered during implementation
- The core task is still clearly doable

### Recommendations for Implementation

#### Recommended Approach:
1. **Phase 1 (Quick Win)**: Implement Solution 2 first
   - Enhance frontend fallback logic in formatEffectTooltip()
   - Generate better descriptions from effect names and modifiers
   - This provides immediate improvement with minimal risk

2. **Phase 2 (Proper Fix)**: Implement Solution 1
   - Add description fields to effect classes
   - Update create_stat_buff() and create_dot() helpers to accept descriptions
   - Update rooms/utils.py serialization
   - Audit plugins directory for all effect creation points

3. **Phase 3 (Future-Proof)**: Coordinate Solution 3
   - Align field names with cards/relics pattern
   - Add support for full_about/summarized_about
   - Integrate with "Concise Descriptions" UI setting when available

#### Code Changes Required:
- **Backend**: 
  - `backend/autofighter/effects.py` - Add description fields to dataclasses
  - `backend/autofighter/rooms/utils.py` - Update serialization (lines 204-249)
  - Effect creation helpers and plugins

- **Frontend**:
  - `frontend/src/lib/battle/StatusIcons.svelte` - Enhance formatEffectTooltip() and formatTooltip()

#### Testing Strategy:
- Start battle and observe tooltips for all effect types
- Test both overlay and bar layouts
- Verify with multiple simultaneous effects
- Check stacking behavior

### Audit Conclusion

**Status**: ✅ READY FOR IMPLEMENTATION

**Confidence Level**: High - Task is well-researched and technically sound

**Risk Level**: Low-Medium
- Low risk for Solution 2 (frontend only)
- Medium risk for Solution 1 (backend changes affect data model)

**Estimated Complexity**: Medium
- Frontend changes: ~2-4 hours
- Backend changes: ~4-8 hours
- Testing: ~2-3 hours
- Total: ~8-15 hours of work

**Blocking Issues**: None

**Dependencies**: 
- Optional coordination with task 00dc6da8 (concise description setting)
- May benefit from awaiting user's visual evidence photos

**Auditor Notes**: This is a legitimate bug that affects user experience. The task is well-prepared with accurate technical details, clear acceptance criteria, and feasible solutions. The implementer should have no trouble completing this task successfully.

---

_Audit completed by Auditor on 2025-11-02. Task verified as ready for coder assignment._
