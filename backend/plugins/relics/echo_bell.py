from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class EchoBell(RelicBase):
    """First action each battle repeats at 15% power per stack."""

    id: str = "echo_bell"
    name: str = "Echo Bell"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "First action each battle repeats at 15% power per stack."

    def apply(self, party) -> None:
        super().apply(party)

        state = getattr(party, "_echo_bell_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            used: set[int] = set()

            def _battle_start(*_args) -> None:
                used.clear()

            def _action(actor, target, amount, action_type="damage") -> None:
                pid = id(actor)
                if pid in used:
                    return
                used.add(pid)
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                echo_amount = int(amount * 0.15 * current_stacks)

                # Emit relic effect event for echo action
                BUS.emit("relic_effect", "echo_bell", actor, "echo_action", echo_amount, {
                    "original_amount": amount,
                    "echo_percentage": 15 * current_stacks,
                    "target": getattr(target, 'id', str(target)),
                    "first_action": True,
                    "action_type": action_type,
                    "stacks": current_stacks
                })

                # Echo the same type of action - damage or healing
                if action_type == "healing":
                    safe_async_task(target.apply_healing(echo_amount, healer=actor))
                else:
                    safe_async_task(target.apply_damage(echo_amount, attacker=actor))

            def _healing(actor, target, amount) -> None:
                _action(actor, target, amount, "healing")

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("battle_start", state["battle_start_handler"])
                BUS.unsubscribe("action_used", state["action_handler"])
                BUS.unsubscribe("healing_used", state["healing_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                used.clear()
                if getattr(party, "_echo_bell_state", None) is state:
                    delattr(party, "_echo_bell_state")

            state = {
                "stacks": stacks,
                "used": used,
                "battle_start_handler": _battle_start,
                "action_handler": _action,
                "healing_handler": _healing,
                "cleanup_handler": _cleanup,
            }
            party._echo_bell_state = state

            BUS.subscribe("battle_start", _battle_start)
            BUS.subscribe("action_used", _action)
            BUS.subscribe("healing_used", _healing)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks

    def describe(self, stacks: int) -> str:
        pct = 15 * stacks
        return f"First action each battle repeats at {pct}% power."
