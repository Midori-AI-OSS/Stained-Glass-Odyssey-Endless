from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class PocketManual(RelicBase):
    """+3% damage; every 10th hit deals 3% extra Aftertaste damage."""

    id: str = "pocket_manual"
    name: str = "Pocket Manual"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.03})
    about: str = (
        "+3% damage; every 10th hit triggers an additional Aftertaste hit dealing +3% of the original damage."
    )

    def apply(self, party) -> None:
        super().apply(party)

        counts: dict[int, int] = {}

        def _hit(
            attacker, target, amount, source_type="attack", source_name=None
        ) -> None:
            # Only trigger if the attacker is a party member
            if attacker not in party.members:
                return

            pid = id(attacker)
            counts[pid] = counts.get(pid, 0) + 1
            if counts[pid] % 10 == 0:
                base = int(amount * 0.03)
                if base > 0:
                    # Emit relic effect event
                    BUS.emit(
                        "relic_effect",
                        "pocket_manual",
                        attacker,
                        "trigger_aftertaste",
                        base,
                        {
                            "hit_count": counts[pid],
                            "original_damage": amount,
                            "aftertaste_damage": base,
                        },
                    )

                    effect = Aftertaste(base_pot=base)
                    safe_async_task(effect.apply(attacker, target))

        BUS.subscribe("hit_landed", _hit)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return "+3% damage; every 10th hit triggers an additional Aftertaste hit dealing +3% of the original damage."
        else:
            # Stacks are multiplicative: each copy compounds the effect
            total_dmg_mult = (1.03**stacks - 1) * 100
            aftertaste_dmg = (
                3 * stacks
            )  # This part still stacks additively for the special effect
            return f"+{total_dmg_mult:.1f}% damage ({stacks} stacks, multiplicative); every 10th hit triggers an additional Aftertaste hit dealing +{aftertaste_dmg}% of the original damage."
