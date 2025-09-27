import asyncio

import pytest

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters import player as player_mod


@pytest.mark.asyncio
async def test_swift_footwork_speed_bonuses_and_no_extra_turns():
    player = player_mod.Player()
    base_spd = player.spd
    party = Party(members=[player])
    award_card(party, "swift_footwork")
    await apply_cards(party)
    await asyncio.sleep(0)

    # Permanent SPD boost is applied when cards are awarded
    expected_permanent = int(base_spd * 1.2)
    assert player.spd == expected_permanent

    extra_turns: list[object] = []

    def _on_extra_turn(actor, *_args):
        extra_turns.append(actor)

    BUS.subscribe("extra_turn", _on_extra_turn)

    await BUS.emit_async("battle_start")
    await asyncio.sleep(0)

    # Opening burst further increases SPD without granting extra turns
    expected_burst = int(base_spd * 1.5)
    assert player.spd == expected_burst

    await BUS.emit_async("action_used", player, None, 0)
    await asyncio.sleep(0)

    BUS.unsubscribe("extra_turn", _on_extra_turn)

    assert not extra_turns
