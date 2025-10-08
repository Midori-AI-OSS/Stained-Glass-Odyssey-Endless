import asyncio
import math

import pytest

from autofighter.action_queue import TURN_COUNTER_ID
from autofighter.action_queue import ActionQueue
from autofighter.rooms.battle.progress import build_action_queue_snapshot
from autofighter.stats import Stats


def test_speed_ordering_and_reset():
    a = Stats()
    a.id = "a"
    a.spd = 200  # base AV 50
    b = Stats()
    b.id = "b"
    b.spd = 100  # base AV 100
    q = ActionQueue([a, b])

    first = q.next_actor()
    assert first is a
    assert a.action_value == pytest.approx(a.base_action_value, abs=1e-6)
    assert a.action_gauge == pytest.approx(a.action_value, abs=1e-6)
    assert b.action_value == pytest.approx(
        b.base_action_value - a.base_action_value,
        abs=1.0,
    )
    assert b.action_gauge == pytest.approx(b.action_value, abs=1e-6)

    second = q.next_actor()
    assert second is b
    assert b.action_value == pytest.approx(b.base_action_value, abs=1.0)
    assert b.action_gauge == pytest.approx(b.action_value, abs=1e-6)
    assert a.action_value == pytest.approx(0.0, abs=1.0)
    assert a.action_gauge == pytest.approx(a.action_value, abs=1e-6)

    snap = q.snapshot()
    assert [e["id"] for e in snap] == ["a", "b"]
    for entry in snap:
        assert entry["action_gauge"] == pytest.approx(entry["action_value"], abs=1e-6)


def test_bonus_turn():
    a = Stats()
    a.id = "a"
    a.spd = 200
    b = Stats()
    b.id = "b"
    b.spd = 100
    q = ActionQueue([a, b])

    first = q.next_actor()
    q.grant_extra_turn(first)

    snap = q.snapshot()
    assert snap[0]["id"] == first.id
    assert snap[0]["bonus"] is True

    second = q.next_actor()
    assert second is first

    third = q.next_actor()
    assert third is b

    snap = q.snapshot()
    assert all("bonus" not in e for e in snap)


def test_snapshot_initial_order_preserves_non_negative_values():
    first = Stats()
    first.id = "first"
    first.spd = 100

    second = Stats()
    second.id = "second"
    second.spd = 100

    turn_counter = Stats()
    turn_counter.id = TURN_COUNTER_ID
    turn_counter.spd = 1

    queue = ActionQueue([first, second, turn_counter])
    snapshot = queue.snapshot()

    # Turn counter should remain a sentinel entry at the end of the snapshot.
    assert snapshot[-1]["id"] == TURN_COUNTER_ID

    regular_entries = [
        entry for entry in snapshot if entry["id"] != TURN_COUNTER_ID
    ]
    action_values = [entry["action_value"] for entry in regular_entries]

    assert action_values == sorted(action_values)
    assert all(value >= 0 for value in action_values)


class RecordingStats(Stats):
    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "action_value_updates", [])
        object.__setattr__(self, "action_gauge_updates", [])

    def __setattr__(self, name, value):
        if name in {"action_value", "action_gauge"}:
            history = self.__dict__.get(f"{name}_updates")
            if history is not None:
                history.append(value)
        super().__setattr__(name, value)


def _diff_sequence(values: list[float], starting_value: float) -> list[float]:
    previous = starting_value
    deltas = []
    for value in values:
        deltas.append(previous - value)
        previous = value
    return deltas


def test_queue_advances_one_point_at_a_time():
    first = RecordingStats()
    first.id = "alpha"
    first.spd = 200

    second = RecordingStats()
    second.id = "beta"
    second.spd = 150

    third = RecordingStats()
    third.id = "gamma"
    third.spd = 100

    queue = ActionQueue([first, second, third])

    members = (first, second, third)

    for _ in range(3):
        for member in members:
            member.action_value_updates.clear()
            member.action_gauge_updates.clear()

        initial_values = {id(member): member.action_value for member in members}
        initial_gauges = {
            id(member): getattr(member, "action_gauge", 0.0) for member in members
        }

        actor = queue.next_actor()
        spent = float(initial_values[id(actor)])
        expected_steps = math.ceil(spent) if spent > 0 else 0

        for member in members:
            if member is actor:
                continue
            value_history = member.action_value_updates
            gauge_history = member.action_gauge_updates
            assert len(value_history) >= expected_steps
            assert len(gauge_history) >= expected_steps

            start_value = float(initial_values[id(member)])
            start_gauge = float(initial_gauges[id(member)])

            deltas = _diff_sequence(value_history[:expected_steps], start_value)
            for delta in deltas:
                assert delta <= 1.0 + 1e-6
                assert delta >= -1e-6

            gauge_deltas = _diff_sequence(gauge_history[:expected_steps], start_gauge)
            for delta in gauge_deltas:
                assert delta <= 1.0 + 1e-6
                assert delta >= -1e-6

            assert value_history[-1] == pytest.approx(member.action_value, abs=1e-6)
            assert gauge_history[-1] == pytest.approx(member.action_gauge, abs=1e-6)

        snapshot = queue.snapshot()
        values = [entry["action_value"] for entry in snapshot]
        assert values == sorted(values)
        assert all(value >= 0 for value in values)


def test_same_speed_combatants_have_deterministic_snapshots():
    members = []
    for name in ("alpha", "bravo", "charlie"):
        unit = Stats()
        unit.id = name
        unit.spd = 150
        members.append(unit)

    queue = ActionQueue(list(members))

    baseline_snapshot = queue.snapshot()
    # Repeated snapshot calls without advancement should be identical.
    assert queue.snapshot() == baseline_snapshot

    seen_orders: set[tuple[str, ...]] = set()

    for _ in range(len(members) * 2):
        snapshot = queue.snapshot()
        entries = [entry for entry in snapshot if entry["id"] != TURN_COUNTER_ID]
        ids = [entry["id"] for entry in entries]
        values = [entry["action_value"] for entry in entries]

        assert values == sorted(values)
        assert all(value >= 0 for value in values)

        offsets = [
            getattr(member, "_action_sort_offset", None)
            for member in queue.combatants
            if member is not queue.turn_counter
        ]
        assert all(offset is not None for offset in offsets)
        assert len(offsets) == len(set(offsets))

        seen_orders.add(tuple(ids))

        first_id = ids[0]
        actor = queue.next_actor()
        assert actor.id == first_id

    assert len(seen_orders) == len(members)


@pytest.mark.asyncio
async def test_build_action_queue_snapshot_respects_sort_offsets():
    first = Stats()
    first.id = "first"
    first.spd = 100

    second = Stats()
    second.id = "second"
    second.spd = 100

    queue = ActionQueue([first, second])

    snapshot = await build_action_queue_snapshot(
        [first],
        [second],
        {},
        visual_queue=queue,
    )
    entries = [entry for entry in snapshot if entry["id"] != TURN_COUNTER_ID]
    assert [entry["id"] for entry in entries] == ["first", "second"]
    assert all(entry["action_value"] >= 0 for entry in entries)

    queue.next_actor()

    snapshot = await build_action_queue_snapshot(
        [first],
        [second],
        {},
        visual_queue=queue,
    )
    entries = [entry for entry in snapshot if entry["id"] != TURN_COUNTER_ID]
    assert [entry["id"] for entry in entries] == ["second", "first"]
    assert all(entry["action_value"] >= 0 for entry in entries)
