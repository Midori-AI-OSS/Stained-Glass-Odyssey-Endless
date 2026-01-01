"""Unit tests for the effects system.

Tests stat modifiers, DoT/HoT effects, buffs, debuffs, and passives.
"""

import pytest

from core.buffs import BuffBase
from core.buffs import BuffRegistry
from core.debuffs import DebuffBase
from core.effect_manager import EffectManager
from core.effects import calculate_diminishing_returns
from core.effects import create_stat_buff
from core.effects import DamageOverTime
from core.effects import get_current_stat_value
from core.effects import HealingOverTime
from core.effects import StatModifier
from core.passives import PassiveRegistry
from core.passives import apply_rank_passives
from core.passives import resolve_passives_for_rank
from core.stats import Stats


def create_test_stats(**kwargs) -> Stats:
    """Helper to create a Stats object with custom base values."""
    stats = Stats()
    stats.__post_init__()
    
    # Set base stats using internal attributes
    if 'base_atk' in kwargs:
        stats._base_atk = kwargs['base_atk']
    if 'base_defense' in kwargs:
        stats._base_defense = kwargs['base_defense']
    if 'base_max_hp' in kwargs:
        stats._base_max_hp = kwargs['base_max_hp']
    if 'hp' in kwargs:
        stats.hp = kwargs['hp']
    
    return stats


class TestDiminishingReturns:
    """Test diminishing returns calculations."""

    def test_no_config_returns_full_effectiveness(self):
        """Stats without diminishing returns config should have 100% effectiveness."""
        result = calculate_diminishing_returns("unknown_stat", 1000)
        assert result == 1.0

    def test_below_threshold_returns_full_effectiveness(self):
        """Values below threshold should have 100% effectiveness."""
        # ATK has base_offset=1000, threshold=100
        result = calculate_diminishing_returns("atk", 1050)  # Only 50 above offset
        assert result == 1.0

    def test_above_threshold_returns_reduced_effectiveness(self):
        """Values above threshold should have reduced effectiveness."""
        # ATK has base_offset=1000, threshold=100, scaling_factor=2.0
        # At 1200 (200 above offset = 2 thresholds), effectiveness = 1/(2^2) = 0.25
        result = calculate_diminishing_returns("atk", 1200)
        assert 0.24 < result < 0.26

    def test_very_high_values_minimum_effectiveness(self):
        """Very high values should hit the minimum effectiveness floor."""
        result = calculate_diminishing_returns("atk", 100000)
        assert result >= 1e-6


class TestGetCurrentStatValue:
    """Test stat value retrieval."""

    def test_get_standard_stats(self):
        """Should retrieve standard stat values."""
        stats = create_test_stats(base_atk=200, base_defense=150, hp=1000)
        
        assert get_current_stat_value(stats, "max_hp") == stats.max_hp
        assert get_current_stat_value(stats, "atk") == stats.atk
        assert get_current_stat_value(stats, "defense") == stats.defense

    def test_get_unknown_stat_returns_zero(self):
        """Unknown stats should return 0."""
        stats = Stats()
        stats.__post_init__()
        result = get_current_stat_value(stats, "nonexistent_stat")
        assert result == 0


class TestStatModifier:
    """Test StatModifier functionality."""

    def test_apply_additive_delta(self):
        """Should apply additive stat changes."""
        stats = create_test_stats(base_atk=100)
        initial_atk = stats.atk
        
        mod = StatModifier(
            stats=stats,
            name="test_buff",
            turns=3,
            id="test_buff_1",
            deltas={"atk": 50},
            bypass_diminishing=True,
        )
        mod.apply()
        
        assert stats.atk > initial_atk

    def test_apply_multiplicative_change(self):
        """Should apply multiplicative stat changes."""
        stats = create_test_stats(base_atk=100)
        initial_atk = stats.atk
        
        mod = StatModifier(
            stats=stats,
            name="test_buff",
            turns=3,
            id="test_buff_1",
            multipliers={"atk": 1.5},
            bypass_diminishing=True,
        )
        mod.apply()
        
        assert stats.atk > initial_atk

    def test_remove_effect(self):
        """Should remove effect from stats."""
        stats = create_test_stats(base_atk=100)
        initial_atk = stats.atk
        
        mod = StatModifier(
            stats=stats,
            name="test_buff",
            turns=3,
            id="test_buff_1",
            deltas={"atk": 50},
            bypass_diminishing=True,
        )
        mod.apply()
        mod.remove()
        
        assert stats.atk == initial_atk

    def test_tick_decrements_duration(self):
        """Should decrement duration on tick."""
        stats = Stats()
        stats.__post_init__()
        
        mod = StatModifier(
            stats=stats,
            name="test_buff",
            turns=3,
            id="test_buff_1",
            deltas={"atk": 50},
        )
        mod.apply()
        
        assert mod.turns == 3
        result = mod.tick()
        assert result is True
        assert mod.turns == 2

    def test_tick_removes_when_expired(self):
        """Should remove effect when duration reaches 0."""
        stats = create_test_stats(base_atk=100)
        
        mod = StatModifier(
            stats=stats,
            name="test_buff",
            turns=1,
            id="test_buff_1",
            deltas={"atk": 50},
            bypass_diminishing=True,
        )
        mod.apply()
        
        result = mod.tick()
        assert result is False
        assert mod.turns == 0


class TestCreateStatBuff:
    """Test create_stat_buff helper function."""

    def test_create_with_deltas(self):
        """Should create buff with additive deltas."""
        stats = create_test_stats(base_atk=100)
        
        buff = create_stat_buff(
            stats,
            name="attack_boost",
            turns=3,
            atk=50,
            bypass_diminishing=True,
        )
        
        assert isinstance(buff, StatModifier)
        assert buff.name == "attack_boost"
        assert buff.turns == 3

    def test_create_with_multipliers(self):
        """Should create buff with multipliers."""
        stats = create_test_stats(base_atk=100)
        
        buff = create_stat_buff(
            stats,
            name="attack_mult",
            turns=3,
            atk_mult=1.5,
            bypass_diminishing=True,
        )
        
        assert buff.multipliers is not None
        assert "atk" in buff.multipliers


class TestDamageOverTime:
    """Test DamageOverTime effects."""

    def test_tick_applies_damage(self):
        """Should apply damage on tick."""
        stats = Stats(hp=1000)
        stats.__post_init__()
        
        dot = DamageOverTime(
            name="Burn",
            damage=50,
            turns=3,
            id="burn_1",
        )
        
        initial_hp = stats.hp
        result = dot.tick(stats)
        
        assert result is True
        assert stats.hp < initial_hp
        assert dot.turns == 2

    def test_tick_expires_after_duration(self):
        """Should expire after duration ends."""
        stats = Stats(hp=1000)
        stats.__post_init__()
        
        dot = DamageOverTime(
            name="Burn",
            damage=50,
            turns=1,
            id="burn_1",
        )
        
        result = dot.tick(stats)
        assert result is False
        assert dot.turns == 0

    def test_tick_stops_on_death(self):
        """Should stop ticking if target dies."""
        stats = Stats(hp=10)
        stats.__post_init__()
        
        dot = DamageOverTime(
            name="Burn",
            damage=500,
            turns=3,
            id="burn_1",
        )
        
        result = dot.tick(stats)
        assert stats.hp == 0
        assert result is False


class TestHealingOverTime:
    """Test HealingOverTime effects."""

    def test_tick_applies_healing(self):
        """Should apply healing on tick."""
        stats = Stats(hp=500)
        stats.__post_init__()
        
        hot = HealingOverTime(
            name="Regen",
            healing=50,
            turns=3,
            id="regen_1",
        )
        
        initial_hp = stats.hp
        result = hot.tick(stats)
        
        assert result is True
        assert stats.hp > initial_hp
        assert hot.turns == 2

    def test_tick_expires_after_duration(self):
        """Should expire after duration ends."""
        stats = Stats(hp=500)
        stats.__post_init__()
        
        hot = HealingOverTime(
            name="Regen",
            healing=50,
            turns=1,
            id="regen_1",
        )
        
        result = hot.tick(stats)
        assert result is False
        assert hot.turns == 0


class TestBuffSystem:
    """Test buff base classes and registry."""

    def test_buff_base_initialization(self):
        """Should initialize buff with default values."""
        buff = BuffBase(id="test_buff", name="Test Buff")
        assert buff.id == "test_buff"
        assert buff.name == "Test Buff"
        assert buff.duration == -1

    def test_buff_apply_to_stats(self):
        """Should apply buff to stats object."""
        stats = create_test_stats(base_atk=100)
        
        buff = BuffBase(
            id="atk_up",
            name="Attack Up",
            stat_modifiers={"atk": 50},
            duration=3,
        )
        
        initial_atk = stats.atk
        effect = buff.apply(stats)
        
        assert effect is not None
        assert stats.atk > initial_atk

    def test_buff_registry_registration(self):
        """Should register and retrieve buffs."""
        registry = BuffRegistry()
        
        class TestBuff(BuffBase):
            pass
        
        registry.register("test", TestBuff)
        retrieved = registry.get_buff("test")
        
        assert retrieved == TestBuff

    def test_buff_registry_apply(self):
        """Should apply buff via registry."""
        registry = BuffRegistry()
        stats = create_test_stats(base_atk=100)
        
        class TestBuff(BuffBase):
            def __init__(self):
                super().__init__(
                    id="test_buff",
                    name="Test Buff",
                    stat_modifiers={"atk": 50},
                )
        
        registry.register("test_buff", TestBuff)
        effect = registry.apply_buff("test_buff", stats)
        
        assert effect is not None


class TestDebuffSystem:
    """Test debuff base classes and registry."""

    def test_debuff_base_initialization(self):
        """Should initialize debuff with default values."""
        debuff = DebuffBase(id="test_debuff", name="Test Debuff")
        assert debuff.id == "test_debuff"
        assert debuff.name == "Test Debuff"

    def test_debuff_apply_negative_modifier(self):
        """Should apply negative stat modifier."""
        stats = create_test_stats(base_atk=100)
        
        debuff = DebuffBase(
            id="atk_down",
            name="Attack Down",
            stat_modifiers={"atk": -30},
            duration=3,
        )
        
        initial_atk = stats.atk
        effect = debuff.apply(stats)
        
        assert effect is not None
        assert stats.atk < initial_atk


class TestEffectManager:
    """Test EffectManager orchestration."""

    def test_add_and_tick_dot(self):
        """Should add and tick DoT effect."""
        stats = Stats(hp=1000)
        stats.__post_init__()
        manager = EffectManager(stats)
        
        dot = DamageOverTime(name="Burn", damage=50, turns=3, id="burn_1")
        manager.add_dot(dot)
        
        assert len(manager.dots) == 1
        
        initial_hp = stats.hp
        manager.tick_dots()
        
        assert stats.hp < initial_hp
        assert len(manager.dots) == 1  # Still active

    def test_add_and_tick_hot(self):
        """Should add and tick HoT effect."""
        stats = Stats(hp=500)
        stats.__post_init__()
        manager = EffectManager(stats)
        
        hot = HealingOverTime(name="Regen", healing=50, turns=3, id="regen_1")
        manager.add_hot(hot)
        
        assert len(manager.hots) == 1
        
        initial_hp = stats.hp
        manager.tick_hots()
        
        assert stats.hp > initial_hp
        assert len(manager.hots) == 1

    def test_tick_all_processes_effects(self):
        """Should process all effect types."""
        stats = create_test_stats(hp=1000, base_atk=100)
        manager = EffectManager(stats)
        
        dot = DamageOverTime(name="Burn", damage=50, turns=2, id="burn_1")
        hot = HealingOverTime(name="Regen", healing=30, turns=2, id="regen_1")
        mod = StatModifier(
            stats=stats,
            name="test_buff",
            turns=2,
            id="test_buff_1",
            deltas={"atk": 50},
        )
        
        manager.add_dot(dot)
        manager.add_hot(hot)
        manager.add_modifier(mod)
        
        results = manager.tick_all()
        
        assert "dots_expired" in results
        assert "hots_expired" in results
        assert "mods_expired" in results

    def test_cleanup_removes_all_effects(self):
        """Should clean up all effects."""
        stats = Stats(hp=1000)
        stats.__post_init__()
        manager = EffectManager(stats)
        
        dot = DamageOverTime(name="Burn", damage=50, turns=3, id="burn_1")
        hot = HealingOverTime(name="Regen", healing=50, turns=3, id="regen_1")
        
        manager.add_dot(dot)
        manager.add_hot(hot)
        
        manager.cleanup()
        
        assert len(manager.dots) == 0
        assert len(manager.hots) == 0
        assert len(manager.mods) == 0


class TestPassiveSystem:
    """Test passive ability system."""

    def test_passive_registry_registration(self):
        """Should register and retrieve passives."""
        registry = PassiveRegistry()
        
        class TestPassive:
            id = "test_passive"
            trigger = "turn_start"
        
        registry.register("test_passive", TestPassive)
        retrieved = registry.get_passive("test_passive")
        
        assert retrieved == TestPassive

    def test_trigger_passive_with_matching_event(self):
        """Should trigger passive for matching event."""
        registry = PassiveRegistry()
        
        triggered = []
        
        class TestPassive:
            trigger = "battle_start"
            
            def apply(self, owner, **kwargs):
                triggered.append(owner)
        
        registry.register("test", TestPassive)
        
        class MockOwner:
            passives = ["test"]
        
        owner = MockOwner()
        registry.trigger("battle_start", owner)
        
        assert len(triggered) == 1

    def test_resolve_passives_for_rank(self):
        """Should resolve tier-specific passive variants."""
        registry = PassiveRegistry()
        
        # Register base and tier variants
        class BasePassive:
            pass
        
        class GlitchedPassive:
            pass
        
        registry.register("test_passive", BasePassive)
        registry.register("test_passive_glitched", GlitchedPassive)
        
        result = resolve_passives_for_rank("test_passive", "glitched", registry)
        assert result == ["test_passive_glitched"]

    def test_apply_rank_passives(self):
        """Should apply rank-specific passive transformations."""
        registry = PassiveRegistry()
        
        class BasePassive:
            pass
        
        class BossPassive:
            pass
        
        registry.register("test_passive", BasePassive)
        registry.register("test_passive_boss", BossPassive)
        
        class MockFoe:
            rank = "boss"
            passives = ["test_passive"]
        
        foe = MockFoe()
        apply_rank_passives(foe, registry)
        
        assert foe.passives == ["test_passive_boss"]
