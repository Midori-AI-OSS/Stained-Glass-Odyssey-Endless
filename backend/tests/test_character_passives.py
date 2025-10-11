import asyncio
import math
import random

import pytest

from autofighter.effects import EffectManager
from autofighter.effects import HealingOverTime
from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.generic import Generic
from plugins.effects.aftertaste import Aftertaste
from plugins.passives.normal.ally_overload import AllyOverload
from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir
from plugins.passives.normal.hilander_critical_ferment import HilanderCriticalFerment
from plugins.passives.normal.mezzy_gluttonous_bulwark import MezzyGluttonousBulwark


@pytest.mark.asyncio
async def test_luna_lunar_reservoir_passive():
    """Test Luna's Lunar Reservoir passive doubling cadence."""
    LunaLunarReservoir._charge_points.clear()
    LunaLunarReservoir._swords_by_owner.clear()

    try:
        # Create Luna with the passive
        luna = Stats(hp=1000, damage_type=Generic())
        luna.passives = ["luna_lunar_reservoir"]

        passive = LunaLunarReservoir()
        await passive.apply(luna, event="action_taken")
        assert LunaLunarReservoir.get_charge(luna) == 1
        assert luna.actions_per_turn == 2

        # Each 25 charge should double the actions per turn
        LunaLunarReservoir.add_charge(luna, 24)
        assert LunaLunarReservoir.get_charge(luna) == 25
        assert luna.actions_per_turn == 4

        LunaLunarReservoir.add_charge(luna, 25)
        assert LunaLunarReservoir.get_charge(luna) == 50
        assert luna.actions_per_turn == 8

        LunaLunarReservoir.add_charge(luna, 25)
        assert LunaLunarReservoir.get_charge(luna) == 75
        assert luna.actions_per_turn == 16

        LunaLunarReservoir.add_charge(luna, 25)
        assert LunaLunarReservoir.get_charge(luna) == 100
        assert luna.actions_per_turn == 32

        # After hitting 32 actions, each additional 25 charge should add +1 action
        LunaLunarReservoir.add_charge(luna, 25)
        assert LunaLunarReservoir.get_charge(luna) == 125
        assert luna.actions_per_turn == 33

        LunaLunarReservoir.add_charge(luna, 75)
        assert LunaLunarReservoir.get_charge(luna) == 200
        assert luna.actions_per_turn == 36
    finally:
        LunaLunarReservoir._charge_points.clear()
        LunaLunarReservoir._swords_by_owner.clear()


@pytest.mark.asyncio
async def test_luna_lunar_reservoir_attack_bonus_scaling():
    """Overflow tiers should scale ATK, SPD, and actions per turn."""
    LunaLunarReservoir._charge_points.clear()
    LunaLunarReservoir._swords_by_owner.clear()

    try:
        luna = Stats(hp=1000, damage_type=Generic())
        luna.passives = ["luna_lunar_reservoir"]
        luna._base_atk = 200
        luna._base_spd = 150

        slot = LunaLunarReservoir._ensure_charge_slot(luna)
        scenarios = (
            (2100, 1),
            (2500, 5),
        )

        for charge, expected_tiers in scenarios:
            LunaLunarReservoir._charge_points[slot] = charge
            LunaLunarReservoir.sync_actions(luna)

            atk_effect = next(
                (e for e in luna.get_active_effects() if e.name == "luna_lunar_reservoir_atk_bonus"),
                None,
            )
            assert atk_effect is not None

            bonus_multiplier = 1 + 0.01 * expected_tiers
            base_doubles = min(charge // 25, 2000)
            if base_doubles <= 4:
                base_actions = 2 << base_doubles
            else:
                base_actions = 32 + (base_doubles - 4)

            expected_atk = int(luna._base_atk * 55 * (bonus_multiplier - 1))
            expected_spd_bonus = luna._base_spd * (bonus_multiplier - 1)
            expected_actions = max(base_actions, int(base_actions * bonus_multiplier))
            expected_runtime_spd = int(max(1, luna._base_spd + expected_spd_bonus))

            assert atk_effect.stat_modifiers["atk"] == expected_atk
            assert atk_effect.stat_modifiers["spd"] == pytest.approx(expected_spd_bonus)
            assert luna.actions_per_turn == expected_actions
            assert luna.spd == expected_runtime_spd

        LunaLunarReservoir._charge_points[slot] = 2000
        LunaLunarReservoir.sync_actions(luna)

        atk_effect = next(
            (e for e in luna.get_active_effects() if e.name == "luna_lunar_reservoir_atk_bonus"),
            None,
        )
        assert atk_effect is None
        base_doubles = min(2000 // 25, 2000)
        base_actions = 32 + (base_doubles - 4)
        assert luna.actions_per_turn == base_actions
        assert luna.spd == luna._base_spd
    finally:
        LunaLunarReservoir._charge_points.clear()
        LunaLunarReservoir._swords_by_owner.clear()


@pytest.mark.asyncio
async def test_luna_lunar_reservoir_no_turn_end_drain():
    """Turn end should no longer drain excess charge."""
    passive = LunaLunarReservoir()
    LunaLunarReservoir._charge_points.clear()
    LunaLunarReservoir._swords_by_owner.clear()

    try:
        luna = Stats(hp=1000, damage_type=Generic())
        luna.passives = ["luna_lunar_reservoir"]

        LunaLunarReservoir.add_charge(luna, 2600)
        before = LunaLunarReservoir.get_charge(luna)
        await passive.on_turn_end(luna)
        after = LunaLunarReservoir.get_charge(luna)
        assert after == before
    finally:
        LunaLunarReservoir._charge_points.clear()
        LunaLunarReservoir._swords_by_owner.clear()


@pytest.mark.asyncio
async def test_luna_glitched_nonboss_actions_double_charge():
    """Glitched non-boss Luna should gain double charge from actions and ultimates."""
    passive = LunaLunarReservoir()

    LunaLunarReservoir._charge_points.clear()
    LunaLunarReservoir._swords_by_owner.clear()

    try:
        luna = Stats(hp=1000, damage_type=Generic())
        luna.rank = "glitched champion"

        starting_charge = LunaLunarReservoir.get_charge(luna)
        await passive.apply(luna, event="action_taken")
        after_action = LunaLunarReservoir.get_charge(luna)

        assert after_action - starting_charge == 2

        await passive.apply(luna, event="ultimate_used")
        after_ultimate = LunaLunarReservoir.get_charge(luna)

        assert after_ultimate - after_action == 128
    finally:
        LunaLunarReservoir._charge_points.clear()
        LunaLunarReservoir._swords_by_owner.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("rank", "expected_multiplier", "damage"),
    [
        ("prime", 5, 1),
        ("glitched prime champion", 10, 2_500_000),
        ("prime boss", 5, 12_345_678_901),
    ],
)
async def test_luna_prime_hit_landed_heals_and_stacks(rank, expected_multiplier, damage):
    """Prime Luna variants should lifesteal and gain multiplied charge on hits."""

    passive = LunaLunarReservoir()

    LunaLunarReservoir._charge_points.clear()
    LunaLunarReservoir._swords_by_owner.clear()

    try:
        luna = Stats(hp=1000, damage_type=Generic())
        luna.passives = ["luna_lunar_reservoir"]
        luna.rank = rank
        luna.hp = luna.max_hp - 100

        before_charge = LunaLunarReservoir.get_charge(luna)
        before_hp = luna.hp

        await passive.apply(luna, event="hit_landed", damage=damage)

        after_charge = LunaLunarReservoir.get_charge(luna)
        expected_heal = max(1, min(32, math.ceil(damage * 0.000001)))

        assert after_charge - before_charge == expected_multiplier
        assert luna.hp - before_hp == expected_heal
    finally:
        LunaLunarReservoir._charge_points.clear()
        LunaLunarReservoir._swords_by_owner.clear()


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
    first = next(
        effect
        for effect in ally._active_effects
        if effect.name == "mezzy_gluttonous_bulwark_siphon_atk"
    ).stat_modifiers["atk"]

    await registry.trigger("turn_start", mezzy)
    second = next(
        effect
        for effect in ally._active_effects
        if effect.name == "mezzy_gluttonous_bulwark_siphon_atk"
    ).stat_modifiers["atk"]

    assert second < first
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
async def test_ally_overload_battle_end_restores_hots():
    """Ensure Overload cleanup restores HoTs when battles end abruptly."""

    AllyOverload._overload_charge.clear()
    AllyOverload._overload_active.clear()
    AllyOverload._add_hot_backup.clear()
    AllyOverload._battle_end_handlers.clear()

    registry = PassiveRegistry()
    ally = Stats(hp=1000, damage_type=Generic())
    ally.effect_manager = EffectManager(ally)
    ally.passives = ["ally_overload"]

    original_add_hot = ally.effect_manager.add_hot

    # Build enough charge to activate Overload and block HoTs.
    for _ in range(21):
        await registry.trigger("action_taken", ally)

    assert ally.actions_per_turn == 4
    assert ally.effect_manager.add_hot is not original_add_hot

    blocked_hot = HealingOverTime("blocked", 5, 2, "blocked")
    await ally.effect_manager.add_hot(blocked_hot)
    assert not ally.effect_manager.hots
    assert not ally.hots

    await BUS.emit_async("battle_end", ally)

    assert not AllyOverload.is_overload_active(ally)
    assert ally.actions_per_turn == 2
    assert ally.effect_manager.add_hot.__func__ is original_add_hot.__func__

    restored_hot = HealingOverTime("restored", 7, 3, "restored")
    await ally.effect_manager.add_hot(restored_hot)

    assert ally.effect_manager.hots == [restored_hot]
    assert ally.hots == [restored_hot.id]
    assert id(ally) not in AllyOverload._add_hot_backup
    assert id(ally) not in AllyOverload._battle_end_handlers


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

    # Trigger level up via the passive directly
    bonus_passive = registry._registry["player_level_up_bonus"]()
    await bonus_passive.apply(player, player.level + 1)

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
