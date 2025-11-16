# Task: Action Plugin Architecture Design

**Status:** WIP  
**Priority:** High  
**Category:** Architecture/Design  
**Goal File:** `.codex/tasks/wip/GOAL-action-plugin-system.md`

## Objective

Design a comprehensive action plugin architecture that will serve as the foundation for converting all hardcoded battle actions into modular, reusable plugin components.

## Background

Currently, all combat actions (normal attacks, abilities, passives) are hardcoded in the battle turn loop. This task involves designing a plugin-based architecture that will:
1. Define a clear interface for all action types
2. Integrate with the existing plugin system
3. Work seamlessly with damage types, effects, and the event bus
4. Support all current action patterns (single target, multi-target, AOE, DoT, HoT, etc.)

## Requirements

### 1. Action Base Class Design

Create a base class `ActionBase` (or similar) with the following interface:

```python
@dataclass
class ActionBase:
    """Base class for all combat action plugins."""
    
    plugin_type = "action"
    
    # Metadata
    id: str  # Unique action identifier
    name: str  # Display name
    description: str  # Action description
    action_type: str  # "normal_attack", "special", "passive", "ultimate", "item"
    
    # Execution properties
    cost: int = 0  # Action point cost or energy cost
    cooldown: int = 0  # Cooldown in turns
    target_type: str = "single"  # "single", "aoe", "all", "self", "allies"
    max_targets: int = 1
    
    # Animation properties
    animation_duration: float = 0.0
    animation_per_target: float = 0.0
    animation_name: str = ""
    
    # Methods to implement
    async def can_execute(self, actor: Stats, targets: list[Stats], context: BattleContext) -> bool:
        """Check if this action can be executed."""
        raise NotImplementedError
    
    async def execute(self, actor: Stats, targets: list[Stats], context: BattleContext) -> ActionResult:
        """Execute the action and return results."""
        raise NotImplementedError
    
    def get_valid_targets(self, actor: Stats, allies: list[Stats], enemies: list[Stats]) -> list[Stats]:
        """Return list of valid targets for this action."""
        raise NotImplementedError
```

**Considerations:**
- Should there be separate base classes for different action types?
- How to handle actions that change target selection mid-execution?
- How to represent complex cost mechanics (e.g., HP cost, multiple resource types)?

### 2. Action Result Structure

Define a standard result structure that actions return:

```python
@dataclass
class ActionResult:
    """Result of an action execution."""
    
    success: bool
    damage_dealt: dict[Stats, int]  # Target -> damage mapping
    healing_done: dict[Stats, int]  # Target -> healing mapping
    effects_applied: list[tuple[Stats, str]]  # (target, effect_id) pairs
    effects_removed: list[tuple[Stats, str]]
    resources_consumed: dict[str, int]  # Resource type -> amount
    messages: list[str]  # Combat log messages
    animations: list[AnimationData]  # Animation trigger data
    extra_turns_granted: list[Stats]  # Actors who get extra turns
```

### 3. Battle Context Object

Design a context object that provides battle state to actions:

```python
@dataclass
class BattleContext:
    """Context provided to actions during execution."""
    
    turn: int
    actor: Stats
    allies: list[Stats]
    enemies: list[Stats]
    registry: PassiveRegistry
    effect_managers: dict[Stats, EffectManager]
    enrage_state: EnrageState
    visual_queue: Any
    event_bus: EventBus
    
    # Helper methods
    def get_effect_manager(self, target: Stats) -> EffectManager:
        """Get the effect manager for a target."""
        pass
    
    async def apply_damage_to_target(self, target: Stats, amount: float, **kwargs) -> int:
        """Apply damage using the standard damage pipeline."""
        pass
    
    async def apply_healing_to_target(self, target: Stats, amount: float) -> int:
        """Apply healing using the standard healing pipeline."""
        pass
```

### 4. Action Registry

Design an action registry system:

```python
class ActionRegistry:
    """Registry for managing action plugins."""
    
    def register_action(self, action_class: type[ActionBase]) -> None:
        """Register an action plugin."""
        pass
    
    def get_action(self, action_id: str) -> ActionBase | None:
        """Get an action by ID."""
        pass
    
    def get_actions_by_type(self, action_type: str) -> list[ActionBase]:
        """Get all actions of a specific type."""
        pass
    
    def get_character_actions(self, character_id: str) -> list[ActionBase]:
        """Get all actions available to a character."""
        pass
```

### 5. Integration Points

Document how the action plugin system integrates with:

- **Damage Type System**: How do actions interact with damage types?
- **Effect System**: How do actions apply/remove effects?
- **Event Bus**: What events should actions emit?
- **Animation System**: How do actions trigger animations?
- **Passive System**: How do passive effects interact with actions?
- **Turn Loop**: How does the turn loop select and execute actions?

### 6. Migration Strategy

Design the migration path:

1. **Phase 1**: Create action plugin infrastructure without breaking existing code
2. **Phase 2**: Implement normal attack as plugin, run in parallel with hardcoded version
3. **Phase 3**: Switch to plugin-based normal attack, remove hardcoded version
4. **Phase 4**: Migrate character abilities one at a time
5. **Phase 5**: Migrate passive effects to use action plugin system

### 7. File Structure

Propose directory structure for action plugins:

```
backend/plugins/actions/
├── __init__.py
├── _base.py              # ActionBase class
├── registry.py           # ActionRegistry class
├── context.py            # BattleContext class
├── result.py             # ActionResult class
├── normal/               # Normal attacks
│   ├── basic_attack.py
│   └── ...
├── special/              # Character special abilities
│   ├── luna_sword_summon.py
│   ├── becca_heal.py
│   └── ...
├── ultimate/             # Ultimate abilities
│   └── ...
└── passive/              # Passive action triggers
    └── ...
```

## Deliverables

1. **Design Document** (`.codex/implementation/action-plugin-system.md`):
   - Detailed class diagrams
   - Interface specifications
   - Integration point documentation
   - Migration strategy

2. **Code Stubs** (in `backend/plugins/actions/`):
   - `_base.py` with `ActionBase` class
   - `registry.py` with `ActionRegistry` class
   - `context.py` with `BattleContext` class
   - `result.py` with `ActionResult` class

3. **Example Action Plugin**:
   - Implement one simple action (e.g., basic attack) as proof of concept
   - Should compile and pass basic tests
   - Does not need to be integrated with battle system yet

4. **Test Plan**:
   - Unit tests for action plugin infrastructure
   - Integration test strategy
   - Backward compatibility verification plan

## Research Tasks

Before finalizing the design, investigate and document in `GOAL-action-plugin-system.md`:

1. **Current Action Patterns**: Survey all existing actions (character abilities, passives, etc.)
2. **Edge Cases**: Identify complex actions that might not fit the standard pattern
3. **Performance Considerations**: Ensure plugin system won't introduce overhead
4. **Save Compatibility**: Verify that plugin changes won't break saves

## Acceptance Criteria

- [ ] Design document completed and reviewed
- [ ] All base classes implemented as stubs with docstrings
- [ ] Example action plugin implemented and tested
- [ ] Integration points documented
- [ ] Migration strategy approved
- [ ] No existing tests broken
- [ ] Code passes linting (`uvx ruff check`)

## Dependencies

- None (this is the foundation task)

## Estimated Effort

- Design: 4-6 hours
- Implementation: 6-8 hours
- Testing: 2-4 hours
- Documentation: 3-4 hours
- **Total: ~15-22 hours**

## Notes

- This is a design-heavy task - take time to think through the architecture
- Consult existing plugin system patterns for consistency
- Consider future extensibility (e.g., combo actions, conditional effects)
- Keep performance in mind - this will be called frequently in battle
- Document any open questions or design tradeoffs for review
