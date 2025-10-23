from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase

log = logging.getLogger(__name__)


@dataclass
class FeatherweightAnklet(RelicBase):
    """Early tempo relic: +2% SPD per stack permanent, +6% SPD per stack for 1 turn on first action."""

    id: str = "featherweight_anklet"
    name: str = "Featherweight Anklet"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"spd": 0.02})
    about: str = "+2% SPD per stack; First action each battle grants +6% SPD per stack for 1 turn"

    async def apply(self, party) -> None:
        await super().apply(party)

        # Track which members have received the first-action burst this battle
        state = getattr(party, "_featherweight_anklet_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {
                "stacks": stacks,
                "activated": set(),
            }
            party._featherweight_anklet_state = state
        else:
            state["stacks"] = stacks

        activated: set[int] = state.setdefault("activated", set())

        def _battle_start(*_args) -> None:
            """Reset activation tracking at battle start."""
            activated.clear()

        async def _action_used(actor, *_args) -> None:
            """Grant SPD burst on first action per ally per battle."""
            if actor is None or actor not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return

            pid = id(actor)
            if pid in activated:
                return

            activated.add(pid)
            current_state = getattr(party, "_featherweight_anklet_state", state)
            current_stacks = current_state.get("stacks", 0)

            if current_stacks <= 0:
                return

            # Get or create effect manager
            effect_manager = getattr(actor, "effect_manager", None)
            if effect_manager is None:
                effect_manager = EffectManager(actor)
                actor.effect_manager = effect_manager

            # Grant +6% SPD per stack for 1 turn
            spd_bonus = 0.06 * current_stacks
            spd_mod = create_stat_buff(
                actor,
                name=f"{self.id}_first_action",
                turns=1,
                spd_mult=1 + spd_bonus,
            )
            await effect_manager.add_modifier(spd_mod)

            log.debug(
                "Featherweight Anklet granted +%.1f%% SPD burst to %s for 1 turn",
                spd_bonus * 100,
                getattr(actor, "id", "member"),
            )

            # Emit telemetry for the burst
            await BUS.emit_async(
                "relic_effect",
                self.id,
                actor,
                "first_action_spd_burst",
                int(spd_bonus * 100),
                {
                    "spd_bonus_percent": spd_bonus * 100,
                    "duration": 1,
                    "stacks": current_stacks,
                    "permanent_spd_bonus": 2 * current_stacks,
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions at battle end."""
            self.clear_subscriptions(party)
            activated.clear()
            if getattr(party, "_featherweight_anklet_state", None) is state:
                delattr(party, "_featherweight_anklet_state")

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "action_used", _action_used)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return "+2% SPD; First action each battle grants +6% SPD for 1 turn"
        else:
            # Calculate multiplicative permanent bonus
            permanent_mult = (1.02**stacks - 1) * 100
            burst_bonus = 6 * stacks
            return (
                f"+{permanent_mult:.1f}% SPD ({stacks} stacks, multiplicative); "
                f"First action each battle grants +{burst_bonus}% SPD for 1 turn"
            )
