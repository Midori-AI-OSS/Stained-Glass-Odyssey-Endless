#!/usr/bin/env python3
"""
Test script to measure performance with 800 DOT effects.
This will help identify async blocking issues.
"""

import asyncio
import time

import pytest

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_many_dots_performance():
    """Test performance with many DOT effects."""

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
            turns=10000,  # 10 turns each
            id=f"dot_{i}",
            source=target
        )
        await manager.add_dot(dot)

    print(f"Added {len(manager.dots)} DOT effects")
    print(f"Target HP: {target.hp}/{target.max_hp}")

    # Measure time for a single tick
    print("\nTesting single tick performance...")
    start_time = time.perf_counter()
    await manager.tick()
    end_time = time.perf_counter()

    tick_duration = end_time - start_time
    print(f"Single tick took: {tick_duration:.4f} seconds")
    print(f"Target HP after tick: {target.hp}/{target.max_hp}")
    print(f"Remaining DOTs: {len(manager.dots)}")

    # Test multiple ticks to simulate battle turns
    print("\nTesting 10 ticks...")
    start_time = time.perf_counter()
    for turn in range(10):
        await manager.tick()
        if turn % 2 == 0:
            print(f"Turn {turn+1}: HP={target.hp}, DOTs={len(manager.dots)}")
    end_time = time.perf_counter()

    total_duration = end_time - start_time
    avg_tick_time = total_duration / 10
    print(f"10 ticks took: {total_duration:.4f} seconds")
    print(f"Average tick time: {avg_tick_time:.4f} seconds")
    print(f"Final target HP: {target.hp}/{target.max_hp}")
    print(f"Final DOT count: {len(manager.dots)}")

    # Estimate battle impact
    print("\nBattle impact analysis:")
    print("With 1 character having 800 DOTs:")
    print(f"  - Each turn would take ~{avg_tick_time:.3f}s just for DOT processing")
    print(f"  - A 100-turn battle would take ~{avg_tick_time * 100:.1f}s for DOTs alone")
    print("With multiple characters each having 800 DOTs:")
    print(f"  - 4 characters = ~{avg_tick_time * 4:.3f}s per turn")
    print(f"  - 100-turn battle = ~{avg_tick_time * 4 * 100:.1f}s for DOTs alone")


if __name__ == "__main__":
    asyncio.run(test_many_dots_performance())
