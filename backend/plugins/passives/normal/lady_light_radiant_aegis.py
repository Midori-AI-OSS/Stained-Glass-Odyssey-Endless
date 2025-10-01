from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Callable
from typing import ClassVar
from typing import Mapping
from typing import Optional
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from autofighter.stats import get_enrage_percent

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyLightRadiantAegis:
    """Lady Light's Radiant Aegis passive - HoT enhancements with shields and cleansing."""
    plugin_type = "passive"
    id = "lady_light_radiant_aegis"
    name = "Radiant Aegis"
    trigger = "action_taken"  # Triggers when Lady Light acts (heals)
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of attack bonuses from cleansing DoTs
    _attack_bonuses: ClassVar[dict[int, int]] = {}
    _effect_callbacks: ClassVar[dict[int, Callable[..., object]]] = {}
    _cleanse_callbacks: ClassVar[dict[int, Callable[..., object]]] = {}
    _cleanup_callbacks: ClassVar[dict[int, Callable[..., object]]] = {}

    async def apply(self, target: "Stats") -> None:
        """Apply Lady Light's HoT enhancement mechanics."""
        entity_id = id(target)

        # Initialize attack bonus tracking if not present
        if entity_id not in self._attack_bonuses:
            self._attack_bonuses[entity_id] = 0

        # Apply current attack bonus from previous cleanses
        if self._attack_bonuses[entity_id] > 0:
            attack_bonus_effect = StatEffect(
                name=f"{self.id}_cleanse_bonus",
                stat_modifiers={"atk": self._attack_bonuses[entity_id]},
                duration=-1,  # Permanent for rest of battle
                source=self.id,
            )
            target.add_effect(attack_bonus_effect)

        cls = self.__class__
        if entity_id not in cls._effect_callbacks:
            target_ref = ref(target)

            async def _on_effect_applied(
                effect_name: str,
                entity: Optional["Stats"],
                details: Mapping[str, object] | None = None,
            ) -> None:
                tracked = target_ref()
                if tracked is None:
                    teardown()
                    return

                if (
                    entity is None
                    or details is None
                    or details.get("effect_type") != "hot"
                ):
                    return

                effect_id = details.get("effect_id")
                if effect_id is None:
                    return

                mgr = getattr(entity, "effect_manager", None)
                if mgr is None:
                    return

                for hot in getattr(mgr, "hots", []):
                    if getattr(hot, "id", None) != effect_id:
                        continue
                    if getattr(hot, "source", None) is not tracked:
                        continue
                    if getattr(hot, "_radiant_aegis_registered", False):
                        continue

                    hot_amount = self._calculate_hot_amount(
                        tracked,
                        entity,
                        hot,
                        details,
                    )
                    hot._radiant_aegis_registered = True  # type: ignore[attr-defined]
                    if hot_amount <= 0:
                        continue
                    await self.on_hot_applied(tracked, entity, hot_amount)
                    break

            async def _on_dot_cleansed(
                cleanser: Optional["Stats"],
                cleansed_ally: Optional["Stats"],
                _dot_id: str | None = None,
                _metadata: Mapping[str, object] | None = None,
            ) -> None:
                tracked = target_ref()
                if tracked is None:
                    teardown()
                    return

                if cleanser is not tracked or cleansed_ally is None:
                    return

                await self.on_dot_cleanse(tracked, cleansed_ally)

            def teardown(*_args: object, **_kwargs: object) -> None:
                BUS.unsubscribe("effect_applied", _on_effect_applied)
                BUS.unsubscribe("dot_cleansed", _on_dot_cleansed)
                BUS.unsubscribe("battle_end", teardown)
                cls._effect_callbacks.pop(entity_id, None)
                cls._cleanse_callbacks.pop(entity_id, None)
                cls._cleanup_callbacks.pop(entity_id, None)

            BUS.subscribe("effect_applied", _on_effect_applied)
            BUS.subscribe("dot_cleansed", _on_dot_cleansed)
            BUS.subscribe("battle_end", teardown)

            cls._effect_callbacks[entity_id] = _on_effect_applied
            cls._cleanse_callbacks[entity_id] = _on_dot_cleansed
            cls._cleanup_callbacks[entity_id] = teardown

    async def on_hot_applied(self, target: "Stats", healed_ally: "Stats", hot_amount: int) -> None:
        """Enhance HoTs with shields and effect resistance."""
        # Grant one-turn shield to the healed ally
        shield_amount = int(hot_amount * 0.5)  # Shield equal to 50% of HoT amount

        if shield_amount > 0:
            if not healed_ally.overheal_enabled:
                healed_ally.enable_overheal()
            healed_ally.shields += shield_amount

        # Grant +5% effect resistance for one turn
        resistance_effect = StatEffect(
            name=f"{self.id}_hot_resistance",
            stat_modifiers={"effect_resistance": 0.05},  # 5% resistance to negative effects
            duration=1,  # One turn
            source=self.id,
        )
        healed_ally.add_effect(resistance_effect)

    async def on_dot_cleanse(self, target: "Stats", cleansed_ally: "Stats") -> None:
        """Grant bonuses when cleansing a DoT."""
        entity_id = id(target)

        # Heal ally for additional 5% of their max HP
        additional_healing = int(cleansed_ally.max_hp * 0.05)
        if additional_healing > 0:
            await cleansed_ally.apply_healing(
                additional_healing,
                healer=target,
                source_type="cleanse",
                source_name=self.id,
            )

        # Grant Lady Light +2% attack (stacking with no cap)
        attack_increase = int(target.atk * 0.02)
        self._attack_bonuses[entity_id] += attack_increase

        # Apply the bonus immediately
        cleanse_bonus_effect = StatEffect(
            name=f"{self.id}_cleanse_attack_{entity_id}",
            stat_modifiers={"atk": attack_increase},
            duration=-1,  # Permanent for rest of battle
            source=self.id,
        )
        target.add_effect(cleanse_bonus_effect)

    @classmethod
    def get_attack_bonus(cls, target: "Stats") -> int:
        """Get current attack bonus from DoT cleanses."""
        return cls._attack_bonuses.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "HoTs grant shields equal to 50% of the heal and +5% effect resistance for one turn. "
            "Cleansing a DoT heals 5% of max HP and gives Lady Light +2% attack per cleanse."
        )

    def _calculate_hot_amount(
        self,
        healer: "Stats",
        ally: "Stats",
        hot: object,
        details: Mapping[str, object] | None,
    ) -> int:
        base_value = None
        if details is not None:
            base_value = details.get("healing")
        if base_value is None:
            base_value = getattr(hot, "healing", None)
        if base_value is None:
            return 0

        heal_amount = float(base_value)
        dtype = getattr(hot, "damage_type", None)
        if dtype is None:
            dtype = getattr(healer, "damage_type", None)

        if dtype is not None:
            heal_amount = dtype.on_hot_heal_received(heal_amount, healer, ally)
            heal_amount = dtype.on_party_hot_heal_received(heal_amount, healer, ally)

        healer_type = getattr(healer, "damage_type", None)
        if healer_type is not None and healer_type is not dtype:
            heal_amount = healer_type.on_party_hot_heal_received(
                heal_amount,
                healer,
                ally,
            )

        heal_amount *= getattr(healer, "vitality", 1.0)
        heal_amount *= getattr(ally, "vitality", 1.0)

        enrage = get_enrage_percent()
        if enrage > 0:
            heal_amount *= max(1.0 - enrage, 0.0)

        return max(0, int(heal_amount))
