import pytest

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active


@pytest.mark.asyncio
async def test_farsight_scope_crit_bonus_applied_and_removed():
    party = Party()
    ally = Stats()
    enemy = Stats()
    ally.set_base_stat("atk", 100)
    enemy.set_base_stat("max_hp", 1000)
    enemy.hp = 1000
    party.members.append(ally)
    award_card(party, "farsight_scope")
    await apply_cards(party)

    base_crit = ally.crit_rate

    enemy.hp = 400  # Below 50%
    await BUS.emit_async("before_attack", ally, enemy)
    assert ally.crit_rate == pytest.approx(base_crit + 0.06, abs=1e-6)

    await BUS.emit_async("action_used", ally, enemy, ally.atk)
    assert ally.crit_rate == pytest.approx(base_crit, abs=1e-6)


@pytest.mark.asyncio
async def test_farsight_scope_triggers_during_normal_attack_flow():
    party = Party()
    ally = Stats()
    enemy = Stats()
    ally.set_base_stat("atk", 150)
    enemy.set_base_stat("max_hp", 1000)
    enemy.hp = 1000
    enemy.dodge_odds = 0.0
    party.members.append(ally)
    award_card(party, "farsight_scope")
    await apply_cards(party)

    base_crit = ally.crit_rate
    enemy.hp = 400  # Below 50%

    set_battle_active(True)
    try:
        damage = await enemy.apply_damage(ally.atk, attacker=ally, action_name="Normal Attack")
        assert damage > 0
        assert ally.crit_rate == pytest.approx(base_crit + 0.06, abs=1e-6)
        await BUS.emit_async("action_used", ally, enemy, damage)
    finally:
        set_battle_active(False)

    assert ally.crit_rate == pytest.approx(base_crit, abs=1e-6)
