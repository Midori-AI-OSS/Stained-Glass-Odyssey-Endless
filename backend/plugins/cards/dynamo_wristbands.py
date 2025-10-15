from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase

log = logging.getLogger(__name__)


@dataclass
class DynamoWristbands(CardBase):
    id: str = "dynamo_wristbands"
    name: str = "Dynamo Wristbands"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.03})
    about: str = "+3% ATK; When an ally deals Lightning damage, grant them +3% Crit Rate for 1 turn, stacking up to 2 times"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track current crit rate buff stacks per member
        active_stacks: dict[int, int] = {}

        async def _on_damage_dealt(
            attacker, target, damage, damage_type, source, source_action, action_name, details=None
        ):
            """Grant crit rate buff when ally deals Lightning damage."""
            # Check if attacker is one of our party members
            if attacker not in party.members:
                return

            # Check if this is Lightning damage
            damage_type_id = getattr(damage_type, "id", str(damage_type))
            if damage_type_id != "Lightning":
                return

            member_id = id(attacker)
            current_stacks = active_stacks.get(member_id, 0)

            # Don't stack beyond 2
            if current_stacks >= 2:
                return

            # Get or create effect manager
            effect_manager = getattr(attacker, "effect_manager", None)
            if effect_manager is None:
                effect_manager = EffectManager(attacker)
                attacker.effect_manager = effect_manager

            # Add new crit rate buff
            new_stacks = current_stacks + 1
            active_stacks[member_id] = new_stacks

            # Create crit rate buff (3% per stack)
            # Each buff is independent and lasts 1 turn
            crit_mod = create_stat_buff(
                attacker,
                name=f"{self.id}_crit_{new_stacks}",
                turns=1,
                crit_rate_mult=1.03,  # +3% crit rate
            )
            await effect_manager.add_modifier(crit_mod)

            log.debug(
                "Dynamo Wristbands granted +3%% crit rate to %s (stack %d/2)",
                getattr(attacker, "id", "member"),
                new_stacks,
            )

            # Emit telemetry for the buff
            await BUS.emit_async(
                "card_effect",
                self.id,
                attacker,
                "lightning_crit_buff",
                3,
                {
                    "crit_rate_bonus": 3,
                    "duration": 1,
                    "current_stacks": new_stacks,
                    "max_stacks": 2,
                    "damage_type": "Lightning",
                },
            )

        async def _on_turn_start(*_) -> None:
            """Reset stack tracking at the start of each turn since buffs expire."""
            active_stacks.clear()

        async def _on_battle_end(*_) -> None:
            """Clean up stack tracking at battle end."""
            active_stacks.clear()

        # Subscribe to relevant events
        self.subscribe("damage_dealt", _on_damage_dealt)
        self.subscribe("turn_start", _on_turn_start)
        self.subscribe("battle_end", _on_battle_end)
