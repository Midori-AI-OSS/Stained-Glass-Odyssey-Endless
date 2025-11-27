from dataclasses import dataclass
from typing import TYPE_CHECKING

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class AdvancedCombatSynergyPrime(AdvancedCombatSynergy):
    """[PRIME] Synergy with wider team hooks and heavier scaling."""

    plugin_type = "passive"
    id = "advanced_combat_synergy_prime"
    name = "Prime Combat Synergy"
    trigger = ["hit_landed", "turn_start", "action_taken"]
    max_stacks = 5
    stack_display = "pips"

    async def apply(self, target: "Stats", **kwargs) -> None:
        """Empower ally buffs on low-HP targets with larger gains."""

        if kwargs.get("event") != "hit_landed":
            return

        hit_target = kwargs.get("hit_target")
        damage = kwargs.get("damage", 0)
        party = kwargs.get("party", [])

        if hit_target and damage > 0:
            if hit_target.hp < (hit_target.max_hp * 0.65):
                for ally in party:
                    if ally != target and getattr(ally, "hp", 0) > 0:
                        effect = StatEffect(
                            name=f"{self.id}_ally_atk_boost",
                            stat_modifiers={
                                "atk": 25,
                                "crit_rate": 0.03,
                            },
                            duration=3,
                            source=self.id,
                        )
                        ally.add_effect(effect)

    async def on_turn_start(self, target: "Stats", **kwargs) -> None:
        """Larger tempo buff when the team is healthy."""

        party = kwargs.get("party", [])
        living_allies = sum(1 for ally in party if getattr(ally, "hp", 0) > 0)

        if living_allies >= 2:
            bonus_damage = living_allies * 10
            effect = StatEffect(
                name=f"{self.id}_synergy_damage",
                stat_modifiers={
                    "atk": bonus_damage,
                    "spd": 1,
                },
                duration=1,
                source=self.id,
            )
            target.add_effect(effect)

    async def on_action_taken(self, target: "Stats", **kwargs) -> None:
        """Prime stacks grant stronger stat packages."""

        entity_id = id(target)
        current_stacks = self._synergy_stacks.get(entity_id, 0)

        if current_stacks < self.max_stacks:
            self._synergy_stacks[entity_id] = current_stacks + 1

        stacks = self._synergy_stacks.get(entity_id, 0)
        effect = StatEffect(
            name=f"{self.id}_persistent_buff",
            stat_modifiers={
                "atk": stacks * 8,
                "crit_rate": stacks * 0.02,
                "mitigation": stacks * 0.01,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Buff allies for +25 ATK and +3% crit when striking foes below 65% HP. "
            "Turn start grants +10 ATK and +1 SPD per living ally. "
            "Actions build up to 5 stacks, each adding +8 ATK, +2% crit rate, and 1% mitigation for the party lead."
        )

