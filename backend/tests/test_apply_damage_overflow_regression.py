import sys

import pytest

from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from autofighter.stats import set_enrage_percent


@pytest.mark.asyncio
async def test_apply_damage_extreme_enrage_remains_finite():
    attacker = Stats()
    defender = Stats()

    attacker.crit_rate = 0.0
    attacker.vitality = 1e150

    defender.dodge_odds = 0.0
    defender.defense = 1
    defender.mitigation = 0.1
    defender.vitality = 0.01
    defender.hp = defender.max_hp

    raw_amount = 1e150

    set_enrage_percent(1e6)
    set_battle_active(True)
    try:
        damage = await defender.apply_damage(raw_amount, attacker=attacker)
    finally:
        set_battle_active(False)
        set_enrage_percent(0.0)

    assert isinstance(damage, int)
    assert damage >= 1
    assert damage < sys.float_info.max
