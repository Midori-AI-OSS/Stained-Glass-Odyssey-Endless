"""Regression tests for reward staging hooks in reward_service."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

enc: ModuleType | None = None
lifecycle: ModuleType | None = None
party_manager: ModuleType | None = None
reward_service: ModuleType | None = None


def _import_real_modules() -> None:
    """Reload the real runs and services modules instead of test stubs."""

    global enc
    global lifecycle
    global party_manager
    global reward_service

    for name in list(sys.modules):
        if name == "runs" or name.startswith("runs."):
            sys.modules.pop(name)
        if name == "services" or name.startswith("services."):
            sys.modules.pop(name)

    enc = importlib.import_module("runs.encryption")
    lifecycle = importlib.import_module("runs.lifecycle")
    party_manager = importlib.import_module("runs.party_manager")
    reward_service = importlib.import_module("services.reward_service")


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Provide a fresh encrypted database for each test."""

    _import_real_modules()

    assert enc is not None
    assert lifecycle is not None
    assert party_manager is not None
    assert reward_service is not None

    db_path = tmp_path / "reward-staging-hooks.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))

    original_manager = enc.SAVE_MANAGER
    original_fernet = enc.FERNET
    enc.SAVE_MANAGER = None
    enc.FERNET = None
    lifecycle.battle_snapshots.clear()

    try:
        yield
    finally:
        lifecycle.battle_snapshots.clear()
        enc.SAVE_MANAGER = original_manager
        enc.FERNET = original_fernet
        monkeypatch.delenv("AF_DB_PATH", raising=False)


def _insert_run(run_id: str, party_payload: dict[str, object], map_payload: dict[str, object]) -> None:
    assert enc is not None
    manager = enc.get_save_manager()
    with manager.connection() as conn:
        conn.execute(
            "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
            (run_id, json.dumps(party_payload), json.dumps(map_payload)),
        )


@pytest.mark.asyncio()
async def test_select_card_stages_without_modifying_party() -> None:
    run_id = "stage-card"
    party_payload = {
        "members": ["player"],
        "gold": 0,
        "relics": [],
        "cards": [],
        "exp": {"player": 0},
        "level": {"player": 1},
        "player": {"pronouns": "", "damage_type": "Light", "stats": {}},
    }
    map_payload = {
        "rooms": [
            {"room_id": 0, "room_type": "battle-normal"},
            {"room_id": 1, "room_type": "shop"},
        ],
        "current": 0,
        "battle": False,
        "awaiting_card": True,
        "awaiting_relic": False,
        "awaiting_loot": False,
        "awaiting_next": False,
        "reward_progression": {
            "available": ["card"],
            "completed": [],
            "current_step": "card",
        },
        "reward_staging": {"cards": [], "relics": [], "items": []},
    }
    _insert_run(run_id, party_payload, map_payload)

    lifecycle.battle_snapshots[run_id] = {
        "result": "battle",
        "ended": True,
        "card_choices": [
            {
                "id": "arc_lightning",
                "name": "Arc Lightning",
                "stars": 3,
                "about": "+255% ATK; every attack chains 50% of dealt damage to a random foe.",
            }
        ],
        "relic_choices": [],
        "reward_staging": {"cards": [], "relics": [], "items": []},
    }

    assert reward_service is not None
    result = await reward_service.select_card(run_id, "arc_lightning")

    assert result["card"]["id"] == "arc_lightning"
    assert result["cards"] == []  # party deck unchanged
    assert result["awaiting_card"] is True
    assert result["awaiting_next"] is False
    progression_payload = result["reward_progression"]
    assert isinstance(progression_payload, dict)
    assert progression_payload.get("current_step") == "card"
    assert progression_payload.get("completed") == []
    staged_cards = result["reward_staging"]["cards"]
    assert len(staged_cards) == 1
    assert staged_cards[0]["id"] == "arc_lightning"

    assert party_manager is not None
    party = await asyncio.to_thread(party_manager.load_party, run_id)
    assert party.cards == []

    assert lifecycle is not None
    state, _ = lifecycle.load_map(run_id)
    assert state["awaiting_card"] is True
    assert state["awaiting_next"] is False
    progression_state = state.get("reward_progression")
    assert isinstance(progression_state, dict)
    assert progression_state.get("current_step") == "card"
    assert state["reward_staging"]["cards"][0]["id"] == "arc_lightning"
    snapshot = lifecycle.battle_snapshots[run_id]
    assert snapshot["card_choices"] == []
    assert snapshot["awaiting_card"] is True
    assert snapshot["awaiting_next"] is False
    progression_snapshot = snapshot.get("reward_progression")
    assert isinstance(progression_snapshot, dict)
    assert progression_snapshot.get("current_step") == "card"
    assert snapshot["reward_staging"]["cards"][0]["id"] == "arc_lightning"


@pytest.mark.asyncio()
async def test_select_relic_stages_without_duplicate_application() -> None:
    run_id = "stage-relic"
    party_payload = {
        "members": ["player"],
        "gold": 0,
        "relics": ["old_coin"],
        "cards": [],
        "exp": {"player": 0},
        "level": {"player": 1},
        "player": {"pronouns": "", "damage_type": "Light", "stats": {}},
    }
    map_payload = {
        "rooms": [
            {"room_id": 0, "room_type": "battle-normal"},
            {"room_id": 1, "room_type": "battle-normal"},
        ],
        "current": 0,
        "battle": False,
        "awaiting_card": False,
        "awaiting_relic": True,
        "awaiting_loot": False,
        "awaiting_next": False,
        "reward_progression": {
            "available": ["relic"],
            "completed": [],
            "current_step": "relic",
        },
        "reward_staging": {"cards": [], "relics": [], "items": []},
    }
    _insert_run(run_id, party_payload, map_payload)

    lifecycle.battle_snapshots[run_id] = {
        "result": "battle",
        "ended": True,
        "card_choices": [],
        "relic_choices": [
            {
                "id": "old_coin",
                "name": "Old Coin",
                "stars": 2,
                "about": "Gain 20% more gold from all sources.",
                "stacks": 1,
            }
        ],
        "reward_staging": {"cards": [], "relics": [], "items": []},
    }

    assert reward_service is not None
    result = await reward_service.select_relic(run_id, "old_coin")

    assert result["relic"]["id"] == "old_coin"
    assert result["relic"]["stacks"] == 2
    assert result["relics"] == ["old_coin"]
    assert result["awaiting_relic"] is True
    assert result["awaiting_next"] is False
    progression_payload = result["reward_progression"]
    assert isinstance(progression_payload, dict)
    assert progression_payload.get("current_step") == "relic"
    assert progression_payload.get("completed") == []
    staged_relics = result["reward_staging"]["relics"]
    assert len(staged_relics) == 1
    assert staged_relics[0]["id"] == "old_coin"
    assert staged_relics[0]["stacks"] == 2

    assert party_manager is not None
    party = await asyncio.to_thread(party_manager.load_party, run_id)
    assert party.relics == ["old_coin"]

    assert lifecycle is not None
    state, _ = lifecycle.load_map(run_id)
    assert state["awaiting_relic"] is True
    assert state["awaiting_next"] is False
    progression_state = state.get("reward_progression")
    assert isinstance(progression_state, dict)
    assert progression_state.get("current_step") == "relic"
    staged_state = state["reward_staging"]["relics"][0]
    assert staged_state["id"] == "old_coin"
    assert staged_state["stacks"] == 2
    snapshot = lifecycle.battle_snapshots[run_id]
    assert snapshot["relic_choices"] == []
    assert snapshot["awaiting_relic"] is True
    assert snapshot["awaiting_next"] is False
    progression_snapshot = snapshot.get("reward_progression")
    assert isinstance(progression_snapshot, dict)
    assert progression_snapshot.get("current_step") == "relic"
    staged_snapshot = snapshot["reward_staging"]["relics"][0]
    assert staged_snapshot["id"] == "old_coin"
    assert staged_snapshot["stacks"] == 2
