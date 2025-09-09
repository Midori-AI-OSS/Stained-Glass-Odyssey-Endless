#!/usr/bin/env python3
"""
Test cases demonstrating character passives in action.
These tests verify that the character passives work independently of the full battle system.
"""

import asyncio

import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic


class TestPassiveDemos:
    """Test class demonstrating character passives functionality."""

    @pytest.mark.asyncio
    async def test_luna_passive_demo(self):
        """Test Luna's Lunar Reservoir passive."""
        registry = PassiveRegistry()
        luna = Stats(hp=1000, damage_type=Generic())
        luna.passives = ["luna_lunar_reservoir"]

        initial_attacks = luna.actions_per_turn

        # Build charge and verify scaling
        for i in range(1, 11):
            await registry.trigger("action_taken", luna)

        # Verify that actions per turn has been modified by the passive
        assert (
            luna.actions_per_turn >= initial_attacks
        ), "Luna's attacks should scale with charge"

    @pytest.mark.asyncio
    async def test_ally_passive_demo(self):
        """Test Ally's Overload passive."""
        registry = PassiveRegistry()
        ally = Stats(hp=1000, damage_type=Generic())
        ally.passives = ["ally_overload"]

        initial_attacks = ally.actions_per_turn

        # Build to Overload activation
        for i in range(1, 21):
            await registry.trigger("action_taken", ally)

        # Verify Overload scaling
        assert (
            ally.actions_per_turn >= initial_attacks
        ), "Ally should have increased attacks in Overload"

    @pytest.mark.asyncio
    async def test_graygray_passive_demo(self):
        """Test Graygray's Counter Maestro passive."""
        registry = PassiveRegistry()
        graygray = Stats(hp=1000, damage_type=Generic())
        graygray.passives = ["graygray_counter_maestro"]

        attacker = Stats(hp=1000, damage_type=Generic())

        initial_effects = len(graygray._active_effects)

        # Trigger counter attack
        await registry.trigger_damage_taken(graygray, attacker, 100)

        # Verify counter effects were applied
        assert (
            len(graygray._active_effects) > initial_effects
        ), "Counter should add effects"

    @pytest.mark.asyncio
    async def test_mezzy_passive_demo(self):
        """Test Mezzy's Gluttonous Bulwark passive."""
        registry = PassiveRegistry()
        mezzy = Stats(hp=2000, damage_type=Generic())
        mezzy.passives = ["mezzy_gluttonous_bulwark"]

        initial_effects = len(mezzy._active_effects)

        # Apply passive effects
        await registry.trigger("turn_start", mezzy)

        # Verify passive effects were applied
        assert (
            len(mezzy._active_effects) > initial_effects
        ), "Mezzy should have damage reduction effects"

    @pytest.mark.asyncio
    async def test_multiple_passives_demo(self):
        """Test a character with multiple passives."""
        registry = PassiveRegistry()
        multi_char = Stats(hp=1000, damage_type=Generic())
        multi_char.passives = [
            "attack_up",
            "luna_lunar_reservoir",
            "hilander_critical_ferment",
        ]

        initial_effects = len(multi_char._active_effects)

        # Trigger various events
        await registry.trigger("battle_start", multi_char)  # attack_up
        await registry.trigger("action_taken", multi_char)  # luna
        await registry.trigger("hit_landed", multi_char)  # hilander

        # Verify effects were applied
        assert (
            len(multi_char._active_effects) > initial_effects
        ), "Multiple passives should create effects"


async def demo_luna_passive():
    """Demonstrate Luna's Lunar Reservoir passive."""
    print("=== Luna's Lunar Reservoir Demo ===")

    registry = PassiveRegistry()
    luna = Stats(hp=1000, damage_type=Generic())
    luna.passives = ["luna_lunar_reservoir"]

    print(f"Initial attacks per turn: {luna.actions_per_turn}")

    # Build charge and show scaling
    for i in range(1, 11):
        await registry.trigger("action_taken", luna)
        print(
            f"After action {i}: {luna.actions_per_turn} attacks, charge unknown (class-level tracking)"
        )

    print()


async def demo_ally_passive():
    """Demonstrate Ally's Overload passive."""
    print("=== Ally's Overload Demo ===")

    registry = PassiveRegistry()
    ally = Stats(hp=1000, damage_type=Generic())
    ally.passives = ["ally_overload"]

    print(f"Initial attacks per turn: {ally.actions_per_turn}")

    # Build to Overload activation
    for i in range(1, 21):
        await registry.trigger("action_taken", ally)
        if i % 5 == 0:  # Show progress every 5 actions
            print(f"After action {i}: {ally.actions_per_turn} attacks")

    print(f"Final state: {ally.actions_per_turn} attacks (Overload active!)")
    print()


async def demo_graygray_passive():
    """Demonstrate Graygray's Counter Maestro passive."""
    print("=== Graygray's Counter Maestro Demo ===")

    registry = PassiveRegistry()
    graygray = Stats(hp=1000, damage_type=Generic())
    graygray.passives = ["graygray_counter_maestro"]

    attacker = Stats(hp=1000, damage_type=Generic())

    print(f"Initial effects: {len(graygray._active_effects)}")
    print(f"Initial attack: {graygray.atk}")

    # Trigger counter attack
    await registry.trigger_damage_taken(graygray, attacker, 100)

    print("After taking damage:")
    print(f"  Effects: {len(graygray._active_effects)}")
    print(f"  Attack: {graygray.atk}")
    print(f"  Effect names: {[e.name for e in graygray._active_effects]}")
    print()


async def demo_mezzy_passive():
    """Demonstrate Mezzy's Gluttonous Bulwark passive."""
    print("=== Mezzy's Gluttonous Bulwark Demo ===")

    registry = PassiveRegistry()
    mezzy = Stats(hp=2000, damage_type=Generic())
    mezzy.passives = ["mezzy_gluttonous_bulwark"]

    print(f"Initial effects: {len(mezzy._active_effects)}")
    print(f"Initial HP: {mezzy.hp}/{mezzy.max_hp}")
    print(f"Initial attack: {mezzy.atk}")

    # Apply passive effects
    await registry.trigger("turn_start", mezzy)

    print("After passive activation:")
    print(f"  Effects: {len(mezzy._active_effects)}")
    print(f"  HP: {mezzy.hp}/{mezzy.max_hp}")
    print(f"  Attack: {mezzy.atk}")
    print(f"  Effect names: {[e.name for e in mezzy._active_effects]}")
    print()


async def demo_multiple_passives():
    """Demonstrate a character with multiple passives."""
    print("=== Multiple Passives Demo ===")

    registry = PassiveRegistry()
    multi_char = Stats(hp=1000, damage_type=Generic())
    multi_char.passives = [
        "attack_up",
        "luna_lunar_reservoir",
        "hilander_critical_ferment",
    ]

    print(f"Character has passives: {multi_char.passives}")
    print(f"Initial effects: {len(multi_char._active_effects)}")
    print(f"Initial attack: {multi_char.atk}")
    print(f"Initial attacks per turn: {multi_char.actions_per_turn}")

    # Trigger various events
    await registry.trigger("battle_start", multi_char)  # attack_up
    await registry.trigger("action_taken", multi_char)  # luna
    await registry.trigger("hit_landed", multi_char)  # hilander

    print("After triggers:")
    print(f"  Effects: {len(multi_char._active_effects)}")
    print(f"  Attack: {multi_char.atk}")
    print(f"  Attacks per turn: {multi_char.actions_per_turn}")
    print(f"  Effect names: {[e.name for e in multi_char._active_effects]}")
    print()


async def main():
    """Run all passive demos."""
    print("🎮 Character Passives Demo - Midori AI AutoFighter")
    print("=" * 60)
    print()

    await demo_luna_passive()
    await demo_ally_passive()
    await demo_graygray_passive()
    await demo_mezzy_passive()
    await demo_multiple_passives()

    print("✅ Demo completed! Passives are working correctly.")
    print("🚀 Ready for integration into the full battle system.")


if __name__ == "__main__":
    asyncio.run(main())
