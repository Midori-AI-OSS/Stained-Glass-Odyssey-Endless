"""Tests for the Lady Echo Resonant Static passive."""

import asyncio

import pytest
from tests.helpers import call_maybe_async

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.passives.normal.lady_echo_resonant_static import LadyEchoResonantStatic


@pytest.mark.asyncio
async def test_chain_bonus_counts_effect_manager_dots():
    """Chain damage scales based on DoTs from effect manager."""
    _reset_passive_state()
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
    _reset_passive_state()
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


def _reset_passive_state() -> None:
    LadyEchoResonantStatic._current_target.clear()
    LadyEchoResonantStatic._consecutive_hits.clear()
    LadyEchoResonantStatic._party_crit_stacks.clear()
    for handler in LadyEchoResonantStatic._battle_end_handlers.values():
        BUS.unsubscribe("battle_end", handler)
    LadyEchoResonantStatic._battle_end_handlers.clear()


@pytest.mark.asyncio
async def test_consecutive_hits_increment_party_crit_stacks():
    """Consecutive hits on the same foe add party crit stacks."""
    _reset_passive_state()

    attacker = Stats()
    target = Stats()
    passive = LadyEchoResonantStatic()

    await passive.on_hit_landed(attacker, target, damage=42)
    assert passive.get_consecutive_hits(attacker) == 1
    assert passive.get_party_crit_stacks(attacker) == 0

    await passive.on_hit_landed(attacker, target, damage=37)
    assert passive.get_consecutive_hits(attacker) == 2
    assert passive.get_party_crit_stacks(attacker) == 1

    await passive.apply(attacker, hit_target=target)
    crit_effects = [
        effect for effect in attacker._active_effects
        if effect.name == f"{passive.id}_party_crit"
    ]
    assert len(crit_effects) == 1
    assert crit_effects[0].stat_modifiers["crit_rate"] == pytest.approx(0.02)


@pytest.mark.asyncio
async def test_switching_targets_resets_consecutive_hits():
    """Hitting a new target resets the combo and removes crit effects."""
    _reset_passive_state()

    attacker = Stats()
    first_target = Stats()
    second_target = Stats()
    passive = LadyEchoResonantStatic()

    await passive.on_hit_landed(attacker, first_target)
    await passive.on_hit_landed(attacker, first_target)
    await passive.apply(attacker, hit_target=first_target)

    assert passive.get_party_crit_stacks(attacker) == 1

    await passive.on_hit_landed(attacker, second_target)

    assert passive.get_consecutive_hits(attacker) == 1
    assert passive.get_party_crit_stacks(attacker) == 0
    assert not any(
        effect.name == f"{passive.id}_party_crit" for effect in attacker._active_effects
    )


@pytest.mark.asyncio
async def test_defeat_clears_state_and_effects():
    """Defeat cleanup removes combo state and the party crit buff."""
    _reset_passive_state()

    attacker = Stats()
    target = Stats()
    passive = LadyEchoResonantStatic()

    await passive.on_hit_landed(attacker, target)
    await passive.on_hit_landed(attacker, target)
    await passive.apply(attacker, hit_target=target)

    entity_id = id(attacker)
    assert entity_id in LadyEchoResonantStatic._consecutive_hits
    assert entity_id in LadyEchoResonantStatic._party_crit_stacks
    assert any(
        effect.name == f"{passive.id}_party_crit" for effect in attacker._active_effects
    )

    await passive.on_defeat(attacker)

    assert entity_id not in LadyEchoResonantStatic._consecutive_hits
    assert entity_id not in LadyEchoResonantStatic._party_crit_stacks
    assert entity_id not in LadyEchoResonantStatic._current_target
    assert not any(
        effect.name == f"{passive.id}_party_crit" for effect in attacker._active_effects
    )


@pytest.mark.asyncio
async def test_battle_end_event_triggers_cleanup():
    """Battle end events clear cached state via the registered handler."""
    _reset_passive_state()

    attacker = Stats()
    target = Stats()
    passive = LadyEchoResonantStatic()

    await passive.on_hit_landed(attacker, target)
    await passive.on_hit_landed(attacker, target)
    await passive.apply(attacker, hit_target=target)

    entity_id = id(attacker)
    assert entity_id in LadyEchoResonantStatic._battle_end_handlers

    await BUS.emit_async("battle_end", attacker)
    await asyncio.sleep(0)

    assert entity_id not in LadyEchoResonantStatic._battle_end_handlers
    assert entity_id not in LadyEchoResonantStatic._consecutive_hits
    assert not any(
        effect.name == f"{passive.id}_party_crit" for effect in attacker._active_effects
    )

