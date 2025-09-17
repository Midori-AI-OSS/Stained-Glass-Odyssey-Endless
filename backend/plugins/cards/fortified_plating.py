from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class FortifiedPlating(CardBase):
    id: str = "fortified_plating"
    name: str = "Fortified Plating"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.04})
    about: str = "+4% DEF; Reduce damage from the first hit each turn by 6%"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track which members have used their first hit reduction this turn
        first_hit_used = set()

        async def _on_damage_taken(target, attacker, damage):
            # Check if target is one of our party members
            if target in party.members:
                target_id = id(target)
                if target_id not in first_hit_used:
                    # Use the first hit reduction
                    first_hit_used.add(target_id)
                    damage_reduction = int(damage * 0.06)
                    if damage_reduction > 0:
                        # Add back the damage reduction to HP to simulate reduced damage
                        target.hp = min(target.hp + damage_reduction, getattr(target, 'max_hp', 1000))
                        import logging
                        log = logging.getLogger(__name__)
                        log.debug("Fortified Plating first hit reduction: +%d HP restored to %s", damage_reduction, target.id)
                        await BUS.emit_async("card_effect", self.id, target, "first_hit_reduction", damage_reduction, {
                            "damage_reduction": damage_reduction,
                            "reduction_percentage": 6,
                            "trigger_event": "first_hit_per_turn"
                        })

        def _on_turn_start():
            # Reset first hit usage at the start of each turn
            first_hit_used.clear()

        BUS.subscribe("damage_taken", _on_damage_taken)
        BUS.subscribe("turn_start", _on_turn_start)