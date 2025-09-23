# ruff: noqa: E402

import asyncio
from pathlib import Path
import sys
from types import ModuleType

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

writers_module = sys.modules.get("battle_logging.writers")
if writers_module is None:
    battle_logging_pkg = sys.modules.setdefault(
        "battle_logging",
        ModuleType("battle_logging"),
    )
    writers_module = ModuleType("battle_logging.writers")
    setattr(battle_logging_pkg, "writers", writers_module)
    sys.modules["battle_logging.writers"] = writers_module

writers_module.end_run_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.end_battle_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.start_run_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.start_battle_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.get_current_run_logger = lambda: None  # noqa: E731

tracking_module = sys.modules.setdefault("tracking", ModuleType("tracking"))
tracking_module.log_play_session_end = lambda *args, **kwargs: None  # noqa: E731
tracking_module.log_run_end = lambda *args, **kwargs: None  # noqa: E731

from runs.lifecycle import battle_snapshots

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.effects import HealingOverTime
from autofighter.rooms.battle.progress import build_battle_progress_payload
from autofighter.rooms.battle.turns import EnrageState
from autofighter.rooms.battle.turns import mutate_snapshot_overlay
from autofighter.rooms.battle.turns import prepare_snapshot_overlay
from autofighter.rooms.battle.turns import register_snapshot_entities
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.event_bus import bus

STUB_PASSIVE_ID = "stub_passive"


class StubTurnEndPassive:
    """Simple passive that ticks at turn end for testing."""

    max_stacks = 1
    trigger = "turn_end"

    async def on_turn_end(self, stats: Stats) -> None:  # pragma: no cover - trivial stub
        _ = stats


def _stub_discover() -> dict[str, type[StubTurnEndPassive]]:
    return {STUB_PASSIVE_ID: StubTurnEndPassive}


@pytest.mark.asyncio
async def test_status_phase_events_emit_with_pacing(monkeypatch):
    target = Stats(hp=1000)
    target.set_base_stat('max_hp', 1000)
    target.set_base_stat('defense', 1)
    target.set_base_stat('mitigation', 1)
    target.set_base_stat('vitality', 1)
    target.id = "phase_target"

    target.passives = [STUB_PASSIVE_ID]

    monkeypatch.setattr("autofighter.passives.discover", _stub_discover)

    manager = EffectManager(target)

    hot = HealingOverTime("regen", healing=10, turns=1, id="hot_1", source=target)
    dot = DamageOverTime("burn", damage=10, turns=1, id="dot_1", source=target)

    manager.add_hot(hot)
    manager.add_dot(dot)

    captured_events: list[tuple[str, tuple[object, ...]]] = []

    async def fake_emit_async(event: str, *args: object) -> None:
        captured_events.append((event, args))

    monkeypatch.setattr("autofighter.stats.BUS.emit_async", fake_emit_async)

    sleep_calls: list[float] = []
    expected_multiplier = 0.25

    async def fake_pace_sleep(multiplier: float = 1.0) -> None:
        sleep_calls.append(multiplier)

    pacing_stub = ModuleType("autofighter.rooms.battle.pacing")
    pacing_stub.YIELD_MULTIPLIER = expected_multiplier
    pacing_stub.pace_sleep = fake_pace_sleep

    monkeypatch.setitem(sys.modules, "autofighter.rooms.battle.pacing", pacing_stub)

    await manager.tick()

    assert sleep_calls == [
        expected_multiplier,
        expected_multiplier,
        expected_multiplier,
        expected_multiplier,
    ]

    status_events = [evt for evt in captured_events if evt[0].startswith("status_phase_")]
    assert [name for name, _ in status_events] == [
        "status_phase_start",
        "status_phase_end",
        "status_phase_start",
        "status_phase_end",
        "status_phase_start",
        "status_phase_end",
        "status_phase_start",
        "status_phase_end",
    ]

    start_hot_name, start_hot_args = status_events[0]
    assert start_hot_args[0] == "hot"
    assert start_hot_args[1] is target
    assert start_hot_args[2]["phase"] == "hot"
    assert start_hot_args[2]["effect_count"] == 1
    assert start_hot_args[2]["order"] == 0
    assert start_hot_args[2]["has_effects"] is True
    assert start_hot_args[2]["effect_ids"] == [hot.id]
    assert start_hot_args[2]["effect_names"] == [hot.name]

    end_hot_name, end_hot_args = status_events[1]
    assert end_hot_args[2]["phase"] == "hot"
    assert end_hot_args[2]["effect_count"] == 0
    assert end_hot_args[2]["expired_count"] == 1
    assert end_hot_args[2]["order"] == 0
    assert end_hot_args[2]["effect_ids"] == []
    assert end_hot_args[2]["effect_names"] == []

    start_dot_name, start_dot_args = status_events[2]
    assert start_dot_args[0] == "dot"
    assert start_dot_args[2]["phase"] == "dot"
    assert start_dot_args[2]["effect_count"] == 1
    assert start_dot_args[2]["order"] == 1
    assert start_dot_args[2]["effect_ids"] == [dot.id]
    assert start_dot_args[2]["effect_names"] == [dot.name]

    end_dot_name, end_dot_args = status_events[3]
    assert end_dot_args[2]["phase"] == "dot"
    assert end_dot_args[2]["effect_count"] == 0
    assert end_dot_args[2]["expired_count"] == 1
    assert end_dot_args[2]["order"] == 1
    assert end_dot_args[2]["effect_ids"] == []
    assert end_dot_args[2]["effect_names"] == []

    start_mod_name, start_mod_args = status_events[4]
    assert start_mod_name == "status_phase_start"
    assert start_mod_args[0] == "stat_mods"
    assert start_mod_args[1] is target
    assert start_mod_args[2]["phase"] == "stat_mods"
    assert start_mod_args[2]["effect_count"] == 0
    assert start_mod_args[2]["order"] == 2
    assert start_mod_args[2]["has_effects"] is False
    assert start_mod_args[2]["effect_ids"] == []

    end_mod_name, end_mod_args = status_events[5]
    assert end_mod_name == "status_phase_end"
    assert end_mod_args[0] == "stat_mods"
    assert end_mod_args[1] is target
    assert end_mod_args[2]["phase"] == "stat_mods"
    assert end_mod_args[2]["effect_count"] == 0
    assert end_mod_args[2]["expired_count"] == 0
    assert end_mod_args[2]["order"] == 2
    assert end_mod_args[2]["effect_ids"] == []

    start_passive_name, start_passive_args = status_events[6]
    assert start_passive_name == "status_phase_start"
    assert start_passive_args[0] == "passives"
    assert start_passive_args[1] is target
    start_passive_payload = start_passive_args[2]
    assert start_passive_payload["phase"] == "passives"
    assert start_passive_payload["effect_count"] == 1
    assert start_passive_payload["expired_count"] == 0
    assert start_passive_payload["order"] == 3
    assert start_passive_payload["has_effects"] is True
    assert start_passive_payload["effect_ids"] == [STUB_PASSIVE_ID]

    end_passive_name, end_passive_args = status_events[7]
    assert end_passive_name == "status_phase_end"
    assert end_passive_args[0] == "passives"
    assert end_passive_args[1] is target
    end_passive_payload = end_passive_args[2]
    assert end_passive_payload["phase"] == "passives"
    assert end_passive_payload["effect_count"] == 1
    assert end_passive_payload["expired_count"] == 0
    assert end_passive_payload["order"] == 3
    assert end_passive_payload["effect_ids"] == [STUB_PASSIVE_ID]

    assert manager.hots == []
    assert manager.dots == []


def test_target_acquired_mutates_snapshot_state():
    run_id = "snapshot-target"
    battle_snapshots.clear()

    attacker = Stats()
    attacker.id = "attacker"
    target = Stats()
    target.id = "target"

    prepare_snapshot_overlay(run_id, [attacker, target])
    mutate_snapshot_overlay(
        run_id,
        active_id=attacker.id,
        active_target_id=target.id,
    )

    snapshot = battle_snapshots[run_id]
    assert snapshot["active_id"] == "attacker"
    assert snapshot["active_target_id"] == "target"
    assert snapshot.get("recent_events") == []


@pytest.mark.asyncio
async def test_target_acquired_event_records_recent_events():
    run_id = "snapshot-target-event"
    battle_snapshots.clear()

    attacker = Stats()
    attacker.id = "attacker"
    target = Stats()
    target.id = "target"

    prepare_snapshot_overlay(run_id, [attacker, target])
    register_snapshot_entities(run_id, [attacker, target])

    await BUS.emit_async("target_acquired", attacker, target)
    await bus._process_batches_internal()

    snapshot = battle_snapshots[run_id]
    events = snapshot.get("recent_events", [])
    assert any(evt.get("type") == "target_acquired" for evt in events)
    acquired_event = next(evt for evt in events if evt.get("type") == "target_acquired")
    assert acquired_event.get("source_id") == "attacker"
    assert acquired_event.get("target_id") == "target"
    metadata = acquired_event.get("metadata")
    assert metadata is not None
    assert metadata.get("damage_type_id") == "Generic"


@pytest.mark.asyncio
async def test_status_phase_events_update_snapshot_queue(monkeypatch):
    run_id = "snapshot-status"
    battle_snapshots.clear()

    target = Stats(hp=1000)
    target.id = "phase_target"
    attacker = Stats(hp=1000)
    attacker.id = "phase_attacker"
    target.set_base_stat("max_hp", 1000)
    target.set_base_stat("defense", 1)
    target.set_base_stat("mitigation", 1)
    target.set_base_stat("vitality", 1)
    target.set_base_stat("dodge_odds", 0)
    target.hp = 900
    target.passives = [STUB_PASSIVE_ID]

    monkeypatch.setattr(
        "autofighter.rooms.battle.snapshots._RECENT_EVENT_LIMIT",
        20,
        raising=False,
    )

    prepare_snapshot_overlay(run_id, [target, attacker])
    register_snapshot_entities(run_id, [target, attacker])

    monkeypatch.setattr("autofighter.passives.discover", _stub_discover)

    manager = EffectManager(target)
    hot = HealingOverTime("regen", healing=10, turns=1, id="hot_1", source=target)
    dot = DamageOverTime("burn", damage=10, turns=1, id="dot_1", source=target)

    manager.add_hot(hot)
    manager.add_dot(dot)

    set_battle_active(True)
    try:
        await manager.tick()
        await bus._process_batches_internal()
        await asyncio.sleep(0)
        await bus._process_batches_internal()
    finally:
        set_battle_active(False)

    snapshot = battle_snapshots[run_id]
    events = list(snapshot.get("recent_events", []))

    def _group_by_type(records: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
        grouped: dict[str, list[dict[str, object]]] = {}
        for record in records:
            grouped.setdefault(record["type"], []).append(record)
        return grouped

    events_by_type = _group_by_type(events)

    assert "effect_applied" in events_by_type
    applied_events = events_by_type["effect_applied"]
    assert len(applied_events) == 2
    first_applied_metadata = applied_events[0].get("metadata", {})
    assert first_applied_metadata.get("effect_name") in {"regen", "burn"}
    assert first_applied_metadata.get("effect_id") in {"hot_1", "dot_1"}

    assert "hot_tick" in events_by_type
    hot_event = events_by_type["hot_tick"][0]
    hot_metadata = hot_event.get("metadata", {})
    assert hot_metadata.get("effect_ids") == ["hot_1"]
    assert hot_metadata.get("remaining_turns") == 0
    effects = hot_metadata.get("effects") or []
    assert effects and effects[0].get("id") == "hot_1"
    assert effects[0].get("type") == "hot"

    assert "dot_tick" in events_by_type
    dot_event = events_by_type["dot_tick"][0]
    dot_metadata = dot_event.get("metadata", {})
    assert dot_metadata.get("effect_ids") == ["dot_1"]
    assert dot_metadata.get("remaining_turns") == 0
    dot_effects = dot_metadata.get("effects") or []
    assert dot_effects and dot_effects[0].get("id") == "dot_1"
    assert dot_effects[0].get("type") == "dot"

    assert "effect_expired" in events_by_type
    expired_events = events_by_type["effect_expired"]
    assert len(expired_events) == 2
    expired_metadata = {evt.get("metadata", {}).get("effect_id") for evt in expired_events}
    assert {"hot_1", "dot_1"}.issubset(expired_metadata)

    resist_details = {
        "effect_type": "dot",
        "target_id": target.id,
        "source_id": attacker.id,
        "chance": 25,
        "roll": 99,
    }
    BUS.emit_batched("effect_resisted", "burn", target, attacker, resist_details)
    await bus._process_batches_internal()

    events_after_resist = list(battle_snapshots[run_id]["recent_events"])
    events_by_type = _group_by_type(events_after_resist)
    assert "effect_resisted" in events_by_type
    resist_event = events_by_type["effect_resisted"][-1]
    resist_metadata = resist_event.get("metadata", {})
    assert resist_metadata.get("effect_name") == "burn"
    assert resist_metadata.get("source_id") == attacker.id
    assert resist_metadata.get("target_id") == target.id

    await BUS.emit_async(
        "damage_taken",
        target,
        target,
        77,
        None,
        None,
        True,
        "test_action",
    )
    await BUS.emit_async(
        "heal_received",
        target,
        target,
        33,
        "test_source_type",
        "Test Source",
    )
    await bus._process_batches_internal()

    final_events = list(battle_snapshots[run_id]["recent_events"])
    events_by_type = _group_by_type(final_events)

    assert "heal_received" in events_by_type
    assert "damage_taken" in events_by_type

    heal_event = events_by_type["heal_received"][-1]
    assert heal_event.get("metadata", {}).get("damage_type_id") == "Generic"

    damage_event = events_by_type["damage_taken"][-1]
    damage_metadata = damage_event.get("metadata", {})
    assert damage_metadata.get("damage_type_id") == "Generic"
    assert damage_metadata.get("is_critical") is True
    assert damage_metadata.get("action_name") == "test_action"

    heal_metadata = heal_event.get("metadata", {})
    assert heal_metadata.get("source_type") == "test_source_type"
    assert heal_metadata.get("source_name") == "Test Source"

    status_phase = snapshot.get("status_phase")
    assert status_phase is not None
    assert status_phase.get("phase") == "passives"
    assert status_phase.get("state") == "end"
    assert status_phase.get("effect_count") == 1
    assert status_phase.get("effect_ids") == [STUB_PASSIVE_ID]

    payload = await build_battle_progress_payload(
        [target],
        [],
        EnrageState(threshold=1),
        rdr=0.0,
        extra_turns={},
        turn=0,
        run_id=run_id,
        active_id=None,
        active_target_id=None,
    )
    assert payload.get("recent_events") == final_events
    assert payload.get("status_phase") == status_phase
    assert payload.get("turn") == 0
