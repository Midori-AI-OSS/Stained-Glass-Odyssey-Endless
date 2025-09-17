import logging
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import llms.torch_checker as torch_checker

from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.summons.manager import SummonManager


@pytest.mark.asyncio
async def test_on_entity_killed_no_event_loop_warning(monkeypatch, caplog):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    SummonManager.cleanup()

    summoner = Stats()
    summoner.id = "test_summoner"
    summoner.ensure_permanent_summon_slots(1)
    SummonManager.create_summon(summoner, summon_type="test")
    summon = SummonManager.get_summons("test_summoner")[0]

    with caplog.at_level(logging.WARNING, logger="plugins.event_bus"):
        await BUS.emit_async("entity_killed", summon)

    SummonManager.cleanup()
    messages = [record.getMessage().lower() for record in caplog.records]
    assert not any("no event loop" in msg for msg in messages)
    assert SummonManager.get_summons("test_summoner") == []
