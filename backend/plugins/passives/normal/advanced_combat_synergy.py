from dataclasses import dataclass
from typing import ClassVar

from autofighter.stat_effect import StatEffect


@dataclass
class AdvancedCombatSynergy:
    """
    Advanced passive that demonstrates conditional triggers and cross-character effects.

    - On hit_landed: Grants temporary ATK bonus to allies if target is below 50% HP
    - On turn_start: Grants damage bonus if multiple allies are alive
    - On action_taken: Builds stacks that enhance party-wide effects
    """
    plugin_type = "passive"
    id = "advanced_combat_synergy"
    name = "Advanced Combat Synergy"
    trigger = ["hit_landed", "turn_start", "action_taken"]  # React to multiple events
    max_stacks = 3
    stack_display = "pips"

    # Class-level state for tracking synergy stacks per entity
    _synergy_stacks: ClassVar[dict[int, int]] = {}

    async def apply(self, target, **kwargs) -> None:
        """Handle event-based logic; currently only acts on hit_landed."""
        if kwargs.get("event") != "hit_landed":
            return

        hit_target = kwargs.get("hit_target")
        damage = kwargs.get("damage", 0)
        party = kwargs.get("party", [])

        if hit_target and damage > 0:
            # Conditional trigger: only activate if target is below 50% HP
            if hit_target.hp < (hit_target.max_hp * 0.5):
                # Cross-character effect: buff all living allies
                for ally in party:
                    if ally != target and ally.hp > 0:
                        effect = StatEffect(
                            name=f"{self.id}_ally_atk_boost",
                            stat_modifiers={"atk": 10},
                            duration=3,
                            source=self.id,
                        )
                        ally.add_effect(effect)

    async def on_turn_start(self, target, **kwargs) -> None:
        """Handle turn_start with dynamic behavior based on party state."""
        party = kwargs.get('party', [])
        living_allies = sum(1 for ally in party if ally.hp > 0)

        if living_allies >= 3:  # Only trigger with 3+ living allies
            # Dynamic passive: effect scales with number of living allies
            bonus_damage = living_allies * 5
            effect = StatEffect(
                name=f"{self.id}_synergy_damage",
                stat_modifiers={"atk": bonus_damage},
                duration=1,  # Just for this turn
                source=self.id,
            )
            target.add_effect(effect)

    async def on_action_taken(self, target, **kwargs) -> None:
        """Build synergy stacks on action taken."""
        entity_id = id(target)
        current_stacks = AdvancedCombatSynergy._synergy_stacks.get(entity_id, 0)

        if current_stacks < self.max_stacks:
            AdvancedCombatSynergy._synergy_stacks[entity_id] = current_stacks + 1

            # Apply persistent effect based on current stacks
            stacks = AdvancedCombatSynergy._synergy_stacks[entity_id]
            effect = StatEffect(
                name=f"{self.id}_persistent_buff",
                stat_modifiers={
                    "atk": stacks * 3,
                    "crit_rate": stacks * 0.01,
                },
                duration=-1,  # Permanent effect
                source=self.id,
            )
            target.add_effect(effect)

    @classmethod
    def get_stacks(cls, target) -> int:
        """Return current synergy stacks for display purposes."""
        return cls._synergy_stacks.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Grants allies +10 attack for 3 turns when hitting a foe below 50% HP. "
            "If 3+ allies are alive at turn start, gains +5 attack per ally for that turn. "
            "Each action builds up to 3 stacks, adding +3 attack and +1% crit rate per stack."
        )
