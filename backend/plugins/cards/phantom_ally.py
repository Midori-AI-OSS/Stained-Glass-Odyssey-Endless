from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from autofighter.summons.manager import SummonManager
from plugins.cards._base import CardBase


@dataclass
class PhantomAlly(CardBase):
    id: str = "phantom_ally"
    name: str = "Phantom Ally"
    stars: int = 5
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 15.0})
    about: str = (
        "+1500% ATK; on the first turn, summon a permanent copy of a random ally."
    )

    async def apply(self, party):
        await super().apply(party)
        if not party.members:
            return

        # Choose a random ally to create a phantom of
        original = random.choice(party.members)
        summoner_id = getattr(original, "id", str(id(original)))

        # Prevent multiple concurrent phantoms - replace only when existing ones are failing
        active_summons = SummonManager.get_summons(summoner_id)
        active_phantoms = [
            summon
            for summon in active_summons
            if getattr(summon, "summon_source", "") == self.id
        ]
        if active_phantoms:
            phantom_viable = any(
                SummonManager.evaluate_summon_viability(phantom)["viable"]
                for phantom in active_phantoms
            )
            if phantom_viable:
                return
            for phantom in active_phantoms:
                SummonManager.remove_summon(phantom, "phantom_ally_replaced")
                if phantom in party.members:
                    party.members.remove(phantom)

        phantom_slot_tracker = "_phantom_ally_temp_slots"
        existing_slot_allocation = max(
            0, int(getattr(original, phantom_slot_tracker, 0))
        )
        slots_added_this_cast = 0
        if hasattr(original, "add_temporary_summon_slots"):
            additional_needed = max(0, 1 - existing_slot_allocation)
            if additional_needed > 0:
                original.add_temporary_summon_slots(additional_needed)
                slots_added_this_cast = additional_needed
                setattr(
                    original,
                    phantom_slot_tracker,
                    existing_slot_allocation + additional_needed,
                )

        # Create phantom using the new summons system
        # Phantoms are full-strength copies (multiplier=1.0) that last the entire battle
        summon = SummonManager.create_summon(
            summoner=original,
            summon_type="phantom",
            source=self.id,
            stat_multiplier=1.0,  # Full strength copy
            turns_remaining=-1,  # Lasts the entire battle
        )

        if not summon:
            if (
                slots_added_this_cast > 0
                and hasattr(original, "remove_temporary_summon_slots")
            ):
                original.remove_temporary_summon_slots(slots_added_this_cast)
                setattr(original, phantom_slot_tracker, existing_slot_allocation)
            return

        # Add the summon to the party for this battle
        party.members.append(summon)

        # Track phantom ally summoning
        await BUS.emit_async("card_effect", "phantom_ally", original, "phantom_summoned", 1, {
            "original_ally": getattr(original, 'id', str(original)),
            "phantom_id": summon.id,
            "phantom_stats": {
                "hp": summon.hp,
                "max_hp": summon.max_hp,
                "atk": summon.atk,
                "defense": summon.defense,
                "crit_rate": summon.crit_rate,
                "crit_damage": summon.crit_damage,
                "effect_hit_rate": summon.effect_hit_rate,
                "effect_resistance": summon.effect_resistance,
                "mitigation": summon.mitigation,
                "vitality": summon.vitality,
                "dodge_odds": summon.dodge_odds,
                "regain": summon.regain,
                "damage_type": getattr(summon.damage_type, 'id', 'Generic'),
                "ultimate_charge": summon.ultimate_charge,
                "level": summon.level,
                "actions_per_turn": summon.actions_per_turn
            },
            "atk_bonus_applied": 1500
        })

        # Register cleanup handler to remove from party when battle ends
        async def _cleanup(_entity):
            if summon in party.members:
                party.members.remove(summon)
                # Track phantom cleanup
                await BUS.emit_async("card_effect", "phantom_ally", summon, "phantom_dismissed", 1, {
                    "reason": "battle_end",
                    "original_ally": getattr(original, 'id', str(original))
                })
            if slots_added_this_cast > 0 and hasattr(
                original, "remove_temporary_summon_slots"
            ):
                original.remove_temporary_summon_slots(slots_added_this_cast)
                setattr(
                    original,
                    phantom_slot_tracker,
                    max(
                        0,
                        int(getattr(original, phantom_slot_tracker, 0))
                        - slots_added_this_cast,
                    ),
                )
            else:
                remaining_phantoms = any(
                    getattr(other, "summon_source", "") == self.id
                    for other in SummonManager.get_summons(summoner_id)
                    if other is not summon
                )
                if not remaining_phantoms:
                    setattr(original, phantom_slot_tracker, 0)
            SummonManager.remove_summon(summon, "phantom_ally_cleanup")
            self.cleanup_subscriptions()

        self.subscribe("battle_end", _cleanup)
