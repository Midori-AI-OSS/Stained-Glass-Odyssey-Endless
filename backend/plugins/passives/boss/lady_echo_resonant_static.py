from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_echo_resonant_static import LadyEchoResonantStatic

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyEchoResonantStaticBoss(LadyEchoResonantStatic):
    """Boss Resonant Static that doubles down on DoT-focused chain hits."""

    plugin_type = "passive"
    id = "lady_echo_resonant_static_boss"
    name = "Resonant Static (Boss)"
    trigger = "hit_landed"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(
        self,
        target: "Stats",
        hit_target: Optional["Stats"] = None,
        **kwargs,
    ) -> None:
        """Grant 15% damage per DoT and +3% party crit per chain stack."""

        entity_id = id(target)
        if entity_id not in self._consecutive_hits:
            self._consecutive_hits[entity_id] = 0
            self._party_crit_stacks[entity_id] = 0
        self._register_battle_end(target)

        dot_target = hit_target or target
        mgr = getattr(dot_target, "effect_manager", None)
        dot_count = len(getattr(mgr, "dots", [])) if mgr is not None else len(getattr(dot_target, "dots", []))

        chain_damage_bonus = dot_count * 0.15
        if chain_damage_bonus > 0:
            chain_effect = StatEffect(
                name=f"{self.id}_chain_bonus",
                stat_modifiers={"atk": int(target.atk * chain_damage_bonus)},
                duration=1,
                source=self.id,
            )
            target.add_effect(chain_effect)

        current_crit_stacks = self._party_crit_stacks[entity_id]
        if current_crit_stacks > 0:
            party_crit_bonus = min(current_crit_stacks * 0.03, 0.30)
            party_crit_effect = StatEffect(
                name=f"{self.id}_party_crit",
                stat_modifiers={"crit_rate": party_crit_bonus},
                duration=-1,
                source=self.id,
            )
            target.add_effect(party_crit_effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Chain lightning gains +15% damage per DoT on the target and grants the party +3% crit rate per consecutive hit (max 30%)."
        )
