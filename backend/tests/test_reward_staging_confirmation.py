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

    db_path = tmp_path / "reward-confirmation.db"
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
async def test_confirm_card_commits_and_unlocks_next_step() -> None:
    assert lifecycle is not None
    assert party_manager is not None
    assert reward_service is not None

    run_id = "confirm-card"
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

    await reward_service.select_card(run_id, "arc_lightning")

    confirm_payload = await reward_service.confirm_reward(run_id, "card")

    assert confirm_payload["awaiting_card"] is False
    assert confirm_payload["awaiting_next"] is True
    assert confirm_payload["reward_staging"]["cards"] == []
    assert "cards" in confirm_payload and "arc_lightning" in confirm_payload["cards"]

    activation_record = confirm_payload.get("activation_record")
    assert isinstance(activation_record, dict)
    assert activation_record["bucket"] == "cards"
    staged_values = activation_record.get("staged_values")
    assert isinstance(staged_values, list) and len(staged_values) == 1
    staged_card = staged_values[0]
    assert staged_card["id"] == "arc_lightning"
    assert staged_card["name"] == "Arc Lightning"
    assert staged_card["stars"] == 3
    assert (
        staged_card["about"]
        == "+255% ATK; every attack chains 50% of dealt damage to a random foe."
    )
    preview = staged_card.get("preview")
    assert isinstance(preview, dict)
    assert preview.get("summary") == staged_card["about"]
    stats = preview.get("stats")
    assert isinstance(stats, list) and stats
    atk_stat = stats[0]
    assert atk_stat["stat"] == "atk"
    assert atk_stat["mode"] == "percent"
    assert atk_stat["stacks"] == 1
    assert pytest.approx(atk_stat["total_amount"], rel=1e-6) == 255.0
    triggers = preview.get("triggers")
    assert isinstance(triggers, list)
    assert "activation_id" in activation_record
    assert "activated_at" in activation_record

    activation_log = confirm_payload.get("reward_activation_log")
    assert isinstance(activation_log, list)
    assert activation_log and activation_log[-1]["activation_id"] == activation_record["activation_id"]

    party = await asyncio.to_thread(party_manager.load_party, run_id)
    assert party.cards == ["arc_lightning"]

    state, _ = lifecycle.load_map(run_id)
    assert state.get("awaiting_card") is False
    assert state.get("awaiting_next") is True
    assert state.get("reward_staging", {}).get("cards") == []
    assert "reward_progression" not in state
    state_log = state.get("reward_activation_log")
    assert isinstance(state_log, list)
    assert state_log[-1]["activation_id"] == activation_record["activation_id"]

    snapshot = lifecycle.battle_snapshots[run_id]
    assert snapshot["reward_staging"]["cards"] == []
    assert snapshot["awaiting_card"] is False
    assert snapshot["awaiting_next"] is True
    assert snapshot["reward_activation_log"][-1]["activation_id"] == activation_record["activation_id"]


@pytest.mark.asyncio()
async def test_confirm_card_is_single_use() -> None:
    assert lifecycle is not None
    assert reward_service is not None

    run_id = "confirm-card-once"
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
            {"room_id": 1, "room_type": "treasure"},
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
            }
        ],
        "relic_choices": [],
        "reward_staging": {"cards": [], "relics": [], "items": []},
    }

    await reward_service.select_card(run_id, "arc_lightning")
    first_payload = await reward_service.confirm_reward(run_id, "card")
    assert first_payload["awaiting_next"] is True

    with pytest.raises(ValueError):
        await reward_service.confirm_reward(run_id, "card")

    state, _ = lifecycle.load_map(run_id)
    activation_log = state.get("reward_activation_log")
    assert isinstance(activation_log, list)
    assert len(activation_log) == 1


@pytest.mark.asyncio()
async def test_cancel_card_reopens_progression_step() -> None:
    assert lifecycle is not None
    assert reward_service is not None

    run_id = "cancel-card"
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

    await reward_service.select_card(run_id, "arc_lightning")

    cancel_payload = await reward_service.cancel_reward(run_id, "card")

    assert cancel_payload["awaiting_card"] is True
    assert cancel_payload["awaiting_next"] is False
    assert cancel_payload["reward_staging"]["cards"] == []

    state, _ = lifecycle.load_map(run_id)
    assert state.get("awaiting_card") is True
    assert state.get("awaiting_next") is False
    progression = state.get("reward_progression")
    assert isinstance(progression, dict)
    assert progression.get("current_step") == "card"

    snapshot = lifecycle.battle_snapshots[run_id]
    assert snapshot["reward_staging"]["cards"] == []
    assert snapshot["awaiting_card"] is True
    assert snapshot.get("reward_progression", {}).get("current_step") == "card"


@pytest.mark.asyncio()
async def test_confirm_multiple_steps_advances_sequence() -> None:
    assert lifecycle is not None
    assert party_manager is not None
    assert reward_service is not None

    run_id = "confirm-sequence"
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
        "awaiting_card": True,
        "awaiting_relic": True,
        "awaiting_loot": False,
        "awaiting_next": False,
        "reward_progression": {
            "available": ["card", "relic"],
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
            }
        ],
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

    await reward_service.select_card(run_id, "arc_lightning")
    card_payload = await reward_service.confirm_reward(run_id, "card")
    assert card_payload["awaiting_card"] is False
    assert card_payload["awaiting_relic"] is True
    assert card_payload["awaiting_next"] is False
    progression = card_payload.get("reward_progression")
    assert isinstance(progression, dict)
    assert progression.get("current_step") == "relic"

    await reward_service.select_relic(run_id, "old_coin")
    relic_payload = await reward_service.confirm_reward(run_id, "relic")

    assert relic_payload["awaiting_relic"] is False
    assert relic_payload["awaiting_next"] is True
    assert relic_payload["reward_staging"]["relics"] == []
    assert "relics" in relic_payload and relic_payload["relics"].count("old_coin") == 2

    party = await asyncio.to_thread(party_manager.load_party, run_id)
    assert party.cards == ["arc_lightning"]
    assert party.relics.count("old_coin") == 2

    state, _ = lifecycle.load_map(run_id)
    assert state.get("awaiting_card") is False
    assert state.get("awaiting_relic") is False
    assert state.get("awaiting_next") is True
    assert state.get("reward_staging", {}).get("relics") == []
    assert "reward_progression" not in state


@pytest.mark.asyncio()
async def test_advance_room_rejects_when_staging_remains() -> None:
    assert lifecycle is not None

    from services.run_service import advance_room

    run_id = "staging-blocks-advance"
    party_payload = {
        "members": ["player"],
        "gold": 0,
        "relics": [],
        "cards": ["strike"],
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
        "awaiting_card": False,
        "awaiting_relic": False,
        "awaiting_loot": False,
        "awaiting_next": True,
        "reward_staging": {
            "cards": [
                {
                    "id": "arc_lightning",
                    "name": "Arc Lightning",
                    "stars": 3,
                }
            ],
            "relics": [],
            "items": [],
        },
    }
    _insert_run(run_id, party_payload, map_payload)

    with pytest.raises(ValueError, match="pending rewards must be collected"):
        await advance_room(run_id)

