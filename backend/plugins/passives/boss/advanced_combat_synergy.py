from dataclasses import dataclass
from typing import ClassVar

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy


@dataclass
class AdvancedCombatSynergyBoss(AdvancedCombatSynergy):
    """Boss-tier Combat Synergy with elevated party buffs and crit scaling."""

    plugin_type = "passive"
    id = "advanced_combat_synergy_boss"
    name = "Combat Synergy (Boss)"
    trigger = ["hit_landed", "turn_start", "action_taken"]
    max_stacks = 3
    stack_display = "pips"

    _synergy_stacks: ClassVar[dict[int, int]] = {}

    async def apply(self, target, **kwargs) -> None:
        """Give stronger ally attack buffs when focus targets are weakened."""

        if kwargs.get("event") != "hit_landed":
            return

        hit_target = kwargs.get("hit_target")
        damage = kwargs.get("damage", 0)
        party = kwargs.get("party", [])

        if hit_target and damage > 0 and hit_target.hp < (hit_target.max_hp * 0.5):
            for ally in party:
                if ally != target and ally.hp > 0:
                    effect = StatEffect(
                        name=f"{self.id}_ally_atk_boost",
                        stat_modifiers={"atk": 15},
                        duration=3,
                        source=self.id,
                    )
                    ally.add_effect(effect)

    async def on_turn_start(self, target, **kwargs) -> None:
        """Amplify cadence bonuses when the squad stays alive."""

        party = kwargs.get("party", [])
        living_allies = sum(1 for ally in party if ally.hp > 0)
        if living_allies >= 3:
            bonus_damage = living_allies * 7
            effect = StatEffect(
                name=f"{self.id}_synergy_damage",
                stat_modifiers={"atk": bonus_damage},
                duration=1,
                source=self.id,
            )
            target.add_effect(effect)

    async def on_action_taken(self, target, **kwargs) -> None:
        """Build stacking offensive focus with boss tuning."""

        entity_id = id(target)
        current = self._synergy_stacks.get(entity_id, 0)
        if current >= self.max_stacks:
            return

        stacks = current + 1
        self._synergy_stacks[entity_id] = stacks
        atk_bonus = int(stacks * 4.5)
        crit_bonus = stacks * 0.015
        effect = StatEffect(
            name=f"{self.id}_persistent_buff",
            stat_modifiers={
                "atk": atk_bonus,
                "crit_rate": crit_bonus,
            },
            duration=-1,
            source=self.id,
        )
        target.add_effect(effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Gains +15 attack for allies when striking foes below 50% HP. "
            "With 3+ allies alive, grants +7 attack per ally each turn. "
            "Each action adds a stack (max 3) worth +4.5 attack and +1.5% crit rate, persisting until dispelled."
        )
