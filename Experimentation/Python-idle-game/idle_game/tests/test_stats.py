"""Unit tests for the Stats system.

Tests core stat calculations, damage/healing formulas, effects, and gauge system.
"""

from pathlib import Path
import random
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stat_effect import StatEffect
from core.stats import GAUGE_START
from core.stats import CharacterType
from core.stats import Stats
from core.stats import get_enrage_percent
from core.stats import set_enrage_percent


class TestStatEffect:
    """Tests for StatEffect class."""

    def test_permanent_effect(self):
        """Permanent effects never expire."""
        effect = StatEffect("test", {"atk": 50}, duration=-1)
        assert not effect.is_expired()
        effect.tick()
        assert not effect.is_expired()
        assert effect.duration == -1

    def test_temporary_effect_expiry(self):
        """Temporary effects expire after ticking down."""
        effect = StatEffect("test", {"atk": 50}, duration=3)
        assert not effect.is_expired()

        effect.tick()
        assert effect.duration == 2
        assert not effect.is_expired()

        effect.tick()
        assert effect.duration == 1
        assert not effect.is_expired()

        effect.tick()
        assert effect.duration == 0
        assert effect.is_expired()

    def test_expired_effect_stays_expired(self):
        """Expired effects stay at 0."""
        effect = StatEffect("test", {"atk": 50}, duration=0)
        assert effect.is_expired()
        effect.tick()
        assert effect.duration == 0
        assert effect.is_expired()


class TestStatsBasics:
    """Basic Stats class functionality."""

    def test_stats_creation(self):
        """Stats can be created with defaults."""
        stats = Stats()
        assert stats.hp == 1000
        assert stats.max_hp == 1000
        assert stats.atk == 200
        assert stats.defense == 200
        assert stats.level == 1

    def test_stats_custom_values(self):
        """Stats can be initialized with custom values."""
        stats = Stats(hp=500, level=10)
        assert stats.hp == 500
        assert stats.level == 10

    def test_character_type_enum(self):
        """CharacterType enum works."""
        assert CharacterType.A.value == "A"
        assert CharacterType.B.value == "B"
        assert CharacterType.C.value == "C"


class TestStatModifiers:
    """Tests for stat modifiers via effects."""

    def test_stat_with_no_effects(self):
        """Base stats returned when no effects."""
        stats = Stats()
        stats._base_atk = 100
        assert stats.atk == 100

    def test_stat_with_single_effect(self):
        """Effects modify stats correctly."""
        stats = Stats()
        stats._base_atk = 100
        effect = StatEffect("atk_up", {"atk": 50})
        stats.add_effect(effect)
        assert stats.atk == 150

    def test_stat_with_multiple_effects(self):
        """Multiple effects stack additively."""
        stats = Stats()
        stats._base_atk = 100
        stats.add_effect(StatEffect("buff1", {"atk": 30}))
        stats.add_effect(StatEffect("buff2", {"atk": 20}))
        assert stats.atk == 150

    def test_effect_replacement(self):
        """Adding effect with same name replaces old one."""
        stats = Stats()
        stats._base_atk = 100
        stats.add_effect(StatEffect("buff", {"atk": 30}))
        assert stats.atk == 130
        stats.add_effect(StatEffect("buff", {"atk": 50}))
        assert stats.atk == 150

    def test_effect_removal_by_name(self):
        """Effects can be removed by name."""
        stats = Stats()
        stats._base_atk = 100
        stats.add_effect(StatEffect("buff", {"atk": 30}))
        assert stats.atk == 130
        assert stats.remove_effect_by_name("buff")
        assert stats.atk == 100
        assert not stats.remove_effect_by_name("nonexistent")

    def test_effect_removal_by_source(self):
        """Effects can be removed by source."""
        stats = Stats()
        stats.add_effect(StatEffect("buff1", {"atk": 10}, source="relic"))
        stats.add_effect(StatEffect("buff2", {"atk": 20}, source="relic"))
        stats.add_effect(StatEffect("buff3", {"atk": 30}, source="card"))
        assert stats.remove_effect_by_source("relic") == 2
        assert len(stats.get_active_effects()) == 1

    def test_tick_effects(self):
        """Tick removes expired temporary effects."""
        stats = Stats()
        stats.add_effect(StatEffect("temp1", {"atk": 10}, duration=2))
        stats.add_effect(StatEffect("temp2", {"atk": 20}, duration=1))
        stats.add_effect(StatEffect("perm", {"atk": 30}, duration=-1))

        assert len(stats.get_active_effects()) == 3

        stats.tick_effects()
        assert len(stats.get_active_effects()) == 2

        stats.tick_effects()
        assert len(stats.get_active_effects()) == 1
        assert stats.get_active_effects()[0].name == "perm"

    def test_clear_all_effects(self):
        """Can clear all effects at once."""
        stats = Stats()
        stats.add_effect(StatEffect("buff1", {"atk": 10}))
        stats.add_effect(StatEffect("buff2", {"atk": 20}))
        stats.clear_all_effects()
        assert len(stats.get_active_effects()) == 0


class TestDamageCalculation:
    """Tests for damage calculations."""

    def test_basic_damage(self):
        """Basic damage without modifiers."""
        stats = Stats()
        stats.hp = 1000
        damage = stats.take_damage(100)
        assert damage > 0
        assert stats.hp < 1000

    def test_damage_with_mitigation(self):
        """Higher defense reduces damage."""
        attacker = Stats()
        attacker._base_atk = 1000

        defender_low = Stats()
        defender_low._base_defense = 100
        defender_low.hp = 10000

        defender_high = Stats()
        defender_high._base_defense = 300
        defender_high.hp = 10000

        damage_low = defender_low.take_damage(5000, attacker)
        damage_high = defender_high.take_damage(5000, attacker)

        assert damage_high < damage_low

    def test_critical_hit(self):
        """Critical hits increase damage."""
        random.seed(42)  # For reproducibility

        attacker = Stats()
        attacker._base_crit_rate = 1.0  # Always crit
        attacker._base_crit_damage = 2.0
        attacker._base_atk = 1000

        defender = Stats()
        defender.hp = 10000  # Large HP pool
        defender._base_defense = 100  # Lower defense for clearer results

        crit_damage = defender.take_damage(5000, attacker)

        # Reset for non-crit
        defender.hp = 10000
        attacker._base_crit_rate = 0.0  # Never crit
        non_crit_damage = defender.take_damage(5000, attacker)

        assert crit_damage > non_crit_damage

    def test_dodge(self):
        """Dodge avoids all damage."""
        random.seed(42)

        attacker = Stats()
        attacker._base_atk = 1000

        defender = Stats()
        defender._base_dodge_odds = 1.0  # Always dodge
        defender.hp = 1000

        damage = defender.take_damage(10000, attacker)
        assert damage == 0
        assert defender.hp == 1000

    def test_shields_absorb_damage(self):
        """Shields absorb damage before HP."""
        random.seed(100)  # Seed to avoid dodges

        attacker = Stats()
        attacker._base_atk = 1000  # High attack

        stats = Stats()
        stats.hp = 1000
        stats.shields = 500
        stats.overheal_enabled = True
        stats._base_defense = 100  # Lower defense for clearer test
        stats._base_dodge_odds = 0.0  # No dodge

        # Use higher damage that survives mitigation
        damage = stats.take_damage(10000, attacker)

        # Shields should absorb some damage
        assert stats.last_shield_absorbed > 0
        assert stats.shields < 500  # Some shields consumed

    def test_shields_overflow_to_hp(self):
        """Damage exceeding shields goes to HP."""
        attacker = Stats()
        attacker._base_atk = 5000  # Very high attack

        stats = Stats()
        stats.hp = 1000
        stats.shields = 50  # Small shields
        stats._base_defense = 50  # Very low defense for high damage

        old_hp = stats.hp
        damage = stats.take_damage(100000, attacker)  # Huge damage

        # All shields should be consumed
        assert stats.shields == 0
        # HP should be reduced
        assert stats.hp < old_hp
        # Should have taken damage to both shields and HP
        assert stats.last_shield_absorbed > 0
        assert damage > 0

    def test_enrage_increases_damage(self):
        """Enrage increases damage taken."""
        set_enrage_percent(0.5)  # 50% more damage

        attacker = Stats()
        attacker._base_atk = 1000

        stats1 = Stats()
        stats1.hp = 10000
        stats1._base_defense = 100
        damage_enraged = stats1.take_damage(5000, attacker)

        set_enrage_percent(0.0)  # No enrage
        stats2 = Stats()
        stats2.hp = 10000
        stats2._base_defense = 100
        damage_normal = stats2.take_damage(5000, attacker)

        assert damage_enraged > damage_normal
        set_enrage_percent(0.0)  # Reset

    def test_damage_tracking(self):
        """Damage is tracked correctly."""
        attacker = Stats()
        defender = Stats()
        defender.hp = 1000

        damage = defender.take_damage(100, attacker)
        assert defender.damage_taken_total == damage
        assert attacker.damage_dealt_total == damage
        assert defender.last_damage_taken == damage

    def test_minimum_damage(self):
        """Damage is at least 1."""
        defender = Stats()
        defender._base_defense = 10000  # Very high defense
        defender._base_mitigation = 10.0
        defender.hp = 1000

        damage = defender.take_damage(1)
        assert damage >= 1


class TestHealing:
    """Tests for healing mechanics."""

    def test_basic_healing(self):
        """Basic healing restores HP."""
        stats = Stats()
        stats.hp = 500
        stats._base_max_hp = 1000

        healed = stats.heal(200)
        assert healed > 0
        assert stats.hp > 500
        assert stats.hp <= 1000

    def test_healing_capped_at_max_hp(self):
        """Healing cannot exceed max HP without overheal."""
        stats = Stats()
        stats.hp = 900
        stats._base_max_hp = 1000
        stats.overheal_enabled = False

        healed = stats.heal(500)
        assert stats.hp == 1000
        assert stats.shields == 0

    def test_overheal_creates_shields(self):
        """Overheal creates shields."""
        stats = Stats()
        stats.hp = 1000
        stats._base_max_hp = 1000
        stats.enable_overheal()

        stats.heal(200)
        assert stats.hp == 1000
        assert stats.shields > 0

    def test_overheal_diminishing_returns(self):
        """Overheal has diminishing returns when shields exist."""
        stats = Stats()
        stats.hp = 1000
        stats._base_max_hp = 1000
        stats.enable_overheal()

        # First overheal - full effectiveness
        stats.shields = 0
        healed1 = stats.heal(100)
        shields1 = stats.shields

        # Second overheal with shields - diminished
        healed2 = stats.heal(100)
        shields2 = stats.shields - shields1

        assert shields2 < shields1

    def test_enrage_reduces_healing(self):
        """Enrage reduces healing effectiveness."""
        set_enrage_percent(0.5)  # 50% less healing

        stats1 = Stats()
        stats1.hp = 500
        stats1._base_max_hp = 1000
        heal_enraged = stats1.heal(100)

        set_enrage_percent(0.0)
        stats2 = Stats()
        stats2.hp = 500
        stats2._base_max_hp = 1000
        heal_normal = stats2.heal(100)

        assert heal_enraged < heal_normal
        set_enrage_percent(0.0)  # Reset

    def test_vitality_amplifies_healing(self):
        """Higher vitality increases healing."""
        stats = Stats()
        stats.hp = 500
        stats._base_max_hp = 1000
        stats._base_vitality = 2.0

        healed = stats.heal(100)
        assert healed > 100  # Amplified by vitality


class TestGaugeSystem:
    """Tests for action gauge mechanics."""

    def test_gauge_initialization(self):
        """Gauge starts at GAUGE_START."""
        stats = Stats()
        assert stats.action_gauge == GAUGE_START

    def test_advance_gauge(self):
        """Gauge can be advanced."""
        stats = Stats()
        initial = stats.action_gauge
        stats.advance_gauge(100)
        assert stats.action_gauge == initial + 100

    def test_reset_gauge(self):
        """Gauge can be reset."""
        stats = Stats()
        stats.advance_gauge(1000)
        assert stats.action_gauge != GAUGE_START
        stats.reset_gauge()
        assert stats.action_gauge == GAUGE_START


class TestCharacterDictIntegration:
    """Tests for character dictionary conversion."""

    def test_from_character_dict(self):
        """Can create Stats from character dict."""
        char_data = {
            "id": "test_char",
            "damage_type": "Fire",
            "base_stats": {
                "max_hp": 1500,
                "atk": 250,
                "defense": 180,
                "crit_rate": 0.1,
                "crit_damage": 2.5,
            },
            "runtime": {
                "level": 5,
                "exp": 100,
                "hp": 1200,
                "exp_multiplier": 1.5,
            }
        }

        stats = Stats.from_character_dict(char_data)
        assert stats.level == 5
        assert stats.exp == 100
        assert stats.hp == 1200
        assert stats.exp_multiplier == 1.5
        assert stats._base_max_hp == 1500
        assert stats._base_atk == 250
        assert stats._base_defense == 180
        assert stats.damage_type == "Fire"

    def test_to_character_dict_update(self):
        """Can export Stats back to dict format."""
        stats = Stats()
        stats.hp = 800
        stats.exp = 500
        stats.level = 10

        update = stats.to_character_dict_update()
        assert update["runtime"]["hp"] == 800
        assert update["runtime"]["exp"] == 500
        assert update["runtime"]["level"] == 10


class TestAggroSystem:
    """Tests for aggro calculations."""

    def test_base_aggro(self):
        """Aggro calculation includes base aggro."""
        stats = Stats()
        stats.base_aggro = 0.5
        assert stats.aggro >= 0.5

    def test_aggro_modifier(self):
        """Aggro modifier affects aggro."""
        stats = Stats()
        stats.base_aggro = 1.0
        stats.aggro_modifier = 0.5
        assert stats.aggro > 1.0

    def test_defense_affects_aggro(self):
        """Defense changes affect aggro."""
        stats = Stats()
        stats.base_aggro = 1.0
        base_aggro = stats.aggro

        stats.add_effect(StatEffect("def_buff", {"defense": 100}))
        buffed_aggro = stats.aggro

        assert buffed_aggro != base_aggro


class TestCritCalculation:
    """Tests for crit calculation helper."""

    def test_calculate_crit_always(self):
        """100% crit rate always crits."""
        random.seed(42)
        stats = Stats()
        stats._base_crit_rate = 1.0
        stats._base_crit_damage = 3.0

        is_crit, multiplier = stats.calculate_crit()
        assert is_crit
        assert multiplier == 3.0

    def test_calculate_crit_never(self):
        """0% crit rate never crits."""
        random.seed(42)
        stats = Stats()
        stats._base_crit_rate = 0.0

        is_crit, multiplier = stats.calculate_crit()
        assert not is_crit
        assert multiplier == 1.0


class TestEnrageSystem:
    """Tests for global enrage system."""

    def test_set_enrage_percent(self):
        """Can set enrage percent."""
        set_enrage_percent(0.25)
        assert get_enrage_percent() == 0.25
        set_enrage_percent(0.0)

    def test_enrage_percent_clamped(self):
        """Enrage percent cannot be negative."""
        set_enrage_percent(-0.5)
        assert get_enrage_percent() == 0.0
        set_enrage_percent(0.0)
