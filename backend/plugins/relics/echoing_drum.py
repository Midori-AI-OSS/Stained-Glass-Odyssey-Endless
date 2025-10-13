from dataclasses import dataclass
from dataclasses import field
from math import ceil
import random

from autofighter.stat_effect import StatEffect
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
    about: str = "First attack each battle gains +25% Aftertaste chance per stack; every full 100% guarantees another hit."

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

            if attacker is None or attacker not in getattr(party, "members", ()):  # type: ignore[arg-type]
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

            base_atk = int(attacker.get_base_stat("atk"))
            buff_amount = int(base_atk * 1.5 * current_stacks)
            if buff_amount > 0:
                buff_effect = StatEffect(
                    name=f"{self.id}_aftertaste_atk_buff",
                    stat_modifiers={"atk": buff_amount},
                    duration=5,
                    source=self.id,
                )
                attacker.add_effect(buff_effect)
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    attacker,
                    "aftertaste_attack_buff",
                    buff_amount,
                    {
                        "stacks": current_stacks,
                        "buff_amount": buff_amount,
                        "base_atk": base_atk,
                        "target": getattr(attacker, "id", str(attacker)),
                        "duration": 5,
                    },
                )

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
                        "effect_label": "aftertaste",
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

        def _on_defeat(entity, *_args) -> None:
            if entity in getattr(party, "members", ()):  # type: ignore[arg-type]
                used.discard(id(entity))

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "action_used", _attack)
        self.subscribe(party, "attack_used", _attack)
        self.subscribe(party, "entity_defeat", _on_defeat)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        total_chance = max(0, 25 * stacks)
        guaranteed_hits = total_chance // 100
        remainder = total_chance % 100

        stack_text = "stack" if stacks == 1 else "stacks"

        guaranteed_text = (
            f"{guaranteed_hits} guaranteed extra hit"
            f"{'s' if guaranteed_hits != 1 else ''}"
            if guaranteed_hits
            else "no guaranteed extra hits"
        )
        overflow_text = (
            f"{remainder}% overflow chance"
            if remainder
            else "no overflow chance"
        )

        chance_sentence = (
            "Aftertaste: "
            f"{total_chance}% total chance (25% per stack, {stacks} {stack_text}); "
            f"{guaranteed_text}; {overflow_text}."
        )

        buff_percentage = 150 * stacks
        buff_sentence = (
            "ATK buff: "
            f"+{buff_percentage}% base ATK for 5 turns after it triggers."
        )

        return f"{chance_sentence} {buff_sentence}"
