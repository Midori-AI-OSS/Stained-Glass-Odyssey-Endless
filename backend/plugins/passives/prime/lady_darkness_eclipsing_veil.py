from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Mapping
from weakref import ref

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from plugins.passives.normal.lady_darkness_eclipsing_veil import LadyDarknessEclipsingVeil

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyDarknessEclipsingVeilPrime(LadyDarknessEclipsingVeil):
    """[PRIME] Eclipsing Veil with longer DoTs and richer siphons."""

    plugin_type = "passive"
    id = "lady_darkness_eclipsing_veil_prime"
    name = "Prime Eclipsing Veil"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(self, target: "Stats", **kwargs: object) -> None:
        entity_id = id(target)
        party_members = self._collect_party_members(kwargs.get("party"))
        party_ids = frozenset({id(member) for member in party_members} | {entity_id})
        self.__class__._party_cache[entity_id] = party_ids

        if entity_id not in self._attack_bonuses:
            self._attack_bonuses[entity_id] = 0

        dot_extension_effect = StatEffect(
            name=f"{self.id}_dot_extension",
            stat_modifiers={"dot_duration_bonus": 2},
            duration=-1,
            source=self.id,
        )
        target.add_effect(dot_extension_effect)

        if self._attack_bonuses[entity_id] > 0:
            attack_bonus_effect = StatEffect(
                name=self._resist_effect_name(entity_id),
                stat_modifiers={"atk": self._attack_bonuses[entity_id]},
                duration=-1,
                source=self.id,
            )
            target.add_effect(attack_bonus_effect)

        self._ensure_event_hooks(target)

    async def on_dot_tick(self, target: "Stats", dot_damage: int) -> None:
        siphoned_healing = max(1, int(dot_damage * 0.03))
        await target.apply_healing(siphoned_healing)
        drain = StatEffect(
            name=f"{self.id}_veil_bite",
            stat_modifiers={"mitigation": -0.02},
            duration=1,
            source=self.id,
        )
        target.add_effect(drain)

    async def on_debuff_resist(self, target: "Stats") -> None:
        entity_id = id(target)
        attack_increase = int(target.atk * 0.1)
        self._attack_bonuses[entity_id] += attack_increase
        total_attack_bonus = self._attack_bonuses[entity_id]
        resist_bonus_effect = StatEffect(
            name=self._resist_effect_name(entity_id),
            stat_modifiers={
                "atk": total_attack_bonus,
                "lifesteal": 0.05,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(resist_bonus_effect)

    def _ensure_event_hooks(self, target: "Stats") -> None:
        cls = self.__class__
        entity_id = id(target)

        if entity_id in cls._dot_callbacks:
            return

        target_ref = ref(target)

        async def _on_dot_tick(attacker, dot_target, amount, *_args: object) -> None:
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
    def get_description(cls) -> str:
        return (
            "[PRIME] Extends DoTs by two turns and siphons 3% of each tick as healing while eroding foe mitigation. "
            "Resisting a debuff grants +10% attack and 5% lifesteal, stacking for the rest of the fight."
        )

