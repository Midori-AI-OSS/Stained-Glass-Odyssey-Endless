"""Event Horizon relic: turn-start gravity pulses."""

from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class EventHorizon(RelicBase):
    """Detonate gravity pulses at the start of every ally turn."""

    id: str = "event_horizon"
    name: str = "Event Horizon"
    stars: int = 5
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "Detonates a gravity pulse at the start of every ally turn. Each pulse rips "
        "6% of current HP (minimum 1) from every living foe per stack, while draining "
        "the acting ally for 3% of their Max HP per stack. An all-or-nothing tempo engine."
    )

    async def apply(self, party) -> None:
        """Set up turn-start gravity pulse system."""
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_event_horizon_state", None)

        if state is None:
            state = {
                "stacks": stacks,
                "foes": [],
            }
            party._event_horizon_state = state
        else:
            state["stacks"] = stacks
            state["foes"].clear()

        async def _turn_start(entity) -> None:
            """Track foes and trigger gravity pulses on ally turns."""
            from plugins.characters._base import PlayerBase
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_event_horizon_state", state)
            current_stacks = current_state.get("stacks", 0)

            if current_stacks <= 0:
                return

            # Track foes when they start their turn
            if isinstance(entity, FoeBase):
                if entity not in current_state["foes"]:
                    current_state["foes"].append(entity)
                return

            # Only process gravity pulses for allies
            if not isinstance(entity, PlayerBase):
                return

            # Skip if ally has no HP
            if getattr(entity, "hp", 0) <= 0:
                return

            # Get living foes
            living_foes = [foe for foe in current_state["foes"] if getattr(foe, "hp", 0) > 0]

            # Skip if no living foes
            if not living_foes:
                return

            # Apply gravity damage to each living foe
            for foe in living_foes:
                foe_hp = getattr(foe, "hp", 0)
                foe_max_hp = getattr(foe, "max_hp", 1)

                if foe_hp <= 0 or foe_max_hp <= 0:
                    continue

                # Calculate 6% of foe's current HP per stack, minimum 1
                raw_damage = foe_hp * 0.06 * current_stacks
                damage = max(1, int(raw_damage))

                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    foe,
                    "gravity_pulse",
                    damage,
                    {
                        "stacks": current_stacks,
                        "foe_current_hp": foe_hp,
                        "foe_max_hp": foe_max_hp,
                        "damage_percentage": 6 * current_stacks,
                        "acting_ally": getattr(entity, "id", "unknown"),
                    },
                )

                # Apply damage with mitigation (use apply_damage)
                safe_async_task(foe.apply_damage(damage, attacker=entity))

            # Drain the acting ally
            ally_max_hp = getattr(entity, "max_hp", 0)
            if ally_max_hp > 0:
                self_drain = int(ally_max_hp * 0.03 * current_stacks)

                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    entity,
                    "self_drain",
                    self_drain,
                    {
                        "stacks": current_stacks,
                        "drain_percentage": 3 * current_stacks,
                        "max_hp": ally_max_hp,
                    },
                )

                if self_drain > 0:
                    safe_async_task(entity.apply_cost_damage(self_drain))

        def _battle_end(_entity) -> None:
            """Clear foe cache and clean up subscriptions."""
            current_state = getattr(party, "_event_horizon_state", None)
            if current_state is not None:
                current_state["foes"].clear()

        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        """Return a stack-aware description."""
        foe_damage_pct = 6 * stacks
        self_drain_pct = 3 * stacks
        return (
            f"Every ally turn detonates a gravity pulse: {foe_damage_pct}% of each foe's current HP "
            f"(minimum {stacks}) to all living foes, then drains {self_drain_pct}% of the acting ally's Max HP."
        )
