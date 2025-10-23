import asyncio
from unittest.mock import patch

import pytest
from tests.helpers import call_maybe_async

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
        await BUS.emit_async("hit_landed", ally, foe, dmg, "attack")
        loop.run_until_complete(asyncio.sleep(0))
    expected = dmg + int(dmg * 0.5)
    assert foe.hp == 1000 - expected


@pytest.mark.asyncio
async def test_steady_grip_super_crit_bonus_damage():
    party = Party()
    attacker = PlayerBase()
    attacker.id = "ally"
    attacker.crit_rate = 0.5
    party.members.append(attacker)
    award_card(party, "steady_grip")
    await apply_cards(party)

    class DummyTarget:
        def __init__(self) -> None:
            self.hp = 1000
            self.id = "target"
            self.calls: list[dict[str, object]] = []

        async def apply_damage(
            self,
            amount,
            attacker,
            *,
            trigger_on_hit=True,
            action_name=None,
        ):
            self.calls.append(
                {
                    "amount": amount,
                    "attacker": attacker,
                    "trigger_on_hit": trigger_on_hit,
                    "action_name": action_name,
                }
            )
            self.hp -= amount
            return int(amount)

    target = DummyTarget()
    damage = 100

    with patch("plugins.cards.steady_grip.random.random", return_value=0.0):
        await BUS.emit_async("critical_hit", attacker, target, damage, "attack")
        await asyncio.sleep(0)

    assert target.hp == 1000 - damage * 3
    assert target.calls
    first_call = target.calls[0]
    assert first_call["trigger_on_hit"] is False
    assert first_call["action_name"] == "steady_grip_super_crit"

    await BUS.emit_async("battle_end")


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
    await call_maybe_async(mgr.add_dot, bleed)
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
    await call_maybe_async(mgr.add_dot, poison)
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


@pytest.mark.asyncio
async def test_guardians_beacon_heals_lowest_hp():
    """Test that Guardian's Beacon heals the lowest-HP ally at turn end."""
    party = Party()
    ally1 = PlayerBase()
    ally2 = PlayerBase()
    ally1.hp = ally1.set_base_stat('max_hp', 1000)
    ally2.hp = ally2.set_base_stat('max_hp', 1000)
    ally1.id = "ally1"
    ally2.id = "ally2"
    party.members.extend([ally1, ally2])

    # Set ally1 to 500 HP (50%), ally2 to 700 HP (70%)
    ally1.hp = 500
    ally2.hp = 700

    # Award card and apply
    award_card(party, "guardians_beacon")
    await apply_cards(party)

    # Trigger turn_end event
    await BUS.emit_async("turn_end")
    await asyncio.sleep(0.01)

    # ally1 should have been healed (8% of 1000 = 80)
    assert ally1.hp == 580, f"Expected ally1 HP 580, got {ally1.hp}"
    # ally2 should not have been healed
    assert ally2.hp == 700, f"Expected ally2 HP 700, got {ally2.hp}"


@pytest.mark.asyncio
async def test_guardians_beacon_light_mitigation():
    """Test that Guardian's Beacon grants mitigation to Light allies."""
    from plugins.damage_types.light import Light

    party = Party()
    light_ally = PlayerBase()
    non_light_ally = PlayerBase()

    light_ally.hp = light_ally.set_base_stat('max_hp', 1000)
    light_ally.set_base_stat('mitigation', 1.0)
    light_ally.damage_type = Light()
    light_ally.id = "light_ally"

    non_light_ally.hp = non_light_ally.set_base_stat('max_hp', 1000)
    non_light_ally.set_base_stat('mitigation', 1.0)
    non_light_ally.id = "non_light_ally"

    party.members.extend([light_ally, non_light_ally])

    # Set light_ally to lower HP (50%), non_light to 70%
    light_ally.hp = 500
    non_light_ally.hp = 700

    # Award card and apply
    award_card(party, "guardians_beacon")
    await apply_cards(party)

    # Get initial mitigation
    initial_mitigation = light_ally.mitigation

    # Trigger turn_end event
    await BUS.emit_async("turn_end")
    await asyncio.sleep(0.01)

    # Light ally should have increased mitigation (+10%)
    assert light_ally.mitigation > initial_mitigation, f"Expected mitigation > {initial_mitigation}, got {light_ally.mitigation}"


@pytest.mark.asyncio
async def test_guardians_beacon_no_light_bonus():
    """Test that Guardian's Beacon doesn't grant mitigation to non-Light allies."""
    from plugins.damage_types.fire import Fire

    party = Party()
    fire_ally = PlayerBase()
    fire_ally.hp = fire_ally.set_base_stat('max_hp', 1000)
    fire_ally.set_base_stat('mitigation', 1.0)
    fire_ally.damage_type = Fire()
    fire_ally.id = "fire_ally"
    party.members.append(fire_ally)

    # Set to low HP
    fire_ally.hp = 500

    # Award card and apply
    award_card(party, "guardians_beacon")
    await apply_cards(party)

    # Get initial mitigation
    initial_mitigation = fire_ally.mitigation

    # Trigger turn_end event
    await BUS.emit_async("turn_end")
    await asyncio.sleep(0.01)

    # Fire ally should NOT have increased mitigation beyond base card effects
    # The card itself provides +55% DEF but no mitigation
    assert fire_ally.mitigation == initial_mitigation, f"Expected mitigation {initial_mitigation}, got {fire_ally.mitigation}"


@pytest.mark.asyncio
async def test_guardians_beacon_skips_dead_allies():
    """Test that Guardian's Beacon skips dead allies when finding lowest HP."""
    party = Party()
    dead_ally = PlayerBase()
    alive_ally = PlayerBase()

    dead_ally.hp = dead_ally.set_base_stat('max_hp', 1000)
    alive_ally.hp = alive_ally.set_base_stat('max_hp', 1000)
    dead_ally.id = "dead_ally"
    alive_ally.id = "alive_ally"

    party.members.extend([dead_ally, alive_ally])

    # Set dead_ally to 0 HP, alive_ally to 700 HP
    dead_ally.hp = 0
    alive_ally.hp = 700

    # Award card and apply
    award_card(party, "guardians_beacon")
    await apply_cards(party)

    # Trigger turn_end event
    await BUS.emit_async("turn_end")
    await asyncio.sleep(0.01)

    # dead_ally should stay at 0
    assert dead_ally.hp == 0, f"Expected dead_ally HP 0, got {dead_ally.hp}"
    # alive_ally should have been healed (8% of 1000 = 80)
    assert alive_ally.hp == 780, f"Expected alive_ally HP 780, got {alive_ally.hp}"


@pytest.mark.asyncio
async def test_guardians_beacon_telemetry():
    """Test that Guardian's Beacon emits proper telemetry events."""
    party = Party()
    ally = PlayerBase()
    ally.hp = ally.set_base_stat('max_hp', 1000)
    ally.id = "ally"
    party.members.append(ally)

    # Set to low HP
    ally.hp = 500

    # Award card and apply
    award_card(party, "guardians_beacon")
    await apply_cards(party)

    # Capture telemetry events
    events: list[tuple] = []

    def capture(*args: object) -> None:
        events.append(args)

    BUS.subscribe("card_effect", capture)

    # Trigger turn_end event
    await BUS.emit_async("turn_end")
    await asyncio.sleep(0.01)

    BUS.unsubscribe("card_effect", capture)

    # Check that telemetry was emitted (filtering out stat_buff events from card application)
    heal_events = [e for e in events if e[2] == "turn_end_heal"]
    assert len(heal_events) > 0, "Expected telemetry event"
    card_id, actor, effect_type, value, metadata = heal_events[0]
    assert card_id == "guardians_beacon"
    assert effect_type == "turn_end_heal"
    assert value == 80  # 8% of 1000
    assert metadata["heal_percentage"] == 8
    # HP percentage is measured at turn end, not before healing
    assert metadata["hp_percentage"] >= 50.0  # Should be at least 50% after considering healing

