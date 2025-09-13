# Unified Summons System

The Midori AI AutoFighter now has a unified summons system that provides a consistent framework for creating and managing summons across characters, passives, cards, and relics.

## Architecture

### Core Components

#### `Summon` Class (`autofighter.summons.base`)
- Inherits from `Stats` for full integration with the game's stat system
- Supports configurable stat inheritance (default 50% of summoner's stats)
- Automatic damage type inheritance with 70% chance to match summoner's element
- Turn-based expiration system for temporary summons
- Unique ID generation based on summoner and summon type

#### `SummonManager` Class (`autofighter.summons.manager`)
- Centralized tracking and lifecycle management of all summons
- Event-driven cleanup (battle end, summoner defeat, turn expiration)
- Configurable summon limits per summoner
- Integration with party system for battle participation
  (summons fight alongside the party but are excluded from party snapshots
  and reported separately under `party_summons` to avoid duplicate listings)
- Thread-safe class-level tracking

### Key Features

#### Stat Inheritance
- Summons inherit stats from their summoner at a configurable multiplier
- Default 50% inheritance as specified in planning documents
- Supports all stat types: HP, ATK, DEF, crit rates, mitigation, etc.
- Base stats are properly set to ensure stat effects work correctly

#### Damage Type Logic
- 70% chance to inherit summoner's damage type
- 30% chance for random damage type
- Override support for specific damage types
- Fallback to Generic type if inheritance fails

#### Lifecycle Management
- Automatic registration and tracking when summons are created
- Battle event integration for cleanup
- Turn-based expiration for temporary summons
- Summoner defeat cleanup
- `SummonManager.reset_all()` runs at the start of each battle to remove any
  leftover summons from previous encounters

## Usage Examples

### Creating a Simple Summon

```python
from autofighter.summons.manager import SummonManager

# Create a summon with default settings (50% stats, random type, permanent)
summon = SummonManager.create_summon(
    summoner=character,
    summon_type="guardian", 
    source="guardian_shield_relic"
)

# Add to party for battle
party.members.append(summon)
```

### Creating a Temporary Summon

```python
# Create a temporary summon that lasts 3 turns
summon = SummonManager.create_summon(
    summoner=character,
    summon_type="phantom",
    source="phantom_ally_card",
    stat_multiplier=1.0,  # Full strength copy
    turns_remaining=3,
    max_summons=1
)
```

### Custom Damage Type

```python
from plugins.damage_types.lightning import Lightning

# Create summon with specific damage type
summon = SummonManager.create_summon(
    summoner=character,
    summon_type="electric_familiar",
    source="lightning_mastery",
    override_damage_type=Lightning()
)
```

## Current Implementations

### PhantomAlly Card (5-star)
- Creates full-strength temporary copy of random ally
- Duration: 1 turn
- Uses unified summons system with party integration
- Automatic cleanup on battle end

### BeccaMenagerieBond Passive
- Jellyfish summoning with HP cost (10% current HP)
- Different jellyfish types with appropriate damage types:
  - Electric → Lightning damage
  - Poison → Dark damage  
  - Healing → Light damage
  - Shielding → Ice damage
- Spirit stacking system when replacing summons
- One-turn cooldown between summons

## Event Integration

The summons system integrates with the existing event bus:

- `summon_created`: Fired when a new summon is created
- `summon_removed`: Fired when a summon is removed
- `battle_start`: Resets temporary tracking
- `battle_end`: Cleans up temporary summons
- `turn_start`: Processes turn expiration
- `entity_defeat`: Emitted automatically when an entity's HP reaches zero and
  again during battle cleanup; removes the summoner's active summons

## Testing

Comprehensive test suite covers:
- Basic summon creation and stat inheritance
- Manager functionality and limits
- Battle lifecycle events
- Turn-based expiration
- Damage type inheritance probability
- Integration with existing cards and passives
- Party integration for battles

All tests are located in `backend/tests/test_summons_system.py`.

## Future Expansion

The system is designed to support:
- Additional summon types and behaviors
- More complex summon interactions
- Summon-specific passives and effects
- Upgradeable summons
- Multiple summons per character (configurable limits)

## Migration Guide

For updating existing summon implementations:

1. Replace manual entity creation with `SummonManager.create_summon()`
2. Remove manual cleanup code (handled automatically)
3. Use the event system for summon-specific behaviors
4. Update tests to use the new summon identification methods

Example migration:
```python
# Old way
summon = copy.deepcopy(original)
summon.id = f"{original.id}_phantom"
party.members.append(summon)

# New way  
summon = SummonManager.create_summon(
    summoner=original,
    summon_type="phantom",
    source="phantom_ally"
)
party.members.append(summon)
```
