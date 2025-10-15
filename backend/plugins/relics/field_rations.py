from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.stats import BUS
from plugins.relics._base import RelicBase

log = logging.getLogger(__name__)


@dataclass
class FieldRations(RelicBase):
    """Post-battle recovery: heal 2% Max HP per stack and grant +1 ultimate charge per stack."""

    id: str = "field_rations"
    name: str = "Field Rations"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "After each battle, heal 2% Max HP per stack and grant +1 ultimate charge per stack to all allies"

    async def apply(self, party) -> None:
        await super().apply(party)

        async def _battle_end(*_args) -> None:
            """Apply post-battle healing and ultimate charge to all party members."""
            current_stacks = party.relics.count(self.id)

            if current_stacks <= 0:
                return

            # Apply healing and ultimate charge to each party member
            for member in party.members:
                # Skip dead members
                if getattr(member, "hp", 0) <= 0:
                    continue

                # Calculate healing: 2% Max HP per stack
                max_hp = getattr(member, "max_hp", 1)
                heal_amount = int(max_hp * 0.02 * current_stacks)

                if heal_amount > 0:
                    # Apply healing
                    await member.apply_healing(
                        heal_amount, healer=member, source_type="relic", source_name=self.id
                    )

                    log.debug(
                        "Field Rations healed %s for %d HP (%d stacks)",
                        getattr(member, "id", "member"),
                        heal_amount,
                        current_stacks,
                    )

                # Grant ultimate charge: +1 per stack
                charge_amount = current_stacks

                # Use add_ultimate_charge to properly set ultimate_ready flag
                member.add_ultimate_charge(charge_amount)

                log.debug(
                    "Field Rations granted %d ultimate charge to %s (now %d/%d)",
                    charge_amount,
                    getattr(member, "id", "member"),
                    member.ultimate_charge,
                    member.ultimate_charge_max,
                )

                # Emit telemetry for the post-battle recovery
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "post_battle_recovery",
                    heal_amount,
                    {
                        "heal_amount": heal_amount,
                        "ultimate_charge_granted": charge_amount,
                        "stacks": current_stacks,
                        "new_ultimate_charge": member.ultimate_charge,
                        "ultimate_charge_capacity": member.ultimate_charge_max,
                        "ultimate_ready": member.ultimate_ready,
                    },
                )

        self.subscribe(party, "battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return "After each battle, heal 2% Max HP and grant +1 ultimate charge to all allies"
        else:
            heal_percent = 2 * stacks
            charge_amount = stacks
            return (
                f"After each battle, heal {heal_percent}% Max HP and grant +{charge_amount} "
                f"ultimate charge to all allies ({stacks} stacks)"
            )
