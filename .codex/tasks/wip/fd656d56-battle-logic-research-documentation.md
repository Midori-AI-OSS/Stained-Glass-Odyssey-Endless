# Task: Battle Logic Research and Documentation

**Status:** WIP  
**Priority:** High  
**Category:** Research/Documentation  
**Goal File:** `.codex/tasks/wip/GOAL-action-plugin-system.md`

## Objective

Conduct a thorough investigation of the game's battle logic system and document findings in the goal file to inform the action plugin system design and implementation.

## Background

Before we can successfully extract actions into plugins, we need a complete understanding of how the current battle system works, including all integration points, edge cases, and dependencies. This task involves deep-dive code analysis and documentation.

## Research Areas

### 1. Battle Flow Analysis

**Files to investigate:**
- `backend/autofighter/rooms/battle/engine.py`
- `backend/autofighter/rooms/battle/core.py`
- `backend/autofighter/rooms/battle/turn_loop/orchestrator.py`
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py`
- `backend/autofighter/rooms/battle/turn_loop/foe_turn.py`

**Questions to answer:**
1. What is the exact sequence of events during a turn?
2. Where are action decisions made (targeting, ability selection)?
3. What are all the hooks/callbacks available during action execution?
4. How do extra turns work and where are they triggered?
5. How does the action point system work?

**Document in:** Goal file under "Research Findings → Component: Action Execution Flow"

### 2. Damage Application Deep-Dive

**Files to investigate:**
- `backend/autofighter/stats.py` (especially `apply_damage()` method)
- `backend/plugins/damage_types/_base.py`
- `backend/plugins/damage_types/*.py` (all damage type implementations)

**Questions to answer:**
1. What are all the stages of damage calculation?
2. How do damage types modify damage?
3. What events are emitted during damage application?
4. How are dodge, crit, shields, and overkill handled?
5. What metadata is passed through damage calls?
6. How should action plugins integrate with `apply_damage()`?

**Document in:** Goal file under "Research Findings → Component: Damage Type Integration"

### 3. Multi-Target and Spread Actions

**Files to investigate:**
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py` (lines 430-483)
- `backend/plugins/damage_types/wind.py` (example of spread damage)
- `backend/plugins/damage_types/lightning.py` (example of chain damage)

**Questions to answer:**
1. How does the current spread damage system work?
2. What is the interface for defining spread behavior?
3. How are additional targets collected and processed?
4. How does animation timing work for multi-hit actions?
5. What patterns exist for AOE vs. chain vs. splash damage?

**Document in:** Goal file under "Research Findings → Component: Multi-Hit/AOE Actions"

### 4. Character Ability Survey

**Files to investigate:**
- `backend/plugins/characters/*.py` (all character files)
- Focus on: Luna, Becca, Lady Darkness, Lady Lightning, Bubbles

**Questions to answer:**
1. What special abilities do characters currently have?
2. How are these abilities triggered (events, conditions)?
3. What patterns are common across abilities?
4. What are the most complex abilities that need to be supported?
5. How do character-specific mechanics work (e.g., Luna's swords)?

**Document in:** Goal file under "Research Findings → Component: Character Special Abilities"

### 5. Passive System Analysis

**Files to investigate:**
- `backend/plugins/passives/*.py` (all passive implementations)
- `backend/autofighter/passives.py` (PassiveRegistry)
- `backend/plugins/passives/_base.py`

**Questions to answer:**
1. How do passives currently integrate with the battle system?
2. What events do passives subscribe to?
3. How are passive stacks managed?
4. Should passives become action plugins or remain separate?
5. How do tier passives (normal, prime, boss, glitched) differ?

**Document in:** Goal file under "Research Findings → Component: Passive System Integration"

### 6. Effect System Investigation

**Files to investigate:**
- `backend/autofighter/effects.py`
- `backend/plugins/dots/*.py`
- `backend/plugins/hots/*.py`
- `backend/autofighter/stat_effect.py`

**Questions to answer:**
1. How does the EffectManager work?
2. How are DoTs and HoTs applied and ticked?
3. What is the relationship between effects and actions?
4. How should action plugins interact with the effect system?
5. How are effect durations and stacks managed?

**Document in:** Goal file under "Research Findings → Component: Effect System Integration"

### 7. Event Bus Mapping

**Files to investigate:**
- `backend/plugins/event_bus.py`
- `backend/autofighter/stats.py` (BUS emissions)
- All turn loop files (search for `BUS.emit_async`)

**Questions to answer:**
1. What events are currently emitted during combat?
2. What events should action plugins emit?
3. How do event subscriptions work?
4. What is the timing/order of event emissions?
5. Are there any event naming conventions?

**Document in:** Goal file under "Research Findings → Component: Event Bus Integration"

### 8. Animation and Timing System

**Files to investigate:**
- `backend/autofighter/rooms/battle/pacing.py`
- `backend/autofighter/stats.py` (animation constants)
- Turn loop files (animation_start/animation_end emissions)

**Questions to answer:**
1. How are animation durations calculated?
2. How does the pacing system work?
3. What events control animation playback?
4. How do multi-target animations differ?
5. What metadata is needed for animations?

**Document in:** Goal file under "Research Findings → Component: Animation System"

### 9. Testing Infrastructure

**Files to investigate:**
- `backend/tests/test_*.py` (all test files)
- Focus on combat-related tests

**Questions to answer:**
1. What tests exist for the combat system?
2. How are battles mocked/simulated in tests?
3. What test patterns should be followed?
4. What new tests are needed for action plugins?
5. How can we ensure backward compatibility?

**Document in:** Goal file under "Research Findings → Component: Testing Strategy"

### 10. Edge Cases and Special Mechanics

**Files to investigate:**
- All battle system files
- Character files with unique mechanics

**Questions to answer:**
1. What are the most unusual/complex action patterns?
2. How do summons attack?
3. How do reflect/counter mechanics work?
4. How are status effects that prevent actions handled?
5. What happens with zero-damage or heal-only actions?

**Document in:** Goal file under "Research Findings → Component: Edge Cases"

## Methodology

For each research area:

1. **Read the Code**: Carefully examine the relevant files
2. **Trace Execution**: Follow the code path for typical scenarios
3. **Identify Patterns**: Note common patterns and conventions
4. **Document Findings**: Write clear, detailed notes in the goal file
5. **Flag Questions**: Note any uncertainties or areas needing clarification
6. **Create Examples**: Include code snippets showing current implementation

## Deliverables

1. **Completed Research Sections** in `GOAL-action-plugin-system.md`:
   - All 10+ research areas documented
   - Each section includes:
     - Your name and date
     - Key findings (bulleted list)
     - Code examples where relevant
     - Open questions or concerns
     - Recommendations for action plugin design

2. **Integration Point Map**:
   - Diagram or detailed description of how components interact
   - Identify where action plugins need to integrate
   - Note any potential breaking points

3. **Pattern Library**:
   - Document common action patterns found
   - Group similar abilities/actions
   - Identify what can be abstracted vs. what needs custom logic

4. **Risk Assessment**:
   - List potential challenges in the refactoring
   - Identify areas where changes might break existing functionality
   - Suggest mitigation strategies

## Tools and Techniques

- **Grep/Search**: Use to find all instances of key methods/patterns
  ```bash
  grep -r "apply_damage" backend/autofighter/
  grep -r "BUS.emit_async" backend/autofighter/rooms/battle/
  ```

- **Call Graph**: Trace function calls to understand flow
- **Git Blame**: Check history for context on why things work certain ways
- **Test Runs**: Run existing tests to understand expected behavior
  ```bash
  cd backend && uv run pytest tests/test_battle*.py -v
  ```

## Time Estimate

- Reading and analyzing code: 8-12 hours
- Documentation writing: 4-6 hours
- Testing and verification: 2-3 hours
- **Total: ~14-21 hours**

## Acceptance Criteria

- [ ] All 10 research areas documented in goal file
- [ ] Each section includes your name, date, and findings
- [ ] At least 3 code examples provided per section
- [ ] Integration points clearly identified
- [ ] Pattern library created
- [ ] Risk assessment completed
- [ ] All findings are clear and actionable for implementation tasks

## Dependencies

- None (this can be done independently)

## Follow-up Tasks

After completing this research:
- Review findings with Task Master
- Refine action plugin architecture design based on findings
- Prioritize which actions to migrate first
- Create specific implementation tasks for high-priority actions

## Notes

- This is primarily a documentation task - focus on understanding and explaining
- Be thorough but practical - we need enough detail to implement, not exhaustive
- When in doubt, add more detail rather than less
- Flag anything that seems overly complex or problematic
- Include your thought process, not just facts
- Update the goal file as you go - don't wait until the end
