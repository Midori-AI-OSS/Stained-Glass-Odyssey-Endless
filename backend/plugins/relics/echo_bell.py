from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task

# Global flag to prevent infinite echo loops
_echo_processing = False


@dataclass
class EchoBell(RelicBase):
    """First action each battle repeats at 15% power per stack."""

    id: str = "echo_bell"
    name: str = "Echo Bell"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "First action each battle repeats at 15% power per stack."

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_echo_bell_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {
                "stacks": stacks,
                "used": set(),
            }
            party._echo_bell_state = state
        else:
            state["stacks"] = stacks

        used: set[int] = state.setdefault("used", set())

        def _battle_start(*_args) -> None:
            used.clear()

        async def _action(actor, target, amount, action_type="damage") -> None:
            global _echo_processing
            # Prevent infinite loops from recursive echo effects
            if _echo_processing:
                return

            pid = id(actor)
            if pid in used:
                return
            used.add(pid)
            current_state = getattr(party, "_echo_bell_state", state)
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return

            # Set flag to prevent recursive echo effects
            _echo_processing = True
            try:
                echo_amount = int(amount * 0.15 * current_stacks)

                # Emit relic effect event for echo action
                await BUS.emit_async("relic_effect", "echo_bell", actor, "echo_action", echo_amount, {
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
            finally:
                _echo_processing = False

        async def _healing(actor, target, amount) -> None:
            await _action(actor, target, amount, "healing")

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            used.clear()
            if getattr(party, "_echo_bell_state", None) is state:
                delattr(party, "_echo_bell_state")

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "action_used", _action)
        self.subscribe(party, "healing_used", _healing)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        pct = 15 * stacks
        return f"First action each battle repeats at {pct}% power."
