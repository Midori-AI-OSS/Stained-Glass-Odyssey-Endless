# Migrate Character Special Abilities to Action Plugins

## Task ID
`fac8f16b-migrate-character-special-abilities`

## Priority
Medium

## Status
WIP

## Description
Extract character-specific special abilities from character plugin classes and convert them to action plugins. Special abilities are unique skills that differentiate characters beyond normal attacks and ultimates (e.g., summon abilities, special attacks, utility skills). This migration will standardize ability implementation and make it easier to add new character abilities.

## Context
Currently, character-specific abilities are embedded directly in character plugin classes. For example, Luna's sword summons are implemented as methods in the Luna character class. With the action plugin system now in place, these abilities should be extracted as standalone action plugins that can be registered to characters.

## Rationale
- **Separation of Concerns**: Character definitions should focus on stats, appearance, and passive traits
- **Reusability**: Abilities implemented as plugins can potentially be shared across characters
- **Consistency**: All active abilities use the same action plugin interface
- **Maintainability**: Easier to find, modify, and test individual abilities
- **Extensibility**: New abilities can be added without modifying character classes

## Current Implementation

### Example: Character with Embedded Abilities
Character classes currently may include:
- Ability trigger methods (e.g., `on_ability_use()`)
- Summon creation logic
- Special attack implementations
- Conditional ability logic

These need to be extracted and standardized as action plugins.

## Objectives
1. Identify all character-specific special abilities across all character plugins
2. Create action plugin for each special ability
3. Register abilities to characters in ActionRegistry
4. Update character classes to reference abilities by ID instead of implementing them
5. Ensure abilities are properly available during character's turns
6. Maintain backward compatibility during migration

## Implementation Steps

### Step 1: Audit Character Files
Review all files in `backend/plugins/characters/`:
```bash
ls -1 backend/plugins/characters/*.py
```

For each character file:
1. Identify special abilities (methods that trigger actions beyond basic attack)
2. Document ability name, effect, trigger condition
3. Note dependencies (summons, specific stats, etc.)

### Step 2: Create Special Ability Base Class
Create `backend/plugins/actions/special/_base.py`:
```python
from dataclasses import dataclass
from plugins.actions._base import ActionBase, ActionType

@dataclass(kw_only=True, slots=True)
class SpecialAbilityBase(ActionBase):
    """Base class for character special abilities."""
    
    action_type: ActionType = ActionType.SPECIAL
    character_id: str = ""  # Which character can use this
    
    # Override if ability has special unlock conditions
    async def can_execute(self, actor, targets, context):
        """Check if ability can be used."""
        # Verify actor is the right character
        if self.character_id and getattr(actor, 'id', '') != self.character_id:
            return False
        return await super().can_execute(actor, targets, context)
```

### Step 3: Migrate Individual Abilities
For each identified ability:

1. Create file: `backend/plugins/actions/special/{character_id}_{ability_name}.py`
2. Implement ability as action plugin extending SpecialAbilityBase
3. Move logic from character class to plugin's execute() method
4. Preserve all behavior exactly as it was

Example:
```python
@dataclass(kw_only=True, slots=True)
class LunaSwordSummon(SpecialAbilityBase):
    plugin_type = "action"
    id: str = "special.luna.sword_summon"
    name: str = "Summon Sword"
    description: str = "Luna summons a magical sword to fight alongside her"
    character_id: str = "luna"
    cooldown_turns: int = 5
    
    async def execute(self, actor, targets, context):
        # Implementation from luna.py
        result = ActionResult(success=True)
        # ... summon logic ...
        return result
```

### Step 4: Update Character Classes
For each character with migrated abilities:
1. Remove ability implementation methods
2. Add list of ability IDs to character definition
3. Register abilities in ActionRegistry during character initialization

Example character update:
```python
class Luna:
    plugin_type = "character"
    id = "luna"
    name = "Luna"
    # ... stats ...
    
    # NEW: List of special ability IDs
    special_abilities = [
        "special.luna.sword_summon",
        "special.luna.moon_strike",
    ]
    
    # REMOVED: Ability implementation methods
```

### Step 5: Update Character Action Loading
Modify character action assignment logic to load special abilities:
```python
# In ActionRegistry or character loading code
registry = ActionRegistry()
for ability_id in character.special_abilities:
    registry.register_character_actions(character.id, [ability_id])
```

### Step 6: Update Turn Loop
Ensure turn loop can present and execute special abilities:
- Add UI to show available special abilities
- Handle ability selection alongside normal attack
- Execute via ActionRegistry.instantiate()

## Priority Order for Migration

### Phase 1: Simple Abilities (Start Here)
- Single-target damage abilities
- Simple buff/debuff abilities
- Self-heal or self-buff abilities

### Phase 2: Complex Abilities
- Summon-based abilities (Luna's swords)
- Multi-stage abilities
- Conditional abilities

### Phase 3: Advanced Mechanics
- Transformation abilities
- Mode-switching abilities
- Combo abilities

## Files to Review

### Character Files (Audit for Abilities)
```
backend/plugins/characters/luna.py
backend/plugins/characters/becca.py
backend/plugins/characters/carly.py
backend/plugins/characters/hilander.py
backend/plugins/characters/graygray.py
backend/plugins/characters/ixia.py
backend/plugins/characters/kboshi.py
backend/plugins/characters/lady_*.py
backend/plugins/characters/mezzy.py
backend/plugins/characters/mimic.py
backend/plugins/characters/persona_*.py
```

### Files to Create
- `backend/plugins/actions/special/__init__.py`
- `backend/plugins/actions/special/_base.py`
- `backend/plugins/actions/special/{character}_{ability}.py` (multiple files)

### Files to Modify
- Character plugin files (to remove embedded abilities)
- `backend/autofighter/rooms/battle/turn_loop/player_turn.py` (ability selection UI)
- `backend/plugins/actions/registry.py` (character ability loading)

## Acceptance Criteria
- [ ] All character files audited for special abilities
- [ ] SpecialAbilityBase class created
- [ ] At least 5 character abilities migrated to action plugins
- [ ] Character classes updated to reference abilities by ID
- [ ] Character ability loading implemented in ActionRegistry
- [ ] Turn loop can present and execute special abilities
- [ ] All migrated abilities work exactly as they did before
- [ ] Tests created for special ability plugins
- [ ] All existing tests still pass
- [ ] Linting passes (run `uv tool run ruff check backend --fix`)
- [ ] Documentation updated in `.codex/implementation/action-plugin-system.md`

## Testing Requirements

### Unit Tests
- Test SpecialAbilityBase character_id validation
- Test each special ability plugin's execute() method
- Test ability cooldown mechanics
- Test ability cost deduction

### Integration Tests
- Test ability available to correct character only
- Test ability execution in battle context
- Test ability selection UI
- Test ability registration per character

## Dependencies
- Existing action plugin system (ActionBase, ActionRegistry, BattleContext)
- Task `6c57b775-action-plugin-migration-analysis` (should identify all special abilities)
- Task `de34385f-migrate-ultimate-actions-to-plugins` (provides pattern to follow)

## References
- `.codex/implementation/action-plugin-system.md` - Action system documentation
- `backend/plugins/actions/_base.py` - Base action class
- `backend/plugins/characters/` - Character plugin files
- `.codex/implementation/player-foe-reference.md` - Character roster documentation

## Notes for Coder
- Start with the simplest abilities first to establish patterns
- Document which abilities you're migrating for each character
- Preserve exact behavior - this is a refactor, not a redesign
- Some abilities may be passive effects, not active abilities - those stay as passives
- If an ability is tied to a passive trigger, it might not be a good candidate for action plugin
- Consider creating helper methods in SpecialAbilityBase for common patterns
- Make sure to update `.codex/implementation/player-foe-reference.md` if ability descriptions change
- Test each migrated ability individually before moving to the next
