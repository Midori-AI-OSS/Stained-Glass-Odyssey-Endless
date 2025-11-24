from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.casno_phoenix_respite import CasnoPhoenixRespite

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class CasnoPhoenixRespitePrime(CasnoPhoenixRespite):
    """[PRIME] Phoenix Respite accelerates relaxed cycles and boosts payouts."""

    plugin_type = "passive"
    id = "casno_phoenix_respite_prime"
    name = "Prime Phoenix Respite"
    trigger = "action_taken"
    stack_display = "number"

    async def apply(self, target: "Stats", **_: object) -> None:
        entity_id = id(target)
        cls = type(self)

        cls._register_battle_end(target)
        cls._relaxed_stacks.setdefault(entity_id, 0)
        cls._relaxed_converted.setdefault(entity_id, 0)
        cls._attack_counts[entity_id] = cls._attack_counts.get(entity_id, 0) + 1

        if cls._pending_relaxed.get(entity_id):
            return

        if cls._attack_counts[entity_id] < 3:
            return

        cls._attack_counts[entity_id] = 0
        cls._relaxed_stacks[entity_id] = cls._relaxed_stacks.get(entity_id, 0) + 2

        if cls._relaxed_stacks[entity_id] > 30:
            await cls._schedule_relaxed_pause(target)

    @classmethod
    def _apply_relaxed_boost(cls, target: "Stats", converted_stacks: int) -> None:
        effect_name = cls._boost_effect_name(id(target))
        target.remove_effect_by_name(effect_name)

        stat_names = [
            "max_hp",
            "atk",
            "defense",
            "crit_rate",
            "crit_damage",
            "effect_hit_rate",
            "effect_resistance",
            "mitigation",
            "vitality",
            "regain",
            "dodge_odds",
            "spd",
        ]

        modifiers: dict[str, float | int] = {}
        multiplier = 0.25 * converted_stacks
        for stat in stat_names:
            base_value = target.get_base_stat(stat)
            bonus = base_value * multiplier
            if isinstance(base_value, int):
                bonus = int(bonus)
            modifiers[stat] = bonus

        effect = cls._build_effect(effect_name, modifiers)
        target.add_effect(effect)

    @classmethod
    def _build_effect(cls, name: str, modifiers: dict[str, float | int]):
        from autofighter.stat_effect import StatEffect

        return StatEffect(
            name=name,
            stat_modifiers=modifiers,
            duration=-1,
            source=cls.id,
        )

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Gains relaxed stacks faster (every 3 actions, +2 stacks) and cashes out sooner. "
            "Pause cycles convert stacks into 25% scaling bonuses across all stats for smoother sustained fights."
        )

