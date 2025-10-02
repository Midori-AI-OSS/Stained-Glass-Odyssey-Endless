# ruff: noqa: E402

from pathlib import Path
import sys
import types

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

writers_module = sys.modules.get("battle_logging.writers")
if writers_module is None:
    battle_logging_pkg = sys.modules.setdefault(
        "battle_logging",
        types.ModuleType("battle_logging"),
    )
    writers_module = types.ModuleType("battle_logging.writers")
    setattr(battle_logging_pkg, "writers", writers_module)
    sys.modules["battle_logging.writers"] = writers_module

writers_module.end_run_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.end_battle_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.start_run_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.start_battle_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.get_current_run_logger = lambda: None  # noqa: E731

tracking_module = sys.modules.setdefault("tracking", types.ModuleType("tracking"))
tracking_module.log_play_session_end = lambda *args, **kwargs: None  # noqa: E731
tracking_module.log_run_end = lambda *args, **kwargs: None  # noqa: E731

from runs.lifecycle import battle_snapshots

from autofighter.party import Party
from autofighter.rooms.battle import events as battle_events
from autofighter.rooms.battle.turns import prepare_snapshot_overlay
from autofighter.rooms.battle.turns import register_snapshot_entities
from autofighter.stats import BUS
from autofighter.stats import Stats


class _StubCard:
    id = "stub_card"
    name = "Stub Card"

    def __init__(self) -> None:
        self.id = self.__class__.id
        self.name = self.__class__.name


class _StubRelic:
    id = "stub_relic"
    name = "Stub Relic"

    def __init__(self) -> None:
        self.id = self.__class__.id
        self.name = self.__class__.name


@pytest.mark.asyncio
async def test_card_and_relic_events_record_snapshot_metadata(monkeypatch):
    run_id = "card-relic-run"
    battle_snapshots.clear()

    monkeypatch.setattr(battle_events, "_CARD_NAME_CACHE", {})
    monkeypatch.setattr(battle_events, "_RELIC_NAME_CACHE", {})

    member = Stats()
    member.id = "member"
    party = Party(members=[member])

    prepare_snapshot_overlay(run_id, [party, member])
    register_snapshot_entities(run_id, [party, member])

    async def fake_sleep(multiplier: float = 1.0) -> None:  # pragma: no cover - patched in test
        calls.append(multiplier)

    calls: list[float] = []
    expected_multiplier = 0.25

    monkeypatch.setattr("autofighter.rooms.battle.events.pace_sleep", fake_sleep)
    monkeypatch.setattr(
        "autofighter.rooms.battle.events.YIELD_MULTIPLIER",
        expected_multiplier,
        raising=False,
    )

    monkeypatch.setattr(
        battle_events,
        "_card_registry",
        lambda: {"stub_card": _StubCard},
    )
    monkeypatch.setattr(
        battle_events,
        "_relic_registry",
        lambda: {"stub_relic": _StubRelic},
    )

    await BUS.emit_async(
        "card_effect",
        "stub_card",
        member,
        "bonus",
        7,
        {"note": "value"},
    )

    snapshot = battle_snapshots[run_id]
    events = list(snapshot.get("recent_events", []))
    assert len(events) == 1

    card_event = events[0]
    assert card_event["type"] == "card_effect"
    assert card_event["amount"] == 7
    assert card_event["target_id"] == member.id
    metadata = card_event.get("metadata", {})
    assert metadata["card_id"] == "stub_card"
    assert metadata["card_name"] == "Stub Card"
    assert metadata["effect"] == "bonus"
    assert metadata["details"] == {"note": "value"}

    assert battle_snapshots[run_id]["active_id"] == member.id
    assert battle_snapshots[run_id]["active_target_id"] == member.id

    await BUS.emit_async(
        "relic_effect",
        "stub_relic",
        party,
        "gold_bonus",
        9,
        {"source": "shop"},
    )

    events = list(battle_snapshots[run_id].get("recent_events", []))
    assert len(events) == 2
    relic_event = events[-1]
    assert relic_event["type"] == "relic_effect"
    assert relic_event["amount"] == 9
    assert relic_event["target_id"] is None
    relic_metadata = relic_event.get("metadata", {})
    assert relic_metadata["relic_id"] == "stub_relic"
    assert relic_metadata["relic_name"] == "Stub Relic"
    assert relic_metadata["effect"] == "gold_bonus"
    assert relic_metadata["details"] == {"source": "shop"}

    assert calls == [expected_multiplier, expected_multiplier]

    attacker = Stats()
    attacker.id = "attacker"

    await BUS.emit_async(
        "relic_effect",
        "aftertaste",
        member,
        "aftertaste",
        21,
        {
            "effect_label": "aftertaste",
            "effect_type": "aftertaste",
            "base_damage": 18,
            "actual_damage": 21,
        },
        attacker,
    )

    events = list(battle_snapshots[run_id].get("recent_events", []))
    assert len(events) == 3
    aftertaste_event = events[-1]
    assert aftertaste_event["type"] == "relic_effect"
    assert aftertaste_event["amount"] == 21
    assert aftertaste_event["source_id"] == attacker.id
    assert aftertaste_event["target_id"] == member.id
    aftertaste_metadata = aftertaste_event.get("metadata", {})
    assert aftertaste_metadata["relic_id"] == "aftertaste"
    assert aftertaste_metadata["effect"] == "aftertaste"
    assert aftertaste_metadata["details"]["effect_label"] == "aftertaste"
    assert aftertaste_metadata["details"]["effect_type"] == "aftertaste"

    assert battle_snapshots[run_id]["active_id"] == attacker.id
    assert battle_snapshots[run_id]["active_target_id"] == member.id
