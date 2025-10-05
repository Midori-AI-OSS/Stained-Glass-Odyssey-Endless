import asyncio

import pytest

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_tactical_kit_converts_hp_once_per_battle():
    party = Party()
    acting_ally = PlayerBase()
    other_ally = PlayerBase()
    party.members.extend([acting_ally, other_ally])

    award_card(party, "tactical_kit")
    await apply_cards(party)

    await BUS.emit_async("battle_start", acting_ally)
    await BUS.emit_async("battle_start", other_ally)
    await asyncio.sleep(0)

    initial_max_hp = acting_ally.max_hp
    initial_hp = acting_ally.hp
    initial_atk = acting_ally.atk

    await BUS.emit_async("action_used", acting_ally, other_ally, 0)
    await asyncio.sleep(0)

    expected_hp_after_conversion = max(1, initial_hp - int(initial_max_hp * 0.01))
    assert acting_ally.hp == expected_hp_after_conversion
    after_first_atk = acting_ally.atk
    assert after_first_atk > initial_atk

    await BUS.emit_async("action_used", acting_ally, other_ally, 0)
    await asyncio.sleep(0)

    assert acting_ally.hp == expected_hp_after_conversion
    assert acting_ally.atk == pytest.approx(after_first_atk)
