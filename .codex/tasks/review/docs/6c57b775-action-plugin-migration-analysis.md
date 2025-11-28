# Action Plugin Migration Analysis

## Task ID
`6c57b775-action-plugin-migration-analysis`

## Priority
High - Strategic planning task

## Status
**COMPLETE** - Moved to review 2025-11-28

## Completion Notes

### Work Completed
1. ✅ Reviewed all battle system files for hardcoded actions
2. ✅ Reviewed character files for special abilities
3. ✅ Reviewed damage type system for ultimate actions
4. ✅ Discovered that ALL ultimates and 5 character special abilities are already migrated
5. ✅ Updated migration roadmap document at `.codex/implementation/action-plugin-migration-roadmap.md`

### Key Findings
- **Ultimates**: All 7 damage-type ultimates are now implemented as action plugins
- **Special Abilities**: 5 character abilities migrated (Ally, Becca, Carly, Graygray, Ixia)
- **Basic Attack**: Fully migrated and integrated with turn loop
- **Remaining**: On-action behaviors (Light heal, Dark drain, Wind spread) and summon creation

### Updated Documentation
The migration roadmap was significantly out of date. Updated to reflect:
- What has been completed (Phases 1-3)
- What remains (Phase 4 - optional further work)
- Current architecture and integration points

## Original Description
Conduct a comprehensive code review of the battle system, room system, and character mechanics to identify all actions that could be migrated to the action plugin system. This analysis will inform future implementation tasks and ensure a systematic approach to extending the action plugin architecture.

## Context
The action plugin system was recently implemented with BasicAttackAction as the first plugin. The infrastructure exists (ActionBase, ActionRegistry, BattleContext, etc.) but most combat actions remain hardcoded throughout the codebase. This task is to systematically identify what should be migrated next.

## Objectives
1. Review all hardcoded action execution in the battle system
2. Review character-specific abilities embedded in character classes
3. Review card effects and their execution mechanisms
4. Identify room-based actions (if any qualify as "actions" vs "effects")
5. Categorize findings by priority and implementation difficulty
6. Create recommendations for migration order

## Files to Review

### Battle System
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py` - Player action execution
- `backend/autofighter/rooms/battle/turn_loop/foe_turn.py` - Foe action execution
- `backend/autofighter/rooms/battle/enrage.py` - Enrage mechanics
- `backend/autofighter/rooms/battle/engine.py` - Battle orchestration
- `backend/autofighter/stats.py` - Core stat/damage/healing methods

### Damage Type System (CRITICAL - Contains Ultimate Actions!)
- `backend/plugins/damage_types/_base.py` - Base damage type with `ultimate()` and `on_action()` methods
- `backend/plugins/damage_types/light.py` - Light ultimate (heal allies, cleanse DoTs, debuff enemies)
- `backend/plugins/damage_types/dark.py` - Dark ultimate (drain allies for 6x strikes) and drain action
- `backend/plugins/damage_types/wind.py` - Wind ultimate (AoE multi-hit) and AoE normal attack
- `backend/plugins/damage_types/fire.py` - Fire ultimate (AoE with burn DoT)
- `backend/plugins/damage_types/ice.py` - Ice ultimate and freeze mechanics
- `backend/plugins/damage_types/lightning.py` - Lightning ultimate and chain mechanics
- `backend/plugins/damage_types/generic.py` - Generic damage type (neutral element, no strengths/weaknesses)

**KEY INSIGHT:** Each damage type has:
- `ultimate()` method - Character ultimates are damage-type-based!
- `on_action()` method - Special behaviors during normal attacks (Wind AoE, Light healing, Dark drain)
- `on_damage()` / `on_damage_taken()` - Damage modification hooks

### Character System
- `backend/plugins/characters/*.py` - All character plugin files
- Look for character-specific ability implementations
- `prepare_for_battle()` methods (Luna's sword summoning)

### Summons System
- `backend/autofighter/summons/base.py` - Summon entity base class
- `backend/autofighter/summons/manager.py` - SummonManager.create_summon()
- Luna's `_LunaSwordCoordinator` in `backend/plugins/characters/luna.py`

### Card System
- `backend/autofighter/cards.py` - Card mechanics
- `backend/plugins/cards/*.py` - Card plugin files

### Other Systems
- `backend/autofighter/rooms/shop.py` - Shop actions (if applicable)
- `backend/autofighter/rooms/chat.py` - Chat room actions (if applicable)
- `backend/autofighter/effects.py` - Effect application mechanisms

## Analysis Categories

### 1. Combat Actions (HIGH PRIORITY)
These are active choices made during combat:
- **Ultimate actions** (Found in damage type files! Each damage type has `ultimate()` method)
  - Light ultimate: Heal allies, cleanse DoTs, debuff enemies
  - Dark ultimate: Drain allies for powered 6x strikes
  - Wind ultimate: AoE multi-hit attack
  - Fire ultimate: AoE with burn DoT application
  - Ice ultimate: 6 waves of ramping AoE damage
  - Lightning ultimate: AoE with random DoTs and Aftertaste
  - Generic ultimate: 64 rapid strikes on single target
- **Damage type special actions** (Found in `on_action()` methods)
  - Wind AoE normal attack (spreads to multiple targets via `get_turn_spread()`)
  - Light healing action (heals low HP allies during normal action)
  - Dark drain action (drains allies for damage bonus)
- **Summon creation actions** (e.g., Luna's sword summoning via `prepare_for_battle()`, Becca's menagerie)
- **Summon attacks** (Luna's swords attack, should use normal attack action)
- Multi-target attack variants
- Skill-based healing actions

### 2. Card-Based Actions (MEDIUM PRIORITY)
Actions triggered by card usage:
- Damage-dealing cards
- Healing cards
- Buff/debuff cards
- Utility cards

### 3. Automatic/Passive Effects (EVALUATE CAREFULLY)
These may NOT be good candidates for action plugins:
- DoT/HoT ticks (already have their own plugin system)
- Passive triggers (already have passive system)
- Automatic room effects
- Status effect proc effects

### 4. Buffs and Debuffs (SEPARATE SYSTEM)
**NOTE:** Buffs and debuffs should NOT be action plugins. They are the EFFECTS that actions apply.
- Currently using `StatEffect` class for stat modifications
- Should be moved to plugin system in `backend/plugins/effects/` (separate task 7782ecea)
- Examples: attack up, defense down, speed buffs, etc.
- Similar to DoT/HoT plugin structure but for stat modifiers
- This analysis should identify which actions APPLY buffs/debuffs, not treat buffs as actions
- **Passives like Ally's overload and Becca's menagerie should APPLY buffs/debuffs, not be actions**

### 5. Passive Effects that Apply Buffs (NOT ACTIONS)
**IMPORTANT:** Some passives trigger buff/debuff application but should NOT become actions:
- Ally's `ally_overload` passive - Should apply buff/debuff effects when triggered
- Becca's `becca_menagerie_bond` passive - Should apply coordinated buff effects
- These remain as passive plugins but should use the new buff/debuff plugin system

## Deliverables

Create a new document in `.codex/implementation/` called `action-plugin-migration-roadmap.md` with:

1. **Executive Summary**
   - Total actions identified
   - Recommended migration order
   - Estimated effort

2. **Detailed Findings**
   - For each identified action:
     - Current implementation location
     - Action type/category
     - Complexity estimate (simple/medium/complex)
     - Dependencies
     - Migration priority (high/medium/low)
     - Rationale for priority

3. **Migration Recommendations**
   - Phase 1: Quick wins (simple, high-impact)
   - Phase 2: Character abilities
   - Phase 3: Advanced mechanics

4. **Technical Considerations**
   - Integration challenges
   - Backward compatibility concerns
   - Testing requirements
   - Performance implications

## Acceptance Criteria
- [x] All battle system files reviewed for hardcoded actions
- [x] All character files reviewed for special abilities
- [x] Card system reviewed for action patterns
- [x] Migration roadmap document created in `.codex/implementation/`
- [x] Each identified action has priority and complexity rating
- [x] Recommendations include specific file references
- [x] Document follows existing implementation doc format

## Dependencies
- Existing action plugin system documentation (`.codex/implementation/action-plugin-system.md`)
- Understanding of ActionBase, ActionRegistry, BattleContext

## References
- `.codex/implementation/action-plugin-system.md` - Current action system docs
- `.codex/tasks/wip/GOAL-action-plugin-system.md` - Overall goal and research findings
- `backend/plugins/actions/_base.py` - Action plugin base class
- `backend/plugins/actions/registry.py` - Action registry

## Notes for Coder
- Focus on identifying **active choices** made during combat, not passive/automatic effects
- Consider implementation difficulty when prioritizing
- Look for patterns that can be standardized across multiple actions
- Some mechanics may be better suited to their existing plugin systems (passives, DoTs, etc.)
- Document the rationale for excluding certain mechanics from action plugin migration
