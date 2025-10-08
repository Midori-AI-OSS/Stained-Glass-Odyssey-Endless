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
                self._sync_action_gauge(combatant, base)
                continue
            base = GAUGE_START / max(combatant.spd, 1)
            combatant.base_action_value = base
            combatant.action_value = base
            self._sync_action_gauge(combatant, base)
        self._stabilize_action_values()

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
            key=lambda i: self._sort_key(
                self.combatants[i],
                fallback_index=i,
            ),
        )
        actor = self.combatants[actor_index]
        self.advance_with_actor(actor)
        return actor

    def snapshot(self) -> list[dict[str, float]]:
        """Return queue state for serialization."""
        ordered = sorted(self.combatants, key=self._sort_key)
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
            gauge_step = 1.0
            remaining = float(spent)
            cycle_count = 0
            others = [
                combatant
                for combatant in self.combatants
                if combatant is not actor and combatant is not self.turn_counter
            ]
            while remaining > 1e-9:
                step = gauge_step if remaining >= gauge_step else remaining
                for combatant in others:
                    current_value = float(getattr(combatant, "action_value", 0.0))
                    new_value = current_value - step
                    if new_value < 0.0:
                        new_value = 0.0
                    combatant.action_value = new_value
                    self._sync_action_gauge(combatant, new_value)
                cycle_count += self._update_turn_counter(step)
                remaining -= step

            base_value = float(getattr(actor, "base_action_value", GAUGE_START))
            actor.action_value = base_value
            self._sync_action_gauge(actor, base_value)
            # Rotate actor to end to reflect moving to the back of the line
            idx = self.combatants.index(actor)
            self.combatants.append(self.combatants.pop(idx))
            self._stabilize_action_values()
            self.last_cycle_count = cycle_count
            return cycle_count
        except Exception:
            # Best-effort; never let UI queue progression break battle logic
            self.last_cycle_count = 0
            return 0

    def _sort_key(
        self,
        combatant: Stats,
        *,
        fallback_index: int | None = None,
    ) -> tuple[float, float, str]:
        """Return the ordering key for ``combatant`` in the queue."""

        try:
            value = float(getattr(combatant, "action_value", 0.0))
        except Exception:
            value = 0.0
        if value < 0.0:
            value = 0.0

        try:
            offset = float(getattr(combatant, "_action_sort_offset"))
        except Exception:
            if fallback_index is None:
                try:
                    fallback_index = self.combatants.index(combatant)
                except ValueError:
                    fallback_index = 0
            offset = float(fallback_index)

        identifier = getattr(combatant, "id", "")
        return (value, offset, identifier)

    def _update_turn_counter(self, spent: float) -> int:
        """Apply time advancement to the shared turn counter."""

        turn_counter = self.turn_counter
        if turn_counter is None:
            return 0

        try:
            current_value = float(getattr(turn_counter, "action_value", GAUGE_START))
        except Exception:
            current_value = float(GAUGE_START)

        if spent <= 0:
            return 0

        new_value = current_value - spent
        if new_value > 0:
            turn_counter.action_value = new_value
            self._sync_action_gauge(turn_counter, new_value)
            return 0

        overspend = -new_value
        reset_value = float(GAUGE_START)
        turn_counter.base_action_value = reset_value
        turn_counter.action_value = reset_value
        self._sync_action_gauge(turn_counter, reset_value)

        if overspend > 0:
            return 1 + self._update_turn_counter(overspend)
        return 1

    def _stabilize_action_values(self) -> None:
        """Ensure non-turn counter combatants have unique action values."""

        for index, combatant in enumerate(self.combatants):
            if combatant is self.turn_counter:
                continue
            if getattr(combatant, "id", None) == TURN_COUNTER_ID:
                continue

            try:
                value = float(getattr(combatant, "action_value", 0.0))
            except Exception:
                value = 0.0
            if value < 0.0:
                value = 0.0

            try:
                setattr(combatant, "_action_sort_offset", float(index))
            except Exception:
                pass

            self._sync_action_gauge(combatant, value)

    def _sync_action_gauge(self, combatant: Stats, new_value: float) -> None:
        """Mirror ``action_value`` changes onto the combatant's gauge field."""

        try:
            combatant.action_gauge = float(max(new_value, 0.0))
        except Exception:
            try:
                combatant.action_gauge = GAUGE_START
            except Exception:
                pass
