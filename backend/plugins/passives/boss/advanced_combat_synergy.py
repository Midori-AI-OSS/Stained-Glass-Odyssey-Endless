from dataclasses import dataclass

from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy


@dataclass
class AdvancedCombatSynergyBoss(AdvancedCombatSynergy):
    """Boss variant of Advanced Combat Synergy with enhanced bonuses."""
    plugin_type = "passive"
    id = "advanced_combat_synergy_boss"
    name = "Advanced Combat Synergy (Boss)"
    trigger = ["hit_landed", "turn_start", "action_taken"]
    max_stacks = 5  # Increased from 3
    stack_display = "pips"

    async def apply(self, target, **kwargs) -> None:
        """Handle event-based logic; currently only acts on hit_landed with enhanced buff."""
        if kwargs.get("event") != "hit_landed":
            return

        from autofighter.stat_effect import StatEffect

        hit_target = kwargs.get("hit_target")
        damage = kwargs.get("damage", 0)
        party = kwargs.get("party", [])

        if hit_target and damage > 0:
            # Conditional trigger: only activate if target is below 50% HP
            if hit_target.hp < (hit_target.max_hp * 0.5):
                # Cross-character effect: buff all living allies with enhanced values
                for ally in party:
                    if ally != target and ally.hp > 0:
                        effect = StatEffect(
                            name=f"{self.id}_ally_atk_boost",
                            stat_modifiers={"atk": 25},  # Boss: 25 instead of 10
                            duration=3,
                            source=self.id,
                        )
                        ally.add_effect(effect)

    async def on_turn_start(self, target, **kwargs) -> None:
        """Handle turn_start with enhanced dynamic behavior."""
        from autofighter.stat_effect import StatEffect

        party = kwargs.get('party', [])
        living_allies = sum(1 for ally in party if ally.hp > 0)

        if living_allies >= 3:
            # Boss: Enhanced scaling
            bonus_damage = living_allies * 12  # Boss: 12 instead of 5
            effect = StatEffect(
                name=f"{self.id}_synergy_damage",
                stat_modifiers={"atk": bonus_damage},
                duration=1,
                source=self.id,
            )
            target.add_effect(effect)

    async def on_action_taken(self, target, **kwargs) -> None:
        """Build synergy stacks on action taken with enhanced bonuses."""
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)
        current_stacks = AdvancedCombatSynergyBoss._synergy_stacks.get(entity_id, 0)

        if current_stacks < self.max_stacks:
            AdvancedCombatSynergyBoss._synergy_stacks[entity_id] = current_stacks + 1

            # Boss: Enhanced persistent effect
            stacks = AdvancedCombatSynergyBoss._synergy_stacks[entity_id]
            effect = StatEffect(
                name=f"{self.id}_persistent_buff",
                stat_modifiers={
                    "atk": stacks * 7,  # Boss: 7 instead of 3
                    "crit_rate": stacks * 0.02,  # Boss: 0.02 instead of 0.01
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[BOSS] Grants allies +25 attack for 3 turns when hitting a foe below 50% HP. "
            "If 3+ allies are alive at turn start, gains +12 attack per ally for that turn. "
            "Each action builds up to 5 stacks, adding +7 attack and +2% crit rate per stack."
        )
