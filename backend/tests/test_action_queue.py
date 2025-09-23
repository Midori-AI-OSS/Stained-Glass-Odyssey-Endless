import pytest

from autofighter.action_queue import GAUGE_START
from autofighter.action_queue import TURN_COUNTER_ID
from autofighter.action_queue import ActionQueue
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
    assert a.action_value == a.base_action_value
    assert b.action_value == pytest.approx(
        b.base_action_value - a.base_action_value,
        abs=1.0,
    )

    second = q.next_actor()
    assert second is b
    assert b.action_value == pytest.approx(b.base_action_value, abs=1.0)
    assert a.action_value == pytest.approx(0.0, abs=1.0)

    snap = q.snapshot()
    assert [e["id"] for e in snap] == ["a", "b"]
    assert all(e["action_gauge"] == GAUGE_START for e in snap)


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


def test_snapshot_initial_order_unique():
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
    assert len(action_values) == len(set(action_values))
