import pytest

from autofighter.rooms.utils import _serialize
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.characters._base import PlayerBase
from plugins.characters.luna import Luna
from plugins.damage_types.generic import Generic
from plugins.damage_types.ice import Ice
from plugins.damage_types.wind import Wind


def test_charge_accumulates_and_caps():
    player = PlayerBase(damage_type=Generic())
    cap = player.ultimate_charge_max
    for _ in range(cap + 5):
        player.add_ultimate_charge()
    assert player.ultimate_charge == cap
    assert player.ultimate_ready is True


def test_charge_from_multiple_ally_actions():
    actor = PlayerBase(damage_type=Generic())
    wind = PlayerBase(damage_type=Wind())
    wind.handle_ally_action(actor)
    wind.handle_ally_action(actor)
    assert wind.ultimate_charge == actor.actions_per_turn * 2


@pytest.mark.asyncio
async def test_ice_ultimate_damage_scaling():
    user = PlayerBase(damage_type=Ice())
    user.id = "ice_user"
    user._base_atk = 10
    user.ultimate_charge = user.ultimate_charge_max
    user.ultimate_ready = True
    foe_a = Stats()
    foe_b = Stats()
    for idx, foe in enumerate([foe_a, foe_b], start=1):
        foe.id = f"f{idx}"
        foe._base_defense = 1
        foe._base_max_hp = 2000
        foe.hp = foe.max_hp
    set_battle_active(True)
    try:
        await user.damage_type.ultimate(user, [user], [foe_a, foe_b])
    finally:
        set_battle_active(False)
    assert foe_a.hp == 2000 - 100 * 6
    assert foe_b.hp == 2000 - 169 * 6


@pytest.mark.asyncio
async def test_use_ultimate_emits_event():
    player = PlayerBase(damage_type=Generic())
    player.ultimate_charge = player.ultimate_charge_max
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


def test_luna_uses_custom_ultimate_cap_and_serializes_maximum():
    luna = Luna()
    assert luna.ultimate_charge_max == 15_000

    luna.add_ultimate_charge(luna.ultimate_charge_max - 1)
    assert luna.ultimate_ready is False
    luna.add_ultimate_charge(1)
    assert luna.ultimate_ready is True

    payload = _serialize(luna)
    assert payload["ultimate_max"] == luna.ultimate_charge_max

