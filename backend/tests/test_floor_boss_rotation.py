import asyncio
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # noqa: E402

from runs.lifecycle import load_map  # noqa: E402
from runs.lifecycle import save_map  # noqa: E402
from services.run_service import advance_room  # noqa: E402
from services.run_service import start_run  # noqa: E402
from test_app import app_with_db as _app_with_db  # noqa: F401

app_with_db = _app_with_db


class DummyFoe:
    def __init__(self, ident: str) -> None:
        self.id = ident
        self.name = ident
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
    assert len(picks) == 2
