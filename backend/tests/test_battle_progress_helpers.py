# ruff: noqa: E402


from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from types import ModuleType

writers_module = sys.modules.get("battle_logging.writers")
if writers_module is None:
    battle_logging_pkg = sys.modules.setdefault(
        "battle_logging",
        ModuleType("battle_logging"),
    )
    writers_module = ModuleType("battle_logging.writers")
    setattr(battle_logging_pkg, "writers", writers_module)
    sys.modules["battle_logging.writers"] = writers_module

writers_module.end_run_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.end_battle_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.start_run_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.start_battle_logging = lambda *args, **kwargs: None  # noqa: E731
writers_module.get_current_run_logger = lambda: None  # noqa: E731

tracking_module = sys.modules.setdefault("tracking", ModuleType("tracking"))
tracking_module.log_play_session_end = lambda *args, **kwargs: None  # noqa: E731
tracking_module.log_run_end = lambda *args, **kwargs: None  # noqa: E731


from runs.lifecycle import battle_snapshots as run_snapshots

from autofighter.rooms.battle import snapshots as battle_snapshots
from autofighter.rooms.battle.progress import build_action_queue_snapshot
from autofighter.rooms.battle.progress import build_battle_progress_payload
from autofighter.rooms.battle.progress import collect_summon_snapshots
from autofighter.rooms.battle.turns import EnrageState
from autofighter.stats import Stats
from autofighter.summons.manager import SummonManager


@pytest.fixture(autouse=True)
def cleanup_summons():
    SummonManager.cleanup()
    yield
    SummonManager.cleanup()


@pytest.mark.asyncio
async def test_collect_summon_snapshots_groups_by_owner():
    summoner = Stats(hp=1_000)
    summoner.id = "summoner"
    summoner.ensure_permanent_summon_slots(1)
    summon = SummonManager.create_summon(summoner, summon_type="test", source="unit_test")
    assert summon is not None

    snapshots = await collect_summon_snapshots([summoner])

    assert list(snapshots.keys()) == ["summoner"]
    [payload] = snapshots["summoner"]
    assert payload["owner_id"] == "summoner"
    assert payload["instance_id"] == summon.instance_id
    assert payload["summon_type"] == "test"


@pytest.mark.asyncio
async def test_build_action_queue_snapshot_preserves_sorting_and_bonus_entries():
    party_member = Stats(hp=1_000)
    party_member.id = "party"
    party_member.action_value = 2.0
    party_member.action_gauge = 120
    party_member.base_action_value = 1.8

    foe = Stats(hp=1_000)
    foe.id = "foe"
    foe.action_value = 1.0
    foe.action_gauge = 90
    foe.base_action_value = 1.0

    queue = await build_action_queue_snapshot(
        [party_member],
        [foe],
        {id(party_member): 1},
    )

    assert queue[0]["bonus"] is True
    assert queue[0]["id"] == "party"
    assert [entry["id"] for entry in queue[1:]] == ["foe", "party"]
    assert queue[1]["action_value"] <= queue[2]["action_value"]


@pytest.mark.asyncio
async def test_build_battle_progress_payload_includes_snapshots_and_events():
    run_id = "progress-run"
    party_member = Stats(hp=1_000)
    party_member.id = "hero"
    party_member.ensure_permanent_summon_slots(1)
    hero_summon = SummonManager.create_summon(
        party_member,
        summon_type="sprite",
        source="unit_test",
    )
    assert hero_summon is not None

    foe = Stats(hp=900)
    foe.id = "foe"
    foe.ensure_permanent_summon_slots(1)
    foe_summon = SummonManager.create_summon(
        foe,
        summon_type="minion",
        source="unit_test",
    )
    assert foe_summon is not None

    battle_snapshots.prepare_snapshot_overlay(run_id, [party_member, foe])
    battle_snapshots.mutate_snapshot_overlay(run_id, event={"id": "evt"})
    battle_snapshots.mutate_snapshot_overlay(run_id, status_phase={"phase": "hot"})

    enrage_state = EnrageState(threshold=5)
    enrage_state.active = True
    enrage_state.stacks = 3

    payload = await build_battle_progress_payload(
        [party_member],
        [foe],
        enrage_state,
        rdr=1.25,
        extra_turns={},
        turn=7,
        run_id=run_id,
        active_id=party_member.id,
        active_target_id=foe.id,
        ended=True,
    )

    assert payload["turn"] == 7
    assert payload["party"][0]["id"] == "hero"
    assert payload["foes"][0]["id"] == "foe"
    assert payload["party"][0]["ultimate_max"] == party_member.ultimate_charge_max
    assert payload["foes"][0]["ultimate_max"] == foe.ultimate_charge_max
    assert payload["party_summons"]["hero"][0]["instance_id"] == hero_summon.instance_id
    assert payload["foe_summons"]["foe"][0]["instance_id"] == foe_summon.instance_id
    assert payload["recent_events"] == [{"id": "evt"}]
    assert payload["status_phase"] == {"phase": "hot"}
    assert payload["enrage"]["stacks"] == 3
    assert payload["ended"] is True

    run_snapshots.pop(run_id, None)
