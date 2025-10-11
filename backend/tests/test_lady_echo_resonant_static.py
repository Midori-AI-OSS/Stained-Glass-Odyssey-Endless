"""Tests for the Lady Echo Resonant Static passive."""

import pytest

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import Stats
from plugins.passives.normal.lady_echo_resonant_static import LadyEchoResonantStatic
from tests.helpers import call_maybe_async


@pytest.mark.asyncio
async def test_chain_bonus_counts_effect_manager_dots():
    """Chain damage scales based on DoTs from effect manager."""
    attacker = Stats()
    attacker._base_atk = 100
    base_atk = attacker.atk

    target = Stats()
    target.effect_manager = EffectManager(target)
    await call_maybe_async(
        target.effect_manager.add_dot,
        DamageOverTime("d1", 1, 1, "d1"),
    )
    await call_maybe_async(
        target.effect_manager.add_dot,
        DamageOverTime("d2", 1, 1, "d2"),
    )

    passive = LadyEchoResonantStatic()
    await passive.apply(attacker, hit_target=target)

    effects = [e for e in attacker._active_effects if e.name == f"{passive.id}_chain_bonus"]
    assert len(effects) == 1
    assert effects[0].stat_modifiers["atk"] == int(base_atk * 0.2)


@pytest.mark.asyncio
async def test_chain_bonus_falls_back_to_target_dots():
    """Counts dots from Stats.dots when effect manager is missing."""
    attacker = Stats()
    attacker._base_atk = 100
    base_atk = attacker.atk

    target = Stats()
    target.dots = ["d1", "d2", "d3"]

    passive = LadyEchoResonantStatic()
    await passive.apply(attacker, hit_target=target)

    effects = [e for e in attacker._active_effects if e.name == f"{passive.id}_chain_bonus"]
    assert len(effects) == 1
    assert effects[0].stat_modifiers["atk"] == int(base_atk * 0.3)

