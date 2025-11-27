# Task: Complete Complex Glitched Passive Implementations

**ID:** 36f41aac  
**Status:** WIP  
**Priority:** Medium  
**Created:** 2025-11-24  
**Related PR:** copilot/perform-task (Implement glitched-tier passive plugins)

## Background

During the implementation of glitched-tier passive plugins (task b15b27b9), 21 out of 23 passives were successfully implemented with proper doubled mechanics. However, two highly complex passives remain as simple wrapper classes without the actual doubled logic:

1. **lady_storm_supercell_glitched** - 255-line multi-phase wind/lightning system
2. **persona_light_and_dark_duality_glitched** - 365-line dual-stance system

These passives are significantly more complex than the others, with dozens of stat modifiers across multiple methods and phase transitions. They require careful analysis to identify all multipliers that need doubling while maintaining the complex state machine logic.

## Problem

Without proper doubled implementations, these glitched passives will simply inherit the normal behavior, defeating the purpose of the glitched encounter modifier. Players facing glitched lady_storm_supercell or persona_light_and_dark_duality foes will not experience the intended difficulty spike.

## Current State

Both files exist as minimal wrapper classes:
- `backend/plugins/passives/glitched/lady_storm_supercell.py` (~26 lines)
- `backend/plugins/passives/glitched/persona_light_and_dark_duality.py` (~28 lines)

Each contains only:
- Basic plugin metadata (id, name, trigger, etc.)
- A docstring describing intended behavior
- A `get_description()` method with "[GLITCHED]" prefix
- No method overrides with doubled logic

## Requested Changes

### For lady_storm_supercell_glitched:
Review `backend/plugins/passives/normal/lady_storm_supercell.py` (255 lines) and identify all numeric multipliers in:
- Wind phase bonuses (SPD, dodge, aggro reduction)
- Lightning phase bonuses (ATK, crit rate, crit damage, effect hit rate)
- Charge accumulation mechanics
- Phase transition thresholds
- Storm intensity scaling

Override the necessary methods to double these values while preserving the complex phase-switching logic.

### For persona_light_and_dark_duality_glitched:
Review `backend/plugins/passives/normal/persona_light_and_dark_duality.py` (365 lines) and identify all numeric multipliers in:
- Light stance bonuses (healing, shields, support effects)
- Dark stance bonuses (damage, DoTs, debuffs)
- Stance-switching mechanics
- Balance/imbalance penalties
- Duality synergy effects

Override the necessary methods to double these values while maintaining the dual-stance state machine.

## Implementation Guidelines

1. **Analyze before implementing**: Read through each normal passive carefully to map out all numeric multipliers
2. **Override selectively**: Only override methods that contain multipliers that need doubling
3. **Preserve state logic**: Don't modify the phase/stance switching logic, only the numeric bonuses
4. **Add inline comments**: Mark each doubled value with `# Was X, now Y` comments
5. **Update descriptions**: Ensure `get_description()` accurately reflects all doubled mechanics
6. **Test thoroughly**: Verify the passives work with FoeFactory glitched spawns

## Acceptance Criteria

- [ ] `lady_storm_supercell_glitched` overrides all methods with numeric multipliers
- [ ] All wind and lightning phase bonuses are properly doubled
- [ ] `persona_light_and_dark_duality_glitched` overrides all methods with numeric multipliers
- [ ] All light and dark stance bonuses are properly doubled
- [ ] Both passives maintain their complex state machine logic
- [ ] Inline comments document what was doubled
- [ ] Plugin registry successfully loads both glitched variants
- [ ] Smoke tests confirm both can be instantiated and applied
- [ ] No breaking changes to normal passive behavior

## Notes

- These are the most complex passives in the codebase - expect 100+ lines of implementation each
- Consider breaking down the work into phases (e.g., wind phase first, then lightning)
- Reference the successfully implemented glitched passives for patterns
- The complexity is why these were deferred during the initial implementation

## References

- Original task: `.codex/tasks/review/passives/glitched/b15b27b9-glitched-passives-implementation.md`
- Normal implementations:
  - `backend/plugins/passives/normal/lady_storm_supercell.py`
  - `backend/plugins/passives/normal/persona_light_and_dark_duality.py`
- Glitched stubs to complete:
  - `backend/plugins/passives/glitched/lady_storm_supercell.py`
  - `backend/plugins/passives/glitched/persona_light_and_dark_duality.py`
