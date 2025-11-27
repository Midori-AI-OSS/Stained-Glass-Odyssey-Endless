import pytest

from autofighter.buffs import BuffRegistry
from autofighter.debuffs import DebuffRegistry
from autofighter.stats import Stats
from plugins.effects.buffs.attack_up import AttackUp
from plugins.effects.buffs.crit_damage_up import CritDamageUp
from plugins.effects.buffs.crit_rate_up import CritRateUp
from plugins.effects.buffs.defense_up import DefenseUp
from plugins.effects.buffs.speed_up import SpeedUp
from plugins.effects.debuffs.attack_down import AttackDown
from plugins.effects.debuffs.blind import Blind
from plugins.effects.debuffs.defense_down import DefenseDown
from plugins.effects.debuffs.speed_down import SpeedDown
from plugins.effects.debuffs.vulnerability import Vulnerability


@pytest.mark.asyncio
async def test_attack_up_buff_applies_stat_increase():
    stats = Stats()
    base_attack = stats.atk
    buff = AttackUp(amount=50, duration=2)
    effect = await buff.apply(stats)
    assert stats.atk == pytest.approx(base_attack + 50)
    assert effect.duration == 2


@pytest.mark.asyncio
async def test_stack_index_creates_unique_buff_effects():
    stats = Stats()
    buff = AttackUp(amount=20, duration=1)
    await buff.apply(stats, stack_index=0)
    await buff.apply(stats, stack_index=1)
    effect_names = [effect.name for effect in stats.get_active_effects()]
    assert "attack_up_0" in effect_names
    assert "attack_up_1" in effect_names


@pytest.mark.asyncio
async def test_blind_debuff_reduces_hit_rate():
    stats = Stats()
    base_hit_rate = stats.effect_hit_rate
    blind = Blind()
    await blind.apply(stats)
    assert stats.effect_hit_rate == pytest.approx(base_hit_rate + blind.stat_modifiers["effect_hit_rate"])


@pytest.mark.asyncio
async def test_defense_up_buff_increases_defense():
    stats = Stats()
    base_defense = stats.defense
    buff = DefenseUp(amount=25.0, duration=2)
    effect = await buff.apply(stats)
    assert stats.defense == pytest.approx(base_defense + 25.0)
    assert effect.duration == 2
    assert effect.stat_modifiers["defense"] == pytest.approx(25.0)
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "defense_up" in effect_names


@pytest.mark.asyncio
async def test_speed_up_buff_boosts_speed():
    stats = Stats()
    base_speed = stats.spd
    buff = SpeedUp(amount=6.0, duration=1)
    effect = await buff.apply(stats)
    assert stats.spd == pytest.approx(base_speed + 6.0)
    assert effect.duration == 1
    assert effect.stat_modifiers["spd"] == pytest.approx(6.0)
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "speed_up" in effect_names


@pytest.mark.asyncio
async def test_crit_rate_up_buff_increases_crit_rate():
    stats = Stats()
    base_rate = stats.crit_rate
    buff = CritRateUp(amount=0.1, duration=3)
    effect = await buff.apply(stats)
    assert stats.crit_rate == pytest.approx(base_rate + 0.1)
    assert effect.duration == 3
    assert effect.stat_modifiers["crit_rate"] == pytest.approx(0.1)
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "crit_rate_up" in effect_names


@pytest.mark.asyncio
async def test_crit_damage_up_buff_increases_crit_damage():
    stats = Stats()
    base_damage = stats.crit_damage
    buff = CritDamageUp(amount=0.15, duration=2)
    effect = await buff.apply(stats)
    assert stats.crit_damage == pytest.approx(base_damage + 0.15)
    assert effect.duration == 2
    assert effect.stat_modifiers["crit_damage"] == pytest.approx(0.15)
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "crit_damage_up" in effect_names


@pytest.mark.asyncio
async def test_attack_down_debuff_reduces_attack():
    stats = Stats()
    base_attack = stats.atk
    debuff = AttackDown(duration=1)
    effect = await debuff.apply(stats)
    assert stats.atk == pytest.approx(base_attack + effect.stat_modifiers["atk"])
    assert effect.duration == 1
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "attack_down" in effect_names


@pytest.mark.asyncio
async def test_defense_down_debuff_reduces_defense():
    stats = Stats()
    base_defense = stats.defense
    debuff = DefenseDown(duration=1)
    effect = await debuff.apply(stats)
    assert stats.defense == pytest.approx(base_defense + effect.stat_modifiers["defense"])
    assert effect.duration == 1
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "defense_down" in effect_names


@pytest.mark.asyncio
async def test_speed_down_debuff_slows_speed():
    stats = Stats()
    base_speed = stats.spd
    debuff = SpeedDown(duration=1)
    effect = await debuff.apply(stats)
    assert stats.spd == pytest.approx(base_speed + effect.stat_modifiers["spd"])
    assert effect.duration == 1
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "speed_down" in effect_names


@pytest.mark.asyncio
async def test_vulnerability_debuff_reduces_mitigation():
    stats = Stats()
    base_mitigation = stats.mitigation
    debuff = Vulnerability(duration=2)
    effect = await debuff.apply(stats)
    assert stats.mitigation == pytest.approx(base_mitigation + effect.stat_modifiers["mitigation"])
    assert effect.duration == 2
    effect_names = [active.name for active in stats.get_active_effects()]
    assert "vulnerability" in effect_names


@pytest.mark.asyncio
async def test_buff_registry_apply_with_custom_amount():
    registry = BuffRegistry()
    stats = Stats()
    base_attack = stats.atk
    applied = await registry.apply_buff(
        "attack_up",
        stats,
        init_kwargs={"amount": 60.0, "duration": 1},
        stack_index=2,
    )
    assert stats.atk == pytest.approx(base_attack + 60)
    assert applied.name.endswith("_2")


@pytest.mark.asyncio
async def test_debuff_registry_apply_blind():
    registry = DebuffRegistry()
    stats = Stats()
    base = stats.effect_hit_rate
    await registry.apply_debuff("blind", stats)
    assert stats.effect_hit_rate < base


def test_registry_discovery_includes_new_plugins():
    buff_registry = BuffRegistry()
    debuff_registry = DebuffRegistry()
    assert "attack_up" in buff_registry.all_buffs()
    assert "vulnerability" in debuff_registry.all_debuffs()
