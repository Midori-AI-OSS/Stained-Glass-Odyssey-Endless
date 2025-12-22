from dataclasses import dataclass, field

from plugins.relics._base import RelicBase, safe_async_task


@dataclass
class ThreadbareCloak(RelicBase):
    """Start battle with a small shield equal to 3% Max HP per stack."""

    id: str = "threadbare_cloak"
    name: str = "Threadbare Cloak"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = "At battle start, all allies gain a shield equal to 3% Max HP per relic stack. Shields stack additively with multiple copies."
    summarized_about: str = "Grants shield at battle start based on max hp"

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
            self.clear_subscriptions(party)

        self.subscribe(party, "battle_end", _reset)

    def describe(self, stacks: int) -> str:
        pct = 3 * stacks
        return f"Allies start battle with a shield equal to {pct}% Max HP."
