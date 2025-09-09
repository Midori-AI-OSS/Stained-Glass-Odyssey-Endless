"""
Comprehensive stress test to demonstrate event bus performance improvements
with 100 fallback effects scenario requested by @lunamidori5.
"""

import asyncio
import time

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats


class TestEventBusStressWithFallbackEffects:
    """Stress test simulating 100 fallback effects during combat."""

    def test_100_fallback_effects_sync_performance(self):
        """Test current sync performance with 100 fallback effects subscribed to damage events."""
        # Simulate 100 entities with fallback effects (like Aftertaste)
        fallback_count = 100
        damage_events_handled = 0
        processing_times = []

        def fallback_effect_handler(effect_id):
            """Simulate a fallback effect that processes damage events."""

            def handler(attacker, target, amount, *args):
                nonlocal damage_events_handled
                start = time.perf_counter()

                # Simulate fallback effect processing (like Aftertaste calculation)
                # This includes random number generation, damage type selection, etc.
                time.sleep(0.0005)  # 0.5ms processing time per effect (realistic)

                processing_times.append(time.perf_counter() - start)
                damage_events_handled += 1

            return handler

        # Subscribe 100 fallback effects to damage_dealt event
        effect_handlers = []
        for i in range(fallback_count):
            handler = fallback_effect_handler(f"fallback_effect_{i}")
            effect_handlers.append(handler)
            BUS.subscribe("damage_dealt", handler)

        try:
            print("\n=== 100 Fallback Effects Stress Test ===")
            print(
                f"Simulating {fallback_count} fallback effects subscribed to damage events"
            )

            # Simulate a combat turn with multiple damage instances
            attacker = Stats()
            attacker.id = "main_attacker"
            target = Stats()
            target.id = "target"

            # Test single damage event processing time
            start_time = time.perf_counter()
            BUS.emit(
                "damage_dealt",
                attacker,
                target,
                100,
                "attack",
                None,
                None,
                "Normal Attack",
            )
            single_event_time = time.perf_counter() - start_time

            print(
                f"Single damage event processing time: {single_event_time*1000:.1f}ms"
            )
            print(f"Events handled by effects: {damage_events_handled}")
            print(
                f"Average processing time per effect: {(single_event_time/fallback_count)*1000:.3f}ms"
            )

            # Reset counters for burst test
            damage_events_handled = 0
            processing_times.clear()

            # Test burst scenario (multiple rapid damage events)
            burst_size = 20
            start_time = time.perf_counter()

            for i in range(burst_size):
                BUS.emit(
                    "damage_dealt",
                    attacker,
                    target,
                    25 + i,
                    "attack",
                    None,
                    None,
                    f"Attack_{i}",
                )

            burst_time = time.perf_counter() - start_time

            print(f"\nBurst test ({burst_size} events):")
            print(f"Total burst processing time: {burst_time*1000:.1f}ms")
            print(f"Total effect invocations: {damage_events_handled}")
            print(f"Average time per event: {(burst_time/burst_size)*1000:.1f}ms")
            print(f"Events per second: {burst_size/burst_time:.0f}")

            # Performance analysis
            if single_event_time > 0.016:  # >16ms blocks 60fps
                print(
                    f"❌ PERFORMANCE ISSUE: Single event blocks UI for {single_event_time*1000:.1f}ms"
                )

            if burst_time > 0.1:  # >100ms burst severely impacts UX
                print(
                    f"❌ SEVERE BLOCKING: Burst processing blocks UI for {burst_time*1000:.1f}ms"
                )

            # Expected behavior: each event should cause significant blocking
            assert (
                single_event_time > 0.04
            ), f"Expected blocking behavior not observed: {single_event_time*1000:.1f}ms"
            assert damage_events_handled == burst_size * fallback_count

        finally:
            # Cleanup
            for handler in effect_handlers:
                BUS.unsubscribe("damage_dealt", handler)

    @pytest.mark.asyncio
    async def test_100_fallback_effects_async_improvement(self):
        """Test async performance improvement with 100 fallback effects."""
        fallback_count = 100
        async_events_handled = 0
        async_processing_times = []

        async def async_fallback_effect_handler(effect_id):
            """Async version of fallback effect handler."""

            async def handler(attacker, target, amount, *args):
                nonlocal async_events_handled
                start = time.perf_counter()

                # Simulate async fallback effect processing
                await asyncio.sleep(0.0005)  # 0.5ms async processing

                async_processing_times.append(time.perf_counter() - start)
                async_events_handled += 1

            return handler

        # Subscribe 100 async fallback effects
        async_handlers = []
        for i in range(fallback_count):
            handler = await async_fallback_effect_handler(f"async_fallback_{i}")
            async_handlers.append(handler)
            BUS.subscribe("damage_dealt", handler)

        try:
            print("\n=== Async Performance Improvement Test ===")

            attacker = Stats()
            attacker.id = "async_attacker"
            target = Stats()
            target.id = "async_target"

            # Test async single event
            start_time = time.perf_counter()
            await BUS.emit_async(
                "damage_dealt",
                attacker,
                target,
                100,
                "attack",
                None,
                None,
                "Async Attack",
            )
            async_single_time = time.perf_counter() - start_time

            print(f"Async single event time: {async_single_time*1000:.1f}ms")
            print(f"Async events handled: {async_events_handled}")

            # Reset for burst test
            async_events_handled = 0
            async_processing_times.clear()

            # Test async burst
            burst_size = 20
            start_time = time.perf_counter()

            for i in range(burst_size):
                await BUS.emit_async(
                    "damage_dealt",
                    attacker,
                    target,
                    25 + i,
                    "attack",
                    None,
                    None,
                    f"AsyncAttack_{i}",
                )

            async_burst_time = time.perf_counter() - start_time

            print(f"\nAsync burst test ({burst_size} events):")
            print(f"Total async burst time: {async_burst_time*1000:.1f}ms")
            print(f"Total async invocations: {async_events_handled}")
            print(f"Async events per second: {burst_size/async_burst_time:.0f}")

            # The async version should be significantly faster
            # Performance should be much better due to concurrent execution
            print("\n=== Performance Comparison ===")

            # We expect dramatic improvement with async processing
            if async_single_time < 0.01:  # <10ms is much better
                print(
                    f"✅ ASYNC IMPROVEMENT: Event processing reduced to {async_single_time*1000:.1f}ms"
                )

            if async_burst_time < 0.05:  # <50ms burst is much better
                print(
                    f"✅ ASYNC BURST IMPROVEMENT: Burst reduced to {async_burst_time*1000:.1f}ms"
                )

        finally:
            # Cleanup
            for handler in async_handlers:
                BUS.unsubscribe("damage_dealt", handler)

    def test_event_bus_batching_performance(self):
        """Test the new batching functionality for high-frequency events."""
        fallback_count = 50  # Smaller number for batching test
        batched_events = []

        def batching_effect_handler(effect_id):
            def handler(*args):
                batched_events.append((effect_id, time.perf_counter(), args))

            return handler

        # Subscribe handlers to high-frequency events
        handlers = []
        for i in range(fallback_count):
            handler = batching_effect_handler(f"batch_effect_{i}")
            handlers.append(handler)
            BUS.subscribe("damage_dealt", handler)

        try:
            print("\n=== Event Batching Performance Test ===")

            attacker = Stats()
            attacker.id = "batch_attacker"
            target = Stats()
            target.id = "batch_target"

            # Test batched emission
            start_time = time.perf_counter()

            # Use emit_batched for high-frequency events
            for i in range(10):
                BUS.emit_batched(
                    "damage_dealt",
                    attacker,
                    target,
                    10 + i,
                    "attack",
                    None,
                    None,
                    f"Batch_{i}",
                )

            batch_time = time.perf_counter() - start_time

            print(f"Batched emission time: {batch_time*1000:.3f}ms")
            print(f"Events processed immediately: {len(batched_events)}")

            # Batching should be very fast for emission
            assert (
                batch_time < 0.01
            ), f"Batching should be fast: {batch_time*1000:.1f}ms"

        finally:
            for handler in handlers:
                BUS.unsubscribe("damage_dealt", handler)

    def test_performance_metrics_collection(self):
        """Test that performance metrics are being collected properly."""
        print("\n=== Performance Metrics Test ===")

        # Clear metrics first
        BUS.clear_metrics()

        # Generate some events with known timing
        def slow_handler(*args):
            time.sleep(0.02)  # 20ms - intentionally slow

        def fast_handler(*args):
            time.sleep(0.001)  # 1ms - normal speed

        BUS.subscribe("test_slow", slow_handler)
        BUS.subscribe("test_fast", fast_handler)

        try:
            # Emit events
            BUS.emit("test_slow", "data")
            BUS.emit("test_fast", "data")
            BUS.emit("test_fast", "data")  # Emit twice

            # Check metrics
            metrics = BUS.get_performance_metrics()

            print(f"Collected metrics: {metrics}")

            assert "test_slow" in metrics
            assert "test_fast" in metrics

            slow_stats = metrics["test_slow"]
            fast_stats = metrics["test_fast"]

            assert slow_stats["count"] == 1
            assert fast_stats["count"] == 2
            assert slow_stats["avg_time"] > 0.015  # Should be ~20ms
            assert fast_stats["avg_time"] < 0.005  # Should be ~1ms

            print(f"✅ Slow event average: {slow_stats['avg_time']*1000:.1f}ms")
            print(f"✅ Fast event average: {fast_stats['avg_time']*1000:.1f}ms")

        finally:
            BUS.unsubscribe("test_slow", slow_handler)
            BUS.unsubscribe("test_fast", fast_handler)
