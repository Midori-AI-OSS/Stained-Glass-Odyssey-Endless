"""Simple action queue based on Speed (SPD) stats."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from .stats import GAUGE_START
from .stats import Stats

TURN_COUNTER_ID = "turn_counter"


@dataclass
class ActionQueue:
    """Maintain turn order using an Action Gauge system.

    Each combatant starts with an action gauge of ``GAUGE_START``.  A combatant's
    base action value (AV) is ``GAUGE_START / SPD``.  During each step the actor
    with the lowest current AV takes a turn.  The amount of AV spent is deducted
    from every other combatant's AV, and the actor's AV is reset to its base
    value.
    """

    combatants: list[Stats] = field(default_factory=list)
    bonus_actors: list[Stats] = field(default_factory=list)
    turn_counter: Stats | None = field(default=None, init=False)
    last_cycle_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.turn_counter = None
        for combatant in self.combatants:
            if getattr(combatant, "id", None) == TURN_COUNTER_ID:
                self.turn_counter = combatant
            combatant.action_gauge = GAUGE_START
            if combatant is self.turn_counter:
                base = float(GAUGE_START)
                combatant.base_action_value = base
                combatant.action_value = base
                continue
            base = GAUGE_START / max(combatant.spd, 1)
            combatant.base_action_value = base
            combatant.action_value = base

    def grant_extra_turn(self, actor: Stats) -> None:
        """Queue ``actor`` for an immediate bonus turn."""
        if actor is self.turn_counter:
            return
        if actor not in self.bonus_actors:
            self.bonus_actors.append(actor)

    def next_actor(self) -> Stats:
        """Return the combatant with the lowest action value and advance time."""
        if self.bonus_actors:
            self.last_cycle_count = 0
            return self.bonus_actors.pop(0)

        available_indices = [
            index
            for index, combatant in enumerate(self.combatants)
            if combatant is not self.turn_counter
        ]
        if not available_indices:
            raise RuntimeError("ActionQueue has no combatants to act")

        actor_index = min(
            available_indices,
            key=lambda i: getattr(self.combatants[i], "action_value", GAUGE_START),
        )
        actor = self.combatants[actor_index]
        self.advance_with_actor(actor)
        return actor

    def snapshot(self) -> list[dict[str, float]]:
        """Return queue state for serialization."""
        ordered = sorted(self.combatants, key=lambda c: c.action_value)
        extras = [
            {
                "id": getattr(c, "id", ""),
                "action_gauge": c.action_gauge,
                "action_value": c.action_value,
                "base_action_value": c.base_action_value,
                "bonus": True,
            }
            for c in self.bonus_actors
        ]
        return extras + [
            {
                "id": getattr(c, "id", ""),
                "action_gauge": c.action_gauge,
                "action_value": c.action_value,
                "base_action_value": c.base_action_value,
            }
            for c in ordered
        ]

    def advance_with_actor(self, actor: Stats) -> int:
        """Advance the queue math using the provided actor.

        This mirrors ``next_actor`` time advancement but does not select the
        actor by min action value. It allows external battle loops to drive the
        visual/action gauge independently while preserving consistent queue
        dynamics for snapshots.
        """
        if actor not in self.combatants:
            self.last_cycle_count = 0
            return 0
        try:
            spent_raw = getattr(actor, "action_value", None)
            if spent_raw is None:
                spent_raw = getattr(actor, "base_action_value", GAUGE_START)
            spent = float(spent_raw)
            if spent <= 0:
                spent = float(getattr(actor, "base_action_value", GAUGE_START))
            if spent <= 0:
                self.last_cycle_count = 0
                return 0
            cycle_count = self._update_turn_counter(spent)
            for combatant in self.combatants:
                if combatant is actor or combatant is self.turn_counter:
                    continue
                current_value = float(getattr(combatant, "action_value", 0.0))
                combatant.action_value = max(0.0, current_value - spent)
            actor.action_value = float(getattr(actor, "base_action_value", GAUGE_START))
            # Rotate actor to end to reflect moving to the back of the line
            idx = self.combatants.index(actor)
            self.combatants.append(self.combatants.pop(idx))
            self.last_cycle_count = cycle_count
            return cycle_count
        except Exception:
            # Best-effort; never let UI queue progression break battle logic
            self.last_cycle_count = 0
            return 0

    def _update_turn_counter(self, spent: float) -> int:
        """Apply time advancement to the shared turn counter."""

        turn_counter = self.turn_counter
        if turn_counter is None:
            return 0

        try:
            current_value = float(getattr(turn_counter, "action_value", GAUGE_START))
        except Exception:
            current_value = float(GAUGE_START)

        new_value = current_value - spent
        if new_value > 0:
            turn_counter.action_value = new_value
            try:
                turn_counter.action_gauge = int(max(new_value, 0.0))
            except Exception:
                turn_counter.action_gauge = GAUGE_START
            return 0

        overspend = -new_value
        try:
            cycles = int(overspend // GAUGE_START) + 1
        except Exception:
            cycles = 1

        leftover = overspend % GAUGE_START
        turn_counter.action_value = float(GAUGE_START)
        turn_counter.base_action_value = float(GAUGE_START)
        turn_counter.action_gauge = GAUGE_START
        if leftover > 0:
            remaining = GAUGE_START - leftover
            turn_counter.action_value = float(remaining)
            try:
                turn_counter.action_gauge = int(max(remaining, 0))
            except Exception:
                turn_counter.action_gauge = GAUGE_START
        return cycles
