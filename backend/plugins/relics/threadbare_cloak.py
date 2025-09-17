from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class ThreadbareCloak(RelicBase):
    """Start battle with a small shield equal to 3% Max HP per stack."""

    id: str = "threadbare_cloak"
    name: str = "Threadbare Cloak"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Start battle with a small shield equal to 3% Max HP per stack."

    async def apply(self, party) -> None:
        await super().apply(party)

        applied = getattr(party, "_threadbare_cloak_stacks", 0)
        stacks = party.relics.count(self.id)
        additional = stacks - applied
        if additional <= 0:
            return

        for member in party.members:
            member.enable_overheal()  # Enable shields for this member
            shield = int(member.max_hp * 0.03 * additional)
            safe_async_task(member.apply_healing(shield))

        party._threadbare_cloak_stacks = stacks

        def _reset(*_: object) -> None:
            party._threadbare_cloak_stacks = 0
            BUS.unsubscribe("battle_end", _reset)

        BUS.subscribe("battle_end", _reset)

    def describe(self, stacks: int) -> str:
        pct = 3 * stacks
        return f"Allies start battle with a shield equal to {pct}% Max HP."
