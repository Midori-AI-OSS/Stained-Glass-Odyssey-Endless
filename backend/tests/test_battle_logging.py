import asyncio
import json
from pathlib import Path
import tempfile

from battle_logging.writers import BattleLogger
from battle_logging.writers import RunLogger
import pytest

from autofighter import stats as stats_module
from autofighter.stats import BUS
from autofighter.stats import Stats


@pytest.fixture
def temp_logs_dir():
    """Create a temporary logs directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def test_battle_logger_creates_folder_structure(temp_logs_dir):
    """Test that BattleLogger creates the proper folder structure."""
    run_id = "test_run_123"
    battle_index = 1

    logger = BattleLogger(run_id, battle_index, temp_logs_dir)

    # Check folder structure
    expected_base = temp_logs_dir / "runs" / run_id / "battles" / "1"
    expected_raw = expected_base / "raw"
    expected_summary = expected_base / "summary"

    assert expected_base.exists()
    assert expected_raw.exists()
    assert expected_summary.exists()

    # Check raw log file exists
    assert (expected_raw / "battle.log").exists()

    logger.finalize_battle("test")


@pytest.mark.asyncio
async def test_battle_logger_tracks_events(temp_logs_dir):
    """Test that BattleLogger properly tracks battle events."""
    run_id = "test_run_456"
    battle_index = 1

    logger = BattleLogger(run_id, battle_index, temp_logs_dir)

    # Create mock entities
    attacker = Stats()
    attacker.id = "test_attacker"
    target = Stats()
    target.id = "test_target"

    # Simulate battle events
    await BUS.emit_async("battle_start", attacker)
    await BUS.emit_async("battle_start", target)
    await BUS.emit_async("damage_dealt", attacker, target, 50)
    await BUS.emit_async("hit_landed", attacker, target, 50)

    # Finalize to write summary
    logger.finalize_battle("victory")

    # Check summary files were created
    summary_path = temp_logs_dir / "runs" / run_id / "battles" / "1" / "summary"
    assert (summary_path / "battle_summary.json").exists()
    assert (summary_path / "events.json").exists()
    assert (summary_path / "human_summary.txt").exists()

    # Check summary content
    with open(summary_path / "battle_summary.json") as f:
        summary = json.load(f)

    assert summary["result"] == "victory"
    assert summary["total_damage_dealt"]["test_attacker"] == 50
    assert summary["total_hits_landed"]["test_attacker"] == 1

    # Check events content
    with open(summary_path / "events.json") as f:
        events = json.load(f)

    assert len(events) == 4  # 2 battle_start, 1 damage_dealt, 1 hit_landed
    event_types = [e["event_type"] for e in events]
    assert "battle_start" in event_types
    assert "damage_dealt" in event_types
    assert "hit_landed" in event_types


def test_run_logging_management(temp_logs_dir):
    """Test run logging start/end functionality."""
    run_id = "test_run_789"

    run_logger = RunLogger(run_id, temp_logs_dir)
    assert run_logger is not None
    assert run_logger.run_id == run_id

    # Start and end a battle
    battle_logger = run_logger.start_battle()
    assert battle_logger is not None

    run_logger.end_battle("victory")

    # Finalize run
    run_logger.finalize_run()

    # Check that run folder exists
    run_path = temp_logs_dir / "runs" / run_id
    assert run_path.exists()


@pytest.mark.asyncio
async def test_human_readable_summary(temp_logs_dir):
    """Test that human-readable summary is generated correctly."""
    run_id = "test_run_readable"
    battle_index = 1

    logger = BattleLogger(run_id, battle_index, temp_logs_dir)

    # Simulate some events
    attacker = Stats()
    attacker.id = "hero"
    target = Stats()
    target.id = "monster"

    await BUS.emit_async("battle_start", attacker)
    await BUS.emit_async("battle_start", target)
    await BUS.emit_async("damage_dealt", attacker, target, 100)
    await BUS.emit_async("damage_taken", target, attacker, 100)
    await BUS.emit_async("hit_landed", attacker, target, 100)
    await BUS.emit_async("heal", attacker, attacker, 25)

    logger.finalize_battle("victory")

    # Check human summary content
    summary_path = temp_logs_dir / "runs" / run_id / "battles" / "1" / "summary"
    with open(summary_path / "human_summary.txt") as f:
        content = f.read()

    assert "Battle Summary:" in content
    assert "Result: VICTORY" in content
    assert "hero: 100" in content  # damage dealt
    assert "monster: 100" in content  # damage taken
    assert "hero: 1" in content  # hits landed
    assert "hero: 25" in content  # healing done
    assert "Total Events:" in content


@pytest.mark.asyncio
async def test_damage_dealt_defaults_to_normal_attack(temp_logs_dir):
    run_id = "test_run_normal_attack"
    battle_index = 1
    logger = BattleLogger(run_id, battle_index, temp_logs_dir)

    attacker = Stats()
    attacker.id = "hero"
    target = Stats()
    target.id = "monster"

    await BUS.emit_async("battle_start", attacker)
    await BUS.emit_async("battle_start", target)
    await BUS.emit_async("damage_dealt", attacker, target, 42)

    logger.finalize_battle("victory")

    summary_path = temp_logs_dir / "runs" / run_id / "battles" / "1" / "summary"
    with open(summary_path / "battle_summary.json") as f:
        summary = json.load(f)

    assert summary["damage_by_action"]["hero"]["Normal Attack"] == 42


@pytest.mark.asyncio
async def test_battle_logger_records_overkill_details(temp_logs_dir):
    stats_module.set_battle_active(True)
    run_id = "test_run_overkill"
    battle_index = 1
    logger = BattleLogger(run_id, battle_index, temp_logs_dir)

    attacker = Stats()
    attacker.id = "overkill_attacker"
    attacker._base_crit_rate = 0.0
    attacker.vitality = 1.0

    target = Stats()
    target.id = "overkill_target"
    target._base_max_hp = 100
    target.hp = 100
    target._base_defense = 1
    target.vitality = 1.0
    target.mitigation = 1.0
    target._base_dodge_odds = 0.0
    target.shields = 25

    await BUS.emit_async("battle_start", attacker)
    await BUS.emit_async("battle_start", target)

    try:
        damage_dealt = await target.apply_damage(13, attacker=attacker, action_name="attack")
        assert damage_dealt == 100
        assert target.hp == 0
        assert target.last_shield_absorbed == 25
        assert target.last_overkill == 44

        await asyncio.sleep(0.05)
        logger.finalize_battle("victory")
        await asyncio.sleep(0.05)

        summary_path = temp_logs_dir / "runs" / run_id / "battles" / "1" / "summary"
        with open(summary_path / "battle_summary.json") as f:
            summary = json.load(f)

        assert summary["total_damage_dealt"]["overkill_attacker"] == 100
        assert summary["total_damage_taken"]["overkill_target"] == 100

        with open(summary_path / "events.json") as f:
            events = json.load(f)

        damage_event = next(e for e in events if e["event_type"] == "damage_dealt")
        assert damage_event["amount"] == 100
        assert damage_event["details"]["shield_absorbed"] == 25
        assert damage_event["details"]["hp_damage"] == 100
        assert damage_event["details"]["overkill"] == 44
        assert damage_event["details"]["raw_amount"] == 169

        taken_event = next(e for e in events if e["event_type"] == "damage_taken")
        assert taken_event["amount"] == 100
        assert taken_event["details"]["overkill"] == 44

        kill_event = next(e for e in events if e["event_type"] == "entity_killed")
        assert kill_event["amount"] == 100
        assert kill_event["details"]["overkill"] == 44
    finally:
        stats_module.set_battle_active(False)
