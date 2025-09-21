import asyncio
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runs import encryption as enc
from runs.lifecycle import load_map
from runs.party_manager import load_party
from runs.party_manager import save_party
from services.run_service import advance_room
from services.run_service import start_run

from autofighter.mapgen import MapGenerator
from autofighter.stats import BUS
from plugins.relics.null_lantern import NullLantern


@pytest.fixture(autouse=True)
def reset_save(monkeypatch, tmp_path):
    original_manager = enc.SAVE_MANAGER
    original_fernet = enc.FERNET
    monkeypatch.setenv("AF_DB_PATH", str(tmp_path / "null_lantern.db"))
    enc.SAVE_MANAGER = None
    enc.FERNET = None
    yield
    enc.SAVE_MANAGER = original_manager
    enc.FERNET = original_fernet


@pytest.mark.asyncio
async def test_null_lantern_removes_future_shops():
    run_state = await start_run(["player"])
    run_id = run_state["run_id"]

    _, initial_nodes = await asyncio.to_thread(load_map, run_id)
    interior_initial = [node.room_type for node in initial_nodes[1:-1]]
    assert "shop" in interior_initial  # sanity check the baseline map

    party = await asyncio.to_thread(load_party, run_id)
    relic = NullLantern()
    party.relics.append(relic.id)
    await relic.apply(party)
    assert party.no_shops is True
    assert party.no_rests is True
    await asyncio.to_thread(save_party, run_id, party)

    # Clean up event bus subscribers to avoid leaking state between tests
    state = getattr(party, "_null_lantern_state", None)
    if isinstance(state, dict):
        handler = state.get("battle_start_handler")
        if handler is not None:
            BUS.unsubscribe("battle_start", handler)
        end_handler = state.get("battle_end_handler")
        if end_handler is not None:
            BUS.unsubscribe("battle_end", end_handler)
        cleanup_handler = state.get("cleanup_handler")
        if cleanup_handler is not None:
            BUS.unsubscribe("battle_end", cleanup_handler)
        if hasattr(party, "_null_lantern_state"):
            delattr(party, "_null_lantern_state")

    persisted_party = await asyncio.to_thread(load_party, run_id)
    assert persisted_party.no_shops is True
    assert persisted_party.no_rests is True

    saw_reset = False
    for _ in range(MapGenerator.rooms_per_floor * 2):
        result = await advance_room(run_id)
        if result.get("current_index") == 1:
            saw_reset = True
            break
    assert saw_reset, "expected to reach the next floor"

    _, new_nodes = await asyncio.to_thread(load_map, run_id)
    inner_types = [node.room_type for node in new_nodes[1:-1]]
    assert "shop" not in inner_types
    assert "rest" not in inner_types
