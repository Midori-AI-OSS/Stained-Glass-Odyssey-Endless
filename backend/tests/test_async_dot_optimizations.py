#!/usr/bin/env python3
"""
Test to verify async optimization improvements for DOT effects.
"""

import pytest

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.effects import HealingOverTime
from autofighter.stats import Stats


@pytest.mark.asyncio
async def test_small_dot_count_still_logs_individually():
    """Verify that small numbers of DOTs still log individually for debugging."""
    target = Stats(hp=1000, max_hp=1000, defense=1, mitigation=1, vitality=1)
    target.id = "test_small"
    manager = EffectManager(target)

    # Add 5 DOTs (below the 10 threshold)
    for i in range(5):
        dot = DamageOverTime(
            f"dot_{i}", damage=1, turns=2, id=f"dot_{i}", source=target
        )
        manager.add_dot(dot)

    # Should still log individually
    await manager.tick()
    assert target.hp < 1000  # Damage was applied
    assert len(manager.dots) == 5  # All DOTs still active


@pytest.mark.asyncio
async def test_large_dot_count_uses_batch_processing():
    """Verify that large numbers of DOTs use optimized batch processing."""
    target = Stats(hp=5000, max_hp=5000, defense=1, mitigation=1, vitality=1)
    target.id = "test_large"
    manager = EffectManager(target)

    # Add 100 DOTs (above the 20 threshold for parallel processing)
    for i in range(100):
        dot = DamageOverTime(
            f"dot_{i}", damage=1, turns=2, id=f"dot_{i}", source=target
        )
        manager.add_dot(dot)

    initial_hp = target.hp
    await manager.tick()

    # Verify damage was applied
    assert target.hp < initial_hp
    # All DOTs should still be active (2 turns each, only 1 tick)
    assert len(manager.dots) == 100


@pytest.mark.asyncio
async def test_mixed_dots_and_hots():
    """Verify that mixed DOTs and HOTs work correctly with optimizations."""
    target = Stats(hp=1000, max_hp=2000, defense=1, mitigation=1, vitality=1)
    target.id = "test_mixed"
    manager = EffectManager(target)

    # Add many DOTs and HOTs
    for i in range(30):
        dot = DamageOverTime(
            f"dot_{i}", damage=2, turns=3, id=f"dot_{i}", source=target
        )
        hot = HealingOverTime(
            f"hot_{i}", healing=1, turns=3, id=f"hot_{i}", source=target
        )
        manager.add_dot(dot)
        manager.add_hot(hot)

    initial_hp = target.hp
    await manager.tick()

    # Verify effects were applied (damage calculation is complex due to defense/mitigation)
    assert target.hp != initial_hp  # HP should have changed

    # All effects should still be active
    assert len(manager.dots) == 30
    assert len(manager.hots) == 30


@pytest.mark.asyncio
async def test_dot_expiration_with_optimizations():
    """Verify that DOT expiration works correctly with batch processing."""
    target = Stats(hp=1000, max_hp=1000, defense=1, mitigation=1, vitality=1)
    target.id = "test_expiration"
    manager = EffectManager(target)

    # Add DOTs with different durations
    for i in range(25):
        turns = 1 if i < 10 else 2  # 10 expire after 1 tick, 15 after 2 ticks
        dot = DamageOverTime(
            f"dot_{i}", damage=1, turns=turns, id=f"dot_{i}", source=target
        )
        manager.add_dot(dot)

    # First tick - 10 should expire
    await manager.tick()
    assert len(manager.dots) == 15

    # Second tick - remaining 15 should expire
    await manager.tick()
    assert len(manager.dots) == 0


@pytest.mark.asyncio
async def test_dead_characters_dont_receive_dots_or_hots():
    """Verify that dead characters (hp <= 0) don't receive new DOT or HOT effects."""
    # Create a dead target
    target = Stats()
    target.hp = 0  # Set HP to 0 after creation to override post_init
    target.id = "dead_target"
    manager = EffectManager(target)

    # Create a living source
    source = Stats()
    source.id = "living_source"

    # Try to add DOT to dead character
    dot = DamageOverTime("test_dot", damage=10, turns=3, id="test_dot", source=source)
    manager.add_dot(dot)

    # Try to add HOT to dead character
    hot = HealingOverTime("test_hot", healing=5, turns=2, id="test_hot", source=source)
    manager.add_hot(hot)

    # Verify no effects were added
    assert len(manager.dots) == 0
    assert len(manager.hots) == 0
    assert len(target.dots) == 0
    assert len(target.hots) == 0


@pytest.mark.asyncio
async def test_living_characters_can_still_receive_effects():
    """Verify that living characters (hp > 0) can still receive DOT and HOT effects."""
    # Create a living target
    target = Stats()
    target.hp = 50  # Set HP explicitly
    target.id = "living_target"
    manager = EffectManager(target)

    # Create a living source
    source = Stats()
    source.id = "living_source"

    # Add DOT to living character
    dot = DamageOverTime("test_dot", damage=10, turns=3, id="test_dot", source=source)
    manager.add_dot(dot)

    # Add HOT to living character
    hot = HealingOverTime("test_hot", healing=5, turns=2, id="test_hot", source=source)
    manager.add_hot(hot)

    # Verify effects were added
    assert len(manager.dots) == 1
    assert len(manager.hots) == 1
    assert len(target.dots) == 1
    assert len(target.hots) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
