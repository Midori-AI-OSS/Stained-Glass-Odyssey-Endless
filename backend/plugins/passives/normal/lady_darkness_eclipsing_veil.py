from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Callable
from typing import ClassVar
from typing import Iterable
from typing import Mapping
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyDarknessEclipsingVeil:
    """Lady Darkness's Eclipsing Veil passive - DoT enhancement and siphoning."""
    plugin_type = "passive"
    id = "lady_darkness_eclipsing_veil"
    name = "Eclipsing Veil"
    trigger = "turn_start"  # Triggers at start of turn for DoT management
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of attack bonuses from debuff resistance
    _attack_bonuses: ClassVar[dict[int, int]] = {}
    _dot_callbacks: ClassVar[dict[int, Callable[..., object]]] = {}
    _resist_callbacks: ClassVar[dict[int, Callable[..., object]]] = {}
    _cleanup_callbacks: ClassVar[dict[int, Callable[..., object]]] = {}
    _party_cache: ClassVar[dict[int, frozenset[int]]] = {}

    async def apply(self, target: "Stats", **kwargs: object) -> None:
        """Apply Lady Darkness's DoT enhancement and siphoning mechanics."""
        entity_id = id(target)

        party_members = self._collect_party_members(kwargs.get("party"))
        party_ids = frozenset({id(member) for member in party_members} | {entity_id})
        self.__class__._party_cache[entity_id] = party_ids

        # Initialize attack bonus tracking if not present
        if entity_id not in self._attack_bonuses:
            self._attack_bonuses[entity_id] = 0

        # Extend DoT durations by one turn (would need DoT system integration)
        # For now, apply this as a passive effect that the DoT system can check
        dot_extension_effect = StatEffect(
            name=f"{self.id}_dot_extension",
            stat_modifiers={"dot_duration_bonus": 1},  # Extend DoTs by 1 turn
            duration=-1,  # Permanent passive effect
            source=self.id,
        )
        target.add_effect(dot_extension_effect)

        # Apply current attack bonus from previous debuff resistances
        if self._attack_bonuses[entity_id] > 0:
            attack_bonus_effect = StatEffect(
                name=self._resist_effect_name(entity_id),
                stat_modifiers={"atk": self._attack_bonuses[entity_id]},
                duration=-1,  # Permanent for rest of battle
                source=self.id,
            )
            target.add_effect(attack_bonus_effect)

        self._ensure_event_hooks(target)

    async def on_dot_tick(self, target: "Stats", dot_damage: int) -> None:
        """Siphon 1% of DoT damage as HoT when any DoT ticks on the battlefield."""
        # Siphon 1% of the DoT damage as healing
        siphoned_healing = max(1, int(dot_damage * 0.01))

        # Apply immediate healing using proper healing system
        await target.apply_healing(siphoned_healing)

    async def on_debuff_resist(self, target: "Stats") -> None:
        """Grant +5% attack when resisting a debuff."""
        entity_id = id(target)

        # Increase permanent attack bonus by 5%
        attack_increase = int(target.atk * 0.05)
        self._attack_bonuses[entity_id] += attack_increase
        total_attack_bonus = self._attack_bonuses[entity_id]

        # Apply the total bonus immediately so successive resists stack
        resist_bonus_effect = StatEffect(
            name=self._resist_effect_name(entity_id),
            stat_modifiers={"atk": total_attack_bonus},
            duration=-1,  # Permanent for rest of battle
            source=self.id,
        )
        target.add_effect(resist_bonus_effect)

    @classmethod
    def get_attack_bonus(cls, target: "Stats") -> int:
        """Get current attack bonus from debuff resistances."""
        return cls._attack_bonuses.get(id(target), 0)

    @classmethod
    def _resist_effect_name(cls, entity_id: int) -> str:
        return f"{cls.id}_resist_bonus_{entity_id}"

    @classmethod
    def get_description(cls) -> str:
        return (
            "Extends DoTs by one turn and siphons 1% of each DoT tick as healing. "
            "Resisting a debuff grants +5% attack, stacking indefinitely."
        )

    def _collect_party_members(self, value: object | None) -> list["Stats"]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return [member for member in value if member is not None]
        if hasattr(value, "members"):
            members = getattr(value, "members")
            if isinstance(members, Iterable):
                return [member for member in members if member is not None]
        return []

    def _ensure_event_hooks(self, target: "Stats") -> None:
        cls = self.__class__
        entity_id = id(target)

        if entity_id in cls._dot_callbacks:
            return

        target_ref = ref(target)

        async def _on_dot_tick(
            attacker: "Stats | None",
            dot_target: "Stats | None",
            amount: int | None,
            *_args: object,
        ) -> None:
            tracked = target_ref()
            if tracked is None:
                cls._unregister_entity(entity_id)
                return

            if amount is None or amount <= 0:
                return

            party_ids = cls._party_cache.get(entity_id)
            if not party_ids:
                return

            attacker_id = id(attacker) if attacker is not None else None
            target_id = id(dot_target) if dot_target is not None else None

            if attacker_id not in party_ids and target_id not in party_ids:
                return

            await self.on_dot_tick(tracked, int(amount))

        async def _on_effect_resisted(
            _effect_name: str | None,
            resisted_target: "Stats | None",
            _source: "Stats | None" = None,
            details: Mapping[str, object] | None = None,
        ) -> None:
            tracked = target_ref()
            if tracked is None:
                cls._unregister_entity(entity_id)
                return

            if resisted_target is not tracked:
                return

            effect_type = ""
            if details is not None:
                raw_type = details.get("effect_type")
                if isinstance(raw_type, str):
                    effect_type = raw_type.lower()

            if effect_type in {"hot", "buff"}:
                return

            await self.on_debuff_resist(tracked)

        def _teardown(*_args: object, **_kwargs: object) -> None:
            cls._unregister_entity(entity_id)

        BUS.subscribe("dot_tick", _on_dot_tick)
        BUS.subscribe("effect_resisted", _on_effect_resisted)
        BUS.subscribe("battle_end", _teardown)

        cls._dot_callbacks[entity_id] = _on_dot_tick
        cls._resist_callbacks[entity_id] = _on_effect_resisted
        cls._cleanup_callbacks[entity_id] = _teardown

    @classmethod
    def _unregister_entity(cls, entity_id: int) -> None:
        dot_cb = cls._dot_callbacks.pop(entity_id, None)
        if dot_cb is not None:
            BUS.unsubscribe("dot_tick", dot_cb)

        resist_cb = cls._resist_callbacks.pop(entity_id, None)
        if resist_cb is not None:
            BUS.unsubscribe("effect_resisted", resist_cb)

        cleanup_cb = cls._cleanup_callbacks.pop(entity_id, None)
        if cleanup_cb is not None:
            BUS.unsubscribe("battle_end", cleanup_cb)

        cls._party_cache.pop(entity_id, None)
        cls._attack_bonuses.pop(entity_id, None)

    async def on_defeat(self, target: "Stats") -> None:
        self.__class__._unregister_entity(id(target))
