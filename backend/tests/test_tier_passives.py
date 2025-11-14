"""Tests for tier-specific passive resolution system."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import PassiveRegistry
from autofighter.passives import apply_rank_passives
from autofighter.passives import resolve_passive_for_rank
from plugins.characters.luna import Luna


def test_resolve_passive_for_rank_normal():
    """Test that normal rank resolves to base passive."""
    resolved = resolve_passive_for_rank("luna_lunar_reservoir", "normal")
    assert resolved == "luna_lunar_reservoir"


def test_resolve_passive_for_rank_glitched():
    """Test that glitched rank resolves to glitched passive."""
    resolved = resolve_passive_for_rank("luna_lunar_reservoir", "glitched")
    assert resolved == "luna_lunar_reservoir_glitched"


def test_resolve_passive_for_rank_boss():
    """Test that boss rank resolves to boss passive."""
    resolved = resolve_passive_for_rank("luna_lunar_reservoir", "boss")
    assert resolved == "luna_lunar_reservoir_boss"


def test_resolve_passive_for_rank_prime():
    """Test that prime rank resolves to prime passive."""
    resolved = resolve_passive_for_rank("luna_lunar_reservoir", "prime")
    assert resolved == "luna_lunar_reservoir_prime"


def test_resolve_passive_for_rank_glitched_boss():
    """Test that glitched boss prioritizes glitched variant."""
    resolved = resolve_passive_for_rank("luna_lunar_reservoir", "glitched boss")
    assert resolved == "luna_lunar_reservoir_glitched"


def test_resolve_passive_for_rank_nonexistent():
    """Test that non-existent tier passives fall back to base."""
    # Assuming attack_up doesn't have tier variants yet
    resolved = resolve_passive_for_rank("attack_up", "glitched")
    assert resolved == "attack_up"


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
    luna.passives = ["luna_lunar_reservoir", "attack_up"]

    apply_rank_passives(luna)

    # luna_lunar_reservoir should be glitched, attack_up should stay as is
    assert luna.passives == ["luna_lunar_reservoir_glitched", "attack_up"]


def test_passive_registry_contains_tier_passives():
    """Test that the passive registry contains tier-specific Luna passives."""
    registry = PassiveRegistry()

    assert "luna_lunar_reservoir" in registry._registry
    assert "luna_lunar_reservoir_glitched" in registry._registry
    assert "luna_lunar_reservoir_boss" in registry._registry
    assert "luna_lunar_reservoir_prime" in registry._registry
