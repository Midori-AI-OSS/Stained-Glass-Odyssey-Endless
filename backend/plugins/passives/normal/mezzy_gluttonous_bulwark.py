from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect

SAFE_MAX_HP_FLOOR = 1

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class MezzyGluttonousBulwark:
    """Mezzy's Gluttonous Bulwark passive - damage reduction and stat siphoning."""
    plugin_type = "passive"
    id = "mezzy_gluttonous_bulwark"
    name = "Gluttonous Bulwark"
    trigger = "turn_start"  # Triggers at start of Mezzy's turn
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of siphoned stats per ally
    _siphoned_stats: ClassVar[dict[int, dict[str, int]]] = {}

    async def apply(self, target: "Stats", allies: list["Stats"] | None = None, **_: object) -> None:
        """Apply Mezzy's bulk and siphoning mechanics."""
        # Apply 20% damage reduction (permanent while passive is active)
        damage_reduction = StatEffect(
            name=f"{self.id}_damage_reduction",
            stat_modifiers={"mitigation": 0.2},  # 20% damage reduction
            duration=-1,  # Permanent
            source=self.id,
        )
        target.add_effect(damage_reduction)

        # Focus on Max HP growth
        hp_growth_bonus = StatEffect(
            name=f"{self.id}_hp_focus",
            stat_modifiers={"max_hp": int(target.max_hp * 0.1)},  # 10% max HP bonus
            duration=-1,  # Permanent
            source=self.id,
        )
        target.add_effect(hp_growth_bonus)

        # Immunity to allied debuffs (would need battle system integration)
        # For now, just add resistance
        debuff_immunity = StatEffect(
            name=f"{self.id}_debuff_immunity",
            stat_modifiers={"effect_resistance": 0.5},  # 50% debuff resistance
            duration=-1,  # Permanent
            source=self.id,
        )
        target.add_effect(debuff_immunity)

        if allies is None:
            allies = list(getattr(target, "allies", []))
        if allies:
            await self.siphon_from_allies(target, allies)

    async def siphon_from_allies(self, mezzy: "Stats", allies: list["Stats"]) -> None:
        """Siphon stats from allies whose HP exceeds 20% of Mezzy's max HP."""
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

            # Siphon 1% of attack, defense, and max HP
            stats_to_siphon = ["atk", "defense", "max_hp"]

            if ally_id not in self._siphoned_stats:
                self._siphoned_stats[ally_id] = {}

            for stat in stats_to_siphon:
                base_value = getattr(ally, stat, 0)
                siphon_amount = max(1, int(base_value * 0.01))  # 1% minimum 1

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
                    duration=-1,  # Permanent until returned
                    source=f"{self.id}_siphon",
                )
                ally.add_effect(ally_debuff)

                # Apply buff to Mezzy
                mezzy_buff = StatEffect(
                    name=f"{self.id}_gain_{stat}",
                    stat_modifiers={stat: new_total},
                    duration=-1,  # Permanent
                    source=f"{self.id}_gain",
                )
                mezzy.add_effect(mezzy_buff)

            if not self._siphoned_stats[ally_id]:
                del self._siphoned_stats[ally_id]

    @classmethod
    def get_description(cls) -> str:
        return (
            "Reduces damage taken by 20% and increases max HP by 10%. "
            "Siphons 1% of attack, defense, and max HP from allies above 20% of her max HP each turn, "
            "returning half when they fall below. Also grants 50% debuff resistance."
        )
