from dataclasses import dataclass
from typing import TYPE_CHECKING

from plugins.passives.normal.mezzy_gluttonous_bulwark import SAFE_MAX_HP_FLOOR, MezzyGluttonousBulwark

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class MezzyGluttonousBulwarkGlitched(MezzyGluttonousBulwark):
    """[GLITCHED] Mezzy's Gluttonous Bulwark - doubled stat siphoning.

    This glitched variant doubles the stat siphoning rate (2% per turn instead of 1%)
    while maintaining the same damage reduction, HP bonus, and debuff resistance
    mechanics. This allows for much faster stat accumulation.
    """
    plugin_type = "passive"
    id = "mezzy_gluttonous_bulwark_glitched"
    name = "Glitched Gluttonous Bulwark"
    trigger = "turn_start"
    max_stacks = 1
    stack_display = "spinner"

    async def siphon_from_allies(self, mezzy: "Stats", allies: list["Stats"]) -> None:
        """Siphon stats with DOUBLED rate (2% instead of 1%)."""
        from autofighter.stat_effect import StatEffect

        mezzy_id = id(mezzy)
        hp_threshold = mezzy.max_hp * 0.2

        for ally in allies:
            ally_id = id(ally)

            # Skip if ally HP is too low or if it's Mezzy herself
            if ally.hp <= hp_threshold or ally_id == mezzy_id:
                # Return half of previously siphoned stats if ally falls below threshold
                if ally_id in self._siphoned_stats:
                    returned_stats = self._siphoned_stats[ally_id]
                    remaining_stats: dict[str, int] = {}
                    for stat, amount in returned_stats.items():
                        if amount <= 0:
                            ally.remove_effect_by_name(f"{self.id}_siphon_{stat}")
                            mezzy.remove_effect_by_name(f"{self.id}_gain_{stat}")
                            continue

                        remaining = amount - (amount // 2)

                        if remaining > 0:
                            remaining_stats[stat] = remaining
                            ally.add_effect(
                                StatEffect(
                                    name=f"{self.id}_siphon_{stat}",
                                    stat_modifiers={stat: -remaining},
                                    duration=-1,
                                    source=f"{self.id}_siphon",
                                )
                            )
                            mezzy.add_effect(
                                StatEffect(
                                    name=f"{self.id}_gain_{stat}",
                                    stat_modifiers={stat: remaining},
                                    duration=-1,
                                    source=f"{self.id}_gain",
                                )
                            )
                        else:
                            ally.remove_effect_by_name(f"{self.id}_siphon_{stat}")
                            mezzy.remove_effect_by_name(f"{self.id}_gain_{stat}")

                    if remaining_stats:
                        self._siphoned_stats[ally_id] = remaining_stats
                    else:
                        del self._siphoned_stats[ally_id]
                continue

            # DOUBLED siphon rate (2% instead of 1%)
            stats_to_siphon = ["atk", "defense", "max_hp"]

            if ally_id not in self._siphoned_stats:
                self._siphoned_stats[ally_id] = {}

            for stat in stats_to_siphon:
                base_value = getattr(ally, stat, 0)
                siphon_amount = max(1, int(base_value * 0.02))  # DOUBLED from 0.01

                if stat == "max_hp":
                    if base_value <= SAFE_MAX_HP_FLOOR:
                        continue
                    max_reducible = base_value - SAFE_MAX_HP_FLOOR
                    if max_reducible <= 0:
                        continue
                    siphon_amount = min(siphon_amount, max_reducible)

                # Track total siphoned
                if stat not in self._siphoned_stats[ally_id]:
                    self._siphoned_stats[ally_id][stat] = 0
                new_total = self._siphoned_stats[ally_id][stat] + siphon_amount
                self._siphoned_stats[ally_id][stat] = new_total

                # Apply debuff to ally
                ally_debuff = StatEffect(
                    name=f"{self.id}_siphon_{stat}",
                    stat_modifiers={stat: -new_total},
                    duration=-1,
                    source=f"{self.id}_siphon",
                )
                ally.add_effect(ally_debuff)

                # Apply buff to Mezzy
                mezzy_buff = StatEffect(
                    name=f"{self.id}_gain_{stat}",
                    stat_modifiers={stat: new_total},
                    duration=-1,
                    source=f"{self.id}_gain",
                )
                mezzy.add_effect(mezzy_buff)

            if not self._siphoned_stats[ally_id]:
                del self._siphoned_stats[ally_id]

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Reduces damage taken by 20% and increases max HP by 10%. "
            "Siphons 2% (doubled) of attack, defense, and max HP from allies above 20% of her max HP each turn, "
            "returning half when they fall below. Also grants 50% debuff resistance."
        )
