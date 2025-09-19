from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Callable
from typing import ClassVar
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyWindTempestGuard:
    """Lady Wind's Tempest Guard passive - evasive wind barriers and stacking gusts."""

    plugin_type = "passive"
    id = "lady_wind_tempest_guard"
    name = "Tempest Guard"
    trigger = "turn_start"
    max_stacks = 5
    stack_display = "pips"

    _gust_stacks: ClassVar[dict[int, int]] = {}
    _pending_crits: ClassVar[dict[int, set[int]]] = {}
    _crit_callbacks: ClassVar[dict[int, Callable[..., None]]] = {}
    _cleanup_callbacks: ClassVar[dict[int, Callable[..., None]]] = {}

    async def apply(self, target: "Stats") -> None:
        """Wrap Lady Wind in a baseline slipstream of protection."""
        entity_id = id(target)
        cls = self.__class__
        if entity_id not in cls._gust_stacks:
            cls._gust_stacks[entity_id] = 0

        if entity_id not in cls._pending_crits:
            cls._pending_crits[entity_id] = set()

        if entity_id not in cls._crit_callbacks:
            target_ref = ref(target)

            def _on_critical_hit(attacker, crit_target, *_args, **_kwargs) -> None:
                tracked = target_ref()
                if tracked is None:
                    BUS.unsubscribe("critical_hit", _on_critical_hit)
                    cls._crit_callbacks.pop(entity_id, None)
                    cleanup_cb = cls._cleanup_callbacks.pop(entity_id, None)
                    if cleanup_cb is not None:
                        BUS.unsubscribe("battle_end", cleanup_cb)
                    return

                if attacker is tracked and crit_target is not None:
                    crit_id = id(crit_target)
                    cls._pending_crits.setdefault(entity_id, set()).add(crit_id)

            BUS.subscribe("critical_hit", _on_critical_hit)
            cls._crit_callbacks[entity_id] = _on_critical_hit

            def _on_battle_end(*_args, **_kwargs) -> None:
                BUS.unsubscribe("critical_hit", _on_critical_hit)
                BUS.unsubscribe("battle_end", _on_battle_end)
                cls._crit_callbacks.pop(entity_id, None)
                cls._cleanup_callbacks.pop(entity_id, None)
                cls._gust_stacks.pop(entity_id, None)
                cls._pending_crits.pop(entity_id, None)

            BUS.subscribe("battle_end", _on_battle_end)
            cls._cleanup_callbacks[entity_id] = _on_battle_end

        baseline_barrier = StatEffect(
            name=f"{self.id}_baseline_barrier",
            stat_modifiers={
                "dodge_odds": 0.07,
                "mitigation": 0.12,
                "effect_resistance": 0.05,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(baseline_barrier)

        stacks = cls._gust_stacks[entity_id]
        if stacks > 0:
            self._apply_turn_gust(target, stacks)

    async def on_turn_start(self, target: "Stats", **_: object) -> None:
        """Spin up Tempest Guard gusts each round to add temporary evasion."""
        entity_id = id(target)
        cls = self.__class__
        existing = cls._gust_stacks.get(entity_id, 0)
        reduced = max(0, existing - 3)

        crit_targets = cls._pending_crits.setdefault(entity_id, set())
        gained = len(crit_targets)
        crit_targets.clear()

        stacks = min(self.max_stacks, reduced + gained)
        cls._gust_stacks[entity_id] = stacks
        if stacks > 0:
            self._apply_turn_gust(target, stacks)

    async def on_damage_taken(
        self,
        target: "Stats",
        _attacker: "Stats",
        damage: int,
        **_: object,
    ) -> None:
        """Convert a slice of incoming damage into restorative tailwinds."""
        if damage <= 0:
            return

        entity_id = id(target)
        stacks = self._gust_stacks.get(entity_id, 0)
        if stacks <= 0:
            return

        tailwind_heal = max(1, int(damage * 0.05 * stacks))
        try:
            await target.apply_healing(
                tailwind_heal,
                source_type="passive",
                source_name=self.id,
            )
        except Exception:
            # Healing is best-effort—if the battle context rejects it, continue.
            pass

        remaining = max(0, stacks - 1)
        self._gust_stacks[entity_id] = remaining

        gust_effect_name = f"{self.id}_turn_gust"
        if remaining > 0:
            self._apply_turn_gust(target, remaining)
        else:
            target.remove_effect_by_name(gust_effect_name)

    def _apply_turn_gust(self, target: "Stats", stacks: int) -> None:
        """Apply the turn-based gust bonus derived from accumulated stacks."""
        gust_effect_name = f"{self.id}_turn_gust"
        target.remove_effect_by_name(gust_effect_name)

        dodge_bonus = 0.03 + (stacks * 0.01)
        mitigation_bonus = 0.04 + (stacks * 0.015)
        speed_bonus = stacks * 6
        attack_bonus = max(1, int(target.atk * 0.01 * stacks))

        gust_effect = StatEffect(
            name=gust_effect_name,
            stat_modifiers={
                "dodge_odds": dodge_bonus,
                "mitigation": mitigation_bonus,
                "spd": speed_bonus,
                "atk": attack_bonus,
            },
            duration=1,
            source=self.id,
        )
        target.add_effect(gust_effect)

    @classmethod
    def get_gust_level(cls, target: "Stats") -> int:
        """Expose the current gust stack count for UI elements."""
        return cls._gust_stacks.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Starts battles wrapped in a slipstream granting +7% dodge, +12% mitigation, "
            "+5% effect resistance, and can hold up to five Tempest Guard stacks. Each "
            "turn, three stacks bleed away before she gains one for every foe she landed "
            "a critical hit on. Active stacks conjure gusts that add dodge, mitigation, "
            "speed, and attack for the round, while damage siphons 5% per stack back as "
            "healing and consumes a stack."
        )
