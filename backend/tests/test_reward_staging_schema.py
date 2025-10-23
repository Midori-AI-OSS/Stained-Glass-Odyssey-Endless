from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

EXPECTED_EMPTY = {"cards": [], "relics": [], "items": []}

enc: ModuleType | None = None
lifecycle: ModuleType | None = None


def _import_runs_modules() -> tuple[ModuleType, ModuleType]:
    """Load real ``runs`` modules instead of the test stubs."""

    for name in list(sys.modules):
        if name == "runs" or name.startswith("runs."):
            sys.modules.pop(name)
    real_enc = importlib.import_module("runs.encryption")
    real_lifecycle = importlib.import_module("runs.lifecycle")
    return real_enc, real_lifecycle


@pytest.fixture(autouse=True)
def reset_save_manager(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate each test with a dedicated encrypted database and real modules."""

    global enc
    global lifecycle

    enc, lifecycle = _import_runs_modules()

    db_path = tmp_path / "reward-staging.db"
    monkeypatch.setenv("AF_DB_PATH", str(db_path))

    original_manager = getattr(enc, "SAVE_MANAGER", None)
    original_fernet = getattr(enc, "FERNET", None)
    setattr(enc, "SAVE_MANAGER", None)
    setattr(enc, "FERNET", None)

    lifecycle.battle_snapshots.clear()

    try:
        yield
    finally:
        lifecycle.battle_snapshots.clear()
        setattr(enc, "SAVE_MANAGER", original_manager)
        setattr(enc, "FERNET", original_fernet)
        monkeypatch.delenv("AF_DB_PATH", raising=False)


def _insert_run(run_id: str, map_payload: dict[str, object]) -> None:
    assert enc is not None
    manager = enc.get_save_manager()
    with manager.connection() as conn:
        conn.execute(
            "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
            (run_id, json.dumps({}), json.dumps(map_payload)),
        )


def test_load_map_backfills_reward_staging() -> None:
    assert lifecycle is not None
    run_id = "staging-run"
    initial_map = {"rooms": [], "current": 0, "battle": False}
    _insert_run(run_id, initial_map)
    lifecycle.battle_snapshots[run_id] = {"result": "victory"}

    state, rooms = lifecycle.load_map(run_id)
    assert rooms == []

    staging = state.get("reward_staging")
    assert isinstance(staging, dict)
    for bucket in ("cards", "relics", "items"):
        assert staging[bucket] == []

    snapshot = lifecycle.battle_snapshots[run_id]
    assert "reward_staging" in snapshot
    for bucket in ("cards", "relics", "items"):
        assert snapshot["reward_staging"][bucket] == []

    manager = enc.get_save_manager()
    with manager.connection() as conn:
        stored_map = json.loads(
            conn.execute("SELECT map FROM runs WHERE id = ?", (run_id,)).fetchone()[0]
        )
    assert stored_map["reward_staging"] == staging


def test_save_map_initialises_missing_reward_staging() -> None:
    assert lifecycle is not None
    run_id = "staging-save"
    _insert_run(run_id, {"rooms": [], "current": 0, "battle": False})

    state = {"rooms": [], "current": 0, "battle": False}
    lifecycle.save_map(run_id, state)

    assert state["reward_staging"] == EXPECTED_EMPTY

    manager = enc.get_save_manager()
    with manager.connection() as conn:
        stored = json.loads(
            conn.execute("SELECT map FROM runs WHERE id = ?", (run_id,)).fetchone()[0]
        )

    assert stored["reward_staging"] == EXPECTED_EMPTY
