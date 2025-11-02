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

## Audit Report

**Full audit report**: [.codex/audit/3a125d68-buff-debuff-display-bug.audit.md](../.codex/audit/3a125d68-buff-debuff-display-bug.audit.md)

### Executive Summary (Revised 2025-11-02)

**Status**: ✅ ROOT CAUSE IDENTIFIED

**Critical Finding**: The bug is NOT missing descriptions - it's a **frontend prop mapping error** in `BattleView.svelte`.

**Root Cause**: Lines 2433, 2636, and 2703 incorrectly pass `member.passives` to the `active_effects` prop of StatusIcons, instead of passing `member.active_effects`. This explains why:
- Only passive abilities show up in the buff bar
- Buffs/debuffs from relics and cards don't appear at all  
- Passives show "Unknown Effect" (wrong data structure for effect rendering)

**The Fix**: Change 3 lines in `frontend/src/lib/components/BattleView.svelte`:
```diff
- active_effects={(member.passives || []).slice(0, 6)}
+ active_effects={(member.active_effects || []).slice(0, 6)}
```

**Corrected Complexity**: 1-2 hours (was 8-15 hours in original audit)
- Frontend fix: 15 minutes
- Testing: 30-60 minutes  
- Optional description improvements: 30-60 minutes

**Risk Level**: Low (simple prop name change, high impact)

**Original Audit Errors**: Initial audit incorrectly identified the issue as backend serialization/missing description fields. User feedback and screenshot analysis revealed the true scope.

See full audit report for complete analysis, testing checklist, and lessons learned.

---

_Audit completed by Auditor on 2025-11-02. Revised based on user feedback. Ready for coder assignment._
