"""Tests for tier-specific passive resolution system."""
import importlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import PassiveRegistry
from autofighter.passives import apply_rank_passives
from autofighter.passives import resolve_passives_for_rank
from plugins.characters.luna import Luna


def test_resolve_passives_for_rank_normal():
    """Test that normal rank resolves to base passive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "normal")
    assert resolved == ["luna_lunar_reservoir"]


def test_resolve_passives_for_rank_glitched():
    """Test that glitched rank resolves to glitched passive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "glitched")
    assert resolved == ["luna_lunar_reservoir_glitched"]


def test_resolve_passives_for_rank_boss():
    """Test that boss rank resolves to boss passive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "boss")
    assert resolved == ["luna_lunar_reservoir_boss"]


def test_resolve_passives_for_rank_prime():
    """Test that prime rank resolves to prime passive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "prime")
    assert resolved == ["luna_lunar_reservoir_prime"]


def test_resolve_passives_for_rank_glitched_boss():
    """Test that glitched boss stacks both glitched and boss variants."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "glitched boss")
    assert set(resolved) == {"luna_lunar_reservoir_glitched", "luna_lunar_reservoir_boss"}
    assert len(resolved) == 2


def test_resolve_passives_for_rank_prime_boss():
    """Test that prime boss stacks both prime and boss variants."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "prime boss")
    assert set(resolved) == {"luna_lunar_reservoir_prime", "luna_lunar_reservoir_boss"}
    assert len(resolved) == 2


def test_resolve_passives_for_rank_glitched_prime():
    """Test that glitched prime stacks both glitched and prime variants."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "glitched prime")
    assert set(resolved) == {"luna_lunar_reservoir_glitched", "luna_lunar_reservoir_prime"}
    assert len(resolved) == 2


def test_resolve_passives_for_rank_glitched_prime_boss():
    """Test that glitched prime boss stacks all three tier variants."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "glitched prime boss")
    assert set(resolved) == {
        "luna_lunar_reservoir_glitched",
        "luna_lunar_reservoir_prime",
        "luna_lunar_reservoir_boss"
    }
    assert len(resolved) == 3


def test_resolve_passives_for_rank_empty_string():
    """Test that empty rank string falls back to base passive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "")
    assert resolved == ["luna_lunar_reservoir"]


def test_resolve_passives_for_rank_none_like():
    """Test that None-like values fall back to base passive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "")
    assert resolved == ["luna_lunar_reservoir"]


def test_resolve_passives_for_rank_unknown_tag():
    """Test that unknown rank tags fall back to base passive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "unknown_rank")
    assert resolved == ["luna_lunar_reservoir"]


def test_resolve_passives_for_rank_case_insensitive():
    """Test that rank matching is case-insensitive."""
    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "GLITCHED")
    assert resolved == ["luna_lunar_reservoir_glitched"]

    resolved = resolve_passives_for_rank("luna_lunar_reservoir", "Prime Boss")
    assert set(resolved) == {"luna_lunar_reservoir_prime", "luna_lunar_reservoir_boss"}


def test_resolve_passives_for_rank_nonexistent():
    """Test that non-existent tier passives fall back to base."""
    # Using player_level_up_bonus which doesn't have tier variants
    resolved = resolve_passives_for_rank("player_level_up_bonus", "glitched")
    assert resolved == ["player_level_up_bonus"]


def test_apply_rank_passives_normal():
    """Test applying rank passives to a normal foe."""
    luna = Luna()
    luna.rank = "normal"
    luna.passives = ["luna_lunar_reservoir"]

    apply_rank_passives(luna)

    assert luna.passives == ["luna_lunar_reservoir"]


def test_apply_rank_passives_glitched():
    """Test applying rank passives to a glitched foe."""
    luna = Luna()
    luna.rank = "glitched"
    luna.passives = ["luna_lunar_reservoir"]

    apply_rank_passives(luna)

    assert luna.passives == ["luna_lunar_reservoir_glitched"]


def test_apply_rank_passives_boss():
    """Test applying rank passives to a boss foe."""
    luna = Luna()
    luna.rank = "boss"
    luna.passives = ["luna_lunar_reservoir"]

    apply_rank_passives(luna)

    assert luna.passives == ["luna_lunar_reservoir_boss"]


def test_apply_rank_passives_prime():
    """Test applying rank passives to a prime foe."""
    luna = Luna()
    luna.rank = "prime"
    luna.passives = ["luna_lunar_reservoir"]

    apply_rank_passives(luna)

    assert luna.passives == ["luna_lunar_reservoir_prime"]


def test_apply_rank_passives_multiple():
    """Test applying rank passives with multiple passives."""
    luna = Luna()
    luna.rank = "glitched"
    luna.passives = ["luna_lunar_reservoir", "ixia_tiny_titan"]

    apply_rank_passives(luna)

    # Both should be resolved to glitched variants
    assert luna.passives == ["luna_lunar_reservoir_glitched", "ixia_tiny_titan_glitched"]


def test_apply_rank_passives_glitched_prime_boss():
    """Test applying rank passives with all tier tags stacks all variants."""
    luna = Luna()
    luna.rank = "glitched prime boss"
    luna.passives = ["luna_lunar_reservoir"]

    apply_rank_passives(luna)

    # Should stack all three tier variants
    assert set(luna.passives) == {
        "luna_lunar_reservoir_glitched",
        "luna_lunar_reservoir_prime",
        "luna_lunar_reservoir_boss"
    }
    assert len(luna.passives) == 3


def test_apply_rank_passives_prime_boss():
    """Test applying rank passives with prime boss stacks both variants."""
    luna = Luna()
    luna.rank = "prime boss"
    luna.passives = ["luna_lunar_reservoir"]

    apply_rank_passives(luna)

    # Should stack both tier variants
    assert set(luna.passives) == {
        "luna_lunar_reservoir_prime",
        "luna_lunar_reservoir_boss"
    }
    assert len(luna.passives) == 2


def test_apply_rank_passives_no_rank():
    """Test applying rank passives with no rank attribute."""
    luna = Luna()
    # Don't set rank attribute
    if hasattr(luna, 'rank'):
        delattr(luna, 'rank')
    luna.passives = ["luna_lunar_reservoir"]

    apply_rank_passives(luna)

    # Should fall back to base passive
    assert luna.passives == ["luna_lunar_reservoir"]


def test_apply_rank_passives_empty_passives_list():
    """Test applying rank passives with empty passives list."""
    luna = Luna()
    luna.rank = "glitched"
    luna.passives = []

    apply_rank_passives(luna)

    # Should remain empty
    assert luna.passives == []


def test_apply_rank_passives_no_passives_attribute():
    """Test applying rank passives when foe has no passives attribute."""
    class FoeWithoutPassives:
        rank = "glitched"

    foe = FoeWithoutPassives()

    # Should not raise an error
    apply_rank_passives(foe)

    # Should not add a passives attribute
    assert not hasattr(foe, 'passives')


def test_passive_registry_contains_tier_passives():
    """Test that the passive registry contains tier-specific Luna passives."""
    registry = PassiveRegistry()

    assert "luna_lunar_reservoir" in registry._registry
    assert "luna_lunar_reservoir_glitched" in registry._registry
    assert "luna_lunar_reservoir_boss" in registry._registry
    assert "luna_lunar_reservoir_prime" in registry._registry


def test_all_boss_passives_register():
    """Ensure every boss passive module exposes a concrete passive class."""

    plugins_root = Path(__file__).resolve().parents[1] / "plugins" / "passives" / "boss"
    for module_path in plugins_root.glob("*.py"):
        if module_path.name.startswith("__"):
            continue
        importlib.import_module(f"plugins.passives.boss.{module_path.stem}")

    registry = PassiveRegistry()
    for module_path in plugins_root.glob("*.py"):
        if module_path.name.startswith("__"):
            continue
        passive_id = f"{module_path.stem}_boss"
        cls = registry._registry.get(passive_id)
        assert cls is not None, f"Missing boss passive {passive_id}"
        instance = cls()
        assert getattr(instance, "plugin_type", None) == "passive"
