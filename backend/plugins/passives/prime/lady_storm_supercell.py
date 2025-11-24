from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.lady_storm_supercell import LadyStormSupercell

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LadyStormSupercellPrime(LadyStormSupercell):
    """[PRIME] Supercell with stronger gale support and lightning payout."""

    plugin_type = "passive"
    id = "lady_storm_supercell_prime"
    name = "Prime Supercell Convergence"
    trigger = ["turn_start", "action_taken", "hit_landed"]
    max_stacks = 1
    stack_display = "spinner"

    async def on_action_taken(self, target: "Stats", **kwargs: object) -> None:
        await super().on_action_taken(target, **kwargs)

        entity_id = id(target)
        charges = self._storm_charge.get(entity_id, 0)
        if charges > 0:
            tempo = StatEffect(
                name=f"{self.id}_prime_slipstream",
                stat_modifiers={"spd": charges * 4, "effect_hit_rate": charges * 0.05},
                duration=2,
                source=self.id,
            )
            target.add_effect(tempo)

    async def on_hit_landed(
        self,
        attacker: "Stats",
        target_hit: "Stats",
        damage: int = 0,
        action_type: str = "attack",
        **kwargs,
    ) -> None:
        await super().on_hit_landed(attacker, target_hit, damage, action_type, **kwargs)

        attacker_id = id(attacker)
        charges = self._storm_charge.get(attacker_id, 0)
        if charges <= 0:
            return

        residual = StatEffect(
            name=f"{self.id}_storm_residual",
            stat_modifiers={
                "crit_damage": 0.05 * charges,
                "mitigation": 0.03 * charges,
            },
            duration=2,
            source=self.id,
        )
        attacker.add_effect(residual)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Alternating wind/lightning now layers extra speed and effect hit per stored charge, and detonations grant lingering crit damage and mitigation."
        )

