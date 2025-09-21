from unittest.mock import AsyncMock

import pytest

from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.relics.pocket_manual import PocketManual


def test_pocket_manual_subscribes_to_hit_landed():
    """Test that PocketManual properly subscribes to hit_landed events."""
    party = Party(members=[], gold=0, relics=[], cards=[], rdr=1.0)

    # Track event subscriptions
    original_subscribe = BUS.subscribe
    subscribed_events = []

    def mock_subscribe(event, callback):
        subscribed_events.append(event)
        return original_subscribe(event, callback)

    BUS.subscribe = mock_subscribe

    try:
        relic = PocketManual()
        relic.apply(party)

        # Verify hit_landed was subscribed to
        assert "hit_landed" in subscribed_events
    finally:
        # Restore original subscribe method
        BUS.subscribe = original_subscribe


@pytest.mark.asyncio
async def test_pocket_manual_triggers_aftertaste():
    """Test that PocketManual triggers aftertaste after 10 hits."""
    # Create mock attacker and target
    attacker = Stats()
    target = Stats()

    # Add attacker to party so the relic can apply to them
    party = Party(members=[attacker], gold=0, relics=[], cards=[], rdr=1.0)

    # Mock the event loop to track tasks
    tasks_created = []

    import asyncio
    original_create_task = asyncio.get_event_loop().create_task

    async def mock_create_task(coro):
        tasks_created.append(coro)
        # Return a mock task that doesn't actually run
        task = AsyncMock()
        return task

    asyncio.get_event_loop().create_task = mock_create_task

    try:
        relic = PocketManual()
        relic.apply(party)

        # Create mock target (attacker is already created above)
        target = Stats()

        # Simulate 9 hits (should not trigger aftertaste)
        for i in range(9):
            await BUS.emit_async("hit_landed", attacker, target, 100)

        assert len(tasks_created) == 0

        # 10th hit should trigger aftertaste
        await BUS.emit_async("hit_landed", attacker, target, 100)

        assert len(tasks_created) >= 1  # At least one aftertaste task should be created

        # 20th hit should trigger aftertaste again
        for i in range(10):
            await BUS.emit_async("hit_landed", attacker, target, 100)

        assert len(tasks_created) >= 2  # At least two aftertaste tasks should be created

    finally:
        # Restore original create_task
        asyncio.get_event_loop().create_task = original_create_task