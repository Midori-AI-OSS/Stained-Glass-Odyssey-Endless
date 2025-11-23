# Standardize Buff and Debuff Plugin System

## Task ID
`7782ecea-standardize-buff-debuff-plugins`

## Priority
High

## Status
WIP

## Description
Create a standardized plugin system for buffs and debuffs, moving them into the `backend/plugins/effects/` directory. Currently buffs and debuffs are applied via the `StatEffect` class which is a generic stat modifier system, but they lack the plugin organization and discoverability of DoTs and HoTs. This task creates a proper plugin structure for buffs (positive effects) and debuffs (negative effects) similar to the existing DoT/HoT systems.

## Context
Currently:
- Buffs/debuffs are applied using `StatEffect(stat_modifiers={"atk": 5})` scattered throughout code
- No central registry or plugin system for effect discovery
- Inconsistent naming and application patterns
- Hard to discover what buffs/debuffs exist in the game

Desired:
- Plugin-based buff/debuff system in `backend/plugins/effects/`
- Similar structure to DoTs (`backend/plugins/dots/`) and HoTs (`backend/plugins/hots/`)
- Discoverability via plugin loader
- Consistent interface for applying and tracking effects

## Current Implementation

### StatEffect System
Located in `backend/autofighter/stat_effect.py`:
```python
@dataclass
class StatEffect:
    name: str
    stat_modifiers: Dict[str, Union[int, float]]
    duration: int = -1  # -1 for permanent, >0 for temporary
    source: str = "unknown"
```

Usage example from `attack_up` passive:
```python
effect = StatEffect(
    name=f"{self.id}_atk_up_{stack_index}",
    stat_modifiers={"atk": self.amount},
    source=self.id,
)
target.add_effect(effect)
```

### Existing Effect Systems
- **DoTs** (`backend/plugins/dots/`): 16 different DoT plugins (bleed, poison, frozen_wound, etc.)
- **HoTs** (`backend/plugins/hots/`): 4 different HoT plugins (regeneration, player_heal, etc.)
- **Effects folder** (`backend/plugins/effects/`): Currently has 2 files (aftertaste.py, critical_boost.py)

## Objectives
1. Design buff/debuff plugin base classes similar to DoT/HoT structure
2. Create plugin directory structure in `backend/plugins/effects/`
3. Migrate common buffs to plugin format (attack up, defense up, speed up, etc.)
4. Migrate common debuffs to plugin format (attack down, defense down, slow, stun, etc.)
5. Integrate with plugin loader for auto-discovery
6. Maintain backward compatibility with StatEffect system
7. Update documentation

## Implementation Steps

### Step 1: Analyze DoT/HoT Structure
Review existing systems to understand pattern:
```bash
cat backend/plugins/dots/bleed.py
cat backend/plugins/hots/regeneration.py
```

Key learnings:
- Plugin type identifier
- Trigger mechanism
- Application method
- Stacking behavior

### Step 2: Design Buff/Debuff Base Classes
Create `backend/plugins/effects/_base.py`:
```python
from dataclasses import dataclass
from autofighter.stat_effect import StatEffect

@dataclass
class BuffBase:
    """Base class for positive stat effects (buffs)."""
    plugin_type = "buff"
    id: str = ""
    name: str = ""
    stat_modifiers: dict[str, float] = field(default_factory=dict)
    duration: int = -1  # -1 for permanent
    stack_display: str = "pips"
    max_stacks: int | None = None
    
    async def apply(self, target, **kwargs):
        """Apply the buff to a target."""
        effect = StatEffect(
            name=self.id,
            stat_modifiers=self.stat_modifiers,
            duration=self.duration,
            source=self.id,
        )
        target.add_effect(effect)
    
    @classmethod
    def get_description(cls) -> str:
        raise NotImplementedError

@dataclass  
class DebuffBase:
    """Base class for negative stat effects (debuffs)."""
    plugin_type = "debuff"
    # Similar structure to BuffBase
    # ...
```

### Step 3: Create Directory Structure
```bash
mkdir -p backend/plugins/effects/buffs
mkdir -p backend/plugins/effects/debuffs
touch backend/plugins/effects/__init__.py
touch backend/plugins/effects/buffs/__init__.py
touch backend/plugins/effects/debuffs/__init__.py
touch backend/plugins/effects/_base.py
```

### Step 4: Migrate Common Buffs
Create plugin files for standard buffs:

**Attack Up** (`backend/plugins/effects/buffs/attack_up.py`):
```python
from dataclasses import dataclass
from .._base import BuffBase

@dataclass
class AttackUpBuff(BuffBase):
    plugin_type = "buff"
    id = "buff_attack_up"
    name = "Attack Up"
    stat_modifiers = {"atk": 5}
    duration = -1
    
    @classmethod
    def get_description(cls) -> str:
        return f"Increases ATK by {cls.stat_modifiers['atk']}"
```

Similar plugins for:
- Defense Up
- Speed Up
- Critical Rate Up
- Critical Damage Up
- Effect Hit Rate Up
- Effect Resistance Up

### Step 5: Migrate Common Debuffs
Create plugin files for standard debuffs:

**Attack Down** (`backend/plugins/effects/debuffs/attack_down.py`):
```python
from dataclasses import dataclass
from .._base import DebuffBase

@dataclass
class AttackDownDebuff(DebuffBase):
    plugin_type = "debuff"
    id = "debuff_attack_down"
    name = "Attack Down"
    stat_modifiers = {"atk": -5}
    duration = 3  # Temporary effect
    
    @classmethod
    def get_description(cls) -> str:
        return f"Decreases ATK by {abs(cls.stat_modifiers['atk'])} for {cls.duration} turns"
```

Similar plugins for:
- Defense Down
- Speed Down (Slow)
- Blind (reduced hit rate)
- Weakness (reduced damage dealt)
- Vulnerability (increased damage taken)

### Step 6: Update Plugin Loader
Modify `backend/plugins/plugin_loader.py` if needed to:
- Discover buff/debuff plugins
- Register in appropriate registries
- Handle "buff" and "debuff" plugin types

### Step 7: Create Registry System
Create `backend/autofighter/buffs.py` and `backend/autofighter/debuffs.py`:
```python
# Similar to PassiveRegistry pattern
class BuffRegistry:
    def __init__(self):
        self._buffs = {}
    
    def register(self, buff_id, buff_class):
        self._buffs[buff_id] = buff_class
    
    def get_buff(self, buff_id):
        return self._buffs.get(buff_id)
    
    async def apply_buff(self, buff_id, target, **kwargs):
        buff_cls = self.get_buff(buff_id)
        if buff_cls:
            buff = buff_cls()
            await buff.apply(target, **kwargs)
```

### Step 8: Maintain Backward Compatibility
Ensure existing `StatEffect` usage still works:
- Don't break existing code that directly creates StatEffect
- Buff/debuff plugins are a layer on top of StatEffect
- Gradually migrate callsites to use plugins instead of raw StatEffect

### Step 9: Update Existing Code
Find and update callsites that could use the new system:
```bash
grep -r "StatEffect" backend/ --include="*.py" | grep -v ".venv"
```

Priority areas:
- Character abilities
- Card effects
- Relic effects
- Passive effects

### Step 10: Documentation
Update:
- `.codex/implementation/stats-and-effects.md` - Add buff/debuff plugin system
- Create `.codex/implementation/buff-debuff-system.md` - Detailed documentation
- Update `.codex/implementation/plugin-system.md` - Add buff/debuff to plugin types

## Files to Create

### New Files
- `backend/plugins/effects/_base.py` - BuffBase and DebuffBase classes
- `backend/plugins/effects/buffs/__init__.py`
- `backend/plugins/effects/debuffs/__init__.py`
- `backend/plugins/effects/buffs/attack_up.py`
- `backend/plugins/effects/buffs/defense_up.py`
- `backend/plugins/effects/buffs/speed_up.py`
- `backend/plugins/effects/buffs/crit_rate_up.py`
- `backend/plugins/effects/buffs/crit_damage_up.py`
- `backend/plugins/effects/debuffs/attack_down.py`
- `backend/plugins/effects/debuffs/defense_down.py`
- `backend/plugins/effects/debuffs/speed_down.py`
- `backend/plugins/effects/debuffs/blind.py`
- `backend/autofighter/buffs.py` - BuffRegistry
- `backend/autofighter/debuffs.py` - DebuffRegistry
- `.codex/implementation/buff-debuff-system.md` - Documentation

### Files to Modify
- `backend/plugins/plugin_loader.py` - Add buff/debuff discovery
- `.codex/implementation/stats-and-effects.md` - Update with new system
- `.codex/implementation/plugin-system.md` - Add buff/debuff plugin types

## Acceptance Criteria
- [ ] BuffBase and DebuffBase classes created with proper interface
- [ ] Directory structure created (effects/buffs/, effects/debuffs/)
- [ ] At least 5 common buffs migrated to plugins
- [ ] At least 5 common debuffs migrated to plugins
- [ ] BuffRegistry and DebuffRegistry implemented
- [ ] Plugin loader discovers and registers buff/debuff plugins
- [ ] Backward compatibility maintained with StatEffect
- [ ] All existing tests still pass
- [ ] New tests created for buff/debuff plugins
- [ ] Documentation created/updated
- [ ] Linting passes (run `uv tool run ruff check backend --fix`)

## Testing Requirements

### Unit Tests
- Test BuffBase and DebuffBase application
- Test each buff plugin's effect
- Test each debuff plugin's effect
- Test stacking behavior
- Test duration/expiration

### Integration Tests
- Test buff application in battle context
- Test debuff application in battle context
- Test interaction with existing StatEffect code
- Test plugin auto-discovery

## Dependencies
- Understanding of DoT/HoT plugin systems
- Understanding of StatEffect system
- Plugin loader system

## References
- `backend/autofighter/stat_effect.py` - Current StatEffect implementation
- `backend/plugins/dots/` - DoT plugin examples
- `backend/plugins/hots/` - HoT plugin examples
- `backend/plugins/plugin_loader.py` - Plugin discovery system
- `.codex/implementation/stats-and-effects.md` - Stats and effects documentation

## Notes for Coder
- This is about ORGANIZATION, not functionality - StatEffect already works
- Goal is discoverability and consistency, not replacing StatEffect
- Follow DoT/HoT patterns closely for consistency
- Start with simple buffs/debuffs before complex ones
- Buffs are positive effects (increases), debuffs are negative (decreases)
- Some effects might be neither (e.g., element conversion) - handle case-by-case
- Consider whether "critical_boost" and "aftertaste" should be buffs or stay separate
- This is separate from ACTION plugins - these are the EFFECTS that actions apply
