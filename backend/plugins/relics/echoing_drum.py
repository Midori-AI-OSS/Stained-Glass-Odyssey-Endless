from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class EchoingDrum(RelicBase):
    """First attack each battle repeats at 25% power per stack."""

    id: str = "echoing_drum"
    name: str = "Echoing Drum"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "First attack each battle repeats at 25% power per stack."

    def apply(self, party) -> None:
        super().apply(party)

        used: set[int] = set()

        def _battle_start(*args) -> None:
            used.clear()

        def _attack(attacker, target, amount) -> None:
            pid = id(attacker)
            if pid in used:
                return
            used.add(pid)
            stacks = party.relics.count(self.id)
            dmg = int(amount * 0.25 * stacks)

            # Emit relic effect event for echo attack
            BUS.emit(
                "relic_effect",
                "echoing_drum",
                attacker,
                "echo_attack",
                dmg,
                {
                    "original_amount": amount,
                    "echo_percentage": 25 * stacks,
                    "target": getattr(target, "id", str(target)),
                    "first_attack": True,
                    "stacks": stacks,
                },
            )

            safe_async_task(target.apply_damage(dmg, attacker=attacker))

        BUS.subscribe("battle_start", _battle_start)
        BUS.subscribe("action_used", _attack)

    def describe(self, stacks: int) -> str:
        pct = 25 * stacks
        return f"First attack each battle repeats at {pct}% power."
