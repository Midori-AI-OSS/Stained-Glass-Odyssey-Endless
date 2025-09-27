from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from tracking import log_battle_summary
from tracking import log_card_acquisition
from tracking import log_deck_change
from tracking import log_game_action
from tracking import log_menu_action
from tracking import log_play_session_end
from tracking import log_play_session_start
from tracking import log_relic_acquisition
from tracking import log_run_end
from tracking import log_run_start
from tracking.db import sqlcipher3
from tracking.manager import get_tracking_manager


@pytest.mark.asyncio
async def test_log_run_start_and_end(tmp_path, monkeypatch):
    track_path = tmp_path / "track.db"
    monkeypatch.setenv("AF_TRACK_DB_PATH", str(track_path))
    from tracking import manager as tracking_manager

    tracking_manager.TRACKING_MANAGER = None

    await log_run_start(
        "run-1",
        10,
        [
            {"slot": 0, "character_id": "player", "stats": {"hp": 1000}},
            {"slot": 1, "character_id": "ally", "stats": {"hp": 800}},
        ],
    )
    await log_play_session_start("run-1", "local", 10)
    await log_battle_summary(
        "run-1",
        "1",
        5,
        1200,
        300,
        True,
        logs_url="/logs/run-1/battles/1/summary",
        ts=12,
    )
    await log_run_end("run-1", "victory", end_ts=20)
    await log_play_session_end("run-1", logout_ts=21)

    manager = get_tracking_manager()
    with manager.connection() as conn:
        row = conn.execute(
            "SELECT start_ts, end_ts, outcome FROM runs WHERE run_id = ?",
            ("run-1",),
        ).fetchone()
        assert row == (10, 20, "victory")
        members = conn.execute(
            "SELECT COUNT(*) FROM party_members WHERE run_id = ?",
            ("run-1",),
        ).fetchone()[0]
        assert members == 2
        session = conn.execute(
            "SELECT login_ts, logout_ts, duration FROM play_sessions WHERE session_id = ?",
            ("run-1",),
        ).fetchone()
        assert session == (10, 21, 11)
        battle = conn.execute(
            "SELECT turns, dmg_dealt, victory, logs_url FROM battle_summaries WHERE run_id = ?",
            ("run-1",),
        ).fetchone()
        assert battle == (5, 1200, 1, "/logs/run-1/battles/1/summary")


@pytest.mark.asyncio
async def test_item_logging(tmp_path, monkeypatch):
    track_path = tmp_path / "track.db"
    monkeypatch.setenv("AF_TRACK_DB_PATH", str(track_path))
    from tracking import manager as tracking_manager

    tracking_manager.TRACKING_MANAGER = None

    await log_run_start(
        "run-2",
        5,
        [{"slot": 0, "character_id": "player", "stats": {"hp": 1000}}],
    )
    await log_card_acquisition("run-2", "room-a", "card-x", "reward", ts=5)
    await log_deck_change("run-2", "room-a", "reward_add", "card-x", {"source": "reward"}, ts=6)
    await log_relic_acquisition("run-2", "room-b", "relic-y", "shop", ts=7)
    await log_menu_action("Inventory", "view_cards", {"count": 1})

    manager = get_tracking_manager()
    with manager.connection() as conn:
        cards = conn.execute(
            "SELECT card_id, source FROM cards WHERE run_id = ?",
            ("run-2",),
        ).fetchone()
        assert cards == ("card-x", "reward")
        changes = conn.execute(
            "SELECT change_type, card_id FROM deck_changes WHERE run_id = ?",
            ("run-2",),
        ).fetchone()
        assert changes == ("reward_add", "card-x")
        relic = conn.execute(
            "SELECT relic_id, source FROM relics WHERE run_id = ?",
            ("run-2",),
        ).fetchone()
        assert relic == ("relic-y", "shop")
        menu = conn.execute(
            "SELECT menu_item, result FROM menu_actions ORDER BY ts DESC LIMIT 1"
        ).fetchone()
        assert menu[0] == "Inventory"


@pytest.mark.asyncio
async def test_log_game_action_without_run(tmp_path, monkeypatch):
    track_path = tmp_path / "track.db"
    monkeypatch.setenv("AF_TRACK_DB_PATH", str(track_path))
    from tracking import manager as tracking_manager

    tracking_manager.TRACKING_MANAGER = None

    await log_game_action("turn_start", run_id="missing-run", details={"turn": 1})

    manager = get_tracking_manager()
    with manager.connection() as conn:
        row = conn.execute(
            "SELECT run_id, action_type, details_json FROM game_actions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row[0] is None
        assert row[1] == "turn_start"
        assert "turn" in row[2]
        run_count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        assert run_count == 0


@pytest.mark.asyncio
async def test_migration_handles_existing_logs_url(tmp_path, monkeypatch):
    track_path = tmp_path / "track.db"
    monkeypatch.setenv("AF_TRACK_DB_PATH", str(track_path))
    from tracking import manager as tracking_manager

    tracking_manager.TRACKING_MANAGER = None

    conn = sqlcipher3.connect(track_path)
    try:
        conn.execute(
            """
            CREATE TABLE battle_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                room_id TEXT,
                turns INTEGER,
                dmg_dealt INTEGER,
                dmg_taken INTEGER,
                victory INTEGER NOT NULL,
                logs_url TEXT,
                ts INTEGER NOT NULL
            )
            """
        )
        conn.execute("PRAGMA user_version = 1")
        conn.commit()
    finally:
        conn.close()

    manager = get_tracking_manager()
    with manager.connection() as conn:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == 2
        columns = [row[1] for row in conn.execute("PRAGMA table_info('battle_summaries')")]
        assert "logs_url" in columns
