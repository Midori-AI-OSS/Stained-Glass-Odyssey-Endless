from dataclasses import dataclass, field

from autofighter.effects import EffectManager, create_stat_buff
from plugins.relics._base import RelicBase


@dataclass
class GuardianCharm(RelicBase):
    """At battle start, grants +20% DEF to the lowest-HP ally."""

    id: str = "guardian_charm"
    name: str = "Guardian Charm"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "At the start of each battle, identifies the party member with the lowest current HP "
        "and grants them +20% DEF per stack for the entire battle (9999 turns). The buff is "
        "permanent for that battle and stacks multiply the effect (e.g., 2 stacks = +40% DEF, "
        "3 stacks = +60% DEF). Great for protecting vulnerable low-HP characters."
    )
    summarized_about: str = (
        "Grants def bonus to lowest-HP ally at battle start"
    )

    async def apply(self, party) -> None:
        from autofighter.stats import BUS  # Import here to avoid circular imports

        await super().apply(party)
        if not party.members:
            return
        member = min(party.members, key=lambda m: m.hp)
        stacks = party.relics.count(self.id)
        defense_pct = 20 * stacks

        # Emit relic effect event for defense boost
        await BUS.emit_async(
            "relic_effect",
            "guardian_charm",
            member,
            "defense_boost",
            defense_pct,
            {
                "target_selection": "lowest_hp",
                "defense_percentage": defense_pct,
                "target_hp": member.hp,
                "target_max_hp": member.max_hp,
                "stacks": stacks,
            },
        )

        mgr = getattr(member, "effect_manager", None)
        if mgr is None:
            mgr = EffectManager(member)
            member.effect_manager = mgr

        mod = create_stat_buff(
            member,
            name=self.id,
            defense_mult=1 + 0.2 * stacks,
            turns=9999,
        )
        await mgr.add_modifier(mod)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        pct = 20 * stacks
        return f"At battle start, grants +{pct}% DEF to the lowest-HP ally."
