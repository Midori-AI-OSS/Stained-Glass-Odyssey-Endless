# Action Plugin Migration Roadmap

## Status Summary (Updated 2025-11-28)

### Completed Migrations ✅
- **Basic Attack**: `BasicAttackAction` in `backend/plugins/actions/normal/basic_attack.py`
- **All Ultimate Actions**: Now routed through action plugins (see `backend/plugins/actions/ultimate/`)
  - ✅ `LightUltimate` (`ultimate/light_ultimate.py`)
  - ✅ `DarkUltimate` (`ultimate/dark_ultimate.py`)
  - ✅ `WindUltimate` (`ultimate/wind_ultimate.py`)
  - ✅ `FireUltimate` (`ultimate/fire_ultimate.py`)
  - ✅ `IceUltimate` (`ultimate/ice_ultimate.py`)
  - ✅ `LightningUltimate` (`ultimate/lightning_ultimate.py`)
  - ✅ `GenericUltimate` (`ultimate/generic_ultimate.py`)
- **Character Special Abilities** (5 implemented):
  - ✅ `AllyOverloadCascade` (`special/ally_overload_cascade.py`)
  - ✅ `BeccaMenagerieConvergence` (`special/becca_menagerie_convergence.py`)
  - ✅ `CarlyGuardianBarrier` (`special/carly_guardian_barrier.py`)
  - ✅ `GraygrayCounterOpus` (`special/graygray_counter_opus.py`)
  - ✅ `IxiaLightningBurst` (`special/ixia_lightning_burst.py`)

### Remaining Work
- **On-Action Behaviors** (3 remaining): Light healing, Dark drain, Wind spread - still embedded in damage type files
- **Summon Creation Actions** (2 remaining): Luna's sword summoning, Phantom Ally card
- **Additional Character Abilities**: Most characters still have abilities embedded in their class files

## Executive Summary
- Originally identified 12 combat actions that lived outside `ActionBase`/`ActionRegistry`
- **Progress**: 14 actions now migrated (1 basic attack, 7 ultimates, 5 special abilities, 1 turn loop integration)
- **Remaining**: 5 actions still need migration (3 on-action behaviors, 2 summon-creation flows)
- The turn loop now routes normal attacks and ultimates through the action registry
- Damage type files still contain wrapper methods for ultimates and on-action behaviors

## Detailed Findings

### 1. Combat Actions - COMPLETED ✅

**Ultimate Actions - All Migrated:**

All seven damage-type ultimates are now implemented as action plugins and routed through `ActionRegistry.instantiate_ultimate()`. The damage type files (`backend/plugins/damage_types/*.py`) contain thin wrapper methods that delegate to the action plugins.

| Ultimate | Plugin Location | Status |
|----------|-----------------|--------|
| Light Ultimate | `plugins/actions/ultimate/light_ultimate.py` | ✅ Complete |
| Dark Ultimate | `plugins/actions/ultimate/dark_ultimate.py` | ✅ Complete |
| Wind Ultimate | `plugins/actions/ultimate/wind_ultimate.py` | ✅ Complete |
| Fire Ultimate | `plugins/actions/ultimate/fire_ultimate.py` | ✅ Complete |
| Ice Ultimate | `plugins/actions/ultimate/ice_ultimate.py` | ✅ Complete |
| Lightning Ultimate | `plugins/actions/ultimate/lightning_ultimate.py` | ✅ Complete |
| Generic Ultimate | `plugins/actions/ultimate/generic_ultimate.py` | ✅ Complete |

### 2. Special Abilities - PARTIALLY COMPLETE

**Implemented (5 characters):**
| Ability | Character | Plugin Location |
|---------|-----------|-----------------|
| Overload Cascade | Ally | `plugins/actions/special/ally_overload_cascade.py` |
| Menagerie Convergence | Becca | `plugins/actions/special/becca_menagerie_convergence.py` |
| Guardian Barrier | Carly | `plugins/actions/special/carly_guardian_barrier.py` |
| Counter Opus | Graygray | `plugins/actions/special/graygray_counter_opus.py` |
| Lightning Burst | Ixia | `plugins/actions/special/ixia_lightning_burst.py` |

**Not Yet Migrated (Characters with embedded abilities):**
- **Luna**: Sword summoning via `_LunaSwordCoordinator` in `plugins/characters/luna.py`
- **Other characters**: May have abilities in their class files that should be extracted

### 3. On-Action Behaviors - NOT YET MIGRATED

These damage-type-specific behaviors are still embedded in the damage type files:

- **Light `on_action` healing/HoT** – `backend/plugins/damage_types/light.py` (method: `on_action`)
  - Category: `ActionType.SPECIAL`
  - Behavior: Heals allies under 25% HP, adds HoTs to all allies
  - Dependencies: `EffectManager`, `damage_effects.create_hot`, `pace_per_target`
  - Priority: Medium - could be extracted as a standalone action plugin

- **Dark `on_action` drain-to-bonus** – `backend/plugins/damage_types/dark.py` (method: `on_action`)
  - Category: `ActionType.SPECIAL`
  - Behavior: Drains 10% HP from allies, provides damage bonus for next attack
  - Dependencies: `Stats.apply_cost_damage`, BUS subscription cleanup
  - Priority: Medium - complex state management makes this non-trivial

- **Wind spread (AoE normal attack)** – `backend/plugins/damage_types/wind.py` (`WindTurnSpread` class) + `player_turn.py` (`_handle_wind_spread` function)
  - Category: `ActionType.SPECIAL` with spread helper (`WindTurnSpread`)
  - Behavior: Normal attacks spread to additional targets with scaled damage
  - Dependencies: `_collect_wind_spread_targets`, `_handle_wind_spread`
  - Priority: Low - already well-integrated with turn loop via `get_turn_spread()`

### 4. Summon Creation Actions - NOT YET MIGRATED

- **Luna sword summon creation** – `backend/plugins/characters/luna.py` (`_LunaSwordCoordinator` class)
  - Category: `ActionType.SPECIAL`
  - Complexity: High (creates Summon instances, registers with coordinator, syncs action counts)
  - Dependencies: `SummonManager`, `_LunaSwordCoordinator`, passive registry
  - Priority: Medium - refactoring would separate summon logic from character class

- **Phantom Ally card** – `backend/plugins/cards/phantom_ally.py`
  - Category: `ActionType.ITEM`
  - Complexity: High (card effect that spawns permanent summon)
  - Dependencies: `SummonManager.create_summon`, card effect lifecycle
  - Priority: Low - cards have their own plugin system

### 5. Auxiliary Systems / Exclusions (Unchanged)
- **Summon manager & rooms**
  - The shop (`backend/autofighter/rooms/shop.py`) and chat (`backend/autofighter/rooms/chat.py`) resolve UI interactions and should stay outside the action plugin scope.
  - Summoning actions triggered by cards or characters should run through plugins only while the underlying room logic keeps its current responsibilities.
- **Effect/passive systems**
  - `EffectManager` + `StatEffect` (`backend/autofighter/effects.py`) currently own buff/debuff/DoT application; migrating actions should continue to use these helpers.
  - Passives such as `Ally Overload` and `Becca Menagerie Bond` manage charge counters, buff timing, and summon cleanup—these should remain passive plugins while relying on action plugins to emit the events they listen to.

## Migration Recommendations (Updated)

### Phase 1 – Complete ✅
**Basic Attack and Turn Loop Integration**
- `BasicAttackAction` is now the primary attack execution path
- Turn loop routes attacks through `ActionRegistry.instantiate("normal.basic_attack")`
- Fallback logic preserved for error handling

### Phase 2 – Complete ✅
**Ultimate Actions Migration**
- All seven damage-type ultimates now have dedicated action plugins
- Damage type files contain thin wrapper methods that delegate to action plugins
- Turn loop uses `ActionRegistry.instantiate_ultimate()` for ultimate execution

### Phase 3 – Complete ✅
**Initial Character Special Abilities**
- Five character-specific special abilities implemented
- `SpecialAbilityBase` provides shared behavior for character-restricted abilities
- Turn loop attempts special abilities via `_try_special_ability()` before basic attacks

### Phase 4 – Remaining Work

**4a. Remaining Character Special Abilities (Medium Priority)**
Audit remaining character files for abilities that should be extracted:
- Luna's sword summoning and coordination
- Other character-specific combat behaviors

**4b. On-Action Behaviors (Low Priority)**
The damage-type `on_action` methods could optionally be converted to action plugins:
- Light healing/HoT application
- Dark drain-to-bonus mechanic
- These work well as damage-type hooks; migration is optional for code organization

**4c. Summon-Aware Actions (Low Priority)**
For characters with summon mechanics:
- Wire `SummonManager` into `BattleContext`
- Create summon-spawning action plugins for Luna and similar characters
- Enable `Phantom Ally` card to use action plugin infrastructure

## Technical Considerations (Updated)

### Current Architecture
- **Action Infrastructure**: `ActionBase`/`ActionRegistry` handle cost/cooldown/targeting logic (`backend/plugins/actions/_base.py`, `registry.py`)
- **Ultimate Base**: `UltimateActionBase` extends `ActionBase` with ultimate-specific charge consumption and validation
- **Special Ability Base**: `SpecialAbilityBase` extends `ActionBase` with character-ID validation for character-restricted abilities
- **Battle Context**: Created via `create_battle_context()` in turn loop initialization; provides access to allies, enemies, and effect managers

### Integration Points
- **Turn Loop**: `player_turn.py` and `foe_turn.py` now use `ActionRegistry` for basic attacks and ultimates
- **Character Special Abilities**: Turn loop checks for available special abilities via `_try_special_ability()` before falling back to basic attack
- **Damage Type Wrappers**: Ultimate methods in damage type files delegate to action plugins via `run_ultimate_action()` utility

### Fallback Safety
Both `player_turn.py` and `foe_turn.py` include fallback logic within the normal attack execution (in `_run_player_turn_iteration` and `_run_foe_turn_iteration` respectively) that still calls `Stats.apply_damage` directly if an action plugin fails. This ensures battles don't abort due to plugin errors.

### Event Coordination
Action plugins must continue to emit `BUS` events (`action_used`, `hit_landed`, `damage_dealt`, etc.) because:
- Passives listen for these events to trigger effects
- UI updates depend on event emissions
- Damage tracking and logging use event data

### Testing Strategy
- Unit tests for action plugins: `backend/tests/test_action_*.py`
- Integration tests: `backend/tests/test_turn_loop_*.py`
- Regression tests ensure existing battle behavior is preserved

## References
- Action plugin system: `.codex/implementation/action-plugin-system.md`
- Battle room: `.codex/implementation/battle-room.md`
- Stats and effects: `.codex/implementation/stats-and-effects.md`
- Tier passive system: `.codex/implementation/tier-passive-system.md`
