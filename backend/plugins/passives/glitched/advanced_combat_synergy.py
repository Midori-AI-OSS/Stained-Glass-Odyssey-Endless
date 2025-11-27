from dataclasses import dataclass
from typing import ClassVar

from autofighter.stat_effect import StatEffect
from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy


@dataclass
class AdvancedCombatSynergyGlitched(AdvancedCombatSynergy):
    """[GLITCHED] Advanced Combat Synergy - doubled party-wide bonuses.

    This glitched variant doubles all party-wide stat bonuses from coordination,
    making party synergy effects much more impactful.
    """
    plugin_type = "passive"
    id = "advanced_combat_synergy_glitched"
    name = "Glitched Combat Synergy"
    trigger = ["hit_landed", "turn_start", "action_taken"]
    max_stacks = 3
    stack_display = "pips"

    _synergy_stacks: ClassVar[dict[int, int]] = {}

    async def apply(self, target, **kwargs) -> None:
        """Handle hit_landed with DOUBLED ally buff."""
        if kwargs.get("event") != "hit_landed":
            return

        hit_target = kwargs.get("hit_target")
        damage = kwargs.get("damage", 0)
        party = kwargs.get("party", [])

        if hit_target and damage > 0:
            if hit_target.hp < (hit_target.max_hp * 0.5):
                # DOUBLED: +20 attack instead of +10
                for ally in party:
                    if ally != target and ally.hp > 0:
                        effect = StatEffect(
                            name=f"{self.id}_ally_atk_boost",
                            stat_modifiers={"atk": 20},  # Was 10
                            duration=3,
                            source=self.id,
                        )
                        ally.add_effect(effect)

    async def on_turn_start(self, target, **kwargs) -> None:
        """Handle turn_start with DOUBLED scaling."""
        party = kwargs.get('party', [])
        living_allies = sum(1 for ally in party if ally.hp > 0)

        if living_allies >= 3:
            # DOUBLED: +10 per ally instead of +5
            bonus_damage = living_allies * 10  # Was 5
            effect = StatEffect(
                name=f"{self.id}_synergy_damage",
                stat_modifiers={"atk": bonus_damage},
                duration=1,
                source=self.id,
            )
            target.add_effect(effect)

    async def on_action_taken(self, target, **kwargs) -> None:
        """Build synergy stacks with DOUBLED benefits."""
        entity_id = id(target)
        current_stacks = self._synergy_stacks.get(entity_id, 0)

        if current_stacks < self.max_stacks:
            self._synergy_stacks[entity_id] = current_stacks + 1

            # DOUBLED: +6 attack and +2% crit per stack (was +3 and +1%)
            stacks = self._synergy_stacks[entity_id]
            effect = StatEffect(
                name=f"{self.id}_persistent_buff",
                stat_modifiers={
                    "atk": stacks * 6,  # Was 3
                    "crit_rate": stacks * 0.02,  # Was 0.01
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Grants allies +20 attack (doubled) for 3 turns when hitting a foe below 50% HP. "
            "If 3+ allies are alive at turn start, gains +10 attack per ally (doubled) for that turn. "
            "Each action builds up to 3 stacks, adding +6 attack and +2% crit rate (doubled) per stack."
        )
