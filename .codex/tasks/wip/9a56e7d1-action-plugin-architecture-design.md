# Task: Action Plugin Architecture Design

**Status:** WIP  
**Priority:** High  
**Category:** Architecture/Design  
**Goal File:** `.codex/tasks/wip/GOAL-action-plugin-system.md`  
**Execution Order:** **#2 - DO THIS SECOND**

## Recommended Task Execution Order

This is the **second task** in the action plugin system project:

1. Battle Logic Research & Documentation (fd656d56) - **Complete this first**
2. **✓ THIS TASK** - Architecture Design (9a56e7d1)
3. Plugin Loader Implementation (4afe1e97)
4. Normal Attack Extraction (b60f5a58)

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

`ActionBase` is the single entry point for every plugin that the battle turn loop will execute. To keep the loader simple, the class owns all metadata as dataclass fields, declares `plugin_type = "action"`, and surfaces explicit helper policies for targeting, costs, cooldowns, and animation pacing. Concrete subclasses can extend or override the policies, but the turn loop never needs to special-case an action.

#### Metadata contracts

Every plugin must set the following fields when instantiating the base class (defaults can be provided by subclasses so the loader can simply construct them without arguments):

| Field | Purpose |
| --- | --- |
| `id: str` | Stable slug used by `ActionRegistry` and save files. Namespacing is encouraged (`normal.basic_attack`). |
| `name: str` / `description: str` | UX copy surfaced in menus, logs, and the combat HUD. |
| `action_type: ActionType` | Enum of `normal`, `special`, `ultimate`, `passive`, or `item`. Determines where the action is surfaced and which UI counters (e.g., ultimate charge) gate it. |
| `tags: tuple[str, ...]` | Optional metadata for UI filters and shared cooldown pools. |
| `targeting: TargetingRules` | Dataclass describing the valid side (allies/enemies/any), scope (`single`, `multi`, `all`, `self`), `max_targets`, whether KO’d or summons are valid, and if the actor counts as a valid target. |
| `cost: ActionCostBreakdown` | Dataclass listing resource deductions (action points, ultimate charge, HP %, inventory items, etc.). |
| `cooldown_turns: int` | Turn count enforced by `ActionRegistry`. A value of `0` means no cooldown. |
| `animation: ActionAnimationPlan` | Optional name + timing data so `autofighter/rooms/battle/pacing.py` can compute `pace_per_target` and `impact_pause`. |

The design avoids per-type base classes: shared logic is centralized in `ActionBase`, while unique flows (e.g., passives) override hooks such as `_can_execute` or `prepare_targets`. Actions that retarget mid-execution call `self.targeting.validate()` after each stage to ensure they stay within their policies.

#### Method reference

```python
@dataclass(kw_only=True, slots=True)
class ActionBase(ABC):
    plugin_type: ClassVar[str] = "action"
    id: str
    name: str
    description: str
    action_type: ActionType = ActionType.NORMAL
    tags: tuple[str, ...] = ()
    targeting: TargetingRules = field(default_factory=TargetingRules)
    cost: ActionCostBreakdown = field(default_factory=ActionCostBreakdown)
    cooldown_turns: int = 0
    animation: ActionAnimationPlan = field(default_factory=ActionAnimationPlan)

    async def can_execute(
        self,
        actor: Stats,
        targets: Sequence[Stats],
        context: BattleContext,
    ) -> bool:
        """Centralized gating: checks cooldowns, resources, and targeting before delegating to subclasses."""

    async def run(
        self,
        actor: Stats,
        targets: Sequence[Stats],
        context: BattleContext,
    ) -> ActionResult:
        """Calls :meth:`can_execute`, deducts costs, starts cooldowns in :class:`ActionRegistry`, and then awaits :meth:`execute`."""

    @abstractmethod
    async def execute(
        self,
        actor: Stats,
        targets: Sequence[Stats],
        context: BattleContext,
    ) -> ActionResult:
        """Apply damage/healing/effects and return a populated :class:`ActionResult`."""

    def get_valid_targets(
        self,
        actor: Stats,
        allies: Sequence[Stats],
        enemies: Sequence[Stats],
    ) -> list[Stats]:
        """Delegates to :class:`TargetingRules` to filter legal candidates."""

    async def _can_execute(
        self,
        actor: Stats,
        targets: Sequence[Stats],
        context: BattleContext,
    ) -> bool:
        """Optional subclass hook for extra gating (e.g., combo prerequisites)."""
```

#### Policy enforcement

- **Targeting**: `TargetingRules.validate()` owns the basic filters (alive-only, summons allowed, friendly/enemy restrictions) and clamps `max_targets`. The base class only considers an action runnable when `validate()` returns true. If a subclass wants to retarget, it calls `TargetingRules.filter_targets()` again with the current ally/enemy lists pulled from `BattleContext`.
- **Cost**: `ActionCostBreakdown.can_pay()` inspects the actor’s stats (`action_points`, `ultimate_charge`, custom attributes) and optional `BattleContext.spend_resource()` helpers for battle-specific pools. `ActionBase.run()` refuses to execute if costs fail and calls `ActionCostBreakdown.apply()` after `execute()` succeeds so the turn loop never forgets to deduct resources.
- **Cooldown**: `ActionRegistry.is_available()` enforces shared cooldown state (per actor + optional `tags`). `ActionBase.run()` invokes `ActionRegistry.start_cooldown()` when `cooldown_turns > 0`, and `ActionRegistry.advance_cooldowns()` is called from the turn loop after every phase so the counters tick down in sync with `turn_end.finish_turn()`.

### 2. Action Result Structure

Every action returns a single `ActionResult` dataclass. The base turn loop logs the messages, updates pacing, and forwards damage/heal numbers to the HUD before asking the effect system to resolve aftermath ticks. The canonical structure is:

```python
@dataclass(slots=True)
class ActionResult:
    success: bool
    damage_dealt: dict[Stats, int] = field(default_factory=dict)
    healing_done: dict[Stats, int] = field(default_factory=dict)
    shields_added: dict[Stats, int] = field(default_factory=dict)
    effects_applied: list[tuple[Stats, str]] = field(default_factory=list)
    effects_removed: list[tuple[Stats, str]] = field(default_factory=list)
    resources_consumed: dict[str, int] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    animations: list[AnimationTrigger] = field(default_factory=list)
    extra_turns_granted: list[Stats] = field(default_factory=list)
    summons_created: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

- `AnimationTrigger` is a typed dict containing `name`, `duration`, and `per_target` overrides so `autofighter/rooms/battle/pacing.py` can schedule `compute_multi_hit_timing()`.
- `resources_consumed` mirrors `ActionCostBreakdown` so the UI can animate resource drains.
- `metadata` captures action-specific payloads (e.g., the final crit chance) for battle logs and audit telemetry.

### 3. Battle Context Object

`BattleContext` is created by `backend/autofighter/rooms/battle/turn_loop/initialization.py` and threaded through all phases. The plugin architecture keeps it lightweight but opinionated so actions always use the same helpers as the handwritten system.

```python
@dataclass(slots=True)
class BattleContext:
    turn: int
    run_id: str
    phase: Literal["player", "foe"]
    actor: Stats
    allies: Sequence[Stats]
    enemies: Sequence[Stats]
    action_registry: ActionRegistry
    passive_registry: PassiveRegistry
    effect_managers: dict[str, EffectManager]
    summon_manager: SummonManager | None
    event_bus: EventBus
    enrage_state: EnrageState
    visual_queue: Any
    damage_router: DamageRouter

    def effect_manager_for(self, target: Stats) -> EffectManager:
        ...

    async def apply_damage(
        self,
        attacker: Stats,
        target: Stats,
        amount: float,
        *,
        damage_type: DamageTypeBase | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        ...

    async def apply_healing(
        self,
        healer: Stats,
        target: Stats,
        amount: float,
        *,
        overheal_allowed: bool = False,
    ) -> int:
        ...

    def spend_resource(self, actor: Stats, resource: str, amount: int) -> None:
        ...

    async def emit_action_event(self, event: str, *args, **kwargs) -> None:
        ...

    def allies_of(self, actor: Stats) -> Sequence[Stats]:
        ...

    def enemies_of(self, actor: Stats) -> Sequence[Stats]:
        ...
```

- `damage_router` encapsulates the helpers already used in `autofighter/rooms/battle/resolution.py` so plugins cannot skip mitigation, enrage checks, or passive triggers.
- The context caches `effect_managers` keyed by stat IDs so actions can apply or remove effects without re-instantiating `EffectManager`.
- `SummonManager` is optional because some tests spawn contexts without the subsystem; actions must guard before calling it.

### 4. Action Registry

`ActionRegistry` tracks the discovered plugin classes, instantiates them for the turn loop, and enforces cooldown bookkeeping. The API mirrors the loader workflow so the follow-up “Plugin Loader Implementation” task can plug it in immediately.

```python
class ActionRegistry:
    def register_action(self, action_class: type[ActionBase]) -> None:
        """Validates metadata, stores the class by `action_class.id`, and indexes it under `action_class.action_type`."""

    def register_character_actions(
        self,
        character_id: str,
        action_ids: Sequence[str],
    ) -> None:
        """Defines the action loadout for a specific `Stats.id`."""

    def instantiate(self, action_id: str) -> ActionBase:
        """Returns a new plugin instance using the subclass defaults (no kwargs required)."""

    def get_actions_by_type(self, action_type: ActionType | str) -> list[type[ActionBase]]:
        ...

    def get_character_actions(self, character_id: str) -> list[type[ActionBase]]:
        ...

    def is_available(self, actor: Stats, action: ActionBase) -> bool:
        """Checks the actor’s cooldown map and optional shared cooldown tags."""

    def start_cooldown(self, actor: Stats, action: ActionBase) -> None:
        ...

    def advance_cooldowns(self) -> None:
        """Called from `turn_end.finish_turn()` to decrement all timers by one turn."""

    def reset_actor(self, actor: Stats) -> None:
        ...
```

- Cooldowns are stored as `Dict[str, Dict[str, int]]` mapping `actor_id -> action_id -> turns_remaining`. Actions that share a cooldown tag (e.g., two variants of “Normal Attack”) add the tag to `ActionBase.tags`; the registry copies the highest `cooldown_turns` value for every action with the same tag when `start_cooldown()` fires.
- The registry is battle-scoped. `initialization.py` creates one per battle and seeds it with the plugin loader output and the party/foe loadouts. No global state leaks between encounters.

### 5. Integration Points

- **Damage types** (`backend/plugins/damage_types/_base.py`): actions MUST call `target.damage_type.on_action()` before applying damage to give the defender a chance to veto or modify the attack. The actual damage numbers flow through `BattleContext.apply_damage()` which pipes the payload to `DamageTypeBase.on_damage`, `DamageTypeBase.on_damage_taken`, and the event bus. When actions override the damage type (e.g., elemental infusions) they must pass the override into `apply_damage()` so mitigation checks stay coherent.
- **Effect manager** (`backend/autofighter/effects.py`): status applications and removals run through `context.effect_manager_for(target)` which returns the canonical `EffectManager`. Plugins should never mutate `Stats.mods` directly; they call `effect_manager.apply_effect()` / `remove_effect()` and log the resulting IDs inside `ActionResult.effects_applied`.
- **Event bus emissions** (`backend/plugins/event_bus.py`): `BattleContext.emit_action_event()` wraps `BUS.emit_async` / `emit_batched_async`. Actions emit at least `"action_started"`, `"hit_landed"`, `"damage_dealt"`, `"heal_received"`, and `"action_completed"` so downstream analytics and VFX keep working. High-frequency events must use batched emissions to respect the pacing guardrails defined in the bus (`_SOFT_YIELD_THRESHOLD`).
- **Turn loop pacing** (`backend/autofighter/rooms/battle/turn_loop/*.py` + `autofighter/rooms/battle/pacing.py`): `ActionResult.animations` feeds the pacing helpers (`compute_multi_hit_timing`, `pace_per_target`, `impact_pause`) invoked from `player_turn.prepare_action_attack_metadata()` and `turn_end.finish_turn()`. Plugins should never sleep directly; they hand the timing to the turn loop which already uses `_pace`, `pace_sleep`, and `_EXTRA_TURNS` for consistent behavior.
- **Summon handling** (`backend/autofighter/summons/manager.py`): Actions that spawn or recycle summons request slots through `context.summon_manager`. The manager enforces slot capacity, replacement rules, and event emissions (`summon_created`, `entity_defeat`). Plugins record the resulting summon IDs inside `ActionResult.summons_created` so `autofighter/rooms/battle/turns.py` can update overlays.
- **Passive registry triggers** (`backend/autofighter/passives.py`): After every successful execution, `ActionBase.run()` tells `BattleContext.passive_registry` to fire `action_taken`, `damage_dealt`, or `heal_done` as appropriate. Plugins never import passives directly. Instead they surface enough metadata inside `ActionResult.metadata` for `PassiveRegistry.trigger()` to understand context (actor, targets, damage numbers). The registry already yields control using `pace_sleep`, so actions do not need extra throttling.
- **Turn loop selection** (`backend/autofighter/rooms/battle/turn_loop/player_turn.py` and `foe_turn.py`): `execute_player_phase()` and `execute_foe_phase()` ask `ActionRegistry` which actions are available for the current actor, call `ActionBase.run()` with the selected targets, and then push the result to `turn_end.finish_turn()` for bookkeeping. `cleanup.py` and `turns.py` continue to handle KO sweeps, enrage ticks, and ultimate charge updates based on the returned `ActionResult`.

### 6. Migration Strategy

1. **Phase 1** *(this task)*: land the shared dataclasses, registry, and skeleton plugin modules without wiring them into the turn loop. Ship doc + stubs so loader work can begin immediately.
2. **Phase 2** *(task 4afe1e97)*: update `PluginLoader` to call `ActionRegistry.register_action()` for every `plugin_type="action"` class under `backend/plugins/actions/`. Provide a guard that fails fast when metadata is missing.
3. **Phase 3** *(task b60f5a58)*: move the existing normal attack logic in `autofighter/rooms/battle/turn_loop/player_turn.py` into `normal/basic_attack.py`, keeping the hardcoded path behind a feature flag. The turn loop should call `ActionRegistry.instantiate("normal.basic_attack")` and run it alongside the legacy branch for comparison.
4. **Phase 4**: convert character abilities (ultimates, specials, items) one at a time. Each migration should update `.codex/implementation/action-plugin-system.md` and delete the old inline code once parity tests pass.
5. **Phase 5**: let passives that currently fire ad-hoc actions migrate to the plugin system by instantiating actions directly from `PassiveRegistry.trigger()`.

### 7. File Structure

```
backend/plugins/actions/
├── __init__.py                  # Re-export ActionBase helpers for consumers
├── _base.py                     # ActionBase + policy dataclasses
├── context.py                   # BattleContext shim used by plugins
├── registry.py                  # ActionRegistry, cooldown helpers, character loadouts
├── result.py                    # ActionResult + animation payloads
├── normal/
│   ├── __init__.py              # Keeps package discovery simple
│   └── basic_attack.py          # First concrete plugin (logic implemented in follow-up task)
└── ... (future folders: special/, ultimate/, passive/)
```

- Each module contains a descriptive docstring explaining how plugin authors should interact with it.
- `PluginLoader.discover()` already inspects `backend/plugins/**`. Once the loader task points it at `backend/plugins/actions`, every class with `plugin_type = "action"` will be registered automatically.
- Plugins must rely on the exported base classes to guarantee consistent metadata. Any helper dataclasses (e.g., `TargetingRules`) live in `_base.py` to avoid circular imports.

### 8. Open Questions & Follow-ups

1. **Cooldown persistence**: the current design tracks cooldowns per battle. If the UX needs cooldowns to persist between rooms (e.g., dungeon floors), we must store the map on the `Stats` object or the save file.
2. **Animation helpers**: we still rely on the battle pacing module to interpret animation payloads. Future work should add helpers (e.g., `ActionAnimationPlan.multi_hit()`) so plugin authors do not reach into `autofighter/rooms/battle/pacing.py` directly.
3. **Ultimate gating**: the turn loop currently flips `stats.ultimate_ready`. We need a follow-up task to formalize how `ActionCostBreakdown` spends `ultimate_charge` so plugins cannot bypass the readiness flag.
4. **Snapshot integration**: `autofighter/rooms/battle/snapshots.py` needs to understand plugin actions for battle logs. Capture requirements should be documented once the loader task wires everything up.
5. **Visual queue contract**: the `visual_queue` placeholder in `BattleContext` still maps to the existing queue object. Later work should define a typed helper so plugins can schedule camera pans or screen shakes without guessing at queue semantics.

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
