import pytest

#!/usr/bin/env python3
"""
Test script to measure performance improvements with async optimizations.
"""

import asyncio
import time

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_optimized_performance():
    """Test performance with optimized DOT processing."""

    # Create a test character with many DOTs
    target = Stats(hp=10000)
    target.set_base_stat('max_hp', 10000)
    target.set_base_stat('defense', 1)
    target.set_base_stat('mitigation', 1)
    target.set_base_stat('vitality', 1)
    target.id = "test_target"

    # Create effect manager
    manager = EffectManager(target)

    # Add 800 DOT effects
    print("Adding 800 DOT effects...")
    for i in range(800):
        dot = DamageOverTime(
            name=f"test_dot_{i}",
            damage=1,  # Small damage to avoid killing the target too quickly
            turns=10,  # 10 turns each
            id=f"dot_{i}",
            source=target
        )
        await manager.add_dot(dot)

    print(f"Added {len(manager.dots)} DOT effects")
    print(f"Target HP: {target.hp}/{target.max_hp}")

    # Measure time for a single tick with optimizations
    print("\nTesting optimized single tick performance...")
    start_time = time.perf_counter()
    await manager.tick()
    end_time = time.perf_counter()

    tick_duration = end_time - start_time
    print(f"Optimized single tick took: {tick_duration:.4f} seconds")
    print(f"Target HP after tick: {target.hp}/{target.max_hp}")
    print(f"Remaining DOTs: {len(manager.dots)}")

    # Test multiple ticks
    print("\nTesting 5 optimized ticks...")
    start_time = time.perf_counter()
    for turn in range(5):
        await manager.tick()
        print(f"Turn {turn+1}: HP={target.hp}, DOTs={len(manager.dots)}")
    end_time = time.perf_counter()

    total_duration = end_time - start_time
    avg_tick_time = total_duration / 5
    print(f"5 optimized ticks took: {total_duration:.4f} seconds")
    print(f"Average optimized tick time: {avg_tick_time:.4f} seconds")
    print(f"Final target HP: {target.hp}/{target.max_hp}")
    print(f"Final DOT count: {len(manager.dots)}")

    # Calculate improvement
    print("\nPerformance improvement analysis:")
    original_time = 0.446  # From previous test
    improvement_factor = original_time / avg_tick_time if avg_tick_time > 0 else float('inf')
    improvement_percent = ((original_time - avg_tick_time) / original_time) * 100 if original_time > 0 else 0

    print(f"Original tick time: {original_time:.4f}s")
    print(f"Optimized tick time: {avg_tick_time:.4f}s")
    print(f"Improvement factor: {improvement_factor:.2f}x faster")
    print(f"Improvement percentage: {improvement_percent:.1f}% faster")


if __name__ == "__main__":
    asyncio.run(test_optimized_performance())
