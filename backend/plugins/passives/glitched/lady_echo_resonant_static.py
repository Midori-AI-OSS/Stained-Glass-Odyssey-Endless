from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Optional

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_echo_resonant_static import LadyEchoResonantStatic

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyEchoResonantStaticGlitched(LadyEchoResonantStatic):
    """[GLITCHED] Lady Echo's Resonant Static - doubled consecutive hit bonuses.

    This glitched variant doubles all damage and effect bonuses from consecutive
    hits, making the chain lightning mechanic significantly more powerful when
    focusing on a single target.
    """
    plugin_type = "passive"
    id = "lady_echo_resonant_static_glitched"
    name = "Glitched Resonant Static"
    trigger = "hit_landed"
    max_stacks = 1
    stack_display = "spinner"

    async def apply(
        self,
        target: "Stats",
        hit_target: Optional["Stats"] = None,
        **kwargs,
    ) -> None:
        """Apply chain lightning scaling with DOUBLED bonuses."""
        entity_id = id(target)

        # Initialize tracking if not present
        if entity_id not in self._consecutive_hits:
            self._consecutive_hits[entity_id] = 0
            self._party_crit_stacks[entity_id] = 0
        self._register_battle_end(target)

        # Count DoTs on the hit target (enemy) for chain damage scaling
        dot_target = hit_target or target
        mgr = getattr(dot_target, "effect_manager", None)
        if mgr is not None:
            dot_count = len(getattr(mgr, "dots", []))
        else:
            dot_count = len(getattr(dot_target, "dots", []))

        # DOUBLED: 20% per DoT instead of 10%
        chain_damage_bonus = dot_count * 0.2  # Was 0.1

        if chain_damage_bonus > 0:
            chain_effect = StatEffect(
                name=f"{self.id}_chain_bonus",
                stat_modifiers={"atk": int(target.atk * chain_damage_bonus)},
                duration=1,
                source=self.id,
            )
            target.add_effect(chain_effect)

        # Apply party crit rate bonus from consecutive hits
        current_crit_stacks = self._party_crit_stacks[entity_id]
        if current_crit_stacks > 0:
            # DOUBLED: 4% per stack instead of 2%, max 40% instead of 20%
            party_crit_bonus = min(current_crit_stacks * 0.04, 0.4)  # Was 0.02, 0.2

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
            "[GLITCHED] Chain lightning hits deal +20% damage per DoT (doubled). "
            "Consecutive hits on the same foe grant the party +4% crit rate per stack (doubled), up to 40%."
        )
