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

        state = getattr(party, "_echoing_drum_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            used: set[int] = set()

            def _battle_start(*_args) -> None:
                used.clear()

            def _attack(attacker, target, amount) -> None:
                pid = id(attacker)
                if pid in used:
                    return
                used.add(pid)
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                dmg = int(amount * 0.25 * current_stacks)

                # Emit relic effect event for echo attack
                BUS.emit("relic_effect", "echoing_drum", attacker, "echo_attack", dmg, {
                    "original_amount": amount,
                    "echo_percentage": 25 * current_stacks,
                    "target": getattr(target, 'id', str(target)),
                    "first_attack": True,
                    "stacks": current_stacks
                })

                safe_async_task(target.apply_damage(dmg, attacker=attacker))

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("battle_start", state["battle_start_handler"])
                BUS.unsubscribe("action_used", state["attack_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                used.clear()
                if getattr(party, "_echoing_drum_state", None) is state:
                    delattr(party, "_echoing_drum_state")

            state = {
                "stacks": stacks,
                "used": used,
                "battle_start_handler": _battle_start,
                "attack_handler": _attack,
                "cleanup_handler": _cleanup,
            }
            party._echoing_drum_state = state

            BUS.subscribe("battle_start", _battle_start)
            BUS.subscribe("action_used", _attack)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks

    def describe(self, stacks: int) -> str:
        pct = 25 * stacks
        return f"First attack each battle repeats at {pct}% power."
