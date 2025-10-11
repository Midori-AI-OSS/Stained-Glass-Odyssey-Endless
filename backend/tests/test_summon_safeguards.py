"""
Tests for summon safeguards to prevent infinite summoning chains.
"""

from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import llms.torch_checker as torch_checker

from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager
from plugins.characters.ally import Ally


@pytest.mark.asyncio
async def test_summons_cannot_create_more_summons(monkeypatch):
    """Test that summons are prevented from creating more summons."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Clean up any existing state
    SummonManager.cleanup()

    # Create original summoner
    original_summoner = Ally()
    original_summoner.id = "original_summoner"
    original_summoner.ensure_permanent_summon_slots(1)

    # Create a summon from the original summoner
    first_summon = await SummonManager.create_summon(
        summoner=original_summoner,
        summon_type="first_summon",
        source="test_source"
    )

    assert first_summon is not None
    assert isinstance(first_summon, Summon)

    # Now try to create a summon from the first summon (this should be blocked)
    second_summon = await SummonManager.create_summon(
        summoner=first_summon,  # Summon trying to create another summon
        summon_type="second_summon",
        source="test_source"
    )

    # This should return None due to safeguard
    assert second_summon is None

    # Verify only the original summon exists
    all_summons = SummonManager.get_all_summons()
    assert len(all_summons) == 1
    assert all_summons[0].id == first_summon.id


@pytest.mark.asyncio
async def test_regular_entities_can_still_create_summons(monkeypatch):
    """Test that regular (non-summon) entities can still create summons normally."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Clean up any existing state
    SummonManager.cleanup()

    # Create regular entities
    player1 = Ally()
    player1.id = "player1"
    player1.ensure_permanent_summon_slots(1)

    player2 = Ally()
    player2.id = "player2"
    player2.ensure_permanent_summon_slots(1)

    # Both should be able to create summons
    summon1 = await SummonManager.create_summon(
        summoner=player1,
        summon_type="summon1",
        source="test_source"
    )

    summon2 = await SummonManager.create_summon(
        summoner=player2,
        summon_type="summon2",
        source="test_source"
    )

    assert summon1 is not None
    assert summon2 is not None
    assert isinstance(summon1, Summon)
    assert isinstance(summon2, Summon)

    # Verify both summons exist
    all_summons = SummonManager.get_all_summons()
    assert len(all_summons) == 2


@pytest.mark.asyncio
async def test_summon_identification_works(monkeypatch):
    """Test that the system can correctly identify summons vs regular entities."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Clean up any existing state
    SummonManager.cleanup()

    # Create regular entity and summon
    player = Ally()
    player.id = "player"
    player.ensure_permanent_summon_slots(1)

    summon = await SummonManager.create_summon(
        summoner=player,
        summon_type="test_summon",
        source="test_source"
    )

    # Test identification
    assert not isinstance(player, Summon)
    assert isinstance(summon, Summon)

    # Test that summon has expected summon properties
    assert hasattr(summon, 'summoner_id')
    assert hasattr(summon, 'summon_type')
    assert hasattr(summon, 'summon_source')
    assert summon.summoner_id == "player"
    assert summon.summon_type == "test_summon"
    assert summon.summon_source == "test_source"


@pytest.mark.asyncio
async def test_summon_safeguard_logging(monkeypatch, caplog):
    """Test that the safeguard logs appropriate warning when blocking summon creation."""
    import logging
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    # Set logging level to capture warnings
    caplog.set_level(logging.WARNING)

    # Clean up any existing state
    SummonManager.cleanup()

    # Create original summoner and first summon
    player = Ally()
    player.id = "test_player"
    player.ensure_permanent_summon_slots(1)

    first_summon = await SummonManager.create_summon(
        summoner=player,
        summon_type="first_summon",
        source="test_source"
    )

    assert first_summon is not None

    # Try to create summon from summon (should be blocked and logged)
    second_summon = await SummonManager.create_summon(
        summoner=first_summon,
        summon_type="second_summon",
        source="test_source"
    )

    # Verify blocking worked
    assert second_summon is None

    # Verify warning was logged
    assert any("attempted to create another summon - blocked for safety" in record.message
              for record in caplog.records if record.levelno >= logging.WARNING)
