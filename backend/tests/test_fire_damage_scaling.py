import pytest

from autofighter.stats import Stats, set_battle_active
from plugins.damage_types.fire import Fire


@pytest.mark.asyncio
async def test_fire_damage_increases_as_hp_drops():
    set_battle_active(True)  # Enable battle mode for damage calculations

    attacker = Stats(damage_type=Fire())
    attacker.set_base_stat('defense', 0)
    attacker.id = "fire_attacker"

    target_full = Stats()
    target_full.set_base_stat('defense', 0)
    target_full.id = "target_full"
    dmg_full = await target_full.apply_damage(100, attacker)

    attacker.hp = attacker.max_hp // 2
    target_half = Stats()
    target_half.set_base_stat('defense', 0)
    target_half.id = "target_half"
    dmg_half = await target_half.apply_damage(100, attacker)

    attacker.hp = 1
    target_low = Stats()
    target_low.set_base_stat('defense', 0)
    target_low.id = "target_low"
    dmg_low = await target_low.apply_damage(100, attacker)

    assert dmg_full < dmg_half < dmg_low
