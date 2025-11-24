# Tier-Specific Passive System Implementation

## Overview

The tier-specific passive system allows foes to have different passive variants based on their rank (normal, glitched, boss, prime). This eliminates hardcoded rank checks in normal passives and provides a clean, extensible architecture for tier-specific behaviors.

## Architecture

### Passive Resolution Flow

1. **Character Definition**: Characters define base passive IDs in their `passives` list
   ```python
   passives = ["luna_lunar_reservoir"]
   ```

2. **Rank Assignment**: `FoeFactory.build_encounter()` assigns rank to foes
   ```python
   foe.rank = "glitched"  # or "boss", "prime", etc.
   ```

3. **Passive Resolution**: `apply_rank_passives()` maps base IDs to tier-specific IDs
   ```python
   luna_lunar_reservoir → luna_lunar_reservoir_glitched
   ```

4. **Plugin Loading**: `PassiveRegistry` loads the tier-specific passive class

### Key Functions

#### `resolve_passives_for_rank(base_passive_id: str, rank: str) -> list[str]`

Maps a base passive ID to tier-specific variants based on rank, **stacking all applicable tiers**.

**Stacking Behavior** (for mixed rank tags):
When a foe has multiple rank tags (e.g., "glitched prime boss"), the function returns **ALL matching tier variants** that exist. This allows tier effects to stack and combine:

- `"glitched prime boss"` → `["..._glitched", "..._prime", "..._boss"]` (all three stack)
- `"prime boss"` → `["..._prime", "..._boss"]` (both stack)
- `"glitched"` → `["..._glitched"]` (single tier)
- `"boss"` → `["..._boss"]` (single tier)
- `""` or `"normal"` or no matching tags → `["base_passive"]` (base only)

**Tier Check Order**:
1. Check for glitched variant (`{base_id}_glitched`)
2. Check for prime variant (`{base_id}_prime`)
3. Check for boss variant (`{base_id}_boss`)
4. If no tier variants exist, return base passive

The system is case-insensitive and handles edge cases gracefully:
- Empty rank strings fall back to base passive
- Unknown rank tags fall back to base passive
- Missing tier variants are skipped (partial stacking works)
- If NO tier variants exist, falls back to base passive

**Examples**:
```python
resolve_passives_for_rank("luna_lunar_reservoir", "glitched")
# → ["luna_lunar_reservoir_glitched"]

resolve_passives_for_rank("luna_lunar_reservoir", "glitched prime boss")
# → ["luna_lunar_reservoir_glitched", "luna_lunar_reservoir_prime", "luna_lunar_reservoir_boss"]
# All three tier effects stack!

resolve_passives_for_rank("luna_lunar_reservoir", "prime boss")
# → ["luna_lunar_reservoir_prime", "luna_lunar_reservoir_boss"]
# Both prime and boss effects stack

resolve_passives_for_rank("attack_up", "boss")
# → ["attack_up_boss"]

resolve_passives_for_rank("some_passive", "glitched")
# → ["some_passive"] (if glitched variant doesn't exist, returns base)

resolve_passives_for_rank("luna_lunar_reservoir", "")
# → ["luna_lunar_reservoir"] (empty rank)
```

#### `apply_rank_passives(foe: Any) -> None`

Transforms a foe's passive list in-place, resolving each base passive ID to its tier-specific variants.
**All matching tier variants are added (stacking behavior)**, so a foe with multiple tier tags will have multiple passive variants active simultaneously.

Called in `FoeFactory.build_encounter()` after rank is set but before the foe is returned.

**Example**:
```python
foe.passives = ["luna_lunar_reservoir"]
foe.rank = "glitched prime boss"
apply_rank_passives(foe)
# foe.passives = [
#     "luna_lunar_reservoir_glitched",  # 2x charge gains
#     "luna_lunar_reservoir_prime",     # 5x charge gains + healing
#     "luna_lunar_reservoir_boss"       # enhanced soft cap
# ]
# All three effects stack multiplicatively!
```

## Tier Implementation Patterns

### Simple Stat Modifiers

For passives that modify stats directly (attack_up, etc.):

- **Normal**: Base value (e.g., +5 attack)
- **Glitched**: 2x base (e.g., +10 attack)
- **Boss**: 3x base (e.g., +15 attack)
- **Prime**: 5x base (e.g., +25 attack)

**Implementation**:
```python
@dataclass
class AttackUpGlitched(AttackUp):
    plugin_type = "passive"
    id = "attack_up_glitched"
    name = "Glitched Attack Up"
    amount = 10  # 2x base 5
    
    @classmethod
    def get_description(cls) -> str:
        return f"[GLITCHED] Grants +{cls.amount} attack (doubled)."
```

### Complex State-Tracking Passives

For passives with accumulated state (Luna's Lunar Reservoir, Ixia's Tiny Titan):

**Glitched**:
- 2x charge/resource gains
- Maintains core mechanics
- More volatile/risky gameplay

**Boss**:
- Enhanced multipliers (1.5-2x)
- Reduced penalties
- Higher soft caps
- More forgiving gameplay

**Prime**:
- Extreme multipliers (2.5-5x)
- Added sustain (healing)
- Minimal penalties
- Pinnacle power level

**Implementation Example** (Luna):
```python
@dataclass
class LunaLunarReservoirGlitched(LunaLunarReservoir):
    plugin_type = "passive"
    id = "luna_lunar_reservoir_glitched"
    name = "Glitched Lunar Reservoir"
    
    @classmethod
    def _charge_multiplier(cls, charge_holder: "Stats") -> int:
        return 2  # Glitched always has 2x
    
    @classmethod
    def _sword_charge_amount(cls, owner: "Stats | None") -> int:
        return 8  # Base 4 * 2
```

## Implementation Status

### Completed (9/27 characters)
- ✅ Luna Midori (complex charge system)
- ✅ Ixia (complex vitality system)
- ✅ Attack Up (generic stat modifier)

### Remaining (17/27 characters)
- [ ] Ally Overload
- [ ] Becca Menagerie Bond
- [ ] Bubbles Bubble Burst
- [ ] Carly Guardian's Aegis
- [ ] Casno Phoenix Respite
- [ ] Graygray Counter Maestro
- [ ] Hilander Critical Ferment
- [ ] Kboshi Flux Cycle
- [ ] Lady Darkness Eclipsing Veil
- [ ] Lady Echo Resonant Static
- [ ] Lady Fire and Ice Duality Engine
- [ ] Lady Light Radiant Aegis
- [ ] Lady Lightning Stormsurge
- [ ] Lady of Fire Infernal Momentum
- [ ] Lady Storm Supercell
- [ ] Lady Wind Tempest Guard
- [ ] Mezzy Gluttonous Bulwark
- [ ] Mimic Player Copy
- [ ] Persona Ice Cryo Cycle
- [ ] Persona Light and Dark Duality
- [ ] Player Level Up Bonus
- [ ] Ryne Oracle of Balance
- [ ] Advanced Combat Synergy

### Special Cases
- **Mimic Player Copy**: May need special handling for copying tier passives
- **Player Level Up Bonus**: Player-specific, may not need tier variants
- **Advanced Combat Synergy**: Generic synergy passive

## Implementation Guidelines

### For Each Character Passive

1. **Read the normal passive** to understand its mechanics
2. **Identify key parameters** (damage, healing, stacks, multipliers, etc.)
3. **Apply tier multipliers**:
   - Glitched: 2x core effect
   - Boss: 3x core effect + reduced penalties
   - Prime: 5x core effect + added sustain
4. **Maintain mechanical identity** - don't change what makes the passive unique
5. **Update description** with tier prefix and explain changes
6. **Test** that the passive loads and registers correctly

### Code Structure

Each tier passive should:
- Define `plugin_type = "passive"`
- Set unique `id = "{base_id}_{tier}"`
- Set appropriate `name`
- Inherit or reimplement `trigger`, `max_stacks`, `stack_display`
- Override methods/attributes that change for the tier
- Provide tier-specific `get_description()`

### State Management Caveat

Passives with `ClassVar` state dictionaries (like `_charge_points`, `_vitality_bonuses`) share state across all instances of that class **and its subclasses**. This means:

- Tier variants that inherit from base classes share the class-level state
- This is generally fine because only one tier variant will be active per foe
- If issues arise, implement separate state dicts for each tier class

## Testing

The test suite in `tests/test_tier_passives.py` validates:

### Resolution Function Tests (13 tests)
1. ✅ Normal rank resolution
2. ✅ Individual tier resolution (glitched, boss, prime)
3. ✅ Two-tier stacking (glitched boss, prime boss, glitched prime)
4. ✅ All tiers combined (glitched prime boss) - **stacks all three variants**
5. ✅ Empty rank string handling
6. ✅ Unknown rank tag handling
7. ✅ Case-insensitive rank matching
8. ✅ Fallback when tier variant doesn't exist

### Transformation Function Tests (11 tests)
9. ✅ Apply passives for each tier (normal, glitched, boss, prime)
10. ✅ Multiple passives with mixed tier availability
11. ✅ All tier tags combined (glitched prime boss) - **stacks all variants**
12. ✅ Two-tier stacking (prime boss) - **stacks both variants**
13. ✅ Missing rank attribute handling
14. ✅ Empty passives list handling
15. ✅ Missing passives attribute handling
16. ✅ Passive registry contains all tier variants

**Total: 24 tests, all passing**

**Stacking Behavior Validated**:
- Single tier tags apply single tier passive
- Two-tier tags (e.g., "prime boss") apply BOTH tier passives (stacking)
- Three-tier tags (e.g., "glitched prime boss") apply ALL THREE tier passives (full stacking)

Add additional tests for:
- Character-specific tier passive behaviors
- State tracking across battle phases
- Tier-specific multipliers produce expected results
- Multiplicative stacking effects

## Future Enhancements

Potential improvements to the system:

1. ~~**Combined Tiers**: Handle "glitched prime boss" by stacking tier effects~~ ✅ **IMPLEMENTED**
2. **Tier Traits**: Share common tier behaviors (e.g., all glitched passives have instability)
3. **Dynamic Scaling**: Scale tier multipliers based on progression depth
4. **Tier-Specific Events**: New event triggers for tier-specific mechanics

## Related Files

### Core System
- `backend/autofighter/passives.py` - Resolution functions and registry
- `backend/autofighter/rooms/foe_factory.py` - Integration point
- `backend/tests/test_tier_passives.py` - Test suite

### Passive Implementations
- `backend/plugins/passives/normal/` - Base implementations
- `backend/plugins/passives/glitched/` - Glitched variants
- `backend/plugins/passives/boss/` - Boss variants
- `backend/plugins/passives/prime/` - Prime variants

### Task Files
- `.codex/tasks/wip/passives/glitched/b15b27b9-glitched-passives-implementation.md`
- `.codex/tasks/wip/passives/boss/30b7c731-boss-passives-implementation.md`
- `.codex/tasks/wip/passives/prime/1eade916-prime-passives-implementation.md`
