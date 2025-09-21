import asyncio

import pytest

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import Stats


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


@pytest.mark.asyncio
async def test_farsight_scope_crit_bonus_applied_and_removed():
    loop = setup_event_loop()
    party = Party()
    ally = Stats()
    enemy = Stats()
    ally.set_base_stat("atk", 100)
    enemy.set_base_stat("max_hp", 1000)
    enemy.hp = 1000
    party.members.append(ally)
    award_card(party, "farsight_scope")
    loop.run_until_complete(apply_cards(party))

    base_crit = ally.crit_rate

    enemy.hp = 400  # Below 50%
    await BUS.emit_async("before_attack", ally, enemy)
    assert ally.crit_rate == pytest.approx(base_crit + 0.06, abs=1e-6)

    await BUS.emit_async("action_used", ally, enemy, ally.atk)
    assert ally.crit_rate == pytest.approx(base_crit, abs=1e-6)
