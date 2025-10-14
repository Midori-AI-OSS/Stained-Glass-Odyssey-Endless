"""Tests for Lady of Fire Infernal Momentum passive - burn and HoT mechanics."""
import asyncio
import sys
import types

from autofighter.effects import EffectManager
from autofighter.party import Party
from plugins.characters._base import PlayerBase
from plugins.passives.normal.lady_of_fire_infernal_momentum import (
    LadyOfFireInfernalMomentum,
)


def setup_event_loop():
    """Set up an event loop for testing."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def test_infernal_momentum_burn_counter():
    """Test that Infernal Momentum applies burn DoT to attackers."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create Lady of Fire
    lady = PlayerBase()
    lady.id = "lady_of_fire"
    lady.set_base_stat("max_hp", 100)
    lady.set_base_stat("atk", 50)
    lady.hp = 50
    lady.effect_manager = EffectManager(lady)
    party.members.append(lady)

    # Create attacker
    attacker = PlayerBase()
    attacker.id = "attacker"
    attacker.set_base_stat("max_hp", 100)
    attacker.hp = 100
    attacker.effect_manager = EffectManager(attacker)

    # Apply passive when taking damage
    passive = LadyOfFireInfernalMomentum()
    loop.run_until_complete(passive.apply(lady, attacker, damage=40))

    # Check that burn DoT was applied to attacker
    assert len(attacker.effect_manager.dots) > 0, "Burn DoT should be applied to attacker"
    burn_dot = attacker.effect_manager.dots[0]
    assert burn_dot.damage > 0, "Burn should have positive damage"
    assert burn_dot.damage == 10, f"Burn should be 25% of 40 damage = 10 (got {burn_dot.damage})"
    assert burn_dot.turns == 1, "Burn should last 1 turn"


def test_infernal_momentum_burn_without_effect_manager():
    """Test that burn works when attacker lacks effect_manager."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()

    # Create Lady of Fire
    lady = PlayerBase()
    lady.id = "lady_of_fire"
    lady.set_base_stat("max_hp", 100)
    lady.hp = 50
    lady.effect_manager = EffectManager(lady)

    # Create attacker without effect_manager
    attacker = PlayerBase()
    attacker.id = "attacker_no_mgr"
    attacker.set_base_stat("max_hp", 100)
    attacker.hp = 100
    # Intentionally do NOT create effect_manager

    # Apply passive
    passive = LadyOfFireInfernalMomentum()
    loop.run_until_complete(passive.apply(lady, attacker, damage=40))

    # Check that effect_manager was created and burn was applied
    assert hasattr(attacker, "effect_manager"), "Effect manager should be created"
    assert len(attacker.effect_manager.dots) > 0, "Burn DoT should be applied"


def test_infernal_momentum_self_damage_hot():
    """Test that self-damage grants HoT to Lady of Fire."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()

    # Create Lady of Fire
    lady = PlayerBase()
    lady.id = "lady_of_fire"
    lady.set_base_stat("max_hp", 100)
    lady.hp = 60
    lady.effect_manager = EffectManager(lady)

    # Apply self-damage HoT
    passive = LadyOfFireInfernalMomentum()
    loop.run_until_complete(passive.on_self_damage(lady, self_damage=20))

    # Check that HoT was applied
    assert len(lady.effect_manager.hots) > 0, "HoT should be applied"
    hot = lady.effect_manager.hots[0]
    assert hot.healing > 0, "HoT should have positive healing"
    assert hot.turns == 2, "HoT should last 2 turns"

    # Simulate HoT tick and check healing happens
    initial_hp = lady.hp
    loop.run_until_complete(lady.effect_manager.tick())
    assert lady.hp > initial_hp, "Lady should be healed by HoT"


def test_infernal_momentum_self_damage_hot_without_effect_manager():
    """Test that self-damage HoT works when Lady lacks effect_manager."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()

    # Create Lady of Fire without effect_manager
    lady = PlayerBase()
    lady.id = "lady_of_fire"
    lady.set_base_stat("max_hp", 100)
    lady.hp = 60
    # Intentionally do NOT create effect_manager

    # Apply self-damage HoT
    passive = LadyOfFireInfernalMomentum()
    loop.run_until_complete(passive.on_self_damage(lady, self_damage=20))

    # Check that effect_manager was created and HoT was applied
    assert hasattr(lady, "effect_manager"), "Effect manager should be created"
    assert len(lady.effect_manager.hots) > 0, "HoT should be applied"


def test_infernal_momentum_burn_scales_with_damage():
    """Test that burn damage scales with incoming damage."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()

    # Test with low damage
    lady1 = PlayerBase()
    lady1.id = "lady1"
    lady1.set_base_stat("max_hp", 100)
    lady1.hp = 50
    lady1.effect_manager = EffectManager(lady1)

    attacker1 = PlayerBase()
    attacker1.id = "attacker1"
    attacker1.set_base_stat("max_hp", 100)
    attacker1.hp = 100
    attacker1.effect_manager = EffectManager(attacker1)

    passive1 = LadyOfFireInfernalMomentum()
    loop.run_until_complete(passive1.apply(lady1, attacker1, damage=20))
    low_burn = attacker1.effect_manager.dots[0].damage

    # Test with high damage
    lady2 = PlayerBase()
    lady2.id = "lady2"
    lady2.set_base_stat("max_hp", 100)
    lady2.hp = 50
    lady2.effect_manager = EffectManager(lady2)

    attacker2 = PlayerBase()
    attacker2.id = "attacker2"
    attacker2.set_base_stat("max_hp", 100)
    attacker2.hp = 100
    attacker2.effect_manager = EffectManager(attacker2)

    passive2 = LadyOfFireInfernalMomentum()
    loop.run_until_complete(passive2.apply(lady2, attacker2, damage=80))
    high_burn = attacker2.effect_manager.dots[0].damage

    # Higher damage should result in more burn
    assert high_burn > low_burn, f"High damage burn ({high_burn}) should be greater than low damage burn ({low_burn})"
