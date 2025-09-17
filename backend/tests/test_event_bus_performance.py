"""
Performance tests for the event bus system to identify blocking behaviors.
Tests with 100+ subscribers to simulate heavy effect load scenarios.
"""
import time

import pytest

from autofighter.rooms.battle.pacing import DOUBLE_YIELD_DELAY
from autofighter.rooms.battle.pacing import YIELD_DELAY
from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
from autofighter.rooms.battle.pacing import pace_sleep
from autofighter.stats import BUS
from autofighter.stats import Stats


class TestEventBusPerformance:
    """Test event bus performance under heavy load scenarios."""

    @pytest.mark.asyncio
    async def test_async_event_yield(self):
        """Ensure async emissions yield at least 2ms per event."""
        async def handler(*args):
            return None

        BUS.subscribe("yield_test", handler)

        try:
            event_count = 5
            start = time.perf_counter()
            for _ in range(event_count):
                await BUS.emit_async("yield_test", "data")
            elapsed = time.perf_counter() - start
            assert elapsed >= event_count * DOUBLE_YIELD_DELAY
        finally:
            BUS.unsubscribe("yield_test", handler)

    def test_sync_emit_with_100_subscribers(self):
        """Test synchronous event emission with 100 subscribers to measure blocking."""
        # Setup: Create 100 mock subscribers that simulate processing time
        processing_times = []
        subscriber_count = 100

        def slow_subscriber(index):
            """Simulate a subscriber that takes time to process (like complex relic effects)."""
            async def handler(*args):
                start = time.perf_counter()
                # Simulate 1ms of processing time per subscriber (realistic for complex effects)
                time.sleep(YIELD_DELAY)
                end = time.perf_counter()
                processing_times.append((index, end - start))
            return handler

        # Subscribe 100 handlers to damage_dealt event
        subscribers = []
        for i in range(subscriber_count):
            handler = slow_subscriber(i)
            subscribers.append(handler)
            BUS.subscribe("damage_dealt", handler)

        try:
            # Measure total time for a single event emission
            start_time = time.perf_counter()

            # Emit a damage event (typical during combat)
            attacker = Stats()
            attacker.id = "test_attacker"
            target = Stats()
            target.id = "test_target"

            await BUS.emit_async("damage_dealt", attacker, target, 100, "attack", None, None, "Normal Attack")

            end_time = time.perf_counter()
            total_time = end_time - start_time

            # Verify all subscribers were called
            assert len(processing_times) == subscriber_count

            # Print performance metrics
            print("\nEvent Bus Performance Test Results:")
            print(f"Total subscribers: {subscriber_count}")
            print(f"Total emission time: {total_time:.4f}s ({total_time*1000:.1f}ms)")
            print(f"Average time per subscriber: {total_time/subscriber_count:.6f}s")
            print(f"Estimated UI blocking time: {total_time*1000:.1f}ms")

            # Performance assertions
            # With 100 subscribers at 1ms each, total should be around 100ms
            # This would cause noticeable UI lag (>16ms for 60fps)
            assert total_time > 0.050  # Should take at least 50ms

            if total_time > 0.016:  # More than one 60fps frame
                print(f"WARNING: Event emission takes {total_time*1000:.1f}ms - may cause UI lag!")

        finally:
            # Cleanup: Unsubscribe all test handlers
            for handler in subscribers:
                BUS.unsubscribe("damage_dealt", handler)

    def test_battle_with_multiple_aftertaste_effects(self):
        """Test performance with multiple Aftertaste effects (realistic heavy load scenario)."""
        # Create multiple entities with Aftertaste-like effects
        aftertaste_count = 50  # Simulate 50 entities with Aftertaste relics

        # Track event emissions
        emission_times = []

        async def track_emission(*args):
            emission_times.append(time.perf_counter())

        BUS.subscribe("damage_dealt", track_emission)

        try:
            start_time = time.perf_counter()

            # Simulate a battle turn with many Aftertaste procs
            attacker = Stats()
            attacker.id = "main_attacker"
            target = Stats()
            target.id = "target"
            target.hp = 10000  # Ensure target survives

            # Simulate initial attack triggering multiple Aftertaste effects
            for i in range(aftertaste_count):
                # Each Aftertaste effect emits a relic_effect event
                await BUS.emit_async("relic_effect", "aftertaste", attacker, "damage", 25, {
                    "effect_type": "aftertaste",
                    "base_damage": 25,
                    "random_damage_type": "Fire",
                    "actual_damage": 25
                })

                # Then emits damage_dealt when damage is applied
                await BUS.emit_async("damage_dealt", attacker, target, 25, "effect", "aftertaste", "Fire", "Aftertaste (Fire)")

            end_time = time.perf_counter()
            total_time = end_time - start_time

            print("\nAftertaste Stress Test Results:")
            print(f"Aftertaste effects simulated: {aftertaste_count}")
            print(f"Total events emitted: {len(emission_times)}")
            print(f"Total processing time: {total_time:.4f}s ({total_time*1000:.1f}ms)")
            print(f"Average time per effect: {total_time/aftertaste_count:.6f}s")

            # With 50 Aftertaste effects, this could easily block UI for 100+ms
            if total_time > 0.050:  # More than 50ms
                print(f"WARNING: Aftertaste cascade takes {total_time*1000:.1f}ms - severe UI blocking!")

        finally:
            BUS.unsubscribe("damage_dealt", track_emission)

    @pytest.mark.asyncio
    async def test_async_emit_performance_comparison(self):
        """Compare async vs sync event emission performance."""
        subscriber_count = 100
        sync_times = []
        async_times = []

        def sync_handler(*args):
            time.sleep(YIELD_DELAY)  # 1ms processing

        async def async_handler(*args):
            await pace_sleep(YIELD_MULTIPLIER)  # 1ms async processing

        # Test synchronous emission
        for i in range(subscriber_count):
            BUS.subscribe("test_sync", sync_handler)

        try:
            start = time.perf_counter()
            await BUS.emit_async("test_sync", "data")
            sync_time = time.perf_counter() - start
            sync_times.append(sync_time)
        finally:
            for i in range(subscriber_count):
                BUS.unsubscribe("test_sync", sync_handler)

        # Test asynchronous emission (if available)
        for i in range(subscriber_count):
            BUS.subscribe("test_async", async_handler)

        try:
            start = time.perf_counter()
            await BUS.emit_async("test_async", "data")
            async_time = time.perf_counter() - start
            async_times.append(async_time)
        finally:
            for i in range(subscriber_count):
                BUS.unsubscribe("test_async", async_handler)

        print("\nSync vs Async Performance Comparison:")
        print(f"Synchronous emission: {sync_time*1000:.1f}ms")
        print(f"Asynchronous emission: {async_time*1000:.1f}ms")
        print(f"Performance improvement: {(sync_time/async_time):.1f}x faster" if async_time > 0 else "N/A")

        # Async should be significantly faster due to concurrent execution
        assert async_time < sync_time

    def test_event_burst_scenario(self):
        """Test performance under event burst scenarios (rapid successive events)."""
        burst_size = 200  # 200 rapid events

        event_times = []

        async def timing_handler(*args):
            event_times.append(time.perf_counter())

        BUS.subscribe("burst_test", timing_handler)

        try:
            start_time = time.perf_counter()

            # Rapid fire events (simulates intense combat with many effects)
            for i in range(burst_size):
                await BUS.emit_async("burst_test", f"event_{i}")

            end_time = time.perf_counter()
            total_time = end_time - start_time

            # Calculate event processing rate
            events_per_second = burst_size / total_time if total_time > 0 else 0

            print("\nEvent Burst Test Results:")
            print(f"Events in burst: {burst_size}")
            print(f"Total time: {total_time:.4f}s ({total_time*1000:.1f}ms)")
            print(f"Events per second: {events_per_second:.0f}")
            print(f"Average time per event: {(total_time/burst_size)*1000:.3f}ms")

            # Verify all events were processed
            assert len(event_times) == burst_size

            # Performance expectation: should handle at least 1000 events/sec
            assert events_per_second > 1000, f"Event processing too slow: {events_per_second:.0f} events/sec"

        finally:
            BUS.unsubscribe("burst_test", timing_handler)