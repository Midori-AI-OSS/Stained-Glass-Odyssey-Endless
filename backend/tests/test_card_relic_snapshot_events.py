import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.rooms.battle import turns as battle_turns
from runs.lifecycle import battle_snapshots

from autofighter.party import Party
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

    monkeypatch.setattr(battle_turns, "_card_name_cache", {})
    monkeypatch.setattr(battle_turns, "_relic_name_cache", {})

    member = Stats()
    member.id = "member"
    party = Party(members=[member])

    prepare_snapshot_overlay(run_id, [party, member])
    register_snapshot_entities(run_id, [party, member])

    async def fake_sleep(multiplier: float = 1.0) -> None:  # pragma: no cover - patched in test
        calls.append(multiplier)

    calls: list[float] = []
    expected_multiplier = 0.25

    monkeypatch.setattr("autofighter.rooms.battle.turns.pace_sleep", fake_sleep)
    monkeypatch.setattr(
        "autofighter.rooms.battle.turns.YIELD_MULTIPLIER",
        expected_multiplier,
        raising=False,
    )

    monkeypatch.setattr(
        battle_turns,
        "_card_registry",
        lambda: {"stub_card": _StubCard},
    )
    monkeypatch.setattr(
        battle_turns,
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
