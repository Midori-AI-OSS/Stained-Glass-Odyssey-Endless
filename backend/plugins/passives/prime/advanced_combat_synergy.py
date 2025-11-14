from dataclasses import dataclass

from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy


@dataclass
class AdvancedCombatSynergyPrime(AdvancedCombatSynergy):
    """Prime variant of Advanced Combat Synergy with massive bonuses."""
    plugin_type = "passive"
    id = "advanced_combat_synergy_prime"
    name = "Prime Advanced Combat Synergy"
    trigger = ["hit_landed", "turn_start", "action_taken"]
    max_stacks = 8  # Increased from 3
    stack_display = "pips"

    async def apply(self, target, **kwargs) -> None:
        """Handle event-based logic with prime-tier buffs."""
        if kwargs.get("event") != "hit_landed":
            return

        from autofighter.stat_effect import StatEffect

        hit_target = kwargs.get("hit_target")
        damage = kwargs.get("damage", 0)
        party = kwargs.get("party", [])

        if hit_target and damage > 0:
            # Prime: Lower HP threshold for more frequent activation
            if hit_target.hp < (hit_target.max_hp * 0.6):  # Prime: 60% instead of 50%
                # Cross-character effect: buff all living allies
                for ally in party:
                    if ally != target and ally.hp > 0:
                        effect = StatEffect(
                            name=f"{self.id}_ally_atk_boost",
                            stat_modifiers={
                                "atk": 40,  # Prime: 40 instead of 10
                                "crit_rate": 0.05,  # Prime: Added crit rate bonus
                            },
                            duration=4,  # Prime: 4 turns instead of 3
                            source=self.id,
                        )
                        ally.add_effect(effect)

    async def on_turn_start(self, target, **kwargs) -> None:
        """Handle turn_start with prime dynamic behavior."""
        from autofighter.stat_effect import StatEffect

        party = kwargs.get('party', [])
        living_allies = sum(1 for ally in party if ally.hp > 0)

        if living_allies >= 2:  # Prime: Only need 2+ allies
            # Prime: Massive scaling
            bonus_damage = living_allies * 20  # Prime: 20 instead of 5
            effect = StatEffect(
                name=f"{self.id}_synergy_damage",
                stat_modifiers={
                    "atk": bonus_damage,
                    "defense": living_allies * 5,  # Prime: Added defense scaling
                },
                duration=1,
                source=self.id,
            )
            target.add_effect(effect)

    async def on_action_taken(self, target, **kwargs) -> None:
        """Build synergy stacks with prime bonuses."""
        from autofighter.stat_effect import StatEffect

        entity_id = id(target)
        current_stacks = AdvancedCombatSynergyPrime._synergy_stacks.get(entity_id, 0)

        if current_stacks < self.max_stacks:
            AdvancedCombatSynergyPrime._synergy_stacks[entity_id] = current_stacks + 1

            # Prime: Massive persistent effect
            stacks = AdvancedCombatSynergyPrime._synergy_stacks[entity_id]
            effect = StatEffect(
                name=f"{self.id}_persistent_buff",
                stat_modifiers={
                    "atk": stacks * 12,  # Prime: 12 instead of 3
                    "crit_rate": stacks * 0.03,  # Prime: 0.03 instead of 0.01
                    "crit_damage": stacks * 0.1,  # Prime: Added crit damage
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(effect)

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Grants allies +40 attack and +5% crit for 4 turns when hitting a foe below 60% HP. "
            "If 2+ allies are alive at turn start, gains +20 attack and +5 defense per ally for that turn. "
            "Each action builds up to 8 stacks, adding +12 attack, +3% crit rate, and +10% crit damage per stack."
        )
