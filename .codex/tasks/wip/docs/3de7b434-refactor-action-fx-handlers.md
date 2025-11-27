# Refactor Action/Effect Handlers Like Aftertaste

## Task ID
`3de7b434-refactor-action-fx-handlers`

## Priority
Medium

## Status
WIP

## Description
There must be better ways to handle some actions/effects like Aftertaste. Currently, effects like Aftertaste (Lightning's stacking effect) are implemented in a scattered manner across multiple files with duplicated logic. This task aims to analyze the current implementation and propose a cleaner, more maintainable pattern for action/effect handlers.

## Context
Aftertaste is a Lightning-specific effect that:
1. Stacks with each hit
2. Triggers bonus damage or effects at certain thresholds
3. Resets or modifies behavior based on action type

The current implementation involves:
- Effect tracking in `backend/plugins/effects/aftertaste.py`
- Stack management scattered across damage type handlers
- Threshold logic in ultimate implementations
- Event-based triggers in multiple locations

This pattern repeats for other complex effects, leading to:
- Code duplication
- Difficult debugging
- Inconsistent behavior across similar effects
- Hard-to-follow control flow

## Current Implementation Analysis

### Aftertaste Effect (`backend/plugins/effects/aftertaste.py`)
```python
# Likely contains:
- Stack tracking per-entity
- Effect application logic
- Description/UI metadata
```

### Lightning Ultimate (`backend/plugins/actions/ultimate/lightning_ultimate.py`)
```python
# Likely contains:
- Aftertaste stack buildup during ultimate
- Threshold checking for bonus effects
- Stack consumption/reset logic
```

### Lightning Damage Type (`backend/plugins/damage_types/lightning.py`)
```python
# Likely contains:
- on_hit handlers for aftertaste
- Chain damage mechanics
- DOT interactions
```

## Problem Analysis
1. **Scattered Logic**: Effect behavior is spread across 3+ files
2. **Duplication**: Stack management code appears in multiple places
3. **Testing Difficulty**: Hard to unit test individual components
4. **Maintainability**: Changes require updates in multiple files
5. **Discoverability**: New developers can't easily find all effect logic

## Objectives
1. Identify all action/effect handlers with similar patterns to Aftertaste
2. Design a unified "complex effect handler" interface
3. Consolidate Aftertaste logic as a proof-of-concept
4. Document the new pattern for future effects
5. Consider a registry-based approach for effect lifecycle management

## Proposed Solution: Effect Handler Pattern

### New Base Class: `ComplexEffectHandler`
```python
# backend/plugins/effects/_handlers.py

@dataclass
class EffectHandlerBase:
    """Base class for complex effects with lifecycle management."""
    
    plugin_type = "effect_handler"
    id: str = ""
    name: str = ""
    
    # Lifecycle hooks
    async def on_apply(self, target: Stats, source: Stats, **kwargs) -> None:
        """Called when effect is first applied."""
        pass
    
    async def on_stack(self, target: Stats, source: Stats, count: int, **kwargs) -> None:
        """Called when effect stacks."""
        pass
    
    async def on_threshold(self, target: Stats, source: Stats, threshold: int, **kwargs) -> None:
        """Called when stack count reaches a threshold."""
        pass
    
    async def on_trigger(self, target: Stats, source: Stats, event: str, **kwargs) -> None:
        """Called when effect triggers (e.g., on hit, on turn end)."""
        pass
    
    async def on_expire(self, target: Stats, **kwargs) -> None:
        """Called when effect expires or is consumed."""
        pass
    
    async def on_remove(self, target: Stats, **kwargs) -> None:
        """Called when effect is forcibly removed."""
        pass
    
    def get_stack_count(self, target: Stats) -> int:
        """Return current stack count for target."""
        return getattr(target, f"_{self.id}_stacks", 0)
    
    def set_stack_count(self, target: Stats, count: int) -> None:
        """Set stack count for target."""
        setattr(target, f"_{self.id}_stacks", count)
```

### Refactored Aftertaste
```python
# backend/plugins/effects/aftertaste.py

@dataclass
class AftertasteHandler(EffectHandlerBase):
    """Aftertaste: Lightning's stacking effect that builds to bonus damage."""
    
    plugin_type = "effect_handler"
    id: str = "aftertaste"
    name: str = "Aftertaste"
    
    # Thresholds for bonus effects
    BONUS_THRESHOLD: ClassVar[int] = 10
    MAX_STACKS: ClassVar[int] = 99
    
    async def on_stack(self, target: Stats, source: Stats, count: int, **kwargs) -> None:
        """Called when Aftertaste stacks increase."""
        current = self.get_stack_count(target)
        new_count = min(current + count, self.MAX_STACKS)
        self.set_stack_count(target, new_count)
        
        # Check thresholds
        if new_count >= self.BONUS_THRESHOLD and current < self.BONUS_THRESHOLD:
            await self.on_threshold(target, source, self.BONUS_THRESHOLD)
    
    async def on_threshold(self, target: Stats, source: Stats, threshold: int, **kwargs) -> None:
        """Trigger bonus damage or effect at threshold."""
        if threshold == self.BONUS_THRESHOLD:
            await self._apply_bonus_damage(target, source)
    
    async def _apply_bonus_damage(self, target: Stats, source: Stats) -> None:
        """Apply Aftertaste's bonus damage."""
        stacks = self.get_stack_count(target)
        bonus = stacks * 0.1  # 10% per stack
        # Apply bonus to next attack or immediate damage
        ...
    
    async def on_trigger(self, target: Stats, source: Stats, event: str, **kwargs) -> None:
        """Handle various trigger events."""
        if event == "hit_landed":
            await self.on_stack(target, source, 1)
        elif event == "ultimate_used":
            # Maybe consume stacks or apply special effect
            pass
```

### Effect Handler Registry
```python
# backend/autofighter/effect_handlers.py

class EffectHandlerRegistry:
    """Central registry for complex effect handlers."""
    
    _handlers: dict[str, EffectHandlerBase] = {}
    
    @classmethod
    def register(cls, handler: EffectHandlerBase) -> None:
        cls._handlers[handler.id] = handler
    
    @classmethod
    def get(cls, effect_id: str) -> EffectHandlerBase | None:
        return cls._handlers.get(effect_id)
    
    @classmethod
    async def trigger_all(cls, event: str, target: Stats, source: Stats, **kwargs) -> None:
        """Trigger all relevant handlers for an event."""
        for handler in cls._handlers.values():
            await handler.on_trigger(target, source, event, **kwargs)
```

## Implementation Steps

### Step 1: Analyze Existing Effects
Review these effects for similar patterns:
- Aftertaste (Lightning)
- Critical Boost (`backend/plugins/effects/critical_boost.py`)
- Burn stacks (Fire)
- Freeze mechanics (Ice)
- Any other stacking/threshold effects

### Step 2: Create Handler Base Class
Create `backend/plugins/effects/_handlers.py` with:
- `EffectHandlerBase` class
- Common lifecycle hooks
- Stack management utilities
- Threshold tracking

### Step 3: Create Handler Registry
Create `backend/autofighter/effect_handlers.py` with:
- `EffectHandlerRegistry` class
- Auto-discovery via plugin loader
- Event trigger distribution

### Step 4: Refactor Aftertaste
Migrate Aftertaste to use the new pattern:
1. Create `AftertasteHandler` class
2. Move stack logic from scattered locations
3. Register with handler registry
4. Update callers to use registry

### Step 5: Update Callers
Modify places that interact with Aftertaste:
- `lightning.py` - Use handler.on_trigger()
- `lightning_ultimate.py` - Use handler for stack management
- Any other files referencing Aftertaste

### Step 6: Document Pattern
Update documentation:
- `.codex/implementation/effect-handler-system.md` (new)
- Update plugin-system.md
- Add examples for future effects

## Files to Create
- `backend/plugins/effects/_handlers.py` - Base handler class
- `backend/autofighter/effect_handlers.py` - Registry
- `.codex/implementation/effect-handler-system.md` - Documentation

## Files to Modify
- `backend/plugins/effects/aftertaste.py` - Refactor to handler
- `backend/plugins/damage_types/lightning.py` - Use handler
- `backend/plugins/actions/ultimate/lightning_ultimate.py` - Use handler
- `backend/plugins/plugin_loader.py` - Add effect_handler discovery

## Acceptance Criteria
- [ ] EffectHandlerBase class created with lifecycle hooks
- [ ] EffectHandlerRegistry created with auto-discovery
- [ ] Aftertaste refactored to use new pattern
- [ ] All Lightning-related tests pass
- [ ] No scattered Aftertaste logic remains in damage types
- [ ] Documentation created for new pattern
- [ ] Linting passes (`uv tool run ruff check backend --fix`)

## Testing Requirements

### Unit Tests
- Test EffectHandlerBase lifecycle hooks
- Test stack management utilities
- Test threshold detection
- Test AftertasteHandler specifically

### Integration Tests
- Test Aftertaste during Lightning combat
- Test Aftertaste during Lightning ultimate
- Test stack persistence across turns
- Test threshold bonus application

## Notes for Coder
- Start with Aftertaste as the proof-of-concept
- Don't migrate other effects yet - wait for pattern validation
- Keep backward compatibility during refactor
- Consider performance implications of registry lookups
- Event-based triggers may need debouncing for high-frequency events
- This is a refactoring task - behavior should not change, only organization
