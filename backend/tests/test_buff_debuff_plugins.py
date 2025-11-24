import pytest

from autofighter.buffs import BuffRegistry
from autofighter.debuffs import DebuffRegistry
from autofighter.stats import Stats
from plugins.effects.buffs.attack_up import AttackUp
from plugins.effects.debuffs.blind import Blind


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
