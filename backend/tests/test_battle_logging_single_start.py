import json

from battle_logging import writers as battle_logging
from battle_logging.writers import RunLogger
from battle_logging.writers import end_run_logging
import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle import BattleRoom
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_battle_logging_single_start(tmp_path):
    end_run_logging()
    battle_logging._current_run_logger = RunLogger("test_run", base_logs_path=tmp_path)
    try:
        node = MapNode(room_id=0, room_type="battle-normal", floor=1, index=1, loop=1, pressure=0)
        room = BattleRoom(node)
        player = Stats()
        player._base_max_hp = 10
        player.hp = 10
        player._base_atk = 1000
        player._base_defense = 0
        player.id = "p1"
        foe = Stats()
        foe._base_max_hp = 1
        foe.hp = 1
        foe._base_atk = 0
        foe._base_defense = 0
        foe.id = "f1"
        party = Party(members=[player])

        await room.resolve(party, {}, foe=foe)

        run_logger = battle_logging._current_run_logger
        assert run_logger.battle_count == 1

        battle_dir = tmp_path / "runs" / "test_run" / "battles"
        folders = list(battle_dir.iterdir())
        assert len(folders) == 1

        summary_file = folders[0] / "summary" / "battle_summary.json"
        with open(summary_file) as f:
            summary = json.load(f)
        assert summary["battle_id"].endswith("_1")
        assert summary["result"] != "interrupted"
    finally:
        end_run_logging()
