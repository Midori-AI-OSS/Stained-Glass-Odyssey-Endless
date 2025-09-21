from dataclasses import dataclass
from dataclasses import field
from math import ceil
import random

from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task

# Global flag to prevent infinite echo loops
_echo_processing = False


@dataclass
class EchoingDrum(RelicBase):
    """First attack each battle has 25% per-stack odds to trigger Aftertaste."""

    id: str = "echoing_drum"
    name: str = "Echoing Drum"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "First attack each battle has 25% chance per stack to trigger Aftertaste "
        "(overflow converts every +100% into a guaranteed extra hit)."
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_echoing_drum_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {"stacks": stacks, "used": set()}
            party._echoing_drum_state = state
        else:
            state["stacks"] = stacks

        used: set[int] = state.setdefault("used", set())

        def _battle_start(*_args) -> None:
            used.clear()

        async def _attack(attacker, target, amount) -> None:
            global _echo_processing
            # Prevent infinite loops from recursive echo effects
            if _echo_processing:
                return

            pid = id(attacker)
            if pid in used:
                return
            if amount <= 0:
                return
            used.add(pid)
            current_state = getattr(party, "_echoing_drum_state", state)
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return

            total_chance = 25 * current_stacks
            guaranteed_hits = total_chance // 100
            remainder_chance = total_chance % 100
            remainder_triggered = False
            total_hits = int(guaranteed_hits)

            if remainder_chance and random.random() < remainder_chance / 100:
                remainder_triggered = True
                total_hits += 1

            if total_hits <= 0:
                return

            base_amount = float(amount)
            base_pot = max(1, int(ceil(base_amount / 0.8)))
            if base_pot <= 0:
                return

            effect = Aftertaste(hits=total_hits, base_pot=base_pot)

            # Set flag to prevent recursive echo effects
            _echo_processing = True
            try:
                await BUS.emit_async(
                    "relic_effect",
                    "echoing_drum",
                    attacker,
                    "aftertaste_trigger",
                    total_hits,
                    {
                        "original_amount": amount,
                        "total_chance": total_chance,
                        "guaranteed_hits": guaranteed_hits,
                        "remainder_chance": remainder_chance,
                        "remainder_triggered": remainder_triggered,
                        "stacks": current_stacks,
                        "target": getattr(target, "id", str(target)),
                        "base_pot": base_pot,
                    },
                )

                safe_async_task(effect.apply(attacker, target))
            finally:
                _echo_processing = False

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            used.clear()
            if getattr(party, "_echoing_drum_state", None) is state:
                delattr(party, "_echoing_drum_state")

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "action_used", _attack)
        self.subscribe(party, "attack_used", _attack)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        return self.about
