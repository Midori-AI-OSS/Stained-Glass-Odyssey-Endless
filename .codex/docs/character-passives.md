# Character Passive System Documentation

## Overview

The character passive system in Midori AI AutoFighter provides unique abilities that modify gameplay mechanics for each character. Passives are implemented as plugins that integrate seamlessly with the battle system.

## Architecture

### Plugin-Based Design

Passives follow the plugin architecture pattern:

- **Location**: `backend/plugins/passives/`
- **Registration**: Automatic discovery via plugin loader
- **Integration**: Linked to character plugins via `passives` field

### Core Components

1. **PassiveRegistry** (`backend/autofighter/passives.py`)
   - Central manager for all passive abilities
   - Handles trigger events and effect application
   - Supports multiple trigger types

2. **Passive Plugins** (`backend/plugins/passives/`)
   - Individual passive implementations
   - Each passive is a self-contained plugin class
   - Standard interface with `apply()` method

3. **Character Integration** (`backend/plugins/characters/`)
   - Characters declare their passives via `passives: list[str]` field
   - Automatic passive loading during character initialization

## Trigger System

### Available Triggers

| Trigger | Description | Usage |
|---------|-------------|--------|
| `battle_start` | Start of battle | Initial buffs, setup effects |
| `turn_start` | Start of character's turn | Recurring effects, charge building |
| `turn_end` | End of character's turn | Cleanup, decay effects |
| `action_taken` | After character takes action | Charge building, scaling effects |
| `damage_taken` | When character receives damage | Counter-attacks, defensive triggers |
| `hit_landed` | When character successfully hits | Offensive stacking effects |
| `level_up` | Character levels up | Stat bonus application |

### Custom Triggers

Passives can implement custom trigger methods:

```python
async def on_defeat(self, target: "Stats") -> None:
    """Custom trigger for character defeat"""
    # Custom logic here
```

## Implementation Guide

### Creating a New Passive

1. **Create Plugin File** (`backend/plugins/passives/character_passive_name.py`)

```python
from dataclasses import dataclass
from typing import TYPE_CHECKING
from autofighter.stats import StatEffect

if TYPE_CHECKING:
    from autofighter.stats import Stats

@dataclass
class CharacterPassiveName:
    """Character's passive description."""
    plugin_type = "passive"
    id = "character_passive_name"
    name = "Passive Display Name"
    trigger = "trigger_event"  # When this passive activates
    max_stacks = 1  # Maximum instances per character
    
    async def apply(self, target: "Stats") -> None:
        """Apply passive effects to target."""
        effect = StatEffect(
            name=f"{self.id}_effect",
            stat_modifiers={"atk": 10},  # Example: +10 attack
            duration=-1,  # -1 = permanent, >0 = temporary
            source=self.id,
        )
        target.add_effect(effect)
```

2. **Link to Character** (`backend/plugins/characters/character.py`)

```python
@dataclass
class Character(PlayerBase):
    id = "character"
    name = "Character"
    # ... other fields ...
    passives: list[str] = field(default_factory=lambda: ["character_passive_name"])
```

### Adding Passives to Existing Characters

To add a passive to a character that doesn't currently have one:

1. **Create the Passive Plugin** (`backend/plugins/passives/character_passive_name.py`)
2. **Update Character Plugin** to declare the passive:

```python
@dataclass
class Character(PlayerBase):
    # ... existing fields ...
    passives: list[str] = field(default_factory=lambda: ["character_passive_name"])
```

3. **Test Integration** with the battle system

#### Example: Adding a Passive to Carly

```python
# backend/plugins/passives/carly_light_guardian.py
@dataclass
class CarlyLightGuardian:
    """Carly's defensive light-based passive."""
    plugin_type = "passive"
    id = "carly_light_guardian"
    name = "Light Guardian"
    trigger = "damage_taken"
    
    async def apply(self, target: "Stats") -> None:
        # Light-based damage reduction
        if hasattr(target, 'damage_type') and target.damage_type.name == "Light":
            effect = StatEffect(
                name="light_protection",
                stat_modifiers={"mitigation": 15},
                duration=2,
                source=self.id,
            )
            target.add_effect(effect)

# backend/plugins/characters/carly.py
@dataclass
class Carly(PlayerBase):
    id = "carly"
    name = "Carly"
    char_type = CharacterType.B
    gacha_rarity = 5
    damage_type: DamageTypeBase = field(default_factory=Light)
    stat_gain_map: dict[str, str] = field(
        default_factory=lambda: {"atk": "defense"}
    )
    passives: list[str] = field(default_factory=lambda: ["carly_light_guardian"])
```

### Advanced Patterns

#### Class-Level State Tracking

For passives that need persistent state across instances:

```python
from typing import ClassVar

@dataclass
class AdvancedPassive:
    # Class-level state shared across all instances
    _charge_points: ClassVar[dict[int, int]] = {}  # entity_id -> charge
    
    async def apply(self, target: "Stats") -> None:
        entity_id = id(target)
        current_charge = self._charge_points.get(entity_id, 0)
        # Use charge for calculations
```

#### Complex Trigger Handling

For passives with multiple trigger types:

```python
@dataclass
class MultiTriggerPassive:
    trigger = "action_taken"  # Primary trigger
    
    async def apply(self, target: "Stats") -> None:
        """Handle primary trigger"""
        pass
        
    async def on_damage_taken(self, target: "Stats", attacker: "Stats", damage: int) -> None:
        """Handle secondary trigger"""
        pass
```

## Character Roster & Passives

### Characters with Implemented Passives

#### Luna - Lunar Reservoir
- **ID**: `luna_lunar_reservoir`
- **Trigger**: `action_taken`
- **Mechanic**: Charge-based attack scaling (2→4→8→16→32 attacks at 350/500/700/850 thresholds)
- **Max Charge**: 2000 points

#### Graygray - Counter Maestro
- **ID**: `graygray_counter_maestro`
- **Trigger**: `damage_taken`
- **Mechanic**: Counter-attacks with stacking attack/mitigation buffs

#### Mezzy - Gluttonous Bulwark
- **ID**: `mezzy_gluttonous_bulwark`
- **Trigger**: `turn_start`
- **Mechanic**: 20% damage reduction + stat siphoning from allies

#### Ally - Overload
- **ID**: `ally_overload`
- **Trigger**: `action_taken`
- **Mechanic**: Twin daggers (2 attacks) scaling to Overload mode (4 attacks); Overload clears existing HoTs, blocks new HoTs, and caps recoverable HP at 20%

#### Hilander - Critical Ferment
- **ID**: `hilander_critical_ferment`
- **Trigger**: `hit_landed`
- **Mechanic**: Crit stacking with Aftertaste damage on crits

#### Kboshi - Flux Cycle
- **ID**: `kboshi_flux_cycle`
- **Trigger**: `turn_start`
- **Mechanic**: Element switching with damage/HoT stacking on failures

#### Player - Enhanced Growth
- **ID**: `player_level_up_bonus`
- **Trigger**: `level_up`
- **Mechanic**: 1.35× multiplier on all level-up stat gains

#### Bubbles - Bubble Burst
- **ID**: `bubbles_bubble_burst`
- **Trigger**: `hit_landed`
- **Mechanic**: Element switching with bubble stacking and area damage

#### Ixia - Tiny Titan
- **ID**: `ixia_tiny_titan`
- **Trigger**: `damage_taken`
- **Mechanic**: Quadruples Vitality HP gain, converts 500% Vitality to attack, adds 0.01 Vitality on hit for mitigation, HoT, and defense penalty

### Characters without Passives (Available for Future Implementation)

#### Carly
- **Character Type**: B
- **Gacha Rarity**: 5
- **Damage Type**: Light
- **Special Mechanic**: Defense-focused stat gain (ATK → Defense)
- **Passive Status**: *Not yet implemented*

#### Becca
- **Character Type**: B
- **Gacha Rarity**: 5
- **Damage Type**: Variable (Becca-specific)
- **Passive Status**: *Not yet implemented*


#### Mimic
- **Character Type**: C
- **Gacha Rarity**: 5
- **Damage Type**: Variable (Mimic-specific)
- **Passive Status**: *Not yet implemented*

#### Lady Darkness
- **Character Type**: B
- **Gacha Rarity**: 5
- **Damage Type**: Dark
- **Passive Status**: *Not yet implemented*

#### Lady Echo
- **Character Type**: B
- **Gacha Rarity**: 5
- **Damage Type**: Lightning
- **Passive Status**: *Not yet implemented*

#### Lady Fire and Ice
- **Character Type**: B
- **Gacha Rarity**: 6
- **Damage Type**: Variable (LadyFireAndIce-specific)
- **Passive Status**: *Not yet implemented*

#### Lady Light
- **Character Type**: B
- **Gacha Rarity**: 5
- **Damage Type**: Light
- **Passive Status**: *Not yet implemented*

#### Lady of Fire
- **Character Type**: B
- **Gacha Rarity**: 5* (*rarity field missing in plugin)
- **Damage Type**: Fire
- **Passive Status**: *Not yet implemented*

## Battle System Integration

### Passive Triggers in Combat

The battle system automatically triggers passives at appropriate times:

```python
# Example: Damage application triggers damage_taken passives
async def apply_damage(self, target: Stats, damage: int, attacker: Stats = None):
    # Apply damage...
    await self.passive_registry.trigger_damage_taken(target, attacker, damage)
```

### Effect Management

Passives use the `StatEffect` system for temporary and permanent modifications:

- **Temporary Effects**: Have positive duration, tick down each turn
- **Permanent Effects**: Duration = -1, last until manually removed
- **Stacking**: Multiple effects with same name stack additively

## Testing

### Unit Tests

Test individual passives in isolation:

```python
@pytest.mark.asyncio
async def test_passive_behavior():
    registry = PassiveRegistry()
    character = Stats(hp=1000, damage_type=Generic())
    character.passives = ["passive_id"]
    
    # Trigger passive
    await registry.trigger("trigger_event", character)
    
    # Verify effects
    assert len(character._active_effects) > 0
```

### Integration Tests

Use `test_passive_demos.py` for comprehensive passive demonstrations.

### Demo Mode

Run standalone demos:

```bash
cd backend
python -m tests.test_passive_demos
```

## Performance Considerations

### Efficient State Management

- Use `ClassVar` for shared state to avoid instance overhead
- Minimize effect creation/removal in hot paths
- Cache expensive calculations where possible

### Memory Management

- Clean up expired effects regularly
- Use weak references for entity tracking when appropriate
- Avoid memory leaks in long-running battles

## Future Extensions

### Planned Features

1. **Conditional Triggers**: Passives that trigger based on conditions
2. **Passive Interactions**: Cross-character passive synergies
3. **Dynamic Passives**: Passives that change behavior based on game state
4. **Passive Upgrades**: Evolution of passives through gameplay

### Characters Ready for Passive Implementation

The following characters are fully functional but lack passive abilities, making them excellent candidates for future passive implementations:

#### Priority Candidates (Based on Unique Mechanics)
- **Carly**: Defense-focused character with ATK→Defense stat conversion
- **Lady Fire and Ice**: Dual-element character with potential for element-switching passives
- **Mimic**: Copy-based character with potential for adaptive passives

#### Additional Candidates
- **Becca**: Variable damage type for versatile passive options
- **Lady Darkness**: Dark damage type for shadow-based mechanics
- **Lady Echo**: Lightning damage type for chain/echo effects
- **Lady Light**: Light damage type for healing/protection passives
- **Lady of Fire**: Fire damage type for burning/DoT mechanics

### Passive Design Themes by Character

#### Element-Based Passives
- **Fire Characters** (Lady of Fire): Burning DoT, area damage
- **Light Characters** (Carly, Lady Light): Healing, damage reduction
- **Dark Characters** (Lady Darkness): Life steal, debuff mechanics
- **Lightning Characters** (Lady Echo): Chain damage, speed boosts

#### Mechanic-Based Passives
- **Defense Specialists** (Carly): Damage mitigation, counter-attacks
- **Variable Types** (Becca, Mimic): Adaptive abilities, form changes
- **Dual Element** (Lady Fire and Ice): Element switching, temperature effects

### API Extensions

```python
# Future: Conditional triggers
async def should_trigger(self, target: "Stats", context: dict) -> bool:
    return context.get("condition_met", False)

# Future: Passive interactions
async def interact_with(self, other_passive: "PassiveBase", target: "Stats") -> None:
    # Handle cross-passive interactions

# Future: Character-specific triggers
async def on_stat_conversion(self, target: "Stats", stat_from: str, stat_to: str, amount: int) -> None:
    # Trigger when stat gain map converts stats (useful for Carly)
```

## Troubleshooting

### Common Issues

1. **Passive Not Triggering**
   - Check if passive ID matches between character and plugin
   - Verify trigger event is being fired in battle system
   - Ensure passive plugin is properly registered

2. **Effects Not Applying**
   - Verify `StatEffect` creation with correct stat names
   - Check effect duration (-1 for permanent, >0 for temporary)
   - Ensure `target.add_effect()` is called

3. **State Not Persisting**
   - Use `ClassVar` for cross-instance state
   - Verify entity ID consistency
   - Check for proper cleanup in `turn_end` triggers

### Debug Tools

```python
# Check active passives
print(f"Character passives: {character.passives}")

# Check active effects
print(f"Active effects: {[e.name for e in character._active_effects]}")

# Verify registry contents
registry = PassiveRegistry()
print(f"Registered passives: {list(registry._registry.keys())}")
```

## Contributing

When adding new passives:

1. Follow the standard plugin structure
2. Add comprehensive unit tests
3. Update this documentation
4. Link passive to appropriate character(s)
5. Test integration with battle system

For questions or issues, refer to the main development documentation in `.codex/`.