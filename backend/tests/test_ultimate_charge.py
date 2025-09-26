import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic
from plugins.damage_types.ice import Ice
from plugins.characters._base import PlayerBase


def test_charge_accumulates_and_caps():
    player = PlayerBase(damage_type=Generic())
    for _ in range(20):
        player.add_ultimate_charge()
    assert player.ultimate_charge == 15
    assert player.ultimate_ready is True


def test_charge_from_multiple_ally_actions():
    actor = PlayerBase(damage_type=Generic())
    ice = PlayerBase(damage_type=Ice())
    ice.handle_ally_action(actor)
    ice.handle_ally_action(actor)
    assert ice.ultimate_charge == actor.actions_per_turn * 2


@pytest.mark.asyncio
async def test_ice_ultimate_damage_scaling():
    user = PlayerBase(damage_type=Ice())
    user._base_atk = 10
    user.ultimate_charge = 15
    user.ultimate_ready = True
    foe_a = Stats()
    foe_b = Stats()
    for idx, foe in enumerate([foe_a, foe_b], start=1):
        foe.id = f"f{idx}"
        foe._base_defense = 1
        foe._base_max_hp = 2000
        foe.hp = foe.max_hp
    await user.damage_type.ultimate(user, [foe_a, foe_b])
    assert foe_a.hp == 2000 - 100 * 6
    assert foe_b.hp == 2000 - 169 * 6


@pytest.mark.asyncio
async def test_use_ultimate_emits_event():
    player = PlayerBase(damage_type=Generic())
    player.ultimate_charge = 15
    player.ultimate_ready = True
    seen: list[Stats] = []

    def _handler(user):
        seen.append(user)

    BUS.subscribe("ultimate_used", _handler)
    try:
        assert await player.use_ultimate() is True
        assert player.ultimate_charge == 0
        assert player.ultimate_ready is False
        assert seen == [player]
    finally:
        BUS.unsubscribe("ultimate_used", _handler)

