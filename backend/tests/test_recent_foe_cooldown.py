import asyncio
import importlib.util
from pathlib import Path
import random
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

sys.modules.pop("services", None)
import services  # noqa: E402
from runs.lifecycle import RECENT_FOE_COOLDOWN  # noqa: E402
from runs.lifecycle import battle_snapshots  # noqa: E402
from runs.lifecycle import battle_tasks  # noqa: E402
from runs.lifecycle import load_map  # noqa: E402
from runs.lifecycle import save_map  # noqa: E402
from services.room_service import battle_room  # noqa: E402
from services.run_service import start_run  # noqa: E402

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms import BattleRoom
from autofighter.rooms import utils
from autofighter.stats import Stats
from plugins.characters import Player


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "save.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))
    monkeypatch.setenv("AF_DB_KEY", "testkey")
    monkeypatch.syspath_prepend(Path(__file__).resolve().parents[1])
    spec = importlib.util.spec_from_file_location(
        "app", Path(__file__).resolve().parents[1] / "app.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_foes_reduces_recent_weights(monkeypatch):
    class FakeFoeA:
        id = "alpha"

        def __init__(self):
            self.id = "alpha"

    class FakeFoeB:
        id = "beta"

        def __init__(self):
            self.id = "beta"

    monkeypatch.setattr("plugins.characters.__all__", ["FakeFoeA", "FakeFoeB"], raising=False)
    monkeypatch.setattr("plugins.characters.FakeFoeA", FakeFoeA, raising=False)
    monkeypatch.setattr("plugins.characters.FakeFoeB", FakeFoeB, raising=False)
    monkeypatch.setattr("plugins.characters.SlimeFoe", FakeFoeB, raising=False)
    monkeypatch.setattr("plugins.characters.CHARACTER_FOES", {}, raising=False)

    captured_weights: list[list[float]] = []

    def fake_choices(candidates, weights, k):
        captured_weights.append(list(weights))
        return [candidates[0]]

    monkeypatch.setattr(random, "random", lambda: 0.99)
    monkeypatch.setattr(random, "choices", fake_choices)

    node = MapNode(room_id=0, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
    party = Party(members=[Player()])

    utils._build_foes(node, party, recent_ids={"alpha"})

    assert captured_weights, "random.choices should be invoked"
    weights = captured_weights[0]
    assert weights[0] < weights[1]
    assert weights[0] > 0


@pytest.mark.asyncio
async def test_battle_room_passes_recent_ids(app_module, monkeypatch):
    run_info = await start_run(["player"])
    run_id = run_info["run_id"]

    state, _ = await asyncio.to_thread(load_map, run_id)
    state["recent_foes"] = [
        {"id": "stale", "cooldown": 0},
        {"id": "keep", "cooldown": 2},
        {"id": None, "cooldown": 5},
    ]
    await asyncio.to_thread(save_map, run_id, state)

    captured_recent: set[str] | None = None

    def fake_build(node, party, *, exclude_ids=None, recent_ids=None):
        nonlocal captured_recent
        captured_recent = {str(r) for r in (recent_ids or set())}
        foe = Stats()
        foe.id = "dummy"
        return [foe]

    async def fake_run_battle(run_id_param, room, foes, party, data, state_param, rooms_param, progress):
        battle_snapshots[run_id_param] = {"result": "battle", "turn": 0, "ended": True}

    monkeypatch.setattr("services.room_service._build_foes", fake_build)
    monkeypatch.setattr("services.room_service._run_battle", fake_run_battle)
    monkeypatch.setattr("services.room_service._scale_stats", lambda foe, node, strength: None)

    await battle_room(run_id, {})

    task = battle_tasks.pop(run_id, None)
    if task is not None:
        await task

    assert captured_recent == {"keep"}

    state_after, _ = await asyncio.to_thread(load_map, run_id)
    assert state_after.get("recent_foes") == [{"id": "keep", "cooldown": 2}]


@pytest.mark.asyncio
async def test_run_battle_updates_recent_foe_cooldowns(app_module, monkeypatch):
    run_info = await start_run(["player"])
    run_id = run_info["run_id"]

    state, _ = await asyncio.to_thread(load_map, run_id)
    state["recent_foes"] = [
        {"id": "gamma", "cooldown": 2},
        {"id": "alpha", "cooldown": 1},
        {"id": "stale", "cooldown": 0},
    ]
    await asyncio.to_thread(save_map, run_id, state)

    battle_result = {
        "result": "battle",
        "loot": {"items": [], "gold": 0},
        "card_choices": [],
        "relic_choices": [],
        "foes": [{"id": "alpha"}, {"id": "beta"}],
        "foe_summons": {},
        "party": [],
        "party_summons": {},
        "gold": 0,
        "relics": [],
        "cards": [],
        "enrage": {"active": False, "stacks": 0},
        "rdr": 0,
        "action_queue": {},
        "ended": True,
    }

    async def fake_resolve(self, party, data, progress, foes, run_id=None):
        return {
            **battle_result,
            "foes": [dict(entry) for entry in battle_result["foes"]],
        }

    monkeypatch.setattr(BattleRoom, "resolve", fake_resolve)

    await battle_room(run_id, {})

    task = battle_tasks.get(run_id)
    if task is not None:
        await task
    else:
        await asyncio.sleep(0)

    state_after, _ = await asyncio.to_thread(load_map, run_id)
    assert state_after.get("recent_foes") == [
        {"id": "gamma", "cooldown": 1},
        {"id": "alpha", "cooldown": RECENT_FOE_COOLDOWN},
        {"id": "beta", "cooldown": RECENT_FOE_COOLDOWN},
    ]
