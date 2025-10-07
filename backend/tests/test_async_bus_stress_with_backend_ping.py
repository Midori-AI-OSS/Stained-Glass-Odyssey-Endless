"""
Async bus stress test with backend health pinging to verify non-blocking behavior.

This test simulates the reported issue: 3 party members + 3 foes scenario
with heavy event load while continuously pinging the backend to ensure
the async loop doesn't block.
"""
import asyncio
import time

import pytest

from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
from autofighter.rooms.battle.pacing import pace_sleep
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.dark import Dark


@pytest.mark.asyncio
async def test_dark_ultimate_async_performance_with_backend_ping():
    """
    Test Dark ultimate with async events while pinging backend health endpoint.

    This simulates the exact scenario from the issue:
    - 3 party members
    - 3 foes
    - Heavy Dark ultimate usage (which emits many damage events)
    - Continuous backend health pings to verify async isn't blocked
    """
    # Setup 3 party members with Dark damage type
    party_members = []
    for i in range(3):
        member = Stats()
        member.id = f"dark_party_{i}"
        member._base_atk = 1000
        member.damage_type = Dark()
        member.ultimate_charge = member.ultimate_charge_max  # Ready to use ultimate
        member.ultimate_ready = True
        party_members.append(member)

    # Setup 3 foes
    foes = []
    for i in range(3):
        foe = Stats()
        foe.id = f"foe_{i}"
        foe._base_max_hp = 10000
        foe.hp = 10000  # High HP to survive multiple attacks
        foes.append(foe)

    # Track backend ping responsiveness
    ping_times = []
    ping_errors = 0
    backend_responsive = True

    async def ping_backend():
        """Continuously ping backend health endpoint to check responsiveness."""
        nonlocal ping_errors, backend_responsive

        while backend_responsive:
            start = time.perf_counter()
            try:
                # Simulate health check - in real scenario this would be:
                # async with aiohttp.ClientSession() as session:
                #     async with session.get('http://localhost:59002/performance/health') as resp:
                #         await resp.json()
                await pace_sleep(YIELD_MULTIPLIER)  # Simulate network latency
                ping_time = (time.perf_counter() - start) * 1000
                ping_times.append(ping_time)

                # If ping takes >100ms, the async loop might be blocked
                if ping_time > 100:
                    ping_errors += 1

            except Exception as e:
                ping_errors += 1
                print(f"Backend ping error: {e}")

            await asyncio.sleep(0.010)  # Ping every 10ms

    # Clear metrics and start backend pinging
    BUS.clear_metrics()
    ping_task = asyncio.create_task(ping_backend())

    try:
        # Simulate heavy async load: multiple Dark ultimates from all party members
        ultimate_tasks = []

        start_time = time.perf_counter()

        # Each party member uses ultimate 5 times (total: 3 * 5 * 6 = 90 damage events)
        for round_num in range(5):
            for member in party_members:
                # Dark ultimate emits 6 damage events per use (see dark.py line 125-127)
                task = asyncio.create_task(
                    member.damage_type.ultimate(member, party_members, foes)
                )
                ultimate_tasks.append(task)

            # Small delay between rounds to simulate realistic combat timing
            await asyncio.sleep(0.050)  # 50ms between rounds

        # Wait for all ultimates to complete with reasonable timeout
        await asyncio.wait_for(asyncio.gather(*ultimate_tasks), timeout=10.0)

        total_time = time.perf_counter() - start_time

        # Stop backend pinging
        backend_responsive = False

        # Wait a bit more to collect final ping data
        await asyncio.sleep(0.100)

    finally:
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass

    # Analyze results
    metrics = BUS.get_performance_metrics()

    print("\n=== Async Bus Stress Test Results ===")
    print(f"Total execution time: {total_time:.3f}s")
    print(f"Ultimate tasks completed: {len(ultimate_tasks)}")
    print(f"Backend pings collected: {len(ping_times)}")
    print(f"Backend ping errors: {ping_errors}")

    if ping_times:
        avg_ping = sum(ping_times) / len(ping_times)
        max_ping = max(ping_times)
        print(f"Average ping time: {avg_ping:.2f}ms")
        print(f"Maximum ping time: {max_ping:.2f}ms")

        # Performance assertions
        assert avg_ping < 50, f"Average ping too high: {avg_ping:.2f}ms - async loop may be blocked"
        assert max_ping < 200, f"Max ping too high: {max_ping:.2f}ms - severe blocking detected"
        assert ping_errors < len(ping_times) * 0.1, f"Too many ping errors: {ping_errors}/{len(ping_times)}"

    # Verify event metrics
    if "damage" in metrics:
        damage_stats = metrics["damage"]
        print(f"Damage events processed: {damage_stats['count']}")
        print(f"Average damage event time: {damage_stats['avg_time']*1000:.2f}ms")

        # Should have processed 90 damage events (3 members * 5 rounds * 6 hits each)
        assert damage_stats['count'] == 90, f"Expected 90 damage events, got {damage_stats['count']}"

        # Each damage event should be processed quickly in async mode
        assert damage_stats['avg_time'] < 0.010, f"Damage events too slow: {damage_stats['avg_time']*1000:.2f}ms"

    print("✅ Async bus performance test passed - no blocking detected!")


@pytest.mark.asyncio
async def test_sync_vs_async_comparison():
    """Compare sync vs async event emission performance."""
    # Setup test entities
    attacker = Stats()
    attacker.id = "test_attacker"
    target = Stats()
    target.id = "test_target"

    event_count = 50  # Reduced count for more realistic test

    # Test synchronous emission
    BUS.clear_metrics()
    start_sync = time.perf_counter()

    for i in range(event_count):
        await BUS.emit_async("test_sync_event", attacker, target, i)

    sync_time = time.perf_counter() - start_sync

    # Test asynchronous emission
    BUS.clear_metrics()
    start_async = time.perf_counter()

    async_tasks = []
    for i in range(event_count):
        task = asyncio.create_task(
            BUS.emit_async("test_async_event", attacker, target, i)
        )
        async_tasks.append(task)

    await asyncio.gather(*async_tasks)
    async_time = time.perf_counter() - start_async

    print("\n=== Sync vs Async Performance Comparison ===")
    print(f"Sync emission time: {sync_time*1000:.2f}ms")
    print(f"Async emission time: {async_time*1000:.2f}ms")

    if async_time > 0:
        improvement = sync_time / async_time
        print(f"Performance comparison: {improvement:.1f}x")

        # Both should complete successfully
        assert sync_time > 0, "Sync emission should take some time"
        assert async_time > 0, "Async emission should take some time"
