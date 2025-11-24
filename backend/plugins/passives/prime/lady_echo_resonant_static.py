from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_echo_resonant_static import LadyEchoResonantStatic

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyEchoResonantStaticPrime(LadyEchoResonantStatic):
    """[PRIME] Resonant Static with sharper chains and crit surges."""

    plugin_type = "passive"
    id = "lady_echo_resonant_static_prime"
    name = "Prime Resonant Static"
    trigger = "hit_landed"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(
        self,
        target: "Stats",
        hit_target: "Stats" | None = None,
        **kwargs,
    ) -> None:
        entity_id = id(target)
        self._consecutive_hits.setdefault(entity_id, 0)
        self._party_crit_stacks.setdefault(entity_id, 0)

        dot_target = hit_target or target
        mgr = getattr(dot_target, "effect_manager", None)
        dot_count = len(getattr(mgr, "dots", [])) if mgr is not None else len(getattr(dot_target, "dots", []))
        chain_damage_bonus = dot_count * 0.15

        if chain_damage_bonus > 0:
            chain_effect = StatEffect(
                name=f"{self.id}_chain_bonus",
                stat_modifiers={
                    "atk": int(target.atk * chain_damage_bonus),
                    "crit_rate": 0.02,
                },
                duration=1,
                source=self.id,
            )
            target.add_effect(chain_effect)

        current_crit_stacks = self._party_crit_stacks[entity_id]
        if current_crit_stacks > 0:
            party_crit_bonus = min(current_crit_stacks * 0.03, 0.3)
            party_crit_effect = StatEffect(
                name=f"{self.id}_party_crit",
                stat_modifiers={"crit_rate": party_crit_bonus},
                duration=-1,
                source=self.id,
            )
            target.add_effect(party_crit_effect)

    async def on_hit_landed(
        self,
        attacker: "Stats",
        target_hit: "Stats",
        damage: int = 0,
        action_type: str = "attack",
        **_: object,
    ) -> None:
        attacker_id = id(attacker)
        target_id = id(target_hit)

        previous_target = self._current_target.get(attacker_id)
        hit_count = self._consecutive_hits.get(attacker_id, 0)
        crit_stacks = self._party_crit_stacks.get(attacker_id, 0)

        if previous_target == target_id and hit_count:
            hit_count = min(hit_count + 1, 12)
            crit_stacks = min(crit_stacks + 1, 12)
        else:
            hit_count = 1
            crit_stacks = 1
            attacker.remove_effect_by_name(f"{self.id}_party_crit")

        self._consecutive_hits[attacker_id] = hit_count
        self._party_crit_stacks[attacker_id] = crit_stacks
        self._current_target[attacker_id] = target_id

        tempo_boost = StatEffect(
            name=f"{self.id}_tempo",
            stat_modifiers={"spd": min(hit_count, 6)},
            duration=2,
            source=self.id,
        )
        attacker.add_effect(tempo_boost)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Chain damage gains +15% per DoT and +2% crit on the strike. "
            "Consecutive hits stack to 12, granting the party up to +30% crit rate and a small speed boost."
        )

