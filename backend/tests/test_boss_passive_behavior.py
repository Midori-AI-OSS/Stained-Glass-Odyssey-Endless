"""Behavior-focused checks for selected boss-tier passives."""

from pathlib import Path
import sys
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from autofighter.stats import Stats
from plugins.passives.boss.advanced_combat_synergy import AdvancedCombatSynergyBoss
from plugins.passives.boss.ally_overload import AllyOverloadBoss
from plugins.passives.boss.lady_wind_tempest_guard import LadyWindTempestGuardBoss
from plugins.passives.normal.advanced_combat_synergy import AdvancedCombatSynergy
from plugins.passives.normal.ally_overload import AllyOverload
from plugins.passives.normal.lady_wind_tempest_guard import LadyWindTempestGuard


def reset_synergy_stacks() -> None:
    """Clear shared stack memory for the Advanced Combat Synergy family."""

    AdvancedCombatSynergy._synergy_stacks = {}
    AdvancedCombatSynergyBoss._synergy_stacks = {}


def reset_overload_state() -> None:
    """Zero out the shared tracking dictionaries used by Ally Overload."""

    for attr in ("_overload_charge", "_overload_active", "_add_hot_backup", "_battle_end_handlers"):
        setattr(AllyOverload, attr, {})


def reset_tempest_guard_state() -> None:
    """Reset the shared dictionaries used by Lady Wind's Tempest Guard."""

    for cls in (LadyWindTempestGuard, LadyWindTempestGuardBoss):
        cls._gust_stacks = {}
        cls._pending_crits = {}
        cls._crit_callbacks = {}
        cls._cleanup_callbacks = {}


@pytest.mark.asyncio
async def test_advanced_combat_synergy_boss_ally_attack_bonus() -> None:
    """Boss nova weight should buff allies 1.5× stronger than the normal tier."""

    reset_synergy_stacks()

    boss = Stats()
    ally = Stats()
    hit_target = Stats()
    hit_target.max_hp = 800
    hit_target.hp = 300

    party = [boss, ally]
    boss_passive = AdvancedCombatSynergyBoss()
    await boss_passive.apply(
        boss,
        event="hit_landed",
        hit_target=hit_target,
        damage=120,
        party=party,
    )

    boss_effect = next(
        effect
        for effect in ally.get_active_effects()
        if effect.name.endswith("_ally_atk_boost")
    )
    assert boss_effect.stat_modifiers["atk"] == 15

    reset_synergy_stacks()
    normal_target = Stats()
    normal_ally = Stats()
    hit_target = Stats()
    hit_target.max_hp = 800
    hit_target.hp = 300

    normal_passive = AdvancedCombatSynergy()
    await normal_passive.apply(
        normal_target,
        event="hit_landed",
        hit_target=hit_target,
        damage=120,
        party=[normal_target, normal_ally],
    )

    normal_effect = next(
        effect
        for effect in normal_ally.get_active_effects()
        if effect.name.endswith("_ally_atk_boost")
    )
    assert normal_effect.stat_modifiers["atk"] == 10


@pytest.mark.asyncio
async def test_advanced_combat_synergy_boss_action_stacks() -> None:
    """Boss stacks should top out at a higher attack/crit total than the normal variant."""

    reset_synergy_stacks()

    boss_passive = AdvancedCombatSynergyBoss()
    boss_target = Stats()
    for _ in range(3):
        await boss_passive.on_action_taken(boss_target)

    effect = next(
        effect
        for effect in boss_target.get_active_effects()
        if effect.name.endswith("_persistent_buff")
    )
    assert effect.stat_modifiers["atk"] == 13
    assert effect.stat_modifiers["crit_rate"] == pytest.approx(0.045)

    await boss_passive.on_action_taken(boss_target)
    effect = next(
        effect
        for effect in boss_target.get_active_effects()
        if effect.name.endswith("_persistent_buff")
    )
    assert effect.stat_modifiers["atk"] == 13

    reset_synergy_stacks()
    normal_passive = AdvancedCombatSynergy()
    normal_target = Stats()
    for _ in range(3):
        await normal_passive.on_action_taken(normal_target)

    normal_effect = next(
        effect
        for effect in normal_target.get_active_effects()
        if effect.name.endswith("_persistent_buff")
    )
    assert normal_effect.stat_modifiers["atk"] == 9
    assert normal_effect.stat_modifiers["crit_rate"] == pytest.approx(0.03)


@pytest.mark.asyncio
async def test_ally_overload_boss_charge_threshold() -> None:
    """Boss Overload holds full gain until a higher charge level than the normal passive."""

    reset_overload_state()

    boss_passive = AllyOverloadBoss()
    normal_passive = AllyOverload()
    boss_target = Stats()
    normal_target = Stats()
    boss_id = id(boss_target)
    normal_id = id(normal_target)

    AllyOverload._overload_charge[boss_id] = 130
    AllyOverload._overload_active[boss_id] = True
    AllyOverload._overload_charge[normal_id] = 130
    AllyOverload._overload_active[normal_id] = True

    await boss_passive.apply(boss_target)
    await normal_passive.apply(normal_target)

    assert boss_passive.get_stacks(boss_target) == pytest.approx(145)
    assert normal_passive.get_stacks(normal_target) == pytest.approx(135)


@pytest.mark.asyncio
async def test_lady_wind_tempest_guard_boss_defense_and_heal() -> None:
    """Storm guard stacks deliver stronger defenses and heals than the normal version."""

    reset_tempest_guard_state()

    boss_target = Stats()
    boss_target.set_base_stat("atk", 100)
    boss_passive = LadyWindTempestGuardBoss()
    boss_id = id(boss_target)
    LadyWindTempestGuardBoss._gust_stacks[boss_id] = 2

    await boss_passive.apply(boss_target)

    boss_base = next(
        effect
        for effect in boss_target.get_active_effects()
        if effect.name.endswith("_baseline_barrier")
    )
    boss_gust = next(
        effect
        for effect in boss_target.get_active_effects()
        if effect.name.endswith("_turn_gust")
    )

    reset_tempest_guard_state()
    normal_target = Stats()
    normal_target.set_base_stat("atk", 100)
    normal_passive = LadyWindTempestGuard()
    normal_id = id(normal_target)
    LadyWindTempestGuard._gust_stacks[normal_id] = 2
    await normal_passive.apply(normal_target)

    normal_base = next(
        effect
        for effect in normal_target.get_active_effects()
        if effect.name.endswith("_baseline_barrier")
    )
    normal_gust = next(
        effect
        for effect in normal_target.get_active_effects()
        if effect.name.endswith("_turn_gust")
    )

    assert boss_base.stat_modifiers["dodge_odds"] == pytest.approx(1.5 * normal_base.stat_modifiers["dodge_odds"])
    assert boss_base.stat_modifiers["mitigation"] == pytest.approx(
        1.5 * normal_base.stat_modifiers["mitigation"]
    )
    assert boss_base.stat_modifiers["effect_resistance"] == pytest.approx(
        1.5 * normal_base.stat_modifiers["effect_resistance"]
    )

    assert boss_gust.stat_modifiers["dodge_odds"] == pytest.approx(
        1.5 * normal_gust.stat_modifiers["dodge_odds"]
    )
    assert boss_gust.stat_modifiers["mitigation"] == pytest.approx(
        1.5 * normal_gust.stat_modifiers["mitigation"]
    )
    assert boss_gust.stat_modifiers["spd"] == pytest.approx(
        1.5 * normal_gust.stat_modifiers["spd"]
    )
    assert boss_gust.stat_modifiers["atk"] == pytest.approx(
        1.5 * normal_gust.stat_modifiers["atk"]
    )

    boss_target.apply_healing = AsyncMock(return_value=0)
    normal_target.apply_healing = AsyncMock(return_value=0)
    LadyWindTempestGuardBoss._gust_stacks[boss_id] = 2
    LadyWindTempestGuard._gust_stacks[normal_id] = 2

    await boss_passive.on_damage_taken(boss_target, Stats(), 100)
    await normal_passive.on_damage_taken(normal_target, Stats(), 100)

    assert boss_target.apply_healing.call_args[0][0] == pytest.approx(15)
    assert normal_target.apply_healing.call_args[0][0] == pytest.approx(10)

    for cls, target in ((LadyWindTempestGuardBoss, boss_target), (LadyWindTempestGuard, normal_target)):
        cleanup = cls._cleanup_callbacks.pop(id(target), None)
        if cleanup is not None:
            cleanup()
