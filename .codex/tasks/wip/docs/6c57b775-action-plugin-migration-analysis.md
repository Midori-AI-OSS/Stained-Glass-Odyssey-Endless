# Action Plugin Migration Analysis

## Task ID
`6c57b775-action-plugin-migration-analysis`

## Priority
High - Strategic planning task

## Status
WIP

## Description
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

### Character System
- `backend/plugins/characters/*.py` - All character plugin files
- Look for character-specific ability implementations
- Identify ultimate action patterns

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
- Ultimate actions
- Character special abilities
- **Summon creation actions** (e.g., Luna's sword summoning, Becca's menagerie)
- Multi-target attack variants
- Skill-based healing actions
- Buff/debuff application skills

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
- [ ] All battle system files reviewed for hardcoded actions
- [ ] All character files reviewed for special abilities
- [ ] Card system reviewed for action patterns
- [ ] Migration roadmap document created in `.codex/implementation/`
- [ ] Each identified action has priority and complexity rating
- [ ] Recommendations include specific file references
- [ ] Document follows existing implementation doc format

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
