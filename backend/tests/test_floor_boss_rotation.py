import asyncio
from pathlib import Path
import sys

import pytest

from autofighter.stats import Stats
from plugins.characters import CHARACTER_FOES

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402
sys.modules.pop("services", None)
sys.modules.pop("runs", None)

from runs.lifecycle import load_map  # noqa: E402
from runs.lifecycle import save_map  # noqa: E402
from services.room_service import battle_snapshots  # noqa: E402
from services.room_service import battle_tasks  # noqa: E402
from services.room_service import boss_room  # noqa: E402
from services.run_service import advance_room  # noqa: E402
from services.run_service import start_run  # noqa: E402
from test_app import app_with_db as _app_with_db  # noqa: F401

app_with_db = _app_with_db


class DummyFoe(Stats):
    def __init__(self, ident: str | None = None) -> None:
        super().__init__()
        resolved = ident or getattr(type(self), "id", "dummy")
        self.id = resolved
        self.name = resolved
        self.rank = "boss"


@pytest.mark.asyncio
async def test_floor_boss_refreshes_per_floor(app_with_db, monkeypatch):
    _, _ = app_with_db

    picks: list[str] = []

    def choose_once(node, party):  # noqa: ANN001
        ident = f"boss-{len(picks)}"
        picks.append(ident)
        return DummyFoe(ident)

    monkeypatch.setattr("services.run_service._choose_foe", choose_once)
    monkeypatch.setattr("services.room_service._choose_foe", choose_once)

    run_info = await start_run(["player"])
    run_id = run_info["run_id"]
    first_record = run_info["map"].get("floor_boss")
    assert first_record is not None
    assert first_record["id"] == "boss-0"
    assert "index" in first_record

    state, rooms = await asyncio.to_thread(load_map, run_id)
    state["current"] = len(rooms) - 1
    state["awaiting_next"] = False
    await asyncio.to_thread(save_map, run_id, state)

    await advance_room(run_id)

    updated_state, _ = await asyncio.to_thread(load_map, run_id)
    refreshed = updated_state.get("floor_boss")
    assert refreshed is not None
    assert refreshed["id"] == "boss-1"
    assert refreshed["id"] != first_record["id"]
    assert "index" in refreshed
    assert len(picks) == 2


@pytest.mark.asyncio
async def test_boss_rush_rolls_unique_bosses(app_with_db, monkeypatch):
    _, _ = app_with_db

    monkeypatch.setattr("autofighter.mapgen.MapGenerator.rooms_per_floor", 4)
    monkeypatch.setattr("services.run_service.MapGenerator.rooms_per_floor", 4)

    picks: list[str] = []

    class BossRushFoe(DummyFoe):
        pass

    def choose_unique(node, party):  # noqa: ANN001
        ident = f"rush-boss-{len(picks)}"
        picks.append(ident)
        foe_cls = type(f"BossRushFoe_{len(picks)}", (BossRushFoe,), {"id": ident})
        CHARACTER_FOES[ident] = foe_cls
        return foe_cls()

    async def fake_run_battle(run_id, room, foes, party, data, state, rooms, progress):  # noqa: ANN001
        await progress({"result": "boss", "turn": 0, "party": [], "foes": []})
        return {"result": "boss"}

    monkeypatch.setattr("services.run_service._choose_foe", choose_unique)
    monkeypatch.setattr("services.room_service._choose_foe", choose_unique)
    monkeypatch.setattr("services.room_service._run_battle", fake_run_battle)

    run_info = await start_run(["player"], run_type="boss_rush")
    run_id = run_info["run_id"]
    picks.clear()

    state, rooms = await asyncio.to_thread(load_map, run_id)
    assert rooms[1].room_type == "battle-boss-floor"

    await boss_room(run_id, {})
    first_task = battle_tasks.get(run_id)
    if first_task is not None:
        await first_task
    battle_tasks.pop(run_id, None)
    battle_snapshots.pop(run_id, None)

    assert len(picks) == 1

    state["current"] = 2
    state["awaiting_next"] = False
    state["battle"] = False
    await asyncio.to_thread(save_map, run_id, state)

    await boss_room(run_id, {})
    second_task = battle_tasks.get(run_id)
    if second_task is not None:
        await second_task
    battle_tasks.pop(run_id, None)
    battle_snapshots.pop(run_id, None)

    assert len(picks) == 2
    assert picks[0] != picks[1]
    for ident in picks:
        CHARACTER_FOES.pop(ident, None)
