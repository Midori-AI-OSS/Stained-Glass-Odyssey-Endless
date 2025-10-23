"""Test for fix of 'Cannot advance room while rewards are pending' bug.

This test covers the scenario where awaiting_card/relic flags are set
but the staging is empty, which can happen due to race conditions or
state synchronization issues.
"""

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
    """Reload the concrete implementations instead of test doubles."""

    global enc
    global lifecycle
    global party_manager
    global reward_service

    for name in list(sys.modules):
        if name == "runs" or name.startswith("runs."):
            sys.modules.pop(name)
        if name == "services" or name.startswith("services."):
            sys.modules.pop(name)
        if name == "routes" or name.startswith("routes."):
            sys.modules.pop(name)

    enc = importlib.import_module("runs.encryption")
    lifecycle = importlib.import_module("runs.lifecycle")
    party_manager = importlib.import_module("runs.party_manager")
    reward_service = importlib.import_module("services.reward_service")


@pytest.fixture(autouse=True)
def isolated_database(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Provide a fresh encrypted database per test."""

    _import_real_modules()

    assert enc is not None
    assert lifecycle is not None
    assert party_manager is not None
    assert reward_service is not None

    db_path = tmp_path / "reward-pending.db"
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
async def test_advance_room_handles_empty_staging_with_awaiting_card_gracefully() -> None:
    """Test that advance_room clears awaiting_card when staging is empty and no choices available.

    This tests the fix for the bug where awaiting_card=True but staged_cards is empty,
    which can happen due to race conditions or double-submission.
    """
    assert lifecycle is not None

    from services.run_service import advance_room

    run_id = "empty-staging-card"
    party_payload = {
        "members": ["player"],
        "gold": 0,
        "relics": [],
        "cards": ["strike"],
        "exp": {"player": 0},
        "level": {"player": 1},
        "player": {"pronouns": "", "damage_type": "Light", "stats": {}},
    }
    # Simulate state where awaiting_card is True but staging is empty
    # This could happen if the reward was confirmed by another process
    map_payload = {
        "rooms": [
            {"room_id": 0, "room_type": "battle-normal"},
            {"room_id": 1, "room_type": "shop"},
        ],
        "current": 0,
        "battle": False,
        "awaiting_card": True,  # Flag is set
        "awaiting_relic": False,
        "awaiting_loot": False,
        "awaiting_next": False,
        "reward_staging": {
            "cards": [],  # But staging is empty
            "relics": [],
            "items": [],
        },
    }
    _insert_run(run_id, party_payload, map_payload)

    # This should NOT error - it should clear the flag and advance
    result = await advance_room(run_id)
    assert result is not None
    assert "next_room" in result or "current_index" in result

    # Verify the flag was cleared
    state, _ = lifecycle.load_map(run_id)
    assert state.get("awaiting_card") is False


@pytest.mark.asyncio()
async def test_advance_room_handles_empty_staging_with_awaiting_relic_gracefully() -> None:
    """Test that advance_room clears awaiting_relic when staging is empty and no choices available."""
    assert lifecycle is not None

    from services.run_service import advance_room

    run_id = "empty-staging-relic"
    party_payload = {
        "members": ["player"],
        "gold": 0,
        "relics": [],
        "cards": ["strike"],
        "exp": {"player": 0},
        "level": {"player": 1},
        "player": {"pronouns": "", "damage_type": "Light", "stats": {}},
    }
    # Simulate state where awaiting_relic is True but staging is empty
    map_payload = {
        "rooms": [
            {"room_id": 0, "room_type": "battle-normal"},
            {"room_id": 1, "room_type": "shop"},
        ],
        "current": 0,
        "battle": False,
        "awaiting_card": False,
        "awaiting_relic": True,  # Flag is set
        "awaiting_loot": False,
        "awaiting_next": False,
        "reward_staging": {
            "cards": [],
            "relics": [],  # But staging is empty
            "items": [],
        },
    }
    _insert_run(run_id, party_payload, map_payload)

    # This should NOT error - it should clear the flag and advance
    result = await advance_room(run_id)
    assert result is not None
    assert "next_room" in result or "current_index" in result

    # Verify the flag was cleared
    state, _ = lifecycle.load_map(run_id)
    assert state.get("awaiting_relic") is False


@pytest.mark.asyncio()
async def test_advance_room_handles_empty_staging_with_awaiting_loot_gracefully() -> None:
    """Test that advance_room clears awaiting_loot when staging is empty."""
    assert lifecycle is not None

    from services.run_service import advance_room

    run_id = "empty-staging-loot"
    party_payload = {
        "members": ["player"],
        "gold": 0,
        "relics": [],
        "cards": ["strike"],
        "exp": {"player": 0},
        "level": {"player": 1},
        "player": {"pronouns": "", "damage_type": "Light", "stats": {}},
    }
    # Simulate state where awaiting_loot is True but staging is empty
    map_payload = {
        "rooms": [
            {"room_id": 0, "room_type": "battle-normal"},
            {"room_id": 1, "room_type": "shop"},
        ],
        "current": 0,
        "battle": False,
        "awaiting_card": False,
        "awaiting_relic": False,
        "awaiting_loot": True,  # Flag is set
        "awaiting_next": False,
        "reward_staging": {
            "cards": [],
            "relics": [],
            "items": [],  # But staging is empty
        },
    }
    _insert_run(run_id, party_payload, map_payload)

    # This should NOT error - it should clear the flag and advance
    result = await advance_room(run_id)
    assert result is not None
    assert "next_room" in result or "current_index" in result

    # Verify the flag was cleared
    state, _ = lifecycle.load_map(run_id)
    assert state.get("awaiting_loot") is False


@pytest.mark.asyncio()
async def test_advance_room_still_errors_when_card_choices_available() -> None:
    """Test that advance_room still errors when user needs to make a choice."""
    assert lifecycle is not None

    from services.run_service import advance_room

    run_id = "needs-card-choice"
    party_payload = {
        "members": ["player"],
        "gold": 0,
        "relics": [],
        "cards": [],
        "exp": {"player": 0},
        "level": {"player": 1},
        "player": {"pronouns": "", "damage_type": "Light", "stats": {}},
    }
    # State where user hasn't selected a card yet
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
        "card_choice_options": [
            {"id": "strike", "name": "Strike", "stars": 1},
            {"id": "defend", "name": "Defend", "stars": 1},
        ],
        "reward_staging": {
            "cards": [],  # Empty because user hasn't selected yet
            "relics": [],
            "items": [],
        },
    }
    _insert_run(run_id, party_payload, map_payload)

    # This SHOULD error because user needs to make a choice
    with pytest.raises(ValueError, match="pending rewards must be collected"):
        await advance_room(run_id)
