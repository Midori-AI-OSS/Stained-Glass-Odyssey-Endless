from dataclasses import dataclass

from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy


@dataclass
class AdvancedCombatSynergyGlitched(AdvancedCombatSynergy):
    """Glitched variant of Advanced Combat Synergy with doubled effects."""
    plugin_type = "passive"
    id = "advanced_combat_synergy_glitched"
    name = "Glitched Advanced Combat Synergy"
    trigger = ["hit_landed", "turn_start", "action_taken"]
    max_stacks = 6  # Glitched: 6 instead of 3
    stack_display = "pips"

    async def apply(self, target, **kwargs) -> None:
        """Handle event-based logic with glitched doubled buffs."""
        if kwargs.get("event") != "hit_landed":
            return

        from autofighter.stat_effect import StatEffect

        hit_target = kwargs.get("hit_target")
        damage = kwargs.get("damage", 0)
        party = kwargs.get("party", [])

        if hit_target and damage > 0:
            # Conditional trigger: only activate if target is below 50% HP
            if hit_target.hp < (hit_target.max_hp * 0.5):
                # Glitched: Doubled ally buffs
                for ally in party:
                    if ally != target and ally.hp > 0:
                        effect = StatEffect(
                            name=f"{self.id}_ally_atk_boost",
                            stat_modifiers={"atk": 20},  # Glitched: 20 (doubled from 10)
                            duration=3,
                            source=self.id,
                        )
                        ally.add_effect(effect)

    async def on_turn_start(self, target, **kwargs) -> None:
        """Handle turn_start with glitched doubled dynamic behavior."""
        from autofighter.stat_effect import StatEffect

        party = kwargs.get('party', [])
        living_allies = sum(1 for ally in party if ally.hp > 0)

        if living_allies >= 3:
            # Glitched: Doubled scaling
            bonus_damage = living_allies * 10  # Glitched: 10 (doubled from 5)
            effect = StatEffect(
                name=f"{self.id}_synergy_damage",
                stat_modifiers={"atk": bonus_damage},
                duration=1,
                source=self.id,
            )
            target.add_effect(effect)

    async def on_action_taken(self, target, **kwargs) -> None:
        """Build synergy stacks with glitched doubled bonuses."""
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)
        current_stacks = AdvancedCombatSynergyGlitched._synergy_stacks.get(entity_id, 0)

        if current_stacks < self.max_stacks:
            AdvancedCombatSynergyGlitched._synergy_stacks[entity_id] = current_stacks + 1

            # Glitched: Doubled persistent effect
            stacks = AdvancedCombatSynergyGlitched._synergy_stacks[entity_id]
            effect = StatEffect(
                name=f"{self.id}_persistent_buff",
                stat_modifiers={
                    "atk": stacks * 6,  # Glitched: 6 (doubled from 3)
                    "crit_rate": stacks * 0.02,  # Glitched: 0.02 (doubled from 0.01)
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[GLITCHED] Grants allies +20 attack for 3 turns when hitting a foe below 50% HP (doubled). "
            "If 3+ allies are alive at turn start, gains +10 attack per ally for that turn (doubled). "
            "Each action builds up to 6 stacks, adding +6 attack and +2% crit rate per stack (doubled)."
        )
