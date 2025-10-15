from __future__ import annotations

import importlib
from pathlib import Path
import sys
import types

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.stats import Stats


@pytest.fixture()
def snapshot_env(monkeypatch: pytest.MonkeyPatch):
    created_stub = False
    try:
        lifecycle = importlib.import_module("runs.lifecycle")
    except ImportError:
        lifecycle = types.ModuleType("runs.lifecycle")
        lifecycle.battle_snapshots = {}
        runs_module = types.ModuleType("runs")
        runs_module.lifecycle = lifecycle
        monkeypatch.setitem(sys.modules, "runs", runs_module)
        monkeypatch.setitem(sys.modules, "runs.lifecycle", lifecycle)
        created_stub = True
    else:
        lifecycle.battle_snapshots.clear()

    snapshots_module = importlib.import_module("autofighter.rooms.battle.snapshots")
    snapshots_module = importlib.reload(snapshots_module)
    try:
        yield snapshots_module, lifecycle.battle_snapshots
    finally:
        lifecycle.battle_snapshots.clear()
        if created_stub:
            monkeypatch.delitem(sys.modules, "runs", raising=False)
            monkeypatch.delitem(sys.modules, "runs.lifecycle", raising=False)


def test_prepare_snapshot_overlay_initializes_state(snapshot_env) -> None:
    snapshots_module, battle_snapshots = snapshot_env
    run_id = "snapshot-init"

    combatant = Stats()
    combatant.id = "hero"

    snapshots_module.prepare_snapshot_overlay(run_id, [combatant])

    assert run_id in battle_snapshots
    snapshot = battle_snapshots[run_id]
    assert snapshot["result"] == "battle"
    assert snapshot.get("recent_events") == []
    assert snapshots_module.resolve_run_id(combatant) == run_id

    snapshots_module.mutate_snapshot_overlay(run_id, event={"type": "seed"})
    assert snapshots_module.get_recent_events(run_id) == [{"type": "seed"}]

    snapshots_module.prepare_snapshot_overlay(run_id, [combatant])
    assert snapshots_module.get_recent_events(run_id) == []
    assert "status_phase" not in battle_snapshots[run_id]


def test_mutate_snapshot_overlay_updates_snapshot_fields(snapshot_env) -> None:
    snapshots_module, battle_snapshots = snapshot_env
    run_id = "snapshot-mutate"

    attacker = Stats()
    attacker.id = "attacker"

    snapshots_module.prepare_snapshot_overlay(run_id, [attacker])

    status_payload = {"phase": "dot", "state": "start"}
    event_payload = {"type": "hit_landed", "amount": 5}

    snapshots_module.mutate_snapshot_overlay(
        run_id,
        active_id=attacker.id,
        active_target_id="target",
        status_phase=status_payload,
        event=event_payload,
    )

    snapshot = battle_snapshots[run_id]
    assert snapshot["active_id"] == attacker.id
    assert snapshot["active_target_id"] == "target"
    assert snapshot["status_phase"] == status_payload
    assert snapshot["recent_events"] == [event_payload]

    events_copy = snapshots_module.get_recent_events(run_id)
    assert events_copy == [event_payload]
    events_copy.append({"type": "other"})
    assert snapshot["recent_events"] == [event_payload]

    assert snapshots_module.get_status_phase(run_id) == status_payload


def test_prepare_snapshot_overlay_clears_effect_charges(snapshot_env) -> None:
    snapshots_module, battle_snapshots = snapshot_env
    run_id = "snapshot-effects"

    combatant = Stats()
    combatant.id = "effect-tester"

    snapshots_module.set_effect_charges(run_id, {"id": "example", "progress": 1.0})
    assert battle_snapshots[run_id]["effects_charge"][0]["id"] == "example"

    snapshots_module.prepare_snapshot_overlay(run_id, [combatant])

    assert snapshots_module.get_effect_charges(run_id) is None
    assert "effects_charge" not in battle_snapshots[run_id]


def test_recent_event_history_survives_bursts(snapshot_env) -> None:
    snapshots_module, battle_snapshots = snapshot_env
    run_id = "snapshot-burst"

    combatant = Stats()
    combatant.id = "burst-tester"

    snapshots_module.prepare_snapshot_overlay(run_id, [combatant])

    burst_events = [
        {"type": "burst", "sequence": index}
        for index in range(24)
    ]

    for payload in burst_events:
        snapshots_module.mutate_snapshot_overlay(run_id, event=payload)

    stored_events = battle_snapshots[run_id]["recent_events"]
    assert len(stored_events) == len(burst_events)
    assert stored_events[0]["sequence"] == 0
    assert stored_events[-1]["sequence"] == burst_events[-1]["sequence"]
