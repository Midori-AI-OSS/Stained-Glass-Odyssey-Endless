from dataclasses import dataclass, field

from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.relics._base import RelicBase, safe_async_task


@dataclass
class FrostSigil(RelicBase):
    """Hits apply chill dealing 5% ATK as Aftertaste; each stack adds a hit."""

    id: str = "frost_sigil"
    name: str = "Frost Sigil"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "When allies land hits, apply chill dealing 5% of attacker's ATK as Aftertaste damage. "
        "Number of Aftertaste hits equals number of stacks."
    )
    summarized_about: str = "Hits apply chill dealing aftertaste damage based on atk"

    async def apply(self, party) -> None:
        await super().apply(party)

        party._frost_sigil_state = True

        async def _hit(attacker, target, amount, source_type="attack", source_name=None) -> None:
            # Only trigger if the attacker is a party member
            if attacker not in party.members:
                return

            stacks = party.relics.count(self.id)
            dmg = int(attacker.atk * 0.05)

            # Track frost sigil application
            await BUS.emit_async("relic_effect", "frost_sigil", attacker, "chill_applied", dmg, {
                "target": getattr(target, 'id', str(target)),
                "aftertaste_hits": stacks,
                "damage_per_hit": dmg,
                "atk_percentage": 5,
                "attacker_atk": attacker.atk,
                "trigger": "hit_landed"
            })

            safe_async_task(
                Aftertaste(base_pot=dmg, hits=stacks).apply(attacker, target)
            )

        self.subscribe(party, "hit_landed", _hit)

    def describe(self, stacks: int) -> str:
        hit_word = "hit" if stacks == 1 else "hits"
        return f"Hits apply chill dealing 5% ATK as Aftertaste {stacks} {hit_word}."
