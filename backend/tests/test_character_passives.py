import asyncio
import random

import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.generic import Generic
from plugins.effects.aftertaste import Aftertaste
from plugins.passives.normal.hilander_critical_ferment import HilanderCriticalFerment
from plugins.passives.normal.mezzy_gluttonous_bulwark import MezzyGluttonousBulwark


@pytest.mark.asyncio
async def test_luna_lunar_reservoir_passive():
    """Test Luna's Lunar Reservoir passive charging system."""
    registry = PassiveRegistry()

    # Create Luna with the passive
    luna = Stats(hp=1000, damage_type=Generic())
    luna.passives = ["luna_lunar_reservoir"]

    # Initially should have default attack count (1)
    await registry.trigger("action_taken", luna)
    assert luna.actions_per_turn == 2  # Should get 2 attacks (below 35 charge)

    # After multiple actions, should scale up
    for _ in range(10):  # Build charge to 11 total
        await registry.trigger("action_taken", luna)

    # Should still be at 2 attacks (below 35 charge)
    assert luna.actions_per_turn == 2

    # Build to 35+ charge
    for _ in range(25):  # Total 36 charge
        await registry.trigger("action_taken", luna)

    assert luna.actions_per_turn == 4  # 35-49 range

    # Build to 50+ charge
    for _ in range(15):  # Total 51 charge
        await registry.trigger("action_taken", luna)

    assert luna.actions_per_turn == 8  # 50-69 range


@pytest.mark.asyncio
async def test_graygray_counter_maestro_passive():
    """Test Graygray's Counter Maestro passive retaliation."""
    registry = PassiveRegistry()

    # Create Graygray with the passive
    graygray = Stats(hp=1000, damage_type=Generic())
    graygray.passives = ["graygray_counter_maestro"]

    # Create an attacker
    attacker = Stats(hp=1000, damage_type=Generic())

    # Trigger damage taken (which should trigger counter)
    await registry.trigger_damage_taken(graygray, attacker, 100)

    # Graygray should have gained attack buff from counter
    # Note: The StatEffect system would need to be properly integrated
    # For now, we just verify the passive was triggered without error
    assert len(graygray._active_effects) > 0  # Should have received effects


@pytest.mark.asyncio
async def test_mezzy_gluttonous_bulwark_passive():
    """Test Mezzy's Gluttonous Bulwark passive siphons from allies."""
    registry = PassiveRegistry()

    mezzy = Stats(hp=2000, damage_type=Generic())
    ally = Stats(hp=2000, damage_type=Generic())
    mezzy.passives = ["mezzy_gluttonous_bulwark"]
    mezzy.allies = [ally]

    await registry.trigger("turn_start", mezzy)
    first = MezzyGluttonousBulwark._siphoned_stats[id(ally)]["atk"]

    await registry.trigger("turn_start", mezzy)
    second = MezzyGluttonousBulwark._siphoned_stats[id(ally)]["atk"]

    assert second > first
    assert any(e.name.startswith("mezzy_gluttonous_bulwark_gain") for e in mezzy._active_effects)
    assert any(e.name.startswith("mezzy_gluttonous_bulwark_siphon") for e in ally._active_effects)


@pytest.mark.asyncio
async def test_ally_overload_passive():
    """Test Ally's Overload passive twin dagger system."""
    registry = PassiveRegistry()

    # Create Ally with the passive
    ally = Stats(hp=1000, damage_type=Generic())
    ally.passives = ["ally_overload"]

    # Initially should have default attack count (1)
    await registry.trigger("action_taken", ally)
    assert ally.actions_per_turn == 2  # Should get twin daggers

    # After enough actions to build charge, should be able to activate Overload
    # Each action gives +10 charge but -5 from decay when inactive
    # Net gain is +5 per action, so need 20 actions to reach 100 charge
    for _ in range(20):  # Build 100+ charge
        await registry.trigger("action_taken", ally)

    # Should now have Overload active (4 attacks)
    assert ally.actions_per_turn == 4


@pytest.mark.asyncio
async def test_passive_registry_handles_unknown_passive():
    """Test that the registry handles unknown passives gracefully."""
    registry = PassiveRegistry()

    # Create entity with unknown passive
    entity = Stats(hp=1000, damage_type=Generic())
    entity.passives = ["unknown_passive"]

    # Should not raise an error
    await registry.trigger("action_taken", entity)
    await registry.trigger_damage_taken(entity, None, 0)
    await registry.trigger_turn_end(entity)


@pytest.mark.asyncio
async def test_passive_registry_handles_no_passives():
    """Test that the registry handles entities with no passives."""
    registry = PassiveRegistry()

    # Create entity with no passives
    entity = Stats(hp=1000, damage_type=Generic())
    entity.passives = []

    # Should not raise an error
    await registry.trigger("action_taken", entity)
    await registry.trigger_damage_taken(entity, None, 0)
    await registry.trigger_turn_end(entity)


@pytest.mark.asyncio
async def test_hilander_critical_ferment_passive():
    """Test Hilander's Critical Ferment passive stacking and consumption."""
    registry = PassiveRegistry()

    # Create Hilander with the passive
    hilander = Stats(hp=1000, damage_type=Generic())
    hilander.passives = ["hilander_critical_ferment"]

    # Initially should have no stacks
    initial_effects = len(hilander._active_effects)

    # Landing hits should build stacks
    await registry.trigger("hit_landed", hilander)
    await registry.trigger("hit_landed", hilander)

    # Should have gained crit bonuses
    assert len(hilander._active_effects) > initial_effects


@pytest.mark.asyncio
async def test_hilander_aftertaste_and_soft_cap(monkeypatch):
    """Critical hits trigger Aftertaste and stacking slows after 20."""
    registry = PassiveRegistry()

    hilander = Stats(hp=1000, damage_type=Generic())
    target = Stats(hp=1000, damage_type=Generic())
    hilander.id = "hilander"
    target.id = "target"
    hilander.passives = ["hilander_critical_ferment"]

    monkeypatch.setattr(random, "random", lambda: 0.99)
    for _ in range(25):
        await registry.trigger("hit_landed", hilander)

    assert HilanderCriticalFerment.get_stacks(hilander) == 20

    monkeypatch.setattr(Aftertaste, "rolls", lambda self: [self.base_pot])
    damage_before = target.damage_taken
    set_battle_active(True)
    await BUS.emit_async("critical_hit", hilander, target, 100, "attack")
    await asyncio.sleep(0)
    set_battle_active(False)

    assert target.damage_taken > damage_before
    assert HilanderCriticalFerment.get_stacks(hilander) == 19


@pytest.mark.asyncio
async def test_hilander_soft_cap_min_chance(monkeypatch):
    """Soft cap retains a 1% minimum stacking chance."""
    registry = PassiveRegistry()

    hilander = Stats(hp=1000, damage_type=Generic())
    hilander.passives = ["hilander_critical_ferment"]

    monkeypatch.setattr(random, "random", lambda: 0.0)
    for _ in range(60):
        await registry.trigger("hit_landed", hilander)

    assert HilanderCriticalFerment.get_stacks(hilander) == 60


@pytest.mark.asyncio
async def test_kboshi_flux_cycle_passive():
    """Test Kboshi's Flux Cycle passive element switching."""
    registry = PassiveRegistry()

    # Create Kboshi with the passive
    kboshi = Stats(hp=1000, damage_type=Generic())
    kboshi.passives = ["kboshi_flux_cycle"]

    # Trigger turn start multiple times to test element switching
    switched_count = 0
    attempts = 20  # Test multiple times since switching is probabilistic (80%)

    for _ in range(attempts):
        prev_type = kboshi.damage_type.id
        await registry.trigger("turn_start", kboshi)

        # Check if type changed
        if kboshi.damage_type.id != prev_type:
            switched_count += 1

    # With 80% switch chance over 20 attempts, we should see multiple switches
    assert switched_count > 0, "Kboshi should switch damage types occasionally"

    # Verify the damage type is one of the valid types
    valid_types = ["Fire", "Ice", "Wind", "Lightning", "Light", "Dark"]
    assert kboshi.damage_type.id in valid_types, f"Damage type should be one of {valid_types}, got {kboshi.damage_type.id}"


@pytest.mark.asyncio
async def test_player_level_up_bonus_passive():
    """Test Player's enhanced level-up gains."""
    registry = PassiveRegistry()

    # Create Player with the passive
    player = Stats(hp=1000, damage_type=Generic())
    player.passives = ["player_level_up_bonus"]

    initial_effects = len(player._active_effects)

    # Trigger level up
    await registry.trigger("level_up", player)

    # Should have gained level-up bonus effects
    assert len(player._active_effects) > initial_effects


@pytest.mark.asyncio
async def test_bubbles_bubble_burst_passive():
    """Test Bubbles' Bubble Burst passive."""
    registry = PassiveRegistry()

    # Create Bubbles with the passive
    bubbles = Stats(hp=1000, damage_type=Generic())
    bubbles.passives = ["bubbles_bubble_burst"]

    # Trigger turn start (changes element)
    await registry.trigger("turn_start", bubbles)

    # Should process without error
    # Actual bubble mechanics would need hit tracking integration