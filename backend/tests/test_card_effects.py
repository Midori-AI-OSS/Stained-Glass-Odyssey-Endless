import asyncio
from unittest.mock import patch

import pytest

from autofighter.action_queue import ActionQueue
from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.party import Party
from autofighter.rooms import battle as battle_module
from autofighter.stats import BUS
from autofighter.stats import GAUGE_START
from plugins.characters._base import PlayerBase


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


@pytest.mark.asyncio
async def test_overclock_speed_buff_queue():
    loop = setup_event_loop()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    ally.set_base_stat("spd", 100)
    foe = PlayerBase()
    foe.id = "foe"
    foe.set_base_stat("spd", 200)
    party.members.append(ally)
    award_card(party, "overclock")
    loop.run_until_complete(apply_cards(party))
    battle_module._VISUAL_QUEUE = ActionQueue([ally, foe])
    battle_module._EXTRA_TURNS.clear()
    await BUS.emit_async("battle_start", foe)
    await BUS.emit_async("battle_start", ally)
    loop.run_until_complete(asyncio.sleep(0))
    try:
        assert battle_module._EXTRA_TURNS == {}

        boosted_spd = ally.spd
        assert boosted_spd > ally.get_base_stat("spd")

        expected_base = GAUGE_START / max(boosted_spd, 1)
        assert ally.base_action_value == pytest.approx(expected_base)
        assert ally.action_value == pytest.approx(expected_base)

        queue = battle_module._VISUAL_QUEUE
        assert queue is not None
        snapshot = queue.snapshot()
        assert snapshot[0]["id"] == "ally"
        assert not snapshot[0].get("bonus", False)

        manager = getattr(ally, "effect_manager", None)
        assert manager is not None
        for _ in range(2):
            loop.run_until_complete(manager.tick())
        loop.run_until_complete(asyncio.sleep(0))

        restored_spd = ally.spd
        assert restored_spd == ally.get_base_stat("spd")
        restored_base = GAUGE_START / max(restored_spd, 1)
        assert ally.base_action_value == pytest.approx(restored_base)
    finally:
        battle_module._VISUAL_QUEUE = None


@pytest.mark.asyncio
async def test_iron_resolve_revives_and_cooldown():
    party = Party()
    ally = PlayerBase()
    enemy = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 100)
    party.members.append(ally)
    loop = setup_event_loop()
    award_card(party, "iron_resolve")
    loop.run_until_complete(apply_cards(party))

    ally.hp = 0
    await BUS.emit_async("damage_taken", ally, enemy, 200)
    assert ally.hp == int(ally.max_hp * 0.30)

    ally.hp = 0
    await BUS.emit_async("damage_taken", ally, enemy, 200)
    assert ally.hp == 0

    for _ in range(3):
        await BUS.emit_async("turn_end")

    ally.hp = 0
    await BUS.emit_async("damage_taken", ally, enemy, 200)
    assert ally.hp == int(ally.max_hp * 0.30)


@pytest.mark.asyncio
async def test_arcane_repeater_repeats_attack():
    loop = setup_event_loop()
    party = Party()
    ally = PlayerBase()
    foe = PlayerBase()
    ally.set_base_stat('atk', 100)
    foe.hp = foe.set_base_stat('max_hp', 1000)
    party.members.append(ally)
    award_card(party, "arcane_repeater")
    loop.run_until_complete(apply_cards(party))

    dmg = loop.run_until_complete(foe.apply_damage(ally.atk, attacker=ally))
    with patch("random.random", return_value=0.1):
        await BUS.emit_async("attack_used", ally, foe, dmg)
        loop.run_until_complete(asyncio.sleep(0))
    expected = dmg + int(dmg * 0.5)
    assert foe.hp == 1000 - expected


@pytest.mark.asyncio
async def test_mindful_tassel_boosts_first_debuff():
    loop = setup_event_loop()
    party = Party()
    ally = PlayerBase()
    foe = PlayerBase()
    party.members.append(ally)
    award_card(party, "mindful_tassel")
    loop.run_until_complete(apply_cards(party))

    await BUS.emit_async("battle_start", ally)
    await BUS.emit_async("battle_start", foe)
    loop.run_until_complete(asyncio.sleep(0))

    mgr = EffectManager(foe)
    foe.effect_manager = mgr
    bleed = DamageOverTime(
        name="Bleed",
        damage=100,
        turns=10,
        id="bleed",
        source=ally,
    )
    mgr.add_dot(bleed)
    loop.run_until_complete(asyncio.sleep(0))
    assert bleed.damage == 105
    assert bleed.turns == 11

    poison = DamageOverTime(
        name="Poison",
        damage=100,
        turns=10,
        id="poison",
        source=ally,
    )
    mgr.add_dot(poison)
    loop.run_until_complete(asyncio.sleep(0))
    assert poison.damage == 100
    assert poison.turns == 10


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "card_id",
        "event_builder",
        "effect_key",
        "expected_events",
        "expected_charge",
        "random_roll",
    ),
    (
        (
            "lucky_coin",
            lambda party, ally, foe: ("critical_hit", (ally, foe, 100, "attack")),
            "charge_refund",
            1,
            1,
            0.0,
        ),
        (
            "energizing_tea",
            lambda party, ally, foe: ("battle_start", (ally,)),
            "charge_bonus",
            1,
            1,
            None,
        ),
    ),
)
async def test_apply_cards_cleans_up_bus_handlers(
    card_id,
    event_builder,
    effect_key,
    expected_events,
    expected_charge,
    random_roll,
):
    setup_event_loop()
    party = Party()
    ally = PlayerBase()
    ally.id = "ally"
    foe = PlayerBase()
    foe.id = "foe"
    party.members.append(ally)

    award_card(party, card_id)

    await apply_cards(party)
    await BUS.emit_async("battle_end", None)
    await apply_cards(party)

    ally.ultimate_charge = 0
    records: list[tuple[object, int]] = []

    def _capture(card, member, effect_type, value, payload):
        if card == card_id and effect_type == effect_key:
            records.append((member, value))

    BUS.subscribe("card_effect", _capture)

    try:
        event_name, args = event_builder(party, ally, foe)
        if random_roll is not None:
            with patch("random.random", return_value=random_roll):
                await BUS.emit_async(event_name, *args)
        else:
            await BUS.emit_async(event_name, *args)
        await asyncio.sleep(0)
    finally:
        BUS.unsubscribe("card_effect", _capture)

    assert len(records) == expected_events
    assert ally.ultimate_charge == expected_charge

    await BUS.emit_async("battle_end", None)
