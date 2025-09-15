import asyncio

from runs.lifecycle import cleanup_battle_state
from runs.lifecycle import get_battle_state_sizes


async def test_get_battle_state_sizes():
    sizes = get_battle_state_sizes()
    assert set(sizes.keys()) == {"tasks", "snapshots", "locks"}
    await cleanup_battle_state()


def test_battle_state_sizes_event_loop():
    asyncio.run(test_get_battle_state_sizes())
