import asyncio
import importlib.util

from pathlib import Path
import sys

import pytest


@pytest.fixture()
def app_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])

    for module_name in tuple(
        name for name in sys.modules if name == "runs" or name.startswith("runs.")
    ):
        sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    app_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(app_module)
    app_module.app.testing = True
    return app_module.app


@pytest.mark.asyncio
async def test_advance_room_requires_reward_selection(app_with_db):
    from runs.lifecycle import battle_snapshots
    from runs.lifecycle import load_map
    from runs.lifecycle import save_map

    app = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    # Simulate a battle that grants both card and relic rewards
    state, _ = await asyncio.to_thread(load_map, run_id)
    staged_loot = [
        {"id": "ember_fragment", "stars": 2},
        {"id": "ticket", "stars": 0},
    ]
    state.update(
        {
            "awaiting_card": True,
            "awaiting_relic": True,
            "awaiting_loot": True,
            "awaiting_next": False,
            "reward_progression": {
                "available": ["drops", "cards", "relics"],
                "completed": [],
                "current_step": "drops",
            },
            "reward_staging": {
                "cards": [],
                "relics": [],
                "items": list(staged_loot),
            },
        }
    )
    await asyncio.to_thread(save_map, run_id, state)
    battle_snapshots[run_id] = {
        "result": "victory",
        "loot": {"gold": 75, "items": list(staged_loot)},
        "awaiting_card": True,
        "awaiting_relic": True,
        "awaiting_loot": True,
        "awaiting_next": False,
    }

    try:
        # With the new phase-based advancement, we CAN advance from drops phase
        # even if there are pending card/relic rewards in future phases
        # The loot will be auto-acknowledged when advancing
        resp = await client.post("/ui/action", json={"action": "advance_room"})
        assert resp.status_code == 200
        data = await resp.get_json()
        print(f"DEBUG: Response data = {data}")
        # Should advance progression from "drops" to "cards"
        assert data.get("progression_advanced") is True
        assert data.get("current_step") == "cards"
        
        # Now we're in the cards phase - cannot advance without selecting a card
        resp = await client.post("/ui/action", json={"action": "advance_room"})
        assert resp.status_code == 400

        # Selecting card should stage it but still allow advance (which will auto-confirm)
        await client.post(
            "/ui/action",
            json={"action": "choose_card", "params": {"card_id": "micro_blade"}},
        )
        # Advancing now should auto-confirm the staged card and move to relics phase
        resp = await client.post("/ui/action", json={"action": "advance_room"})
        assert resp.status_code == 200
        data = await resp.get_json()
        assert data.get("progression_advanced") is True
        assert data.get("current_step") == "relics"

        state_after_card, _ = await asyncio.to_thread(load_map, run_id)
        assert state_after_card.get("awaiting_card") is False

        # Now in relics phase - cannot advance without selecting a relic
        resp = await client.post("/ui/action", json={"action": "advance_room"})
        assert resp.status_code == 400
        
        # Staging a relic should allow advance (which will auto-confirm)
        await client.post(
            "/ui/action",
            json={"action": "choose_relic", "params": {"relic_id": "threadbare_cloak"}},
        )
        resp = await client.post("/ui/action", json={"action": "advance_room"})
        # This should succeed and complete all progression
        assert resp.status_code == 200

        state_after_relic, _ = await asyncio.to_thread(load_map, run_id)
        assert state_after_relic.get("awaiting_relic") is False
        staging_after_relic = state_after_relic.get("reward_staging", {})
        assert isinstance(staging_after_relic, dict)
        assert staging_after_relic.get("relics") == []
        # Loot should have been auto-acknowledged during the first advance
        assert state_after_relic.get("awaiting_loot") is False
        assert staging_after_relic.get("items") == []

        # All rewards have been handled, should be awaiting_next
        assert state_after_relic.get("awaiting_next") is True
    finally:
        battle_snapshots.pop(run_id, None)


@pytest.mark.asyncio
async def test_staged_relic_is_confirmed_during_advance(app_with_db):
    from runs.lifecycle import battle_snapshots
    from runs.lifecycle import load_map
    from runs.lifecycle import save_map

    app = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    state, _ = await asyncio.to_thread(load_map, run_id)
    state.update(
        {
            "awaiting_card": False,
            "awaiting_relic": True,
            "awaiting_loot": False,
            "awaiting_next": False,
            "reward_progression": {
                "available": ["relics"],
                "completed": [],
                "current_step": "relics",
            },
            "reward_staging": {
                "cards": [],
                "relics": [{"id": "threadbare_cloak"}],
                "items": [],
            },
        }
    )
    await asyncio.to_thread(save_map, run_id, state)
    battle_snapshots[run_id] = {
        "result": "victory",
        "loot": {"gold": 0, "items": []},
        "awaiting_card": False,
        "awaiting_relic": True,
        "awaiting_loot": False,
        "awaiting_next": False,
    }

    try:
        resp = await client.post("/ui/action", json={"action": "advance_room"})
        assert resp.status_code == 200
        data = await resp.get_json()
        assert data.get("next_room") is not None

        updated_state, _ = await asyncio.to_thread(load_map, run_id)
        assert updated_state.get("awaiting_relic") is False
        staging = updated_state.get("reward_staging", {})
        assert isinstance(staging, dict)
        assert staging.get("relics") == []
    finally:
        battle_snapshots.pop(run_id, None)


@pytest.mark.asyncio
async def test_advance_room_emits_progression_payload(app_with_db):
    from runs.lifecycle import load_map
    from runs.lifecycle import save_map

    app = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    state, _ = await asyncio.to_thread(load_map, run_id)
    state.update(
        {
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_loot": False,
            "awaiting_next": False,
            "reward_preferences": {"battle_review": True},
            "reward_progression": {
                "available": ["cards", "battle_review"],
                "completed": [],
                "current_step": "cards",
            },
            "reward_staging": {"cards": [], "relics": [], "items": []},
        }
    )
    await asyncio.to_thread(save_map, run_id, state)

    resp = await client.post("/ui/action", json={"action": "advance_room"})
    data = await resp.get_json()

    assert resp.status_code == 200
    assert data["progression_advanced"] is True
    assert data["current_step"] == "cards"
    assert data["awaiting_card"] is False
    assert data["awaiting_relic"] is False
    assert data["awaiting_loot"] is False
    assert data["awaiting_next"] is False
    assert data["reward_progression"]["current_step"] == "cards"
    assert data["reward_progression"]["available"] == ["cards", "battle_review"]
    assert data["reward_progression"]["completed"] == ["cards"]


@pytest.mark.asyncio
async def test_card_selection_unlocks_advancement(app_with_db):
    from runs.lifecycle import battle_snapshots
    from runs.lifecycle import load_map
    from runs.lifecycle import save_map
    from runs.party_manager import load_party

    app = app_with_db
    client = app.test_client()

    start_resp = await client.post("/run/start", json={"party": ["player"]})
    run_id = (await start_resp.get_json())["run_id"]

    state, rooms = await asyncio.to_thread(load_map, run_id)
    state.update(
        {
            "awaiting_card": True,
            "awaiting_relic": False,
            "awaiting_loot": False,
            "awaiting_next": False,
            "reward_progression": {
                "available": ["cards"],
                "completed": [],
                "current_step": "cards",
            },
            "reward_staging": {"cards": [], "relics": [], "items": []},
            "card_choice_options": [
                {
                    "id": "micro_blade",
                    "name": "Micro Blade",
                    "stars": 1,
                    "about": "Deal 110% ATK to the front foe.",
                }
            ],
        }
    )
    await asyncio.to_thread(save_map, run_id, state)
    battle_snapshots[run_id] = {
        "result": "battle",
        "ended": True,
        "card_choices": list(state["card_choice_options"]),
        "relic_choices": [],
        "reward_staging": {"cards": [], "relics": [], "items": []},
    }

    try:
        resp = await client.post("/ui/action", json={"action": "advance_room"})
        assert resp.status_code == 400

        party_before = await asyncio.to_thread(load_party, run_id)
        assert party_before.cards == []

        await client.post(
            "/ui/action",
            json={"action": "choose_card", "params": {"card_id": "micro_blade"}},
        )

        resp = await client.post("/ui/action", json={"action": "advance_room"})
        data = await resp.get_json()
        assert resp.status_code == 200
        assert data.get("next_room") is not None

        party_after = await asyncio.to_thread(load_party, run_id)
        assert party_after.cards == ["micro_blade"]

        state_after, _ = await asyncio.to_thread(load_map, run_id)
        assert state_after.get("awaiting_card") is False
        assert "card_choice_options" not in state_after
    finally:
        battle_snapshots.pop(run_id, None)
